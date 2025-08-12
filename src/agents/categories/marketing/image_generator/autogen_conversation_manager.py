"""
Advanced AutoGen Conversation Manager for Image Generation Workflows.
Demonstrates sophisticated conversation patterns, message routing, state management,
and multi-agent coordination using AutoGen's conversation framework.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Callable, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid

from autogen import (
    ConversableAgent,
    Agent,
    GroupChat,
    GroupChatManager,
    UserProxyAgent,
    AssistantAgent
)
from autogen.agentchat.contrib.capabilities.text_compressors import LLMLinguaTextCompressor
from autogen.agentchat.contrib.capabilities.context_handling import TransformChatHistory
from loguru import logger

from src.log_service import get_logger


class ConversationState(Enum):
    """States of conversation flow."""
    INITIATED = "initiated"
    CONCEPT_DEVELOPMENT = "concept_development"
    COLLABORATIVE_REVIEW = "collaborative_review"
    ITERATIVE_REFINEMENT = "iterative_refinement"
    CONSENSUS_BUILDING = "consensus_building"
    DECISION_MAKING = "decision_making"
    EXECUTION = "execution"
    COMPLETED = "completed"
    PAUSED = "paused"
    FAILED = "failed"


class MessageType(Enum):
    """Types of messages in conversations."""
    REQUEST = "request"
    RESPONSE = "response"
    QUESTION = "question"
    SUGGESTION = "suggestion"
    APPROVAL = "approval"
    REJECTION = "rejection"
    REFINEMENT = "refinement"
    CONSENSUS = "consensus"
    DECISION = "decision"
    STATUS_UPDATE = "status_update"


@dataclass
class ConversationMessage:
    """Enhanced message structure for conversation tracking."""
    id: str
    sender: str
    recipient: Optional[str]
    content: str
    message_type: MessageType
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_message_id: Optional[str] = None
    thread_id: Optional[str] = None
    priority: int = 1  # 1-5, where 5 is highest priority


@dataclass
class ConversationThread:
    """Represents a conversation thread."""
    id: str
    title: str
    participants: List[str]
    messages: List[ConversationMessage] = field(default_factory=list)
    state: ConversationState = ConversationState.INITIATED
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    consensus_items: List[Dict[str, Any]] = field(default_factory=list)
    decisions: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AgentCapabilityProfile:
    """Profile of an agent's capabilities and preferences."""
    agent_name: str
    specialties: List[str]
    conversation_style: str  # "collaborative", "authoritative", "supportive", "analytical"
    decision_weight: float  # 0.0-1.0, weight in consensus decisions
    response_patterns: Dict[str, str] = field(default_factory=dict)
    interaction_preferences: Dict[str, Any] = field(default_factory=dict)


