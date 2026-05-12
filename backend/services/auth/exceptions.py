class AuthServiceError(Exception):
    """Базовый класс ошибок аутентификации"""
    pass


class UsernameAlreadyExistsError(AuthServiceError):
    """Пользователь с таким именем уже существует"""

    def __init__(self, username: str):
        super().__init__(f"Пользователь с именем '{username}' уже существует")


class UserNotFoundError(AuthServiceError):
    """Пользователь не найден"""

    def __init__(self, message: str = "Пользователь с таким именем не найден"):
        super().__init__(message)


class InvalidPasswordError(AuthServiceError):
    """Неверный пароль"""

    def __init__(self, message: str = "Неверный пароль"):
        super().__init__(message)
