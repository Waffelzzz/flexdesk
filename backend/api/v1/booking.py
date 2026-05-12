from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


from core.dependencies import get_current_manager
from db.models import Account, Manager
from db.session import get_db_session
from schemas.booking import (
    SlotGenerateRequest,
    SlotGenerateResponse,
    SlotFreeResponse,
    SlotResponse,
    GenerateSlotsForAllResponse,
    GenerateSlotsForAllRequest,
    GenerateSlotsForMastersRequest,
    SlotFreeRequest,
    BookingResponse,
    BookingCreateRequest,
    BookedSlotsIntervalsResponse, BookingCancelResponse, BookingCancelRequest
)
from services.booking.service import BookingService

router = APIRouter(prefix="/booking", tags=["Booking"])


async def get_manager_organization(
        current_manager: Account = Depends(get_current_manager),
        session: AsyncSession = Depends(get_db_session)
) -> int:
    """
    Получает organization_id текущего менеджера
    """
    result = await session.execute(
        select(Manager).where(Manager.account_id == current_manager.account_id)
    )
    manager = result.scalar_one_or_none()

    if not manager:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Менеджер не привязан к организации"
        )

    return manager.organization_id


@router.post("/generate-slots", response_model=SlotGenerateResponse)
async def generate_slots(
        request: SlotGenerateRequest,
        session: AsyncSession = Depends(get_db_session),
        current_manager: Account = Depends(get_current_manager),
        organization_id: int = Depends(get_manager_organization)
):
    """
    Генерация слотов для мастера с помощью хранимой процедуры.
    Только для менеджеров.

    - **master_id**: ID мастера
    - **start_date**: дата начала (например, 2026-03-20)
    - **end_date**: дата окончания (опционально)

    Процедура создаёт слоты каждые 5 минут на основе шаблонов мастера.
    """
    service = BookingService(session)

    try:
        result = await service.generate_slots_for_master(
            master_id=request.master_id,
            start_date=request.start_date,
            end_date=request.end_date,
            organization_id=organization_id
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при генерации слотов: {str(e)}"
        )

@router.post("/generate-slots-all-masters", response_model=GenerateSlotsForAllResponse)
async def generate_slots_for_all_masters(
        request: GenerateSlotsForAllRequest,
        session: AsyncSession = Depends(get_db_session),
        current_manager: Account = Depends(get_current_manager),
        organization_id: int = Depends(get_manager_organization)
):
    """
    Генерация слотов для ВСЕХ мастеров организации с помощью хранимой процедуры.
    Только для менеджеров.

    - **start_date**: дата начала (например, 2026-03-20)
    - **end_date**: дата окончания (опционально)

    Процедура создаёт слоты каждые 5 минут для каждого мастера на основе их шаблонов.
    """
    service = BookingService(session)

    try:
        result = await service.generate_slots_for_all_masters(
            start_date=request.start_date,
            end_date=request.end_date,
            organization_id=organization_id
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при генерации слотов для всех мастеров: {str(e)}"
        )


@router.post("/generate-slots-masters", response_model=GenerateSlotsForAllResponse)
async def generate_slots_for_masters(
        request: GenerateSlotsForMastersRequest,
        session: AsyncSession = Depends(get_db_session),
        current_manager: Account = Depends(get_current_manager),
        organization_id: int = Depends(get_manager_organization)
):
    """
    Генерация слотов для выбранных мастеров организации.
    Только для менеджеров.
    """
    service = BookingService(session)
    end_date = request.end_date or request.start_date
    total_slots = 0
    errors = []

    for master_id in request.master_ids:
        try:
            result = await service.generate_slots_for_master(
                master_id=master_id,
                start_date=request.start_date,
                end_date=end_date,
                organization_id=organization_id
            )
            total_slots += result["slots_created"]
        except Exception as e:
            errors.append(f"Мастер {master_id}: {str(e)}")

    return {
        "organization_id": organization_id,
        "start_date": request.start_date,
        "end_date": end_date,
        "total_masters": len(request.master_ids),
        "slots_created": total_slots,
        "errors": errors if errors else None,
        "message": f"Создано {total_slots} слотов для {len(request.master_ids)} мастеров"
    }


