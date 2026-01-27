"""
Система батчинга сохранений для повышения производительности
Сохраняет изменения пакетами вместо сохранения при каждом обновлении
"""
import threading
import time
from typing import Dict, Callable, Any, Optional
from datetime import datetime
import atexit


class BatchedSaver:
    """
    Управляет батчингом сохранений для различных компонентов
    
    Сохраняет изменения либо:
    - По таймеру (раз в N секунд)
    - По счетчику (после N изменений)
    - Принудительно (flush)
    """
    
    def __init__(self, 
                 save_interval_seconds: float = 5.0,
                 max_batch_size: int = 10,
                 save_callback: Optional[Callable[[str, Any], None]] = None):
        """
        Args:
            save_interval_seconds: Интервал сохранения в секундах (по умолчанию 5 сек)
            max_batch_size: Максимальный размер батча перед принудительным сохранением
            save_callback: Функция для сохранения данных (user_id, data)
        """
        self.save_interval_seconds = save_interval_seconds
        self.max_batch_size = max_batch_size
        self.save_callback = save_callback
        
        # Очередь изменений: {user_id: (data, timestamp)}
        self.pending_changes: Dict[str, tuple] = {}
        self.lock = threading.Lock()
        
        # Статистика
        self.total_saves = 0
        self.total_batches = 0
        self.last_save_time = datetime.now()
        
        # Флаг работы
        self.running = True
        
        # Запускаем фоновый поток для периодического сохранения
        try:
            self.thread = threading.Thread(target=self._periodic_save, daemon=True)
            self.thread.start()
        except Exception as e:
            print(f"[BatchedSaver] Ошибка запуска фонового потока: {e}")
            self.thread = None
        
        # Регистрируем обработчик завершения для финального сохранения
        try:
            atexit.register(self.flush_all)
        except Exception as e:
            print(f"[BatchedSaver] Ошибка регистрации atexit: {e}")
    
    def schedule_save(self, user_id: str, data: Any):
        """
        Планирует сохранение данных для пользователя
        
        Args:
            user_id: ID пользователя
            data: Данные для сохранения
        """
        with self.lock:
            self.pending_changes[user_id] = (data, datetime.now())
            
            # Если накопилось достаточно изменений, сохраняем принудительно
            if len(self.pending_changes) >= self.max_batch_size:
                self._save_batch()
    
    def flush(self, user_id: Optional[str] = None):
        """
        Принудительно сохраняет изменения
        
        Args:
            user_id: Если указан, сохраняет только для этого пользователя
                     Если None, сохраняет все изменения
        """
        with self.lock:
            if user_id:
                if user_id in self.pending_changes:
                    data, _ = self.pending_changes[user_id]
                    if self.save_callback:
                        try:
                            self.save_callback(user_id, data)
                            self.total_saves += 1
                        except Exception as e:
                            print(f"[BatchedSaver] Ошибка при flush для {user_id}: {e}")
                    del self.pending_changes[user_id]
            else:
                self._save_batch()
    
    def flush_all(self):
        """Принудительно сохраняет все изменения (используется при завершении)"""
        self.running = False
        with self.lock:
            self._save_batch()
    
    def _save_batch(self):
        """Сохраняет все накопленные изменения"""
        if not self.pending_changes:
            return
        
        if not self.save_callback:
            return
        
        # Сохраняем все изменения
        for user_id, (data, _) in self.pending_changes.items():
            try:
                self.save_callback(user_id, data)
                self.total_saves += 1
            except Exception as e:
                print(f"[BatchedSaver] Ошибка сохранения для {user_id}: {e}")
        
        self.pending_changes.clear()
        self.total_batches += 1
        self.last_save_time = datetime.now()
    
    def _periodic_save(self):
        """Фоновый поток для периодического сохранения"""
        try:
            while self.running:
                time.sleep(self.save_interval_seconds)
                
                with self.lock:
                    # Проверяем, есть ли изменения старше интервала
                    now = datetime.now()
                    should_save = False
                    
                    for user_id, (_, timestamp) in self.pending_changes.items():
                        elapsed = (now - timestamp).total_seconds()
                        if elapsed >= self.save_interval_seconds:
                            should_save = True
                            break
                    
                    if should_save:
                        self._save_batch()
        except Exception as e:
            print(f"[BatchedSaver] Ошибка в фоновом потоке: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику работы батчера"""
        with self.lock:
            return {
                "total_saves": self.total_saves,
                "total_batches": self.total_batches,
                "pending_changes": len(self.pending_changes),
                "last_save_time": self.last_save_time.isoformat(),
                "save_interval_seconds": self.save_interval_seconds,
                "max_batch_size": self.max_batch_size
            }


# Глобальные экземпляры батчеров для разных компонентов
_profiler_batcher: Optional[BatchedSaver] = None
_analytics_batcher: Optional[BatchedSaver] = None
_personality_batcher: Optional[BatchedSaver] = None


def get_profiler_batcher() -> BatchedSaver:
    """Получить батчер для ProfilerAgent"""
    global _profiler_batcher
    if _profiler_batcher is None:
        from utils.persistent_storage import persistent_storage
        
        def save_profile(user_id: str, profile_data: Any):
            """Callback для сохранения профиля"""
            try:
                profiles_data = persistent_storage.get("cognitive_profiles", {})
                profiles_data[user_id] = profile_data
                persistent_storage.set("cognitive_profiles", profiles_data)
            except Exception as e:
                print(f"[ProfilerBatcher] Ошибка сохранения профиля {user_id}: {e}")
        
        _profiler_batcher = BatchedSaver(
            save_interval_seconds=5.0,
            max_batch_size=10,
            save_callback=save_profile
        )
    return _profiler_batcher


def get_analytics_batcher() -> BatchedSaver:
    """Получить батчер для AdaptiveEducatorAgent"""
    global _analytics_batcher
    if _analytics_batcher is None:
        from utils.persistent_storage import persistent_storage
        
        def save_analytics(user_id: str, data: Any):
            """Callback для сохранения аналитики"""
            try:
                # data может быть либо dict с analytics_data и ethics_flag, либо просто analytics_data
                if isinstance(data, dict) and "analytics_data" in data:
                    # Расширенный формат с флагами этики
                    analytics_data_dict = data["analytics_data"]
                    ethics_flag = data.get("ethics_flag")
                    
                    analytics_storage = persistent_storage.get("student_analytics", {})
                    analytics_storage[user_id] = analytics_data_dict
                    persistent_storage.set("student_analytics", analytics_storage)
                    
                    # Сохраняем флаг этики если есть
                    if ethics_flag is not None:
                        ethics_data = persistent_storage.get("ethics_message_shown", {})
                        ethics_data[user_id] = ethics_flag
                        persistent_storage.set("ethics_message_shown", ethics_data)
                else:
                    # Простой формат - только аналитика
                    analytics_storage = persistent_storage.get("student_analytics", {})
                    analytics_storage[user_id] = data
                    persistent_storage.set("student_analytics", analytics_storage)
            except Exception as e:
                print(f"[AnalyticsBatcher] Ошибка сохранения аналитики {user_id}: {e}")
        
        _analytics_batcher = BatchedSaver(
            save_interval_seconds=5.0,
            max_batch_size=10,
            save_callback=save_analytics
        )
    return _analytics_batcher


def get_personality_batcher() -> BatchedSaver:
    """Получить батчер для PersonalityProfile"""
    global _personality_batcher
    if _personality_batcher is None:
        from utils.persistent_storage import persistent_storage
        
        def save_personality(user_id: str, personality_data: Any):
            """Callback для сохранения профиля личности"""
            try:
                profiles_data = persistent_storage.get("personality_profiles", {})
                profiles_data[user_id] = personality_data
                persistent_storage.set("personality_profiles", profiles_data)
            except Exception as e:
                print(f"[PersonalityBatcher] Ошибка сохранения профиля личности {user_id}: {e}")
        
        _personality_batcher = BatchedSaver(
            save_interval_seconds=5.0,
            max_batch_size=10,
            save_callback=save_personality
        )
    return _personality_batcher

