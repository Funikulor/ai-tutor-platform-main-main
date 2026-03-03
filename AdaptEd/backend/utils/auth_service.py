"""
Сервис авторизации с поддержкой БД
"""
import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta
AVATAR_SEED_BYTES = 8  # 16 hex chars for unique avatar
from typing import Optional, Dict, List
from models.auth import User, UserRole
from models.user_db import User as UserDB
from utils.persistent_storage import persistent_storage
from utils.db import get_db, has_db


class AuthService:
    """Сервис для работы с авторизацией"""
    
    def __init__(self):
        self.sessions: Dict[str, dict] = {}  # token -> user_data
        self.token_ttl_hours = int(os.getenv("AUTH_TOKEN_TTL_HOURS", "720"))  # 30 days
        # В продакшене задайте AUTH_SECRET_KEY в Railway Variables.
        self.auth_secret = os.getenv("AUTH_SECRET_KEY") or os.getenv("SECRET_KEY") or "change-me-in-production"
        self._ensure_admin_from_env()
    
    def _ensure_admin_from_env(self):
        """Создаёт или обновляет администратора из переменных окружения (Railway / .env)."""
        admin_email = os.getenv("ADMIN_EMAIL", "").strip()
        admin_password = os.getenv("ADMIN_PASSWORD", "").strip()
        if not admin_email or not admin_password:
            return
        hashed = self.hash_password(admin_password)
        admin_id = "admin_001"
        if has_db():
            db = get_db()
            if db:
                try:
                    existing = db.query(UserDB).filter(
                        (UserDB.user_id == admin_id) | (UserDB.email == admin_email)
                    ).first()
                    if existing:
                        # Обновляем пароль и email/имя из env при каждом старте — чтобы войти с текущими Variables
                        existing.password_hash = hashed
                        existing.email = admin_email
                        existing.full_name = os.getenv("ADMIN_FULL_NAME", "Администратор") or existing.full_name
                        existing.is_active = True
                        db.commit()
                        print(f"[Auth] Обновлён администратор из env: {admin_email}")
                    else:
                        # Нет админа с таким email/id — создаём
                        admin = UserDB(
                            user_id=admin_id,
                            email=admin_email,
                            password_hash=hashed,
                            full_name=os.getenv("ADMIN_FULL_NAME", "Администратор"),
                            role="admin",
                            class_id=None,
                            phone=None,
                            is_active=True
                        )
                        db.add(admin)
                        db.commit()
                        print(f"[Auth] Создан администратор из env: {admin_email}")
                except Exception as e:
                    print(f"[Auth] Ошибка создания/обновления админа из env: {e}")
                finally:
                    db.close()
                return
        users = persistent_storage.get("users", {})
        key = admin_id if admin_id in users else next((k for k, v in users.items() if v.get("email") == admin_email), None)
        if key is not None:
            users[key] = {
                **(users.get(key) or {}),
                "user_id": key,
                "email": admin_email,
                "full_name": os.getenv("ADMIN_FULL_NAME", "Администратор"),
                "role": "admin",
                "class_id": None,
                "phone": None,
                "created_at": (users.get(key) or {}).get("created_at") or datetime.now(),
                "is_active": True,
                "password": hashed
            }
            persistent_storage.set("users", users)
            print(f"[Auth] Обновлён администратор из env (storage): {admin_email}")
        else:
            users[admin_id] = {
                "user_id": admin_id,
                "email": admin_email,
                "full_name": os.getenv("ADMIN_FULL_NAME", "Администратор"),
                "role": "admin",
                "class_id": None,
                "phone": None,
                "created_at": datetime.now(),
                "is_active": True,
                "password": hashed
            }
            persistent_storage.set("users", users)
            print(f"[Auth] Создан администратор из env (storage): {admin_email}")
    
    def hash_password(self, password: str) -> str:
        """Хеширует пароль"""
        return hashlib.sha256(password.encode()).hexdigest()

    def _base64url_encode(self, data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

    def _base64url_decode(self, value: str) -> bytes:
        padding = "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode((value + padding).encode("utf-8"))

    def _sign(self, payload_b64: str) -> str:
        digest = hmac.new(
            self.auth_secret.encode("utf-8"),
            payload_b64.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        return self._base64url_encode(digest)
    
    def generate_token(self, user_id: str, role: UserRole) -> str:
        """Генерирует подписанный stateless токен доступа"""
        role_value = role.value if hasattr(role, "value") else str(role)
        payload = {
            "user_id": user_id,
            "role": role_value,
            "iat": int(datetime.utcnow().timestamp()),
            "exp": int((datetime.utcnow() + timedelta(hours=self.token_ttl_hours)).timestamp()),
        }
        payload_json = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        payload_b64 = self._base64url_encode(payload_json)
        signature_b64 = self._sign(payload_b64)
        return f"{payload_b64}.{signature_b64}"
    
    def register_user(self, email: str, password: str, full_name: str, 
                     role: UserRole, class_id: Optional[str] = None,
                     phone: Optional[str] = None,
                     parent_fio: Optional[str] = None,
                     parent_phone: Optional[str] = None) -> Optional[User]:
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
                    
                    # Генерируем user_id и случайный seed для аватара
                    count = db.query(UserDB).count()
                    user_id = f"{role.value}_{count + 1:03d}"
                    avatar_seed = secrets.token_hex(AVATAR_SEED_BYTES)
                    
                    # Создаем пользователя
                    user_db = UserDB(
                        user_id=user_id,
                        email=email,
                        password_hash=hashed_password,
                        full_name=full_name,
                        role=role.value,
                        class_id=class_id,
                        phone=phone,
                        parent_fio=parent_fio,
                        parent_phone=parent_phone,
                        avatar_seed=avatar_seed,
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
                        parent_fio=parent_fio,
                        parent_phone=parent_phone,
                        avatar_seed=avatar_seed,
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
        avatar_seed = secrets.token_hex(AVATAR_SEED_BYTES)
        
        user = User(
            user_id=user_id,
            email=email,
            full_name=full_name,
            role=role,
            class_id=class_id,
            phone=phone,
            parent_fio=parent_fio,
            parent_phone=parent_phone,
            avatar_seed=avatar_seed,
            created_at=datetime.now(),
            is_active=True
        )
        
        users[user_id] = {
            **user.dict(),
            "password": hashed_password,
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
        user_id = None

        # Backward compatibility: старые in-memory токены
        if token in self.sessions:
            user_id = self.sessions[token]["user_id"]
        else:
            # Новый stateless формат: payload.signature
            try:
                payload_b64, signature_b64 = token.split(".", 1)
            except ValueError:
                return None

            expected_signature = self._sign(payload_b64)
            if not hmac.compare_digest(signature_b64, expected_signature):
                return None

            try:
                payload_raw = self._base64url_decode(payload_b64)
                payload = json.loads(payload_raw.decode("utf-8"))
            except Exception:
                return None

            exp = payload.get("exp")
            user_id = payload.get("user_id")
            if not user_id or not isinstance(exp, int):
                return None
            if exp < int(datetime.utcnow().timestamp()):
                return None
        
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
                            "phone": user_db.phone,
                            "parent_fio": getattr(user_db, 'parent_fio', None),
                            "parent_phone": getattr(user_db, 'parent_phone', None),
                            "avatar_seed": getattr(user_db, 'avatar_seed', None),
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
                "phone": user_data.get("phone"),
                "parent_fio": user_data.get("parent_fio"),
                "parent_phone": user_data.get("parent_phone"),
                "avatar_seed": user_data.get("avatar_seed"),
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
                            "parent_fio": getattr(user_db, 'parent_fio', None),
                            "parent_phone": getattr(user_db, 'parent_phone', None),
                            "avatar_seed": getattr(user_db, 'avatar_seed', None),
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
                            "parent_fio": getattr(user_db, 'parent_fio', None),
                            "parent_phone": getattr(user_db, 'parent_phone', None),
                            "avatar_seed": getattr(user_db, 'avatar_seed', None),
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

    def update_profile(self, user_id: str, full_name: Optional[str] = None, phone: Optional[str] = None,
                      avatar_seed: Optional[str] = None) -> bool:
        """Обновить профиль текущего пользователя (имя, телефон, аватар)."""
        if has_db():
            db = get_db()
            if db:
                try:
                    user_db = db.query(UserDB).filter(UserDB.user_id == user_id).first()
                    if not user_db:
                        return False
                    if full_name is not None:
                        user_db.full_name = full_name
                    if phone is not None:
                        user_db.phone = phone
                    if avatar_seed is not None:
                        user_db.avatar_seed = avatar_seed
                    db.commit()
                    return True
                except Exception as e:
                    print(f"[Auth] Ошибка обновления профиля в БД: {e}")
                    db.rollback()
                    return False
                finally:
                    db.close()
        users = persistent_storage.get("users", {})
        if user_id not in users:
            return False
        u = users[user_id]
        if full_name is not None:
            u["full_name"] = full_name
        if phone is not None:
            u["phone"] = phone
        if avatar_seed is not None:
            u["avatar_seed"] = avatar_seed
        persistent_storage.set("users", users)
        return True

    def set_user_password(self, user_id: str, new_password: str) -> bool:
        """Устанавливает новый пароль пользователю (для админа или смены своего)."""
        if not new_password or len(new_password) < 6:
            return False
        hashed = self.hash_password(new_password)
        if has_db():
            db = get_db()
            if db:
                try:
                    user_db = db.query(UserDB).filter(UserDB.user_id == user_id).first()
                    if not user_db:
                        return False
                    user_db.password_hash = hashed
                    db.commit()
                    return True
                except Exception as e:
                    print(f"[Auth] Ошибка смены пароля в БД: {e}")
                    db.rollback()
                    return False
                finally:
                    db.close()
        users = persistent_storage.get("users", {})
        if user_id not in users:
            return False
        users[user_id]["password"] = hashed
        persistent_storage.set("users", users)
        return True


# Создаем глобальный экземпляр
auth_service = AuthService()

