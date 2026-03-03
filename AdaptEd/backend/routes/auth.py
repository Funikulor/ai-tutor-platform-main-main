"""
API маршруты для авторизации и регистрации
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
from pydantic import BaseModel
from models.auth import UserRegistration, UserLogin, Token, User, UserRole
from utils.auth_service import auth_service


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_seed: Optional[str] = None


class ResetAdminPassword(BaseModel):
    secret: str
    new_password: str


class RecreateAdminBody(BaseModel):
    secret: str


class CreateAdminBody(BaseModel):
    secret: str
    email: str
    password: str
    full_name: Optional[str] = "Администратор"


router = APIRouter()


def get_current_user(authorization: str = Header(None)) -> dict:
    """Получает текущего пользователя из токена"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Token missing")
    
    # Извлекаем токен из заголовка
    try:
        token = authorization.split(" ")[1] if " " in authorization else authorization
    except:
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    user = auth_service.get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user


@router.post("/auth/register", response_model=User)
async def register(user_data: UserRegistration):
    """
    Регистрация нового пользователя
    
    Поддерживаемые роли: student, teacher, parent
    """
    try:
        user = auth_service.register_user(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            role=user_data.role,
            class_id=user_data.class_id,
            phone=user_data.phone,
            parent_fio=user_data.parent_fio,
            parent_phone=user_data.parent_phone
        )
        
        if not user:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        return user
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auth/login", response_model=Token)
async def login(login_data: UserLogin):
    """
    Вход пользователя
    
    Возвращает токен доступа
    """
    try:
        result = auth_service.authenticate_user(
            email=login_data.email,
            password=login_data.password
        )
        
        if not result:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Получаем полную информацию о пользователе
        user_data = auth_service.get_user_by_id(result["user_id"])
        
        return Token(
            access_token=result["token"],
            user_id=result["user_id"],
            role=result["role"],
            full_name=user_data.get("full_name") if user_data else None,
            email=user_data.get("email") if user_data else login_data.email
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auth/create-admin")
async def create_admin(body: CreateAdminBody):
    """
    Создать нового админа (без удаления существующих).
    В Railway Variables задайте ADMIN_RESET_SECRET. Тело: secret, email, password, full_name (опционально).
    """
    import os
    expected = (os.getenv("ADMIN_RESET_SECRET") or "").strip()
    secret = (body.secret or "").strip()
    if not expected or secret != expected:
        raise HTTPException(status_code=400, detail="Неверный секрет. Задайте ADMIN_RESET_SECRET в Variables.")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Пароль не короче 6 символов.")
    user = auth_service.register_user(
        email=body.email,
        password=body.password,
        full_name=body.full_name or "Администратор",
        role=UserRole.ADMIN,
        class_id=None,
        phone=None,
    )
    if not user:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует.")
    return {
        "message": "Админ создан. Войдите с указанным email и паролем.",
        "email": user.email,
    }


@router.post("/auth/recreate-admin")
async def recreate_admin(body: RecreateAdminBody):
    """
    Удаляет всех админов и создаёт одного нового из переменных окружения.
    В Railway Variables задайте: ADMIN_RESET_SECRET, ADMIN_EMAIL, ADMIN_PASSWORD.
    Вызовите с телом {"secret": "ваш_ADMIN_RESET_SECRET"} — старый админ будет удалён,
    новый создан. Войдите с ADMIN_EMAIL и ADMIN_PASSWORD.
    """
    email = auth_service.recreate_admin_by_secret(body.secret)
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Неверный секрет или не заданы ADMIN_EMAIL/ADMIN_PASSWORD в Variables.",
        )
    return {
        "message": "Админ пересоздан. Войдите с указанным email и паролем из ADMIN_PASSWORD.",
        "email": email,
    }


@router.get("/auth/check-reset-secret")
async def check_reset_secret():
    """
    Проверка: задана ли переменная ADMIN_RESET_SECRET в окружении (без раскрытия значения).
    Помогает убедиться, что Variables подхватились после редеплоя.
    """
    import os
    return {"set": bool((os.getenv("ADMIN_RESET_SECRET") or "").strip())}


@router.post("/auth/reset-admin-password")
async def reset_admin_password(body: ResetAdminPassword):
    """
    Сброс пароля администратора по секрету из env.
    В Railway Variables добавьте ADMIN_RESET_SECRET=ваш_секрет, вызовите этот endpoint
    с тем же secret и new_password, затем удалите переменную.
    """
    email = auth_service.reset_admin_password_by_secret(body.secret, body.new_password)
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Неверный секрет или пароль короче 6 символов. Убедитесь, что ADMIN_RESET_SECRET задан в Variables и совпадает с secret в запросе."
        )
    return {
        "message": "Пароль сброшен. Войдите с указанным email и новым паролем.",
        "email": email,
    }


@router.post("/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Выход пользователя"""
    # В реальном приложении здесь нужно передавать токен
    return {"message": "Logged out successfully"}


@router.get("/auth/me", response_model=dict)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Получение информации о текущем пользователе"""
    return current_user


@router.get("/users/{user_id}", response_model=dict)
async def get_user_profile(user_id: str, current_user: dict = Depends(get_current_user)):
    """
    Получение профиля пользователя
    
    Ученики могут видеть только свой профиль
    Учителя и админы - профили всех пользователей
    """
    # Проверяем доступ
    if current_user["role"] == "student" and current_user["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Получаем пользователя через AuthService
    user_data = auth_service.get_user_by_id(user_id)
    
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user_data


@router.get("/auth/profile", response_model=dict)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Получение полного профиля текущего пользователя"""
    user_id = current_user["user_id"]
    user_data = auth_service.get_user_by_id(user_id)
    
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Добавляем дополнительную информацию из аналитики (если есть)
    try:
        from services.student_analytics import get_analytics_service
        analytics_service = get_analytics_service()
        analytics = analytics_service.get_analytics(user_id)
        user_data["analytics"] = analytics
    except Exception:
        pass  # Аналитика опциональна
    
    return user_data


@router.put("/auth/profile", response_model=dict)
async def update_profile(updates: ProfileUpdate, current_user: dict = Depends(get_current_user)):
    """Обновить профиль текущего пользователя (имя, телефон, аватар)."""
    user_id = current_user["user_id"]
    ok = auth_service.update_profile(
        user_id,
        full_name=updates.full_name,
        phone=updates.phone,
        avatar_seed=updates.avatar_seed,
    )
    if not ok:
        raise HTTPException(status_code=500, detail="Не удалось обновить профиль")
    user_data = auth_service.get_user_by_id(user_id)
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        from services.student_analytics import get_analytics_service
        analytics_service = get_analytics_service()
        user_data["analytics"] = analytics_service.get_analytics(user_id)
    except Exception:
        pass
    return user_data

