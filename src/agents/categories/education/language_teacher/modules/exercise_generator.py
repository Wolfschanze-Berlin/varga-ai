"""
Exercise Generator Module - Creates dynamic language learning exercises.
Generates varied content based on user level and learning progress.
"""

import json
import random
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import re

from src.log_service import get_logger


class ExerciseType(Enum):
    """Types of exercises that can be generated."""
    VOCABULARY_MATCH = "vocabulary_match"
    GRAMMAR_FILL = "grammar_fill"
    SENTENCE_ORDER = "sentence_order"
    TRANSLATION = "translation"
    PRONUNCIATION = "pronunciation"
    READING_COMPREHENSION = "reading_comprehension"
    LISTENING_COMPREHENSION = "listening_comprehension"
    WORD_ASSOCIATION = "word_association"
    SYNONYM_ANTONYM = "synonym_antonym"
    CONJUGATION = "conjugation"


class DifficultyLevel(Enum):
    """Exercise difficulty levels."""
    BEGINNER = "beginner"
    ELEMENTARY = "elementary"
    INTERMEDIATE = "intermediate"
    UPPER_INTERMEDIATE = "upper_intermediate"
    ADVANCED = "advanced"


@dataclass
class GeneratedExercise:
    """A dynamically generated exercise."""
    id: str
    type: ExerciseType
    difficulty: DifficultyLevel
    language: str
    question: str
    options: Optional[List[str]] = None
    correct_answer: str = ""
    explanation: str = ""
    hints: List[str] = field(default_factory=list)
    points: int = 1
    estimated_time_minutes: int = 1
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class LanguageContent:
    """Content database for a specific language."""
    vocabulary: Dict[str, List[str]]  # level -> words
    grammar_patterns: Dict[str, List[str]]  # level -> patterns
    example_sentences: Dict[str, List[str]]  # level -> sentences
    reading_texts: Dict[str, List[str]]  # level -> texts
    common_phrases: Dict[str, List[str]]  # level -> phrases


