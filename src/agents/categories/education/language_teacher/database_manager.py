"""
Database Manager for Language Teacher Agent.
Handles all database operations for user profiles, progress, and learning data.
"""

import json
import sqlite3
import aiosqlite
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from src.log_service import get_logger


@dataclass
class UserProfile:
    """User profile data structure."""
    user_id: int
    username: Optional[str] = None
    target_language: str = 'english'
    proficiency_level: str = 'beginner'
    native_language: str = 'english'
    created_at: datetime = None
    last_active: datetime = None
    learning_preferences: Dict[str, Any] = None
    streak_count: int = 0
    total_sessions: int = 0
    total_study_minutes: int = 0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_active is None:
            self.last_active = datetime.now()
        if self.learning_preferences is None:
            self.learning_preferences = {
                'session_length': 15,
                'focus_areas': [],
                'reminder_time': None,
                'difficulty_preference': 'adaptive'
            }


@dataclass
class LearningSession:
    """Learning session data structure."""
    session_id: str
    user_id: int
    session_type: str  # 'conversation', 'homework', 'assessment'
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: int = 0
    activities_completed: int = 0
    accuracy_rate: float = 0.0
    vocabulary_introduced: List[str] = None
    errors_corrected: List[Dict] = None
    achievements_unlocked: List[str] = None
    
    def __post_init__(self):
        if self.vocabulary_introduced is None:
            self.vocabulary_introduced = []
        if self.errors_corrected is None:
            self.errors_corrected = []
        if self.achievements_unlocked is None:
            self.achievements_unlocked = []


@dataclass
class ProgressEntry:
    """Individual progress entry."""
    entry_id: str
    user_id: int
    timestamp: datetime
    activity_type: str
    skill_area: str
    difficulty_level: float
    performance_score: float
    time_spent_seconds: int
    correct_responses: int
    total_responses: int
    vocabulary_used: List[str] = None
    
    def __post_init__(self):
        if self.vocabulary_used is None:
            self.vocabulary_used = []


