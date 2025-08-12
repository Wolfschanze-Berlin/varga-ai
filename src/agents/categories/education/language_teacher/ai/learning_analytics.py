"""
Learning Analytics System for tracking and analyzing learning progress.
"""

import json
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
from collections import defaultdict, Counter

from src.log_service import get_logger


class MetricType(Enum):
    """Types of learning metrics."""
    ACCURACY = "accuracy"
    SPEED = "speed"
    RETENTION = "retention"
    ENGAGEMENT = "engagement"
    PROGRESS = "progress"
    DIFFICULTY = "difficulty"
    CONSISTENCY = "consistency"


class LearningStyle(Enum):
    """Detected learning styles."""
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING_WRITING = "reading_writing"
    MIXED = "mixed"


@dataclass
class LearningMetric:
    """Individual learning metric."""
    metric_type: MetricType
    value: float
    timestamp: datetime
    context: Dict[str, Any]
    confidence: float = 1.0


@dataclass
class PerformanceTrend:
    """Performance trend analysis."""
    metric_type: MetricType
    trend_direction: str  # "improving", "declining", "stable"
    trend_strength: float  # 0-1 scale
    recent_average: float
    historical_average: float
    change_percentage: float


@dataclass
class LearningInsight:
    """Learning insight or recommendation."""
    insight_type: str
    title: str
    description: str
    recommendation: str
    priority: float  # 0-1 scale
    evidence: Dict[str, Any]
    created_at: datetime


@dataclass
class WeaknessAnalysis:
    """Analysis of learning weaknesses."""
    topic: str
    weakness_type: str
    severity: float  # 0-1 scale
    evidence_count: int
    examples: List[str]
    suggested_interventions: List[str]


