"""
Скрипт для проверки сохраненных признаков адаптивного педагога-аналитика
"""
import os
import sys
import json
from dotenv import load_dotenv

# Загружаем .env
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

def check_analytics(user_id: str = None):
    """Проверяет сохраненные признаки для ученика"""
    from services.student_analytics import get_analytics_service
    
    analytics_service = get_analytics_service()
    
    # Если user_id не указан, пробуем получить из переменных окружения или запросить
    if not user_id:
        user_id = os.getenv('TEST_USER_ID') or input("Введите user_id ученика: ").strip()
    
    if not user_id:
        print("[ERROR] user_id не указан")
        return
    
    print(f"\n[INFO] Проверка аналитики для ученика: {user_id}")
    print("=" * 60)
    
    try:
        # Получаем аналитические данные
        analytics_data = analytics_service.get_analytics(user_id)
        
        if not analytics_data:
            print("[WARNING] Данные не найдены для этого ученика")
            return
        
        # Выводим данные в читаемом формате
        print("\n📊 АКАДЕМИЧЕСКИЕ ПРИЗНАКИ:")
        print("-" * 60)
        academic = analytics_data.get('academic_traits', {})
        print(f"  Уровень по математике: {academic.get('math_level', 'не определен')}")
        print(f"  Точность в тестах: {academic.get('test_accuracy', '0%')}")
        print(f"  Слабые темы: {', '.join(academic.get('weak_topics', [])) if academic.get('weak_topics') else 'нет данных'}")
        print(f"  Типичные ошибки: {', '.join(academic.get('typical_errors', [])) if academic.get('typical_errors') else 'нет данных'}")
        if academic.get('task_completion_speed'):
            print(f"  Скорость выполнения заданий: {academic.get('task_completion_speed'):.1f} сек")
        
        print("\n🧠 ПОВЕДЕНЧЕСКИЕ ПРИЗНАКИ:")
        print("-" * 60)
        behavioral = analytics_data.get('behavioral_traits', {})
        print(f"  Стиль обучения: {behavioral.get('learning_style', 'не определен')}")
        print(f"  Уровень мотивации: {behavioral.get('motivation_level', 'не определен')}")
        print(f"  Эмоциональное состояние: {behavioral.get('emotional_state', 'не определен')}")
        print(f"  Стиль взаимодействия: {behavioral.get('interaction_style', 'не определен')}")
        
        print("\n📈 МЕТРИКИ ПРОГРЕССА:")
        print("-" * 60)
        progress = analytics_data.get('progress_metrics', {})
        print(f"  Частота запросов подсказок: {progress.get('hint_requests_frequency', 0)}")
        if progress.get('weekly_progress'):
            print(f"  Недельный прогресс: {len(progress.get('weekly_progress', {}))} записей")
        if progress.get('monthly_progress'):
            print(f"  Месячный прогресс: {len(progress.get('monthly_progress', {}))} записей")
        if progress.get('improvement_areas'):
            print(f"  Области улучшения: {', '.join(progress.get('improvement_areas', []))}")
        if progress.get('strengths'):
            print(f"  Сильные стороны: {', '.join(progress.get('strengths', []))}")
        
        print("\n⚙️ НАСТРОЙКИ:")
        print("-" * 60)
        print(f"  Сбор данных включен: {'Да' if analytics_data.get('data_collection_enabled', True) else 'Нет'}")
        print(f"  Всего взаимодействий: {analytics_data.get('total_interactions', 0)}")
        
        # Выводим полный JSON для детального просмотра
        print("\n📄 ПОЛНЫЕ ДАННЫЕ (JSON):")
        print("-" * 60)
        print(json.dumps(analytics_data, indent=2, ensure_ascii=False))
        
        print("\n" + "=" * 60)
        print("[SUCCESS] Проверка завершена!")
        
    except Exception as e:
        print(f"[ERROR] Ошибка при получении данных: {e}")
        import traceback
        traceback.print_exc()


def check_all_students():
    """Проверяет всех учеников, для которых есть данные"""
    from services.student_analytics import get_analytics_service
    
    analytics_service = get_analytics_service()
    educator = analytics_service.adaptive_educator
    
    print("\n[INFO] Поиск всех учеников с данными...")
    print("=" * 60)
    
    student_ids = list(educator.student_data.keys())
    
    if not student_ids:
        print("[INFO] Данных об учениках не найдено")
        return
    
    print(f"[INFO] Найдено учеников: {len(student_ids)}")
    print("\nСписок учеников:")
    for i, user_id in enumerate(student_ids, 1):
        student_data = educator.get_student_data(user_id)
        if student_data:
            print(f"  {i}. {user_id} - взаимодействий: {student_data.total_interactions}")
    
    print("\nДля просмотра данных конкретного ученика используйте:")
    print("  python check_analytics.py <user_id>")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--all":
            check_all_students()
        else:
            check_analytics(sys.argv[1])
    else:
        check_analytics()












