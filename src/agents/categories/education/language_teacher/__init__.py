"""
Language Teacher Bot Module

A comprehensive language learning Telegram bot with dual teacher personas:
- ConversationTeacher: Interactive conversational practice
- HomeworkTeacher: Structured exercises and assessments

Features:
- Adaptive learning algorithms
- Gamification system with achievements
- Voice message support for pronunciation
- Spaced repetition vocabulary training
- Progress tracking and analytics
"""

from .language_teacher_agent import LanguageTeacherAgent
from .conversation_teacher import ConversationTeacher
from .homework_teacher import HomeworkTeacher
from .adaptive_learning_system import AdaptiveLearningSystem
from .gamification_system import GamificationSystem

__all__ = [
    'LanguageTeacherAgent',
    'ConversationTeacher',
    'HomeworkTeacher',
    'AdaptiveLearningSystem',
    'GamificationSystem'
]