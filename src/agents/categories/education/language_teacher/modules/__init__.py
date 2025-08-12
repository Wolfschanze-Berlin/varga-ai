"""
Core modules for language learning functionality.
Provides progress tracking, achievements, and exercise generation.
"""

from .progress_tracker import ProgressTracker
from .achievement_system import AchievementSystem
from .exercise_generator import ExerciseGenerator

__all__ = ["ProgressTracker", "AchievementSystem", "ExerciseGenerator"]