"""
Content Generator for dynamic learning content creation.
"""

import json
import random
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import string

from src.log_service import get_logger


class ContentType(Enum):
    """Types of learning content."""
    VOCABULARY = "vocabulary"
    GRAMMAR = "grammar"
    CONVERSATION = "conversation"
    READING = "reading"
    LISTENING = "listening"
    WRITING = "writing"
    PRONUNCIATION = "pronunciation"
    QUIZ = "quiz"
    STORY = "story"
    EXERCISE = "exercise"


class DifficultyLevel(Enum):
    """Content difficulty levels."""
    BEGINNER = "beginner"
    ELEMENTARY = "elementary"
    INTERMEDIATE = "intermediate"
    UPPER_INTERMEDIATE = "upper_intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class GeneratedContent:
    """Generated learning content."""
    content_id: str
    content_type: ContentType
    difficulty_level: DifficultyLevel
    title: str
    content: Dict[str, Any]
    instructions: str
    expected_response: Optional[str] = None
    hints: List[str] = None
    metadata: Dict[str, Any] = None
    knowledge_components: List[str] = None
    estimated_time: int = 5  # minutes
    created_at: datetime = None
    
    def __post_init__(self):
        if self.hints is None:
            self.hints = []
        if self.metadata is None:
            self.metadata = {}
        if self.knowledge_components is None:
            self.knowledge_components = []
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class ContentTemplate:
    """Template for content generation."""
    template_id: str
    content_type: ContentType
    difficulty_range: Tuple[DifficultyLevel, DifficultyLevel]
    template_structure: Dict[str, Any]
    variables: List[str]
    knowledge_components: List[str]


