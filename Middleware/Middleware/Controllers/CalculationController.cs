using Microsoft.AspNetCore.Mvc;
using Middleware.Clients;
using Middleware.DTO;
using Middleware.DTO.Requests;
using Middleware.Services;

namespace Middleware.Controllers;

[ApiController]
[Route("middleware/calculation")]
public class CalculationController: ControllerBase
{
    private readonly ICalculationService _calculationService;
    private readonly IBookingApiClient _bookingApiClient;
    private readonly IMasterApiClient _masterApiClient;
    public CalculationController(
        ICalculationService calculationService,
        IBookingApiClient bookingApiClient,
        IMasterApiClient masterApiClient)
    {
        _calculationService = calculationService;
        _bookingApiClient = bookingApiClient;
        _masterApiClient = masterApiClient;
    }
    /// <summary>
    /// Возвращает список всех валидных start_time внутри окна 
    /// </summary>
    /// <remarks>
    /// Пример:
    ///{
    ///     "timeInterval": {
    ///        "start": "08:00:00",
    ///        "end": "10:30:00"
    ///    },
    ///    "duration": "00:30:00",
    ///    "granularTimeStep": "00:05:00"
    ///}
    /// </remarks>
    [HttpPost("possible-start-times")]
    public List<TimeOnly> GetPossibleStartTimes([FromBody] PossibleStartTimesRequest request)
    {
        return 
            _calculationService.CalculatePossibleStartTimes(request.timeInterval.Start, request.timeInterval.End,
                request.Duration, request.GranularTimeStep);
    }
    
    //TO-DO доделать когда появится desk-api
    
    /// <summary>
    /// Рассчитывает все возможные временные промежутки работы заданной услуги на основе текущего расписания мастера
    /// </summary>
    /// <remarks>
    /// Пример: { "master_id": 6, "service_id": 10, "date": "2026-04-21", "granular_time_step": "00:05:00" }
    /// </remarks>
    /// <returns>список кортежей (начало-конец) для заданной услуги</returns>
    [HttpPost("possible-time-slots")]
    public async Task<List<TimeSlotWithDate>> GetPossibleTimeSlots([FromBody] PossibleTimeSlotsRequest request)
    {
        //Получаем длительность услуги у desk-api
        TimeSpan serviceDuration = await _masterApiClient.GetMasterServiceDuration(request.MasterId, request.ServiceId);
        
        //Получаем список свободных временных слотов у desk-api
        var freeTimeSlots = await _bookingApiClient
            .GetFreeSlots(request.MasterId, request.Date, request.Date.AddDays(1));
        
        return _calculationService.CalculatePossibleTimeSlotsOnDate(freeTimeSlots, serviceDuration, request.GranularTimeStep);
    }
    /// <summary>
    /// Рассчитывает все возможные слоты работы заданной услуги в временном промежутки на n дней вперед 
    /// </summary>
    /// <remarks>
    /// Пример: { "master_id": 123, "service_id": 456, "time_slot": { "start": "10:00:00", "end": "13:00:00" }, "start_date": "2026-04-20", "end_date": "2026-04-22", "pre_buffer": "00:01:00", "post_buffer": "00:01:00", "granular_time_step": "00:05:00" }
    /// </remarks>
    [HttpPost("closest-possible-time-slots")]
    public async Task<List<TimeSlotWithDate>> GetClosestPossibleTimeSlots([FromBody] ClosestPossibleTimeSlotsRequest request)
    {
        //debug
        //Получаем длительность услуги у desk-api
        TimeSpan serviceDuration = await _masterApiClient.GetMasterServiceDuration(request.MasterId, request.ServiceId);


        //Добавляем буферное время
        serviceDuration = serviceDuration.Add(request.PreBuffer);
        serviceDuration = serviceDuration.Add(request.PostBuffer);

        var freeTimeSlots = await _bookingApiClient
            .GetFreeSlots(request.MasterId, request.StartDate, request.EndDate);
        Console.WriteLine(freeTimeSlots.Count);
        return _calculationService.CalculateClosestPossibleTimeSlots
            (freeTimeSlots, request.timeSlot, serviceDuration ,request.GranularTimeStep);
    }
    
    
    /// <summary>
    /// Возвращает количество рабочих часоав мастера (часы, занятых услугой слотов)
    /// </summary>
    [HttpPost("masters-busy-working-hours")]
    public async Task<double> GetMastersBusyWorkingHours([FromBody] MastersBusyWorkingHoursRequest request)
    {
        //Получаем занятые слоты за период рабочих дней мастера
        var bookedSlots = await _bookingApiClient
            .GetBookedSlots(request.MasterId, request.StartDate, request.EndDate);
        return _calculationService.CalculateMastersBusyWorkingHours(bookedSlots);
    }
    
    
    /// <summary>
    /// Возвращает количество выполненных услуг организации за промежуток времени
    /// </summary>
    //TO-DO доделать
    [HttpPost("organizations-completed-services")]
    public async Task<int> GetOrganizationsCompletedServices([FromBody] OrganizationCompletedServicesRequest request)
    {
        //Получаю список мастеров организации
        List<int> masters = await _masterApiClient.GetMastersIds(request.OrganizationId);
        
        int overallCompletedServices = 0;
        Console.WriteLine(masters.Count);
        //Получаем занятые слоты за период рабочих дней мастера
        foreach (int masterId in masters)
        {
            var bookedSlots = await _bookingApiClient
                .GetBookedSlots(masterId, request.StartDate, request.EndDate);
            
            overallCompletedServices += _calculationService.CalculateMastersCompletedServices(bookedSlots);
        }
        return overallCompletedServices;
    }
    
