class AccountError(Exception):
    """Базовое исключение для аккаунтов"""
    pass


class AccountNotFoundError(AccountError):
    """Аккаунт не найден"""
    def __init__(self, account_id: int):
        self.account_id = account_id
        super().__init__(f"Аккаунт с id={account_id} не найден")


class AccountLoginAlreadyExistsError(AccountError):
    """Логин уже занят"""
    def __init__(self, login: str):
        self.login = login
        super().__init__(f"Аккаунт с логином '{login}' уже существует")


class AccountInvalidPasswordError(AccountError):
    """Неверный пароль"""
    pass


class AccountDisabledError(AccountError):
    """Аккаунт отключен"""
    def __init__(self, account_id: int):
        self.account_id = account_id
        super().__init__(f"Аккаунт с id={account_id} отключен")