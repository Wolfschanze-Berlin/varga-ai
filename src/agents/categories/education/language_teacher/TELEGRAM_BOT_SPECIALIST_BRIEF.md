# Telegram Bot Specialist - Implementation Brief

## Overview
You are responsible for implementing the Telegram bot architecture and integration for the Language Teacher Bot. This builds upon the existing telegram_bot_main.py infrastructure.

## Your Core Responsibilities

### 1. Bot Architecture & Message Routing
- Extend the existing TelegramAssistantBot to support language learning
- Implement teacher persona routing (ConversationTeacher vs HomeworkTeacher)
- Handle complex command structures for learning activities
- Manage user session state across different learning modes

### 2. Telegram API Integration
- Voice message support for pronunciation practice
- File upload/download for exercise materials
- Inline keyboards for interactive exercises
- Poll creation for multiple choice questions
- Message scheduling for spaced repetition reminders

### 3. Command Implementation
Design and implement these commands:
```
/learn - Start a learning session with ConversationTeacher
/practice - Begin homework exercises with HomeworkTeacher
/homework - Access structured assignments
/progress - View learning progress and statistics
/settings - Modify learning preferences
/streak - View current learning streak
/achievements - Show unlocked achievements
/vocab - Practice vocabulary with spaced repetition
/test - Take proficiency assessment
/help_lang - Language learning specific help
```

### 4. Session Management
- Track active learning sessions per user
- Persist session state between message exchanges
- Handle session timeouts and cleanup
- Support concurrent users with proper isolation

## Integration Specifications

### Shared Components You'll Use
```python
from ..shared.interfaces import (
    UserProfile, UserSession, TeacherResponse, SharedContext,
    TeacherType, SessionType, TeacherPersona
)
from ..database.models import (
    DatabaseManager, UserRepository, SessionRepository
)
```

### Key Files You'll Create
```
agents/categories/education/language_teacher/
├── language_teacher_orchestrator.py    # Main orchestrator
├── telegram_language_bot.py           # Extended bot class
├── command_handlers.py               # Command implementations
├── session_manager.py               # Session state management
├── message_router.py               # Route to correct teacher
└── voice_handler.py               # Voice message processing
```

### Expected Interfaces

#### LanguageTeacherOrchestrator
```python
class LanguageTeacherOrchestrator:
    """Main orchestrator for language learning bot."""
    
    async def initialize(self) -> bool:
        """Initialize all components."""
        
    async def process_message(self, message: str, context: Dict) -> str:
        """Route message to appropriate teacher persona."""
        
    async def handle_command(self, command: str, args: List[str], 
                           user_profile: UserProfile) -> TeacherResponse:
        """Handle slash commands."""
        
    async def start_session(self, user_id: int, session_type: SessionType) -> UserSession:
        """Start new learning session."""
```

#### Extended Command Handlers
```python
async def handle_learn_command(message: TelegramMessage) -> None:
    """Start conversation practice session."""
    
async def handle_practice_command(message: TelegramMessage) -> None:
    """Start homework exercise session."""
    
async def handle_progress_command(message: TelegramMessage) -> None:
    """Show user progress and statistics."""
    
async def handle_voice_message(message: TelegramMessage) -> None:
    """Process voice messages for pronunciation."""
```

## Technical Requirements

### Database Integration
You have access to these repositories:
- `UserRepository` - User profiles and preferences
- `SessionRepository` - Active learning sessions
- `ProgressRepository` - Learning progress tracking
- `ExerciseRepository` - Exercise results

### Teacher Persona Integration
```python
# Route messages to appropriate teacher
if session.current_teacher == TeacherType.CONVERSATION_TEACHER:
    response = await self.conversation_teacher.process_message(
        message, session, shared_context
    )
elif session.current_teacher == TeacherType.HOMEWORK_TEACHER:
    response = await self.homework_teacher.process_message(
        message, session, shared_context
    )
```

### Error Handling
- Graceful degradation when teachers are unavailable
- Retry logic for failed voice processing
- User-friendly error messages in target language
- Fallback to text when voice features fail

### Performance Considerations
- Cache user profiles for active sessions
- Batch database operations where possible
- Optimize voice file processing
- Rate limiting per user to prevent abuse

## Integration Points

### With AI Engineer Components
```python
# Get adaptive exercises
exercise = await self.adaptive_learning.get_next_exercise(
    user_profile, skill_type, difficulty
)

# Record performance for learning
await self.adaptive_learning.record_performance(
    user_id, exercise_id, score
)
```

### With Prompt Engineer Components
```python
# Get contextual prompts
prompt = await self.prompt_manager.get_teacher_prompt(
    teacher_type, user_level, conversation_context
)

# Generate feedback
feedback = await self.feedback_generator.provide_feedback(
    user_input, expected_answer, error_type
)
```

## Message Flow Architecture
```
Telegram Message → MessageRouter → SessionManager → TeacherPersona → Response Generator → Telegram API
```

### Sample Implementation Pattern
```python
async def handle_telegram_message(self, message: TelegramMessage) -> None:
    # 1. Get or create user profile
    user_profile = await self.user_repo.get_user_by_telegram_id(message.chat_id)
    
    # 2. Get or create active session
    session = await self.session_manager.get_or_create_session(
        user_profile.user_id, message
    )
    
    # 3. Build shared context
    context = await self.build_shared_context(user_profile, session)
    
    # 4. Route to appropriate teacher
    teacher = self.get_teacher_for_session(session)
    response = await teacher.process_message(message.text, session, context)
    
    # 5. Handle response (text, voice, exercises, achievements)
    await self.send_response(message.chat_id, response)
    
    # 6. Update session and progress
    await self.update_user_state(session, response)
```

## Voice Message Handling
```python
async def handle_voice_message(self, message: TelegramMessage) -> None:
    # 1. Download voice file
    voice_file = await self.telegram_bot.download_voice(message.voice.file_id)
    
    # 2. Transcribe to text
    transcription = await self.voice_processor.transcribe_audio(voice_file)
    
    # 3. Process as regular message
    await self.handle_telegram_message(
        TelegramMessage(text=transcription, **message.dict())
    )
    
    # 4. Analyze pronunciation if in speaking exercise
    if session.current_exercise and session.current_exercise.skill_type == SkillType.SPEAKING:
        pronunciation_analysis = await self.voice_processor.analyze_pronunciation(
            voice_file, session.current_exercise.expected_answer
        )
        feedback = await self.voice_processor.generate_pronunciation_feedback(
            pronunciation_analysis
        )
        await self.telegram_bot.send_message(message.chat_id, feedback)
```

## Testing Requirements
- Unit tests for all command handlers
- Integration tests with teacher personas
- Voice message processing tests
- Session management edge cases
- Error handling scenarios

## Dependencies
- Existing telegram_bot_main.py infrastructure
- ConversationTeacher implementation (from prompt-engineer)
- HomeworkTeacher implementation (from prompt-engineer)
- AdaptiveLearningSystem (from ai-engineer)
- Database repositories
- Voice processing libraries (speech_recognition, pydub)

## Deployment Considerations
- Environment variables for voice processing API keys
- File storage for voice messages and exercise materials
- Database connection pooling for concurrent users
- Monitoring and logging for voice processing errors
- Backup strategy for user sessions

## Success Criteria
- All commands function correctly
- Voice messages are processed accurately
- Teacher persona switching works seamlessly
- Session state persists across conversations
- Error handling provides good user experience
- Performance meets < 2 second response time requirement

This implementation will serve as the foundation that connects users to the intelligent teaching system built by your fellow specialists.