    /// <summary>
    /// Возвращает полную временную карту дня мастера (bitmap / массив статусов: свободно / занято / перерыв / отсутствие / буфер) 
    /// </summary>
    /// <remarks>э
    /// Пример:
    /// {"master_id": 6,"date": "2026-04-20","granular_time_step": "00:05:00","pre_buffer": "00:05:00","post_buffer": "00:05:00"}
    /// </remarks>
    [HttpPost("day-timeline")]
    public async Task<List<TimeSegmentDTO>> GetDayTimeline([FromBody] DayTimelineRequest request)
    {
        var bookedSlots = await _bookingApiClient
            .GetBookedSlots(request.MasterId, request.Date, request.Date.AddDays(1));
        
        var workTime = await _masterApiClient.GetMastersWorkDay(request.MasterId, request.Date);
        
        var segments = _calculationService.BuildDayTimeline(
            workTime,
            bookedSlots,
            request.GranularTimeStep
        );

        return segments.Select(s => new TimeSegmentDTO
        {
            Status = s.Status.ToString(),
            Start = s.Start,
            End = s.End
        }).ToList();
    }

    
    /// <summary>
    /// Рассчитывает лучшие возможные временные промежутки работы заданной услуги на основе текущего расписания мастера
    /// </summary>
    /// <remarks>
    /// Пример: { "master_id": 6, "service_id": 1, "date": "2026-04-20", "granular_time_step": "00:05:00" }
    /// </remarks>
    /// <returns>список кортежей (начало-конец) для заданной услуги</returns>
    [HttpPost("best-time-slot")]
    public async Task<List<TimeSlot>> GetBestTimeSlots(BestTimeSlotsRequest request)
    {
        //Получаю свободные слоты по мастеру,
        var freeTimeSlots = await _bookingApiClient
            .GetFreeSlots(request.MasterID, request.Date);
        //Получаю длительность услуги
        TimeSpan serviceDuration = await _masterApiClient.GetMasterServiceDuration(request.MasterID, request.ServiceID);

        return _calculationService.CalculateBestTimeSlots(freeTimeSlots, serviceDuration, request.GranularTimeStep);
    }
    
}