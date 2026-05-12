from fastapi import HTTPException, status


class OrganizationNotFoundError(HTTPException):
    def __init__(self, org_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Организация  не найдена"
        )


class NotManagerOfOrganizationError(HTTPException):
    def __init__(self, account_id: int, org_id: int):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Пользователь {account_id} не является менеджером организации {org_id}"
        )


class NoRelationToOrganizationError(HTTPException):
    def __init__(self, account_id: int, org_id: int):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"У пользователя {account_id} нет связи с организацией {org_id}"
        )


class OrganizationDisabledError(HTTPException):
    def __init__(self, org_id: int):
        super().__init__(
            status_code=status.HTTP_410_GONE,  # или 403, на твой выбор
            detail=f"Организация с ID {org_id} деактивирована (удалена)"
        )