# AI-Powered Adaptive Language Learning System

A comprehensive AI-driven language learning system built with Microsoft AutoGen framework, featuring adaptive learning algorithms, natural language processing, spaced repetition, learning analytics, and dynamic content generation.

## 🌟 Features

### Core AI Components

1. **Adaptive Learning Engine**
   - Student proficiency modeling (IRT/BKT models)
   - Dynamic difficulty adjustment
   - Personalized learning paths
   - Performance prediction
   - Optimal next-item selection

2. **Natural Language Processing**
   - Grammar error detection and correction
   - Semantic similarity for answer validation
   - Context-aware conversation generation
   - Language complexity analysis
   - Pronunciation assessment support

3. **Spaced Repetition System**
   - Forgetting curve modeling
   - Optimal review scheduling (SM-2+ algorithm)
   - Vocabulary retention tracking
   - Adaptive interval adjustment

4. **Learning Analytics**
   - Progress tracking metrics
   - Learning style identification
   - Weakness detection
   - Performance forecasting
   - Engagement analysis

5. **Content Generation**
   - Dynamic exercise creation
   - Context-relevant examples
   - Personalized stories/scenarios
   - Difficulty-appropriate content

6. **AutoGen Multi-Agent System**
   - Teacher agent for instruction
   - Assessment agent for evaluation
   - Content creation agent
   - Coordinated agent interactions

## 🏗️ Architecture

```
Language Teacher Agent
├── AI Components/
│   ├── Adaptive Learning Engine
│   ├── NLP Processor
│   ├── Spaced Repetition System
│   ├── Learning Analytics
│   └── Content Generator
├── Models/
│   ├── Student Model
│   ├── IRT Model
│   └── BKT Model
├── AutoGen Agents/
│   ├── Teacher Agent
│   ├── Assessment Agent
│   └── Content Agent
└── Integration Layer/
    └── Telegram Bot Interface
```

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install autogen-agentchat numpy pandas nltk scipy pyyaml

# Download NLTK data (first time only)
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

### Basic Usage

```python
from agents.categories.education.language_teacher.agent import LanguageTeacherAgent

# Initialize agent
config = {
    'target_language': 'english',
    'adaptive_learning': {'adaptation_strategy': 'mixed'}
}
agent = LanguageTeacherAgent(config)

# Start learning session
session_result = await agent.start_learning_session(
    student_id="student123",
    session_preferences={'duration_minutes': 15, 'focus_areas': ['vocabulary']}
)

# Process student response
result = await agent.process_student_response(
    student_id="student123",
    response="Hello, how are you?",
    response_time=3.5
)

print(result['feedback'])
print(result['next_activity'])
```

### Telegram Integration

```python
from agents.categories.education.language_teacher.integration import LanguageTeacherIntegration

# Initialize integration
integration = LanguageTeacherIntegration()

# Handle Telegram message
response = await integration.handle_telegram_message(
    user_id="telegram_user",
    message="I want to practice English grammar"
)

print(response)
```

## 🧠 AI Components Deep Dive

### Adaptive Learning Engine

The adaptive learning engine uses multiple algorithms to personalize the learning experience:

- **IRT (Item Response Theory)**: Models student ability and item difficulty
- **BKT (Bayesian Knowledge Tracing)**: Tracks knowledge state evolution
- **Difficulty Optimization**: Maintains optimal challenge level
- **Learning Path Generation**: Creates personalized sequences

```python
from agents.categories.education.language_teacher.ai.adaptive_learning import AdaptiveLearningEngine

engine = AdaptiveLearningEngine()

# Add content items
engine.add_content_item('vocab_hello', {
    'type': 'vocabulary',
    'difficulty': 0.3,
    'knowledge_components': ['basic_vocabulary', 'greetings']
})

# Update student performance
engine.update_student_performance(
    student_id="student123",
    item_id="vocab_hello", 
    correct=True,
    response_time=3.2
)

# Get next recommendation
recommendation = engine.get_next_recommendation("student123")
```

### NLP Processor

Advanced natural language processing for error detection and analysis:

```python
from agents.categories.education.language_teacher.ai.nlp_processor import NLPProcessor

processor = NLPProcessor('english')

# Analyze student response
analysis = processor.analyze_text("I am go to school every day")

print(f"Errors found: {len(analysis.errors)}")
print(f"Complexity: {analysis.complexity_score}")
print(f"Feedback: {processor.generate_feedback(analysis)}")
```

