"""
Vocabulary Tool - Handles vocabulary management, definitions, and practice.
Provides vocabulary lookup, translation, and spaced repetition functionality.
"""

import json
import sqlite3
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import os
import random

from src.log_service import get_logger
from src.tools.base.base_tool import BaseTool


class WordDifficulty(Enum):
    """Word difficulty levels."""
    BEGINNER = "beginner"
    ELEMENTARY = "elementary"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class PartOfSpeech(Enum):
    """Parts of speech."""
    NOUN = "noun"
    VERB = "verb"
    ADJECTIVE = "adjective"
    ADVERB = "adverb"
    PREPOSITION = "preposition"
    CONJUNCTION = "conjunction"
    PRONOUN = "pronoun"
    INTERJECTION = "interjection"
    ARTICLE = "article"


@dataclass
class VocabularyWord:
    """A vocabulary word with definitions and metadata."""
    word: str
    language: str
    part_of_speech: PartOfSpeech
    difficulty: WordDifficulty
    definition: str
    example_sentences: List[str] = field(default_factory=list)
    translations: Dict[str, str] = field(default_factory=dict)
    synonyms: List[str] = field(default_factory=list)
    antonyms: List[str] = field(default_factory=list)
    pronunciation: Optional[str] = None
    frequency_rank: Optional[int] = None
    categories: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class UserVocabulary:
    """User's vocabulary learning progress."""
    user_id: int
    word: str
    language: str
    learned_at: datetime
    mastery_level: float = 0.0  # 0.0 to 1.0
    review_count: int = 0
    correct_count: int = 0
    last_reviewed: Optional[datetime] = None
    next_review: Optional[datetime] = None
    is_favorite: bool = False


