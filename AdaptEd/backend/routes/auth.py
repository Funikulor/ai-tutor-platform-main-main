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

