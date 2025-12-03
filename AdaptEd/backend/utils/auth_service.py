"""
Сервис авторизации
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from models.auth import User, UserRole
from utils.persistent_storage import persistent_storage


class AuthService:
    """Сервис для работы с авторизацией"""
    
    def __init__(self):
        self.sessions: Dict[str, dict] = {}  # token -> user_data
        self._create_default_admin()
        
    def _create_default_admin(self):
        """Создает предустановленного администратора"""
        admin_id = "admin_001"
        admin_email = "admin@adapted.ru"
        admin_password = "admin123"  # В продакшене должен быть сложный пароль
        
        # Проверяем, не существует ли уже админ
        if admin_id not in persistent_storage.get("users", {}):
            hashed_password = self.hash_password(admin_password)
            
            admin_data = {
                "user_id": admin_id,
                "email": admin_email,
                "full_name": "Системный Администратор",
                "role": "admin",
                "class_id": None,
                "phone": None,
                "created_at": datetime.now(),
                "is_active": True,
                "password": hashed_password
            }
            
            # Получаем существующих пользователей и добавляем админа
            existing_users = persistent_storage.get("users", {})
            existing_users[admin_id] = admin_data
            persistent_storage.set("users", existing_users)
    
    def hash_password(self, password: str) -> str:
        """Хеширует пароль"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def generate_token(self, user_id: str, role: UserRole) -> str:
        """Генерирует токен доступа"""
        token = secrets.token_urlsafe(32)
        self.sessions[token] = {
            "user_id": user_id,
            "role": role.value,
            "created_at": datetime.now()
        }
        return token
    
    def register_user(self, email: str, password: str, full_name: str, 
                     role: UserRole, class_id: Optional[str] = None,
                     phone: Optional[str] = None) -> Optional[User]:
        """Регистрирует нового пользователя"""
        # Проверяем, не существует ли уже пользователь
        users = persistent_storage.get("users", {})
        for user_id, user_data in users.items():
            if user_data.get("email") == email:
                return None
        
        # Создаем пользователя
        users = persistent_storage.get("users", {})
        user_id = f"{role.value}_{len(users) + 1:03d}"
        hashed_password = self.hash_password(password)
        
        user = User(
            user_id=user_id,
            email=email,
            full_name=full_name,
            role=role,
            class_id=class_id,
            phone=phone,
            created_at=datetime.now(),
            is_active=True
        )
        
        # Сохраняем в базу данных
        users = persistent_storage.get("users", {})
        users[user_id] = {
            **user.dict(),
            "password": hashed_password
        }
        persistent_storage.set("users", users)
        
        return user
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """Аутентифицирует пользователя"""
        hashed_password = self.hash_password(password)
        print(f"DEBUG: Trying to authenticate email: {email}")
        print(f"DEBUG: Password hash: {hashed_password}")
        
        # Ищем пользователя
        users = persistent_storage.get("users", {})
        print(f"DEBUG: Available users: {list(users.keys())}")
        
        for user_id, user_data in users.items():
            print(f"DEBUG: Checking user {user_id}, email: {user_data.get('email')}")
            if user_data.get("email") == email and user_data.get("password") == hashed_password:
                print(f"DEBUG: Password match for user {user_id}")
                if user_data.get("is_active"):
                    token = self.generate_token(user_id, UserRole(user_data["role"]))
                    print(f"DEBUG: Generated token for user {user_id}")
                    return {
                        "token": token,
                        "user_id": user_id,
                        "role": user_data["role"]
                    }
                else:
                    print(f"DEBUG: User {user_id} is not active")
        
        print(f"DEBUG: Authentication failed for email: {email}")
        return None
    
    def get_user_from_token(self, token: str) -> Optional[Dict]:
        """Получает информацию о пользователе из токена"""
        if token in self.sessions:
            session = self.sessions[token]
            user_id = session["user_id"]
            
            if user_id in persistent_storage.get("users", {}):
                user_data = persistent_storage.get("users", {})[user_id]
                return {
                    "user_id": user_id,
                    "email": user_data.get("email"),
                    "full_name": user_data.get("full_name"),
                    "role": user_data.get("role"),
                    "class_id": user_data.get("class_id")
                }
        
        return None
    
    def logout(self, token: str):
        """Выход пользователя"""
        if token in self.sessions:
            del self.sessions[token]
    
    def get_all_users(self) -> List[Dict]:
        """Получить всех пользователей"""
        users_data = persistent_storage.get("users", {})
        print(f"DEBUG: persistent_storage users: {users_data}")
        users = []
        for user_id, user_data in users_data.items():
            # Исключаем пароль из ответа
            user_info = {k: v for k, v in user_data.items() if k != "password"}
            users.append(user_info)
        print(f"DEBUG: returning {len(users)} users")
        return users


# Создаем глобальный экземпляр
auth_service = AuthService()

