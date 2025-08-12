"""
Homework Teacher - Handles structured exercises, assignments, and skill assessments.
Focuses on grammar, vocabulary drills, reading comprehension, and writing exercises.
"""

import json
import random
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from agents.base.base_agent import BaseAgent, AgentConfig
from src.log_service import get_logger


class ExerciseType(Enum):
    """Types of homework exercises."""
    VOCABULARY = "vocabulary"
    GRAMMAR = "grammar"
    SENTENCE_BUILDING = "sentence_building"
    READING_COMPREHENSION = "reading_comprehension"
    TRANSLATION = "translation"
    FILL_IN_BLANKS = "fill_in_blanks"
    MULTIPLE_CHOICE = "multiple_choice"
    WRITING_PROMPT = "writing_prompt"


class ExerciseDifficulty(Enum):
    """Exercise difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class Exercise:
    """Individual exercise structure."""
    id: str
    type: ExerciseType
    difficulty: ExerciseDifficulty
    question: str
    options: Optional[List[str]] = None
    correct_answer: str = ""
    explanation: str = ""
    points: int = 1
    time_limit_minutes: Optional[int] = None
    hints: List[str] = field(default_factory=list)


@dataclass
class HomeworkSession:
    """Active homework session for a user."""
    user_id: int
    current_exercise: Optional[Exercise] = None
    exercises_completed: List[Exercise] = field(default_factory=list)
    current_score: int = 0
    max_score: int = 0
    session_start: datetime = field(default_factory=datetime.now)
    awaiting_answer: bool = False
    hints_used: int = 0


class HomeworkTeacher(BaseAgent):
    """
    Homework Teacher persona for structured language exercises.
    Creates and manages various types of language learning exercises.
    """
    
    EXERCISE_TEMPLATES = {
        ExerciseType.VOCABULARY: {
            "easy": [
                "What does '{word}' mean?",
                "Choose the correct translation for '{word}':",
                "Complete the sentence: 'I am very ___' (happy/sad/angry)"
            ],
            "medium": [
                "Use '{word}' in a complete sentence.",
                "What's the opposite of '{word}'?",
                "Choose the word that best completes: 'The weather is very ___'"
            ],
            "hard": [
                "Explain the difference between '{word1}' and '{word2}'.",
                "Create a short paragraph using these words: {word_list}",
                "What are three synonyms for '{word}'?"
            ]
        },
        
        ExerciseType.GRAMMAR: {
            "easy": [
                "Choose the correct form: I (am/is/are) happy.",
                "Complete with 'a' or 'an': ___ apple",
                "Past tense of 'go': He ___ to school yesterday."
            ],
            "medium": [
                "Correct the sentence: 'She don't like pizza.'",
                "Choose: 'I have been studying English (for/since) two years.'",
                "Make this sentence negative: 'They play football.'"
            ],
            "hard": [
                "Explain when to use the present perfect vs simple past.",
                "Rewrite using passive voice: 'The chef prepared the meal.'",
                "Identify the grammatical error: 'If I would have money, I would buy a car.'"
            ]
        },
        
        ExerciseType.SENTENCE_BUILDING: {
            "easy": [
                "Put these words in order: [dog/the/big/is]",
                "Make a sentence with: cat, sleeping, chair",
                "Complete: 'My name ___ John.'"
            ],
            "medium": [
                "Combine these sentences: 'It's raining. We stayed inside.'",
                "Make a question from: 'She lives in Paris.'",
                "Add adjectives: 'The car is fast.'"
            ],
            "hard": [
                "Write a complex sentence using 'although' and 'because'.",
                "Transform into reported speech: 'I will come tomorrow,' she said.",
                "Create conditional sentences: If I had more time..."
            ]
        },
        
        ExerciseType.READING_COMPREHENSION: {
            "easy": [
                "Read and answer: What color is the sky in the story?",
                "True or False: The character went to the store.",
                "How many people are mentioned in the text?"
            ],
            "medium": [
                "What is the main idea of this paragraph?",
                "Why did the character make that decision?",
                "What happened first, second, and third?"
            ],
            "hard": [
                "What can you infer about the character's motivation?",
                "Compare the author's opinion in paragraphs 1 and 3.",
                "What is the underlying theme of this passage?"
            ]
        }
    }
    
    SAMPLE_VOCABULARY = {
        "english": {
            "beginner": ["hello", "goodbye", "thank you", "please", "yes", "no", "good", "bad"],
            "elementary": ["beautiful", "important", "difficult", "interesting", "different", "similar"],
            "intermediate": ["although", "however", "therefore", "furthermore", "nevertheless"],
            "advanced": ["sophisticated", "comprehensive", "meticulous", "profound", "intricate"]
        },
        "spanish": {
            "beginner": ["hola", "adiós", "gracias", "por favor", "sí", "no", "bueno", "malo"],
            "elementary": ["hermoso", "importante", "difícil", "interesante", "diferente", "similar"],
            "intermediate": ["aunque", "sin embargo", "por lo tanto", "además", "no obstante"],
            "advanced": ["sofisticado", "comprensivo", "meticuloso", "profundo", "intrincado"]
        }
    }
    
    def __init__(self):
        """Initialize the Homework Teacher."""
        config = AgentConfig(
            name="homework_teacher",
            description="Structured exercise and homework teacher for language learning",
            category="education",
            system_message=self._get_system_message(),
            temperature=0.6,
            max_tokens=1500
        )
        
        super().__init__(config)
        
        # Session management
        self.active_sessions: Dict[int, HomeworkSession] = {}
        self.exercise_database = self._initialize_exercise_database()
        
    def _get_system_message(self) -> str:
        """Get the system message for homework teacher."""
        return """You are an expert Language Homework Teacher who creates and manages structured language learning exercises.

