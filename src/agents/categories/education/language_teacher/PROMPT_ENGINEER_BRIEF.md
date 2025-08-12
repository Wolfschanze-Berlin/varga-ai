# Prompt Engineer - Implementation Brief

## Overview
You are responsible for implementing the teaching prompts, conversation flows, and both teacher personas that make the language learning experience engaging and effective. Your work brings the AI teachers to life.

## Your Core Responsibilities

### 1. Teacher Persona Implementation
- ConversationTeacher: Casual, encouraging conversational practice partner
- HomeworkTeacher: Structured, methodical exercise instructor
- Dynamic persona adaptation based on user proficiency and mood
- Consistent personality traits and teaching philosophies

### 2. Teaching Prompt System
- Level-appropriate prompts for different proficiency levels
- Adaptive prompts that adjust based on user performance
- Contextual prompts for different learning scenarios
- Error-specific correction prompts and strategies

### 3. Conversation Flow Management
- Natural dialogue state tracking
- Topic transitions and conversation steering
- Exercise integration within natural conversation
- Interruption handling and flow recovery

### 4. Feedback Generation
- Constructive error correction without discouragement
- Personalized praise and encouragement
- Specific improvement suggestions
- Progress acknowledgment and motivation

## Integration Specifications

### Shared Components You'll Use
```python
from ..shared.interfaces import (
    TeacherPersona, TeacherResponse, FeedbackResponse,
    UserProfile, UserSession, Exercise, SharedContext,
    SkillType, ProficiencyLevel, SessionType
)
from ..database.models import (
    DatabaseManager, UserRepository, ProgressRepository
)
```

### Key Files You'll Create
```
agents/categories/education/language_teacher/
├── conversation_teacher.py          # Conversational practice persona
├── homework_teacher.py             # Structured exercise persona  
├── conversation_flow_manager.py    # Dialogue state management
├── feedback_generator.py          # Personalized feedback system
├── prompts/                        # Prompt templates and management
│   ├── __init__.py
│   ├── conversation_teacher_prompts.py
│   ├── homework_teacher_prompts.py
│   ├── feedback_prompts.py
│   ├── level_specific_prompts.py
│   └── correction_prompts.py
├── persona_traits/                 # Personality definitions
│   ├── conversation_traits.py
│   └── homework_traits.py
└── dialogue_states/               # Conversation state models
    ├── conversation_states.py
    └── exercise_states.py
```

### Expected Interfaces

#### ConversationTeacher
```python
class ConversationTeacher(TeacherPersona):
    """Casual, encouraging conversation practice teacher."""
    
    async def start_session(self, 
                          user_profile: UserProfile, 
                          session_type: SessionType) -> TeacherResponse:
        """Start conversation session with appropriate greeting."""
        
    async def process_message(self, 
                            message: str, 
                            session: UserSession,
                            context: SharedContext) -> TeacherResponse:
        """Process user message and continue conversation."""
        
    async def provide_feedback(self, 
                             user_input: str, 
                             expected: str,
                             exercise: Exercise) -> FeedbackResponse:
        """Provide gentle, encouraging feedback."""
        
    async def suggest_topic(self, user_profile: UserProfile) -> str:
        """Suggest interesting conversation topic."""
```

#### HomeworkTeacher  
```python
class HomeworkTeacher(TeacherPersona):
    """Structured, methodical exercise instructor."""
    
    async def create_exercise_sequence(self, 
                                     user_profile: UserProfile,
                                     skill_focus: SkillType) -> List[Exercise]:
        """Create structured sequence of exercises."""
        
    async def explain_exercise(self, exercise: Exercise) -> str:
        """Provide clear exercise instructions."""
        
    async def check_answer(self, 
                         user_answer: str, 
                         exercise: Exercise) -> FeedbackResponse:
        """Check answer and provide detailed feedback."""
```

## Teacher Persona Implementations