### Spaced Repetition System

Implements advanced spaced repetition algorithms for optimal retention:

```python
from agents.categories.education.language_teacher.ai.spaced_repetition import (
    SpacedRepetitionSystem, ReviewResult
)

srs = SpacedRepetitionSystem({'algorithm': 'sm2_plus'})

# Add vocabulary card
card = srs.add_card(
    card_id="hello_card",
    content="Hello - A greeting",
    card_type="vocabulary",
    knowledge_components=["greetings"]
)

# Review card
srs.review_card("student123", "hello_card", ReviewResult.GOOD, response_time=3.5)

# Get due cards
due_cards = srs.get_due_cards("student123")
```

### Learning Analytics

Comprehensive analytics for tracking progress and generating insights:

```python
from agents.categories.education.language_teacher.ai.learning_analytics import (
    LearningAnalytics, MetricType
)

analytics = LearningAnalytics()

# Record learning metrics
analytics.record_metric("student123", MetricType.ACCURACY, 0.85)
analytics.record_metric("student123", MetricType.ENGAGEMENT, 0.92)

# Analyze trends
trend = analytics.analyze_performance_trend("student123", MetricType.ACCURACY)
print(f"Trend: {trend.trend_direction} ({trend.change_percentage:+.1f}%)")

# Generate insights
insights = analytics.generate_insights("student123")
for insight in insights:
    print(f"• {insight.title}: {insight.recommendation}")
```

### Content Generator

Dynamic content generation for personalized learning materials:

```python
from agents.categories.education.language_teacher.ai.content_generator import (
    ContentGenerator, ContentType, DifficultyLevel
)

generator = ContentGenerator()

# Generate vocabulary content
vocab_content = generator.generate_vocabulary_content(
    difficulty=DifficultyLevel.INTERMEDIATE,
    topic="travel",
    count=3
)

# Generate grammar exercise
grammar_content = generator.generate_grammar_content(
    difficulty=DifficultyLevel.BEGINNER,
    grammar_focus="present_tense"
)

# Generate personalized content
personalized = generator.generate_personalized_content(
    student_preferences={'interests': ['technology'], 'weak_areas': ['grammar']},
    difficulty=DifficultyLevel.INTERMEDIATE,
    content_type=ContentType.GRAMMAR
)
```

## 📊 Learning Models

### Student Model

Comprehensive student modeling with multiple dimensions:

- **Proficiency Level**: Beginner to Advanced
- **Learning Preferences**: Style, session length, focus areas
- **Performance Metrics**: Accuracy, speed, engagement, consistency
- **Knowledge State**: Mastery level per topic
- **Behavioral Patterns**: Response times, error types, learning velocity

### IRT Model

Item Response Theory implementation with 3-parameter logistic model:

```
P(correct) = c + (1-c) * 1/(1 + exp(-a*(θ - b)))
```

Where:
- θ (theta): Student ability
- a: Item discrimination
- b: Item difficulty  
- c: Guessing parameter

### BKT Model

Bayesian Knowledge Tracing with four parameters:

- **P(L₀)**: Prior probability of knowing
- **P(T)**: Probability of learning (transition)
- **P(G)**: Probability of correct guess
- **P(S)**: Probability of slip (know but incorrect)

## ⚙️ Configuration

### Default Configuration

```yaml
# config/default_config.yaml
agent:
  name: "LanguageTeacher"
  target_language: "english"

adaptive_learning:
  adaptation_strategy: "mixed"
  success_rate_target: 0.75
  mastery_threshold: 0.85

spaced_repetition:
  algorithm: "sm2_plus"
  min_ease_factor: 1.3
  max_ease_factor: 5.0

analytics:
  trend_window_days: 14
  min_data_points: 5

autogen:
  teacher_agent:
    model: "gpt-4"
    temperature: 0.7
```

### Custom Configuration

```python
config = {
    'target_language': 'spanish',
    'adaptive_learning': {
        'adaptation_strategy': 'difficulty_based',
        'success_rate_target': 0.8
    },
    'spaced_repetition': {
        'algorithm': 'anki',
        'graduation_interval': 3
    },
    'content_generation': {
        'focus_topics': ['business', 'travel']
    }
}

agent = LanguageTeacherAgent(config)
```

## 🤖 Telegram Bot Integration

### Command Interface

- `/start` - Begin learning session
- `/help` - Show help information
- `/end` - End current session
- `/progress` - View detailed progress
- `/status` - Check session status
- `/focus <areas>` - Start focused practice

