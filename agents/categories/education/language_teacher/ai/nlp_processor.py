"""
Natural Language Processing Processor for language learning applications.
"""

import re
import json
import string
import nltk
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import numpy as np
from difflib import SequenceMatcher
from datetime import datetime

from src.log_service import get_logger

# Download required NLTK data (run once)
try:
    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    nltk.download('vader_lexicon', quiet=True)
except Exception as e:
    print(f"Warning: Could not download NLTK data: {e}")


class ErrorType(Enum):
    """Types of language errors."""
    GRAMMAR = "grammar"
    SPELLING = "spelling" 
    VOCABULARY = "vocabulary"
    SYNTAX = "syntax"
    PUNCTUATION = "punctuation"
    SEMANTIC = "semantic"
    PRONUNCIATION = "pronunciation"


class LanguageSkill(Enum):
    """Language skills."""
    VOCABULARY = "vocabulary"
    GRAMMAR = "grammar"
    PRONUNCIATION = "pronunciation"
    COMPREHENSION = "comprehension"
    FLUENCY = "fluency"
    ACCURACY = "accuracy"


@dataclass
class LanguageError:
    """Represents a language learning error."""
    error_type: ErrorType
    original_text: str
    corrected_text: str
    position: Tuple[int, int]  # start, end positions
    explanation: str
    severity: float  # 0-1 scale
    suggestions: List[str]
    rule_violated: Optional[str] = None


@dataclass
class SentenceAnalysis:
    """Analysis of a sentence."""
    original: str
    complexity_score: float
    readability_score: float
    pos_tags: List[Tuple[str, str]]
    errors: List[LanguageError]
    vocabulary_level: str  # "beginner", "intermediate", "advanced"
    grammar_patterns: List[str]


@dataclass
class SemanticSimilarity:
    """Semantic similarity analysis."""
    similarity_score: float  # 0-1
    is_semantically_correct: bool
    explanation: str
    key_differences: List[str]


