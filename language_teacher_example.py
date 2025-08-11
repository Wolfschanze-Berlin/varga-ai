"""
Language Teacher Bot Usage Example
Demonstrates how to interact with the AI Language Teacher Bot components.
"""

import asyncio
import os
from datetime import datetime
from typing import Dict, Any

# Set up environment variables for testing
os.environ.setdefault('TELEGRAM_BOT_TOKEN', 'test_token_123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ')
os.environ.setdefault('OPENAI_API_KEY', 'test_openai_key')

from agents.categories.education.language_teacher.agent import LanguageTeacherAgent
from agents.categories.education.language_teacher.teachers.conversation_teacher import ConversationTeacher
from agents.categories.education.language_teacher.modules.progress_tracker import ProgressTracker
from agents.categories.education.language_teacher.modules.achievement_system import AchievementSystem
from agents.categories.education.language_teacher.voice_handler import VoiceMessageHandler


async def demo_language_teacher_agent():
    """Demonstrate the Language Teacher Agent functionality."""
    print("🎓 Language Teacher Agent Demo")
    print("=" * 50)
    
    # Initialize the language teacher agent
    config = {
        'target_language': 'english',
        'agent_name': 'EnglishTeacher',
        'adaptive_learning': {'algorithm': 'irt'},
        'spaced_repetition': {'algorithm': 'sm2_plus'},
        'analytics': {'track_detailed_metrics': True},
        'content_generation': {'enable_dynamic_content': True}
    }
    
    teacher = LanguageTeacherAgent(config)
    
    # Start a learning session
    print("\n📚 Starting learning session...")
    session_result = await teacher.start_learning_session(
        student_id="demo_user_123",
        session_preferences={
            'duration_minutes': 15,
            'max_items': 5,
            'focus_areas': ['vocabulary', 'grammar']
        }
    )
    
    print(f"Session ID: {session_result.get('session_id')}")
    print(f"Welcome Message: {session_result.get('welcome_message')}")
    print(f"First Activity: {session_result.get('first_activity', {}).get('title', 'N/A')}")
    
    # Process a student response
    print("\n✍️ Processing student response...")
    response_result = await teacher.process_student_response(
        student_id="demo_user_123",
        response="Hello, how are you today?",
        activity_id=session_result.get('first_activity', {}).get('activity_id'),
        response_time=3.5
    )
    
    print(f"Feedback: {response_result.get('feedback')}")
    print(f"Next Activity: {response_result.get('next_activity', {}).get('title', 'N/A')}")
    
    # End the session
    print("\n📊 Ending learning session...")
    end_result = await teacher.end_learning_session("demo_user_123")
    
    summary = end_result.get('summary', {})
    print(f"Duration: {summary.get('duration_minutes')} minutes")
    print(f"Activities Completed: {summary.get('activities_completed')}")
    print(f"Accuracy Rate: {summary.get('accuracy_rate', 0):.1%}")
    print(f"Achievements: {summary.get('achievements', [])}")
    
    # Get student progress
    print("\n📈 Student progress report...")
    progress = teacher.get_student_progress("demo_user_123")
    print(f"Total Sessions: {progress.get('learning_analytics', {}).get('total_sessions', 0)}")
    print(f"Study Time: {progress.get('adaptive_learning', {}).get('study_time', '0:00:00')}")
    print(f"Retention Rate: {progress.get('spaced_repetition', {}).get('retention_rate', 0):.1%}")
    
    return teacher


async def demo_conversation_teacher():
    """Demonstrate the Conversation Teacher functionality."""
    print("\n🗣️ Conversation Teacher Demo")
    print("=" * 50)
    
    conversation_teacher = ConversationTeacher()
    await conversation_teacher.setup()
    
    # Simulate user profile
    user_profile = {
        'user_id': 123,
        'target_language': 'english',
        'proficiency_level': 'beginner',
        'name': 'Demo User'
    }
    
    context = {
        'user_profile': user_profile,
        'language': 'english',
        'level': 'beginner',
        'mode': 'conversation_practice'
    }
    
    # Start conversation
    print("\n💬 Starting conversation...")
    response1 = await conversation_teacher.process_message("Let's start talking!", context)
    print(f"Teacher: {response1}")
    
    # Student responds
    print("\n👤 Student: 'Hello! I am good, thank you. How are you?'")
    response2 = await conversation_teacher.process_message(
        "Hello! I am good, thank you. How are you?", context
    )
    print(f"Teacher: {response2}")
    
    # Another exchange
    print("\n👤 Student: 'I like learn English very much!'")
    response3 = await conversation_teacher.process_message(
        "I like learn English very much!", context
    )
    print(f"Teacher: {response3}")
    
    # Get conversation stats
    stats = conversation_teacher.get_conversation_stats(123)
    print(f"\n📊 Conversation Stats:")
    print(f"Total turns: {stats.get('total_turns')}")
    print(f"Vocabulary learned: {stats.get('vocabulary_learned')}")
    print(f"Corrections received: {stats.get('corrections_received')}")
    
    await conversation_teacher.cleanup()
    return conversation_teacher


