"""
Database models for Language Teacher Bot.
SQLite-based data access layer with type safety.
"""

import sqlite3
import json
import asyncio
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Union
from pathlib import Path
from contextlib import asynccontextmanager

from ..shared.interfaces import (
    UserProfile, LearningProgress, UserSession, Exercise, ExerciseResult,
    Achievement, LearningPath, SkillType, ProficiencyLevel, SessionType, TeacherType
)


class DatabaseManager:
    """Manages SQLite database connections and operations."""
    
    def __init__(self, db_path: str = "language_teacher.db"):
        self.db_path = Path(db_path)
        self.schema_path = Path(__file__).parent / "schema.sql"
        self._connection = None
        
    async def initialize(self) -> bool:
        """Initialize database with schema."""
        try:
            # Create database directory if it doesn't exist
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Load and execute schema
            with open(self.schema_path, 'r') as f:
                schema_sql = f.read()
            
            async with self.get_connection() as conn:
                await conn.executescript(schema_sql)
                await conn.commit()
                
            return True
            
        except Exception as e:
            print(f"Failed to initialize database: {e}")
            return False
    
    @asynccontextmanager
    async def get_connection(self):
        """Get async database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()


class UserRepository:
    """Repository for user-related database operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def create_user(self, 
                         telegram_chat_id: int,
                         username: Optional[str] = None,
                         first_name: Optional[str] = None,
                         target_language: str = "Spanish",
                         native_language: str = "English") -> UserProfile:
        """Create new user profile."""
        now = datetime.now()
        
        async with self.db.get_connection() as conn:
            cursor = await conn.execute("""
                INSERT INTO users (
                    telegram_chat_id, username, first_name, 
                    target_language, native_language, proficiency_level,
                    learning_goals, created_at, last_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                telegram_chat_id, username, first_name,
                target_language, native_language, "beginner",
                json.dumps(["basic_conversation"]), now, now
            ))
            
            user_id = cursor.lastrowid
            await conn.commit()
            
            # Initialize progress for all skills
            for skill in SkillType:
                await conn.execute("""
                    INSERT INTO learning_progress (user_id, skill_type)
                    VALUES (?, ?)
                """, (user_id, skill.value))
            
            # Create default preferences
            await conn.execute("""
                INSERT INTO user_preferences (user_id) VALUES (?)
            """, (user_id,))
            
            await conn.commit()
            
        return await self.get_user_by_id(user_id)
    
    async def get_user_by_telegram_id(self, telegram_chat_id: int) -> Optional[UserProfile]:
        """Get user by Telegram chat ID."""
        async with self.db.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT * FROM users WHERE telegram_chat_id = ?
            """, (telegram_chat_id,))
            
            row = await cursor.fetchone()
            if not row:
                return None
                
            return self._row_to_user_profile(row)
    
    async def get_user_by_id(self, user_id: int) -> Optional[UserProfile]:
        """Get user by internal user ID."""
        async with self.db.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT * FROM users WHERE user_id = ?
            """, (user_id,))
            
            row = await cursor.fetchone()
            if not row:
                return None
                
            return self._row_to_user_profile(row)
    
    async def update_user(self, user_profile: UserProfile) -> bool:
        """Update user profile."""
        try:
            async with self.db.get_connection() as conn:
                await conn.execute("""
                    UPDATE users SET
                        username = ?, first_name = ?, target_language = ?,
                        native_language = ?, proficiency_level = ?, learning_goals = ?,
                        preferred_teacher = ?, daily_goal_minutes = ?, timezone = ?,
                        total_xp = ?, current_streak = ?, longest_streak = ?,
                        last_active = ?
                    WHERE user_id = ?
                """, (
                    user_profile.username, user_profile.first_name,
                    user_profile.target_language, user_profile.native_language,
                    user_profile.proficiency_level.value, 
                    json.dumps(user_profile.learning_goals),
                    user_profile.preferred_teacher.value if user_profile.preferred_teacher else None,
                    user_profile.daily_goal_minutes, user_profile.timezone,
                    user_profile.total_xp, user_profile.current_streak,
                    user_profile.longest_streak, user_profile.last_active,
                    user_profile.user_id
                ))
                
                await conn.commit()
                return True
                
        except Exception as e:
            print(f"Failed to update user: {e}")
            return False
    
    async def update_last_active(self, user_id: int) -> None:
        """Update user's last active timestamp."""
        async with self.db.get_connection() as conn:
            await conn.execute("""
                UPDATE users SET last_active = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (user_id,))
            await conn.commit()
    
    def _row_to_user_profile(self, row: sqlite3.Row) -> UserProfile:
        """Convert database row to UserProfile."""
        learning_goals = json.loads(row['learning_goals']) if row['learning_goals'] else []
        
        return UserProfile(
            user_id=row['user_id'],
            telegram_chat_id=row['telegram_chat_id'],
            username=row['username'],
            first_name=row['first_name'],
            target_language=row['target_language'],
            native_language=row['native_language'],
            proficiency_level=ProficiencyLevel(row['proficiency_level']),
            learning_goals=learning_goals,
            preferred_teacher=TeacherType(row['preferred_teacher']) if row['preferred_teacher'] else None,
            daily_goal_minutes=row['daily_goal_minutes'],
            timezone=row['timezone'],
            created_at=datetime.fromisoformat(row['created_at']),
            last_active=datetime.fromisoformat(row['last_active']),
            total_xp=row['total_xp'],
            current_streak=row['current_streak'],
            longest_streak=row['longest_streak']
        )


class ProgressRepository:
    """Repository for learning progress operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def get_user_progress(self, user_id: int) -> Dict[SkillType, LearningProgress]:
        """Get all progress for user."""
        async with self.db.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT * FROM learning_progress WHERE user_id = ?
            """, (user_id,))
            
            rows = await cursor.fetchall()
            
            progress = {}
            for row in rows:
                skill_type = SkillType(row['skill_type'])
                progress[skill_type] = LearningProgress(
                    user_id=row['user_id'],
                    skill_type=skill_type,
                    current_level=row['current_level'],
                    xp_points=row['xp_points'],
                    exercises_completed=row['exercises_completed'],
                    correct_answers=row['correct_answers'],
                    total_attempts=row['total_attempts'],
                    last_practiced=datetime.fromisoformat(row['last_practiced']) if row['last_practiced'] else None,
                    mastery_percentage=row['mastery_percentage']
                )
                
            return progress
    
    async def update_progress(self, progress: LearningProgress) -> bool:
        """Update learning progress for a skill."""
        try:
            async with self.db.get_connection() as conn:
                await conn.execute("""
                    UPDATE learning_progress SET
                        current_level = ?, xp_points = ?, exercises_completed = ?,
                        correct_answers = ?, total_attempts = ?, last_practiced = ?,
                        mastery_percentage = ?
                    WHERE user_id = ? AND skill_type = ?
                """, (
                    progress.current_level, progress.xp_points,
                    progress.exercises_completed, progress.correct_answers,
                    progress.total_attempts, progress.last_practiced,
                    progress.mastery_percentage, progress.user_id,
                    progress.skill_type.value
                ))
                
                await conn.commit()
                return True
                
        except Exception as e:
            print(f"Failed to update progress: {e}")
            return False


class SessionRepository:
    """Repository for user session operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def create_session(self, 
                           user_id: int,
                           session_type: SessionType,
                           teacher_type: TeacherType) -> UserSession:
        """Create new user session."""
        import uuid
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        async with self.db.get_connection() as conn:
            await conn.execute("""
                INSERT INTO user_sessions (
                    session_id, user_id, session_type, current_teacher,
                    session_state, started_at, last_activity
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, user_id, session_type.value, teacher_type.value,
                json.dumps({}), now, now
            ))
            
            await conn.commit()
            
        return UserSession(
            session_id=session_id,
            user_id=user_id,
            session_type=session_type,
            current_teacher=teacher_type,
            session_state={},
            started_at=now,
            last_activity=now
        )
    
    async def get_active_session(self, user_id: int) -> Optional[UserSession]:
        """Get user's active session."""
        async with self.db.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT * FROM user_sessions 
                WHERE user_id = ? AND is_active = TRUE
                ORDER BY started_at DESC
                LIMIT 1
            """, (user_id,))
            
            row = await cursor.fetchone()
            if not row:
                return None
                
            return self._row_to_session(row)
    
    async def update_session(self, session: UserSession) -> bool:
        """Update session state."""
        try:
            async with self.db.get_connection() as conn:
                await conn.execute("""
                    UPDATE user_sessions SET
                        session_state = ?, exercises_completed = ?,
                        current_exercise = ?, is_active = ?
                    WHERE session_id = ?
                """, (
                    json.dumps(session.session_state),
                    session.exercises_completed,
                    json.dumps(session.current_exercise) if session.current_exercise else None,
                    session.is_active,
                    session.session_id
                ))
                
                await conn.commit()
                return True
                
        except Exception as e:
            print(f"Failed to update session: {e}")
            return False
    
    async def end_session(self, session_id: str) -> bool:
        """End a session."""
        try:
            async with self.db.get_connection() as conn:
                await conn.execute("""
                    UPDATE user_sessions SET
                        is_active = FALSE, ended_at = CURRENT_TIMESTAMP
                    WHERE session_id = ?
                """, (session_id,))
                
                await conn.commit()
                return True
                
        except Exception as e:
            print(f"Failed to end session: {e}")
            return False
    
    def _row_to_session(self, row: sqlite3.Row) -> UserSession:
        """Convert database row to UserSession."""
        return UserSession(
            session_id=row['session_id'],
            user_id=row['user_id'],
            session_type=SessionType(row['session_type']),
            current_teacher=TeacherType(row['current_teacher']),
            session_state=json.loads(row['session_state']) if row['session_state'] else {},
            started_at=datetime.fromisoformat(row['started_at']),
            last_activity=datetime.fromisoformat(row['last_activity']),
            exercises_completed=row['exercises_completed'],
            current_exercise=json.loads(row['current_exercise']) if row['current_exercise'] else None,
            is_active=bool(row['is_active'])
        )


class ExerciseRepository:
    """Repository for exercise operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def get_exercise_by_id(self, exercise_id: str) -> Optional[Exercise]:
        """Get exercise by ID."""
        async with self.db.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT * FROM exercises WHERE exercise_id = ?
            """, (exercise_id,))
            
            row = await cursor.fetchone()
            if not row:
                return None
                
            return self._row_to_exercise(row)
    
    async def get_exercises_by_criteria(self,
                                      skill_type: SkillType,
                                      difficulty_min: float = 0.0,
                                      difficulty_max: float = 1.0,
                                      limit: int = 10) -> List[Exercise]:
        """Get exercises matching criteria."""
        async with self.db.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT * FROM exercises 
                WHERE skill_type = ? 
                AND difficulty_level >= ? 
                AND difficulty_level <= ?
                ORDER BY RANDOM()
                LIMIT ?
            """, (skill_type.value, difficulty_min, difficulty_max, limit))
            
            rows = await cursor.fetchall()
            return [self._row_to_exercise(row) for row in rows]
    
    async def record_exercise_result(self, result: ExerciseResult) -> bool:
        """Record exercise completion result."""
        try:
            async with self.db.get_connection() as conn:
                await conn.execute("""
                    INSERT INTO user_exercises (
                        exercise_id, user_id, user_answer, correct_answer,
                        is_correct, score, time_taken_seconds, hints_used,
                        feedback_given, completed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.exercise_id, result.user_id, result.user_answer,
                    result.correct_answer, result.is_correct, result.score,
                    result.time_taken_seconds, result.hints_used,
                    result.feedback_given, result.completed_at
                ))
                
                await conn.commit()
                return True
                
        except Exception as e:
            print(f"Failed to record exercise result: {e}")
            return False
    
    async def get_user_exercise_history(self, 
                                      user_id: int,
                                      days_back: int = 30) -> List[ExerciseResult]:
        """Get user's recent exercise history."""
        async with self.db.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT * FROM user_exercises 
                WHERE user_id = ? 
                AND completed_at >= datetime('now', '-{} days')
                ORDER BY completed_at DESC
            """.format(days_back), (user_id,))
            
            rows = await cursor.fetchall()
            return [self._row_to_exercise_result(row) for row in rows]
    
    def _row_to_exercise(self, row: sqlite3.Row) -> Exercise:
        """Convert database row to Exercise."""
        return Exercise(
            exercise_id=row['exercise_id'],
            exercise_type=row['exercise_type'],
            skill_type=SkillType(row['skill_type']),
            difficulty_level=row['difficulty_level'],
            content=json.loads(row['content']),
            expected_answer=json.loads(row['expected_answer']),
            hints=json.loads(row['hints']) if row['hints'] else [],
            explanation=row['explanation'],
            time_limit_seconds=row['time_limit_seconds'],
            points_value=row['points_value']
        )
    
    def _row_to_exercise_result(self, row: sqlite3.Row) -> ExerciseResult:
        """Convert database row to ExerciseResult."""
        return ExerciseResult(
            exercise_id=row['exercise_id'],
            user_id=row['user_id'],
            user_answer=row['user_answer'],
            correct_answer=row['correct_answer'],
            is_correct=bool(row['is_correct']),
            score=row['score'],
            time_taken_seconds=row['time_taken_seconds'],
            hints_used=row['hints_used'],
            completed_at=datetime.fromisoformat(row['completed_at']),
            feedback_given=row['feedback_given']
        )


class AchievementRepository:
    """Repository for achievement operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def get_user_achievements(self, user_id: int) -> List[Achievement]:
        """Get all achievements for user."""
        async with self.db.get_connection() as conn:
            cursor = await conn.execute("""
                SELECT a.*, ua.unlocked_at
                FROM achievements a
                LEFT JOIN user_achievements ua ON a.achievement_id = ua.achievement_id 
                    AND ua.user_id = ?
            """, (user_id,))
            
            rows = await cursor.fetchall()
            achievements = []
            
            for row in rows:
                achievement = Achievement(
                    achievement_id=row['achievement_id'],
                    title=row['title'],
                    description=row['description'],
                    icon=row['icon'],
                    points_reward=row['points_reward'],
                    unlock_condition=json.loads(row['unlock_condition']),
                    is_unlocked=row['unlocked_at'] is not None,
                    unlocked_at=datetime.fromisoformat(row['unlocked_at']) if row['unlocked_at'] else None
                )
                achievements.append(achievement)
                
            return achievements
    
    async def unlock_achievement(self, user_id: int, achievement_id: str) -> bool:
        """Unlock achievement for user."""
        try:
            async with self.db.get_connection() as conn:
                await conn.execute("""
                    INSERT OR IGNORE INTO user_achievements (user_id, achievement_id)
                    VALUES (?, ?)
                """, (user_id, achievement_id))
                
                await conn.commit()
                return True
                
        except Exception as e:
            print(f"Failed to unlock achievement: {e}")
            return False