class ContentGenerator:
    """
    Dynamic content generator for personalized learning materials.
    
    Features:
    - Adaptive content generation based on difficulty
    - Context-aware exercise creation
    - Personalized scenarios and examples
    - Multiple content types support
    - Template-based generation
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize content generator.
        
        Args:
            config: Configuration dictionary
        """
        self.logger = get_logger("content_generator")
        
        # Configuration
        self.config = config or {}
        self.target_language = self.config.get('target_language', 'english')
        
        # Content templates
        self.templates: Dict[str, ContentTemplate] = {}
        
        # Vocabulary databases
        self.vocabulary_db = self._load_vocabulary_database()
        self.grammar_patterns = self._load_grammar_patterns()
        self.conversation_templates = self._load_conversation_templates()
        
        # Content generation rules
        self.difficulty_mappings = {
            DifficultyLevel.BEGINNER: {
                'vocab_complexity': 0.2,
                'sentence_length': (3, 8),
                'grammar_complexity': 0.3,
                'topics': ['daily_life', 'family', 'food', 'colors', 'numbers']
            },
            DifficultyLevel.ELEMENTARY: {
                'vocab_complexity': 0.4,
                'sentence_length': (5, 12),
                'grammar_complexity': 0.5,
                'topics': ['school', 'work', 'hobbies', 'weather', 'shopping']
            },
            DifficultyLevel.INTERMEDIATE: {
                'vocab_complexity': 0.6,
                'sentence_length': (8, 15),
                'grammar_complexity': 0.7,
                'topics': ['travel', 'culture', 'technology', 'health', 'environment']
            },
            DifficultyLevel.UPPER_INTERMEDIATE: {
                'vocab_complexity': 0.8,
                'sentence_length': (10, 18),
                'grammar_complexity': 0.8,
                'topics': ['business', 'politics', 'science', 'literature', 'philosophy']
            },
            DifficultyLevel.ADVANCED: {
                'vocab_complexity': 0.9,
                'sentence_length': (12, 25),
                'grammar_complexity': 0.9,
                'topics': ['academic', 'professional', 'abstract_concepts', 'critical_thinking']
            }
        }
        
        # Initialize templates
        self._initialize_templates()
        
        self.logger.info("Initialized Content Generator")
    
    def _load_vocabulary_database(self) -> Dict[str, Dict[str, Any]]:
        """Load vocabulary database organized by difficulty and topic."""
        return {
            'beginner': {
                'daily_life': ['hello', 'goodbye', 'please', 'thank you', 'yes', 'no'],
                'family': ['mother', 'father', 'sister', 'brother', 'family', 'child'],
                'food': ['eat', 'drink', 'food', 'water', 'bread', 'fruit'],
                'colors': ['red', 'blue', 'green', 'yellow', 'black', 'white'],
                'numbers': ['one', 'two', 'three', 'four', 'five', 'ten']
            },
            'elementary': {
                'school': ['teacher', 'student', 'book', 'pen', 'classroom', 'homework'],
                'work': ['job', 'office', 'computer', 'meeting', 'colleague', 'salary'],
                'hobbies': ['read', 'music', 'sports', 'painting', 'cooking', 'travel'],
                'weather': ['sunny', 'rainy', 'cloudy', 'hot', 'cold', 'weather'],
                'shopping': ['buy', 'sell', 'price', 'money', 'store', 'customer']
            },
            'intermediate': {
                'travel': ['journey', 'destination', 'adventure', 'explore', 'culture', 'experience'],
                'technology': ['computer', 'internet', 'software', 'digital', 'innovation', 'device'],
                'health': ['exercise', 'nutrition', 'medicine', 'hospital', 'wellness', 'treatment'],
                'environment': ['nature', 'pollution', 'conservation', 'climate', 'sustainable', 'ecosystem']
            },
            'advanced': {
                'business': ['strategy', 'investment', 'entrepreneurship', 'management', 'profit', 'market'],
                'science': ['research', 'experiment', 'hypothesis', 'analysis', 'discovery', 'theory'],
                'abstract': ['concept', 'perspective', 'philosophy', 'consciousness', 'existence', 'reality']
            }
        }
    
    def _load_grammar_patterns(self) -> Dict[str, List[str]]:
        """Load grammar patterns by difficulty."""
        return {
            'beginner': [
                "Subject + Verb",
                "Subject + Verb + Object",
                "Simple present tense",
                "Basic questions (What, Where, Who)"
            ],
            'elementary': [
                "Past tense",
                "Future tense (will)",
                "Prepositions of place",
                "Comparative adjectives"
            ],
            'intermediate': [
                "Present perfect",
                "Conditional sentences",
                "Passive voice",
                "Relative clauses"
            ],
            'advanced': [
                "Subjunctive mood",
                "Complex conditional",
                "Advanced passive constructions",
                "Reported speech variations"
            ]
        }
    
    def _load_conversation_templates(self) -> Dict[str, List[str]]:
        """Load conversation templates by scenario."""
        return {
            'greeting': [
                "Hello! How are you today?",
                "Good morning! Nice to see you.",
                "Hi there! How's everything going?"
            ],
            'ordering_food': [
                "I'd like to order {food_item}, please.",
                "Could I have {food_item} with {side_dish}?",
                "What do you recommend for {meal_type}?"
            ],
            'asking_directions': [
                "Excuse me, how do I get to {destination}?",
                "Could you tell me where {location} is?",
                "Is {destination} far from here?"
            ],
            'shopping': [
                "How much does {item} cost?",
                "Do you have {item} in {color}?",
                "Where can I find {item_category}?"
            ]
        }
    
    def _initialize_templates(self) -> None:
        """Initialize content generation templates."""
        try:
            # Vocabulary template
            vocab_template = ContentTemplate(
                template_id="vocab_flashcard",
                content_type=ContentType.VOCABULARY,
                difficulty_range=(DifficultyLevel.BEGINNER, DifficultyLevel.ADVANCED),
                template_structure={
                    'word': '{target_word}',
                    'definition': '{definition}',
                    'example_sentence': '{example}',
                    'pronunciation': '{pronunciation_guide}'
                },
                variables=['target_word', 'definition', 'example', 'pronunciation_guide'],
                knowledge_components=['vocabulary', 'word_recognition']
            )
            self.templates[vocab_template.template_id] = vocab_template
            
            # Grammar template
            grammar_template = ContentTemplate(
                template_id="grammar_exercise",
                content_type=ContentType.GRAMMAR,
                difficulty_range=(DifficultyLevel.ELEMENTARY, DifficultyLevel.ADVANCED),
                template_structure={
                    'rule': '{grammar_rule}',
                    'example': '{example_sentence}',
                    'exercise': '{fill_in_blank}',
                    'options': ['{option1}', '{option2}', '{option3}', '{option4}']
                },
                variables=['grammar_rule', 'example_sentence', 'fill_in_blank', 'option1', 'option2', 'option3', 'option4'],
                knowledge_components=['grammar', 'sentence_structure']
            )
            self.templates[grammar_template.template_id] = grammar_template
            
            # Conversation template
            conversation_template = ContentTemplate(
                template_id="conversation_practice",
                content_type=ContentType.CONVERSATION,
                difficulty_range=(DifficultyLevel.BEGINNER, DifficultyLevel.INTERMEDIATE),
                template_structure={
                    'scenario': '{scenario_description}',
                    'dialogue': ['{line1}', '{line2}', '{line3}'],
                    'your_turn': '{student_response_prompt}'
                },
                variables=['scenario_description', 'line1', 'line2', 'line3', 'student_response_prompt'],
                knowledge_components=['conversation', 'practical_usage']
            )
            self.templates[conversation_template.template_id] = conversation_template
            
            self.logger.debug("Initialized content templates")
            
        except Exception as e:
            self.logger.error(f"Error initializing templates: {e}")
    
    def generate_vocabulary_content(self, difficulty: DifficultyLevel, 
                                  topic: str = None, count: int = 1) -> List[GeneratedContent]:
        """
        Generate vocabulary learning content.
        
        Args:
            difficulty: Target difficulty level
            topic: Specific topic (optional)
            count: Number of vocabulary items to generate
            
        Returns:
            List of generated vocabulary content
        """
        try:
            content_list = []
            difficulty_key = difficulty.value.lower()
            
            # Get available topics for difficulty
            if difficulty_key not in self.vocabulary_db:
                difficulty_key = 'beginner'  # Fallback
            
            available_topics = list(self.vocabulary_db[difficulty_key].keys())
            
            for i in range(count):
                # Select topic
                if topic and topic in self.vocabulary_db[difficulty_key]:
                    selected_topic = topic
                else:
                    selected_topic = random.choice(available_topics)
                
                # Select word
                words = self.vocabulary_db[difficulty_key][selected_topic]
                target_word = random.choice(words)
                
                # Generate content
                content_id = f"vocab_{difficulty.value}_{target_word}_{int(datetime.now().timestamp())}"
                
                # Create simple definition and example
                definition = self._generate_definition(target_word, difficulty)
                example_sentence = self._generate_example_sentence(target_word, difficulty)
                pronunciation = self._generate_pronunciation_guide(target_word)
                
                content = GeneratedContent(
                    content_id=content_id,
                    content_type=ContentType.VOCABULARY,
                    difficulty_level=difficulty,
                    title=f"Learn: {target_word.title()}",
                    content={
                        'word': target_word,
                        'definition': definition,
                        'example_sentence': example_sentence,
                        'pronunciation': pronunciation,
                        'topic': selected_topic
                    },
                    instructions=f"Learn the word '{target_word}' and its meaning. Try to use it in your own sentence.",
                    expected_response=target_word,
                    hints=[
                        f"This word is related to {selected_topic}",
                        f"The word starts with '{target_word[0].upper()}'"
                    ],
                    knowledge_components=['vocabulary', selected_topic],
                    estimated_time=3
                )
                
                content_list.append(content)
            
            return content_list
            
        except Exception as e:
            self.logger.error(f"Error generating vocabulary content: {e}")
            return []
    
    def generate_grammar_content(self, difficulty: DifficultyLevel, 
                               grammar_focus: str = None) -> GeneratedContent:
        """
        Generate grammar exercise content.
        
        Args:
            difficulty: Target difficulty level
            grammar_focus: Specific grammar point (optional)
            
        Returns:
            Generated grammar content
        """
        try:
            difficulty_key = difficulty.value.lower()
            
            # Select grammar pattern
            if grammar_focus:
                grammar_rule = grammar_focus
            else:
                available_patterns = self.grammar_patterns.get(difficulty_key, ['basic_grammar'])
                grammar_rule = random.choice(available_patterns)
            
            # Generate exercise based on grammar rule
            content_id = f"grammar_{difficulty.value}_{int(datetime.now().timestamp())}"
            
            if 'present' in grammar_rule.lower():
                exercise_content = self._generate_present_tense_exercise(difficulty)
            elif 'past' in grammar_rule.lower():
                exercise_content = self._generate_past_tense_exercise(difficulty)
            elif 'question' in grammar_rule.lower():
                exercise_content = self._generate_question_exercise(difficulty)
            else:
                exercise_content = self._generate_basic_grammar_exercise(difficulty)
            
            content = GeneratedContent(
                content_id=content_id,
                content_type=ContentType.GRAMMAR,
                difficulty_level=difficulty,
                title=f"Grammar Practice: {grammar_rule}",
                content=exercise_content,
                instructions=f"Complete the grammar exercise focusing on {grammar_rule}.",
                expected_response=exercise_content.get('correct_answer'),
                hints=exercise_content.get('hints', []),
                knowledge_components=['grammar', grammar_rule.lower().replace(' ', '_')],
                estimated_time=5
            )
            
            return content
            
        except Exception as e:
            self.logger.error(f"Error generating grammar content: {e}")
            return self._generate_fallback_content(ContentType.GRAMMAR, difficulty)
    
    def generate_conversation_content(self, difficulty: DifficultyLevel, 
                                    scenario: str = None) -> GeneratedContent:
        """
        Generate conversation practice content.
        
        Args:
            difficulty: Target difficulty level
            scenario: Conversation scenario (optional)
            
        Returns:
            Generated conversation content
        """
        try:
            # Select scenario
            if scenario and scenario in self.conversation_templates:
                selected_scenario = scenario
            else:
                available_scenarios = list(self.conversation_templates.keys())
                selected_scenario = random.choice(available_scenarios)
            
            # Generate conversation
            content_id = f"conversation_{difficulty.value}_{selected_scenario}_{int(datetime.now().timestamp())}"
            
            conversation_data = self._generate_conversation_dialogue(
                selected_scenario, difficulty
            )
            
            content = GeneratedContent(
                content_id=content_id,
                content_type=ContentType.CONVERSATION,
                difficulty_level=difficulty,
                title=f"Conversation: {selected_scenario.replace('_', ' ').title()}",
                content=conversation_data,
                instructions=f"Practice this {selected_scenario.replace('_', ' ')} conversation. Read the dialogue and respond appropriately.",
                expected_response=conversation_data.get('expected_response'),
                hints=conversation_data.get('hints', []),
                knowledge_components=['conversation', selected_scenario],
                estimated_time=8
            )
            
            return content
            
        except Exception as e:
            self.logger.error(f"Error generating conversation content: {e}")
            return self._generate_fallback_content(ContentType.CONVERSATION, difficulty)
    
    def generate_reading_content(self, difficulty: DifficultyLevel, 
                               topic: str = None, length: str = "short") -> GeneratedContent:
        """
        Generate reading comprehension content.
        
        Args:
            difficulty: Target difficulty level
            topic: Reading topic (optional)
            length: Content length ("short", "medium", "long")
            
        Returns:
            Generated reading content
        """
        try:
            # Select topic
            difficulty_mapping = self.difficulty_mappings.get(difficulty, self.difficulty_mappings[DifficultyLevel.BEGINNER])
            available_topics = difficulty_mapping['topics']
            
            if topic and topic in available_topics:
                selected_topic = topic
            else:
                selected_topic = random.choice(available_topics)
            
            # Generate reading passage
            content_id = f"reading_{difficulty.value}_{selected_topic}_{int(datetime.now().timestamp())}"
            
            reading_data = self._generate_reading_passage(
                selected_topic, difficulty, length
            )
            
            content = GeneratedContent(
                content_id=content_id,
                content_type=ContentType.READING,
                difficulty_level=difficulty,
                title=f"Reading: {selected_topic.replace('_', ' ').title()}",
                content=reading_data,
                instructions="Read the passage carefully and answer the comprehension questions.",
                expected_response=reading_data.get('answers'),
                hints=reading_data.get('hints', []),
                knowledge_components=['reading_comprehension', selected_topic],
                estimated_time=10 if length == "long" else 7 if length == "medium" else 5
            )
            
            return content
            
        except Exception as e:
            self.logger.error(f"Error generating reading content: {e}")
            return self._generate_fallback_content(ContentType.READING, difficulty)
    
    def generate_personalized_content(self, student_preferences: Dict[str, Any], 
                                    difficulty: DifficultyLevel,
                                    content_type: ContentType) -> GeneratedContent:
        """
        Generate personalized content based on student preferences.
        
        Args:
            student_preferences: Student learning preferences and history
            difficulty: Target difficulty level
            content_type: Type of content to generate
            
        Returns:
            Personalized generated content
        """
        try:
            # Extract preferences
            interests = student_preferences.get('interests', [])
            learning_style = student_preferences.get('learning_style', 'mixed')
            weak_areas = student_preferences.get('weak_areas', [])
            strong_areas = student_preferences.get('strong_areas', [])
            
            # Select topic based on interests and weak areas
            topic = None
            if weak_areas:
                topic = random.choice(weak_areas)  # Focus on improvement
            elif interests:
                topic = random.choice(interests)
            
            # Generate content based on type
            if content_type == ContentType.VOCABULARY:
                content_list = self.generate_vocabulary_content(difficulty, topic, 1)
                return content_list[0] if content_list else self._generate_fallback_content(content_type, difficulty)
            
            elif content_type == ContentType.GRAMMAR:
                grammar_focus = topic if topic in ['present_tense', 'past_tense', 'questions'] else None
                return self.generate_grammar_content(difficulty, grammar_focus)
            
            elif content_type == ContentType.CONVERSATION:
                return self.generate_conversation_content(difficulty, topic)
            
            elif content_type == ContentType.READING:
                length = "short" if learning_style == "kinesthetic" else "medium"
                return self.generate_reading_content(difficulty, topic, length)
            
            else:
                return self._generate_fallback_content(content_type, difficulty)
            
        except Exception as e:
            self.logger.error(f"Error generating personalized content: {e}")
            return self._generate_fallback_content(content_type, difficulty)
    
    def _generate_definition(self, word: str, difficulty: DifficultyLevel) -> str:
        """Generate a definition for a word based on difficulty."""
        # Simplified definition generation
        definitions = {
            'hello': 'A greeting used when meeting someone',
            'goodbye': 'A farewell used when leaving',
            'family': 'A group of people related to each other',
            'food': 'Things that people eat to stay alive',
            'water': 'A clear liquid that people drink',
            'teacher': 'A person who helps others learn',
            'student': 'A person who is learning',
            'book': 'Pages with writing bound together',
            'travel': 'To go from one place to another',
            'computer': 'An electronic device for processing information'
        }
        
        return definitions.get(word.lower(), f"A word meaning {word}")
    
    def _generate_example_sentence(self, word: str, difficulty: DifficultyLevel) -> str:
        """Generate an example sentence using the word."""
        # Simple sentence templates
        if difficulty in [DifficultyLevel.BEGINNER, DifficultyLevel.ELEMENTARY]:
            templates = [
                f"I use {word} every day.",
                f"The {word} is very important.",
                f"This is a {word}.",
                f"I like {word}."
            ]
        else:
            templates = [
                f"Understanding {word} is essential for daily communication.",
                f"The concept of {word} plays a significant role in our lives.",
                f"Many people find {word} to be quite useful.",
                f"Learning about {word} can improve your understanding."
            ]
        
        return random.choice(templates)
    
    def _generate_pronunciation_guide(self, word: str) -> str:
        """Generate a simple pronunciation guide."""
        # Simplified pronunciation guide
        guides = {
            'hello': '/həˈloʊ/',
            'goodbye': '/ˌɡʊdˈbaɪ/',
            'family': '/ˈfæməli/',
            'water': '/ˈwɔːtər/',
            'teacher': '/ˈtiːtʃər/',
            'computer': '/kəmˈpjuːtər/'
        }
        
        return guides.get(word.lower(), f"/{word}/")
    
    def _generate_present_tense_exercise(self, difficulty: DifficultyLevel) -> Dict[str, Any]:
        """Generate present tense grammar exercise."""
        subjects = ['I', 'You', 'He', 'She', 'It', 'We', 'They']
        verbs = ['eat', 'drink', 'go', 'come', 'see', 'hear', 'speak', 'walk']
        
        subject = random.choice(subjects)
        verb = random.choice(verbs)
        
        # Conjugate verb
        if subject in ['He', 'She', 'It']:
            correct_verb = verb + 's' if not verb.endswith('s') else verb + 'es'
        else:
            correct_verb = verb
        
        incorrect_options = [verb, verb + 's', verb + 'ed', verb + 'ing']
        incorrect_options = [v for v in incorrect_options if v != correct_verb]
        
        options = [correct_verb] + random.sample(incorrect_options, 2)
        random.shuffle(options)
        
        return {
            'rule': 'Present Tense: Add -s/-es for he/she/it',
            'example': f"Example: {subject} {correct_verb} every day.",
            'exercise': f"{subject} _____ to the park.",
            'question': f"Choose the correct form of '{verb}' for '{subject}':",
            'options': options,
            'correct_answer': correct_verb,
            'hints': [
                f"Think about the subject '{subject}'",
                "Third person singular takes -s or -es"
            ]
        }
    
    def _generate_past_tense_exercise(self, difficulty: DifficultyLevel) -> Dict[str, Any]:
        """Generate past tense grammar exercise."""
        regular_verbs = {'walk': 'walked', 'play': 'played', 'work': 'worked', 'cook': 'cooked'}
        irregular_verbs = {'go': 'went', 'eat': 'ate', 'see': 'saw', 'come': 'came'}
        
        verb_type = random.choice(['regular', 'irregular'])
        
        if verb_type == 'regular':
            verb, past_form = random.choice(list(regular_verbs.items()))
            hint = "Regular verbs add -ed in past tense"
        else:
            verb, past_form = random.choice(list(irregular_verbs.items()))
            hint = "This is an irregular verb - memorize the past form"
        
        wrong_options = [verb, verb + 'ed', verb + 's', verb + 'ing']
        wrong_options = [v for v in wrong_options if v != past_form]
        
        options = [past_form] + random.sample(wrong_options, 2)
        random.shuffle(options)
        
        return {
            'rule': f'Past Tense: {"Regular verbs add -ed" if verb_type == "regular" else "Irregular verbs change form"}',
            'example': f"Example: Yesterday I {past_form}.",
            'exercise': f"Yesterday I _____ to the store.",
            'question': f"What is the past tense of '{verb}'?",
            'options': options,
            'correct_answer': past_form,
            'hints': [hint, f"The sentence is about something that happened yesterday"]
        }
    
    def _generate_question_exercise(self, difficulty: DifficultyLevel) -> Dict[str, Any]:
        """Generate question formation exercise."""
        wh_words = ['What', 'Where', 'When', 'Who', 'Why', 'How']
        statements = [
            ("She goes to school", "Where", "Where does she go?"),
            ("They eat lunch", "What", "What do they eat?"),
            ("He works tomorrow", "When", "When does he work?"),
            ("Mary teaches English", "Who", "Who teaches English?")
        ]
        
        statement, wh_word, correct_question = random.choice(statements)
        
        wrong_options = [
            f"{wh_word} she goes to school?",
            f"{wh_word} do she go?",
            f"{wh_word} goes she?"
        ]
        
        options = [correct_question] + wrong_options[:2]
        random.shuffle(options)
        
        return {
            'rule': 'Questions: Wh-word + do/does + subject + verb',
            'example': f"Statement: {statement}",
            'exercise': f"Make a question starting with '{wh_word}'",
            'question': f"Which question is correct?",
            'options': options,
            'correct_answer': correct_question,
            'hints': [
                f"Start with '{wh_word}'",
                "Use 'do' or 'does' after the wh-word"
            ]
        }
    
    def _generate_basic_grammar_exercise(self, difficulty: DifficultyLevel) -> Dict[str, Any]:
        """Generate basic grammar exercise."""
        return {
            'rule': 'Basic sentence structure: Subject + Verb + Object',
            'example': 'Example: The cat eats fish.',
            'exercise': 'Complete: The dog _____ the ball.',
            'question': 'What verb completes the sentence?',
            'options': ['plays', 'playing', 'play', 'played'],
            'correct_answer': 'plays',
            'hints': [
                'The subject is "dog" (third person singular)',
                'Use present tense'
            ]
        }
    
    def _generate_conversation_dialogue(self, scenario: str, difficulty: DifficultyLevel) -> Dict[str, Any]:
        """Generate conversation dialogue for a scenario."""
        try:
            if scenario == 'greeting':
                dialogue = [
                    "Person A: Hello! How are you today?",
                    "Person B: I'm fine, thank you. How about you?",
                    "Person A: I'm doing great! Nice weather today, isn't it?"
                ]
                expected_response = "Yes, it's beautiful!"
                hints = ["Respond positively about the weather", "Keep the conversation friendly"]
            
            elif scenario == 'ordering_food':
                dialogue = [
                    "Waiter: Good evening! Are you ready to order?",
                    "Customer: Yes, I'd like a burger, please.",
                    "Waiter: Would you like fries with that?"
                ]
                expected_response = "Yes, please." or "No, thank you."
                hints = ["Answer yes or no", "Be polite"]
            
            elif scenario == 'asking_directions':
                dialogue = [
                    "Tourist: Excuse me, how do I get to the library?",
                    "Local: Go straight for two blocks, then turn left.",
                    "Tourist: Is it far from here?"
                ]
                expected_response = "No, it's about 5 minutes walk."
                hints = ["Give information about distance", "Be helpful"]
            
            else:  # Default shopping scenario
                dialogue = [
                    "Customer: How much does this shirt cost?",
                    "Salesperson: It's $25.",
                    "Customer: Do you have it in blue?"
                ]
                expected_response = "Let me check for you."
                hints = ["Offer to help", "Be professional"]
            
            return {
                'scenario': scenario.replace('_', ' ').title(),
                'dialogue': dialogue,
                'your_turn': "Now it's your turn to respond. What would you say?",
                'expected_response': expected_response,
                'hints': hints
            }
            
        except Exception as e:
            self.logger.error(f"Error generating conversation dialogue: {e}")
            return {
                'scenario': 'Basic Conversation',
                'dialogue': ["Person A: Hello!", "Person B: Hi there!"],
                'your_turn': "What would you say next?",
                'expected_response': "How are you?",
                'hints': ["Keep it simple and friendly"]
            }
    
    def _generate_reading_passage(self, topic: str, difficulty: DifficultyLevel, length: str) -> Dict[str, Any]:
        """Generate reading comprehension passage."""
        try:
            # Simple passage generation based on topic and difficulty
            if topic == 'daily_life' and difficulty == DifficultyLevel.BEGINNER:
                passage = """
                My Daily Routine
                
                I wake up at 7:00 AM every day. First, I brush my teeth and wash my face. 
                Then I eat breakfast with my family. I usually have bread and coffee.
                
                After breakfast, I go to work. I work in an office from 9:00 AM to 5:00 PM.
                At lunch time, I eat with my friends. We often talk about our weekend plans.
                
                When I come home, I help my mother cook dinner. We eat together and watch TV.
                Before bed, I read a book for 30 minutes. I go to sleep at 10:00 PM.
                """
                
                questions = [
                    {
                        'question': 'What time does the person wake up?',
                        'options': ['6:00 AM', '7:00 AM', '8:00 AM', '9:00 AM'],
                        'answer': '7:00 AM'
                    },
                    {
                        'question': 'What does the person eat for breakfast?',
                        'options': ['Rice and tea', 'Bread and coffee', 'Fruit and milk', 'Eggs and juice'],
                        'answer': 'Bread and coffee'
                    },
                    {
                        'question': 'What time does the person go to sleep?',
                        'options': ['9:00 PM', '10:00 PM', '11:00 PM', '12:00 AM'],
                        'answer': '10:00 PM'
                    }
                ]
            
            else:  # Generic passage
                passage = f"""
                About {topic.replace('_', ' ').title()}
                
                This is an interesting topic that many people enjoy learning about.
                There are many different aspects to consider when studying this subject.
                
                People from different cultures may have different perspectives on this topic.
                It's important to keep an open mind and learn from various sources.
                
                By studying this topic, you can improve your knowledge and understanding
                of the world around you.
                """
                
                questions = [
                    {
                        'question': f'What is this passage about?',
                        'options': ['Sports', topic.replace('_', ' ').title(), 'Food', 'Weather'],
                        'answer': topic.replace('_', ' ').title()
                    },
                    {
                        'question': 'According to the passage, what should you keep?',
                        'options': ['A diary', 'An open mind', 'Your books', 'Your time'],
                        'answer': 'An open mind'
                    }
                ]
            
            return {
                'passage': passage.strip(),
                'questions': questions,
                'answers': [q['answer'] for q in questions],
                'hints': ['Read carefully', 'Look for key words in the questions']
            }
            
        except Exception as e:
            self.logger.error(f"Error generating reading passage: {e}")
            return {
                'passage': 'This is a simple reading passage for practice.',
                'questions': [{'question': 'What is this?', 'options': ['A passage', 'A song', 'A game', 'A movie'], 'answer': 'A passage'}],
                'answers': ['A passage'],
                'hints': ['Read the passage carefully']
            }
    
    def _generate_fallback_content(self, content_type: ContentType, difficulty: DifficultyLevel) -> GeneratedContent:
        """Generate fallback content when other methods fail."""
        content_id = f"fallback_{content_type.value}_{int(datetime.now().timestamp())}"
        
        return GeneratedContent(
            content_id=content_id,
            content_type=content_type,
            difficulty_level=difficulty,
            title=f"Practice {content_type.value.title()}",
            content={
                'message': f"Let's practice {content_type.value} together!",
                'activity': f"This is a basic {content_type.value} exercise."
            },
            instructions=f"Complete this {content_type.value} practice activity.",
            expected_response="Practice response",
            hints=[f"Focus on {content_type.value} skills"],
            knowledge_components=[content_type.value],
            estimated_time=5
        )