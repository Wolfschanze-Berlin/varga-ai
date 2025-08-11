"""
Example usage of the Language Teacher Agent and AI components.
"""

import asyncio
import json
from typing import Dict, Any

from .agent import LanguageTeacherAgent
from .ai.adaptive_learning import AdaptiveLearningEngine, AdaptationStrategy
from .ai.nlp_processor import NLPProcessor
from .ai.spaced_repetition import SpacedRepetitionSystem, ReviewResult
from .ai.learning_analytics import LearningAnalytics, MetricType
from .ai.content_generator import ContentGenerator, ContentType, DifficultyLevel
from .integration import LanguageTeacherIntegration


async def example_basic_usage():
    """Example of basic Language Teacher Agent usage."""
    print("=== Basic Language Teacher Agent Usage ===\n")
    
    # Initialize agent with basic configuration
    config = {
        'target_language': 'english',
        'agent_name': 'EnglishTeacher',
        'adaptive_learning': {
            'adaptation_strategy': 'mixed'
        }
    }
    
    agent = LanguageTeacherAgent(config)
    
    # Start learning session for a student
    student_id = "student123"
    session_prefs = {
        'duration_minutes': 20,
        'max_items': 8,
        'focus_areas': ['vocabulary', 'grammar']
    }
    
    print("Starting learning session...")
    session_result = await agent.start_learning_session(student_id, session_prefs)
    
    if 'error' in session_result:
        print(f"Error: {session_result['error']}")
        return
    
    print(f"Session started: {session_result['session_id']}")
    print(f"Welcome: {session_result['welcome_message']}")
    print(f"First activity: {session_result['first_activity']['title']}")
    print()
    
    # Simulate student responses
    responses = [
        ("Hello, how are you?", 5.2),  # (response, time_seconds)
        ("I am good", 3.8),
        ("The cats plays in the garden", 7.1),  # Grammar error
        ("She goes to school every day", 4.5),
        ("I have 25 years old", 6.2),  # Common ESL error
    ]
    
    for i, (response, response_time) in enumerate(responses):
        print(f"--- Response {i+1}: '{response}' ---")
        
        result = await agent.process_student_response(
            student_id, response, response_time=response_time
        )
        
        if 'error' in result:
            print(f"Error: {result['error']}")
            continue
        
        print(f"Feedback: {result['feedback'][:100]}...")
        print(f"Correct: {result['analysis']['is_correct']}")
        print(f"Errors found: {result['analysis']['errors_found']}")
        print(f"Progress: {result['progress']}")
        
        next_activity = result.get('next_activity', {})
        if next_activity:
            print(f"Next activity: {next_activity['title']}")
        print()
    
    # End session
    print("Ending learning session...")
    end_result = await agent.end_learning_session(student_id)
    
    if 'error' not in end_result:
        summary = end_result['summary']
        print(f"Session summary:")
        print(f"  Duration: {summary['duration_minutes']} minutes")
        print(f"  Activities: {summary['activities_completed']}")
        print(f"  Accuracy: {summary['accuracy_rate']:.1%}")
        print(f"  Achievements: {summary['achievements']}")
        print(f"  Goodbye: {end_result['goodbye_message']}")
    
    print("\n" + "="*50 + "\n")


async def example_adaptive_learning():
    """Example of adaptive learning engine usage."""
    print("=== Adaptive Learning Engine Example ===\n")
    
    engine = AdaptiveLearningEngine()
    student_id = "adaptive_student"
    
    # Add some content items
    content_items = [
        {
            'item_id': 'vocab_hello',
            'type': 'vocabulary',
            'difficulty': 0.2,
            'knowledge_components': ['basic_vocabulary', 'greetings']
        },
        {
            'item_id': 'grammar_present_tense',
            'type': 'grammar', 
            'difficulty': 0.6,
            'knowledge_components': ['present_tense', 'verb_conjugation']
        }
    ]
    
    for item in content_items:
        engine.add_content_item(item['item_id'], item)
        print(f"Added content: {item['item_id']}")
    
    # Simulate student performance
    performances = [
        ('vocab_hello', True, 3.2),
        ('vocab_hello', True, 2.8),
        ('grammar_present_tense', False, 8.5),
        ('grammar_present_tense', False, 7.2),
        ('grammar_present_tense', True, 6.1),
    ]
    
    print("\nUpdating student performance...")
    for item_id, correct, response_time in performances:
        engine.update_student_performance(student_id, item_id, correct, response_time)
        print(f"  {item_id}: {'✓' if correct else '✗'} ({response_time}s)")
    
    # Get learning recommendations
    recommendation = engine.get_next_recommendation(student_id)
    print(f"\nNext recommendation:")
    print(f"  Item: {recommendation.item_id}")
    print(f"  Type: {recommendation.item_type}")
    print(f"  Difficulty: {recommendation.difficulty:.2f}")
    print(f"  Success probability: {recommendation.success_probability:.2f}")
    print(f"  Reasoning: {recommendation.reasoning}")
    
    # Analyze student progress
    progress = engine.analyze_student_progress(student_id)
    print(f"\nStudent progress analysis:")
    print(f"  Proficiency level: {progress.get('proficiency_level', 'unknown')}")
    print(f"  Overall accuracy: {progress.get('overall_progress', {}).get('accuracy', 0):.2f}")
    print(f"  Knowledge summary: {progress.get('knowledge_summary', {})}")
    
    print("\n" + "="*50 + "\n")


