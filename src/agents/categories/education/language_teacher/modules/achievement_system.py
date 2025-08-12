"""
Achievement System Module - Manages badges, rewards, and milestones for learners.
Provides gamification elements to motivate continued learning.
"""

import json
import sqlite3
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta, date
from dataclasses import dataclass, field, asdict
from enum import Enum
import os

from src.log_service import get_logger


class AchievementCategory(Enum):
    """Categories of achievements."""
    WELCOME = "welcome"
    STREAK = "streak"
    ACTIVITY = "activity"
    SKILL = "skill"
    MILESTONE = "milestone"
    DEDICATION = "dedication"
    EXPLORATION = "exploration"
    MASTERY = "mastery"


class AchievementRarity(Enum):
    """Rarity levels for achievements."""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


@dataclass
class Achievement:
    """Achievement definition."""
    id: str
    name: str
    description: str
    category: AchievementCategory
    rarity: AchievementRarity
    icon: str
    points: int
    condition: Dict[str, Any]
    hidden: bool = False
    prerequisite_achievement: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class UserAchievement:
    """User's earned achievement."""
    user_id: int
    achievement_id: str
    earned_at: datetime
    progress_data: Dict[str, Any] = field(default_factory=dict)


class AchievementSystem:
    """
    Manages user achievements, badges, and rewards.
    Provides gamification elements to encourage learning engagement.
    """
    
    def __init__(self, db_manager=None):
        """Initialize the achievement system."""
        self.logger = get_logger("achievement_system")
        
        # Use provided database manager or create own connection
        self.db_manager = db_manager
        self.db_connection: Optional[sqlite3.Connection] = None
        self.db_path = "language_teacher_achievements.db"
        
        # Achievement definitions
        self.achievements: Dict[str, Achievement] = {}
        self.achievement_checkers: Dict[str, Callable] = {}
        
        # Cache for user achievements
        self.user_achievements_cache: Dict[int, List[UserAchievement]] = {}
        self.cache_expiry: Dict[int, datetime] = {}
        self.cache_duration = timedelta(minutes=10)
    
    async def initialize(self) -> None:
        """Initialize the achievement system and database."""
        try:
            if not hasattr(self, 'db_path'):
                self.db_path = "language_teacher_achievements.db"
                
            self.db_connection = sqlite3.connect(self.db_path)
            self.db_connection.row_factory = sqlite3.Row
            
            await self._create_tables()
            await self._initialize_achievements()
            
            self.logger.info("Achievement System initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Achievement System: {e}")
            raise
    
    async def _create_tables(self) -> None:
        """Create necessary database tables."""
        cursor = self.db_connection.cursor()
        
        # Achievements definition table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                rarity TEXT NOT NULL,
                icon TEXT NOT NULL,
                points INTEGER NOT NULL,
                condition_data TEXT,
                hidden INTEGER DEFAULT 0,
                prerequisite_achievement TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User achievements table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_achievements (
                user_id INTEGER NOT NULL,
                achievement_id TEXT NOT NULL,
                earned_at TEXT NOT NULL,
                progress_data TEXT,
                PRIMARY KEY (user_id, achievement_id),
                FOREIGN KEY (achievement_id) REFERENCES achievements(id)
            )
        """)
        
        # Achievement progress tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS achievement_progress (
                user_id INTEGER NOT NULL,
                achievement_id TEXT NOT NULL,
                current_value INTEGER DEFAULT 0,
                target_value INTEGER NOT NULL,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, achievement_id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_achievements_user ON user_achievements(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_achievements_category ON achievements(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_progress_user ON achievement_progress(user_id)")
        
        self.db_connection.commit()
    
    async def _initialize_achievements(self) -> None:
        """Initialize the default achievement set."""
        
        # Welcome achievements
        await self._add_achievement(Achievement(
            id="welcome_aboard",
            name="Welcome Aboard!",
            description="Complete your learning profile setup",
            category=AchievementCategory.WELCOME,
            rarity=AchievementRarity.COMMON,
            icon="🎉",
            points=10,
            condition={"type": "setup_complete"}
        ))
        
        await self._add_achievement(Achievement(
            id="first_steps",
            name="First Steps",
            description="Complete your first learning activity",
            category=AchievementCategory.WELCOME,
            rarity=AchievementRarity.COMMON,
            icon="👶",
            points=10,
            condition={"type": "activity_count", "value": 1}
        ))
        
        # Streak achievements
        await self._add_achievement(Achievement(
            id="streak_3",
            name="Getting Started",
            description="Maintain a 3-day learning streak",
            category=AchievementCategory.STREAK,
            rarity=AchievementRarity.COMMON,
            icon="🔥",
            points=25,
            condition={"type": "streak", "value": 3}
        ))
        
        await self._add_achievement(Achievement(
            id="streak_7",
            name="Week Warrior",
            description="Maintain a 7-day learning streak",
            category=AchievementCategory.STREAK,
            rarity=AchievementRarity.UNCOMMON,
            icon="⚡",
            points=50,
            condition={"type": "streak", "value": 7}
        ))
        
        await self._add_achievement(Achievement(
            id="streak_30",
            name="Monthly Master",
            description="Maintain a 30-day learning streak",
            category=AchievementCategory.STREAK,
            rarity=AchievementRarity.RARE,
            icon="🏅",
            points=200,
            condition={"type": "streak", "value": 30}
        ))
        
        await self._add_achievement(Achievement(
            id="streak_100",
            name="Century Scholar",
            description="Maintain a 100-day learning streak",
            category=AchievementCategory.STREAK,
            rarity=AchievementRarity.LEGENDARY,
            icon="👑",
            points=500,
            condition={"type": "streak", "value": 100}
        ))
        
        # Activity-based achievements
        await self._add_achievement(Achievement(
            id="lessons_10",
            name="Lesson Master",
            description="Complete 10 learning activities",
            category=AchievementCategory.ACTIVITY,
            rarity=AchievementRarity.COMMON,
            icon="📚",
            points=30,
            condition={"type": "activity_count", "value": 10}
        ))
        
        await self._add_achievement(Achievement(
            id="lessons_50",
            name="Dedicated Learner",
            description="Complete 50 learning activities",
            category=AchievementCategory.ACTIVITY,
            rarity=AchievementRarity.UNCOMMON,
            icon="🎓",
            points=100,
            condition={"type": "activity_count", "value": 50}
        ))
        
        await self._add_achievement(Achievement(
            id="conversations_25",
            name="Chatterbox",
            description="Have 25 conversation practice sessions",
            category=AchievementCategory.SKILL,
            rarity=AchievementRarity.UNCOMMON,
            icon="💬",
            points=75,
            condition={"type": "activity_type_count", "activity_type": "conversation", "value": 25}
        ))
        
        await self._add_achievement(Achievement(
            id="homework_20",
            name="Homework Hero",
            description="Complete 20 homework exercises",
            category=AchievementCategory.SKILL,
            rarity=AchievementRarity.UNCOMMON,
            icon="✍️",
            points=75,
            condition={"type": "activity_type_count", "activity_type": "homework", "value": 20}
        ))
        
        # Time-based achievements
        await self._add_achievement(Achievement(
            id="minutes_60",
            name="Hour Scholar",
            description="Study for 60 minutes total",
            category=AchievementCategory.DEDICATION,
            rarity=AchievementRarity.COMMON,
            icon="⏰",
            points=25,
            condition={"type": "total_minutes", "value": 60}
        ))
        
        await self._add_achievement(Achievement(
            id="minutes_300",
            name="Five Hour Club",
            description="Study for 300 minutes total (5 hours)",
            category=AchievementCategory.DEDICATION,
            rarity=AchievementRarity.UNCOMMON,
            icon="⌚",
            points=100,
            condition={"type": "total_minutes", "value": 300}
        ))
        
        await self._add_achievement(Achievement(
            id="minutes_1200",
            name="Marathon Learner",
            description="Study for 1200 minutes total (20 hours)",
            category=AchievementCategory.DEDICATION,
            rarity=AchievementRarity.RARE,
            icon="🏃",
            points=300,
            condition={"type": "total_minutes", "value": 1200}
        ))
        
        # Language exploration
        await self._add_achievement(Achievement(
            id="polyglot_2",
            name="Budding Polyglot",
            description="Study 2 different languages",
            category=AchievementCategory.EXPLORATION,
            rarity=AchievementRarity.UNCOMMON,
            icon="🌍",
            points=100,
            condition={"type": "languages_count", "value": 2}
        ))
        
        await self._add_achievement(Achievement(
            id="polyglot_3",
            name="True Polyglot",
            description="Study 3 different languages",
            category=AchievementCategory.EXPLORATION,
            rarity=AchievementRarity.RARE,
            icon="🗺️",
            points=200,
            condition={"type": "languages_count", "value": 3}
        ))
        
        # Points-based achievements
        await self._add_achievement(Achievement(
            id="points_100",
            name="Centurion",
            description="Earn 100 learning points",
            category=AchievementCategory.MILESTONE,
            rarity=AchievementRarity.UNCOMMON,
            icon="💯",
            points=50,
            condition={"type": "total_points", "value": 100}
        ))
        
        await self._add_achievement(Achievement(
            id="points_500",
            name="Point Master",
            description="Earn 500 learning points",
            category=AchievementCategory.MILESTONE,
            rarity=AchievementRarity.RARE,
            icon="⭐",
            points=100,
            condition={"type": "total_points", "value": 500}
        ))
        
        # Special achievements
        await self._add_achievement(Achievement(
            id="perfect_week",
            name="Perfect Week",
            description="Complete daily goals for 7 consecutive days",
            category=AchievementCategory.MASTERY,
            rarity=AchievementRarity.RARE,
            icon="✨",
            points=150,
            condition={"type": "daily_goals_streak", "value": 7}
        ))
        
        await self._add_achievement(Achievement(
            id="night_owl",
            name="Night Owl",
            description="Study after 10 PM",
            category=AchievementCategory.EXPLORATION,
            rarity=AchievementRarity.COMMON,
            icon="🦉",
            points=15,
            condition={"type": "time_of_day", "hour_after": 22}
        ))
        
        await self._add_achievement(Achievement(
            id="early_bird",
            name="Early Bird",
            description="Study before 7 AM",
            category=AchievementCategory.EXPLORATION,
            rarity=AchievementRarity.COMMON,
            icon="🐦",
            points=15,
            condition={"type": "time_of_day", "hour_before": 7}
        ))
    
    async def _add_achievement(self, achievement: Achievement) -> None:
        """Add an achievement to the system."""
        self.achievements[achievement.id] = achievement
        
        # Store in database
        cursor = self.db_connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO achievements 
            (id, name, description, category, rarity, icon, points, condition_data, 
             hidden, prerequisite_achievement)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            achievement.id,
            achievement.name,
            achievement.description,
            achievement.category.value,
            achievement.rarity.value,
            achievement.icon,
            achievement.points,
            json.dumps(achievement.condition),
            1 if achievement.hidden else 0,
            achievement.prerequisite_achievement
        ))
        
        self.db_connection.commit()
    
    async def check_achievements(
        self, 
        user_id: int, 
        activity_data: Dict[str, Any]
    ) -> List[Achievement]:
        """
        Check and award achievements based on user activity.
        
        Args:
            user_id: User identifier
            activity_data: Data about the activity that triggered the check
            
        Returns:
            List of newly earned achievements
        """
        try:
            newly_earned = []
            
            # Get user's existing achievements
            user_achievements = await self.get_user_achievements(user_id)
            earned_ids = {ach.achievement_id for ach in user_achievements}
            
            # Check each achievement
            for achievement in self.achievements.values():
                if achievement.id in earned_ids:
                    continue  # Already earned
                
                # Check prerequisite
                if (achievement.prerequisite_achievement and 
                    achievement.prerequisite_achievement not in earned_ids):
                    continue
                
                # Check condition
                if await self._check_achievement_condition(user_id, achievement, activity_data):
                    # Award achievement
                    await self.award_achievement(user_id, achievement.id)
                    newly_earned.append(achievement)
                    self.logger.info(f"User {user_id} earned achievement: {achievement.name}")
            
            return newly_earned
            
        except Exception as e:
            self.logger.error(f"Error checking achievements: {e}")
            return []
    
    async def _check_achievement_condition(
        self,
        user_id: int,
        achievement: Achievement,
        activity_data: Dict[str, Any]
    ) -> bool:
        """Check if an achievement condition is met."""
        try:
            condition = achievement.condition
            condition_type = condition.get("type")
            
            if condition_type == "setup_complete":
                return activity_data.get("setup_complete", False)
            
            elif condition_type == "activity_count":
                return await self._check_activity_count(user_id, condition["value"])
            
            elif condition_type == "streak":
                return await self._check_streak(user_id, condition["value"])
            
            elif condition_type == "activity_type_count":
                return await self._check_activity_type_count(
                    user_id, 
                    condition["activity_type"], 
                    condition["value"]
                )
            
            elif condition_type == "total_minutes":
                return await self._check_total_minutes(user_id, condition["value"])
            
            elif condition_type == "total_points":
                return await self._check_total_points(user_id, condition["value"])
            
            elif condition_type == "languages_count":
                return await self._check_languages_count(user_id, condition["value"])
            
            elif condition_type == "daily_goals_streak":
                return await self._check_daily_goals_streak(user_id, condition["value"])
            
            elif condition_type == "time_of_day":
                current_hour = datetime.now().hour
                if "hour_after" in condition:
                    return current_hour >= condition["hour_after"]
                elif "hour_before" in condition:
                    return current_hour <= condition["hour_before"]
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking achievement condition: {e}")
            return False
    
    async def _check_activity_count(self, user_id: int, target: int) -> bool:
        """Check if user has completed enough activities."""
        cursor = self.db_connection.cursor()
        
        # Check from progress tracker database (assuming it's available)
        try:
            # This would query the progress tracker's database
            # For now, simulate by checking our activity records if we had them
            cursor.execute("""
                SELECT COUNT(*) FROM user_achievements 
                WHERE user_id = ? AND achievement_id LIKE 'activity_%'
            """, (user_id,))
            
            # This is a simplified check - in practice, we'd query the progress tracker
            return cursor.fetchone()[0] >= target
        except:
            return False
    
    async def _check_streak(self, user_id: int, target: int) -> bool:
        """Check if user has the required streak."""
        # This would integrate with the progress tracker
        # For now, return False as we can't check without the actual progress data
        return False
    
    async def _check_activity_type_count(
        self, 
        user_id: int, 
        activity_type: str, 
        target: int
    ) -> bool:
        """Check activity type count."""
        # This would integrate with the progress tracker
        return False
    
    async def _check_total_minutes(self, user_id: int, target: int) -> bool:
        """Check total minutes studied."""
        # This would integrate with the progress tracker
        return False
    
    async def _check_total_points(self, user_id: int, target: int) -> bool:
        """Check total points earned."""
        cursor = self.db_connection.cursor()
        cursor.execute("""
            SELECT SUM(a.points) FROM user_achievements ua
            JOIN achievements a ON ua.achievement_id = a.id
            WHERE ua.user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        total_points = result[0] if result and result[0] else 0
        
        return total_points >= target
    
    async def _check_languages_count(self, user_id: int, target: int) -> bool:
        """Check number of languages studied."""
        # This would integrate with the progress tracker
        return False
    
    async def _check_daily_goals_streak(self, user_id: int, target: int) -> bool:
        """Check daily goals streak."""
        # This would integrate with the progress tracker
        return False
    
    async def award_achievement(self, user_id: int, achievement_id: str) -> bool:
        """Award an achievement to a user."""
        try:
            if achievement_id not in self.achievements:
                self.logger.error(f"Achievement {achievement_id} not found")
                return False
            
            # Check if already earned
            user_achievements = await self.get_user_achievements(user_id)
            if any(ach.achievement_id == achievement_id for ach in user_achievements):
                return True  # Already earned
            
            # Award achievement
            cursor = self.db_connection.cursor()
            cursor.execute("""
                INSERT INTO user_achievements (user_id, achievement_id, earned_at)
                VALUES (?, ?, ?)
            """, (user_id, achievement_id, datetime.now().isoformat()))
            
            self.db_connection.commit()
            
            # Clear cache
            if user_id in self.user_achievements_cache:
                del self.user_achievements_cache[user_id]
                del self.cache_expiry[user_id]
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error awarding achievement: {e}")
            return False
    
    async def unlock_achievement(
        self,
        user_id: int,
        achievement_id: str,
        custom_description: Optional[str] = None
    ) -> bool:
        """
        Manually unlock an achievement (for special cases).
        
        Args:
            user_id: User identifier
            achievement_id: Achievement to unlock
            custom_description: Optional custom description for the unlock
            
        Returns:
            True if successfully unlocked
        """
        return await self.award_achievement(user_id, achievement_id)
    
    async def get_user_achievements(self, user_id: int) -> Dict[str, Any]:
        """Get user achievements data for Telegram integration."""
        try:
            if not self.db_connection:
                await self.initialize()
            
            # Get user achievements (using simplified version)
            achievements = await self._get_user_achievements_list(user_id)
            
            unlocked_achievements = []
            for ach in achievements[:5]:  # Limit to recent 5
                achievement_def = self.achievements.get(ach.achievement_id)
                if achievement_def:
                    unlocked_achievements.append({
                        'name': achievement_def.name,
                        'description': achievement_def.description,
                        'icon': achievement_def.icon,
                        'points': achievement_def.points,
                        'earned_at': ach.earned_at.isoformat()
                    })
            
            # Calculate total points
            total_points = sum(
                self.achievements[ach.achievement_id].points 
                for ach in achievements 
                if ach.achievement_id in self.achievements
            )
            
            # Generate next goals
            available = await self.get_available_achievements(user_id)
            next_goals = []
            for ach in available[:3]:  # Next 3 available
                progress = await self.get_achievement_progress(user_id, ach.id)
                next_goals.append({
                    'name': ach.name,
                    'progress': progress.get('progress_percent', 0) / 100,
                    'description': ach.description
                })
            
            return {
                'unlocked_achievements': unlocked_achievements,
                'total_points': total_points,
                'progress_to_next': 0.75,  # Placeholder
                'recent_milestones': [],
                'next_goals': next_goals
            }
            
        except Exception as e:
            self.logger.error(f"Error getting user achievements: {e}")
            return {
                'unlocked_achievements': [],
                'total_points': 0,
                'progress_to_next': 0,
                'recent_milestones': [],
                'next_goals': []
            }
    
    async def _get_user_achievements_list(self, user_id: int) -> List[UserAchievement]:
        """Get all achievements earned by a user."""
        try:
            # Check cache
            if (user_id in self.user_achievements_cache and 
                user_id in self.cache_expiry and
                datetime.now() < self.cache_expiry[user_id]):
                return self.user_achievements_cache[user_id]
            
            # Fetch from database
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT * FROM user_achievements 
                WHERE user_id = ?
                ORDER BY earned_at DESC
            """, (user_id,))
            
            achievements = []
            for row in cursor.fetchall():
                achievement = UserAchievement(
                    user_id=row['user_id'],
                    achievement_id=row['achievement_id'],
                    earned_at=datetime.fromisoformat(row['earned_at']),
                    progress_data=json.loads(row['progress_data'] or '{}')
                )
                achievements.append(achievement)
            
            # Cache results
            self.user_achievements_cache[user_id] = achievements
            self.cache_expiry[user_id] = datetime.now() + self.cache_duration
            
            return achievements
            
        except Exception as e:
            self.logger.error(f"Error getting user achievements: {e}")
            return []
    
    async def get_available_achievements(
        self, 
        user_id: int, 
        include_hidden: bool = False
    ) -> List[Achievement]:
        """Get all available achievements for a user."""
        try:
            user_achievements = await self.get_user_achievements(user_id)
            earned_ids = {ach.achievement_id for ach in user_achievements}
            
            available = []
            for achievement in self.achievements.values():
                if achievement.id in earned_ids:
                    continue
                
                if achievement.hidden and not include_hidden:
                    continue
                
                # Check prerequisite
                if (achievement.prerequisite_achievement and 
                    achievement.prerequisite_achievement not in earned_ids):
                    continue
                
                available.append(achievement)
            
            # Sort by rarity and points
            available.sort(key=lambda x: (x.rarity.value, x.points))
            
            return available
            
        except Exception as e:
            self.logger.error(f"Error getting available achievements: {e}")
            return []
    
    async def get_achievement_progress(
        self, 
        user_id: int, 
        achievement_id: str
    ) -> Dict[str, Any]:
        """Get progress toward a specific achievement."""
        try:
            if achievement_id not in self.achievements:
                return {"error": "Achievement not found"}
            
            achievement = self.achievements[achievement_id]
            condition = achievement.condition
            
            # Get current progress (this would integrate with progress tracker)
            current_value = await self._get_current_achievement_value(user_id, achievement)
            target_value = condition.get("value", 1)
            
            progress_percent = min(100, (current_value / target_value) * 100) if target_value > 0 else 100
            
            return {
                "achievement_id": achievement_id,
                "achievement_name": achievement.name,
                "current_value": current_value,
                "target_value": target_value,
                "progress_percent": progress_percent,
                "completed": current_value >= target_value
            }
            
        except Exception as e:
            self.logger.error(f"Error getting achievement progress: {e}")
            return {"error": "Failed to get progress"}
    
    async def _get_current_achievement_value(
        self, 
        user_id: int, 
        achievement: Achievement
    ) -> int:
        """Get current value for achievement progress."""
        # This would integrate with the progress tracker to get actual values
        # For now, return 0
        return 0
    
    def format_achievement_notification(self, achievement: Achievement) -> str:
        """Format an achievement notification message."""
        rarity_colors = {
            AchievementRarity.COMMON: "🟢",
            AchievementRarity.UNCOMMON: "🟡",
            AchievementRarity.RARE: "🟠",
            AchievementRarity.EPIC: "🟣",
            AchievementRarity.LEGENDARY: "🟨"
        }
        
        color = rarity_colors.get(achievement.rarity, "⚪")
        
        return f"""🎉 **Achievement Unlocked!** 🎉