class VocabularyTool(BaseTool):
    """
    Tool for vocabulary management and practice.
    Handles word lookup, definitions, translations, and spaced repetition.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the vocabulary tool."""
        super().__init__()
        self.logger = get_logger("vocabulary_tool")
        
        # Database setup
        if db_path is None:
            db_path = os.path.join("agents", "data", "vocabulary.db")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.db_connection: Optional[sqlite3.Connection] = None
        
        # In-memory cache for frequently accessed words
        self.word_cache: Dict[str, VocabularyWord] = {}
        self.cache_size_limit = 1000
        
        # Language-specific vocabulary databases
        self.language_vocabularies = self._initialize_language_vocabularies()
    
    def _initialize_language_vocabularies(self) -> Dict[str, Dict]:
        """Initialize vocabulary databases for different languages."""
        return {
            "english": {
                "beginner": [
                    {
                        "word": "hello",
                        "part_of_speech": PartOfSpeech.INTERJECTION,
                        "difficulty": WordDifficulty.BEGINNER,
                        "definition": "A greeting used when meeting someone or starting a conversation",
                        "example_sentences": ["Hello, how are you?", "She said hello to her neighbor."],
                        "categories": ["greetings", "social"],
                        "frequency_rank": 100
                    },
                    {
                        "word": "house",
                        "part_of_speech": PartOfSpeech.NOUN,
                        "difficulty": WordDifficulty.BEGINNER,
                        "definition": "A building for human habitation",
                        "example_sentences": ["I live in a big house.", "The house has a red roof."],
                        "categories": ["home", "building"],
                        "frequency_rank": 200
                    },
                    {
                        "word": "happy",
                        "part_of_speech": PartOfSpeech.ADJECTIVE,
                        "difficulty": WordDifficulty.BEGINNER,
                        "definition": "Feeling joy or pleasure",
                        "example_sentences": ["I am very happy today.", "The happy child was smiling."],
                        "synonyms": ["joyful", "pleased", "content"],
                        "antonyms": ["sad", "unhappy", "miserable"],
                        "categories": ["emotions", "feelings"],
                        "frequency_rank": 150
                    }
                ],
                "intermediate": [
                    {
                        "word": "sophisticated",
                        "part_of_speech": PartOfSpeech.ADJECTIVE,
                        "difficulty": WordDifficulty.INTERMEDIATE,
                        "definition": "Having complex or refined characteristics; worldly-wise",
                        "example_sentences": [
                            "She has sophisticated taste in art.",
                            "The restaurant serves sophisticated cuisine."
                        ],
                        "synonyms": ["refined", "cultured", "complex"],
                        "antonyms": ["simple", "naive", "unsophisticated"],
                        "categories": ["personality", "complexity"],
                        "frequency_rank": 2000
                    },
                    {
                        "word": "implement",
                        "part_of_speech": PartOfSpeech.VERB,
                        "difficulty": WordDifficulty.INTERMEDIATE,
                        "definition": "To put a plan or decision into effect",
                        "example_sentences": [
                            "We need to implement the new policy immediately.",
                            "The company implemented several cost-saving measures."
                        ],
                        "synonyms": ["execute", "carry out", "apply"],
                        "categories": ["business", "action"],
                        "frequency_rank": 1500
                    }
                ]
            },
            "spanish": {
                "beginner": [
                    {
                        "word": "hola",
                        "part_of_speech": PartOfSpeech.INTERJECTION,
                        "difficulty": WordDifficulty.BEGINNER,
                        "definition": "A greeting meaning 'hello'",
                        "example_sentences": ["Hola, ¿cómo estás?", "Ella dijo hola a su vecino."],
                        "translations": {"english": "hello"},
                        "categories": ["greetings", "social"],
                        "frequency_rank": 50
                    },
                    {
                        "word": "casa",
                        "part_of_speech": PartOfSpeech.NOUN,
                        "difficulty": WordDifficulty.BEGINNER,
                        "definition": "A building for human habitation (house)",
                        "example_sentences": ["Vivo en una casa grande.", "La casa tiene un techo rojo."],
                        "translations": {"english": "house"},
                        "categories": ["home", "building"],
                        "frequency_rank": 100
                    }
                ]
            }
        }
    
    async def setup(self) -> bool:
        """Setup the vocabulary tool and database."""
        try:
            self.db_connection = sqlite3.connect(self.db_path)
            self.db_connection.row_factory = sqlite3.Row
            
            await self._create_tables()
            await self._populate_initial_vocabulary()
            
            self.logger.info("Vocabulary Tool setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup Vocabulary Tool: {e}")
            return False
    
    async def _create_tables(self) -> None:
        """Create necessary database tables."""
        cursor = self.db_connection.cursor()
        
        # Vocabulary words table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vocabulary_words (
                word TEXT NOT NULL,
                language TEXT NOT NULL,
                part_of_speech TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                definition TEXT NOT NULL,
                example_sentences TEXT,
                translations TEXT,
                synonyms TEXT,
                antonyms TEXT,
                pronunciation TEXT,
                frequency_rank INTEGER,
                categories TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (word, language)
            )
        """)
        
        # User vocabulary progress table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_vocabulary (
                user_id INTEGER NOT NULL,
                word TEXT NOT NULL,
                language TEXT NOT NULL,
                learned_at TEXT NOT NULL,
                mastery_level REAL DEFAULT 0.0,
                review_count INTEGER DEFAULT 0,
                correct_count INTEGER DEFAULT 0,
                last_reviewed TEXT,
                next_review TEXT,
                is_favorite INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, word, language)
            )
        """)
        
        # Word associations and relationships
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS word_relationships (
                word1 TEXT NOT NULL,
                word2 TEXT NOT NULL,
                language TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                strength REAL DEFAULT 1.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (word1, word2, language, relationship_type)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vocab_difficulty ON vocabulary_words(difficulty, language)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vocab_frequency ON vocabulary_words(frequency_rank)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_vocab_review ON user_vocabulary(next_review)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_vocab_mastery ON user_vocabulary(mastery_level)")
        
        self.db_connection.commit()
    
    async def _populate_initial_vocabulary(self) -> None:
        """Populate database with initial vocabulary words."""
        cursor = self.db_connection.cursor()
        
        for language, levels in self.language_vocabularies.items():
            for level, words in levels.items():
                for word_data in words:
                    # Check if word already exists
                    cursor.execute(
                        "SELECT COUNT(*) FROM vocabulary_words WHERE word = ? AND language = ?",
                        (word_data["word"], language)
                    )
                    
                    if cursor.fetchone()[0] == 0:
                        # Insert new word
                        cursor.execute("""
                            INSERT INTO vocabulary_words 
                            (word, language, part_of_speech, difficulty, definition, 
                             example_sentences, synonyms, antonyms, frequency_rank, categories)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            word_data["word"],
                            language,
                            word_data["part_of_speech"].value,
                            word_data["difficulty"].value,
                            word_data["definition"],
                            json.dumps(word_data.get("example_sentences", [])),
                            json.dumps(word_data.get("synonyms", [])),
                            json.dumps(word_data.get("antonyms", [])),
                            word_data.get("frequency_rank"),
                            json.dumps(word_data.get("categories", []))
                        ))
        
        self.db_connection.commit()
    
    async def lookup_word(
        self, 
        word: str, 
        language: str = "english"
    ) -> Optional[VocabularyWord]:
        """
        Look up a word in the vocabulary database.
        
        Args:
            word: Word to look up
            language: Language code
            
        Returns:
            VocabularyWord object or None if not found
        """
        try:
            word = word.lower().strip()
            cache_key = f"{word}_{language}"
            
            # Check cache first
            if cache_key in self.word_cache:
                return self.word_cache[cache_key]
            
            cursor = self.db_connection.cursor()
            cursor.execute(
                "SELECT * FROM vocabulary_words WHERE word = ? AND language = ?",
                (word, language)
            )
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Create VocabularyWord object
            vocab_word = VocabularyWord(
                word=row['word'],
                language=row['language'],
                part_of_speech=PartOfSpeech(row['part_of_speech']),
                difficulty=WordDifficulty(row['difficulty']),
                definition=row['definition'],
                example_sentences=json.loads(row['example_sentences'] or '[]'),
                translations=json.loads(row['translations'] or '{}'),
                synonyms=json.loads(row['synonyms'] or '[]'),
                antonyms=json.loads(row['antonyms'] or '[]'),
                pronunciation=row['pronunciation'],
                frequency_rank=row['frequency_rank'],
                categories=json.loads(row['categories'] or '[]'),
                created_at=datetime.fromisoformat(row['created_at'])
            )
            
            # Cache the result
            self._cache_word(cache_key, vocab_word)
            
            return vocab_word
            
        except Exception as e:
            self.logger.error(f"Error looking up word '{word}': {e}")
            return None
    
    def _cache_word(self, cache_key: str, vocab_word: VocabularyWord) -> None:
        """Cache a vocabulary word."""
        if len(self.word_cache) >= self.cache_size_limit:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self.word_cache))
            del self.word_cache[oldest_key]
        
        self.word_cache[cache_key] = vocab_word
    
    async def get_words_by_difficulty(
        self, 
        difficulty: WordDifficulty, 
        language: str = "english",
        limit: int = 20
    ) -> List[VocabularyWord]:
        """
        Get words by difficulty level.
        
        Args:
            difficulty: Difficulty level
            language: Language code
            limit: Maximum number of words to return
            
        Returns:
            List of vocabulary words
        """
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT * FROM vocabulary_words 
                WHERE difficulty = ? AND language = ?
                ORDER BY frequency_rank ASC
                LIMIT ?
            """, (difficulty.value, language, limit))
            
            words = []
            for row in cursor.fetchall():
                vocab_word = VocabularyWord(
                    word=row['word'],
                    language=row['language'],
                    part_of_speech=PartOfSpeech(row['part_of_speech']),
                    difficulty=WordDifficulty(row['difficulty']),
                    definition=row['definition'],
                    example_sentences=json.loads(row['example_sentences'] or '[]'),
                    synonyms=json.loads(row['synonyms'] or '[]'),
                    antonyms=json.loads(row['antonyms'] or '[]'),
                    categories=json.loads(row['categories'] or '[]'),
                    frequency_rank=row['frequency_rank']
                )
                words.append(vocab_word)
            
            return words
            
        except Exception as e:
            self.logger.error(f"Error getting words by difficulty: {e}")
            return []
    
    async def get_random_words(
        self, 
        language: str = "english",
        difficulty: Optional[WordDifficulty] = None,
        count: int = 5
    ) -> List[VocabularyWord]:
        """
        Get random words for practice.
        
        Args:
            language: Language code
            difficulty: Optional difficulty filter
            count: Number of words to return
            
        Returns:
            List of random vocabulary words
        """
        try:
            cursor = self.db_connection.cursor()
            
            if difficulty:
                cursor.execute("""
                    SELECT * FROM vocabulary_words 
                    WHERE language = ? AND difficulty = ?
                    ORDER BY RANDOM()
                    LIMIT ?
                """, (language, difficulty.value, count))
            else:
                cursor.execute("""
                    SELECT * FROM vocabulary_words 
                    WHERE language = ?
                    ORDER BY RANDOM()
                    LIMIT ?
                """, (language, count))
            
            words = []
            for row in cursor.fetchall():
                vocab_word = VocabularyWord(
                    word=row['word'],
                    language=row['language'],
                    part_of_speech=PartOfSpeech(row['part_of_speech']),
                    difficulty=WordDifficulty(row['difficulty']),
                    definition=row['definition'],
                    example_sentences=json.loads(row['example_sentences'] or '[]'),
                    synonyms=json.loads(row['synonyms'] or '[]'),
                    antonyms=json.loads(row['antonyms'] or '[]'),
                    categories=json.loads(row['categories'] or '[]')
                )
                words.append(vocab_word)
            
            return words
            
        except Exception as e:
            self.logger.error(f"Error getting random words: {e}")
            return []
    
    async def add_user_vocabulary(
        self,
        user_id: int,
        word: str,
        language: str = "english",
        initial_mastery: float = 0.0
    ) -> bool:
        """
        Add a word to user's vocabulary learning list.
        
        Args:
            user_id: User identifier
            word: Word to add
            language: Language code
            initial_mastery: Initial mastery level (0.0 to 1.0)
            
        Returns:
            True if added successfully
        """
        try:
            cursor = self.db_connection.cursor()
            
            # Check if already in user's vocabulary
            cursor.execute("""
                SELECT COUNT(*) FROM user_vocabulary 
                WHERE user_id = ? AND word = ? AND language = ?
            """, (user_id, word.lower(), language))
            
            if cursor.fetchone()[0] > 0:
                return True  # Already exists
            
            # Add to user vocabulary
            cursor.execute("""
                INSERT INTO user_vocabulary 
                (user_id, word, language, learned_at, mastery_level)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_id, 
                word.lower(), 
                language, 
                datetime.now().isoformat(),
                initial_mastery
            ))
            
            self.db_connection.commit()
            self.logger.info(f"Added word '{word}' to user {user_id}'s vocabulary")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding user vocabulary: {e}")
            return False
    
    async def update_word_mastery(
        self,
        user_id: int,
        word: str,
        language: str,
        correct: bool
    ) -> bool:
        """
        Update word mastery based on practice results.
        
        Args:
            user_id: User identifier
            word: Word practiced
            language: Language code
            correct: Whether the user got it correct
            
        Returns:
            True if updated successfully
        """
        try:
            cursor = self.db_connection.cursor()
            
            # Get current progress
            cursor.execute("""
                SELECT mastery_level, review_count, correct_count
                FROM user_vocabulary 
                WHERE user_id = ? AND word = ? AND language = ?
            """, (user_id, word.lower(), language))
            
            row = cursor.fetchone()
            if not row:
                # Add word if it doesn't exist
                await self.add_user_vocabulary(user_id, word, language)
                current_mastery = 0.0
                review_count = 0
                correct_count = 0
            else:
                current_mastery = row['mastery_level']
                review_count = row['review_count']
                correct_count = row['correct_count']
            
            # Update counts
            review_count += 1
            if correct:
                correct_count += 1
            
            # Calculate new mastery level using spaced repetition algorithm
            new_mastery = self._calculate_mastery_level(
                current_mastery, correct, review_count, correct_count
            )
            
            # Calculate next review time
            next_review = self._calculate_next_review(new_mastery, correct)
            
            # Update database
            cursor.execute("""
                UPDATE user_vocabulary 
                SET mastery_level = ?, review_count = ?, correct_count = ?,
                    last_reviewed = ?, next_review = ?
                WHERE user_id = ? AND word = ? AND language = ?
            """, (
                new_mastery, review_count, correct_count,
                datetime.now().isoformat(),
                next_review.isoformat(),
                user_id, word.lower(), language
            ))
            
            self.db_connection.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating word mastery: {e}")
            return False
    
    def _calculate_mastery_level(
        self, 
        current_mastery: float, 
        correct: bool, 
        review_count: int,
        correct_count: int
    ) -> float:
        """Calculate new mastery level using spaced repetition principles."""
        
        accuracy_rate = correct_count / review_count if review_count > 0 else 0.0
        
        if correct:
            # Increase mastery, but with diminishing returns
            increase = (1.0 - current_mastery) * 0.2 * (1.0 + accuracy_rate)
            new_mastery = min(1.0, current_mastery + increase)
        else:
            # Decrease mastery based on how established it was
            decrease = current_mastery * 0.3 * (1.0 - accuracy_rate)
            new_mastery = max(0.0, current_mastery - decrease)
        
        return round(new_mastery, 3)
    
    def _calculate_next_review(self, mastery_level: float, correct: bool) -> datetime:
        """Calculate when the word should be reviewed next."""
        
        base_interval_hours = [1, 4, 24, 72, 168, 336, 720]  # 1h to 30 days
        mastery_index = min(int(mastery_level * len(base_interval_hours)), len(base_interval_hours) - 1)
        
        interval_hours = base_interval_hours[mastery_index]
        
        # Adjust based on performance
        if correct:
            interval_hours = int(interval_hours * 1.3)  # Increase interval if correct
        else:
            interval_hours = max(1, int(interval_hours * 0.5))  # Decrease interval if wrong
        
        return datetime.now() + timedelta(hours=interval_hours)
    
    async def get_words_for_review(
        self, 
        user_id: int, 
        language: str = "english",
        limit: int = 10
    ) -> List[Tuple[VocabularyWord, UserVocabulary]]:
        """
        Get words that are due for review.
        
        Args:
            user_id: User identifier
            language: Language code
            limit: Maximum number of words to return
            
        Returns:
            List of tuples (VocabularyWord, UserVocabulary)
        """
        try:
            cursor = self.db_connection.cursor()
            
            now = datetime.now().isoformat()
            cursor.execute("""
                SELECT uv.*, vw.*
                FROM user_vocabulary uv
                JOIN vocabulary_words vw ON uv.word = vw.word AND uv.language = vw.language
                WHERE uv.user_id = ? AND uv.language = ? 
                AND (uv.next_review IS NULL OR uv.next_review <= ?)
                ORDER BY uv.mastery_level ASC, uv.last_reviewed ASC
                LIMIT ?
            """, (user_id, language, now, limit))
            
            review_words = []
            for row in cursor.fetchall():
                # Create VocabularyWord
                vocab_word = VocabularyWord(
                    word=row['word'],
                    language=row['language'],
                    part_of_speech=PartOfSpeech(row['part_of_speech']),
                    difficulty=WordDifficulty(row['difficulty']),
                    definition=row['definition'],
                    example_sentences=json.loads(row['example_sentences'] or '[]'),
                    synonyms=json.loads(row['synonyms'] or '[]'),
                    antonyms=json.loads(row['antonyms'] or '[]'),
                    categories=json.loads(row['categories'] or '[]')
                )
                
                # Create UserVocabulary
                user_vocab = UserVocabulary(
                    user_id=row['user_id'],
                    word=row['word'],
                    language=row['language'],
                    learned_at=datetime.fromisoformat(row['learned_at']),
                    mastery_level=row['mastery_level'],
                    review_count=row['review_count'],
                    correct_count=row['correct_count'],
                    last_reviewed=datetime.fromisoformat(row['last_reviewed']) if row['last_reviewed'] else None,
                    next_review=datetime.fromisoformat(row['next_review']) if row['next_review'] else None,
                    is_favorite=bool(row['is_favorite'])
                )
                
                review_words.append((vocab_word, user_vocab))
            
            return review_words
            
        except Exception as e:
            self.logger.error(f"Error getting words for review: {e}")
            return []
    
    async def get_user_vocabulary_stats(self, user_id: int, language: str = "english") -> Dict[str, Any]:
        """
        Get user's vocabulary learning statistics.
        
        Args:
            user_id: User identifier
            language: Language code
            
        Returns:
            Dictionary with vocabulary statistics
        """
        try:
            cursor = self.db_connection.cursor()
            
            # Total words learned
            cursor.execute("""
                SELECT COUNT(*) FROM user_vocabulary 
                WHERE user_id = ? AND language = ?
            """, (user_id, language))
            total_words = cursor.fetchone()[0]
            
            # Mastery level distribution
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN mastery_level >= 0.8 THEN 1 END) as mastered,
                    COUNT(CASE WHEN mastery_level >= 0.5 AND mastery_level < 0.8 THEN 1 END) as learning,
                    COUNT(CASE WHEN mastery_level < 0.5 THEN 1 END) as struggling,
                    AVG(mastery_level) as avg_mastery
                FROM user_vocabulary 
                WHERE user_id = ? AND language = ?
            """, (user_id, language))
            
            mastery_stats = cursor.fetchone()
            
            # Words due for review
            now = datetime.now().isoformat()
            cursor.execute("""
                SELECT COUNT(*) FROM user_vocabulary 
                WHERE user_id = ? AND language = ? 
                AND (next_review IS NULL OR next_review <= ?)
            """, (user_id, language, now))
            words_due = cursor.fetchone()[0]
            
            # Recent activity
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute("""
                SELECT COUNT(*) FROM user_vocabulary 
                WHERE user_id = ? AND language = ? 
                AND last_reviewed >= ?
            """, (user_id, language, week_ago))
            words_reviewed_week = cursor.fetchone()[0]
            
            return {
                "total_words": total_words,
                "mastered_words": mastery_stats['mastered'] or 0,
                "learning_words": mastery_stats['learning'] or 0,
                "struggling_words": mastery_stats['struggling'] or 0,
                "average_mastery": round(mastery_stats['avg_mastery'] or 0.0, 2),
                "words_due_for_review": words_due,
                "words_reviewed_this_week": words_reviewed_week,
                "mastery_percentage": round((mastery_stats['mastered'] or 0) / max(total_words, 1) * 100, 1)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting vocabulary stats: {e}")
            return {}
    
    async def search_words(
        self, 
        query: str, 
        language: str = "english",
        limit: int = 10
    ) -> List[VocabularyWord]:
        """
        Search for words by query.
        
        Args:
            query: Search query
            language: Language code
            limit: Maximum results
            
        Returns:
            List of matching vocabulary words
        """
        try:
            cursor = self.db_connection.cursor()
            
            # Search in word, definition, and categories
            search_pattern = f"%{query.lower()}%"
            cursor.execute("""
                SELECT * FROM vocabulary_words 
                WHERE language = ? AND (
                    LOWER(word) LIKE ? OR 
                    LOWER(definition) LIKE ? OR 
                    LOWER(categories) LIKE ?
                )
                ORDER BY 
                    CASE WHEN LOWER(word) = ? THEN 1 
                         WHEN LOWER(word) LIKE ? THEN 2 
                         ELSE 3 END,
                    frequency_rank ASC
                LIMIT ?
            """, (
                language, search_pattern, search_pattern, search_pattern,
                query.lower(), f"{query.lower()}%", limit
            ))
            
            words = []
            for row in cursor.fetchall():
                vocab_word = VocabularyWord(
                    word=row['word'],
                    language=row['language'],
                    part_of_speech=PartOfSpeech(row['part_of_speech']),
                    difficulty=WordDifficulty(row['difficulty']),
                    definition=row['definition'],
                    example_sentences=json.loads(row['example_sentences'] or '[]'),
                    synonyms=json.loads(row['synonyms'] or '[]'),
                    antonyms=json.loads(row['antonyms'] or '[]'),
                    categories=json.loads(row['categories'] or '[]'),
                    frequency_rank=row['frequency_rank']
                )
                words.append(vocab_word)
            
            return words
            
        except Exception as e:
            self.logger.error(f"Error searching words: {e}")
            return []
    
    def format_word_definition(self, vocab_word: VocabularyWord, include_examples: bool = True) -> str:
        """Format a word definition for display."""
        
        # Basic info
        result = f"**{vocab_word.word.title()}** ({vocab_word.part_of_speech.value})\n"
        result += f"*{vocab_word.difficulty.value.title()} level*\n\n"
        result += f"**Definition:** {vocab_word.definition}\n"
        
        # Examples
        if include_examples and vocab_word.example_sentences:
            result += f"\n**Examples:**\n"
            for i, example in enumerate(vocab_word.example_sentences[:2], 1):
                result += f"{i}. {example}\n"
        
        # Synonyms
        if vocab_word.synonyms:
            result += f"\n**Synonyms:** {', '.join(vocab_word.synonyms[:3])}"
        
        # Antonyms
        if vocab_word.antonyms:
            result += f"\n**Antonyms:** {', '.join(vocab_word.antonyms[:3])}"
        
        # Categories
        if vocab_word.categories:
            result += f"\n**Categories:** {', '.join(vocab_word.categories)}"
        
        return result
    
    async def cleanup(self) -> None:
        """Clean up vocabulary tool resources."""
        try:
            if self.db_connection:
                self.db_connection.close()
                self.db_connection = None
            
            self.word_cache.clear()
            self.logger.info("Vocabulary Tool cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up Vocabulary Tool: {e}")
    
    def __del__(self):
        """Destructor to ensure database connection is closed."""
        if hasattr(self, 'db_connection') and self.db_connection:
            self.db_connection.close()