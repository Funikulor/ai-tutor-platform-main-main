"""
Постоянное хранение данных в JSON файле
"""
import json
import os
from typing import Dict, Any


class PersistentStorage:
    """Класс для постоянного хранения данных"""
    
    def __init__(self, data_file: str = "data.json"):
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_file = os.path.join(backend_dir, data_file)
        self.data = self._load_data()
    
    def _load_data(self) -> Dict[str, Any]:
        """Загружает данные из файла"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return self._get_default_data()
        else:
            return self._get_default_data()
    
    def _get_default_data(self) -> Dict[str, Any]:
        """Возвращает структуру данных по умолчанию"""
        return {
            "users": {},
            "cognitive_profiles": {},
            "student_analytics": {},
            "personality_profiles": {},
            "ethics_message_shown": {},
            "task_history": {},
            "assigned_tasks": {}
        }
    
    def save_data(self):
        """Сохраняет данные в файл"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2, default=str)
        except Exception:
            pass
    
    def get(self, key: str, default=None):
        """Получает значение по ключу"""
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any):
        """Устанавливает значение по ключу"""
        self.data[key] = value
        self.save_data()
    
    def update(self, key: str, updates: Dict[str, Any]):
        """Обновляет данные по ключу"""
        if key not in self.data:
            self.data[key] = {}
        self.data[key].update(updates)
        self.save_data()


# Глобальное хранилище данных
persistent_storage = PersistentStorage()

