"""
Conversation Teacher - Handles natural dialogue practice and conversation flow.
Focuses on interactive speaking practice, vocabulary building, and error correction.
"""

import json
import random
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from agents.base.base_agent import BaseAgent, AgentConfig
from src.log_service import get_logger


class ConversationTopic(Enum):
    """Available conversation topics."""
    DAILY_LIFE = "daily_life"
    HOBBIES = "hobbies"
    TRAVEL = "travel"
    FOOD = "food"
    WORK = "work"
    FAMILY = "family"
    WEATHER = "weather"
    CULTURE = "culture"
    TECHNOLOGY = "technology"
    HEALTH = "health"


@dataclass
class ConversationContext:
    """Context for ongoing conversations."""
    user_id: int
    topic: Optional[ConversationTopic] = None
    turn_count: int = 0
    vocabulary_introduced: List[str] = None
    corrections_made: List[Dict] = None
    last_user_message: Optional[str] = None
    conversation_goal: Optional[str] = None
    
    def __post_init__(self):
        if self.vocabulary_introduced is None:
            self.vocabulary_introduced = []
        if self.corrections_made is None:
            self.corrections_made = []


class ConversationTeacher(BaseAgent):
    """
    Conversation Teacher persona for natural language practice.
    Engages users in realistic dialogues while providing gentle corrections and vocabulary building.
    """
    
    CONVERSATION_STARTERS = {
        ConversationTopic.DAILY_LIFE: [
            "How was your day today?",
            "What did you do this morning?",
            "Tell me about your typical weekday.",
            "What time do you usually wake up?"
        ],
        ConversationTopic.HOBBIES: [
            "What do you like to do in your free time?",
            "Do you have any interesting hobbies?",
            "What's your favorite way to relax?",
            "Have you learned any new skills recently?"
        ],
        ConversationTopic.TRAVEL: [
            "Have you traveled anywhere interesting lately?",
            "What's your dream travel destination?",
            "Do you prefer beach or mountain vacations?",
            "Tell me about your hometown."
        ],
        ConversationTopic.FOOD: [
            "What's your favorite type of cuisine?",
            "Can you cook anything special?",
            "What did you eat for breakfast today?",
            "Is there any food you don't like?"
        ]
    }
    
    LEVEL_ADJUSTMENTS = {
        "beginner": {
            "vocabulary_complexity": 1,
            "sentence_length": "short",
            "correction_frequency": "high",
            "explanation_detail": "detailed"
        },
        "elementary": {
            "vocabulary_complexity": 2,
            "sentence_length": "medium",
            "correction_frequency": "medium",
            "explanation_detail": "moderate"
        },
        "intermediate": {
            "vocabulary_complexity": 3,
            "sentence_length": "medium",
            "correction_frequency": "selective",
            "explanation_detail": "brief"
        },
        "advanced": {
            "vocabulary_complexity": 4,
            "sentence_length": "varied",
            "correction_frequency": "minimal",
            "explanation_detail": "contextual"
        }
    }
    
    def __init__(self):
        """Initialize the Conversation Teacher."""
        config = AgentConfig(
            name="conversation_teacher",
            description="Natural dialogue practice teacher for language learning",
            category="education",
            system_message=self._get_system_message(),
            temperature=0.8,
            max_tokens=1500
        )
        
        super().__init__(config)
        
        # Conversation management
        self.active_conversations: Dict[int, ConversationContext] = {}
        self.vocabulary_database = self._load_vocabulary_database()
        
    def _get_system_message(self) -> str:
        """Get the system message for conversation teacher."""
        return """You are an expert Language Conversation Teacher who specializes in natural dialogue practice.

Your teaching approach:
1. Engage in natural, flowing conversations on various topics
2. Adapt your language complexity to the student's level
3. Provide gentle corrections in a supportive way
4. Introduce new vocabulary naturally within context
5. Ask follow-up questions to keep conversations going
6. Give positive reinforcement and encouragement

Correction format: When correcting mistakes, use this format:
"Great point! Just a small correction: instead of '[incorrect]', you could say '[correct]'. [Brief explanation if needed]"

Teaching principles:
- Be patient and encouraging
- Focus on communication over perfect grammar
- Make corrections feel natural, not interrupting
- Celebrate progress and effort
- Keep conversations interesting and relevant
- Adapt to the student's interests and level

Remember: The goal is fluent communication, not perfection!"""
    
    def _load_vocabulary_database(self) -> Dict[str, Dict[str, List[str]]]:
        """Load vocabulary database organized by language and level."""
        # This would typically load from a database or file
        # For now, return a sample structure
        return {
            "english": {
                "beginner": ["hello", "good", "thank you", "please", "yes", "no"],
                "elementary": ["interesting", "beautiful", "difficult", "important", "different"],
                "intermediate": ["occasionally", "furthermore", "nevertheless", "consequently"],
                "advanced": ["sophisticated", "comprehensive", "intricate", "profound"]
            },
            "spanish": {
                "beginner": ["hola", "bueno", "gracias", "por favor", "sí", "no"],
                "elementary": ["interesante", "hermoso", "difícil", "importante", "diferente"],
                "intermediate": ["ocasionalmente", "además", "sin embargo", "por lo tanto"],
                "advanced": ["sofisticado", "comprensivo", "intrincado", "profundo"]
            }
        }
    
    async def setup(self) -> None:
        """Initialize conversation teacher."""
        self.logger.info("Conversation Teacher initialized")
    
    async def process_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process conversation message from user.
        
        Args:
            message: User's message
            context: Context including user_profile, language, level
            
        Returns:
            Teacher's response
        """
        try:
            if not context:
                return "I need context to have a proper conversation with you."
            
            user_profile = context.get("user_profile")
            if not user_profile:
                return "I need your user profile to personalize our conversation."
            
            user_id = user_profile.user_id
            language = context.get("language", "english")
            level = context.get("level", "beginner")
            
            # Get or create conversation context
            conv_context = self.get_conversation_context(user_id)
            conv_context.turn_count += 1
            conv_context.last_user_message = message
            
            # Analyze user message for errors and learning opportunities
            analysis = await self.analyze_user_message(message, language, level)
            
            # Generate response based on conversation flow
            response = await self.generate_conversation_response(
                message, conv_context, language, level, analysis
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in conversation teacher: {e}")
            return "I'm having trouble understanding. Could you try rephrasing that?"
    
    def get_conversation_context(self, user_id: int) -> ConversationContext:
        """Get or create conversation context for user."""
        if user_id not in self.active_conversations:
            self.active_conversations[user_id] = ConversationContext(user_id=user_id)
        return self.active_conversations[user_id]
    
    async def analyze_user_message(
        self, 
        message: str, 
        language: str, 
        level: str
    ) -> Dict[str, Any]:
        """
        Analyze user message for errors and learning opportunities.
        
        Returns:
            Dictionary with analysis results
        """
        # This would typically use NLP libraries or AI models
        # For now, return a basic analysis structure
        return {
            "grammar_errors": [],
            "vocabulary_level": level,
            "message_complexity": len(message.split()),
            "topics_mentioned": [],
            "needs_encouragement": len(message.split()) < 5,
            "correction_suggestions": []
        }
    
    async def generate_conversation_response(
        self,
        message: str,
        conv_context: ConversationContext,
        language: str,
        level: str,
        analysis: Dict[str, Any]
    ) -> str:
        """Generate contextual conversation response."""
        
        # Determine if this is the start of a new conversation
        if conv_context.turn_count == 1:
            return await self.start_new_conversation(conv_context, language, level)
        
        # Build response based on message content and context
        response_parts = []
        
        # Add acknowledgment and encouragement
        response_parts.append(self._generate_acknowledgment(message, analysis))
        
        # Add corrections if needed (based on level)
        correction = self._generate_correction(message, level, analysis)
        if correction:
            response_parts.append(correction)
        
        # Add vocabulary introduction if appropriate
        vocab_intro = self._introduce_vocabulary(message, language, level, conv_context)
        if vocab_intro:
            response_parts.append(vocab_intro)
        
        # Add follow-up question or response
        follow_up = self._generate_follow_up(message, conv_context, level)
        response_parts.append(follow_up)
        
        return "\n\n".join(response_parts)
    
    async def start_new_conversation(
        self, 
        conv_context: ConversationContext, 
        language: str, 
        level: str
    ) -> str:
        """Start a new conversation with appropriate greeting and topic."""
        
        # Choose a random topic or continue previous one
        if not conv_context.topic:
            conv_context.topic = random.choice(list(ConversationTopic))
        
        topic = conv_context.topic
        starter = random.choice(self.CONVERSATION_STARTERS[topic])
        
        greeting = self._get_level_appropriate_greeting(level)
        
        return f"""{greeting}