@router.post("/masters/{master_id}/free-slots", response_model=SlotFreeResponse)
async def get_free_slots(
    master_id: int,
    request: SlotFreeRequest,
    session: AsyncSession = Depends(get_db_session),
    organization_id: int = Depends(get_manager_organization)
):
    """
    Получение свободных слотов мастера за период.
    Только для менеджеров.
    """
    service = BookingService(session)

    try:
        slots = await service.get_free_slots(
            master_id=master_id,
            start_date=request.start_date,
            end_date=request.end_date,
            organization_id=organization_id
        )

        slot_responses = [
            SlotResponse(
                booking_id=slot.booking_id,
                master_id=slot.master_id,
                booking_dt=slot.booking_dt,
                status=slot.status
            )
            for slot in slots
        ]

        return SlotFreeResponse(
            master_id=master_id,
            organization_id=organization_id,
            start_date=request.start_date,
            end_date=request.end_date or request.start_date,
            slots=slot_responses,
            total=len(slot_responses)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении слотов: {str(e)}"
        )


@router.post("/masters/{master_id}/free-slots-intervals")
async def get_free_slots_intervals(
        master_id: int,
        request: SlotFreeRequest,
        session: AsyncSession = Depends(get_db_session),
        organization_id: int = Depends(get_manager_organization)
):
    """
    Получение свободных слотов мастера в виде интервалов.
    Только для менеджеров.
    """
    service = BookingService(session)

    slots = await service.get_free_slots_raw(
        master_id=master_id,
        start_date=request.start_date,
        end_date=request.end_date,
        organization_id=organization_id
    )

    intervals = service._merge_slots(slots)

    return {
        "master_id": master_id,
        "organization_id": organization_id,
        "start_date": request.start_date,
        "end_date": request.end_date or request.start_date,
        "intervals": intervals,
        "total_intervals": len(intervals)
    }


@router.delete("/masters/{master_id}/clear-slots")
async def clear_free_slots(
        master_id: int,
        start_date: date = Query(..., description="Дата начала (YYYY-MM-DD)"),
        end_date: Optional[date] = Query(None, description="Дата окончания (YYYY-MM-DD)"),
        session: AsyncSession = Depends(get_db_session),
        current_manager: Account = Depends(get_current_manager),
        organization_id: int = Depends(get_manager_organization)
):
    """
    Удаление свободных слотов мастера за период.
    Только для менеджеров.
    """
    service = BookingService(session)

    try:
        deleted_count = await service.clear_master_slots(
            master_id=master_id,
            start_date=start_date,
            end_date=end_date,
            organization_id=organization_id
        )

        return {
            "message": f"Удалено {deleted_count} свободных слотов",
            "deleted_count": deleted_count,
            "master_id": master_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat() if end_date else start_date.isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении слотов: {str(e)}"
        )


@router.post("/book", response_model=BookingResponse)
async def book_slot(
        request: BookingCreateRequest,
        session: AsyncSession = Depends(get_db_session),
        organization_id: int = Depends(get_manager_organization)
):
    """
    Создание бронирования с учётом длительности услуги.

    Занимает нужное количество 5-минутных атомарных слотов подряд.
    """
    service = BookingService(session)

    try:
        result = await service.book_slot(
            service_master_id=request.service_master_id,
            client_id=request.client_id,
            booking_dt=request.booking_dt,
            duration_minutes=request.duration_minutes,
            organization_id=organization_id
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при бронировании: {str(e)}"
        )

@router.post("/masters/{master_id}/booked-slots-intervals")
async def get_booked_slots_intervals(
        master_id: int,
        request: SlotFreeRequest,
        session: AsyncSession = Depends(get_db_session),
        organization_id: int = Depends(get_manager_organization)
):
    """
    Получение забронированных слотов мастера в виде интервалов (от-до).
    Только для менеджеров.
    """
    service = BookingService(session)

    try:
        intervals, total_minutes = await service.get_booked_slots_intervals(
            master_id=master_id,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        return BookedSlotsIntervalsResponse(
            master_id=master_id,
            organization_id=organization_id,
            start_date=request.start_date,
            end_date=request.end_date or request.start_date,
            intervals=intervals,
            total_intervals=len(intervals),
            total_minutes=total_minutes
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении интервалов забронированных слотов: {str(e)}"
        )

@router.post("/masters/{master_id}/cancel-booking", response_model=BookingCancelResponse)
async def cancel_booking(
        master_id: int,
        request: BookingCancelRequest,
        session: AsyncSession = Depends(get_db_session),
        organization_id: int = Depends(get_manager_organization)
):
    """
    Отмена записи клиента.

    Освобождает все подряд идущие 5-минутные слоты,
    принадлежащие одной записи (client_id + service_id).
    """
    service = BookingService(session)

    try:
        released = await service.cancel_booking(
            master_id=master_id,
            booking_dt=request.booking_dt,
            client_id=request.client_id,
            organization_id=organization_id
        )

        return BookingCancelResponse(
            master_id=master_id,
            client_id=request.client_id,
            booking_dt=request.booking_dt,
            released_slots=released,
            status="cancelled"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при отмене записи: {str(e)}"
        )

