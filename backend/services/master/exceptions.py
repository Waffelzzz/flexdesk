from fastapi import HTTPException, status

class NoRelationToOrganizationError(HTTPException):
    def __init__(self, account_id: int, org_id: int):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"У пользователя {account_id} нет связи с организацией {org_id}"
        )

class NotManagerOfOrganizationError(HTTPException):
    def __init__(self, account_id: int, org_id: int):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Пользователь {account_id} не является менеджером организации {org_id}"
        )

class ServiceMasterNotFoundError(HTTPException):
    def __init__(self, id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Услуга мастера {id} не найдена"
        )