{starter}

💡 *Remember: Don't worry about making mistakes - that's how we learn! I'm here to help you practice naturally.*"""
    
    def _get_level_appropriate_greeting(self, level: str) -> str:
        """Get greeting appropriate for user level."""
        greetings = {
            "beginner": "Hello! Let's practice together! 😊",
            "elementary": "Hi there! Ready for some conversation practice?",
            "intermediate": "Hey! Great to see you again. Let's have a chat!",
            "advanced": "Hello! I'm excited to have an engaging conversation with you today."
        }
        return greetings.get(level, greetings["beginner"])
    
    def _generate_acknowledgment(self, message: str, analysis: Dict[str, Any]) -> str:
        """Generate acknowledgment of user's message."""
        
        acknowledgments = [
            "That's interesting!",
            "I see!",
            "Great point!",
            "Thanks for sharing that!",
            "That sounds nice!",
            "How wonderful!",
            "I understand!",
            "That's a good way to put it!"
        ]
        
        # Add encouragement if message is short or user seems hesitant
        if analysis.get("needs_encouragement"):
            encouragements = [
                "Don't worry about length - you're doing great!",
                "Perfect! Even short answers help you practice.",
                "Excellent! Keep going - you're improving!"
            ]
            return f"{random.choice(acknowledgments)} {random.choice(encouragements)}"
        
        return random.choice(acknowledgments)
    
    def _generate_correction(
        self, 
        message: str, 
        level: str, 
        analysis: Dict[str, Any]
    ) -> Optional[str]:
        """Generate gentle corrections if needed."""
        
        # Adjust correction frequency based on level
        level_settings = self.LEVEL_ADJUSTMENTS.get(level, self.LEVEL_ADJUSTMENTS["beginner"])
        
        if level_settings["correction_frequency"] == "minimal":
            return None
        
        # For demo purposes, occasionally provide sample corrections
        if "how are you" in message.lower() and random.random() < 0.3:
            return "💡 *Quick tip: You can also say 'How are things?' or 'How's it going?' for variety!*"
        
        return None
    
    def _introduce_vocabulary(
        self,
        message: str,
        language: str,
        level: str,
        conv_context: ConversationContext
    ) -> Optional[str]:
        """Introduce new vocabulary naturally."""
        
        # Get level-appropriate vocabulary
        vocab_list = self.vocabulary_database.get(language, {}).get(level, [])
        
        if not vocab_list:
            return None
        
        # Introduce vocabulary occasionally (every 3-4 turns)
        if conv_context.turn_count % 4 == 0 and random.random() < 0.7:
            new_word = random.choice(vocab_list)
            
            # Only introduce if not already introduced
            if new_word not in conv_context.vocabulary_introduced:
                conv_context.vocabulary_introduced.append(new_word)
                
                return f"📚 *New word: '{new_word}' - this means [definition]. Try using it in your next sentence!*"
        
        return None
    
    def _generate_follow_up(
        self, 
        message: str, 
        conv_context: ConversationContext, 
        level: str
    ) -> str:
        """Generate follow-up question or response to keep conversation flowing."""
        
        # Level-appropriate follow-ups
        if level in ["beginner", "elementary"]:
            follow_ups = [
                "What about you? Tell me more!",
                "That's nice! Can you describe it?",
                "Interesting! How do you feel about that?",
                "Good! What else would you like to share?"
            ]
        else:
            follow_ups = [
                "That's fascinating! Could you elaborate on that?",
                "I'd love to hear more details about your experience.",
                "What's your perspective on this topic?",
                "How does that compare to other experiences you've had?"
            ]
        
        # Try to ask related questions based on keywords
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["work", "job", "office"]):
            return "What do you enjoy most about your work?"
        elif any(word in message_lower for word in ["travel", "trip", "vacation"]):
            return "Where would you like to travel next?"
        elif any(word in message_lower for word in ["food", "eat", "restaurant"]):
            return "Do you like to cook, or do you prefer eating out?"
        elif any(word in message_lower for word in ["family", "friend", "people"]):
            return "Tell me more about the people important to you."
        
        return random.choice(follow_ups)
    
    def get_conversation_stats(self, user_id: int) -> Dict[str, Any]:
        """Get statistics for user's conversation practice."""
        conv_context = self.active_conversations.get(user_id)
        
        if not conv_context:
            return {"total_turns": 0, "vocabulary_learned": 0, "corrections_received": 0}
        
        return {
            "total_turns": conv_context.turn_count,
            "vocabulary_learned": len(conv_context.vocabulary_introduced),
            "corrections_received": len(conv_context.corrections_made),
            "current_topic": conv_context.topic.value if conv_context.topic else None
        }
    
    async def cleanup(self) -> None:
        """Clean up conversation teacher resources."""
        self.active_conversations.clear()
        self.logger.info("Conversation Teacher cleaned up")