"""
Shared interfaces for Language Teacher Bot components.
Defines contracts between different agents and components.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum


class SkillType(Enum):
    """Language skills being tracked."""
    READING = "reading"
    WRITING = "writing"
    SPEAKING = "speaking"
    LISTENING = "listening"
    VOCABULARY = "vocabulary"
    GRAMMAR = "grammar"


class ProficiencyLevel(Enum):
    """User proficiency levels."""
    BEGINNER = "beginner"
    ELEMENTARY = "elementary"
    INTERMEDIATE = "intermediate"
    UPPER_INTERMEDIATE = "upper_intermediate"
    ADVANCED = "advanced"
    PROFICIENT = "proficient"


class SessionType(Enum):
    """Types of learning sessions."""
    CONVERSATION = "conversation"
    HOMEWORK = "homework"
    TEST = "test"
    VOCABULARY_DRILL = "vocabulary_drill"
    GRAMMAR_PRACTICE = "grammar_practice"


class TeacherType(Enum):
    """Available teacher personas."""
    CONVERSATION_TEACHER = "conversation_teacher"
    HOMEWORK_TEACHER = "homework_teacher"


@dataclass
class UserProfile:
    """Complete user profile for language learning."""
    user_id: int
    telegram_chat_id: int
    username: Optional[str]
    first_name: Optional[str]
    target_language: str
    native_language: str
    proficiency_level: ProficiencyLevel
    learning_goals: List[str]
    preferred_teacher: Optional[TeacherType]
    daily_goal_minutes: int
    timezone: str
    created_at: datetime
    last_active: datetime
    total_xp: int = 0
    current_streak: int = 0
    longest_streak: int = 0


@dataclass
class LearningProgress:
    """User progress for a specific skill."""
    user_id: int
    skill_type: SkillType
    current_level: float  # 0-100 scale
    xp_points: int
    exercises_completed: int
    correct_answers: int
    total_attempts: int
    last_practiced: Optional[datetime]
    mastery_percentage: float  # 0-1 scale
    
    @property
    def accuracy(self) -> float:
        """Calculate accuracy percentage."""
        if self.total_attempts == 0:
            return 0.0
        return self.correct_answers / self.total_attempts


@dataclass
class UserSession:
    """Active learning session state."""
    session_id: str
    user_id: int
    session_type: SessionType
    current_teacher: TeacherType
    session_state: Dict[str, Any]
    started_at: datetime
    last_activity: datetime
    exercises_completed: int = 0
    current_exercise: Optional[Dict[str, Any]] = None
    is_active: bool = True


@dataclass
class Exercise:
    """Learning exercise definition."""
    exercise_id: str
    exercise_type: str
    skill_type: SkillType
    difficulty_level: float  # 0-1 scale
    content: Dict[str, Any]
    expected_answer: Union[str, List[str]]
    hints: List[str]
    explanation: Optional[str]
    time_limit_seconds: Optional[int]
    points_value: int


@dataclass
class ExerciseResult:
    """Result of completed exercise."""
    exercise_id: str
    user_id: int
    user_answer: str
    correct_answer: str
    is_correct: bool
    score: float  # 0-1 scale
    time_taken_seconds: int
    hints_used: int
    completed_at: datetime
    feedback_given: Optional[str] = None


@dataclass
class TeacherResponse:
    """Response from teacher persona."""
    message: str
    next_exercise: Optional[Exercise] = None
    feedback: Optional[str] = None
    achievements_unlocked: List[str] = field(default_factory=list)
    session_complete: bool = False
    suggested_break: bool = False
    parse_mode: str = "Markdown"


@dataclass
class FeedbackResponse:
    """Detailed feedback on user input."""
    is_correct: bool
    score: float
    explanation: str
    corrections: List[str]
    encouragement: str
    improvement_tips: List[str]


@dataclass
class Achievement:
    """Gamification achievement."""
    achievement_id: str
    title: str
    description: str
    icon: str
    points_reward: int
    unlock_condition: Dict[str, Any]
    is_unlocked: bool = False
    unlocked_at: Optional[datetime] = None


@dataclass
class LearningPath:
    """Personalized learning path."""
    path_id: str
    user_id: int
    target_level: ProficiencyLevel
    estimated_duration_weeks: int
    current_step: int
    total_steps: int
    steps: List[Dict[str, Any]]
    progress_percentage: float


@dataclass
class SharedContext:
    """Shared context between agents."""
    user_profile: UserProfile
    current_session: Optional[UserSession]
    recent_performance: List[ExerciseResult]
    active_learning_path: Optional[LearningPath]
    pending_achievements: List[Achievement]
    daily_stats: Dict[str, Any]
    preferences: Dict[str, Any]


class TeacherPersona(ABC):
    """Abstract base class for teacher personas."""
    
    @abstractmethod
    async def start_session(self, user_profile: UserProfile, session_type: SessionType) -> TeacherResponse:
        """Start a new learning session with this teacher."""
        pass
    
    @abstractmethod
    async def process_message(self, 
                            message: str, 
                            session: UserSession,
                            context: SharedContext) -> TeacherResponse:
        """Process user message and generate response."""
        pass
    
    @abstractmethod
    async def provide_feedback(self, 
                             user_input: str, 
                             expected: str,
                             exercise: Exercise) -> FeedbackResponse:
        """Provide detailed feedback on user response."""
        pass
    
    @abstractmethod
    async def suggest_next_activity(self, 
                                   user_profile: UserProfile,
                                   context: SharedContext) -> TeacherResponse:
        """Suggest next learning activity."""
        pass
    
    @abstractmethod
    async def end_session(self, 
                         session: UserSession,
                         context: SharedContext) -> TeacherResponse:
        """End the current learning session."""
        pass


class AdaptiveLearningInterface(ABC):
    """Interface for adaptive learning system."""
    
    @abstractmethod
    async def adjust_difficulty(self, 
                              user_id: int, 
                              recent_performance: List[ExerciseResult]) -> float:
        """Adjust difficulty based on user performance."""
        pass
    
    @abstractmethod
    async def get_next_exercise(self, 
                              user_profile: UserProfile,
                              skill_type: SkillType,
                              target_difficulty: Optional[float] = None) -> Exercise:
        """Get next appropriate exercise for user."""
        pass
    
    @abstractmethod
    async def update_learning_path(self, 
                                 user_id: int, 
                                 progress: LearningProgress) -> LearningPath:
        """Update user's learning path based on progress."""
        pass
    
    @abstractmethod
    async def predict_success_rate(self, 
                                 user_id: int, 
                                 exercise: Exercise) -> float:
        """Predict user's success rate for given exercise."""
        pass
    
    @abstractmethod
    async def get_weakness_areas(self, user_id: int) -> List[SkillType]:
        """Identify user's weakness areas for focused practice."""
        pass


