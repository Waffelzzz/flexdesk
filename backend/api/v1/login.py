from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from db.session import get_db_session
from schemas.auth import Token, UserLogin
from schemas.user import UserCreate, UserOut
from services.auth.exceptions import (
    UsernameAlreadyExistsError,
    UserNotFoundError,
    InvalidPasswordError,
)
from services.auth.service import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(session=Depends(get_db_session)) -> AuthService:
    return AuthService(session)


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
    description=(
        "Создаёт нового аккаунт в системе.\n\n"
        "Логин должен быть уникальным.\n"
        "Требования к паролю проверяются на стороне клиента."
    ),
    responses={
        400: {
            "description": "Логин уже занят",
            "content": {
                "application/json": {
                    "example": {"detail": "Пользователь с таким логином уже существует"}
                }
            },
        },
        422: {"description": "Ошибка валидации входных данных"},
    },
)
async def register(
    user_data: UserCreate,
    service: AuthService = Depends(get_auth_service),
) -> UserOut:
    try:
        return await service.register(user_data)
    except UsernameAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500,
            detail="Ошибка при регистрации. Попробуйте позже."
        )


@router.post(
    "/login",
    response_model=Token,
    summary="Вход в систему (получение JWT-токена)",
    description=(
        "Аутентифицирует пользователя по логину и паролю.\n\n"
        "Возвращает JWT access token в формате Bearer.\n"
        "Токен имеет ограниченное время жизни."
    ),
    responses={
        401: {
            "description": "Неверные учетные данные",
            "content": {
                "application/json": {
                    "example": {"detail": "Неверный логин или пароль"}
                }
            },
        },
        422: {"description": "Ошибка валидации входных данных"},
    },
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
) -> Token:
    user_login = UserLogin(
        login=form_data.username,
        password=form_data.password,
    )

    try:
        token_data = await service.login(user_login)
        return token_data

    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidPasswordError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500,
            detail="Ошибка сервера при аутентификации"
        )