async def example_nlp_processing():
    """Example of NLP processor usage."""
    print("=== Natural Language Processing Example ===\n")
    
    processor = NLPProcessor('english')
    
    # Test sentences with various errors
    test_sentences = [
        ("Hello, how are you today?", "Correct greeting"),
        ("I am go to school every day", "Grammar error - verb form"),
        ("The cat eated the fish", "Grammar error - irregular past tense"),
        ("Ther house is very beautifull", "Spelling errors"),
        ("I have 25 years old", "Common ESL error"),
        ("She don't like nothing", "Double negative"),
    ]
    
    for sentence, description in test_sentences:
        print(f"Analyzing: '{sentence}' ({description})")
        
        analysis = processor.analyze_text(sentence)
        
        print(f"  Complexity: {analysis.complexity_score:.2f}")
        print(f"  Readability: {analysis.readability_score:.2f}")
        print(f"  Vocabulary level: {analysis.vocabulary_level}")
        print(f"  Errors found: {len(analysis.errors)}")
        
        for error in analysis.errors[:2]:  # Show first 2 errors
            print(f"    - {error.error_type.value}: '{error.original_text}' → '{error.corrected_text}'")
            print(f"      {error.explanation}")
        
        # Generate feedback
        feedback = processor.generate_feedback(analysis)
        print(f"  Feedback: {feedback[:80]}...")
        print()
    
    # Test semantic similarity
    print("Semantic similarity examples:")
    similarity_tests = [
        ("I am happy", "I feel happy"),
        ("The cat is sleeping", "A cat sleeps"),
        ("Hello world", "Goodbye universe"),
    ]
    
    for text1, text2 in similarity_tests:
        similarity = processor.calculate_semantic_similarity(text1, text2)
        print(f"  '{text1}' vs '{text2}'")
        print(f"    Similarity: {similarity.similarity_score:.2f}")
        print(f"    Semantic match: {similarity.is_semantically_correct}")
        print()
    
    print("="*50 + "\n")


async def example_spaced_repetition():
    """Example of spaced repetition system usage."""
    print("=== Spaced Repetition System Example ===\n")
    
    srs = SpacedRepetitionSystem()
    student_id = "srs_student"
    
    # Add vocabulary cards
    vocab_cards = [
        ("hello", "A greeting used when meeting someone", "vocabulary"),
        ("goodbye", "A farewell used when leaving", "vocabulary"),  
        ("beautiful", "Pleasing to look at", "vocabulary"),
        ("present_tense", "Grammar rule for current actions", "grammar"),
    ]
    
    print("Adding cards to spaced repetition system...")
    for word, definition, card_type in vocab_cards:
        content = json.dumps({'word': word, 'definition': definition})
        card = srs.add_card(word, content, card_type, [card_type, 'basic'])
        srs.add_card_to_student_deck(student_id, card.card_id)
        print(f"  Added: {word}")
    
    # Start review session
    session_id = srs.start_review_session(student_id)
    print(f"\nStarted review session: {session_id}")
    
    # Get due cards and simulate reviews
    due_cards = srs.get_due_cards(student_id, limit=3)
    print(f"Cards due for review: {len(due_cards)}")
    
    # Simulate review results
    review_results = [ReviewResult.GOOD, ReviewResult.EASY, ReviewResult.HARD]
    
    for i, card in enumerate(due_cards[:3]):
        result = review_results[i] if i < len(review_results) else ReviewResult.GOOD
        response_time = 3.5 + i * 0.8
        
        print(f"\nReviewing card: {card.card_id}")
        print(f"  Content: {card.content[:50]}...")
        print(f"  Current interval: {card.interval} days")
        print(f"  Review result: {result.value}")
        
        srs.review_card(student_id, card.card_id, result, response_time)
        
        # Show updated card info
        updated_card = srs.cards[card.card_id]
        print(f"  New interval: {updated_card.interval} days")
        print(f"  Ease factor: {updated_card.ease_factor:.2f}")
        print(f"  Success rate: {updated_card.success_rate:.2f}")
    
    # End session and get stats
    stats = srs.end_review_session(session_id)
    print(f"\nSession statistics: {stats}")
    
    # Get student statistics
    student_stats = srs.get_student_statistics(student_id)
    print(f"\nStudent SRS statistics:")
    for key, value in student_stats.items():
        if key != 'error':
            print(f"  {key}: {value}")
    
    print("\n" + "="*50 + "\n")


