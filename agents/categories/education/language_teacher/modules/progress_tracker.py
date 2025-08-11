"""
Progress Tracker Module - Tracks user learning progress, streaks, and statistics.
Manages learning analytics and provides detailed progress reports.
"""

import json
import sqlite3
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta, date
from dataclasses import dataclass, field, asdict
from enum import Enum
import os

from src.log_service import get_logger


class ActivityType(Enum):
    """Types of learning activities."""
    CONVERSATION = "conversation"
    HOMEWORK = "homework"
    VOCABULARY = "vocabulary"
    GRAMMAR = "grammar"
    READING = "reading"
    LISTENING = "listening"
    WRITING = "writing"
    ASSESSMENT = "assessment"


@dataclass
class LearningActivity:
    """Individual learning activity record."""
    user_id: int
    activity_type: ActivityType
    timestamp: datetime
    duration_minutes: int = 0
    points_earned: int = 0
    details: Dict[str, Any] = field(default_factory=dict)
    language: str = "english"
    level: str = "beginner"
    session_id: Optional[str] = None


@dataclass
class DailyProgress:
    """Daily progress summary."""
    date: date
    total_minutes: int = 0
    total_activities: int = 0
    points_earned: int = 0
    streak_day: bool = False
    activities: List[LearningActivity] = field(default_factory=list)


@dataclass
class UserProgressStats:
    """Comprehensive user progress statistics."""
    user_id: int
    total_minutes: int = 0
    total_activities: int = 0
    total_points: int = 0
    current_streak: int = 0
    longest_streak: int = 0
    days_active: int = 0
    last_activity: Optional[datetime] = None
    daily_goal_minutes: int = 15
    languages_studied: List[str] = field(default_factory=list)
    favorite_activity: Optional[ActivityType] = None
    weekly_minutes: int = 0
    monthly_minutes: int = 0


