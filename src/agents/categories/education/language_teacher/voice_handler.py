"""
Voice Message Handler - Processes voice messages for pronunciation practice.
Handles speech recognition, pronunciation analysis, and feedback generation.
"""

import os
import asyncio
import tempfile
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from src.log_service import get_logger


class PronunciationLevel(Enum):
    """Pronunciation difficulty levels."""
    BEGINNER = "beginner"
    ELEMENTARY = "elementary"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


@dataclass
class PronunciationExercise:
    """Pronunciation exercise structure."""
    exercise_id: str
    text: str
    phonetic: str
    difficulty: PronunciationLevel
    language: str = "english"
    tips: List[str] = None
    common_mistakes: List[str] = None
    
    def __post_init__(self):
        if self.tips is None:
            self.tips = []
        if self.common_mistakes is None:
            self.common_mistakes = []


@dataclass
class VoiceProcessingResult:
    """Result of voice message processing."""
    success: bool
    transcription: Optional[str] = None
    pronunciation_score: Optional[float] = None
    feedback: Optional[str] = None
    error: Optional[str] = None
    duration_seconds: Optional[int] = None
    confidence_score: Optional[float] = None
    detailed_feedback: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.detailed_feedback is None:
            self.detailed_feedback = {}


class VoiceMessageHandler:
    """
    Handles voice message processing for pronunciation practice.
    Provides speech recognition, pronunciation scoring, and feedback generation.
    """
    
    # Pronunciation exercises by level
    EXERCISES = {
        PronunciationLevel.BEGINNER: [
            {
                "text": "Hello, how are you today?",
                "phonetic": "/həˈloʊ haʊ ɑr ju təˈdeɪ/",
                "tips": ["Stress on 'lo' in hello", "Clear 'h' sound"],
                "common_mistakes": ["Dropping the 'h'", "Unclear vowel sounds"]
            },
            {
                "text": "Thank you very much.",
                "phonetic": "/θæŋk ju ˈvɛri mʌtʃ/",
                "tips": ["'th' sound with tongue between teeth", "Clear 'v' sound"],
                "common_mistakes": ["'f' instead of 'th'", "Weak 'v' sound"]
            },
            {
                "text": "Nice to meet you.",
                "phonetic": "/naɪs tu mit ju/",
                "tips": ["Long 'i' sound in 'nice'", "Clear 't' sounds"],
                "common_mistakes": ["Short 'i' in 'nice'", "Unclear consonants"]
            }
        ],
        PronunciationLevel.ELEMENTARY: [
            {
                "text": "I would like to order some coffee, please.",
                "phonetic": "/aɪ wʊd laɪk tu ˈɔrdər sʌm ˈkɔfi pliz/",
                "tips": ["Clear 'would' pronunciation", "Stress on 'order' and 'coffee'"],
                "common_mistakes": ["Unclear 'would'", "Wrong stress patterns"]
            },
            {
                "text": "The weather is beautiful today.",
                "phonetic": "/ðə ˈwɛðər ɪz ˈbjutəfəl təˈdeɪ/",
                "tips": ["'th' sound in 'the' and 'weather'", "Clear syllables in 'beautiful'"],
                "common_mistakes": ["'d' instead of 'th'", "Rushed 'beautiful'"]
            }
        ],
        PronunciationLevel.INTERMEDIATE: [
            {
                "text": "I'm particularly interested in learning about sustainable development.",
                "phonetic": "/aɪm pərˈtɪkjələrli ˈɪntrəstəd ɪn ˈlɜrnɪŋ əˈbaʊt səˈsteɪnəbəl dɪˈvɛləpmənt/",
                "tips": ["Clear syllable breaks", "Proper stress on multi-syllable words"],
                "common_mistakes": ["Rushing through long words", "Incorrect stress patterns"]
            }
        ],
        PronunciationLevel.ADVANCED: [
            {
                "text": "The phenomenon of globalization has significantly influenced contemporary society.",
                "phonetic": "/ðə fəˈnɑməˌnɑn ʌv ˌgloʊbələˈzeɪʃən hæz sɪgˈnɪfəkəntli ˈɪnfluənst kənˈtɛmpərˌɛri səˈsaɪəti/",
                "tips": ["Complex stress patterns", "Clear articulation of complex words"],
                "common_mistakes": ["Unclear consonant clusters", "Wrong stress placement"]
            }
        ]
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the voice message handler."""
        self.logger = get_logger("voice_handler")
        self.config = config or {}
        
        # Voice processing configuration
        self.max_audio_duration = self.config.get('max_audio_duration', 60)  # seconds
        self.supported_languages = self.config.get('supported_languages', ['english'])
        self.speech_recognition_provider = self.config.get('speech_recognition_provider', 'mock')
        self.pronunciation_scoring_enabled = self.config.get('pronunciation_scoring', True)
        
        # Temporary file management
        self.temp_dir = tempfile.mkdtemp(prefix="voice_processing_")
        
        self.logger.info("Voice Message Handler initialized")
    
    async def process_voice_message(
        self,
        voice_file_path: str,
        user_profile: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> VoiceProcessingResult:
        """
        Process a voice message for pronunciation practice.
        
        Args:
            voice_file_path: Path to the voice file
            user_profile: User's profile information
            context: Additional context (expected text, exercise type, etc.)
            
        Returns:
            VoiceProcessingResult with analysis and feedback
        """
        try:
            self.logger.info(f"Processing voice message: {voice_file_path}")
            
            # Validate file exists and size
            if not os.path.exists(voice_file_path):
                return VoiceProcessingResult(
                    success=False,
                    error="Voice file not found"
                )
            
            file_size = os.path.getsize(voice_file_path)
            if file_size == 0:
                return VoiceProcessingResult(
                    success=False,
                    error="Voice file is empty"
                )
            
            # Extract language and level from user profile
            language = user_profile.get('target_language', 'english')
            level = user_profile.get('proficiency_level', 'beginner')
            
            if language not in self.supported_languages:
                return VoiceProcessingResult(
                    success=False,
                    error=f"Voice processing not supported for {language}"
                )
            
            # Perform speech recognition
            transcription_result = await self._perform_speech_recognition(
                voice_file_path, language
            )
            
            if not transcription_result['success']:
                return VoiceProcessingResult(
                    success=False,
                    error=transcription_result.get('error', 'Speech recognition failed')
                )
            
            transcription = transcription_result['transcription']
            confidence = transcription_result.get('confidence', 0.8)
            
            # Get expected text from context
            expected_text = context.get('expected_text', '') if context else ''
            
            # Calculate pronunciation score
            pronunciation_score = await self._calculate_pronunciation_score(
                transcription, expected_text, language, level
            )
            
            # Generate detailed feedback
            feedback = await self._generate_pronunciation_feedback(
                transcription, expected_text, pronunciation_score, language, level
            )
            
            # Calculate audio duration (mock)
            duration_seconds = min(10, max(1, int(file_size / 1000)))  # Rough estimation
            
            return VoiceProcessingResult(
                success=True,
                transcription=transcription,
                pronunciation_score=pronunciation_score,
                feedback=feedback,
                duration_seconds=duration_seconds,
                confidence_score=confidence,
                detailed_feedback={
                    'word_level_scores': {},
                    'rhythm_score': 0.8,
                    'intonation_score': 0.75,
                    'fluency_score': 0.7
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error processing voice message: {e}")
            return VoiceProcessingResult(
                success=False,
                error=f"Voice processing failed: {str(e)}"
            )
    
    async def _perform_speech_recognition(
        self,
        audio_file_path: str,
        language: str
    ) -> Dict[str, Any]:
        """
        Perform speech recognition on audio file.
        
        Args:
            audio_file_path: Path to audio file
            language: Target language
            
        Returns:
            Dictionary with transcription results
        """
        try:
            # For demonstration, return mock transcription
            # In production, this would use actual speech recognition APIs
            
            if self.speech_recognition_provider == 'openai_whisper':
                return await self._whisper_recognition(audio_file_path, language)
            elif self.speech_recognition_provider == 'google_speech':
                return await self._google_speech_recognition(audio_file_path, language)
            else:
                # Mock recognition for demo
                return await self._mock_speech_recognition(audio_file_path)
            
        except Exception as e:
            self.logger.error(f"Speech recognition error: {e}")
            return {
                'success': False,
                'error': f"Speech recognition failed: {str(e)}"
            }
    
    async def _whisper_recognition(self, audio_file_path: str, language: str) -> Dict[str, Any]:
        """Mock Whisper API recognition."""
        # This would integrate with OpenAI Whisper API
        await asyncio.sleep(0.5)  # Simulate processing time
        
        # Mock result
        sample_transcriptions = [
            "Hello, how are you today?",
            "Thank you very much.",
            "Nice to meet you.",
            "I would like to practice pronunciation.",
            "The weather is beautiful today."
        ]
        
        import random
        transcription = random.choice(sample_transcriptions)
        
        return {
            'success': True,
            'transcription': transcription,
            'confidence': random.uniform(0.7, 0.95),
            'language_detected': language
        }
    
    async def _google_speech_recognition(self, audio_file_path: str, language: str) -> Dict[str, Any]:
        """Mock Google Speech API recognition."""
        await asyncio.sleep(0.3)  # Simulate processing time
        
        return {
            'success': True,
            'transcription': "Hello, this is a test transcription.",
            'confidence': 0.85,
            'language_detected': language
        }
    
    async def _mock_speech_recognition(self, audio_file_path: str) -> Dict[str, Any]:
        """Mock speech recognition for testing."""
        await asyncio.sleep(0.1)  # Simulate processing time
        
        sample_texts = [
            "Hello, how are you?",
            "Thank you very much for your help.",
            "I am learning English pronunciation.",
            "The weather is nice today.",
            "Could you help me with this exercise?",
            "I would like to practice speaking."
        ]
        
        import random
        return {
            'success': True,
            'transcription': random.choice(sample_texts),
            'confidence': random.uniform(0.75, 0.95)
        }
    
    async def _calculate_pronunciation_score(
        self,
        transcription: str,
        expected_text: str,
        language: str,
        level: str
    ) -> float:
        """
        Calculate pronunciation accuracy score.
        
        Args:
            transcription: What was actually said
            expected_text: What was supposed to be said
            language: Target language
            level: User's proficiency level
            
        Returns:
            Pronunciation score between 0.0 and 1.0
        """
        try:
            if not expected_text:
                # If no expected text, give a generic score based on transcription quality
                return self._calculate_general_pronunciation_score(transcription, level)
            
            # Calculate similarity between expected and actual
            similarity_score = self._calculate_text_similarity(
                transcription.lower().strip(),
                expected_text.lower().strip()
            )
            
            # Adjust score based on user level
            level_adjustments = {
                'beginner': 0.1,    # More forgiving
                'elementary': 0.05,
                'intermediate': 0.0,
                'advanced': -0.05   # More strict
            }
            
            adjustment = level_adjustments.get(level, 0.0)
            final_score = min(1.0, max(0.0, similarity_score + adjustment))
            
            return final_score
            
        except Exception as e:
            self.logger.error(f"Error calculating pronunciation score: {e}")
            return 0.7  # Default score
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using simple word matching."""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 and not words2:
            return 1.0
        
        # Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_general_pronunciation_score(self, transcription: str, level: str) -> float:
        """Calculate general pronunciation score when no expected text is provided."""
        # Base score on transcription clarity and length
        words = transcription.split()
        word_count = len(words)
        
        # Base score
        base_score = 0.7
        
        # Bonus for appropriate length
        if 3 <= word_count <= 15:
            base_score += 0.1
        elif word_count > 15:
            base_score += 0.05
        
        # Level-based adjustments
        level_bonuses = {
            'beginner': 0.1,
            'elementary': 0.05,
            'intermediate': 0.0,
            'advanced': -0.05
        }
        
        final_score = base_score + level_bonuses.get(level, 0.0)
        return min(1.0, max(0.3, final_score))
    
    async def _generate_pronunciation_feedback(
        self,
        transcription: str,
        expected_text: str,
        score: float,
        language: str,
        level: str
    ) -> str:
        """Generate detailed pronunciation feedback."""
        
        # Score-based feedback
        if score >= 0.9:
            base_feedback = "🎉 **Excellent pronunciation!** Your speech was very clear and accurate."
        elif score >= 0.8:
            base_feedback = "👍 **Great job!** Your pronunciation is very good with minor areas to improve."
        elif score >= 0.7:
            base_feedback = "✅ **Good effort!** Your pronunciation is understandable with some room for improvement."
        elif score >= 0.6:
            base_feedback = "📈 **Keep practicing!** You're making progress, but focus on clarity."
        else:
            base_feedback = "💪 **Don't give up!** Practice makes perfect. Focus on speaking slowly and clearly."
        
        feedback_parts = [base_feedback]
        
        # Add specific feedback based on comparison
        if expected_text and transcription:
            expected_words = expected_text.lower().split()
            actual_words = transcription.lower().split()
            
            # Find differences
            if expected_words != actual_words:
                feedback_parts.append("\n**Areas to focus on:**")
                
                if len(actual_words) < len(expected_words):
                    feedback_parts.append("• Try to include all words in the phrase")
                elif len(actual_words) > len(expected_words):
                    feedback_parts.append("• Focus on the key words in the phrase")
                
                # Check for common pronunciation issues
                if any('th' in word for word in expected_words):
                    feedback_parts.append("• Pay attention to 'th' sounds")
                
                if any(word for word in expected_words if len(word) > 6):
                    feedback_parts.append("• Break down longer words into syllables")
        
        # Add level-appropriate tips
        level_tips = {
            'beginner': [
                "💡 **Tip:** Speak slowly and focus on individual sounds",
                "🔄 **Practice:** Try recording the same phrase multiple times"
            ],
            'elementary': [
                "💡 **Tip:** Pay attention to word stress patterns",
                "🔄 **Practice:** Focus on connecting words smoothly"
            ],
            'intermediate': [
                "💡 **Tip:** Work on natural rhythm and intonation",
                "🔄 **Practice:** Try varying your speed and emphasis"
            ],
            'advanced': [
                "💡 **Tip:** Focus on subtle sounds and natural flow",
                "🔄 **Practice:** Practice with longer, more complex sentences"
            ]
        }
        
        tips = level_tips.get(level, level_tips['beginner'])
        feedback_parts.extend(tips)
        
        return "\n".join(feedback_parts)
    
    def get_pronunciation_exercise(self, level: str) -> Dict[str, Any]:
        """Get a pronunciation exercise for the given level."""
        try:
            level_enum = PronunciationLevel(level)
        except ValueError:
            level_enum = PronunciationLevel.BEGINNER
        
        exercises = self.EXERCISES.get(level_enum, self.EXERCISES[PronunciationLevel.BEGINNER])
        
        import random
        exercise_data = random.choice(exercises)
        
        return {
            'exercise_id': f"pronunciation_{level}_{int(datetime.now().timestamp())}",
            'text': exercise_data['text'],
            'phonetic': exercise_data['phonetic'],
            'tips': exercise_data.get('tips', []),
            'common_mistakes': exercise_data.get('common_mistakes', []),
            'level': level,
            'language': 'english'
        }
    
    def format_pronunciation_exercise(self, exercise: Dict[str, Any]) -> str:
        """Format a pronunciation exercise for display."""
        text = exercise.get('text', '')
        phonetic = exercise.get('phonetic', '')
        tips = exercise.get('tips', [])
        common_mistakes = exercise.get('common_mistakes', [])
        
        formatted = f"""🎤 **Pronunciation Exercise**

📝 **Practice saying:**
"{text}"

🔤 **Phonetic guide:**
{phonetic}

💡 **Tips:**
{chr(10).join([f"• {tip}" for tip in tips])}

⚠️ **Common mistakes to avoid:**
{chr(10).join([f"• {mistake}" for mistake in common_mistakes])}

**Instructions:**
1. Read the text aloud slowly
2. Record your voice message
3. Send it to get instant feedback!

Ready? Record yourself saying the phrase! 🎯"""

        return formatted
    
    async def cleanup_temp_files(self, file_path: str) -> None:
        """Clean up temporary audio files."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                self.logger.debug(f"Cleaned up temp file: {file_path}")
        except Exception as e:
            self.logger.error(f"Error cleaning up temp file: {e}")
    
    async def cleanup(self) -> None:
        """Clean up voice handler resources."""
        try:
            # Clean up temporary directory
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            
            self.logger.info("Voice Message Handler cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up Voice Message Handler: {e}")