async def example_telegram_integration():
    """Example of Telegram bot integration."""
    print("=== Telegram Integration Example ===\n")
    
    integration = LanguageTeacherIntegration()
    user_id = "telegram_user_123"
    
    print("Simulating Telegram conversation...")
    
    # Simulate conversation flow
    messages = [
        "/start",
        "Hello teacher!",
        "I want to learn English",
        "The cat are sleeping",  # Grammar error
        "/progress",
        "/end"
    ]
    
    for message in messages:
        print(f"User: {message}")
        
        response = await integration.handle_telegram_message(user_id, message)
        
        # Truncate long responses for display
        if len(response) > 200:
            display_response = response[:197] + "..."
        else:
            display_response = response
            
        print(f"Bot: {display_response}")
        print("-" * 40)
    
    # Show integration status
    status = integration.get_integration_status()
    print(f"\nIntegration Status:")
    print(f"  Status: {status.get('integration_status')}")
    print(f"  Active sessions: {status.get('active_telegram_sessions', 0)}")
    print(f"  Components: {status.get('components', {})}")
    
    print("\n" + "="*50 + "\n")


async def example_learning_analytics():
    """Example of learning analytics usage."""
    print("=== Learning Analytics Example ===\n")
    
    analytics = LearningAnalytics()
    student_id = "analytics_student"
    
    # Record various learning metrics over simulated time
    print("Recording learning metrics...")
    
    # Simulate a week of learning data
    import random
    from datetime import datetime, timedelta
    
    base_time = datetime.now() - timedelta(days=7)
    
    for day in range(7):
        for session in range(2):  # 2 sessions per day
            session_time = base_time + timedelta(days=day, hours=session*8)
            
            # Simulate gradually improving performance
            base_accuracy = 0.6 + (day * 0.05)  # Improve over time
            accuracy = min(0.95, base_accuracy + random.uniform(-0.1, 0.1))
            
            speed = 0.7 + random.uniform(-0.2, 0.2)
            engagement = 0.8 + random.uniform(-0.1, 0.1)
            
            # Record metrics
            analytics.record_metric(student_id, MetricType.ACCURACY, accuracy)
            analytics.record_metric(student_id, MetricType.SPEED, speed)
            analytics.record_metric(student_id, MetricType.ENGAGEMENT, engagement)
            
            # Record session data
            session_data = {
                'session_id': f"session_{day}_{session}",
                'duration_minutes': 15 + random.randint(-3, 5),
                'items_completed': 5 + random.randint(-1, 3),
                'accuracy': accuracy,
                'engagement_score': engagement,
                'session_type': 'practice'
            }
            analytics.record_session(student_id, session_data)
    
    print("Analyzing performance trends...")
    
    # Analyze trends for different metrics
    for metric_type in [MetricType.ACCURACY, MetricType.ENGAGEMENT, MetricType.SPEED]:
        trend = analytics.analyze_performance_trend(student_id, metric_type)
        
        print(f"\n{metric_type.value.title()} Trend:")
        print(f"  Direction: {trend.trend_direction}")
        print(f"  Strength: {trend.trend_strength:.2f}")
        print(f"  Recent average: {trend.recent_average:.2f}")
        print(f"  Change: {trend.change_percentage:+.1f}%")
    
    # Identify learning style
    style, confidence = analytics.identify_learning_style(student_id)
    print(f"\nLearning Style:")
    print(f"  Identified: {style.value}")
    print(f"  Confidence: {confidence:.2f}")
    
    # Generate insights
    insights = analytics.generate_insights(student_id)
    print(f"\nLearning Insights:")
    for insight in insights[:3]:
        print(f"  • {insight.title}")
        print(f"    {insight.description}")
        print(f"    Recommendation: {insight.recommendation}")
        print(f"    Priority: {insight.priority:.2f}")
        print()
    
    # Get comprehensive report
    report = analytics.get_comprehensive_report(student_id)
    print(f"Comprehensive Report:")
    print(f"  Data span: {report.get('data_summary', {}).get('data_span_days', 0)} days")
    print(f"  Total sessions: {report.get('data_summary', {}).get('total_sessions', 0)}")
    print(f"  Overall progress: {report.get('overall_progress', {})}")
    
    print("\n" + "="*50 + "\n")


async def main():
    """Run all examples."""
    print("🎓 Language Teacher Agent - AI Components Demo\n")
    print("This demo showcases the comprehensive AI-powered language learning system.\n")
    
    try:
        # Run all examples
        await example_basic_usage()
        await example_adaptive_learning()
        await example_nlp_processing()
        await example_spaced_repetition()
        await example_learning_analytics()
        await example_telegram_integration()
        
        print("✅ All examples completed successfully!")
        print("\nThe Language Teacher Agent provides a complete AI-powered language learning experience with:")
        print("• Adaptive difficulty adjustment based on student performance")
        print("• Advanced NLP for error detection and feedback")
        print("• Spaced repetition for optimal retention")
        print("• Comprehensive learning analytics and insights")
        print("• Dynamic content generation")
        print("• Seamless Telegram bot integration")
        print("• Multi-agent AutoGen framework support")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())