class NLPProcessor:
    """
    Natural Language Processing component for language learning.
    
    Features:
    - Grammar error detection and correction
    - Semantic similarity analysis
    - Text complexity assessment
    - Vocabulary level detection
    - Pronunciation assessment support
    """
    
    def __init__(self, target_language: str = "english"):
        """
        Initialize NLP processor.
        
        Args:
            target_language: Target language being learned
        """
        self.logger = get_logger("nlp_processor")
        self.target_language = target_language.lower()
        
        # Initialize NLTK components
        try:
            from nltk.corpus import stopwords
            from nltk.sentiment import SentimentIntensityAnalyzer
            from nltk.stem import WordNetLemmatizer
            
            self.stop_words = set(stopwords.words('english'))
            self.sentiment_analyzer = SentimentIntensityAnalyzer()
            self.lemmatizer = WordNetLemmatizer()
            
        except Exception as e:
            self.logger.warning(f"Could not initialize NLTK components: {e}")
            self.stop_words = set()
            self.sentiment_analyzer = None
            self.lemmatizer = None
        
        # Grammar rules and patterns
        self.grammar_rules = self._load_grammar_rules()
        self.common_errors = self._load_common_errors()
        
        # Vocabulary levels
        self.vocabulary_levels = self._load_vocabulary_levels()
        
        # Complexity metrics
        self.complexity_weights = {
            'sentence_length': 0.2,
            'word_complexity': 0.3,
            'grammar_complexity': 0.25,
            'vocabulary_level': 0.25
        }
        
        self.logger.info(f"Initialized NLP Processor for {target_language}")
    
    def _load_grammar_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load grammar rules for error detection."""
        return {
            'subject_verb_agreement': {
                'patterns': [
                    (r'\b(I|you|we|they)\s+(is)\b', 'Subject-verb disagreement'),
                    (r'\b(he|she|it)\s+(are)\b', 'Subject-verb disagreement'),
                ],
                'corrections': {
                    'I is': 'I am',
                    'you is': 'you are',
                    'we is': 'we are',
                    'they is': 'they are',
                    'he are': 'he is',
                    'she are': 'she is',
                    'it are': 'it is'
                }
            },
            'article_usage': {
                'patterns': [
                    (r'\ba\s+([aeiouAEIOU])', 'Use "an" before vowel sounds'),
                    (r'\ban\s+([bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ])', 'Use "a" before consonant sounds')
                ],
                'corrections': {}
            },
            'double_negatives': {
                'patterns': [
                    (r'\b(don\'t|doesn\'t|didn\'t|won\'t|can\'t)\s+.*\b(no|nothing|nobody|never)\b', 
                     'Double negative - use positive form')
                ],
                'corrections': {}
            }
        }
    
    def _load_common_errors(self) -> Dict[str, str]:
        """Load common error patterns and corrections."""
        return {
            # Common spelling errors
            'recieve': 'receive',
            'occurence': 'occurrence',
            'seperate': 'separate',
            'definately': 'definitely',
            'neccessary': 'necessary',
            
            # Common grammar errors
            'your welcome': 'you\'re welcome',
            'its a': 'it\'s a',
            'there house': 'their house',
            'to much': 'too much',
            'alot': 'a lot',
            
            # ESL common errors
            'i have 25 years old': 'i am 25 years old',
            'i am agree': 'i agree',
            'how you are': 'how are you',
            'i am boring': 'i am bored'
        }
    
    def _load_vocabulary_levels(self) -> Dict[str, List[str]]:
        """Load vocabulary by proficiency level."""
        return {
            'beginner': [
                'hello', 'goodbye', 'yes', 'no', 'please', 'thank', 'you',
                'good', 'bad', 'big', 'small', 'hot', 'cold', 'happy', 'sad',
                'eat', 'drink', 'go', 'come', 'see', 'hear', 'speak', 'walk',
                'house', 'car', 'food', 'water', 'family', 'friend', 'work', 'school'
            ],
            'intermediate': [
                'beautiful', 'important', 'difficult', 'necessary', 'possible',
                'government', 'education', 'information', 'development', 'environment',
                'understand', 'explain', 'describe', 'compare', 'analyze',
                'although', 'however', 'therefore', 'furthermore', 'nevertheless'
            ],
            'advanced': [
                'sophisticated', 'comprehensive', 'substantial', 'significant', 'contemporary',
                'phenomenon', 'methodology', 'infrastructure', 'consciousness', 'bureaucracy',
                'facilitate', 'accommodate', 'manipulate', 'substantiate', 'proliferate',
                'consequently', 'predominantly', 'substantially', 'fundamentally'
            ]
        }
    
    def analyze_text(self, text: str, expected_answer: str = None) -> SentenceAnalysis:
        """
        Comprehensive text analysis.
        
        Args:
            text: Text to analyze
            expected_answer: Expected correct answer (optional)
            
        Returns:
            Sentence analysis results
        """
        try:
            # Clean text
            cleaned_text = self._clean_text(text)
            
            # Basic metrics
            complexity_score = self.calculate_complexity(cleaned_text)
            readability_score = self.calculate_readability(cleaned_text)
            
            # POS tagging
            pos_tags = self._get_pos_tags(cleaned_text)
            
            # Error detection
            errors = self.detect_errors(cleaned_text, expected_answer)
            
            # Vocabulary level assessment
            vocab_level = self.assess_vocabulary_level(cleaned_text)
            
            # Grammar patterns
            grammar_patterns = self._identify_grammar_patterns(cleaned_text, pos_tags)
            
            analysis = SentenceAnalysis(
                original=text,
                complexity_score=complexity_score,
                readability_score=readability_score,
                pos_tags=pos_tags,
                errors=errors,
                vocabulary_level=vocab_level,
                grammar_patterns=grammar_patterns
            )
            
            self.logger.debug(f"Analyzed text: complexity={complexity_score:.2f}, errors={len(errors)}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing text: {e}")
            return SentenceAnalysis(
                original=text,
                complexity_score=0.5,
                readability_score=0.5,
                pos_tags=[],
                errors=[],
                vocabulary_level="intermediate",
                grammar_patterns=[]
            )
    
    def detect_errors(self, text: str, expected_answer: str = None) -> List[LanguageError]:
        """
        Detect various types of errors in text.
        
        Args:
            text: Text to check for errors
            expected_answer: Expected correct text (optional)
            
        Returns:
            List of detected errors
        """
        errors = []
        
        try:
            # Grammar errors
            errors.extend(self._detect_grammar_errors(text))
            
            # Spelling errors
            errors.extend(self._detect_spelling_errors(text))
            
            # Common error patterns
            errors.extend(self._detect_common_errors(text))
            
            # If expected answer provided, compare
            if expected_answer:
                semantic_errors = self._compare_with_expected(text, expected_answer)
                errors.extend(semantic_errors)
            
            # Sort errors by position
            errors.sort(key=lambda e: e.position[0])
            
            self.logger.debug(f"Detected {len(errors)} errors in text")
            return errors
            
        except Exception as e:
            self.logger.error(f"Error detecting errors: {e}")
            return []
    
    def _detect_grammar_errors(self, text: str) -> List[LanguageError]:
        """Detect grammar errors using rule-based approach."""
        errors = []
        
        try:
            text_lower = text.lower()
            
            for rule_name, rule_data in self.grammar_rules.items():
                for pattern, description in rule_data['patterns']:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    
                    for match in matches:
                        start, end = match.span()
                        original = match.group()
                        
                        # Try to find correction
                        corrected = rule_data['corrections'].get(original.lower(), original)
                        
                        error = LanguageError(
                            error_type=ErrorType.GRAMMAR,
                            original_text=original,
                            corrected_text=corrected,
                            position=(start, end),
                            explanation=description,
                            severity=0.7,
                            suggestions=[corrected] if corrected != original else [],
                            rule_violated=rule_name
                        )
                        errors.append(error)
            
            return errors
            
        except Exception as e:
            self.logger.error(f"Error detecting grammar errors: {e}")
            return []
    
    def _detect_spelling_errors(self, text: str) -> List[LanguageError]:
        """Detect spelling errors using dictionary lookup and fuzzy matching."""
        errors = []
        
        try:
            words = re.findall(r'\b[a-zA-Z]+\b', text)
            
            for i, word in enumerate(words):
                if word.lower() in self.common_errors:
                    # Find position in original text
                    pattern = r'\b' + re.escape(word) + r'\b'
                    match = re.search(pattern, text, re.IGNORECASE)
                    
                    if match:
                        start, end = match.span()
                        correction = self.common_errors[word.lower()]
                        
                        error = LanguageError(
                            error_type=ErrorType.SPELLING,
                            original_text=word,
                            corrected_text=correction,
                            position=(start, end),
                            explanation=f"Spelling error: '{word}' should be '{correction}'",
                            severity=0.5,
                            suggestions=[correction]
                        )
                        errors.append(error)
            
            return errors
            
        except Exception as e:
            self.logger.error(f"Error detecting spelling errors: {e}")
            return []
    
    def _detect_common_errors(self, text: str) -> List[LanguageError]:
        """Detect common ESL errors."""
        errors = []
        
        try:
            text_lower = text.lower()
            
            for error_pattern, correction in self.common_errors.items():
                if error_pattern in text_lower:
                    # Find position
                    start = text_lower.find(error_pattern)
                    end = start + len(error_pattern)
                    
                    error = LanguageError(
                        error_type=ErrorType.GRAMMAR,
                        original_text=error_pattern,
                        corrected_text=correction,
                        position=(start, end),
                        explanation=f"Common error: use '{correction}' instead of '{error_pattern}'",
                        severity=0.6,
                        suggestions=[correction]
                    )
                    errors.append(error)
            
            return errors
            
        except Exception as e:
            self.logger.error(f"Error detecting common errors: {e}")
            return []
    
    def _compare_with_expected(self, text: str, expected: str) -> List[LanguageError]:
        """Compare student text with expected answer."""
        errors = []
        
        try:
            # Basic similarity check
            similarity = self.calculate_semantic_similarity(text, expected)
            
            if similarity.similarity_score < 0.8:
                # Text is significantly different from expected
                error = LanguageError(
                    error_type=ErrorType.SEMANTIC,
                    original_text=text,
                    corrected_text=expected,
                    position=(0, len(text)),
                    explanation=similarity.explanation,
                    severity=1.0 - similarity.similarity_score,
                    suggestions=[expected]
                )
                errors.append(error)
            
            return errors
            
        except Exception as e:
            self.logger.error(f"Error comparing with expected: {e}")
            return []
    
    def calculate_semantic_similarity(self, text1: str, text2: str) -> SemanticSimilarity:
        """
        Calculate semantic similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Semantic similarity analysis
        """
        try:
            # Clean texts
            clean_text1 = self._clean_text(text1).lower()
            clean_text2 = self._clean_text(text2).lower()
            
            # Exact match
            if clean_text1 == clean_text2:
                return SemanticSimilarity(
                    similarity_score=1.0,
                    is_semantically_correct=True,
                    explanation="Exact match",
                    key_differences=[]
                )
            
            # Calculate similarity using different methods
            
            # 1. Sequence matching (character-level)
            char_similarity = SequenceMatcher(None, clean_text1, clean_text2).ratio()
            
            # 2. Word-level comparison
            words1 = set(clean_text1.split())
            words2 = set(clean_text2.split())
            
            if words1 or words2:
                word_intersection = len(words1.intersection(words2))
                word_union = len(words1.union(words2))
                word_similarity = word_intersection / word_union if word_union > 0 else 0
            else:
                word_similarity = 1.0
            
            # 3. Length similarity
            len1, len2 = len(clean_text1), len(clean_text2)
            length_similarity = 1.0 - abs(len1 - len2) / max(len1, len2, 1)
            
            # Combine similarities
            overall_similarity = (
                0.4 * char_similarity +
                0.4 * word_similarity +
                0.2 * length_similarity
            )
            
            # Determine if semantically correct
            is_correct = overall_similarity > 0.7
            
            # Generate explanation
            if overall_similarity > 0.9:
                explanation = "Very similar meaning"
            elif overall_similarity > 0.7:
                explanation = "Similar meaning with minor differences"
            elif overall_similarity > 0.5:
                explanation = "Somewhat similar meaning"
            else:
                explanation = "Significantly different meaning"
            
            # Find key differences
            differences = []
            missing_words = words2 - words1
            extra_words = words1 - words2
            
            if missing_words:
                differences.append(f"Missing words: {', '.join(list(missing_words)[:3])}")
            if extra_words:
                differences.append(f"Extra words: {', '.join(list(extra_words)[:3])}")
            
            return SemanticSimilarity(
                similarity_score=overall_similarity,
                is_semantically_correct=is_correct,
                explanation=explanation,
                key_differences=differences
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating semantic similarity: {e}")
            return SemanticSimilarity(
                similarity_score=0.5,
                is_semantically_correct=False,
                explanation="Error in similarity calculation",
                key_differences=[]
            )
    
    def calculate_complexity(self, text: str) -> float:
        """
        Calculate text complexity score.
        
        Args:
            text: Text to analyze
            
        Returns:
            Complexity score (0-1, higher = more complex)
        """
        try:
            if not text.strip():
                return 0.0
            
            # Sentence length complexity
            sentences = nltk.sent_tokenize(text)
            if sentences:
                avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
                sentence_complexity = min(1.0, avg_sentence_length / 25)  # 25 words = high complexity
            else:
                sentence_complexity = 0.0
            
            # Word complexity
            words = nltk.word_tokenize(text.lower())
            if words:
                avg_word_length = sum(len(w) for w in words if w.isalpha()) / max(1, len([w for w in words if w.isalpha()]))
                word_complexity = min(1.0, avg_word_length / 8)  # 8+ chars = complex
            else:
                word_complexity = 0.0
            
            # Grammar complexity (based on POS diversity)
            pos_tags = self._get_pos_tags(text)
            if pos_tags:
                unique_pos = len(set(tag for _, tag in pos_tags))
                grammar_complexity = min(1.0, unique_pos / 15)  # 15+ POS tags = complex
            else:
                grammar_complexity = 0.0
            
            # Vocabulary level complexity
            vocab_complexity = self._calculate_vocabulary_complexity(text)
            
            # Weighted combination
            total_complexity = (
                self.complexity_weights['sentence_length'] * sentence_complexity +
                self.complexity_weights['word_complexity'] * word_complexity +
                self.complexity_weights['grammar_complexity'] * grammar_complexity +
                self.complexity_weights['vocabulary_level'] * vocab_complexity
            )
            
            return max(0.0, min(1.0, total_complexity))
            
        except Exception as e:
            self.logger.error(f"Error calculating complexity: {e}")
            return 0.5
    
    def calculate_readability(self, text: str) -> float:
        """
        Calculate readability score (Flesch Reading Ease approximation).
        
        Args:
            text: Text to analyze
            
        Returns:
            Readability score (0-1, higher = more readable)
        """
        try:
            if not text.strip():
                return 0.0
            
            sentences = nltk.sent_tokenize(text)
            words = nltk.word_tokenize(text)
            
            if not sentences or not words:
                return 0.0
            
            # Filter to actual words
            actual_words = [w for w in words if w.isalpha()]
            
            if not actual_words:
                return 0.0
            
            # Calculate metrics
            avg_sentence_length = len(actual_words) / len(sentences)
            avg_syllables = sum(self._count_syllables(word) for word in actual_words) / len(actual_words)
            
            # Simplified Flesch formula
            flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables)
            
            # Convert to 0-1 scale (0-100 Flesch scale)
            readability = max(0.0, min(1.0, flesch_score / 100))
            
            return readability
            
        except Exception as e:
            self.logger.error(f"Error calculating readability: {e}")
            return 0.5
    
    def assess_vocabulary_level(self, text: str) -> str:
        """
        Assess the vocabulary level of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Vocabulary level: "beginner", "intermediate", or "advanced"
        """
        try:
            words = [word.lower() for word in nltk.word_tokenize(text) if word.isalpha()]
            
            if not words:
                return "beginner"
            
            # Count words at each level
            level_counts = {level: 0 for level in self.vocabulary_levels}
            
            for word in words:
                for level, vocab_list in self.vocabulary_levels.items():
                    if word in vocab_list:
                        level_counts[level] += 1
                        break
            
            total_classified = sum(level_counts.values())
            
            if total_classified == 0:
                return "intermediate"  # Default for unclassified words
            
            # Calculate percentages
            percentages = {
                level: count / total_classified 
                for level, count in level_counts.items()
            }
            
            # Determine overall level
            if percentages['advanced'] > 0.3:
                return "advanced"
            elif percentages['intermediate'] > 0.4:
                return "intermediate"
            else:
                return "beginner"
            
        except Exception as e:
            self.logger.error(f"Error assessing vocabulary level: {e}")
            return "intermediate"
    
    def _calculate_vocabulary_complexity(self, text: str) -> float:
        """Calculate vocabulary complexity based on word levels."""
        try:
            vocab_level = self.assess_vocabulary_level(text)
            
            complexity_map = {
                'beginner': 0.2,
                'intermediate': 0.6, 
                'advanced': 1.0
            }
            
            return complexity_map.get(vocab_level, 0.5)
            
        except Exception as e:
            self.logger.error(f"Error calculating vocabulary complexity: {e}")
            return 0.5
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        try:
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text.strip())
            
            # Remove special characters but keep punctuation
            # text = re.sub(r'[^\w\s\.,!?;:\-\']', '', text)
            
            return text
            
        except Exception as e:
            self.logger.error(f"Error cleaning text: {e}")
            return text
    
    def _get_pos_tags(self, text: str) -> List[Tuple[str, str]]:
        """Get part-of-speech tags for text."""
        try:
            tokens = nltk.word_tokenize(text)
            return nltk.pos_tag(tokens)
            
        except Exception as e:
            self.logger.error(f"Error getting POS tags: {e}")
            return []
    
    def _identify_grammar_patterns(self, text: str, pos_tags: List[Tuple[str, str]]) -> List[str]:
        """Identify grammar patterns in text."""
        try:
            patterns = []
            
            if not pos_tags:
                return patterns
            
            # Simple pattern detection
            pos_sequence = [tag for _, tag in pos_tags]
            
            # Check for common patterns
            if any(tag.startswith('VB') for tag in pos_sequence):
                patterns.append('contains_verb')
            
            if any(tag in ['NN', 'NNS', 'NNP', 'NNPS'] for tag in pos_sequence):
                patterns.append('contains_noun')
            
            if any(tag in ['JJ', 'JJR', 'JJS'] for tag in pos_sequence):
                patterns.append('contains_adjective')
            
            # Check for complex structures
            if 'IN' in pos_sequence:  # Prepositions
                patterns.append('prepositional_phrase')
            
            if 'WP' in pos_sequence or 'WRB' in pos_sequence:  # Wh-words
                patterns.append('question_word')
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error identifying grammar patterns: {e}")
            return []
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (approximation)."""
        try:
            word = word.lower()
            vowels = 'aeiouy'
            syllable_count = 0
            previous_was_vowel = False
            
            for char in word:
                if char in vowels:
                    if not previous_was_vowel:
                        syllable_count += 1
                    previous_was_vowel = True
                else:
                    previous_was_vowel = False
            
            # Handle special cases
            if word.endswith('e'):
                syllable_count -= 1
            
            if syllable_count == 0:
                syllable_count = 1
            
            return syllable_count
            
        except Exception as e:
            return 1
    
    def generate_feedback(self, analysis: SentenceAnalysis) -> str:
        """
        Generate human-readable feedback based on analysis.
        
        Args:
            analysis: Sentence analysis results
            
        Returns:
            Feedback string
        """
        try:
            feedback_parts = []
            
            # Overall assessment
            if not analysis.errors:
                feedback_parts.append("✅ Great job! No errors detected.")
            else:
                feedback_parts.append(f"Found {len(analysis.errors)} issue(s) to work on:")
            
            # Error-specific feedback
            for error in analysis.errors[:3]:  # Limit to 3 errors for brevity
                if error.corrected_text != error.original_text:
                    feedback_parts.append(
                        f"• {error.explanation}: '{error.original_text}' → '{error.corrected_text}'"
                    )
                else:
                    feedback_parts.append(f"• {error.explanation}")
            
            # Complexity feedback
            if analysis.complexity_score > 0.8:
                feedback_parts.append("💡 Great use of complex language structures!")
            elif analysis.complexity_score < 0.3:
                feedback_parts.append("💡 Try using more varied vocabulary and sentence structures.")
            
            # Vocabulary level feedback
            feedback_parts.append(f"📚 Vocabulary level: {analysis.vocabulary_level}")
            
            return "\n".join(feedback_parts)
            
        except Exception as e:
            self.logger.error(f"Error generating feedback: {e}")
            return "Unable to generate feedback at this time."