class ProgressTracker:
    """
    Tracks and analyzes user learning progress.
    Maintains learning streaks, statistics, and detailed activity logs.
    """
    
    def __init__(self, db_manager=None):
        """Initialize the progress tracker."""
        self.logger = get_logger("progress_tracker")
        
        # Use provided database manager or create own connection
        self.db_manager = db_manager
        self.db_connection: Optional[sqlite3.Connection] = None
        self.db_path = "language_teacher_progress.db"
        
        # Cache for frequent queries
        self.stats_cache: Dict[int, UserProgressStats] = {}
        self.cache_expiry: Dict[int, datetime] = {}
        self.cache_duration = timedelta(minutes=5)
        
    async def initialize(self) -> None:
        """Initialize the progress tracker and database."""
        try:
            if not hasattr(self, 'db_path'):
                self.db_path = "language_teacher_progress.db"
                
            self.db_connection = sqlite3.connect(self.db_path)
            self.db_connection.row_factory = sqlite3.Row
            
            await self._create_tables()
            self.logger.info("Progress Tracker initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Progress Tracker: {e}")
            raise
    
    async def _create_tables(self) -> None:
        """Create necessary database tables."""
        cursor = self.db_connection.cursor()
        
        # Activities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                duration_minutes INTEGER DEFAULT 0,
                points_earned INTEGER DEFAULT 0,
                language TEXT DEFAULT 'english',
                level TEXT DEFAULT 'beginner',
                session_id TEXT,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User progress stats table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_progress_stats (
                user_id INTEGER PRIMARY KEY,
                total_minutes INTEGER DEFAULT 0,
                total_activities INTEGER DEFAULT 0,
                total_points INTEGER DEFAULT 0,
                current_streak INTEGER DEFAULT 0,
                longest_streak INTEGER DEFAULT 0,
                days_active INTEGER DEFAULT 0,
                last_activity TEXT,
                daily_goal_minutes INTEGER DEFAULT 15,
                languages_studied TEXT,
                favorite_activity TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Daily summaries table for streak calculation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_summaries (
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                total_minutes INTEGER DEFAULT 0,
                total_activities INTEGER DEFAULT 0,
                points_earned INTEGER DEFAULT 0,
                streak_day INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, date)
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_user_date ON learning_activities(user_id, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_type ON learning_activities(activity_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_summaries_user_date ON daily_summaries(user_id, date)")
        
        self.db_connection.commit()
    
    async def log_activity(
        self,
        user_id: int,
        activity_type: str,
        details: Optional[Dict[str, Any]] = None,
        duration_minutes: int = 1,
        points: int = 1,
        language: str = "english",
        level: str = "beginner",
        session_id: Optional[str] = None
    ) -> bool:
        """
        Log a learning activity.
        
        Args:
            user_id: User identifier
            activity_type: Type of activity
            details: Additional activity details
            duration_minutes: Duration in minutes
            points: Points earned
            language: Language being studied
            level: User's level
            session_id: Session identifier
            
        Returns:
            True if logged successfully
        """
        try:
            if not self.db_connection:
                await self.initialize()
            
            # Validate activity type
            try:
                activity_enum = ActivityType(activity_type)
            except ValueError:
                activity_enum = ActivityType.CONVERSATION  # Default
            
            # Create activity record
            activity = LearningActivity(
                user_id=user_id,
                activity_type=activity_enum,
                timestamp=datetime.now(),
                duration_minutes=duration_minutes,
                points_earned=points,
                details=details or {},
                language=language,
                level=level,
                session_id=session_id
            )
            
            # Insert into database
            cursor = self.db_connection.cursor()
            cursor.execute("""
                INSERT INTO learning_activities 
                (user_id, activity_type, timestamp, duration_minutes, points_earned, 
                 language, level, session_id, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                activity.user_id,
                activity.activity_type.value,
                activity.timestamp.isoformat(),
                activity.duration_minutes,
                activity.points_earned,
                activity.language,
                activity.level,
                activity.session_id,
                json.dumps(activity.details)
            ))
            
            self.db_connection.commit()
            
            # Update user stats
            await self._update_user_stats(user_id, activity)
            
            # Update daily summary
            await self._update_daily_summary(user_id, activity)
            
            # Clear cache
            if user_id in self.stats_cache:
                del self.stats_cache[user_id]
                del self.cache_expiry[user_id]
            
            self.logger.info(f"Logged activity for user {user_id}: {activity_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to log activity: {e}")
            return False
    
    async def _update_user_stats(self, user_id: int, activity: LearningActivity) -> None:
        """Update user progress statistics."""
        cursor = self.db_connection.cursor()
        
        # Get current stats
        cursor.execute("SELECT * FROM user_progress_stats WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        
        if row:
            # Update existing stats
            stats = UserProgressStats(
                user_id=user_id,
                total_minutes=row['total_minutes'] + activity.duration_minutes,
                total_activities=row['total_activities'] + 1,
                total_points=row['total_points'] + activity.points_earned,
                current_streak=row['current_streak'],
                longest_streak=row['longest_streak'],
                days_active=row['days_active'],
                last_activity=activity.timestamp,
                daily_goal_minutes=row['daily_goal_minutes'],
                languages_studied=json.loads(row['languages_studied'] or '[]'),
                favorite_activity=ActivityType(row['favorite_activity']) if row['favorite_activity'] else None
            )
            
            # Add language if new
            if activity.language not in stats.languages_studied:
                stats.languages_studied.append(activity.language)
            
            # Update favorite activity based on frequency
            stats.favorite_activity = await self._get_favorite_activity(user_id)
            
            # Update in database
            cursor.execute("""
                UPDATE user_progress_stats SET
                    total_minutes = ?, total_activities = ?, total_points = ?,
                    last_activity = ?, languages_studied = ?, favorite_activity = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (
                stats.total_minutes, stats.total_activities, stats.total_points,
                stats.last_activity.isoformat(),
                json.dumps(stats.languages_studied),
                stats.favorite_activity.value if stats.favorite_activity else None,
                user_id
            ))
        else:
            # Create new stats
            cursor.execute("""
                INSERT INTO user_progress_stats 
                (user_id, total_minutes, total_activities, total_points, 
                 last_activity, languages_studied, favorite_activity)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, activity.duration_minutes, 1, activity.points_earned,
                activity.timestamp.isoformat(),
                json.dumps([activity.language]),
                activity.activity_type.value
            ))
        
        self.db_connection.commit()
    
    async def _update_daily_summary(self, user_id: int, activity: LearningActivity) -> None:
        """Update daily summary and calculate streak."""
        today = activity.timestamp.date()
        today_str = today.isoformat()
        
        cursor = self.db_connection.cursor()
        
        # Update or create daily summary
        cursor.execute("""
            INSERT OR REPLACE INTO daily_summaries 
            (user_id, date, total_minutes, total_activities, points_earned, streak_day)
            VALUES (
                ?, ?, 
                COALESCE((SELECT total_minutes FROM daily_summaries WHERE user_id = ? AND date = ?), 0) + ?,
                COALESCE((SELECT total_activities FROM daily_summaries WHERE user_id = ? AND date = ?), 0) + 1,
                COALESCE((SELECT points_earned FROM daily_summaries WHERE user_id = ? AND date = ?), 0) + ?,
                1
            )
        """, (
            user_id, today_str, user_id, today_str, activity.duration_minutes,
            user_id, today_str, user_id, today_str, activity.points_earned
        ))
        
        # Recalculate streak
        await self._recalculate_streak(user_id)
        
        self.db_connection.commit()
    
    async def _recalculate_streak(self, user_id: int) -> None:
        """Recalculate user's learning streak."""
        cursor = self.db_connection.cursor()
        
        # Get all activity days in descending order
        cursor.execute("""
            SELECT date FROM daily_summaries 
            WHERE user_id = ? AND streak_day = 1
            ORDER BY date DESC
        """, (user_id,))
        
        dates = [datetime.fromisoformat(row['date']).date() for row in cursor.fetchall()]
        
        if not dates:
            current_streak = 0
        else:
            # Calculate current streak
            current_streak = 0
            today = date.today()
            
            for i, activity_date in enumerate(dates):
                expected_date = today - timedelta(days=i)
                if activity_date == expected_date:
                    current_streak += 1
                else:
                    # Allow for yesterday if today has no activity
                    if i == 0 and activity_date == today - timedelta(days=1):
                        current_streak += 1
                    else:
                        break
        
        # Calculate longest streak
        longest_streak = 0
        if dates:
            current_sequence = 1
            longest_streak = 1
            
            for i in range(1, len(dates)):
                if dates[i-1] - dates[i] == timedelta(days=1):
                    current_sequence += 1
                    longest_streak = max(longest_streak, current_sequence)
                else:
                    current_sequence = 1
        
        # Update user stats
        cursor.execute("""
            UPDATE user_progress_stats 
            SET current_streak = ?, longest_streak = CASE 
                WHEN longest_streak < ? THEN ? 
                ELSE longest_streak 
            END,
            days_active = (
                SELECT COUNT(DISTINCT date) 
                FROM daily_summaries 
                WHERE user_id = ? AND streak_day = 1
            )
            WHERE user_id = ?
        """, (current_streak, longest_streak, longest_streak, user_id, user_id))
    
    async def _get_favorite_activity(self, user_id: int) -> Optional[ActivityType]:
        """Get user's most frequent activity type."""
        cursor = self.db_connection.cursor()
        cursor.execute("""
            SELECT activity_type, COUNT(*) as count
            FROM learning_activities 
            WHERE user_id = ?
            GROUP BY activity_type
            ORDER BY count DESC
            LIMIT 1
        """, (user_id,))
        
        row = cursor.fetchone()
        if row:
            try:
                return ActivityType(row['activity_type'])
            except ValueError:
                return None
        return None
    
    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user stats - alias for get_user_progress."""
        return await self.get_user_progress(user_id)
    
    async def get_comprehensive_report(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive progress report."""
        progress = await self.get_user_progress(user_id)
        
        # Add additional comprehensive data
        if "error" not in progress:
            # Get activity breakdown
            activities = await self.get_recent_activities(user_id, days=30)
            activity_breakdown = {}
            
            for activity in activities:
                activity_type = activity.activity_type.value
                if activity_type not in activity_breakdown:
                    activity_breakdown[activity_type] = {'count': 0, 'minutes': 0}
                activity_breakdown[activity_type]['count'] += 1
                activity_breakdown[activity_type]['minutes'] += activity.duration_minutes
            
            progress['activity_breakdown'] = activity_breakdown
            progress['learning_streak'] = progress.get('current_streak', 0)
            progress['average_accuracy'] = 0.85  # Placeholder
            progress['avg_response_time'] = 3.2  # Placeholder
            progress['improvement_rate'] = 0.15  # Placeholder
            progress['achievement_points'] = progress.get('total_points', 0)
            progress['badges_count'] = 0  # Placeholder
            progress['milestones_count'] = progress.get('days_active', 0) // 7
            progress['strengths'] = ['conversation', 'vocabulary']
            progress['focus_areas'] = ['grammar', 'pronunciation']
        
        return progress
    
    async def record_interaction(self, user_id: int, interaction_data: Dict[str, Any]) -> bool:
        """Record a user interaction for progress tracking."""
        activity_type = interaction_data.get('type', 'conversation')
        duration = interaction_data.get('duration_minutes', 1)
        points = interaction_data.get('points', 1)
        details = {
            'message_length': interaction_data.get('message_length', 0),
            'response_time': interaction_data.get('response_time'),
            'exercise_completed': interaction_data.get('exercise_completed', False)
        }
        
        return await self.log_activity(
            user_id=user_id,
            activity_type=activity_type,
            details=details,
            duration_minutes=duration,
            points=points
        )
    
    async def get_user_progress(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user progress information."""
        try:
            # Check cache
            if (user_id in self.stats_cache and 
                user_id in self.cache_expiry and
                datetime.now() < self.cache_expiry[user_id]):
                stats = self.stats_cache[user_id]
            else:
                stats = await self._fetch_user_stats(user_id)
                if stats:
                    self.stats_cache[user_id] = stats
                    self.cache_expiry[user_id] = datetime.now() + self.cache_duration
            
            if not stats:
                return {"error": "No progress data found"}
            
            # Get recent activities
            recent_activities = await self.get_recent_activities(user_id, days=7)
            
            # Calculate weekly and monthly minutes
            weekly_minutes = sum(
                activity.duration_minutes 
                for activity in recent_activities 
                if activity.timestamp > datetime.now() - timedelta(days=7)
            )
            
            monthly_minutes = sum(
                activity.duration_minutes 
                for activity in recent_activities 
                if activity.timestamp > datetime.now() - timedelta(days=30)
            )
            
            # Check if daily goal was met today
            today_minutes = sum(
                activity.duration_minutes 
                for activity in recent_activities 
                if activity.timestamp.date() == date.today()
            )
            
            return {
                "total_minutes": stats.total_minutes,
                "total_activities": stats.total_activities,
                "total_points": stats.total_points,
                "current_streak": stats.current_streak,
                "longest_streak": stats.longest_streak,
                "days_active": stats.days_active,
                "last_activity": stats.last_activity.isoformat() if stats.last_activity else None,
                "daily_goal_minutes": stats.daily_goal_minutes,
                "daily_goal_met": today_minutes >= stats.daily_goal_minutes,
                "daily_minutes": today_minutes,
                "weekly_minutes": weekly_minutes,
                "monthly_minutes": monthly_minutes,
                "languages_studied": stats.languages_studied,
                "favorite_activity": stats.favorite_activity.value if stats.favorite_activity else None,
                "recent_activity": self._format_recent_activity(recent_activities[:5])
            }
            
        except Exception as e:
            self.logger.error(f"Error getting user progress: {e}")
            return {"error": "Failed to fetch progress data"}
    
    async def _fetch_user_stats(self, user_id: int) -> Optional[UserProgressStats]:
        """Fetch user statistics from database."""
        if not self.db_connection:
            await self.initialize()
        
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT * FROM user_progress_stats WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return UserProgressStats(
            user_id=user_id,
            total_minutes=row['total_minutes'],
            total_activities=row['total_activities'],
            total_points=row['total_points'],
            current_streak=row['current_streak'],
            longest_streak=row['longest_streak'],
            days_active=row['days_active'],
            last_activity=datetime.fromisoformat(row['last_activity']) if row['last_activity'] else None,
            daily_goal_minutes=row['daily_goal_minutes'],
            languages_studied=json.loads(row['languages_studied'] or '[]'),
            favorite_activity=ActivityType(row['favorite_activity']) if row['favorite_activity'] else None
        )
    
    async def get_recent_activities(
        self, 
        user_id: int, 
        days: int = 7,
        limit: int = 50
    ) -> List[LearningActivity]:
        """Get recent learning activities for a user."""
        try:
            if not self.db_connection:
                await self.initialize()
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT * FROM learning_activities 
                WHERE user_id = ? AND timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (user_id, cutoff_date.isoformat(), limit))
            
            activities = []
            for row in cursor.fetchall():
                activity = LearningActivity(
                    user_id=row['user_id'],
                    activity_type=ActivityType(row['activity_type']),
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    duration_minutes=row['duration_minutes'],
                    points_earned=row['points_earned'],
                    details=json.loads(row['details'] or '{}'),
                    language=row['language'],
                    level=row['level'],
                    session_id=row['session_id']
                )
                activities.append(activity)
            
            return activities
            
        except Exception as e:
            self.logger.error(f"Error getting recent activities: {e}")
            return []
    
    def _format_recent_activity(self, activities: List[LearningActivity]) -> str:
        """Format recent activities for display."""
        if not activities:
            return "No recent activity"
        
        formatted = []
        for activity in activities:
            time_str = activity.timestamp.strftime("%m/%d %H:%M")
            activity_str = f"{time_str}: {activity.activity_type.value} ({activity.duration_minutes}min, {activity.points_earned}pts)"
            formatted.append(activity_str)
        
        return "\n".join(formatted)
    
    async def get_streak_info(self, user_id: int) -> Dict[str, Any]:
        """Get detailed streak information."""
        stats = await self._fetch_user_stats(user_id)
        
        if not stats:
            return {"current_streak": 0, "longest_streak": 0, "days_active": 0}
        
        return {
            "current_streak": stats.current_streak,
            "longest_streak": stats.longest_streak,
            "days_active": stats.days_active,
            "last_activity": stats.last_activity.isoformat() if stats.last_activity else None
        }
    
    async def set_daily_goal(self, user_id: int, minutes: int) -> bool:
        """Set user's daily learning goal."""
        try:
            if not self.db_connection:
                await self.initialize()
            
            cursor = self.db_connection.cursor()
            
            # Update or create user stats
            cursor.execute("""
                INSERT OR REPLACE INTO user_progress_stats 
                (user_id, daily_goal_minutes, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (user_id, minutes))
            
            self.db_connection.commit()
            
            # Clear cache
            if user_id in self.stats_cache:
                del self.stats_cache[user_id]
                del self.cache_expiry[user_id]
            
            self.logger.info(f"Set daily goal for user {user_id}: {minutes} minutes")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set daily goal: {e}")
            return False
    
    async def get_leaderboard(
        self, 
        timeframe: str = "weekly", 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get leaderboard data."""
        try:
            if not self.db_connection:
                await self.initialize()
            
            if timeframe == "weekly":
                cutoff = datetime.now() - timedelta(days=7)
            elif timeframe == "monthly":
                cutoff = datetime.now() - timedelta(days=30)
            else:
                cutoff = datetime.now() - timedelta(days=365)  # All time
            
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT 
                    user_id,
                    SUM(duration_minutes) as total_minutes,
                    SUM(points_earned) as total_points,
                    COUNT(*) as activities
                FROM learning_activities 
                WHERE timestamp >= ?
                GROUP BY user_id
                ORDER BY total_points DESC, total_minutes DESC
                LIMIT ?
            """, (cutoff.isoformat(), limit))
            
            leaderboard = []
            for i, row in enumerate(cursor.fetchall(), 1):
                leaderboard.append({
                    "rank": i,
                    "user_id": row['user_id'],
                    "total_minutes": row['total_minutes'],
                    "total_points": row['total_points'],
                    "activities": row['activities']
                })
            
            return leaderboard
            
        except Exception as e:
            self.logger.error(f"Error getting leaderboard: {e}")
            return []
    
    async def cleanup(self) -> None:
        """Clean up progress tracker resources."""
        try:
            if self.db_connection:
                self.db_connection.close()
                self.db_connection = None
            
            self.stats_cache.clear()
            self.cache_expiry.clear()
            
            self.logger.info("Progress Tracker cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up Progress Tracker: {e}")
    
    def __del__(self):
        """Destructor to ensure database connection is closed."""
        if hasattr(self, 'db_connection') and self.db_connection:
            self.db_connection.close()