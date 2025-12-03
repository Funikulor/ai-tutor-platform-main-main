from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
from utils.auth_service import auth_service
from utils.persistent_storage import persistent_storage

router = APIRouter()

class UserSubmission(BaseModel):
	user_id: int
	answers: List[int]

class UserResponse(BaseModel):
	user_id: int
	answers: List[int]

class UserUpdate(BaseModel):
	full_name: Optional[str] = None
	email: Optional[str] = None
	role: Optional[str] = None
	class_id: Optional[str] = None
	phone: Optional[str] = None
	is_active: Optional[bool] = None

# In-memory storage for user data
user_data = {}

@router.post("/users/submit_answers", response_model=UserResponse)
async def submit_answers(user: UserSubmission):
	user_data[user.user_id] = user.answers
	return UserResponse(user_id=user.user_id, answers=user.answers)

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_data(user_id: int):
	if user_id not in user_data:
		raise HTTPException(status_code=404, detail="User not found")
	return UserResponse(user_id=user_id, answers=user_data[user_id])

@router.get("/debug")
def debug_storage():
	"""Отладочный endpoint для проверки хранилища"""
	from utils.persistent_storage import persistent_storage
	return {
		"users_count": len(persistent_storage.get("users", {})),
		"users": persistent_storage.get("users", {}),
		"data_file_exists": os.path.exists("data.json")
	}

@router.get("/all")
def get_all_users():
	"""Получить всех пользователей"""
	try:
		users = auth_service.get_all_users()
		return users
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))

@router.put("/users/{user_id}", response_model=Dict)
async def update_user(user_id: str, updates: UserUpdate):
	"""Обновить данные пользователя (админ)."""
	users = persistent_storage.get("users", {})
	if user_id not in users:
		raise HTTPException(status_code=404, detail="Пользователь не найден")
	user = users[user_id]
	for k, v in updates.dict(exclude_unset=True).items():
		if k == "email" and v:
			user["email"] = v
		elif k == "full_name" and v is not None:
			user["full_name"] = v
		elif k == "role" and v:
			user["role"] = v
		elif k == "class_id":
			user["class_id"] = v
		elif k == "phone":
			user["phone"] = v
		elif k == "is_active" and v is not None:
			user["is_active"] = v
	users[user_id] = user
	persistent_storage.set("users", users)
	# Не возвращаем пароль
	return {k: v for k, v in user.items() if k != "password"}

@router.post("/users/{user_id}/toggle", response_model=Dict)
async def toggle_user_active(user_id: str):
	users = persistent_storage.get("users", {})
	if user_id not in users:
		raise HTTPException(status_code=404, detail="Пользователь не найден")
	users[user_id]["is_active"] = not bool(users[user_id].get("is_active", True))
	persistent_storage.set("users", users)
	return {k: v for k, v in users[user_id].items() if k != "password"}

@router.delete("/users/{user_id}", response_model=Dict)
async def delete_user(user_id: str):
	users = persistent_storage.get("users", {})
	if user_id not in users:
		raise HTTPException(status_code=404, detail="Пользователь не найден")
	deleted = {k: v for k, v in users[user_id].items() if k != "password"}
	del users[user_id]
	persistent_storage.set("users", users)
	return deleted