class ExerciseGenerator:
    """
    Generates dynamic language learning exercises based on user level and progress.
    Creates varied content to keep learning engaging and challenging.
    """
    
    def __init__(self):
        """Initialize the exercise generator."""
        self.logger = get_logger("exercise_generator")
        
        # Content database
        self.language_content: Dict[str, LanguageContent] = {}
        
        # Exercise templates
        self.exercise_templates: Dict[ExerciseType, Dict] = {}
        
        # Difficulty scaling factors
        self.difficulty_factors = {
            DifficultyLevel.BEGINNER: {"complexity": 1, "vocabulary_size": 100, "sentence_length": 5},
            DifficultyLevel.ELEMENTARY: {"complexity": 2, "vocabulary_size": 300, "sentence_length": 8},
            DifficultyLevel.INTERMEDIATE: {"complexity": 3, "vocabulary_size": 800, "sentence_length": 12},
            DifficultyLevel.UPPER_INTERMEDIATE: {"complexity": 4, "vocabulary_size": 1500, "sentence_length": 15},
            DifficultyLevel.ADVANCED: {"complexity": 5, "vocabulary_size": 3000, "sentence_length": 20}
        }
        
    async def initialize(self) -> None:
        """Initialize the exercise generator with content and templates."""
        try:
            await self._load_language_content()
            await self._initialize_exercise_templates()
            
            self.logger.info("Exercise Generator initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Exercise Generator: {e}")
            raise
    
    async def _load_language_content(self) -> None:
        """Load language content database."""
        
        # English content
        english_content = LanguageContent(
            vocabulary={
                "beginner": [
                    "hello", "goodbye", "please", "thank you", "yes", "no", "good", "bad",
                    "big", "small", "hot", "cold", "happy", "sad", "cat", "dog", "house",
                    "car", "book", "water", "food", "love", "family", "friend", "work"
                ],
                "elementary": [
                    "beautiful", "important", "difficult", "interesting", "different", "similar",
                    "comfortable", "delicious", "expensive", "cheap", "amazing", "terrible",
                    "wonderful", "horrible", "fantastic", "brilliant", "convenient", "dangerous",
                    "exciting", "boring", "relaxing", "stressful", "peaceful", "noisy"
                ],
                "intermediate": [
                    "sophisticated", "comprehensive", "significant", "necessary", "appropriate",
                    "convenient", "efficient", "sufficient", "obvious", "particular",
                    "individual", "professional", "international", "traditional", "original",
                    "practical", "logical", "typical", "specific", "general"
                ],
                "advanced": [
                    "unprecedented", "quintessential", "ubiquitous", "ambiguous", "meticulous",
                    "serendipitous", "perspicacious", "magnanimous", "tenacious", "vivacious",
                    "gregarious", "loquacious", "efficacious", "voracious", "audacious"
                ]
            },
            grammar_patterns={
                "beginner": [
                    "I am {adjective}",
                    "This is a {noun}",
                    "I like {noun}",
                    "She has {noun}",
                    "We go to {place}"
                ],
                "elementary": [
                    "I have been {verb}ing for {time}",
                    "If I {verb}, I will {verb}",
                    "She is {comparative adjective} than {noun}",
                    "I would like to {verb}",
                    "Could you {verb} me?"
                ],
                "intermediate": [
                    "Although {clause}, {main clause}",
                    "Not only {clause}, but also {clause}",
                    "The more {adjective} {noun} is, the more {adjective} it becomes",
                    "Having {past participle}, {main clause}",
                    "I wish I {past perfect}"
                ]
            },
            example_sentences={
                "beginner": [
                    "The cat is sleeping on the chair.",
                    "I eat breakfast every morning.",
                    "She works in a big office.",
                    "We like to watch movies together.",
                    "The weather is very nice today."
                ],
                "elementary": [
                    "I have been studying English for two years.",
                    "If it rains tomorrow, we will stay inside.",
                    "This book is more interesting than the last one.",
                    "I would like to travel to Japan someday.",
                    "Could you help me with this problem?"
                ],
                "intermediate": [
                    "Although the weather was terrible, we decided to go hiking.",
                    "Not only did she finish her work early, but she also helped her colleagues.",
                    "The more I learn about languages, the more fascinated I become.",
                    "Having completed the project, the team celebrated their success.",
                    "I wish I had studied harder when I was younger."
                ]
            },
            reading_texts={
                "beginner": [
                    "Tom lives in a small house with his cat. Every morning, he drinks coffee and reads the news. He works in a bookstore downtown. Tom likes his job because he loves books.",
                    "Maria goes to school every day. She studies math, science, and English. Her favorite subject is art. After school, she plays with her friends in the park."
                ],
                "elementary": [
                    "Last summer, Jennifer decided to take a cooking class. She had always wanted to learn how to make pasta from scratch. The class was challenging but fun. Now she can make delicious Italian meals for her family.",
                    "The local community center offers many activities for residents. There are fitness classes, art workshops, and book clubs. These programs help people meet new friends and learn new skills."
                ],
                "intermediate": [
                    "Climate change has become one of the most pressing issues of our time. Scientists warn that rising temperatures could lead to severe weather patterns and environmental disruption. However, renewable energy technologies offer hope for a sustainable future. Many countries are now investing heavily in solar and wind power."
                ]
            },
            common_phrases={
                "beginner": [
                    "How are you?", "Nice to meet you", "Excuse me", "I'm sorry",
                    "Can you help me?", "Where is the bathroom?", "How much does it cost?",
                    "What time is it?", "I don't understand", "Could you repeat that?"
                ],
                "elementary": [
                    "I'd like to make a reservation", "Could I have the check, please?",
                    "I'm looking for...", "Do you have anything cheaper?",
                    "What would you recommend?", "I'm not feeling well",
                    "Could you speak more slowly?", "I'm running late"
                ]
            }
        )
        
        self.language_content["english"] = english_content
        
        # Spanish content (abbreviated)
        spanish_content = LanguageContent(
            vocabulary={
                "beginner": [
                    "hola", "adiós", "por favor", "gracias", "sí", "no", "bueno", "malo",
                    "grande", "pequeño", "caliente", "frío", "feliz", "triste", "gato", "perro",
                    "casa", "coche", "libro", "agua", "comida", "amor", "familia", "amigo"
                ],
                "elementary": [
                    "hermoso", "importante", "difícil", "interesante", "diferente", "similar",
                    "cómodo", "delicioso", "caro", "barato", "increíble", "terrible"
                ]
            },
            grammar_patterns={
                "beginner": [
                    "Yo soy {adjective}",
                    "Esto es un {noun}",
                    "Me gusta {noun}",
                    "Ella tiene {noun}",
                    "Vamos a {place}"
                ]
            },
            example_sentences={
                "beginner": [
                    "El gato está durmiendo en la silla.",
                    "Yo desayuno todas las mañanas.",
                    "Ella trabaja en una oficina grande."
                ]
            },
            reading_texts={
                "beginner": [
                    "María vive en una casa pequeña con su perro. Cada mañana, bebe café y lee el periódico. Trabaja en una librería en el centro. A María le gusta su trabajo porque ama los libros."
                ]
            },
            common_phrases={
                "beginner": [
                    "¿Cómo estás?", "Mucho gusto", "Disculpe", "Lo siento",
                    "¿Puedes ayudarme?", "¿Dónde está el baño?", "¿Cuánto cuesta?",
                    "¿Qué hora es?", "No entiendo", "¿Puedes repetir?"
                ]
            }
        )
        
        self.language_content["spanish"] = spanish_content
    
    async def _initialize_exercise_templates(self) -> None:
        """Initialize exercise generation templates."""
        
        self.exercise_templates = {
            ExerciseType.VOCABULARY_MATCH: {
                "question_template": "What does '{word}' mean?",
                "points_base": 1,
                "time_base": 1
            },
            
            ExerciseType.GRAMMAR_FILL: {
                "question_template": "Complete the sentence: {sentence_with_blank}",
                "points_base": 2,
                "time_base": 2
            },
            
            ExerciseType.SENTENCE_ORDER: {
                "question_template": "Put these words in the correct order:",
                "points_base": 2,
                "time_base": 2
            },
            
            ExerciseType.TRANSLATION: {
                "question_template": "Translate to {target_language}: {text}",
                "points_base": 3,
                "time_base": 3
            },
            
            ExerciseType.READING_COMPREHENSION: {
                "question_template": "Read the text and answer: {question}",
                "points_base": 3,
                "time_base": 4
            },
            
            ExerciseType.WORD_ASSOCIATION: {
                "question_template": "Which word is most related to '{word}'?",
                "points_base": 1,
                "time_base": 1
            },
            
            ExerciseType.SYNONYM_ANTONYM: {
                "question_template": "What is a {type} of '{word}'?",
                "points_base": 2,
                "time_base": 2
            }
        }
    
    async def generate_exercise(
        self,
        exercise_type: ExerciseType,
        language: str,
        difficulty: DifficultyLevel,
        user_progress: Optional[Dict[str, Any]] = None,
        topic_focus: Optional[str] = None
    ) -> Optional[GeneratedExercise]:
        """
        Generate a specific type of exercise.
        
        Args:
            exercise_type: Type of exercise to generate
            language: Target language
            difficulty: Difficulty level
            user_progress: Optional user progress data for personalization
            topic_focus: Optional topic to focus on
            
        Returns:
            Generated exercise or None if generation failed
        """
        try:
            # Check if language content exists
            if language not in self.language_content:
                self.logger.warning(f"No content available for language: {language}")
                return None
            
            content = self.language_content[language]
            
            # Generate based on exercise type
            if exercise_type == ExerciseType.VOCABULARY_MATCH:
                return await self._generate_vocabulary_match(content, language, difficulty)
            elif exercise_type == ExerciseType.GRAMMAR_FILL:
                return await self._generate_grammar_fill(content, language, difficulty)
            elif exercise_type == ExerciseType.SENTENCE_ORDER:
                return await self._generate_sentence_order(content, language, difficulty)
            elif exercise_type == ExerciseType.TRANSLATION:
                return await self._generate_translation(content, language, difficulty)
            elif exercise_type == ExerciseType.READING_COMPREHENSION:
                return await self._generate_reading_comprehension(content, language, difficulty)
            elif exercise_type == ExerciseType.WORD_ASSOCIATION:
                return await self._generate_word_association(content, language, difficulty)
            elif exercise_type == ExerciseType.SYNONYM_ANTONYM:
                return await self._generate_synonym_antonym(content, language, difficulty)
            else:
                self.logger.warning(f"Exercise type {exercise_type} not implemented")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating {exercise_type} exercise: {e}")
            return None
    
    async def _generate_vocabulary_match(
        self,
        content: LanguageContent,
        language: str,
        difficulty: DifficultyLevel
    ) -> GeneratedExercise:
        """Generate a vocabulary matching exercise."""
        
        # Get vocabulary for the level
        vocab_list = content.vocabulary.get(difficulty.value, content.vocabulary.get("beginner", []))
        
        if not vocab_list:
            raise ValueError(f"No vocabulary available for {difficulty.value}")
        
        # Select a random word
        target_word = random.choice(vocab_list)
        
        # Create definitions/meanings (simplified)
        word_meanings = {
            "hello": "A greeting used when meeting someone",
            "beautiful": "Very attractive or pleasing to look at",
            "important": "Having great significance or value",
            "sophisticated": "Having complex or refined characteristics",
            "house": "A building for human habitation",
            "happy": "Feeling joy or pleasure",
            "difficult": "Hard to do or understand",
            "book": "A written or printed work of literature"
        }
        
        correct_meaning = word_meanings.get(target_word, f"Related to {target_word}")
        
        # Create distractors
        other_words = [w for w in vocab_list if w != target_word]
        distractors = []
        
        for word in random.sample(other_words, min(3, len(other_words))):
            distractors.append(word_meanings.get(word, f"Related to {word}"))
        
        options = [correct_meaning] + distractors
        random.shuffle(options)
        
        template = self.exercise_templates[ExerciseType.VOCABULARY_MATCH]
        points = template["points_base"] * self.difficulty_factors[difficulty]["complexity"]
        
        return GeneratedExercise(
            id=f"vocab_{datetime.now().timestamp()}",
            type=ExerciseType.VOCABULARY_MATCH,
            difficulty=difficulty,
            language=language,
            question=template["question_template"].format(word=target_word),
            options=options,
            correct_answer=correct_meaning,
            explanation=f"'{target_word}' means: {correct_meaning}",
            hints=[f"Think about when you might use '{target_word}'"],
            points=points,
            estimated_time_minutes=template["time_base"],
            tags=["vocabulary", difficulty.value]
        )
    
    async def _generate_grammar_fill(
        self,
        content: LanguageContent,
        language: str,
        difficulty: DifficultyLevel
    ) -> GeneratedExercise:
        """Generate a grammar fill-in-the-blank exercise."""
        
        sentences = content.example_sentences.get(difficulty.value, [])
        if not sentences:
            raise ValueError(f"No sentences available for {difficulty.value}")
        
        sentence = random.choice(sentences)
        
        # Create a blank by removing a word (simplified approach)
        words = sentence.split()
        if len(words) < 3:
            raise ValueError("Sentence too short for fill exercise")
        
        # Remove a key word (not articles or prepositions)
        skip_words = {"a", "an", "the", "in", "on", "at", "to", "of", "for", "with"}
        removable_words = [(i, word) for i, word in enumerate(words) 
                          if word.lower().strip('.,!?') not in skip_words]
        
        if not removable_words:
            blank_index = len(words) // 2
            removed_word = words[blank_index]
        else:
            blank_index, removed_word = random.choice(removable_words)
        
        # Clean the removed word
        removed_word_clean = re.sub(r'[.,!?]', '', removed_word)
        
        # Create sentence with blank
        sentence_with_blank = words.copy()
        sentence_with_blank[blank_index] = "____"
        sentence_with_blank = " ".join(sentence_with_blank)
        
        # Create options
        vocab_list = content.vocabulary.get(difficulty.value, [])
        distractors = random.sample([w for w in vocab_list if w != removed_word_clean.lower()], 
                                  min(3, len(vocab_list)))
        
        options = [removed_word_clean] + distractors
        random.shuffle(options)
        
        template = self.exercise_templates[ExerciseType.GRAMMAR_FILL]
        points = template["points_base"] * self.difficulty_factors[difficulty]["complexity"]
        
        return GeneratedExercise(
            id=f"grammar_{datetime.now().timestamp()}",
            type=ExerciseType.GRAMMAR_FILL,
            difficulty=difficulty,
            language=language,
            question=template["question_template"].format(sentence_with_blank=sentence_with_blank),
            options=options,
            correct_answer=removed_word_clean,
            explanation=f"The correct word is '{removed_word_clean}' because it fits the grammatical structure.",
            hints=[f"Think about what type of word fits here", "Consider the sentence context"],
            points=points,
            estimated_time_minutes=template["time_base"],
            tags=["grammar", difficulty.value]
        )
    
    async def _generate_sentence_order(
        self,
        content: LanguageContent,
        language: str,
        difficulty: DifficultyLevel
    ) -> GeneratedExercise:
        """Generate a sentence ordering exercise."""
        
        sentences = content.example_sentences.get(difficulty.value, [])
        if not sentences:
            raise ValueError(f"No sentences available for {difficulty.value}")
        
        sentence = random.choice(sentences)
        
        # Remove punctuation for the exercise
        clean_sentence = re.sub(r'[.,!?]', '', sentence)
        words = clean_sentence.split()
        
        # Shuffle words
        shuffled_words = words.copy()
        random.shuffle(shuffled_words)
        
        # Make sure it's actually shuffled
        attempts = 0
        while shuffled_words == words and attempts < 10:
            random.shuffle(shuffled_words)
            attempts += 1
        
        template = self.exercise_templates[ExerciseType.SENTENCE_ORDER]
        points = template["points_base"] * self.difficulty_factors[difficulty]["complexity"]
        
        return GeneratedExercise(
            id=f"order_{datetime.now().timestamp()}",
            type=ExerciseType.SENTENCE_ORDER,
            difficulty=difficulty,
            language=language,
            question=f"{template['question_template']} [{' / '.join(shuffled_words)}]",
            correct_answer=clean_sentence,
            explanation=f"The correct order is: '{clean_sentence}'",
            hints=[
                "Start with the subject of the sentence",
                "Think about basic sentence structure: subject + verb + object",
                f"The sentence should make grammatical sense"
            ],
            points=points,
            estimated_time_minutes=template["time_base"],
            tags=["sentence_structure", "grammar", difficulty.value]
        )
    
    async def _generate_translation(
        self,
        content: LanguageContent,
        language: str,
        difficulty: DifficultyLevel
    ) -> GeneratedExercise:
        """Generate a translation exercise."""
        
        # For this example, assume we're translating from English to the target language
        if language == "english":
            # Translate from Spanish to English
            source_phrases = self.language_content.get("spanish", content).common_phrases.get(difficulty.value, [])
            translations = {
                "¿Cómo estás?": "How are you?",
                "Mucho gusto": "Nice to meet you",
                "Disculpe": "Excuse me",
                "Lo siento": "I'm sorry"
            }
        else:
            # Translate from English to target language
            source_phrases = content.common_phrases.get(difficulty.value, [])
            if language == "spanish":
                translations = {
                    "How are you?": "¿Cómo estás?",
                    "Nice to meet you": "Mucho gusto",
                    "Excuse me": "Disculpe",
                    "I'm sorry": "Lo siento"
                }
            else:
                translations = {}
        
        if not source_phrases or not translations:
            raise ValueError(f"No translation data available")
        
        # Select a phrase that has a translation
        available_phrases = [p for p in source_phrases if p in translations]
        if not available_phrases:
            raise ValueError("No translatable phrases available")
        
        source_phrase = random.choice(available_phrases)
        correct_translation = translations[source_phrase]
        
        template = self.exercise_templates[ExerciseType.TRANSLATION]
        points = template["points_base"] * self.difficulty_factors[difficulty]["complexity"]
        
        return GeneratedExercise(
            id=f"translation_{datetime.now().timestamp()}",
            type=ExerciseType.TRANSLATION,
            difficulty=difficulty,
            language=language,
            question=template["question_template"].format(
                target_language=language.title(),
                text=source_phrase
            ),
            correct_answer=correct_translation,
            explanation=f"'{source_phrase}' translates to '{correct_translation}'",
            hints=[
                "Think about the meaning, not word-by-word translation",
                "Consider cultural context",
                "Focus on natural expression"
            ],
            points=points,
            estimated_time_minutes=template["time_base"],
            tags=["translation", difficulty.value]
        )
    
    async def _generate_reading_comprehension(
        self,
        content: LanguageContent,
        language: str,
        difficulty: DifficultyLevel
    ) -> GeneratedExercise:
        """Generate a reading comprehension exercise."""
        
        texts = content.reading_texts.get(difficulty.value, [])
        if not texts:
            raise ValueError(f"No reading texts available for {difficulty.value}")
        
        text = random.choice(texts)
        
        # Generate questions based on the text (simplified)
        questions = [
            "What is the main topic of this text?",
            "Who is the main character mentioned?",
            "Where does this story take place?",
            "What activity is described in the text?",
            "How does the author feel about the topic?"
        ]
        
        question = random.choice(questions)
        
        # Create a plausible answer (this would be more sophisticated in practice)
        words = text.split()
        
        # Extract potential answers from the text
        if "main topic" in question.lower():
            answer = "The text is about daily life and activities"
        elif "main character" in question.lower():
            # Look for names (capitalized words that aren't at start of sentences)
            names = [word.strip('.,!?') for word in words if word[0].isupper() and 
                    words.index(word) > 0 and not words[words.index(word)-1].endswith('.')]
            answer = names[0] if names else "The main character"
        else:
            answer = "Based on the text content"
        
        template = self.exercise_templates[ExerciseType.READING_COMPREHENSION]
        points = template["points_base"] * self.difficulty_factors[difficulty]["complexity"]
        
        return GeneratedExercise(
            id=f"reading_{datetime.now().timestamp()}",
            type=ExerciseType.READING_COMPREHENSION,
            difficulty=difficulty,
            language=language,
            question=f"Read this text:\n\n\"{text}\"\n\n{question}",
            correct_answer=answer,
            explanation=f"The answer can be found by carefully reading the text.",
            hints=[
                "Read the text carefully",
                "Look for key words related to the question",
                "Consider the overall meaning"
            ],
            points=points,
            estimated_time_minutes=template["time_base"],
            tags=["reading", "comprehension", difficulty.value]
        )
    
    async def _generate_word_association(
        self,
        content: LanguageContent,
        language: str,
        difficulty: DifficultyLevel
    ) -> GeneratedExercise:
        """Generate a word association exercise."""
        
        vocab_list = content.vocabulary.get(difficulty.value, [])
        if len(vocab_list) < 4:
            raise ValueError("Not enough vocabulary for word association")
        
        # Create word associations (simplified)
        associations = {
            "cat": "animal", "dog": "animal", "house": "building", "car": "vehicle",
            "hot": "temperature", "cold": "temperature", "happy": "emotion", "sad": "emotion",
            "beautiful": "appearance", "important": "significance", "difficult": "challenge"
        }
        
        # Select a word that has an association
        available_words = [w for w in vocab_list if w in associations]
        if not available_words:
            # Fallback: use any word
            target_word = random.choice(vocab_list)
            correct_association = "related concept"
        else:
            target_word = random.choice(available_words)
            correct_association = associations[target_word]
        
        # Create options
        all_associations = list(set(associations.values()))
        if correct_association in all_associations:
            other_associations = [a for a in all_associations if a != correct_association]
            distractors = random.sample(other_associations, min(3, len(other_associations)))
        else:
            distractors = random.sample(all_associations, min(3, len(all_associations)))
        
        options = [correct_association] + distractors
        random.shuffle(options)
        
        template = self.exercise_templates[ExerciseType.WORD_ASSOCIATION]
        points = template["points_base"] * self.difficulty_factors[difficulty]["complexity"]
        
        return GeneratedExercise(
            id=f"association_{datetime.now().timestamp()}",
            type=ExerciseType.WORD_ASSOCIATION,
            difficulty=difficulty,
            language=language,
            question=template["question_template"].format(word=target_word),
            options=options,
            correct_answer=correct_association,
            explanation=f"'{target_word}' is most closely related to '{correct_association}'",
            hints=[f"Think about what category '{target_word}' belongs to"],
            points=points,
            estimated_time_minutes=template["time_base"],
            tags=["vocabulary", "association", difficulty.value]
        )
    
    async def _generate_synonym_antonym(
        self,
        content: LanguageContent,
        language: str,
        difficulty: DifficultyLevel
    ) -> GeneratedExercise:
        """Generate a synonym or antonym exercise."""
        
        vocab_list = content.vocabulary.get(difficulty.value, [])
        if not vocab_list:
            raise ValueError("No vocabulary available")
        
        # Synonym/antonym pairs (simplified)
        synonyms = {
            "happy": "joyful", "sad": "unhappy", "big": "large", "small": "tiny",
            "beautiful": "pretty", "important": "significant", "difficult": "hard",
            "good": "excellent", "bad": "terrible"
        }
        
        antonyms = {
            "happy": "sad", "good": "bad", "big": "small", "hot": "cold",
            "beautiful": "ugly", "easy": "difficult", "fast": "slow"
        }
        
        # Choose synonym or antonym
        exercise_type = random.choice(["synonym", "antonym"])
        
        if exercise_type == "synonym":
            available_words = [w for w in vocab_list if w in synonyms]
            word_pairs = synonyms
        else:
            available_words = [w for w in vocab_list if w in antonyms]
            word_pairs = antonyms
        
        if not available_words:
            # Fallback to any word with a made-up answer
            target_word = random.choice(vocab_list)
            correct_answer = f"related to {target_word}"
        else:
            target_word = random.choice(available_words)
            correct_answer = word_pairs[target_word]
        
        # Create distractors
        other_vocab = [w for w in vocab_list if w != target_word and w != correct_answer]
        distractors = random.sample(other_vocab, min(3, len(other_vocab)))
        
        options = [correct_answer] + distractors
        random.shuffle(options)
        
        template = self.exercise_templates[ExerciseType.SYNONYM_ANTONYM]
        points = template["points_base"] * self.difficulty_factors[difficulty]["complexity"]
        
        return GeneratedExercise(
            id=f"{exercise_type}_{datetime.now().timestamp()}",
            type=ExerciseType.SYNONYM_ANTONYM,
            difficulty=difficulty,
            language=language,
            question=template["question_template"].format(type=exercise_type, word=target_word),
            options=options,
            correct_answer=correct_answer,
            explanation=f"'{correct_answer}' is a {exercise_type} of '{target_word}'",
            hints=[f"Think of a word that means the {'same as' if exercise_type == 'synonym' else 'opposite of'} '{target_word}'"],
            points=points,
            estimated_time_minutes=template["time_base"],
            tags=["vocabulary", exercise_type, difficulty.value]
        )
    
    async def generate_random_exercise(
        self,
        language: str,
        difficulty: DifficultyLevel,
        exclude_types: Optional[List[ExerciseType]] = None
    ) -> Optional[GeneratedExercise]:
        """Generate a random exercise for the given parameters."""
        
        available_types = [t for t in ExerciseType if t not in (exclude_types or [])]
        
        if not available_types:
            return None
        
        exercise_type = random.choice(available_types)
        return await self.generate_exercise(exercise_type, language, difficulty)
    
    async def generate_exercise_set(
        self,
        language: str,
        difficulty: DifficultyLevel,
        count: int = 5,
        variety: bool = True
    ) -> List[GeneratedExercise]:
        """
        Generate a set of exercises.
        
        Args:
            language: Target language
            difficulty: Difficulty level
            count: Number of exercises to generate
            variety: Whether to ensure variety in exercise types
            
        Returns:
            List of generated exercises
        """
        exercises = []
        used_types = set()
        
        for _ in range(count):
            if variety and len(used_types) < len(ExerciseType):
                # Ensure variety by excluding used types
                exclude_types = list(used_types) if len(used_types) < len(ExerciseType) else []
            else:
                exclude_types = []
            
            exercise = await self.generate_random_exercise(language, difficulty, exclude_types)
            
            if exercise:
                exercises.append(exercise)
                used_types.add(exercise.type)
        
        return exercises
    
    def get_exercise_stats(self) -> Dict[str, Any]:
        """Get statistics about exercise generation capabilities."""
        return {
            "supported_languages": list(self.language_content.keys()),
            "exercise_types": [t.value for t in ExerciseType],
            "difficulty_levels": [d.value for d in DifficultyLevel],
            "total_templates": len(self.exercise_templates)
        }
    
    async def cleanup(self) -> None:
        """Clean up exercise generator resources."""
        self.language_content.clear()
        self.exercise_templates.clear()
        self.logger.info("Exercise Generator cleaned up")