### ConversationTeacher Personality
```python
class ConversationTeacherTraits:
    """Defines the personality traits of the conversation teacher."""
    
    PERSONALITY = {
        "tone": "casual and friendly",
        "encouragement_style": "enthusiastic and supportive",
        "correction_approach": "gentle and indirect",
        "conversation_style": "natural and engaging",
        "humor_level": "light and appropriate",
        "patience_level": "very high",
        "formality": "informal but respectful"
    }
    
    GREETING_TEMPLATES = [
        "Hey there! Ready for some fun conversation practice? 😊",
        "Hi! What would you like to chat about today?",
        "Hello! I'm excited to practice {target_language} with you today!",
        "Hey! How are you feeling about practicing some {target_language}?"
    ]
    
    ENCOURAGEMENT_PHRASES = [
        "Great job!", "You're getting better!", "Nice try!", 
        "I love your enthusiasm!", "Keep going!", "That was close!",
        "Don't worry, you're learning!", "Excellent effort!"
    ]
```

### HomeworkTeacher Personality
```python
class HomeworkTeacherTraits:
    """Defines the personality traits of the homework teacher."""
    
    PERSONALITY = {
        "tone": "professional and supportive",
        "instruction_style": "clear and methodical", 
        "correction_approach": "direct but constructive",
        "explanation_style": "detailed and systematic",
        "organization_level": "highly structured",
        "patience_level": "high",
        "formality": "semi-formal and encouraging"
    }
    
    INSTRUCTION_TEMPLATES = [
        "Let's work on {skill_type} today. Here's your first exercise:",
        "Time for some {skill_type} practice! Pay attention to the instructions:",
        "Ready for today's lesson on {skill_type}? Let's begin:",
        "Here's a {difficulty} exercise to help you improve your {skill_type}:"
    ]
```

## Prompt System Architecture

### Level-Adaptive Prompts
```python
class LevelAdaptivePrompts:
    """Manages prompts that adapt to user proficiency level."""
    
    BEGINNER_CONVERSATION_STARTERS = [
        "Let's talk about your day! What did you do today?",
        "Tell me about your family. Do you have brothers or sisters?",
        "What's your favorite food? Why do you like it?"
    ]
    
    INTERMEDIATE_CONVERSATION_STARTERS = [
        "What do you think about social media? How has it changed communication?",
        "If you could travel anywhere, where would you go and why?",
        "What's a tradition from your culture that you'd like to share?"
    ]
    
    ADVANCED_CONVERSATION_STARTERS = [
        "What are your thoughts on artificial intelligence and its impact on society?",
        "How do you think we can address climate change as individuals and communities?",
        "What role should governments play in regulating technology companies?"
    ]
    
    def get_conversation_starter(self, level: ProficiencyLevel) -> str:
        """Get appropriate conversation starter for user level."""
        starters = {
            ProficiencyLevel.BEGINNER: self.BEGINNER_CONVERSATION_STARTERS,
            ProficiencyLevel.ELEMENTARY: self.BEGINNER_CONVERSATION_STARTERS,
            ProficiencyLevel.INTERMEDIATE: self.INTERMEDIATE_CONVERSATION_STARTERS,
            ProficiencyLevel.UPPER_INTERMEDIATE: self.INTERMEDIATE_CONVERSATION_STARTERS,
            ProficiencyLevel.ADVANCED: self.ADVANCED_CONVERSATION_STARTERS,
            ProficiencyLevel.PROFICIENT: self.ADVANCED_CONVERSATION_STARTERS,
        }
        return random.choice(starters[level])
```

### Correction Prompts
```python
class CorrectionPrompts:
    """Manages error correction prompts for different error types."""
    
    GRAMMAR_CORRECTIONS = {
        "verb_tense": [
            "I noticed a small tense issue. You said '{user_input}', but it should be '{correct}' because {explanation}.",
            "Good effort! Just a quick note: we use '{correct}' here instead of '{user_input}' for {explanation}.",
        ],
        "article_usage": [
            "Almost there! Remember to use '{correct}' instead of '{user_input}' before {explanation}.",
            "Nice try! The correct article here is '{correct}' because {explanation}.",
        ],
        "word_order": [
            "You have the right words! Try putting them in this order: '{correct}'",
            "Great vocabulary! The word order would be: '{correct}'",
        ]
    }
    
    VOCABULARY_CORRECTIONS = {
        "wrong_word": [
            "Close! The word you're looking for is '{correct}' instead of '{user_input}'.",
            "Good guess! In this context, we'd say '{correct}' rather than '{user_input}'.",
        ],
        "spelling": [
            "You've got the right idea! The spelling is '{correct}'.",
            "Almost perfect! Just check the spelling: '{correct}'.",
        ]
    }
```