Your teaching approach:
1. Create appropriate exercises based on student level
2. Provide clear instructions and examples
3. Give immediate feedback on answers
4. Explain correct answers with reasoning
5. Track progress and adjust difficulty
6. Offer hints when students are struggling
7. Celebrate correct answers and encourage improvement

Exercise feedback format:
- For correct answers: "✅ Excellent! [Brief reinforcement]"
- For incorrect answers: "❌ Not quite. The correct answer is [answer]. [Explanation]"
- For partial credit: "⚡ Good try! You're on the right track. [Guidance]"

Teaching principles:
- Be clear and structured in explanations
- Provide step-by-step guidance for complex topics
- Use examples to illustrate concepts
- Adjust difficulty based on performance
- Encourage practice and repetition
- Make learning systematic but engaging"""
    
    def _initialize_exercise_database(self) -> Dict[str, List[Exercise]]:
        """Initialize the exercise database."""
        # This would typically load from a database or file
        # For now, create some sample exercises
        return {
            "english_beginner": self._create_sample_exercises("english", "beginner"),
            "english_intermediate": self._create_sample_exercises("english", "intermediate"),
            "spanish_beginner": self._create_sample_exercises("spanish", "beginner"),
            "spanish_intermediate": self._create_sample_exercises("spanish", "intermediate")
        }
    
    def _create_sample_exercises(self, language: str, level: str) -> List[Exercise]:
        """Create sample exercises for testing."""
        exercises = []
        
        # Vocabulary exercise
        if language == "english" and level == "beginner":
            exercises.append(Exercise(
                id="vocab_1",
                type=ExerciseType.VOCABULARY,
                difficulty=ExerciseDifficulty.EASY,
                question="What does 'beautiful' mean?",
                options=["Very pretty", "Very ugly", "Very big", "Very small"],
                correct_answer="Very pretty",
                explanation="Beautiful means very attractive or pleasing to look at.",
                points=1
            ))
            
            exercises.append(Exercise(
                id="grammar_1",
                type=ExerciseType.GRAMMAR,
                difficulty=ExerciseDifficulty.EASY,
                question="Choose the correct form: I ___ happy.",
                options=["am", "is", "are"],
                correct_answer="am",
                explanation="We use 'am' with 'I'. I am happy.",
                points=1
            ))
        
        return exercises
    
    async def setup(self) -> None:
        """Initialize homework teacher."""
        self.logger.info("Homework Teacher initialized")
    
    async def process_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process homework-related message from user.
        
        Args:
            message: User's message
            context: Context including user_profile, language, level
            
        Returns:
            Teacher's response
        """
        try:
            if not context:
                return "I need context to create appropriate exercises for you."
            
            user_profile = context.get("user_profile")
            if not user_profile:
                return "I need your user profile to personalize your homework."
            
            user_id = user_profile.user_id
            language = context.get("language", "english")
            level = context.get("level", "beginner")
            
            # Get or create homework session
            session = self.get_homework_session(user_id)
            
            # Check if user is answering an exercise
            if session.awaiting_answer and session.current_exercise:
                return await self.check_exercise_answer(message, session)
            
            # Handle homework requests and commands
            return await self.handle_homework_request(message, session, language, level)
            
        except Exception as e:
            self.logger.error(f"Error in homework teacher: {e}")
            return "I'm having trouble creating exercises right now. Please try again."
    
    def get_homework_session(self, user_id: int) -> HomeworkSession:
        """Get or create homework session for user."""
        if user_id not in self.active_sessions:
            self.active_sessions[user_id] = HomeworkSession(user_id=user_id)
        return self.active_sessions[user_id]
    
    async def handle_homework_request(
        self,
        message: str,
        session: HomeworkSession,
        language: str,
        level: str
    ) -> str:
        """Handle homework requests and start new exercises."""
        
        message_lower = message.lower().strip()
        
        # Check for specific exercise type requests
        if "vocabulary" in message_lower or "vocab" in message_lower:
            return await self.start_exercise(ExerciseType.VOCABULARY, session, language, level)
        elif "grammar" in message_lower:
            return await self.start_exercise(ExerciseType.GRAMMAR, session, language, level)
        elif "sentence" in message_lower or "building" in message_lower:
            return await self.start_exercise(ExerciseType.SENTENCE_BUILDING, session, language, level)
        elif "reading" in message_lower:
            return await self.start_exercise(ExerciseType.READING_COMPREHENSION, session, language, level)
        elif "translation" in message_lower:
            return await self.start_exercise(ExerciseType.TRANSLATION, session, language, level)
        elif "hint" in message_lower and session.current_exercise:
            return self.provide_hint(session)
        elif "score" in message_lower or "progress" in message_lower:
            return self.show_session_progress(session)
        elif "new" in message_lower or "different" in message_lower:
            return await self.start_random_exercise(session, language, level)
        else:
            # Default: start with a random exercise appropriate for their level
            return await self.start_random_exercise(session, language, level)
    
    async def start_exercise(
        self,
        exercise_type: ExerciseType,
        session: HomeworkSession,
        language: str,
        level: str
    ) -> str:
        """Start a specific type of exercise."""
        
        # Create exercise based on type and level
        exercise = await self.create_exercise(exercise_type, language, level)
        
        if not exercise:
            return f"I don't have {exercise_type.value} exercises ready right now. Try a different type!"
        
        # Set current exercise
        session.current_exercise = exercise
        session.awaiting_answer = True
        
        # Format and return exercise
        return self.format_exercise(exercise)
    
    async def start_random_exercise(
        self,
        session: HomeworkSession,
        language: str,
        level: str
    ) -> str:
        """Start a random exercise appropriate for the user's level."""
        
        # Choose random exercise type
        available_types = [
            ExerciseType.VOCABULARY,
            ExerciseType.GRAMMAR,
            ExerciseType.SENTENCE_BUILDING
        ]
        
        exercise_type = random.choice(available_types)
        return await self.start_exercise(exercise_type, session, language, level)
    
    async def create_exercise(
        self,
        exercise_type: ExerciseType,
        language: str,
        level: str
    ) -> Optional[Exercise]:
        """Create an exercise of the specified type."""
        
        try:
            if exercise_type == ExerciseType.VOCABULARY:
                return self.create_vocabulary_exercise(language, level)
            elif exercise_type == ExerciseType.GRAMMAR:
                return self.create_grammar_exercise(language, level)
            elif exercise_type == ExerciseType.SENTENCE_BUILDING:
                return self.create_sentence_building_exercise(language, level)
            elif exercise_type == ExerciseType.READING_COMPREHENSION:
                return self.create_reading_exercise(language, level)
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating {exercise_type} exercise: {e}")
            return None
    
    def create_vocabulary_exercise(self, language: str, level: str) -> Exercise:
        """Create a vocabulary exercise."""
        
        vocab_list = self.SAMPLE_VOCABULARY.get(language, {}).get(level, ["hello", "goodbye"])
        word = random.choice(vocab_list)
        
        # Create multiple choice question
        if level == "beginner":
            if word == "hello":
                return Exercise(
                    id=f"vocab_{word}_{datetime.now().timestamp()}",
                    type=ExerciseType.VOCABULARY,
                    difficulty=ExerciseDifficulty.EASY,
                    question=f"What does '{word}' mean?",
                    options=["Greeting", "Goodbye", "Thank you", "Please"],
                    correct_answer="Greeting",
                    explanation=f"'{word}' is used to greet someone when you meet them.",
                    points=1,
                    hints=[f"Think about when you first meet someone...", "It's the opposite of goodbye"]
                )
            elif word == "thank you":
                return Exercise(
                    id=f"vocab_{word}_{datetime.now().timestamp()}",
                    type=ExerciseType.VOCABULARY,
                    difficulty=ExerciseDifficulty.EASY,
                    question=f"When do you say '{word}'?",
                    options=["When grateful", "When angry", "When leaving", "When arriving"],
                    correct_answer="When grateful",
                    explanation=f"'{word}' expresses gratitude or appreciation.",
                    points=1,
                    hints=["Think about when someone helps you...", "It shows appreciation"]
                )
        
        # Default vocabulary exercise
        return Exercise(
            id=f"vocab_{word}_{datetime.now().timestamp()}",
            type=ExerciseType.VOCABULARY,
            difficulty=ExerciseDifficulty.EASY,
            question=f"Use the word '{word}' in a sentence.",
            correct_answer="(Open answer)",
            explanation=f"Good job using '{word}' in context!",
            points=1,
            hints=[f"Think of a situation where you might use '{word}'"]
        )
    
    def create_grammar_exercise(self, language: str, level: str) -> Exercise:
        """Create a grammar exercise."""
        
        if level == "beginner":
            exercises = [
                {
                    "question": "Choose the correct form: She ___ a student.",
                    "options": ["am", "is", "are"],
                    "correct": "is",
                    "explanation": "Use 'is' with 'she', 'he', or 'it'.",
                    "hints": ["Think about singular vs plural", "'She' is singular"]
                },
                {
                    "question": "Complete: There ___ many books on the table.",
                    "options": ["is", "are", "am"],
                    "correct": "are",
                    "explanation": "Use 'are' with plural nouns like 'books'.",
                    "hints": ["How many books? Many = plural", "'Books' is plural"]
                }
            ]
        else:
            exercises = [
                {
                    "question": "Choose the correct tense: I ___ English for two years.",
                    "options": ["study", "studied", "have studied"],
                    "correct": "have studied",
                    "explanation": "Use present perfect for actions that started in the past and continue now.",
                    "hints": ["Time period: 'for two years'", "Think present perfect"]
                }
            ]
        
        exercise_data = random.choice(exercises)
        
        return Exercise(
            id=f"grammar_{datetime.now().timestamp()}",
            type=ExerciseType.GRAMMAR,
            difficulty=ExerciseDifficulty.EASY if level == "beginner" else ExerciseDifficulty.MEDIUM,
            question=exercise_data["question"],
            options=exercise_data["options"],
            correct_answer=exercise_data["correct"],
            explanation=exercise_data["explanation"],
            points=1,
            hints=exercise_data["hints"]
        )
    
    def create_sentence_building_exercise(self, language: str, level: str) -> Exercise:
        """Create a sentence building exercise."""
        
        if level == "beginner":
            return Exercise(
                id=f"sentence_{datetime.now().timestamp()}",
                type=ExerciseType.SENTENCE_BUILDING,
                difficulty=ExerciseDifficulty.EASY,
                question="Put these words in the correct order: [cat / the / sleeping / is]",
                correct_answer="The cat is sleeping",
                explanation="Subject + verb + object: 'The cat is sleeping'",
                points=1,
                hints=["Start with 'The'", "What is the cat doing?"]
            )
        else:
            return Exercise(
                id=f"sentence_{datetime.now().timestamp()}",
                type=ExerciseType.SENTENCE_BUILDING,
                difficulty=ExerciseDifficulty.MEDIUM,
                question="Combine these sentences using 'because': 'It was raining.' + 'We stayed inside.'",
                correct_answer="We stayed inside because it was raining",
                explanation="Use 'because' to show cause and effect.",
                points=2,
                hints=["Which sentence shows the reason?", "Cause and effect relationship"]
            )
    
    def create_reading_exercise(self, language: str, level: str) -> Exercise:
        """Create a reading comprehension exercise."""
        
        if level == "beginner":
            text = "Tom has a red car. He drives to work every day. His car is very fast."
            return Exercise(
                id=f"reading_{datetime.now().timestamp()}",
                type=ExerciseType.READING_COMPREHENSION,
                difficulty=ExerciseDifficulty.EASY,
                question=f"Read this text: '{text}'\n\nWhat color is Tom's car?",
                options=["Red", "Blue", "Green", "Black"],
                correct_answer="Red",
                explanation="The text says 'Tom has a red car.'",
                points=1,
                hints=["Look for the color word", "First sentence has the answer"]
            )
        else:
            text = "Although the weather was terrible, Sarah decided to go for a walk. She believed that fresh air would help her feel better after a long day at work."
            return Exercise(
                id=f"reading_{datetime.now().timestamp()}",
                type=ExerciseType.READING_COMPREHENSION,
                difficulty=ExerciseDifficulty.MEDIUM,
                question=f"Read this text: '{text}'\n\nWhy did Sarah go for a walk despite bad weather?",
                correct_answer="She thought fresh air would help her feel better",
                explanation="Sarah believed fresh air would help her after a long work day.",
                points=2,
                hints=["Look for her motivation", "What did she believe?"]
            )
    
    def format_exercise(self, exercise: Exercise) -> str:
        """Format exercise for display."""
        
        formatted = f"""📝 **{exercise.type.value.title()} Exercise**
        
{exercise.question}"""
        
        if exercise.options:
            formatted += "\n\n**Options:**"
            for i, option in enumerate(exercise.options, 1):
                formatted += f"\n{i}. {option}"
        
        formatted += f"""

💰 **Points:** {exercise.points}
⏱️ **Difficulty:** {exercise.difficulty.value.title()}

Type your answer or use 'hint' for help!"""
        
        return formatted
    
    async def check_exercise_answer(self, answer: str, session: HomeworkSession) -> str:
        """Check user's answer to the current exercise."""
        
        if not session.current_exercise:
            return "No active exercise to check."
        
        exercise = session.current_exercise
        user_answer = answer.strip()
        
        # Check if answer is correct
        is_correct = self.evaluate_answer(user_answer, exercise)
        
        # Update session
        session.awaiting_answer = False
        session.exercises_completed.append(exercise)
        session.max_score += exercise.points
        
        if is_correct:
            session.current_score += exercise.points
            response = f"✅ **Correct!** {exercise.explanation}\n\n"
            response += f"💯 **Score:** {session.current_score}/{session.max_score}\n\n"
            response += "🎉 Great job! Ready for the next exercise? Just tell me what type you'd like!"
        else:
            response = f"❌ **Not quite right.** The correct answer is: **{exercise.correct_answer}**\n\n"
            response += f"📚 **Explanation:** {exercise.explanation}\n\n"
            response += f"💯 **Score:** {session.current_score}/{session.max_score}\n\n"
            response += "💪 Don't worry - mistakes help us learn! Try another exercise?"
        
        # Clear current exercise
        session.current_exercise = None
        
        return response
    
    def evaluate_answer(self, user_answer: str, exercise: Exercise) -> bool:
        """Evaluate if user's answer is correct."""
        
        correct_answer = exercise.correct_answer.lower().strip()
        user_answer_clean = user_answer.lower().strip()
        
        # For multiple choice, check if it's one of the options
        if exercise.options:
            # Check direct match
            if user_answer_clean == correct_answer:
                return True
            
            # Check if user typed option number
            try:
                option_num = int(user_answer_clean)
                if 1 <= option_num <= len(exercise.options):
                    selected_option = exercise.options[option_num - 1].lower().strip()
                    return selected_option == correct_answer
            except ValueError:
                pass
            
            # Check if user typed the option text
            for option in exercise.options:
                if option.lower().strip() == user_answer_clean:
                    return option.lower().strip() == correct_answer
        
        # For open-ended questions, use basic similarity
        if exercise.correct_answer == "(Open answer)":
            return len(user_answer.split()) >= 3  # At least 3 words for sentence exercises
        
        # Direct comparison
        return user_answer_clean == correct_answer
    
    def provide_hint(self, session: HomeworkSession) -> str:
        """Provide a hint for the current exercise."""
        
        if not session.current_exercise or not session.awaiting_answer:
            return "No active exercise to provide hints for."
        
        exercise = session.current_exercise
        
        if not exercise.hints:
            return "No hints available for this exercise. Try your best!"
        
        if session.hints_used >= len(exercise.hints):
            return "No more hints available. Give it your best try!"
        
        hint = exercise.hints[session.hints_used]
        session.hints_used += 1
        
        return f"💡 **Hint #{session.hints_used}:** {hint}\n\nNow try answering the question!"
    
    def show_session_progress(self, session: HomeworkSession) -> str:
        """Show current session progress."""
        
        total_exercises = len(session.exercises_completed)
        
        if session.current_exercise:
            total_exercises += 1  # Include current exercise
        
        session_time = datetime.now() - session.session_start
        minutes = int(session_time.total_seconds() / 60)
        
        return f"""📊 **Your Homework Session Progress**

📝 **Exercises completed:** {len(session.exercises_completed)}
💯 **Score:** {session.current_score}/{session.max_score} points
⏱️ **Session time:** {minutes} minutes
🎯 **Accuracy:** {(session.current_score/session.max_score*100):.0f}% if session.max_score > 0 else 0}%

{"✍️ Currently working on an exercise" if session.awaiting_answer else "🎯 Ready for next exercise!"}

Keep up the excellent work! 🌟"""
    
    def get_homework_stats(self, user_id: int) -> Dict[str, Any]:
        """Get homework statistics for a user."""
        session = self.active_sessions.get(user_id)
        
        if not session:
            return {
                "exercises_completed": 0,
                "current_score": 0,
                "max_score": 0,
                "session_active": False
            }
        
        return {
            "exercises_completed": len(session.exercises_completed),
            "current_score": session.current_score,
            "max_score": session.max_score,
            "session_active": session.awaiting_answer,
            "session_duration_minutes": int((datetime.now() - session.session_start).total_seconds() / 60)
        }
    
    async def cleanup(self) -> None:
        """Clean up homework teacher resources."""
        self.active_sessions.clear()
        self.logger.info("Homework Teacher cleaned up")