class GamificationInterface(ABC):
    """Interface for gamification system."""
    
    @abstractmethod
    async def check_achievements(self, 
                               user_id: int, 
                               event_data: Dict[str, Any]) -> List[Achievement]:
        """Check for newly unlocked achievements."""
        pass
    
    @abstractmethod
    async def update_xp(self, 
                       user_id: int, 
                       points: int,
                       activity_type: str) -> int:
        """Update user XP and return new total."""
        pass
    
    @abstractmethod
    async def update_streak(self, user_id: int) -> int:
        """Update user's daily streak."""
        pass
    
    @abstractmethod
    async def get_leaderboard(self, 
                            user_id: int, 
                            board_type: str = "friends") -> List[Dict[str, Any]]:
        """Get leaderboard data."""
        pass
    
    @abstractmethod
    async def get_daily_challenge(self, user_id: int) -> Optional[Exercise]:
        """Get daily challenge for user."""
        pass


class ProgressTrackerInterface(ABC):
    """Interface for progress tracking."""
    
    @abstractmethod
    async def record_exercise_result(self, result: ExerciseResult) -> None:
        """Record exercise completion result."""
        pass
    
    @abstractmethod
    async def get_user_progress(self, user_id: int) -> Dict[SkillType, LearningProgress]:
        """Get complete progress for all skills."""
        pass
    
    @abstractmethod
    async def get_analytics_data(self, 
                               user_id: int, 
                               days_back: int = 30) -> Dict[str, Any]:
        """Get analytics data for user."""
        pass
    
    @abstractmethod
    async def calculate_proficiency_level(self, user_id: int) -> ProficiencyLevel:
        """Calculate overall proficiency level."""
        pass


@dataclass
class AgentEvent:
    """Event for inter-agent communication."""
    event_type: str
    user_id: int
    data: Dict[str, Any]
    timestamp: datetime
    source_agent: str
    target_agent: Optional[str] = None


class EventBusInterface(ABC):
    """Interface for event-driven communication between agents."""
    
    @abstractmethod
    async def publish(self, event: AgentEvent) -> None:
        """Publish event to event bus."""
        pass
    
    @abstractmethod
    async def subscribe(self, 
                      event_type: str, 
                      callback: callable,
                      agent_id: str) -> None:
        """Subscribe to specific event type."""
        pass
    
    @abstractmethod
    async def unsubscribe(self, event_type: str, agent_id: str) -> None:
        """Unsubscribe from event type."""
        pass


class VoiceProcessorInterface(ABC):
    """Interface for voice message processing."""
    
    @abstractmethod
    async def transcribe_audio(self, audio_file: bytes) -> str:
        """Transcribe audio to text."""
        pass
    
    @abstractmethod
    async def analyze_pronunciation(self, 
                                  audio_file: bytes, 
                                  expected_text: str) -> Dict[str, Any]:
        """Analyze pronunciation accuracy."""
        pass
    
    @abstractmethod
    async def generate_pronunciation_feedback(self, 
                                           analysis: Dict[str, Any]) -> str:
        """Generate pronunciation feedback."""
        pass