## Conversation Flow Management

### Dialogue State Tracking
```python
class ConversationFlowManager:
    """Manages conversation state and natural dialogue flow."""
    
    def __init__(self):
        self.current_topic = None
        self.conversation_depth = 0
        self.user_interests = []
        self.recent_corrections = []
        
    async def process_user_message(self, 
                                 message: str,
                                 session: UserSession) -> Dict[str, Any]:
        """Analyze message and update conversation state."""
        
        # Detect topic changes
        new_topic = await self._detect_topic_change(message)
        if new_topic and new_topic != self.current_topic:
            await self._handle_topic_transition(new_topic, session)
            
        # Track conversation depth
        self.conversation_depth += 1
        
        # Identify teaching opportunities
        teaching_moments = await self._identify_teaching_moments(message)
        
        return {
            "current_topic": self.current_topic,
            "depth": self.conversation_depth,
            "teaching_moments": teaching_moments,
            "should_provide_exercise": self._should_inject_exercise(),
            "energy_level": await self._assess_user_energy(message)
        }
    
    async def generate_follow_up(self, 
                               user_message: str,
                               user_profile: UserProfile) -> str:
        """Generate natural follow-up response."""
        
        # Analyze message for content and errors
        content_analysis = await self._analyze_message_content(user_message)
        
        # Choose response strategy
        if content_analysis["has_errors"] and content_analysis["error_severity"] > 0.7:
            return await self._generate_correction_response(user_message, content_analysis)
        elif content_analysis["engagement_level"] < 0.5:
            return await self._generate_engagement_boost(content_analysis["topic"])
        else:
            return await self._generate_natural_continuation(user_message, content_analysis)
```

### Exercise Integration
```python
class ExerciseIntegrationManager:
    """Integrates exercises naturally into conversation flow."""
    
    async def inject_exercise_naturally(self, 
                                      conversation_context: Dict[str, Any],
                                      target_skill: SkillType) -> Optional[Exercise]:
        """Insert exercise that fits naturally in conversation."""
        
        if target_skill == SkillType.VOCABULARY:
            return await self._create_vocabulary_exercise(conversation_context)
        elif target_skill == SkillType.GRAMMAR:
            return await self._create_grammar_exercise(conversation_context)
        # ... other skills
        
    async def _create_vocabulary_exercise(self, context: Dict[str, Any]) -> Exercise:
        """Create vocabulary exercise based on conversation context."""
        current_topic = context.get("current_topic", "general")
        
        # Find words related to current topic that user might not know
        topic_vocabulary = await self._get_topic_vocabulary(current_topic)
        unknown_words = await self._filter_unknown_words(topic_vocabulary, context["user_id"])
        
        if unknown_words:
            target_word = random.choice(unknown_words)
            return Exercise(
                exercise_id=f"vocab_conv_{int(datetime.now().timestamp())}",
                exercise_type="definition",
                skill_type=SkillType.VOCABULARY,
                difficulty_level=context.get("difficulty", 0.5),
                content={
                    "question": f"By the way, do you know what '{target_word}' means? Take a guess!",
                    "word": target_word,
                    "context": f"We were just talking about {current_topic}",
                    "is_conversational": True
                },
                expected_answer=[self._get_word_definition(target_word)],
                hints=[f"It's related to {current_topic}", "Think about what we were discussing"],
                explanation=f"'{target_word}' is useful when talking about {current_topic}",
                points_value=15
            )
```

## Feedback Generation System

