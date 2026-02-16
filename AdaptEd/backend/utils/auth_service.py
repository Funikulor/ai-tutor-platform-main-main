"""
Сервис авторизации с поддержкой БД
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from models.auth import User, UserRole
from models.user_db import User as UserDB
from utils.persistent_storage import persistent_storage
from utils.db import get_db, has_db


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
        hashed_password = self.hash_password(admin_password)
        
        # Пробуем создать в БД
        if has_db():
            db = get_db()
            if db:
                try:
                    # Проверяем, не существует ли уже админ
                    existing = db.query(UserDB).filter(
                        (UserDB.user_id == admin_id) | (UserDB.email == admin_email)
                    ).first()
                    
                    if not existing:
                        admin = UserDB(
                            user_id=admin_id,
                            email=admin_email,
                            password_hash=hashed_password,
                            full_name="Системный Администратор",
                            role="admin",
                            class_id=None,
                            phone=None,
                            is_active=True
                        )
                        db.add(admin)
                        db.commit()
                        print(f"[Auth] Создан администратор: {admin_email}")
                except Exception as e:
                    print(f"[Auth] Ошибка создания админа в БД: {e}")
                finally:
                    db.close()
                return
        
        # Fallback на persistent_storage
        if admin_id not in persistent_storage.get("users", {}):
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
        hashed_password = self.hash_password(password)
        
        # Пробуем создать в БД
        if has_db():
            db = get_db()
            if db:
                try:
                    # Проверяем, не существует ли уже пользователь
                    existing = db.query(UserDB).filter(UserDB.email == email).first()
                    if existing:
                        return None
                    
                    # Генерируем user_id
                    count = db.query(UserDB).count()
                    user_id = f"{role.value}_{count + 1:03d}"
                    
                    # Создаем пользователя
                    user_db = UserDB(
                        user_id=user_id,
                        email=email,
                        password_hash=hashed_password,
                        full_name=full_name,
                        role=role.value,
                        class_id=class_id,
                        phone=phone,
                        is_active=True
                    )
                    db.add(user_db)
                    db.commit()
                    
                    # Возвращаем Pydantic модель
                    return User(
                        user_id=user_id,
                        email=email,
                        full_name=full_name,
                        role=role,
                        class_id=class_id,
                        phone=phone,
                        created_at=user_db.created_at,
                        is_active=True
                    )
                except Exception as e:
                    print(f"[Auth] Ошибка регистрации в БД: {e}")
                    db.rollback()
                finally:
                    db.close()
        
        # Fallback на persistent_storage
        users = persistent_storage.get("users", {})
        for user_id, user_data in users.items():
            if user_data.get("email") == email:
                return None
        
        users = persistent_storage.get("users", {})
        user_id = f"{role.value}_{len(users) + 1:03d}"
        
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
        
        users[user_id] = {
            **user.dict(),
            "password": hashed_password
        }
        persistent_storage.set("users", users)
        
        return user
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """Аутентифицирует пользователя"""
        hashed_password = self.hash_password(password)
        
        # Пробуем найти в БД
        if has_db():
            db = get_db()
            if db:
                try:
                    user_db = db.query(UserDB).filter(
                        UserDB.email == email,
                        UserDB.password_hash == hashed_password,
                        UserDB.is_active == True
                    ).first()
                    
                    if user_db:
                        token = self.generate_token(user_db.user_id, UserRole(user_db.role))
                        return {
                            "token": token,
                            "user_id": user_db.user_id,
                            "role": user_db.role
                        }
                except Exception as e:
                    print(f"[Auth] Ошибка аутентификации в БД: {e}")
                finally:
                    db.close()
        
        # Fallback на persistent_storage
        users = persistent_storage.get("users", {})
        for user_id, user_data in users.items():
            if user_data.get("email") == email and user_data.get("password") == hashed_password:
                if user_data.get("is_active"):
                    token = self.generate_token(user_id, UserRole(user_data["role"]))
                    return {
                        "token": token,
                        "user_id": user_id,
                        "role": user_data["role"]
                    }
        
        return None
    
    def get_user_from_token(self, token: str) -> Optional[Dict]:
        """Получает информацию о пользователе из токена"""
        if token not in self.sessions:
            return None
        
        session = self.sessions[token]
        user_id = session["user_id"]
        
        # Пробуем получить из БД
        if has_db():
            db = get_db()
            if db:
                try:
                    user_db = db.query(UserDB).filter(UserDB.user_id == user_id).first()
                    if user_db and user_db.is_active:
                        return {
                            "user_id": user_db.user_id,
                            "email": user_db.email,
                            "full_name": user_db.full_name,
                            "role": user_db.role,
                            "class_id": user_db.class_id,
                            "phone": user_db.phone
                        }
                except Exception as e:
                    print(f"[Auth] Ошибка получения пользователя из БД: {e}")
                finally:
                    db.close()
        
        # Fallback на persistent_storage
        if user_id in persistent_storage.get("users", {}):
            user_data = persistent_storage.get("users", {})[user_id]
            return {
                "user_id": user_id,
                "email": user_data.get("email"),
                "full_name": user_data.get("full_name"),
                "role": user_data.get("role"),
                "class_id": user_data.get("class_id"),
                "phone": user_data.get("phone")
            }
        
        return None
    
    def logout(self, token: str):
        """Выход пользователя"""
        if token in self.sessions:
            del self.sessions[token]
    
    def get_all_users(self) -> List[Dict]:
        """Получить всех пользователей"""
        users = []
        
        # Пробуем получить из БД
        if has_db():
            db = get_db()
            if db:
                try:
                    users_db = db.query(UserDB).all()
                    for user_db in users_db:
                        users.append({
                            "user_id": user_db.user_id,
                            "email": user_db.email,
                            "full_name": user_db.full_name,
                            "role": user_db.role,
                            "class_id": user_db.class_id,
                            "phone": user_db.phone,
                            "is_active": user_db.is_active,
                            "created_at": user_db.created_at.isoformat() if user_db.created_at else None
                        })
                    return users
                except Exception as e:
                    print(f"[Auth] Ошибка получения пользователей из БД: {e}")
                finally:
                    db.close()
        
        # Fallback на persistent_storage
        users_data = persistent_storage.get("users", {})
        for user_id, user_data in users_data.items():
            user_info = {k: v for k, v in user_data.items() if k != "password"}
            users.append(user_info)
        
        return users
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Получить пользователя по ID"""
        # Пробуем получить из БД
        if has_db():
            db = get_db()
            if db:
                try:
                    user_db = db.query(UserDB).filter(UserDB.user_id == user_id).first()
                    if user_db:
                        return {
                            "user_id": user_db.user_id,
                            "email": user_db.email,
                            "full_name": user_db.full_name,
                            "role": user_db.role,
                            "class_id": user_db.class_id,
                            "phone": user_db.phone,
                            "is_active": user_db.is_active,
                            "created_at": user_db.created_at.isoformat() if user_db.created_at else None
                        }
                except Exception as e:
                    print(f"[Auth] Ошибка получения пользователя из БД: {e}")
                finally:
                    db.close()
        
        # Fallback на persistent_storage
        users = persistent_storage.get("users", {})
        if user_id in users:
            user_data = users[user_id]
            return {k: v for k, v in user_data.items() if k != "password"}
        
        return None


# Создаем глобальный экземпляр
auth_service = AuthService()

