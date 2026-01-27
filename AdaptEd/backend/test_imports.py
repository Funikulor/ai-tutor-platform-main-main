"""
Скрипт для проверки импортов и инициализации компонентов
"""
import sys
import traceback

def test_imports():
    """Тестирует импорты всех компонентов"""
    print("=" * 60)
    print("Тестирование импортов...")
    print("=" * 60)
    
    modules = [
        ("utils.persistent_storage", "persistent_storage"),
        ("utils.batched_saver", "get_profiler_batcher"),
        ("models.cognitive_profile", "CognitiveProfile"),
        ("models.student_analytics", "StudentAnalyticsData"),
        ("models.personality_profile", "PersonalityProfile"),
        ("agents.profiler_agent", "ProfilerAgent"),
        ("agents.adaptive_educator_agent", "AdaptiveEducatorAgent"),
        ("services.assistant", "get_assistant_service"),
        ("services.student_analytics", "get_analytics_service"),
        ("agents.orchestrator", "AgentOrchestrator"),
    ]
    
    failed = []
    success = []
    
    for module_name, item_name in modules:
        try:
            print(f"\n[TEST] Импорт {module_name}.{item_name}...")
            module = __import__(module_name, fromlist=[item_name])
            item = getattr(module, item_name)
            print(f"[OK] {module_name}.{item_name} успешно импортирован")
            success.append((module_name, item_name))
        except Exception as e:
            print(f"[ERROR] Ошибка импорта {module_name}.{item_name}: {e}")
            traceback.print_exc()
            failed.append((module_name, item_name, str(e)))
    
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ:")
    print("=" * 60)
    print(f"Успешно: {len(success)}/{len(modules)}")
    print(f"Ошибок: {len(failed)}/{len(modules)}")
    
    if failed:
        print("\nОШИБКИ:")
        for module_name, item_name, error in failed:
            print(f"  - {module_name}.{item_name}: {error}")
        return False
    else:
        print("\nВсе импорты успешны!")
        return True

def test_initialization():
    """Тестирует инициализацию компонентов"""
    print("\n" + "=" * 60)
    print("Тестирование инициализации...")
    print("=" * 60)
    
    try:
        print("\n[TEST] Инициализация ProfilerAgent...")
        from agents.profiler_agent import ProfilerAgent
        profiler = ProfilerAgent()
        print("[OK] ProfilerAgent инициализирован")
    except Exception as e:
        print(f"[ERROR] Ошибка инициализации ProfilerAgent: {e}")
        traceback.print_exc()
        return False
    
    try:
        print("\n[TEST] Инициализация AdaptiveEducatorAgent...")
        from agents.adaptive_educator_agent import AdaptiveEducatorAgent
        educator = AdaptiveEducatorAgent()
        print("[OK] AdaptiveEducatorAgent инициализирован")
    except Exception as e:
        print(f"[ERROR] Ошибка инициализации AdaptiveEducatorAgent: {e}")
        traceback.print_exc()
        return False
    
    try:
        print("\n[TEST] Инициализация AssistantService...")
        from services.assistant import get_assistant_service
        assistant = get_assistant_service()
        print("[OK] AssistantService инициализирован")
    except Exception as e:
        print(f"[ERROR] Ошибка инициализации AssistantService: {e}")
        traceback.print_exc()
        return False
    
    try:
        print("\n[TEST] Инициализация AgentOrchestrator...")
        from agents.orchestrator import AgentOrchestrator
        orchestrator = AgentOrchestrator()
        print("[OK] AgentOrchestrator инициализирован")
    except Exception as e:
        print(f"[ERROR] Ошибка инициализации AgentOrchestrator: {e}")
        traceback.print_exc()
        return False
    
    print("\n[OK] Все компоненты успешно инициализированы!")
    return True

if __name__ == "__main__":
    print("Проверка импортов и инициализации компонентов\n")
    
    imports_ok = test_imports()
    if not imports_ok:
        print("\n[ERROR] Есть ошибки импорта. Исправьте их перед запуском.")
        sys.exit(1)
    
    init_ok = test_initialization()
    if not init_ok:
        print("\n[ERROR] Есть ошибки инициализации. Исправьте их перед запуском.")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("[SUCCESS] Все тесты пройдены! Приложение готово к запуску.")
    print("=" * 60)



