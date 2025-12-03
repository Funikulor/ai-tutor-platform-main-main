"""
Пакет ИИ-агентов для AdaptEd
"""

from .base_agent import BaseAgent, AgentMessage
from .error_analyzer_agent import ErrorAnalyzerAgent
from .profiler_agent import ProfilerAgent
from .task_generator_agent import TaskGeneratorAgent
from .mentor_agent import MentorAgent
from .teacher_analytics_agent import TeacherAnalyticsAgent
from .orchestrator import AgentOrchestrator

__all__ = [
    'BaseAgent',
    'AgentMessage',
    'ErrorAnalyzerAgent',
    'ProfilerAgent',
    'TaskGeneratorAgent',
    'MentorAgent',
    'TeacherAnalyticsAgent',
    'AgentOrchestrator'
]