### Conversation Flow

1. **Session Initiation**: User starts with `/start` or any message
2. **Activity Presentation**: AI presents personalized learning activity
3. **Response Processing**: User responds, AI analyzes and provides feedback
4. **Adaptive Progression**: AI selects next activity based on performance
5. **Session Completion**: Comprehensive summary and recommendations

### Example Conversation

```
User: /start
Bot: 🎓 Welcome to AI Language Learning! Ready to practice English?

🔤 **Word:** beautiful
📖 **Definition:** Pleasing to look at
💬 **Example:** The sunset is beautiful tonight.
💡 **Instructions:** Use this word in your own sentence.

User: The flowers in garden is beautiful.
Bot: ✅ Great use of the word "beautiful"! 

I noticed a small grammar point: "The flowers in garden are beautiful" would be correct because "flowers" is plural, so we use "are" instead of "is".

📚 **Grammar Practice: Subject-Verb Agreement**
Complete: The cats _____ in the yard.
**Options:**
1. plays  2. play  3. playing  4. played
```

## 📈 Performance Metrics

### Student Metrics
- **Accuracy Rate**: Percentage of correct responses
- **Learning Velocity**: Concepts mastered per hour
- **Retention Rate**: Long-term knowledge retention
- **Engagement Score**: Based on response patterns
- **Consistency Index**: Regularity of practice

### Agent Metrics
- **Response Time**: Average processing time
- **Success Rate**: Successful lesson completion
- **Adaptation Effectiveness**: Difficulty optimization accuracy
- **Content Quality**: Generated content appropriateness

## 🔧 Development and Testing

### Running Examples

```bash
# Run comprehensive examples
python -m agents.categories.education.language_teacher.example_usage

# Run specific component tests
python -c "
from agents.categories.education.language_teacher.ai.nlp_processor import NLPProcessor
processor = NLPProcessor()
analysis = processor.analyze_text('I am go to school')
print(analysis.errors)
"
```

### Testing Individual Components

```python
# Test adaptive learning
from agents.categories.education.language_teacher.ai.adaptive_learning import AdaptiveLearningEngine
engine = AdaptiveLearningEngine()
# ... test scenarios

# Test spaced repetition
from agents.categories.education.language_teacher.ai.spaced_repetition import SpacedRepetitionSystem
srs = SpacedRepetitionSystem()
# ... test scenarios

# Test learning analytics
from agents.categories.education.language_teacher.ai.learning_analytics import LearningAnalytics
analytics = LearningAnalytics()
# ... test scenarios
```

## 🎯 Use Cases

### Individual Learning
- Personalized vocabulary building
- Grammar practice with error correction
- Conversation skill development
- Reading comprehension improvement

### Educational Institutions
- Supplementary language learning tool
- Student progress tracking
- Adaptive assessment system
- Homework and practice assignments

### Corporate Training
- Professional English improvement
- Industry-specific vocabulary
- Business communication skills
- Progress reporting for HR

## 🔮 Future Enhancements

### Planned Features
- **Voice Recognition**: Pronunciation assessment
- **Multimodal Content**: Images, audio, video integration
- **Advanced Analytics**: Predictive modeling, learning path optimization
- **Collaborative Learning**: Peer interactions, group activities
- **Assessment Tools**: Standardized test preparation

### Integration Possibilities
- **LMS Integration**: Canvas, Blackboard, Moodle
- **Video Conferencing**: Zoom, Teams integration
- **Mobile Apps**: React Native, Flutter implementations
- **AR/VR**: Immersive language experiences

## 🤝 Contributing

### Development Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables
4. Run tests: `python -m pytest tests/`

### Code Structure

- Follow 1 file 1 class principle
- Maximum 400 lines per file
- Comprehensive error handling
- Extensive logging with loguru
- Type hints for all functions

### Adding New Components

1. Extend base classes in `ai/models/`
2. Implement error handling and fallbacks
3. Add configuration options
4. Include comprehensive tests
5. Update documentation

## 📜 License

This project is part of the Varga AI platform and follows the project's licensing terms.

## 🙏 Acknowledgments

- **Microsoft AutoGen**: Multi-agent framework
- **OpenAI**: Language model APIs
- **NLTK**: Natural language processing
- **NumPy/SciPy**: Scientific computing
- **Community**: Open source contributors

---

*Built with ❤️ for democratizing AI-powered education*