class AutoGenConversationManager:
    """
    Advanced conversation manager that demonstrates sophisticated AutoGen patterns.
    
    Features:
    - Intelligent message routing and conversation flow
    - Dynamic speaker selection based on context and expertise
    - Conversation state management and transitions
    - Consensus building and decision making processes
    - Context compression and memory management
    - Multi-threaded conversation support
    - Conversation analytics and insights
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the conversation manager."""
        self.config = config
        self.logger = get_logger("autogen_conversation_manager")
        
        # Conversation management
        self.active_threads: Dict[str, ConversationThread] = {}
        self.agent_profiles: Dict[str, AgentCapabilityProfile] = {}
        self.conversation_templates: Dict[str, Dict[str, Any]] = {}
        
        # AutoGen components
        self.group_chats: Dict[str, GroupChat] = {}
        self.group_managers: Dict[str, GroupChatManager] = {}
        self.agents: Dict[str, ConversableAgent] = {}
        
        # Conversation capabilities
        self.text_compressor: Optional[LLMLinguaTextCompressor] = None
        self.context_handler: Optional[TransformChatHistory] = None
        
        # Analytics
        self.conversation_metrics: Dict[str, Any] = {
            "total_conversations": 0,
            "successful_completions": 0,
            "average_duration": 0.0,
            "message_patterns": {},
            "agent_participation": {},
            "consensus_success_rate": 0.0
        }
        
        # Initialize components
        self._initialize_conversation_templates()
    
    async def setup(self) -> None:
        """Set up the conversation manager."""
        try:
            # Initialize text compression capability
            self.text_compressor = LLMLinguaTextCompressor()
            
            # Initialize context handling capability
            self.context_handler = TransformChatHistory(
                transforms=[
                    # Add conversation-specific transforms
                    self._transform_for_image_generation,
                    self._compress_technical_details
                ]
            )
            
            # Create agent profiles
            self._create_agent_capability_profiles()
            
            self.logger.info("AutoGen Conversation Manager setup completed")
            
        except Exception as e:
            self.logger.error(f"Conversation manager setup failed: {e}")
            raise
    
    def _initialize_conversation_templates(self) -> None:
        """Initialize conversation flow templates."""
        
        self.conversation_templates = {
            "image_concept_development": {
                "description": "Collaborative image concept development",
                "flow": [
                    {"state": "initiated", "next_states": ["concept_development"]},
                    {"state": "concept_development", "next_states": ["collaborative_review", "iterative_refinement"]},
                    {"state": "collaborative_review", "next_states": ["consensus_building", "iterative_refinement"]},
                    {"state": "iterative_refinement", "next_states": ["collaborative_review", "consensus_building"]},
                    {"state": "consensus_building", "next_states": ["decision_making", "iterative_refinement"]},
                    {"state": "decision_making", "next_states": ["execution", "iterative_refinement"]},
                    {"state": "execution", "next_states": ["completed"]},
                    {"state": "completed", "next_states": []}
                ],
                "required_roles": ["creative_director", "prompt_engineer", "qa_reviewer"],
                "optional_roles": ["brand_officer", "campaign_strategist"]
            },
            
            "collaborative_refinement": {
                "description": "Multi-round collaborative refinement process", 
                "flow": [
                    {"state": "initiated", "next_states": ["collaborative_review"]},
                    {"state": "collaborative_review", "next_states": ["iterative_refinement", "consensus_building"]},
                    {"state": "iterative_refinement", "next_states": ["collaborative_review", "consensus_building"]},
                    {"state": "consensus_building", "next_states": ["decision_making"]},
                    {"state": "decision_making", "next_states": ["execution", "iterative_refinement"]},
                    {"state": "execution", "next_states": ["completed"]},
                    {"state": "completed", "next_states": []}
                ],
                "required_roles": ["prompt_engineer", "qa_reviewer"],
                "optional_roles": ["creative_director", "brand_officer"]
            },
            
            "consensus_decision": {
                "description": "Consensus-based decision making process",
                "flow": [
                    {"state": "initiated", "next_states": ["collaborative_review"]},
                    {"state": "collaborative_review", "next_states": ["consensus_building"]},
                    {"state": "consensus_building", "next_states": ["decision_making", "collaborative_review"]},
                    {"state": "decision_making", "next_states": ["execution"]},
                    {"state": "execution", "next_states": ["completed"]},
                    {"state": "completed", "next_states": []}
                ],
                "required_roles": ["creative_director", "qa_reviewer", "brand_officer"],
                "consensus_threshold": 0.75  # 75% agreement required
            }
        }
    
    def _create_agent_capability_profiles(self) -> None:
        """Create detailed capability profiles for agents."""
        
        self.agent_profiles = {
            "creative_director": AgentCapabilityProfile(
                agent_name="creative_director",
                specialties=["creative_vision", "brand_alignment", "strategic_direction", "concept_evaluation"],
                conversation_style="authoritative",
                decision_weight=0.3,
                response_patterns={
                    "concept_evaluation": "I'll evaluate this concept for creative merit and brand alignment...",
                    "strategic_guidance": "From a strategic perspective, we should consider...",
                    "final_decision": "Based on our discussion, my recommendation is..."
                },
                interaction_preferences={
                    "prefers_structured_discussion": True,
                    "leads_decision_making": True,
                    "provides_final_approval": True
                }
            ),
            
            "prompt_engineer": AgentCapabilityProfile(
                agent_name="prompt_engineer",
                specialties=["prompt_optimization", "technical_enhancement", "dall_e_expertise", "style_guidance"],
                conversation_style="analytical",
                decision_weight=0.25,
                response_patterns={
                    "prompt_analysis": "Looking at this prompt, I can enhance it with...",
                    "technical_feedback": "From a technical perspective, we should modify...",
                    "optimization_suggestion": "To improve DALL-E 3 results, let's add..."
                },
                interaction_preferences={
                    "detail_oriented": True,
                    "technical_focus": True,
                    "iterative_approach": True
                }
            ),
            
            "qa_reviewer": AgentCapabilityProfile(
                agent_name="qa_reviewer",
                specialties=["quality_assessment", "improvement_feedback", "standard_compliance", "final_review"],
                conversation_style="collaborative",
                decision_weight=0.25,
                response_patterns={
                    "quality_assessment": "Reviewing the quality, I notice...",
                    "improvement_suggestion": "To enhance quality, I suggest...",
                    "compliance_check": "Checking against our standards..."
                },
                interaction_preferences={
                    "thorough_review": True,
                    "constructive_feedback": True,
                    "collaborative_improvement": True
                }
            ),
            
            "brand_officer": AgentCapabilityProfile(
                agent_name="brand_officer",
                specialties=["brand_compliance", "guideline_enforcement", "consistency_check", "brand_protection"],
                conversation_style="supportive",
                decision_weight=0.2,
                response_patterns={
                    "brand_review": "From a brand perspective, this aligns/doesn't align with...",
                    "compliance_feedback": "To ensure brand compliance, we need to...",
                    "guideline_reference": "According to our brand guidelines..."
                },
                interaction_preferences={
                    "guideline_focused": True,
                    "consistency_emphasis": True,
                    "protective_stance": True
                }
            )
        }
    
    async def start_conversation(
        self,
        template_type: str,
        initial_message: str,
        participants: List[str],
        context: Optional[Dict[str, Any]] = None,
        priority: int = 1
    ) -> str:
        """
        Start a new conversation with specified participants.
        
        Args:
            template_type: Type of conversation template to use
            initial_message: Initial message to start conversation
            participants: List of agent names to include
            context: Additional context for the conversation
            priority: Priority level (1-5)
            
        Returns:
            Conversation thread ID
        """
        try:
            thread_id = f"conv_{template_type}_{uuid.uuid4().hex[:8]}"
            context = context or {}
            
            # Validate template
            if template_type not in self.conversation_templates:
                raise ValueError(f"Unknown conversation template: {template_type}")
            
            template = self.conversation_templates[template_type]
            
            # Validate participants
            missing_required = set(template.get("required_roles", [])) - set(participants)
            if missing_required:
                raise ValueError(f"Missing required participants: {missing_required}")
            
            # Create conversation thread
            thread = ConversationThread(
                id=thread_id,
                title=f"{template['description']} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                participants=participants,
                context={
                    "template_type": template_type,
                    "template": template,
                    "user_context": context,
                    "priority": priority
                }
            )
            
            # Add initial message
            initial_msg = ConversationMessage(
                id=f"msg_{uuid.uuid4().hex[:8]}",
                sender="system",
                recipient=None,
                content=initial_message,
                message_type=MessageType.REQUEST,
                context=context,
                priority=priority
            )
            
            thread.messages.append(initial_msg)
            
            # Store thread
            self.active_threads[thread_id] = thread
            
            # Create group chat for this conversation
            group_chat = await self._create_group_chat_for_thread(thread)
            group_manager = await self._create_group_manager_for_thread(thread, group_chat)
            
            self.logger.info(f"Started conversation {thread_id} with {len(participants)} participants")
            return thread_id
            
        except Exception as e:
            self.logger.error(f"Failed to start conversation: {e}")
            raise
    
    async def _create_group_chat_for_thread(self, thread: ConversationThread) -> GroupChat:
        """Create a specialized group chat for the conversation thread."""
        
        # Get or create agents for participants
        agents = []
        for participant in thread.participants:
            agent = await self._get_or_create_agent(participant, thread)
            agents.append(agent)
        
        # Create custom speaker selection function
        def custom_speaker_selection(
            last_speaker: Agent, 
            groupchat: GroupChat
        ) -> Union[Agent, str, None]:
            """Intelligent speaker selection based on conversation state and context."""
            return self._select_next_speaker(last_speaker, groupchat, thread)
        
        # Create group chat with advanced configuration
        group_chat = GroupChat(
            agents=agents,
            messages=[],
            max_round=30,  # Allow longer conversations for complex workflows
            speaker_selection_method=custom_speaker_selection,
            allow_repeat_speaker=True,  # Allow same agent to speak multiple times if needed
            send_introductions=True
        )
        
        # Add conversation state tracking
        group_chat.conversation_state = thread.state
        group_chat.thread_id = thread.id
        
        self.group_chats[thread.id] = group_chat
        return group_chat
    
    async def _create_group_manager_for_thread(
        self, 
        thread: ConversationThread, 
        group_chat: GroupChat
    ) -> GroupChatManager:
        """Create a specialized group manager for the thread."""
        
        template = thread.context.get("template", {})
        
        system_message = f"""You are managing a {template.get('description', 'conversation')} between specialized agents.
        
        Thread: {thread.title}
        Participants: {', '.join(thread.participants)}
        Current State: {thread.state.value}
        
        Your responsibilities:
        - Guide the conversation flow according to the template
        - Ensure all required participants contribute meaningfully
        - Facilitate consensus building when needed
        - Manage conversation state transitions
        - Summarize key decisions and outcomes
        - Keep discussions focused and productive
        
        Conversation Context:
        {json.dumps(thread.context.get('user_context', {}), indent=2)}
        
        Maintain professional, collaborative communication while ensuring efficient progress toward the conversation goals."""
        
        manager = GroupChatManager(
            groupchat=group_chat,
            llm_config=self._get_llm_config(),
            system_message=system_message,
            is_termination_msg=self._create_termination_checker(thread)
        )
        
        # Add conversation capabilities
        if self.text_compressor:
            manager.register_capability(self.text_compressor)
        
        if self.context_handler:
            manager.register_capability(self.context_handler)
        
        # Add custom reply functions
        manager.register_reply(
            [Agent, ConversableAgent],
            self._enhanced_group_manager_reply,
            position=0
        )
        
        self.group_managers[thread.id] = manager
        return manager
    
    def _select_next_speaker(
        self, 
        last_speaker: Agent, 
        groupchat: GroupChat, 
        thread: ConversationThread
    ) -> Union[Agent, str, None]:
        """Intelligent speaker selection based on conversation context."""
        
        try:
            # Get conversation history
            recent_messages = thread.messages[-5:]  # Last 5 messages
            
            # Determine conversation needs
            conversation_needs = self._analyze_conversation_needs(recent_messages, thread)
            
            # Find best suited agent
            best_agent = self._find_best_suited_agent(
                conversation_needs, 
                thread.participants,
                last_speaker.name if last_speaker else None
            )
            
            if best_agent:
                # Find the actual agent object
                for agent in groupchat.agents:
                    if agent.name == best_agent:
                        return agent
            
            # Fallback to AutoGen's default selection
            return None
            
        except Exception as e:
            self.logger.error(f"Speaker selection error: {e}")
            return None
    
    def _analyze_conversation_needs(
        self, 
        recent_messages: List[ConversationMessage], 
        thread: ConversationThread
    ) -> Dict[str, Any]:
        """Analyze what the conversation currently needs."""
        
        needs = {
            "creative_input": False,
            "technical_expertise": False,
            "quality_review": False,
            "brand_compliance": False,
            "decision_making": False,
            "consensus_building": False
        }
        
        # Analyze recent messages for patterns
        for msg in recent_messages[-3:]:  # Focus on most recent
            content_lower = msg.content.lower()
            
            # Check for creative needs
            if any(word in content_lower for word in ["concept", "creative", "idea", "vision"]):
                needs["creative_input"] = True
            
            # Check for technical needs
            if any(word in content_lower for word in ["prompt", "technical", "dall-e", "generation"]):
                needs["technical_expertise"] = True
            
            # Check for quality concerns
            if any(word in content_lower for word in ["quality", "review", "assess", "improve"]):
                needs["quality_review"] = True
            
            # Check for brand concerns
            if any(word in content_lower for word in ["brand", "guideline", "compliance", "consistent"]):
                needs["brand_compliance"] = True
            
            # Check for decision needs
            if any(word in content_lower for word in ["decide", "choose", "approve", "final"]):
                needs["decision_making"] = True
        
        # Check conversation state for consensus needs
        if thread.state in [ConversationState.CONSENSUS_BUILDING, ConversationState.DECISION_MAKING]:
            needs["consensus_building"] = True
        
        return needs
    
    def _find_best_suited_agent(
        self, 
        conversation_needs: Dict[str, bool], 
        participants: List[str],
        last_speaker: Optional[str] = None
    ) -> Optional[str]:
        """Find the best suited agent for current conversation needs."""
        
        # Calculate suitability scores
        agent_scores = {}
        
        for participant in participants:
            if participant == last_speaker:
                continue  # Avoid immediate repeat unless necessary
            
            profile = self.agent_profiles.get(participant)
            if not profile:
                continue
            
            score = 0
            
            # Score based on specialties matching needs
            if conversation_needs["creative_input"] and "creative_vision" in profile.specialties:
                score += 3
            if conversation_needs["technical_expertise"] and "technical_enhancement" in profile.specialties:
                score += 3
            if conversation_needs["quality_review"] and "quality_assessment" in profile.specialties:
                score += 3
            if conversation_needs["brand_compliance"] and "brand_compliance" in profile.specialties:
                score += 3
            if conversation_needs["decision_making"] and profile.interaction_preferences.get("leads_decision_making"):
                score += 2
            if conversation_needs["consensus_building"] and profile.conversation_style == "collaborative":
                score += 2
            
            agent_scores[participant] = score
        
        # Return highest scoring agent
        if agent_scores:
            return max(agent_scores, key=agent_scores.get)
        
        return None
    
    async def _get_or_create_agent(
        self, 
        agent_name: str, 
        thread: ConversationThread
    ) -> ConversableAgent:
        """Get existing agent or create new one for the conversation."""
        
        if agent_name in self.agents:
            return self.agents[agent_name]
        
        # Get agent profile
        profile = self.agent_profiles.get(agent_name)
        if not profile:
            # Create generic agent
            agent = AssistantAgent(
                name=agent_name,
                system_message=f"You are {agent_name} participating in image generation workflow discussions.",
                llm_config=self._get_llm_config(),
                human_input_mode="NEVER"
            )
        else:
            # Create specialized agent based on profile
            system_message = f"""You are {profile.agent_name} with expertise in {', '.join(profile.specialties)}.
            
            Your conversation style is {profile.conversation_style}.
            Your specialties include: {', '.join(profile.specialties)}
            
            In conversations, you should:
            - Focus on your areas of expertise
            - Provide {profile.conversation_style} input
            - Collaborate effectively with other specialists
            - Contribute meaningfully to discussions
            
            Response patterns:
            {json.dumps(profile.response_patterns, indent=2)}
            
            Always maintain professional communication while leveraging your specialized knowledge."""
            
            agent = AssistantAgent(
                name=agent_name,
                system_message=system_message,
                llm_config=self._get_llm_config(),
                human_input_mode="NEVER"
            )
        
        # Add conversation-specific capabilities
        agent.register_reply(
            [Agent, ConversableAgent],
            self._agent_enhanced_reply,
            position=0
        )
        
        self.agents[agent_name] = agent
        return agent
    
    def _get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration for agents."""
        from src.config.config_manager import get_config
        
        config_manager = get_config()
        return config_manager.get_llm_config()
    
    def _create_termination_checker(self, thread: ConversationThread) -> Callable:
        """Create termination checker for the conversation."""
        
        def is_termination_msg(msg) -> bool:
            """Check if message should terminate conversation."""
            if not isinstance(msg, dict):
                return False
            
            content = msg.get("content", "").lower()
            
            # Check for explicit termination phrases
            termination_phrases = [
                "conversation complete",
                "workflow finished", 
                "final decision made",
                "consensus reached and approved",
                "image generation completed"
            ]
            
            if any(phrase in content for phrase in termination_phrases):
                return True
            
            # Check conversation state
            if thread.state == ConversationState.COMPLETED:
                return True
            
            # Check for natural conclusion indicators
            conclusion_indicators = [
                "thank you all",
                "great work team",
                "perfect, let's proceed",
                "approved for implementation"
            ]
            
            return any(indicator in content for indicator in conclusion_indicators)
        
        return is_termination_msg
    
    async def _enhanced_group_manager_reply(
        self,
        recipient: Agent,
        messages: Optional[List[Dict]] = None,
        sender: Optional[Agent] = None,
        config: Optional[Any] = None
    ) -> Union[str, Dict, None]:
        """Enhanced group manager reply with conversation state management."""
        
        try:
            if not messages:
                return None
            
            # Find the thread for this conversation
            thread = None
            for t in self.active_threads.values():
                if sender and sender.name in t.participants:
                    thread = t
                    break
            
            if not thread:
                return None  # Let default handler manage
            
            last_message = messages[-1]["content"] if messages else ""
            
            # Update conversation state based on content
            new_state = self._determine_state_transition(last_message, thread)
            if new_state and new_state != thread.state:
                await self._transition_conversation_state(thread, new_state)
            
            # Check for consensus building needs
            if self._needs_consensus_building(last_message, thread):
                return await self._facilitate_consensus(thread, messages)
            
            # Check for decision making needs
            if self._needs_decision_facilitation(last_message, thread):
                return await self._facilitate_decision(thread, messages)
            
            # Let default processing handle
            return None
            
        except Exception as e:
            self.logger.error(f"Enhanced group manager reply error: {e}")
            return None
    
    async def _agent_enhanced_reply(
        self,
        recipient: Agent,
        messages: Optional[List[Dict]] = None,
        sender: Optional[Agent] = None,
        config: Optional[Any] = None
    ) -> Union[str, Dict, None]:
        """Enhanced agent reply with profile-based responses."""
        
        try:
            if not messages or not recipient:
                return None
            
            # Get agent profile
            profile = self.agent_profiles.get(recipient.name)
            if not profile:
                return None  # Use default processing
            
            last_message = messages[-1]["content"] if messages else ""
            
            # Determine response type needed
            response_type = self._determine_response_type(last_message, profile)
            
            # Use appropriate response pattern if available
            if response_type in profile.response_patterns:
                response_starter = profile.response_patterns[response_type]
                
                # Enhance the default response with pattern
                enhanced_prompt = f"{response_starter}\n\nContext: {last_message}"
                
                # Generate response using the pattern
                enhanced_messages = messages[:-1] + [{"role": "user", "content": enhanced_prompt}]
                
                # Let the agent generate response with enhanced prompt
                return await recipient.a_generate_reply(enhanced_messages, sender)
            
            return None  # Use default processing
            
        except Exception as e:
            self.logger.error(f"Enhanced agent reply error: {e}")
            return None
    
    def _determine_response_type(self, message: str, profile: AgentCapabilityProfile) -> str:
        """Determine what type of response is needed based on message content."""
        
        message_lower = message.lower()
        
        # Map message content to response types
        if any(word in message_lower for word in ["concept", "idea", "creative"]):
            if "concept_evaluation" in profile.response_patterns:
                return "concept_evaluation"
        
        if any(word in message_lower for word in ["prompt", "enhance", "optimize"]):
            if "prompt_analysis" in profile.response_patterns:
                return "prompt_analysis"
        
        if any(word in message_lower for word in ["quality", "review", "assess"]):
            if "quality_assessment" in profile.response_patterns:
                return "quality_assessment"
        
        if any(word in message_lower for word in ["brand", "guideline", "compliance"]):
            if "brand_review" in profile.response_patterns:
                return "brand_review"
        
        if any(word in message_lower for word in ["strategy", "plan", "campaign"]):
            if "strategic_guidance" in profile.response_patterns:
                return "strategic_guidance"
        
        # Default to first available pattern
        return list(profile.response_patterns.keys())[0] if profile.response_patterns else ""
    
    def _determine_state_transition(
        self, 
        message: str, 
        thread: ConversationThread
    ) -> Optional[ConversationState]:
        """Determine if conversation state should transition."""
        
        message_lower = message.lower()
        current_state = thread.state
        
        # Define transition triggers
        if current_state == ConversationState.INITIATED:
            if any(word in message_lower for word in ["concept", "develop", "create"]):
                return ConversationState.CONCEPT_DEVELOPMENT
        
        elif current_state == ConversationState.CONCEPT_DEVELOPMENT:
            if any(word in message_lower for word in ["review", "feedback", "thoughts"]):
                return ConversationState.COLLABORATIVE_REVIEW
            if any(word in message_lower for word in ["refine", "improve", "iterate"]):
                return ConversationState.ITERATIVE_REFINEMENT
        
        elif current_state == ConversationState.COLLABORATIVE_REVIEW:
            if any(word in message_lower for word in ["consensus", "agree", "alignment"]):
                return ConversationState.CONSENSUS_BUILDING
            if any(word in message_lower for word in ["refine", "change", "modify"]):
                return ConversationState.ITERATIVE_REFINEMENT
        
        elif current_state == ConversationState.CONSENSUS_BUILDING:
            if any(word in message_lower for word in ["decide", "decision", "choose"]):
                return ConversationState.DECISION_MAKING
        
        elif current_state == ConversationState.DECISION_MAKING:
            if any(word in message_lower for word in ["execute", "implement", "proceed"]):
                return ConversationState.EXECUTION
        
        elif current_state == ConversationState.EXECUTION:
            if any(word in message_lower for word in ["complete", "finished", "done"]):
                return ConversationState.COMPLETED
        
        return None
    
    async def _transition_conversation_state(
        self, 
        thread: ConversationThread, 
        new_state: ConversationState
    ) -> None:
        """Transition conversation to new state."""
        
        old_state = thread.state
        thread.state = new_state
        thread.last_activity = datetime.now()
        
        # Log state transition
        self.logger.info(f"Thread {thread.id} transitioned from {old_state.value} to {new_state.value}")
        
        # Add state transition message
        transition_msg = ConversationMessage(
            id=f"msg_{uuid.uuid4().hex[:8]}",
            sender="system",
            recipient=None,
            content=f"Conversation state transitioned to: {new_state.value}",
            message_type=MessageType.STATUS_UPDATE,
            context={"state_transition": {"from": old_state.value, "to": new_state.value}}
        )
        
        thread.messages.append(transition_msg)
    
    def _needs_consensus_building(self, message: str, thread: ConversationThread) -> bool:
        """Check if conversation needs consensus building facilitation."""
        
        message_lower = message.lower()
        
        # Check for disagreement indicators
        disagreement_indicators = [
            "disagree", "however", "but i think", "on the other hand", 
            "different perspective", "alternative approach"
        ]
        
        has_disagreement = any(indicator in message_lower for indicator in disagreement_indicators)
        
        # Check if we're in a state that benefits from consensus
        consensus_states = [ConversationState.COLLABORATIVE_REVIEW, ConversationState.CONSENSUS_BUILDING]
        
        return has_disagreement and thread.state in consensus_states
    
    def _needs_decision_facilitation(self, message: str, thread: ConversationThread) -> bool:
        """Check if conversation needs decision facilitation."""
        
        message_lower = message.lower()
        
        decision_indicators = [
            "what should we decide", "need to choose", "make a decision",
            "final call", "approve", "proceed with"
        ]
        
        has_decision_need = any(indicator in message_lower for indicator in decision_indicators)
        
        decision_states = [ConversationState.CONSENSUS_BUILDING, ConversationState.DECISION_MAKING]
        
        return has_decision_need and thread.state in decision_states
    
    async def _facilitate_consensus(
        self, 
        thread: ConversationThread, 
        messages: List[Dict]
    ) -> str:
        """Facilitate consensus building in the conversation."""
        
        consensus_facilitation = f"""
        Let me help facilitate consensus building for our discussion.
        
        Current participants: {', '.join(thread.participants)}
        
        I notice we have different perspectives. Let's work toward alignment:
        
        1. **Summarize positions**: Each participant, please briefly state your position
        2. **Find common ground**: What aspects do we all agree on?
        3. **Address differences**: Let's discuss the specific points of disagreement
        4. **Build consensus**: How can we find a solution that addresses everyone's concerns?
        
        Please share your key points for consensus building.
        """
        
        return consensus_facilitation
    
    async def _facilitate_decision(
        self, 
        thread: ConversationThread, 
        messages: List[Dict]
    ) -> str:
        """Facilitate decision making in the conversation."""
        
        decision_facilitation = f"""
        It's time to make a decision based on our discussion.
        
        **Decision Point**: {thread.context.get('user_context', {}).get('original_request', 'Image generation approach')}
        
        **Options discussed**: Based on our conversation, here are the key options:
        - [The participants should summarize the options discussed]
        
        **Decision Process**:
        1. Each participant: State your preferred option and reasoning
        2. Creative Director: Provide final strategic recommendation
        3. Group: Confirm consensus or majority decision
        4. Move to execution phase
        
        Let's proceed with decision making. Each participant, please state your preference.
        """
        
        return decision_facilitation
    
    async def execute_conversation(
        self, 
        thread_id: str, 
        max_rounds: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute a conversation thread to completion."""
        
        try:
            if thread_id not in self.active_threads:
                raise ValueError(f"Thread not found: {thread_id}")
            
            thread = self.active_threads[thread_id]
            group_chat = self.group_chats[thread_id]
            group_manager = self.group_managers[thread_id]
            
            # Set max rounds if specified
            if max_rounds:
                group_chat.max_round = max_rounds
            
            # Execute conversation
            initial_message = thread.messages[0].content if thread.messages else "Let's begin our discussion."
            
            # Start the group conversation
            result = await group_manager.a_initiate_chat(
                message=initial_message,
                clear_history=False
            )
            
            # Process conversation results
            conversation_result = await self._process_conversation_results(thread, result)
            
            # Update metrics
            self._update_conversation_metrics(thread)
            
            return conversation_result
            
        except Exception as e:
            self.logger.error(f"Conversation execution failed for {thread_id}: {e}")
            return {
                "success": False,
                "thread_id": thread_id,
                "error": str(e)
            }
    
    async def _process_conversation_results(
        self, 
        thread: ConversationThread, 
        autogen_result: Any
    ) -> Dict[str, Any]:
        """Process and analyze conversation results."""
        
        # Extract final messages and decisions
        final_messages = getattr(autogen_result, 'chat_history', [])
        
        # Analyze conversation outcomes
        outcomes = self._analyze_conversation_outcomes(thread, final_messages)
        
        # Calculate conversation metrics
        duration = (datetime.now() - thread.created_at).total_seconds()
        message_count = len(thread.messages)
        participant_contributions = self._analyze_participant_contributions(thread)
        
        return {
            "success": True,
            "thread_id": thread.id,
            "final_state": thread.state.value,
            "duration_seconds": duration,
            "message_count": message_count,
            "participant_contributions": participant_contributions,
            "outcomes": outcomes,
            "decisions": thread.decisions,
            "consensus_items": thread.consensus_items,
            "conversation_summary": self._generate_conversation_summary(thread)
        }
    
    def _analyze_conversation_outcomes(
        self, 
        thread: ConversationThread, 
        final_messages: List[Dict]
    ) -> Dict[str, Any]:
        """Analyze conversation outcomes and decisions."""
        
        outcomes = {
            "decisions_made": [],
            "consensus_achieved": [],
            "action_items": [],
            "unresolved_issues": []
        }
        
        # Analyze final messages for outcomes
        for msg in final_messages[-10:]:  # Focus on recent messages
            content = msg.get('content', '').lower()
            
            if any(word in content for word in ['decided', 'decision', 'choose']):
                outcomes["decisions_made"].append(msg.get('content', ''))
            
            if any(word in content for word in ['consensus', 'agree', 'alignment']):
                outcomes["consensus_achieved"].append(msg.get('content', ''))
            
            if any(word in content for word in ['action', 'next step', 'implement']):
                outcomes["action_items"].append(msg.get('content', ''))
        
        return outcomes
    
    def _analyze_participant_contributions(self, thread: ConversationThread) -> Dict[str, Any]:
        """Analyze how much each participant contributed."""
        
        contributions = {}
        
        for participant in thread.participants:
            participant_messages = [
                msg for msg in thread.messages 
                if msg.sender == participant
            ]
            
            contributions[participant] = {
                "message_count": len(participant_messages),
                "word_count": sum(len(msg.content.split()) for msg in participant_messages),
                "message_types": [msg.message_type.value for msg in participant_messages]
            }
        
        return contributions
    
    def _generate_conversation_summary(self, thread: ConversationThread) -> str:
        """Generate a summary of the conversation."""
        
        summary_parts = [
            f"Conversation: {thread.title}",
            f"Duration: {(thread.last_activity - thread.created_at).total_seconds():.1f} seconds",
            f"Participants: {', '.join(thread.participants)}",
            f"Final State: {thread.state.value}",
            f"Messages Exchanged: {len(thread.messages)}",
        ]
        
        if thread.decisions:
            summary_parts.append(f"Decisions Made: {len(thread.decisions)}")
        
        if thread.consensus_items:
            summary_parts.append(f"Consensus Items: {len(thread.consensus_items)}")
        
        return "\n".join(summary_parts)
    
    def _update_conversation_metrics(self, thread: ConversationThread) -> None:
        """Update conversation analytics metrics."""
        
        self.conversation_metrics["total_conversations"] += 1
        
        if thread.state == ConversationState.COMPLETED:
            self.conversation_metrics["successful_completions"] += 1
        
        # Update duration metrics
        duration = (thread.last_activity - thread.created_at).total_seconds()
        current_avg = self.conversation_metrics["average_duration"]
        total_convs = self.conversation_metrics["total_conversations"]
        
        self.conversation_metrics["average_duration"] = (
            (current_avg * (total_convs - 1) + duration) / total_convs
        )
        
        # Update participant metrics
        for participant in thread.participants:
            if participant not in self.conversation_metrics["agent_participation"]:
                self.conversation_metrics["agent_participation"][participant] = 0
            self.conversation_metrics["agent_participation"][participant] += 1
    
    # === Transform Functions for Context Handling ===
    
    def _transform_for_image_generation(self, messages: List[Dict]) -> List[Dict]:
        """Transform messages to focus on image generation context."""
        
        transformed = []
        
        for msg in messages:
            content = msg.get('content', '')
            
            # Enhance image generation related messages
            if any(word in content.lower() for word in ['image', 'generate', 'dall-e', 'visual']):
                enhanced_content = f"[IMAGE GENERATION CONTEXT] {content}"
                transformed.append({**msg, 'content': enhanced_content})
            else:
                transformed.append(msg)
        
        return transformed
    
    def _compress_technical_details(self, messages: List[Dict]) -> List[Dict]:
        """Compress technical details while preserving key information."""
        
        compressed = []
        
        for msg in messages:
            content = msg.get('content', '')
            
            # Identify technical messages that can be compressed
            if len(content) > 500 and any(word in content.lower() for word in ['technical', 'parameter', 'configuration']):
                # Extract key technical points
                key_points = self._extract_key_technical_points(content)
                compressed_content = f"[TECHNICAL SUMMARY] {key_points}"
                compressed.append({**msg, 'content': compressed_content})
            else:
                compressed.append(msg)
        
        return compressed
    
    def _extract_key_technical_points(self, content: str) -> str:
        """Extract key technical points from detailed content."""
        
        # Simple extraction logic - in practice, would use more sophisticated NLP
        sentences = content.split('.')
        key_sentences = [
            s.strip() for s in sentences 
            if any(keyword in s.lower() for keyword in ['important', 'key', 'critical', 'must', 'should'])
        ]
        
        return '. '.join(key_sentences[:3])  # Top 3 key points
    
    # === Public Interface Methods ===
    
    async def add_message_to_thread(
        self, 
        thread_id: str, 
        sender: str, 
        content: str, 
        message_type: MessageType = MessageType.RESPONSE,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add a message to an existing conversation thread."""
        
        try:
            if thread_id not in self.active_threads:
                return False
            
            thread = self.active_threads[thread_id]
            
            message = ConversationMessage(
                id=f"msg_{uuid.uuid4().hex[:8]}",
                sender=sender,
                recipient=None,
                content=content,
                message_type=message_type,
                context=context or {}
            )
            
            thread.messages.append(message)
            thread.last_activity = datetime.now()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add message to thread {thread_id}: {e}")
            return False
    
    def get_thread_status(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a conversation thread."""
        
        if thread_id not in self.active_threads:
            return None
        
        thread = self.active_threads[thread_id]
        
        return {
            "thread_id": thread_id,
            "title": thread.title,
            "state": thread.state.value,
            "participants": thread.participants,
            "message_count": len(thread.messages),
            "is_active": thread.is_active,
            "created_at": thread.created_at.isoformat(),
            "last_activity": thread.last_activity.isoformat(),
            "decisions_count": len(thread.decisions),
            "consensus_items_count": len(thread.consensus_items)
        }
    
    def list_active_threads(self) -> List[Dict[str, Any]]:
        """List all active conversation threads."""
        
        return [
            self.get_thread_status(thread_id)
            for thread_id in self.active_threads
            if self.active_threads[thread_id].is_active
        ]
    
    def get_conversation_metrics(self) -> Dict[str, Any]:
        """Get conversation analytics and metrics."""
        
        return {
            **self.conversation_metrics,
            "active_threads": len([
                t for t in self.active_threads.values() 
                if t.is_active and t.state not in [ConversationState.COMPLETED, ConversationState.FAILED]
            ]),
            "total_agents": len(self.agents),
            "agent_profiles": len(self.agent_profiles),
            "conversation_templates": len(self.conversation_templates)
        }
    
    async def cleanup(self) -> None:
        """Clean up conversation manager resources."""
        
        try:
            # Clean up completed threads older than 24 hours
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            threads_to_remove = [
                thread_id for thread_id, thread in self.active_threads.items()
                if thread.state == ConversationState.COMPLETED and thread.completed_at and thread.completed_at < cutoff_time
            ]
            
            for thread_id in threads_to_remove:
                del self.active_threads[thread_id]
                if thread_id in self.group_chats:
                    del self.group_chats[thread_id]
                if thread_id in self.group_managers:
                    del self.group_managers[thread_id]
            
            self.logger.info(f"Cleaned up {len(threads_to_remove)} completed conversation threads")
            
        except Exception as e:
            self.logger.error(f"Conversation manager cleanup failed: {e}")