"""
Spaced Repetition System for optimal learning retention.
"""

import math
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np

from src.log_service import get_logger


class ReviewResult(Enum):
    """Possible outcomes of a review session."""
    AGAIN = "again"      # Completely forgot, show again
    HARD = "hard"        # Remembered with difficulty
    GOOD = "good"        # Remembered correctly
    EASY = "easy"        # Too easy, remembered instantly


@dataclass
class ReviewCard:
    """Represents a learning item in the spaced repetition system."""
    card_id: str
    content: str
    card_type: str  # "vocabulary", "grammar", "phrase", etc.
    knowledge_components: List[str]
    
    # SRS parameters
    ease_factor: float = 2.5  # SM-2 ease factor (minimum 1.3)
    interval: int = 1  # Days until next review
    repetitions: int = 0  # Number of successful repetitions
    
    # Review history
    last_reviewed: Optional[datetime] = None
    next_review: Optional[datetime] = None
    review_count: int = 0
    
    # Performance tracking
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    difficulty_score: float = 0.5  # 0-1 scale
    
    # Metadata
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.next_review is None:
            self.next_review = datetime.now()


@dataclass
class ReviewSession:
    """Represents a review session."""
    session_id: str
    student_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    cards_reviewed: List[str] = None
    session_stats: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.cards_reviewed is None:
            self.cards_reviewed = []
        if self.session_stats is None:
            self.session_stats = {
                'total_cards': 0,
                'correct_answers': 0,
                'accuracy_rate': 0.0,
                'avg_response_time': 0.0
            }