class LearningAnalytics:
    """
    Learning Analytics System for comprehensive progress tracking.
    
    Features:
    - Progress tracking across multiple dimensions
    - Learning style identification
    - Weakness detection and analysis
    - Performance forecasting
    - Adaptive recommendations
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize learning analytics system.
        
        Args:
            config: Configuration dictionary
        """
        self.logger = get_logger("learning_analytics")
        
        # Configuration
        self.config = config or {}
        
        # Data storage
        self.student_metrics: Dict[str, List[LearningMetric]] = defaultdict(list)
        self.student_sessions: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.performance_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # Analysis caches
        self.trend_cache: Dict[str, Dict[MetricType, PerformanceTrend]] = {}
        self.insight_cache: Dict[str, List[LearningInsight]] = {}
        self.weakness_cache: Dict[str, List[WeaknessAnalysis]] = {}
        
        # Analysis parameters
        self.trend_window_days = 14
        self.min_data_points = 5
        self.insight_refresh_hours = 6
        self.prediction_horizon_days = 7
        
        # Learning style indicators
        self.style_indicators = {
            LearningStyle.VISUAL: {
                'prefers_images': 0.3,
                'visual_memory': 0.4,
                'diagram_performance': 0.3
            },
            LearningStyle.AUDITORY: {
                'listening_tasks': 0.4,
                'pronunciation_focus': 0.3,
                'audio_preference': 0.3
            },
            LearningStyle.KINESTHETIC: {
                'interactive_tasks': 0.4,
                'hands_on_practice': 0.3,
                'movement_breaks': 0.3
            },
            LearningStyle.READING_WRITING: {
                'text_performance': 0.4,
                'writing_tasks': 0.3,
                'note_taking': 0.3
            }
        }
        
        self.logger.info("Initialized Learning Analytics System")
    
    def record_metric(self, student_id: str, metric_type: MetricType, 
                     value: float, context: Dict[str, Any] = None) -> None:
        """
        Record a learning metric.
        
        Args:
            student_id: Student identifier
            metric_type: Type of metric
            value: Metric value
            context: Additional context data
        """
        try:
            metric = LearningMetric(
                metric_type=metric_type,
                value=value,
                timestamp=datetime.now(),
                context=context or {}
            )
            
            self.student_metrics[student_id].append(metric)
            
            # Clear caches that might be affected
            if student_id in self.trend_cache:
                if metric_type in self.trend_cache[student_id]:
                    del self.trend_cache[student_id][metric_type]
            
            self.logger.debug(f"Recorded metric for {student_id}: {metric_type.value} = {value}")
            
        except Exception as e:
            self.logger.error(f"Error recording metric: {e}")
    
    def record_session(self, student_id: str, session_data: Dict[str, Any]) -> None:
        """
        Record a learning session.
        
        Args:
            student_id: Student identifier
            session_data: Session data
        """
        try:
            session_data['timestamp'] = datetime.now()
            self.student_sessions[student_id].append(session_data)
            
            # Extract metrics from session data
            self._extract_session_metrics(student_id, session_data)
            
            self.logger.debug(f"Recorded session for {student_id}")
            
        except Exception as e:
            self.logger.error(f"Error recording session: {e}")
    
    def _extract_session_metrics(self, student_id: str, session_data: Dict[str, Any]) -> None:
        """Extract and record metrics from session data."""
        try:
            # Accuracy metric
            if 'accuracy' in session_data:
                self.record_metric(
                    student_id, MetricType.ACCURACY, 
                    session_data['accuracy'],
                    {'session_id': session_data.get('session_id')}
                )
            
            # Speed metric (response time)
            if 'avg_response_time' in session_data:
                # Convert to speed (inverse of time, normalized)
                speed = 1.0 / (1.0 + session_data['avg_response_time'] / 10.0)
                self.record_metric(
                    student_id, MetricType.SPEED, speed,
                    {'response_time': session_data['avg_response_time']}
                )
            
            # Engagement metric
            if 'engagement_score' in session_data:
                self.record_metric(
                    student_id, MetricType.ENGAGEMENT,
                    session_data['engagement_score'],
                    {'session_duration': session_data.get('duration_minutes', 0)}
                )
            
            # Progress metric (items completed)
            if 'items_completed' in session_data:
                self.record_metric(
                    student_id, MetricType.PROGRESS,
                    session_data['items_completed'],
                    {'session_type': session_data.get('session_type', 'practice')}
                )
            
            # Consistency metric (based on streak)
            if 'streak_count' in session_data:
                consistency = min(1.0, session_data['streak_count'] / 10.0)
                self.record_metric(
                    student_id, MetricType.CONSISTENCY, consistency,
                    {'streak': session_data['streak_count']}
                )
            
        except Exception as e:
            self.logger.error(f"Error extracting session metrics: {e}")
    
    def analyze_performance_trend(self, student_id: str, 
                                metric_type: MetricType) -> PerformanceTrend:
        """
        Analyze performance trend for a specific metric.
        
        Args:
            student_id: Student identifier
            metric_type: Type of metric to analyze
            
        Returns:
            Performance trend analysis
        """
        try:
            # Check cache
            if (student_id in self.trend_cache and 
                metric_type in self.trend_cache[student_id]):
                
                cached_trend = self.trend_cache[student_id][metric_type]
                # Return cached if recent enough
                cache_age = datetime.now() - cached_trend.recent_average  # Using as timestamp
                if cache_age.total_seconds() < self.insight_refresh_hours * 3600:
                    return cached_trend
            
            # Get metrics for this type
            metrics = [
                m for m in self.student_metrics.get(student_id, [])
                if m.metric_type == metric_type
            ]
            
            if len(metrics) < self.min_data_points:
                return self._create_default_trend(metric_type)
            
            # Sort by timestamp
            metrics.sort(key=lambda m: m.timestamp)
            
            # Calculate time windows
            now = datetime.now()
            cutoff_date = now - timedelta(days=self.trend_window_days)
            
            recent_metrics = [m for m in metrics if m.timestamp >= cutoff_date]
            historical_metrics = [m for m in metrics if m.timestamp < cutoff_date]
            
            if not recent_metrics:
                return self._create_default_trend(metric_type)
            
            # Calculate averages
            recent_avg = np.mean([m.value for m in recent_metrics])
            historical_avg = (
                np.mean([m.value for m in historical_metrics])
                if historical_metrics
                else recent_avg
            )
            
            # Determine trend
            change_percentage = (
                ((recent_avg - historical_avg) / historical_avg * 100)
                if historical_avg != 0
                else 0
            )
            
            # Trend direction and strength
            if abs(change_percentage) < 5:  # Less than 5% change
                trend_direction = "stable"
                trend_strength = 1.0 - abs(change_percentage) / 5.0
            elif change_percentage > 0:
                trend_direction = "improving"
                trend_strength = min(1.0, abs(change_percentage) / 20.0)  # 20% = max strength
            else:
                trend_direction = "declining"
                trend_strength = min(1.0, abs(change_percentage) / 20.0)
            
            trend = PerformanceTrend(
                metric_type=metric_type,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                recent_average=recent_avg,
                historical_average=historical_avg,
                change_percentage=change_percentage
            )
            
            # Cache the result
            if student_id not in self.trend_cache:
                self.trend_cache[student_id] = {}
            self.trend_cache[student_id][metric_type] = trend
            
            return trend
            
        except Exception as e:
            self.logger.error(f"Error analyzing performance trend: {e}")
            return self._create_default_trend(metric_type)
    
    def _create_default_trend(self, metric_type: MetricType) -> PerformanceTrend:
        """Create default trend when insufficient data."""
        return PerformanceTrend(
            metric_type=metric_type,
            trend_direction="stable",
            trend_strength=0.0,
            recent_average=0.5,
            historical_average=0.5,
            change_percentage=0.0
        )
    
    def identify_learning_style(self, student_id: str) -> Tuple[LearningStyle, float]:
        """
        Identify student's learning style based on behavior patterns.
        
        Args:
            student_id: Student identifier
            
        Returns:
            Tuple of (learning_style, confidence)
        """
        try:
            sessions = self.student_sessions.get(student_id, [])
            
            if len(sessions) < 3:
                return LearningStyle.MIXED, 0.3  # Default with low confidence
            
            # Calculate style scores
            style_scores = {style: 0.0 for style in LearningStyle}
            
            for session in sessions:
                # Visual indicators
                if session.get('visual_content_used', False):
                    style_scores[LearningStyle.VISUAL] += 0.2
                if session.get('diagram_performance', 0) > 0.8:
                    style_scores[LearningStyle.VISUAL] += 0.3
                
                # Auditory indicators
                if session.get('audio_content_used', False):
                    style_scores[LearningStyle.AUDITORY] += 0.2
                if session.get('listening_performance', 0) > 0.8:
                    style_scores[LearningStyle.AUDITORY] += 0.3
                if session.get('pronunciation_practice', False):
                    style_scores[LearningStyle.AUDITORY] += 0.1
                
                # Kinesthetic indicators
                if session.get('interactive_exercises', 0) > 5:
                    style_scores[LearningStyle.KINESTHETIC] += 0.2
                if session.get('typing_speed_above_avg', False):
                    style_scores[LearningStyle.KINESTHETIC] += 0.1
                
                # Reading/Writing indicators
                if session.get('text_heavy_content', False):
                    style_scores[LearningStyle.READING_WRITING] += 0.2
                if session.get('writing_exercises', 0) > 0:
                    style_scores[LearningStyle.READING_WRITING] += 0.3
            
            # Normalize scores
            total_score = sum(style_scores.values())
            if total_score > 0:
                for style in style_scores:
                    style_scores[style] /= total_score
            
            # Find dominant style
            max_style = max(style_scores, key=style_scores.get)
            max_score = style_scores[max_style]
            
            # Check if mixed (no clear dominant style)
            if max_score < 0.4:
                return LearningStyle.MIXED, max_score
            
            # Calculate confidence based on dominance
            confidence = min(1.0, max_score * 2)  # Scale to 0-1
            
            return max_style, confidence
            
        except Exception as e:
            self.logger.error(f"Error identifying learning style: {e}")
            return LearningStyle.MIXED, 0.3
    
    def detect_weaknesses(self, student_id: str) -> List[WeaknessAnalysis]:
        """
        Detect learning weaknesses and problem areas.
        
        Args:
            student_id: Student identifier
            
        Returns:
            List of weakness analyses
        """
        try:
            # Check cache
            if (student_id in self.weakness_cache and
                datetime.now() - datetime.now() < timedelta(hours=self.insight_refresh_hours)):
                return self.weakness_cache[student_id]
            
            weaknesses = []
            sessions = self.student_sessions.get(student_id, [])
            
            if len(sessions) < self.min_data_points:
                return weaknesses
            
            # Analyze by topic
            topic_performance = defaultdict(list)
            topic_errors = defaultdict(list)
            
            for session in sessions:
                # Group performance by topic
                if 'topics_covered' in session:
                    for topic, performance in session['topics_covered'].items():
                        topic_performance[topic].append(performance.get('accuracy', 0))
                
                # Group errors by topic
                if 'errors' in session:
                    for error in session['errors']:
                        topic = error.get('topic', 'unknown')
                        topic_errors[topic].append(error)
            
            # Identify weak topics
            for topic, performances in topic_performance.items():
                if len(performances) >= 3:
                    avg_performance = np.mean(performances)
                    
                    if avg_performance < 0.6:  # Below 60% accuracy
                        severity = 1.0 - avg_performance
                        errors = topic_errors.get(topic, [])
                        
                        # Analyze error types
                        error_types = Counter(error.get('type', 'unknown') for error in errors)
                        most_common_error = error_types.most_common(1)[0][0] if error_types else 'general'
                        
                        # Generate examples and interventions
                        examples = [
                            error.get('example', 'No example')
                            for error in errors[:3]
                        ]
                        
                        interventions = self._suggest_interventions(topic, most_common_error, severity)
                        
                        weakness = WeaknessAnalysis(
                            topic=topic,
                            weakness_type=most_common_error,
                            severity=severity,
                            evidence_count=len(performances),
                            examples=examples,
                            suggested_interventions=interventions
                        )
                        
                        weaknesses.append(weakness)
            
            # Sort by severity
            weaknesses.sort(key=lambda w: w.severity, reverse=True)
            
            # Cache results
            self.weakness_cache[student_id] = weaknesses
            
            return weaknesses
            
        except Exception as e:
            self.logger.error(f"Error detecting weaknesses: {e}")
            return []
    
    def _suggest_interventions(self, topic: str, error_type: str, severity: float) -> List[str]:
        """Suggest interventions for a specific weakness."""
        interventions = []
        
        try:
            # Topic-specific interventions
            topic_interventions = {
                'vocabulary': [
                    "Practice with flashcards and spaced repetition",
                    "Use vocabulary in context sentences",
                    "Try visual associations and memory techniques"
                ],
                'grammar': [
                    "Review grammar rules with examples",
                    "Practice with targeted exercises",
                    "Focus on sentence construction patterns"
                ],
                'pronunciation': [
                    "Listen to native speakers and repeat",
                    "Use pronunciation apps with feedback",
                    "Practice minimal pairs exercises"
                ],
                'conversation': [
                    "Engage in more speaking practice",
                    "Practice common conversation patterns",
                    "Record yourself and analyze speech"
                ]
            }
            
            # Error-type specific interventions
            error_interventions = {
                'spelling': [
                    "Practice spelling rules and patterns",
                    "Use spelling games and exercises"
                ],
                'grammar': [
                    "Review specific grammar concepts",
                    "Practice with guided exercises"
                ],
                'semantic': [
                    "Focus on meaning and context",
                    "Practice paraphrasing exercises"
                ]
            }
            
            # Add topic interventions
            if topic in topic_interventions:
                interventions.extend(topic_interventions[topic])
            
            # Add error-type interventions
            if error_type in error_interventions:
                interventions.extend(error_interventions[error_type])
            
            # Severity-based interventions
            if severity > 0.8:
                interventions.append("Consider reviewing fundamental concepts")
                interventions.append("Reduce difficulty level temporarily")
            elif severity > 0.6:
                interventions.append("Increase practice frequency")
            
            # Remove duplicates and limit
            interventions = list(dict.fromkeys(interventions))[:5]
            
            return interventions
            
        except Exception as e:
            self.logger.error(f"Error suggesting interventions: {e}")
            return ["Continue regular practice"]
    
    def generate_insights(self, student_id: str) -> List[LearningInsight]:
        """
        Generate learning insights and recommendations.
        
        Args:
            student_id: Student identifier
            
        Returns:
            List of learning insights
        """
        try:
            insights = []
            
            # Performance trend insights
            for metric_type in MetricType:
                trend = self.analyze_performance_trend(student_id, metric_type)
                
                if trend.trend_strength > 0.5:
                    if trend.trend_direction == "improving":
                        insights.append(LearningInsight(
                            insight_type="positive_trend",
                            title=f"{metric_type.value.title()} is Improving",
                            description=f"Your {metric_type.value} has improved by {trend.change_percentage:.1f}% recently",
                            recommendation="Keep up the great work! Continue with your current study approach.",
                            priority=0.7,
                            evidence={"trend_strength": trend.trend_strength, "change": trend.change_percentage},
                            created_at=datetime.now()
                        ))
                    
                    elif trend.trend_direction == "declining":
                        insights.append(LearningInsight(
                            insight_type="concern",
                            title=f"{metric_type.value.title()} Needs Attention",
                            description=f"Your {metric_type.value} has declined by {abs(trend.change_percentage):.1f}% recently",
                            recommendation="Consider adjusting your study approach or taking a brief break to avoid burnout.",
                            priority=0.8,
                            evidence={"trend_strength": trend.trend_strength, "change": trend.change_percentage},
                            created_at=datetime.now()
                        ))
            
            # Learning style insights
            style, confidence = self.identify_learning_style(student_id)
            if confidence > 0.6:
                insights.append(LearningInsight(
                    insight_type="learning_style",
                    title=f"Your Learning Style: {style.value.title()}",
                    description=f"Analysis suggests you learn best through {style.value} methods",
                    recommendation=self._get_style_recommendation(style),
                    priority=0.6,
                    evidence={"style": style.value, "confidence": confidence},
                    created_at=datetime.now()
                ))
            
            # Weakness insights
            weaknesses = self.detect_weaknesses(student_id)
            for weakness in weaknesses[:2]:  # Top 2 weaknesses
                insights.append(LearningInsight(
                    insight_type="weakness",
                    title=f"Focus Area: {weakness.topic.title()}",
                    description=f"This area shows room for improvement (severity: {weakness.severity:.1f})",
                    recommendation=f"Suggested actions: {'; '.join(weakness.suggested_interventions[:2])}",
                    priority=weakness.severity,
                    evidence={"topic": weakness.topic, "error_count": weakness.evidence_count},
                    created_at=datetime.now()
                ))
            
            # Study consistency insights
            consistency_metrics = [
                m for m in self.student_metrics.get(student_id, [])
                if m.metric_type == MetricType.CONSISTENCY
            ]
            
            if consistency_metrics:
                recent_consistency = np.mean([m.value for m in consistency_metrics[-7:]])
                if recent_consistency < 0.5:
                    insights.append(LearningInsight(
                        insight_type="consistency",
                        title="Improve Study Consistency",
                        description="Regular practice sessions would help improve retention",
                        recommendation="Try to study for shorter periods more frequently rather than long, infrequent sessions.",
                        priority=0.7,
                        evidence={"consistency_score": recent_consistency},
                        created_at=datetime.now()
                    ))
            
            # Sort insights by priority
            insights.sort(key=lambda i: i.priority, reverse=True)
            
            return insights[:10]  # Return top 10 insights
            
        except Exception as e:
            self.logger.error(f"Error generating insights: {e}")
            return []
    
    def _get_style_recommendation(self, style: LearningStyle) -> str:
        """Get recommendation based on learning style."""
        recommendations = {
            LearningStyle.VISUAL: "Focus on visual content like images, diagrams, and charts. Use color-coding and visual memory techniques.",
            LearningStyle.AUDITORY: "Emphasize listening exercises, pronunciation practice, and discussion. Try reading aloud.",
            LearningStyle.KINESTHETIC: "Engage with interactive content, typing exercises, and hands-on practice. Take breaks to move around.",
            LearningStyle.READING_WRITING: "Focus on text-based exercises, note-taking, and writing practice. Create written summaries.",
            LearningStyle.MIXED: "Vary your learning methods to include visual, auditory, and hands-on activities."
        }
        return recommendations.get(style, "Experiment with different learning methods to find what works best for you.")
    
    def predict_performance(self, student_id: str, days_ahead: int = 7) -> Dict[str, float]:
        """
        Predict future performance based on current trends.
        
        Args:
            student_id: Student identifier
            days_ahead: Number of days to predict ahead
            
        Returns:
            Dictionary of predicted metric values
        """
        try:
            predictions = {}
            
            for metric_type in [MetricType.ACCURACY, MetricType.ENGAGEMENT, MetricType.PROGRESS]:
                trend = self.analyze_performance_trend(student_id, metric_type)
                
                # Simple linear extrapolation
                current_value = trend.recent_average
                daily_change = trend.change_percentage / 100 / self.trend_window_days
                
                predicted_value = current_value + (daily_change * days_ahead)
                
                # Clamp to reasonable bounds
                predicted_value = max(0.0, min(1.0, predicted_value))
                
                predictions[metric_type.value] = predicted_value
            
            return predictions
            
        except Exception as e:
            self.logger.error(f"Error predicting performance: {e}")
            return {}
    
    def get_comprehensive_report(self, student_id: str) -> Dict[str, Any]:
        """
        Generate comprehensive analytics report for student.
        
        Args:
            student_id: Student identifier
            
        Returns:
            Comprehensive analytics report
        """
        try:
            # Gather all analyses
            trends = {}
            for metric_type in MetricType:
                trends[metric_type.value] = asdict(
                    self.analyze_performance_trend(student_id, metric_type)
                )
            
            style, style_confidence = self.identify_learning_style(student_id)
            weaknesses = [asdict(w) for w in self.detect_weaknesses(student_id)]
            insights = [asdict(i) for i in self.generate_insights(student_id)]
            predictions = self.predict_performance(student_id)
            
            # Calculate summary statistics
            sessions = self.student_sessions.get(student_id, [])
            metrics = self.student_metrics.get(student_id, [])
            
            report = {
                'student_id': student_id,
                'report_generated_at': datetime.now().isoformat(),
                'data_summary': {
                    'total_sessions': len(sessions),
                    'total_metrics': len(metrics),
                    'data_span_days': self._calculate_data_span(sessions),
                    'last_activity': max((s.get('timestamp', datetime.min) for s in sessions), default=datetime.min).isoformat()
                },
                'performance_trends': trends,
                'learning_style': {
                    'identified_style': style.value,
                    'confidence': style_confidence,
                    'recommendation': self._get_style_recommendation(style)
                },
                'weaknesses': weaknesses,
                'insights': insights,
                'predictions': predictions,
                'overall_progress': self._calculate_overall_progress(student_id)
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive report: {e}")
            return {'error': str(e)}
    
    def _calculate_data_span(self, sessions: List[Dict[str, Any]]) -> int:
        """Calculate span of data in days."""
        try:
            if len(sessions) < 2:
                return 0
            
            timestamps = [s.get('timestamp', datetime.min) for s in sessions]
            timestamps = [t for t in timestamps if t != datetime.min]
            
            if len(timestamps) < 2:
                return 0
            
            return (max(timestamps) - min(timestamps)).days
            
        except Exception as e:
            return 0
    
    def _calculate_overall_progress(self, student_id: str) -> Dict[str, float]:
        """Calculate overall progress metrics."""
        try:
            # Get recent accuracy trend
            accuracy_trend = self.analyze_performance_trend(student_id, MetricType.ACCURACY)
            
            # Get engagement trend
            engagement_trend = self.analyze_performance_trend(student_id, MetricType.ENGAGEMENT)
            
            # Get progress trend
            progress_trend = self.analyze_performance_trend(student_id, MetricType.PROGRESS)
            
            # Calculate composite score
            composite_score = (
                accuracy_trend.recent_average * 0.4 +
                engagement_trend.recent_average * 0.3 +
                progress_trend.recent_average * 0.3
            )
            
            return {
                'composite_score': composite_score,
                'accuracy_level': accuracy_trend.recent_average,
                'engagement_level': engagement_trend.recent_average,
                'progress_rate': progress_trend.recent_average
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating overall progress: {e}")
            return {'composite_score': 0.5}