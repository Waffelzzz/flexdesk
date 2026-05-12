from datetime import datetime


class ClientError(Exception):
    """Базовое исключение для клиентов"""
    pass


class ClientNotFoundError(ClientError):
    """Клиент не найден"""
    def __init__(self, client_id: int):
        self.client_id = client_id
        super().__init__(f"Клиент с id={client_id} не найден")


class ClientAlreadyExistsError(ClientError):
    """Клиент уже существует в этой организации"""
    def __init__(self, account_id: int, org_id: int):
        self.account_id = account_id
        self.org_id = org_id
        super().__init__(f"Аккаунт {account_id} уже является клиентом организации {org_id}")


class BookingNotFoundError(ClientError):
    """Запись не найдена"""
    def __init__(self, booking_id: int):
        self.booking_id = booking_id
        super().__init__(f"Запись с id={booking_id} не найдена")


class BookingTimeUnavailableError(ClientError):
    """Время записи недоступно"""
    def __init__(self, booking_dt: datetime):
        self.booking_dt = booking_dt
        super().__init__(f"Время {booking_dt} недоступно для записи")


class BookingAlreadyExistsError(ClientError):
    """Запись уже существует"""
    pass


class InvalidBookingStatusError(ClientError):
    """Неверный статус записи"""
    pass