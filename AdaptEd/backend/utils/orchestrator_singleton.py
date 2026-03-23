"""
Единый экземпляр AgentOrchestrator на процесс.
Иначе маршруты (например agents vs homework) держали разные ProfilerAgent и
topic_mastery не совпадал с графом знаний.
"""

_orchestrator = None


def get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        from agents.orchestrator import AgentOrchestrator

        _orchestrator = AgentOrchestrator()
    return _orchestrator