async def demo_progress_tracking():
    """Demonstrate the Progress Tracker functionality."""
    print("\n📈 Progress Tracker Demo")
    print("=" * 50)
    
    progress_tracker = ProgressTracker()
    await progress_tracker.initialize()
    
    # Log some activities
    print("\n📝 Logging learning activities...")
    
    activities = [
        {'type': 'conversation', 'duration': 5, 'points': 10},
        {'type': 'vocabulary', 'duration': 3, 'points': 5},
        {'type': 'homework', 'duration': 8, 'points': 15},
        {'type': 'pronunciation', 'duration': 4, 'points': 8}
    ]
    
    for i, activity in enumerate(activities):
        success = await progress_tracker.log_activity(
            user_id=123,
            activity_type=activity['type'],
            duration_minutes=activity['duration'],
            points=activity['points'],
            details={'exercise_id': f"demo_{i}"}
        )
        print(f"✅ Logged {activity['type']} activity: {success}")
    
    # Get user progress
    print("\n📊 User progress:")
    progress = await progress_tracker.get_user_progress(123)
    
    print(f"Total minutes: {progress.get('total_minutes')}")
    print(f"Total activities: {progress.get('total_activities')}")
    print(f"Total points: {progress.get('total_points')}")
    print(f"Current streak: {progress.get('current_streak')}")
    print(f"Daily goal met: {progress.get('daily_goal_met')}")
    
    # Get recent activities
    recent = await progress_tracker.get_recent_activities(123, days=7)
    print(f"\n🕐 Recent activities ({len(recent)}):")
    for activity in recent[:3]:
        print(f"- {activity.activity_type.value}: {activity.points_earned} points")
    
    await progress_tracker.cleanup()
    return progress_tracker


async def demo_achievement_system():
    """Demonstrate the Achievement System functionality."""
    print("\n🏆 Achievement System Demo")
    print("=" * 50)
    
    achievement_system = AchievementSystem()
    await achievement_system.initialize()
    
    # Simulate some achievements being earned
    print("\n🎉 Checking for achievements...")
    
    # Check for welcome achievement
    achievements = await achievement_system.check_achievements(
        user_id=123,
        activity_data={'setup_complete': True}
    )
    
    for achievement in achievements:
        print(f"🏅 Earned: {achievement.name} - {achievement.description}")
        notification = achievement_system.format_achievement_notification(achievement)
        print(notification)
        print()
    
    # Get achievement stats
    print("\n📊 Achievement statistics:")
    stats = await achievement_system.get_achievement_stats(123)
    
    print(f"Total earned: {stats.get('total_earned')}")
    print(f"Total available: {stats.get('total_available')}")
    print(f"Completion: {stats.get('completion_percent', 0):.1f}%")
    print(f"Total points: {stats.get('total_points')}")
    
    # Get available achievements
    available = await achievement_system.get_available_achievements(123)
    print(f"\n🎯 Next available achievements ({len(available)}):")
    for achievement in available[:3]:
        print(f"- {achievement.icon} {achievement.name}: {achievement.description}")
    
    await achievement_system.cleanup()
    return achievement_system


async def demo_voice_handler():
    """Demonstrate the Voice Handler functionality."""
    print("\n🎤 Voice Handler Demo")
    print("=" * 50)
    
    voice_handler = VoiceMessageHandler({
        'speech_recognition_provider': 'mock',
        'pronunciation_scoring': True
    })
    
    # Get a pronunciation exercise
    print("\n📝 Getting pronunciation exercise...")
    exercise = voice_handler.get_pronunciation_exercise('beginner')
    formatted_exercise = voice_handler.format_pronunciation_exercise(exercise)
    print(formatted_exercise)
    
    # Simulate processing a voice message
    print("\n🎵 Processing voice message...")
    
    # Create a mock audio file
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
        temp_file.write(b"mock_audio_data")
        temp_file_path = temp_file.name
    
    user_profile = {
        'target_language': 'english',
        'proficiency_level': 'beginner'
    }
    
    context = {
        'expected_text': exercise['text'],
        'exercise_type': 'pronunciation_practice'
    }
    
    result = await voice_handler.process_voice_message(
        temp_file_path, user_profile, context
    )
    
    if result.success:
        print(f"🎯 Transcription: {result.transcription}")
        print(f"📊 Pronunciation Score: {result.pronunciation_score:.1%}")
        print(f"💬 Feedback:")
        print(result.feedback)
    else:
        print(f"❌ Error: {result.error}")
    
    # Cleanup
    await voice_handler.cleanup_temp_files(temp_file_path)
    await voice_handler.cleanup()
    
    return voice_handler


async def main():
    """Run all demonstrations."""
    print("🎓 AI Language Teacher Bot - Complete Demo")
    print("=" * 60)
    print()
    
    try:
        # Run all demos
        await demo_language_teacher_agent()
        await demo_conversation_teacher()
        await demo_progress_tracking()
        await demo_achievement_system()
        await demo_voice_handler()
        
        print("\n✅ All demos completed successfully!")
        print("\n🎉 The AI Language Teacher Bot is ready to help users learn languages!")
        print("\nTo start the full bot, run:")
        print("  python language_teacher_bot.py")
        print("\nOr use the startup script:")
        print("  ./start_language_teacher.sh")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())