class DatabaseManager:
    """
    Database Manager for Language Teacher Agent.
    Handles SQLite database operations for user data, progress tracking, and analytics.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize database manager."""
        self.logger = get_logger("language_teacher_db")
        self.config = config or {}
        
        # Database configuration
        self.db_path = self.config.get('db_path', 'language_teacher.db')
        self.connection_pool_size = self.config.get('connection_pool_size', 5)
        
        # Database connection
        self.db_connection: Optional[aiosqlite.Connection] = None
        
        self.logger.info(f"DatabaseManager initialized with db_path: {self.db_path}")
    
    async def initialize(self) -> bool:
        """Initialize database and create tables."""
        try:
            self.logger.info("Initializing database...")
            
            # Create database connection
            self.db_connection = await aiosqlite.connect(self.db_path)
            
            # Enable foreign keys
            await self.db_connection.execute("PRAGMA foreign_keys = ON")
            
            # Create tables
            await self._create_tables()
            
            # Create indexes
            await self._create_indexes()
            
            await self.db_connection.commit()
            
            self.logger.info("Database initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            return False
    
    async def _create_tables(self) -> None:
        """Create all necessary database tables."""
        
        # User profiles table
        await self.db_connection.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                target_language TEXT NOT NULL DEFAULT 'english',
                proficiency_level TEXT NOT NULL DEFAULT 'beginner',
                native_language TEXT NOT NULL DEFAULT 'english',
                created_at TEXT NOT NULL,
                last_active TEXT NOT NULL,
                learning_preferences TEXT,
                streak_count INTEGER DEFAULT 0,
                total_sessions INTEGER DEFAULT 0,
                total_study_minutes INTEGER DEFAULT 0
            )
        """)
        
        # Learning sessions table
        await self.db_connection.execute("""
            CREATE TABLE IF NOT EXISTS learning_sessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                session_type TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                duration_minutes INTEGER DEFAULT 0,
                activities_completed INTEGER DEFAULT 0,
                accuracy_rate REAL DEFAULT 0.0,
                vocabulary_introduced TEXT,
                errors_corrected TEXT,
                achievements_unlocked TEXT,
                FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
            )
        """)
        
        # Progress entries table
        await self.db_connection.execute("""
            CREATE TABLE IF NOT EXISTS progress_entries (
                entry_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                skill_area TEXT NOT NULL,
                difficulty_level REAL NOT NULL,
                performance_score REAL NOT NULL,
                time_spent_seconds INTEGER NOT NULL,
                correct_responses INTEGER NOT NULL,
                total_responses INTEGER NOT NULL,
                vocabulary_used TEXT,
                FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
            )
        """)
        
        # Vocabulary progress table
        await self.db_connection.execute("""
            CREATE TABLE IF NOT EXISTS vocabulary_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                word TEXT NOT NULL,
                language TEXT NOT NULL,
                first_encountered TEXT NOT NULL,
                last_practiced TEXT NOT NULL,
                practice_count INTEGER DEFAULT 1,
                mastery_level REAL DEFAULT 0.0,
                next_review_date TEXT,
                FOREIGN KEY (user_id) REFERENCES user_profiles (user_id),
                UNIQUE(user_id, word, language)
            )
        """)
        
        # Achievement progress table
        await self.db_connection.execute("""
            CREATE TABLE IF NOT EXISTS achievement_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_type TEXT NOT NULL,
                achievement_name TEXT NOT NULL,
                progress_value REAL DEFAULT 0.0,
                target_value REAL NOT NULL,
                unlocked_at TEXT,
                is_unlocked BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (user_id) REFERENCES user_profiles (user_id),
                UNIQUE(user_id, achievement_name)
            )
        """)
        
        # Error patterns table
        await self.db_connection.execute("""
            CREATE TABLE IF NOT EXISTS error_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                error_type TEXT NOT NULL,
                original_text TEXT NOT NULL,
                corrected_text TEXT NOT NULL,
                context TEXT,
                frequency INTEGER DEFAULT 1,
                last_occurrence TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
            )
        """)
        
        # Study streaks table
        await self.db_connection.execute("""
            CREATE TABLE IF NOT EXISTS study_streaks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                streak_date TEXT NOT NULL,
                study_minutes INTEGER DEFAULT 0,
                sessions_completed INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES user_profiles (user_id),
                UNIQUE(user_id, streak_date)
            )
        """)
    
    async def _create_indexes(self) -> None:
        """Create database indexes for better performance."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_profiles_last_active ON user_profiles(last_active)",
            "CREATE INDEX IF NOT EXISTS idx_learning_sessions_user_start ON learning_sessions(user_id, start_time)",
            "CREATE INDEX IF NOT EXISTS idx_progress_entries_user_timestamp ON progress_entries(user_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_vocabulary_progress_user_next_review ON vocabulary_progress(user_id, next_review_date)",
            "CREATE INDEX IF NOT EXISTS idx_achievement_progress_user ON achievement_progress(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_error_patterns_user_type ON error_patterns(user_id, error_type)",
            "CREATE INDEX IF NOT EXISTS idx_study_streaks_user_date ON study_streaks(user_id, streak_date)"
        ]
        
        for index_sql in indexes:
            await self.db_connection.execute(index_sql)
    
    async def create_user_profile(self, user_profile: Dict[str, Any]) -> bool:
        """Create a new user profile."""
        try:
            # Convert datetime objects to strings
            created_at = user_profile.get('created_at', datetime.now())
            last_active = user_profile.get('last_active', datetime.now())
            
            if isinstance(created_at, datetime):
                created_at = created_at.isoformat()
            if isinstance(last_active, datetime):
                last_active = last_active.isoformat()
            
            # Convert learning preferences to JSON
            preferences_json = json.dumps(user_profile.get('learning_preferences', {}))
            
            await self.db_connection.execute("""
                INSERT OR REPLACE INTO user_profiles (
                    user_id, username, target_language, proficiency_level, native_language,
                    created_at, last_active, learning_preferences, streak_count,
                    total_sessions, total_study_minutes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_profile['user_id'],
                user_profile.get('username'),
                user_profile.get('target_language', 'english'),
                user_profile.get('proficiency_level', 'beginner'),
                user_profile.get('native_language', 'english'),
                created_at,
                last_active,
                preferences_json,
                user_profile.get('streak_count', 0),
                user_profile.get('total_sessions', 0),
                user_profile.get('total_study_minutes', 0)
            ))
            
            await self.db_connection.commit()
            
            self.logger.info(f"Created user profile for user {user_profile['user_id']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating user profile: {e}")
            return False
    
    async def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user profile by user ID."""
        try:
            cursor = await self.db_connection.execute("""
                SELECT * FROM user_profiles WHERE user_id = ?
            """, (user_id,))
            
            row = await cursor.fetchone()
            if not row:
                return None
            
            # Convert row to dictionary
            profile = {
                'user_id': row[0],
                'username': row[1],
                'target_language': row[2],
                'proficiency_level': row[3],
                'native_language': row[4],
                'created_at': datetime.fromisoformat(row[5]),
                'last_active': datetime.fromisoformat(row[6]),
                'learning_preferences': json.loads(row[7]) if row[7] else {},
                'streak_count': row[8],
                'total_sessions': row[9],
                'total_study_minutes': row[10]
            }
            
            return profile
            
        except Exception as e:
            self.logger.error(f"Error getting user profile: {e}")
            return None
    
    async def update_user_profile(self, user_id: int, updates: Dict[str, Any]) -> bool:
        """Update user profile with new data."""
        try:
            # Build update query dynamically
            update_fields = []
            values = []
            
            for key, value in updates.items():
                if key in ['created_at', 'last_active'] and isinstance(value, datetime):
                    value = value.isoformat()
                elif key == 'learning_preferences':
                    value = json.dumps(value)
                
                update_fields.append(f"{key} = ?")
                values.append(value)
            
            if not update_fields:
                return False
            
            values.append(user_id)  # For WHERE clause
            
            query = f"""
                UPDATE user_profiles 
                SET {', '.join(update_fields)} 
                WHERE user_id = ?
            """
            
            await self.db_connection.execute(query, values)
            await self.db_connection.commit()
            
            self.logger.debug(f"Updated user profile for user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating user profile: {e}")
            return False
    
    async def record_learning_session(self, session_data: Dict[str, Any]) -> bool:
        """Record a completed learning session."""
        try:
            # Convert datetime objects to strings
            start_time = session_data['start_time']
            end_time = session_data.get('end_time')
            
            if isinstance(start_time, datetime):
                start_time = start_time.isoformat()
            if isinstance(end_time, datetime):
                end_time = end_time.isoformat()
            
            # Convert lists to JSON
            vocabulary_json = json.dumps(session_data.get('vocabulary_introduced', []))
            errors_json = json.dumps(session_data.get('errors_corrected', []))
            achievements_json = json.dumps(session_data.get('achievements_unlocked', []))
            
            await self.db_connection.execute("""
                INSERT OR REPLACE INTO learning_sessions (
                    session_id, user_id, session_type, start_time, end_time,
                    duration_minutes, activities_completed, accuracy_rate,
                    vocabulary_introduced, errors_corrected, achievements_unlocked
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_data['session_id'],
                session_data['user_id'],
                session_data['session_type'],
                start_time,
                end_time,
                session_data.get('duration_minutes', 0),
                session_data.get('activities_completed', 0),
                session_data.get('accuracy_rate', 0.0),
                vocabulary_json,
                errors_json,
                achievements_json
            ))
            
            await self.db_connection.commit()
            
            # Update user totals
            await self._update_user_session_totals(
                session_data['user_id'], 
                session_data.get('duration_minutes', 0)
            )
            
            self.logger.debug(f"Recorded learning session {session_data['session_id']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error recording learning session: {e}")
            return False
    
    async def _update_user_session_totals(self, user_id: int, duration_minutes: int) -> None:
        """Update user's total sessions and study time."""
        await self.db_connection.execute("""
            UPDATE user_profiles 
            SET total_sessions = total_sessions + 1,
                total_study_minutes = total_study_minutes + ?,
                last_active = ?
            WHERE user_id = ?
        """, (duration_minutes, datetime.now().isoformat(), user_id))
        
        await self.db_connection.commit()
    
    async def record_progress_entry(self, progress_data: Dict[str, Any]) -> bool:
        """Record a progress entry for analytics."""
        try:
            timestamp = progress_data.get('timestamp', datetime.now())
            if isinstance(timestamp, datetime):
                timestamp = timestamp.isoformat()
            
            vocabulary_json = json.dumps(progress_data.get('vocabulary_used', []))
            
            await self.db_connection.execute("""
                INSERT INTO progress_entries (
                    entry_id, user_id, timestamp, activity_type, skill_area,
                    difficulty_level, performance_score, time_spent_seconds,
                    correct_responses, total_responses, vocabulary_used
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                progress_data['entry_id'],
                progress_data['user_id'],
                timestamp,
                progress_data['activity_type'],
                progress_data['skill_area'],
                progress_data['difficulty_level'],
                progress_data['performance_score'],
                progress_data['time_spent_seconds'],
                progress_data['correct_responses'],
                progress_data['total_responses'],
                vocabulary_json
            ))
            
            await self.db_connection.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error recording progress entry: {e}")
            return False
    
    async def get_user_sessions(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent learning sessions for user."""
        try:
            cursor = await self.db_connection.execute("""
                SELECT * FROM learning_sessions 
                WHERE user_id = ? 
                ORDER BY start_time DESC 
                LIMIT ?
            """, (user_id, limit))
            
            rows = await cursor.fetchall()
            sessions = []
            
            for row in rows:
                session = {
                    'session_id': row[0],
                    'user_id': row[1],
                    'session_type': row[2],
                    'start_time': datetime.fromisoformat(row[3]),
                    'end_time': datetime.fromisoformat(row[4]) if row[4] else None,
                    'duration_minutes': row[5],
                    'activities_completed': row[6],
                    'accuracy_rate': row[7],
                    'vocabulary_introduced': json.loads(row[8]) if row[8] else [],
                    'errors_corrected': json.loads(row[9]) if row[9] else [],
                    'achievements_unlocked': json.loads(row[10]) if row[10] else []
                }
                sessions.append(session)
            
            return sessions
            
        except Exception as e:
            self.logger.error(f"Error getting user sessions: {e}")
            return []
    
    async def get_user_progress_analytics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive progress analytics for user."""
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Get progress entries
            cursor = await self.db_connection.execute("""
                SELECT * FROM progress_entries 
                WHERE user_id = ? AND timestamp >= ? 
                ORDER BY timestamp ASC
            """, (user_id, start_date.isoformat()))
            
            progress_rows = await cursor.fetchall()
            
            # Get sessions
            cursor = await self.db_connection.execute("""
                SELECT * FROM learning_sessions 
                WHERE user_id = ? AND start_time >= ? 
                ORDER BY start_time ASC
            """, (user_id, start_date.isoformat()))
            
            session_rows = await cursor.fetchall()
            
            # Calculate analytics
            analytics = self._calculate_progress_analytics(progress_rows, session_rows)
            analytics['user_id'] = user_id
            analytics['analysis_period_days'] = days
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Error getting progress analytics: {e}")
            return {'error': 'Failed to get analytics'}
    
    def _calculate_progress_analytics(self, progress_rows: List, session_rows: List) -> Dict[str, Any]:
        """Calculate detailed progress analytics from raw data."""
        analytics = {
            'total_entries': len(progress_rows),
            'total_sessions': len(session_rows),
            'average_accuracy': 0.0,
            'total_study_time': 0,
            'skill_breakdown': {},
            'improvement_trend': 0.0,
            'consistency_score': 0.0,
            'strengths': [],
            'focus_areas': []
        }
        
        if not progress_rows:
            return analytics
        
        # Calculate average accuracy
        total_correct = sum(row[8] for row in progress_rows)  # correct_responses
        total_attempts = sum(row[9] for row in progress_rows)  # total_responses
        
        if total_attempts > 0:
            analytics['average_accuracy'] = total_correct / total_attempts
        
        # Calculate total study time
        analytics['total_study_time'] = sum(row[7] for row in progress_rows)  # time_spent_seconds
        
        # Skill area breakdown
        skill_performance = {}
        for row in progress_rows:
            skill_area = row[4]  # skill_area
            performance_score = row[6]  # performance_score
            
            if skill_area not in skill_performance:
                skill_performance[skill_area] = []
            skill_performance[skill_area].append(performance_score)
        
        for skill, scores in skill_performance.items():
            analytics['skill_breakdown'][skill] = {
                'average_score': sum(scores) / len(scores),
                'attempts': len(scores),
                'improvement': self._calculate_improvement_trend(scores)
            }
        
        # Identify strengths and focus areas
        for skill, data in analytics['skill_breakdown'].items():
            if data['average_score'] >= 0.8:
                analytics['strengths'].append(skill)
            elif data['average_score'] < 0.6:
                analytics['focus_areas'].append(skill)
        
        # Calculate overall improvement trend
        if len(progress_rows) >= 5:  # Need minimum data points
            scores = [row[6] for row in progress_rows]  # performance_score
            analytics['improvement_trend'] = self._calculate_improvement_trend(scores)
        
        return analytics
    
    def _calculate_improvement_trend(self, scores: List[float]) -> float:
        """Calculate improvement trend from scores (simple linear trend)."""
        if len(scores) < 2:
            return 0.0
        
        n = len(scores)
        x_sum = sum(range(n))
        y_sum = sum(scores)
        xy_sum = sum(i * score for i, score in enumerate(scores))
        x_sq_sum = sum(i * i for i in range(n))
        
        # Linear regression slope
        try:
            slope = (n * xy_sum - x_sum * y_sum) / (n * x_sq_sum - x_sum * x_sum)
            return slope
        except ZeroDivisionError:
            return 0.0
    
    async def update_vocabulary_progress(self, user_id: int, word: str, language: str, mastery_change: float) -> None:
        """Update vocabulary mastery progress."""
        try:
            now = datetime.now().isoformat()
            
            # Check if word exists for user
            cursor = await self.db_connection.execute("""
                SELECT mastery_level, practice_count FROM vocabulary_progress 
                WHERE user_id = ? AND word = ? AND language = ?
            """, (user_id, word, language))
            
            row = await cursor.fetchone()
            
            if row:
                # Update existing entry
                new_mastery = min(1.0, max(0.0, row[0] + mastery_change))
                new_count = row[1] + 1
                
                await self.db_connection.execute("""
                    UPDATE vocabulary_progress 
                    SET mastery_level = ?, practice_count = ?, last_practiced = ?
                    WHERE user_id = ? AND word = ? AND language = ?
                """, (new_mastery, new_count, now, user_id, word, language))
            else:
                # Create new entry
                initial_mastery = max(0.0, mastery_change)
                
                await self.db_connection.execute("""
                    INSERT INTO vocabulary_progress (
                        user_id, word, language, first_encountered, last_practiced,
                        practice_count, mastery_level
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (user_id, word, language, now, now, 1, initial_mastery))
            
            await self.db_connection.commit()
            
        except Exception as e:
            self.logger.error(f"Error updating vocabulary progress: {e}")
    
    async def get_vocabulary_for_review(self, user_id: int, language: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get vocabulary words that need review."""
        try:
            cursor = await self.db_connection.execute("""
                SELECT word, mastery_level, last_practiced, practice_count 
                FROM vocabulary_progress 
                WHERE user_id = ? AND language = ? AND mastery_level < 0.9
                ORDER BY last_practiced ASC, mastery_level ASC 
                LIMIT ?
            """, (user_id, language, limit))
            
            rows = await cursor.fetchall()
            vocabulary = []
            
            for row in rows:
                vocab_item = {
                    'word': row[0],
                    'mastery_level': row[1],
                    'last_practiced': datetime.fromisoformat(row[2]),
                    'practice_count': row[3]
                }
                vocabulary.append(vocab_item)
            
            return vocabulary
            
        except Exception as e:
            self.logger.error(f"Error getting vocabulary for review: {e}")
            return []
    
    async def update_study_streak(self, user_id: int) -> int:
        """Update user's study streak and return current streak count."""
        try:
            today = datetime.now().date().isoformat()
            
            # Record today's study
            await self.db_connection.execute("""
                INSERT OR REPLACE INTO study_streaks (user_id, streak_date, study_minutes, sessions_completed)
                VALUES (?, ?, 1, 1)
            """, (user_id, today))
            
            # Calculate current streak
            cursor = await self.db_connection.execute("""
                SELECT streak_date FROM study_streaks 
                WHERE user_id = ? 
                ORDER BY streak_date DESC
            """, (user_id,))
            
            dates = [datetime.fromisoformat(row[0]).date() for row in await cursor.fetchall()]
            
            if not dates:
                streak = 0
            else:
                streak = 1
                current_date = dates[0]
                
                for i in range(1, len(dates)):
                    expected_date = current_date - timedelta(days=i)
                    if dates[i] == expected_date:
                        streak += 1
                    else:
                        break
            
            # Update user profile
            await self.db_connection.execute("""
                UPDATE user_profiles SET streak_count = ? WHERE user_id = ?
            """, (streak, user_id))
            
            await self.db_connection.commit()
            return streak
            
        except Exception as e:
            self.logger.error(f"Error updating study streak: {e}")
            return 0
    
    async def cleanup(self) -> None:
        """Clean up database resources."""
        try:
            if self.db_connection:
                await self.db_connection.close()
            self.logger.info("Database manager cleaned up successfully")
            
        except Exception as e:
            self.logger.error(f"Error during database cleanup: {e}")
    
    async def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user statistics."""
        try:
            # Get basic profile stats
            profile = await self.get_user_profile(user_id)
            if not profile:
                return {}
            
            # Get recent performance
            analytics = await self.get_user_progress_analytics(user_id, days=7)
            
            # Get vocabulary stats
            cursor = await self.db_connection.execute("""
                SELECT COUNT(*), AVG(mastery_level) FROM vocabulary_progress 
                WHERE user_id = ?
            """, (user_id,))
            vocab_row = await cursor.fetchone()
            
            stats = {
                'user_id': user_id,
                'total_sessions': profile['total_sessions'],
                'total_study_minutes': profile['total_study_minutes'],
                'current_streak': profile['streak_count'],
                'current_level': profile['proficiency_level'],
                'target_language': profile['target_language'],
                'account_age_days': (datetime.now() - profile['created_at']).days,
                'words_learned': vocab_row[0] if vocab_row[0] else 0,
                'average_vocabulary_mastery': vocab_row[1] if vocab_row[1] else 0.0,
                'recent_accuracy': analytics.get('average_accuracy', 0.0),
                'improvement_trend': analytics.get('improvement_trend', 0.0),
                'strengths': analytics.get('strengths', []),
                'focus_areas': analytics.get('focus_areas', [])
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting user statistics: {e}")
            return {}