{achievement.icon} **{achievement.name}**
{achievement.description}

{color} **{achievement.rarity.value.title()}** | 💰 **{achievement.points} points**

Great job! Keep learning to unlock more achievements! 🌟"""
    
    async def get_achievement_stats(self, user_id: int) -> Dict[str, Any]:
        """Get achievement statistics for a user."""
        try:
            user_achievements = await self.get_user_achievements(user_id)
            
            # Calculate stats
            total_earned = len(user_achievements)
            total_available = len(self.achievements)
            total_points = sum(self.achievements[ach.achievement_id].points for ach in user_achievements)
            
            # Count by category
            category_counts = {}
            for ach in user_achievements:
                achievement = self.achievements[ach.achievement_id]
                category = achievement.category.value
                category_counts[category] = category_counts.get(category, 0) + 1
            
            # Count by rarity
            rarity_counts = {}
            for ach in user_achievements:
                achievement = self.achievements[ach.achievement_id]
                rarity = achievement.rarity.value
                rarity_counts[rarity] = rarity_counts.get(rarity, 0) + 1
            
            return {
                "total_earned": total_earned,
                "total_available": total_available,
                "completion_percent": (total_earned / total_available * 100) if total_available > 0 else 0,
                "total_points": total_points,
                "category_counts": category_counts,
                "rarity_counts": rarity_counts,
                "recent_achievements": [
                    {
                        "name": self.achievements[ach.achievement_id].name,
                        "icon": self.achievements[ach.achievement_id].icon,
                        "earned_at": ach.earned_at.isoformat()
                    }
                    for ach in user_achievements[:5]  # Last 5
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting achievement stats: {e}")
            return {"error": "Failed to get stats"}
    
    async def cleanup(self) -> None:
        """Clean up achievement system resources."""
        try:
            if self.db_connection:
                self.db_connection.close()
                self.db_connection = None
            
            self.user_achievements_cache.clear()
            self.cache_expiry.clear()
            
            self.logger.info("Achievement System cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up Achievement System: {e}")
    
    def __del__(self):
        """Destructor to ensure database connection is closed."""
        if hasattr(self, 'db_connection') and self.db_connection:
            self.db_connection.close()