### Personalized Feedback
```python
class FeedbackGenerator:
    """Generates personalized, constructive feedback."""
    
    async def generate_comprehensive_feedback(self, 
                                            user_input: str,
                                            correct_answer: str,
                                            user_profile: UserProfile,
                                            performance_history: List[ExerciseResult]) -> FeedbackResponse:
        """Generate comprehensive, personalized feedback."""
        
        # Analyze the error
        error_analysis = await self._analyze_error(user_input, correct_answer)
        
        # Get user-specific encouragement style
        encouragement_style = await self._get_encouragement_style(
            user_profile, performance_history
        )
        
        # Generate specific corrections
        corrections = await self._generate_corrections(error_analysis)
        
        # Create personalized encouragement
        encouragement = await self._generate_encouragement(
            encouragement_style, error_analysis, performance_history
        )
        
        # Provide improvement tips
        improvement_tips = await self._generate_improvement_tips(
            error_analysis, user_profile
        )
        
        return FeedbackResponse(
            is_correct=error_analysis["is_correct"],
            score=error_analysis["similarity_score"],
            explanation=error_analysis["explanation"],
            corrections=corrections,
            encouragement=encouragement,
            improvement_tips=improvement_tips
        )
    
    async def _get_encouragement_style(self, 
                                     user_profile: UserProfile,
                                     history: List[ExerciseResult]) -> str:
        """Determine appropriate encouragement style for user."""
        
        recent_performance = [r.score for r in history[-10:]]
        avg_performance = sum(recent_performance) / len(recent_performance) if recent_performance else 0.5
        
        if avg_performance > 0.8:
            return "challenge_seeker"  # User is doing well, can handle more challenge
        elif avg_performance < 0.4:
            return "confidence_builder"  # User needs encouragement
        else:
            return "balanced"  # Standard encouragement
```

## Integration Points

### With AI Engineer Components
```python
# Get adaptive prompts based on difficulty
current_difficulty = await adaptive_learning.get_user_difficulty(user_id, skill_type)
prompt = self.prompt_manager.get_adaptive_prompt(current_difficulty, exercise_type)

# Use learning insights for personalized teaching
insights = await analytics.get_learning_insights(user_id)
teaching_strategy = self.strategy_manager.adapt_teaching_style(insights)
```

### With Telegram Bot Specialist
```python
# Provide responses for bot to send
teacher_response = await conversation_teacher.process_message(
    message, session, context
)

# Handle complex message types
if teacher_response.next_exercise:
    await bot.send_exercise(chat_id, teacher_response.next_exercise)
if teacher_response.achievements_unlocked:
    await bot.send_achievement_notification(chat_id, teacher_response.achievements_unlocked)
```

## Advanced Features

### Context-Aware Teaching
```python
class ContextAwareTeaching:
    """Adapts teaching based on conversation context and user state."""
    
    async def adapt_teaching_approach(self, 
                                    context: SharedContext,
                                    session: UserSession) -> Dict[str, Any]:
        """Adapt teaching approach based on context."""
        
        # Consider time of day, user energy, recent performance
        time_context = await self._analyze_time_context()
        energy_level = await self._assess_user_energy(context.user_profile)
        recent_struggles = await self._identify_recent_struggles(context.recent_performance)
        
        return {
            "patience_level": self._adjust_patience(energy_level),
            "explanation_depth": self._adjust_explanation_depth(recent_struggles),
            "exercise_intensity": self._adjust_intensity(time_context, energy_level),
            "encouragement_frequency": self._adjust_encouragement(recent_struggles)
        }
```

## Testing Requirements
- Conversation flow continuity tests
- Prompt appropriateness validation
- Feedback quality assessment  
- Persona consistency checks
- Multi-turn dialogue coherence
- Error correction effectiveness

## Success Criteria
- Natural, engaging conversations that feel human-like
- Effective error correction without discouraging users
- Appropriate difficulty progression in prompts
- High user engagement and session completion rates
- Measurable learning outcomes from conversations
- Consistent persona personalities across sessions

Your work will make the AI teachers feel alive and create the engaging learning experience that keeps users coming back.