class SpacedRepetitionSystem:
    """
    Spaced Repetition System implementing SuperMemo SM-2+ algorithm.
    
    Features:
    - Forgetting curve modeling
    - Optimal review scheduling
    - Adaptive difficulty adjustment
    - Performance tracking
    - Multiple review algorithms
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize spaced repetition system.
        
        Args:
            config: Configuration dictionary
        """
        self.logger = get_logger("spaced_repetition")
        
        # Configuration
        self.config = config or {}
        self.algorithm = self.config.get('algorithm', 'sm2_plus')
        
        # Cards storage
        self.cards: Dict[str, ReviewCard] = {}
        
        # Student decks
        self.student_decks: Dict[str, List[str]] = {}
        
        # Review sessions
        self.review_sessions: Dict[str, ReviewSession] = {}
        
        # Algorithm parameters
        self.sm2_params = {
            'min_ease_factor': 1.3,
            'max_ease_factor': 5.0,
            'ease_bonus': 0.15,
            'ease_penalty': 0.20,
            'min_interval': 1,
            'max_interval': 365,
            'graduation_interval': 4,
            'initial_intervals': [1, 6]  # Learning phase intervals (minutes, days)
        }
        
        # Forgetting curve parameters
        self.forgetting_curve = {
            'initial_strength': 1.0,
            'decay_constant': 0.05,
            'retrieval_threshold': 0.9
        }
        
        self.logger.info(f"Initialized Spaced Repetition System with {self.algorithm} algorithm")
    
    def add_card(self, card_id: str, content: str, card_type: str = "vocabulary",
                knowledge_components: List[str] = None) -> ReviewCard:
        """
        Add new card to the system.
        
        Args:
            card_id: Unique card identifier
            content: Card content
            card_type: Type of card
            knowledge_components: Related knowledge components
            
        Returns:
            Created review card
        """
        try:
            if knowledge_components is None:
                knowledge_components = [card_type]
            
            card = ReviewCard(
                card_id=card_id,
                content=content,
                card_type=card_type,
                knowledge_components=knowledge_components
            )
            
            self.cards[card_id] = card
            self.logger.debug(f"Added card: {card_id}")
            
            return card
            
        except Exception as e:
            self.logger.error(f"Error adding card {card_id}: {e}")
            raise
    
    def add_card_to_student_deck(self, student_id: str, card_id: str) -> None:
        """Add card to student's learning deck."""
        try:
            if student_id not in self.student_decks:
                self.student_decks[student_id] = []
            
            if card_id not in self.student_decks[student_id]:
                self.student_decks[student_id].append(card_id)
                self.logger.debug(f"Added card {card_id} to student {student_id}")
            
        except Exception as e:
            self.logger.error(f"Error adding card to student deck: {e}")
    
    def get_due_cards(self, student_id: str, limit: int = 20) -> List[ReviewCard]:
        """
        Get cards due for review for a student.
        
        Args:
            student_id: Student identifier
            limit: Maximum number of cards to return
            
        Returns:
            List of cards due for review
        """
        try:
            if student_id not in self.student_decks:
                return []
            
            now = datetime.now()
            due_cards = []
            
            for card_id in self.student_decks[student_id]:
                if card_id in self.cards:
                    card = self.cards[card_id]
                    
                    # Check if card is due
                    if card.next_review and card.next_review <= now:
                        due_cards.append(card)
            
            # Sort by priority (overdue cards first, then by difficulty)
            due_cards.sort(key=lambda c: (
                (now - c.next_review).total_seconds() if c.next_review else 0,
                -c.difficulty_score  # Higher difficulty first
            ), reverse=True)
            
            return due_cards[:limit]
            
        except Exception as e:
            self.logger.error(f"Error getting due cards: {e}")
            return []
    
    def review_card(self, student_id: str, card_id: str, result: ReviewResult,
                   response_time: float = None) -> None:
        """
        Process card review result and update scheduling.
        
        Args:
            student_id: Student identifier
            card_id: Card identifier
            result: Review result
            response_time: Response time in seconds
        """
        try:
            if card_id not in self.cards:
                self.logger.warning(f"Card {card_id} not found")
                return
            
            card = self.cards[card_id]
            
            # Update review stats
            card.review_count += 1
            card.last_reviewed = datetime.now()
            card.updated_at = datetime.now()
            
            # Update response time
            if response_time is not None:
                if card.avg_response_time == 0:
                    card.avg_response_time = response_time
                else:
                    # Exponential moving average
                    alpha = 0.3
                    card.avg_response_time = (
                        alpha * response_time + (1 - alpha) * card.avg_response_time
                    )
            
            # Update success rate
            correct = result in [ReviewResult.GOOD, ReviewResult.EASY]
            if card.review_count == 1:
                card.success_rate = 1.0 if correct else 0.0
            else:
                # Exponential moving average
                alpha = 0.2
                new_success = 1.0 if correct else 0.0
                card.success_rate = alpha * new_success + (1 - alpha) * card.success_rate
            
            # Update difficulty based on performance
            self._update_difficulty(card, result, response_time)
            
            # Schedule next review based on algorithm
            if self.algorithm == 'sm2_plus':
                self._schedule_sm2_plus(card, result)
            elif self.algorithm == 'anki':
                self._schedule_anki(card, result)
            else:
                self._schedule_sm2_basic(card, result)
            
            self.logger.debug(
                f"Reviewed card {card_id}: {result.value}, "
                f"next review in {card.interval} days"
            )
            
        except Exception as e:
            self.logger.error(f"Error reviewing card: {e}")
    
    def _update_difficulty(self, card: ReviewCard, result: ReviewResult, 
                          response_time: float = None) -> None:
        """Update card difficulty based on performance."""
        try:
            # Adjust difficulty based on review result
            if result == ReviewResult.EASY:
                card.difficulty_score = max(0.0, card.difficulty_score - 0.1)
            elif result == ReviewResult.GOOD:
                card.difficulty_score = max(0.0, card.difficulty_score - 0.05)
            elif result == ReviewResult.HARD:
                card.difficulty_score = min(1.0, card.difficulty_score + 0.1)
            elif result == ReviewResult.AGAIN:
                card.difficulty_score = min(1.0, card.difficulty_score + 0.2)
            
            # Adjust based on response time if available
            if response_time is not None and card.avg_response_time > 0:
                time_ratio = response_time / card.avg_response_time
                
                if time_ratio > 1.5:  # Slow response
                    card.difficulty_score = min(1.0, card.difficulty_score + 0.05)
                elif time_ratio < 0.7:  # Fast response
                    card.difficulty_score = max(0.0, card.difficulty_score - 0.05)
            
        except Exception as e:
            self.logger.error(f"Error updating difficulty: {e}")
    
    def _schedule_sm2_basic(self, card: ReviewCard, result: ReviewResult) -> None:
        """Schedule using basic SM-2 algorithm."""
        try:
            if result == ReviewResult.AGAIN:
                # Reset learning
                card.repetitions = 0
                card.interval = 1
                card.ease_factor = max(
                    self.sm2_params['min_ease_factor'],
                    card.ease_factor - self.sm2_params['ease_penalty']
                )
            
            elif result == ReviewResult.HARD:
                card.repetitions = 0
                card.interval = max(1, int(card.interval * 0.6))
                card.ease_factor = max(
                    self.sm2_params['min_ease_factor'],
                    card.ease_factor - self.sm2_params['ease_penalty']
                )
            
            elif result == ReviewResult.GOOD:
                card.repetitions += 1
                
                if card.repetitions == 1:
                    card.interval = 1
                elif card.repetitions == 2:
                    card.interval = 6
                else:
                    card.interval = int(card.interval * card.ease_factor)
                
            elif result == ReviewResult.EASY:
                card.repetitions += 1
                
                if card.repetitions == 1:
                    card.interval = 4
                else:
                    card.interval = int(card.interval * card.ease_factor)
                
                card.ease_factor = min(
                    self.sm2_params['max_ease_factor'],
                    card.ease_factor + self.sm2_params['ease_bonus']
                )
            
            # Apply limits
            card.interval = max(
                self.sm2_params['min_interval'],
                min(self.sm2_params['max_interval'], card.interval)
            )
            
            # Set next review date
            card.next_review = datetime.now() + timedelta(days=card.interval)
            
        except Exception as e:
            self.logger.error(f"Error in SM-2 basic scheduling: {e}")
    
    def _schedule_sm2_plus(self, card: ReviewCard, result: ReviewResult) -> None:
        """Schedule using enhanced SM-2+ algorithm."""
        try:
            # Factor in success rate and difficulty
            difficulty_modifier = 1.0 + (card.difficulty_score - 0.5) * 0.5
            success_modifier = 0.5 + card.success_rate * 0.5
            
            if result == ReviewResult.AGAIN:
                card.repetitions = 0
                card.interval = 1
                card.ease_factor = max(
                    self.sm2_params['min_ease_factor'],
                    card.ease_factor - self.sm2_params['ease_penalty'] * difficulty_modifier
                )
            
            elif result == ReviewResult.HARD:
                # Don't reset repetitions for hard, just reduce interval
                card.interval = max(1, int(card.interval * 0.7 * success_modifier))
                card.ease_factor = max(
                    self.sm2_params['min_ease_factor'],
                    card.ease_factor - (self.sm2_params['ease_penalty'] * 0.5)
                )
            
            elif result == ReviewResult.GOOD:
                card.repetitions += 1
                
                if card.repetitions == 1:
                    card.interval = int(1 * difficulty_modifier)
                elif card.repetitions == 2:
                    card.interval = int(6 * difficulty_modifier)
                else:
                    card.interval = int(
                        card.interval * card.ease_factor * success_modifier
                    )
            
            elif result == ReviewResult.EASY:
                card.repetitions += 1
                
                if card.repetitions == 1:
                    card.interval = int(4 * success_modifier)
                else:
                    card.interval = int(
                        card.interval * card.ease_factor * 1.3 * success_modifier
                    )
                
                card.ease_factor = min(
                    self.sm2_params['max_ease_factor'],
                    card.ease_factor + (self.sm2_params['ease_bonus'] * success_modifier)
                )
            
            # Apply limits and modifiers
            card.interval = max(
                self.sm2_params['min_interval'],
                min(self.sm2_params['max_interval'], card.interval)
            )
            
            # Set next review date
            card.next_review = datetime.now() + timedelta(days=card.interval)
            
        except Exception as e:
            self.logger.error(f"Error in SM-2+ scheduling: {e}")
            self._schedule_sm2_basic(card, result)  # Fallback
    
    def _schedule_anki(self, card: ReviewCard, result: ReviewResult) -> None:
        """Schedule using Anki-like algorithm."""
        try:
            # Anki uses graduating intervals and learning steps
            if card.repetitions == 0:  # Learning phase
                if result in [ReviewResult.GOOD, ReviewResult.EASY]:
                    card.interval = self.sm2_params['graduation_interval']
                    card.repetitions = 1
                else:
                    card.interval = 0  # Show again today
            else:  # Review phase
                if result == ReviewResult.AGAIN:
                    card.repetitions = 0  # Back to learning
                    card.interval = 0
                elif result == ReviewResult.HARD:
                    card.interval = max(1, int(card.interval * 1.2))
                elif result == ReviewResult.GOOD:
                    card.interval = int(card.interval * card.ease_factor)
                elif result == ReviewResult.EASY:
                    card.interval = int(card.interval * card.ease_factor * 1.3)
                    card.ease_factor += 0.15
            
            # Set next review
            if card.interval == 0:
                card.next_review = datetime.now() + timedelta(minutes=10)
            else:
                card.next_review = datetime.now() + timedelta(days=card.interval)
            
        except Exception as e:
            self.logger.error(f"Error in Anki scheduling: {e}")
            self._schedule_sm2_basic(card, result)  # Fallback
    
    def calculate_retention_probability(self, card: ReviewCard, 
                                      time_since_review: timedelta = None) -> float:
        """
        Calculate probability of remembering based on forgetting curve.
        
        Args:
            card: Review card
            time_since_review: Time since last review (optional)
            
        Returns:
            Retention probability (0-1)
        """
        try:
            if not card.last_reviewed:
                return self.forgetting_curve['initial_strength']
            
            if time_since_review is None:
                time_since_review = datetime.now() - card.last_reviewed
            
            # Convert to hours
            hours_elapsed = time_since_review.total_seconds() / 3600
            
            # Modified forgetting curve considering ease factor and success rate
            decay_rate = (
                self.forgetting_curve['decay_constant'] / 
                (card.ease_factor * (card.success_rate + 0.1))
            )
            
            retention = math.exp(-decay_rate * hours_elapsed)
            
            return max(0.01, min(1.0, retention))
            
        except Exception as e:
            self.logger.error(f"Error calculating retention: {e}")
            return 0.5
    
    def start_review_session(self, student_id: str, session_id: str = None) -> str:
        """
        Start a new review session.
        
        Args:
            student_id: Student identifier
            session_id: Optional session identifier
            
        Returns:
            Session identifier
        """
        try:
            if session_id is None:
                session_id = f"session_{student_id}_{int(datetime.now().timestamp())}"
            
            session = ReviewSession(
                session_id=session_id,
                student_id=student_id,
                start_time=datetime.now()
            )
            
            self.review_sessions[session_id] = session
            self.logger.info(f"Started review session {session_id} for student {student_id}")
            
            return session_id
            
        except Exception as e:
            self.logger.error(f"Error starting review session: {e}")
            raise
    
    def end_review_session(self, session_id: str) -> Dict[str, Any]:
        """
        End review session and return statistics.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session statistics
        """
        try:
            if session_id not in self.review_sessions:
                raise ValueError(f"Session {session_id} not found")
            
            session = self.review_sessions[session_id]
            session.end_time = datetime.now()
            
            # Calculate session duration
            duration = session.end_time - session.start_time
            
            # Update session stats
            if session.cards_reviewed:
                session.session_stats['total_cards'] = len(session.cards_reviewed)
                session.session_stats['duration_minutes'] = duration.total_seconds() / 60
                
                # Calculate accuracy from card performance
                correct_count = 0
                total_time = 0.0
                
                for card_id in session.cards_reviewed:
                    if card_id in self.cards:
                        card = self.cards[card_id]
                        if card.success_rate > 0.7:  # Consider as correct
                            correct_count += 1
                        total_time += card.avg_response_time
                
                session.session_stats['correct_answers'] = correct_count
                session.session_stats['accuracy_rate'] = (
                    correct_count / len(session.cards_reviewed) 
                    if session.cards_reviewed else 0
                )
                session.session_stats['avg_response_time'] = (
                    total_time / len(session.cards_reviewed) 
                    if session.cards_reviewed else 0
                )
            
            self.logger.info(f"Ended review session {session_id}")
            return session.session_stats
            
        except Exception as e:
            self.logger.error(f"Error ending review session: {e}")
            return {}
    
    def get_student_statistics(self, student_id: str) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a student.
        
        Args:
            student_id: Student identifier
            
        Returns:
            Student statistics
        """
        try:
            if student_id not in self.student_decks:
                return {'error': 'Student not found'}
            
            cards = [
                self.cards[card_id] 
                for card_id in self.student_decks[student_id]
                if card_id in self.cards
            ]
            
            if not cards:
                return {'total_cards': 0}
            
            # Basic stats
            total_cards = len(cards)
            total_reviews = sum(card.review_count for card in cards)
            
            # Due cards
            now = datetime.now()
            due_cards = [
                card for card in cards 
                if card.next_review and card.next_review <= now
            ]
            
            # Learning progress
            mature_cards = [card for card in cards if card.repetitions >= 3]
            young_cards = [card for card in cards if 0 < card.repetitions < 3]
            new_cards = [card for card in cards if card.repetitions == 0]
            
            # Average metrics
            avg_ease = np.mean([card.ease_factor for card in cards])
            avg_interval = np.mean([card.interval for card in cards])
            avg_success_rate = np.mean([card.success_rate for card in cards])
            
            # Difficulty distribution
            difficulty_distribution = {
                'easy': len([c for c in cards if c.difficulty_score < 0.3]),
                'medium': len([c for c in cards if 0.3 <= c.difficulty_score < 0.7]),
                'hard': len([c for c in cards if c.difficulty_score >= 0.7])
            }
            
            statistics = {
                'total_cards': total_cards,
                'total_reviews': total_reviews,
                'cards_due': len(due_cards),
                'mature_cards': len(mature_cards),
                'young_cards': len(young_cards),
                'new_cards': len(new_cards),
                'average_ease_factor': round(avg_ease, 2),
                'average_interval': round(avg_interval, 1),
                'average_success_rate': round(avg_success_rate, 3),
                'difficulty_distribution': difficulty_distribution,
                'retention_rate': avg_success_rate,
                'next_review_due': min(
                    (card.next_review for card in due_cards),
                    default=None
                )
            }
            
            return statistics
            
        except Exception as e:
            self.logger.error(f"Error getting student statistics: {e}")
            return {'error': str(e)}
    
    def export_student_data(self, student_id: str) -> Dict[str, Any]:
        """Export all data for a student."""
        try:
            data = {
                'student_id': student_id,
                'exported_at': datetime.now().isoformat(),
                'cards': {},
                'statistics': self.get_student_statistics(student_id)
            }
            
            if student_id in self.student_decks:
                for card_id in self.student_decks[student_id]:
                    if card_id in self.cards:
                        card = self.cards[card_id]
                        data['cards'][card_id] = {
                            'card_id': card.card_id,
                            'content': card.content,
                            'card_type': card.card_type,
                            'knowledge_components': card.knowledge_components,
                            'ease_factor': card.ease_factor,
                            'interval': card.interval,
                            'repetitions': card.repetitions,
                            'last_reviewed': card.last_reviewed.isoformat() if card.last_reviewed else None,
                            'next_review': card.next_review.isoformat() if card.next_review else None,
                            'review_count': card.review_count,
                            'success_rate': card.success_rate,
                            'difficulty_score': card.difficulty_score,
                            'created_at': card.created_at.isoformat(),
                            'updated_at': card.updated_at.isoformat()
                        }
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error exporting student data: {e}")
            return {'error': str(e)}