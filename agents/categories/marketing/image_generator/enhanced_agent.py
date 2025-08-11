"""
Enhanced Image Generator Agent with Advanced AutoGen Capabilities.
Demonstrates best practices for AutoGen conversation management, multi-agent workflows,
and collaborative image generation processes.
"""

import json
import asyncio
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from autogen import (
    ConversableAgent, 
    Agent, 
    GroupChat, 
    GroupChatManager,
    UserProxyAgent
)
from autogen.coding import LocalCommandLineCodeExecutor
from loguru import logger

from agents.base.base_agent import BaseAgent, AgentConfig, AgentResponse
from src.tools.integrations.image_generation.dalle_tool import DalleTool
from src.log_service import get_logger


class ImageGenerationState(Enum):
    """States for image generation workflow."""
    CONCEPT = "concept"
    REFINEMENT = "refinement" 
    GENERATION = "generation"
    REVIEW = "review"
    FINALIZATION = "finalization"
    COMPLETED = "completed"


@dataclass
class ImageRequest:
    """Structured image generation request."""
    id: str
    prompt: str
    requester_agent: str
    context: Dict[str, Any] = field(default_factory=dict)
    state: ImageGenerationState = ImageGenerationState.CONCEPT
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    generated_images: List[Dict[str, Any]] = field(default_factory=list)
    refinement_feedback: List[str] = field(default_factory=list)
    collaborating_agents: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ConversationContext:
    """Context for AutoGen conversations."""
    tenant_id: str
    session_id: str
    workflow_type: str
    participants: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class EnhancedImageGeneratorAgent(BaseAgent):
    """
    Enhanced Image Generator Agent showcasing AutoGen best practices.
    
    Features:
    - Advanced conversation management
    - Multi-agent collaboration workflows
    - Group chat capabilities
    - State-based image generation process
    - Intelligent agent-to-agent communication
    - Context-aware message handling
    """
    
    def __init__(self, config: AgentConfig):
        """Initialize the Enhanced Image Generator Agent."""
        super().__init__(config)
        
        # Initialize DALL-E tool
        dalle_config = {
            "rate_limit_per_minute": 50,
            "rate_limit_per_hour": 1000, 
            "timeout_seconds": 120,
            "retry_attempts": 3,
            "save_directory": "./generated_images",
            "max_prompt_length": 4000,
            "enabled": True
        }
        
        self.dalle_tool = DalleTool(dalle_config)
        
        # Enhanced tracking
        self.active_requests: Dict[str, ImageRequest] = {}
        self.conversation_contexts: Dict[str, ConversationContext] = {}
        self.collaboration_history: List[Dict[str, Any]] = []
        
        # Agent personas for different roles in workflow
        self.agent_personas = self._create_agent_personas()
        
        # Conversation templates
        self.conversation_templates = self._load_conversation_templates()
        
        # Function registry for AutoGen
        self.function_registry = {}
        
    async def setup(self) -> None:
        """Set up the Enhanced Image Generator Agent."""
        try:
            # Set up DALL-E tool
            if not await self.dalle_tool.setup():
                raise RuntimeError("Failed to initialize DALL-E tool")
            
            # Register all tool functions
            self._register_enhanced_functions()
            
            # Set up conversation handlers
            self._setup_conversation_handlers()
            
            self.logger.info("Enhanced Image Generator Agent setup completed")
            
        except Exception as e:
            self.logger.error(f"Enhanced Image Generator Agent setup failed: {e}")
            raise
    
    def _create_agent_personas(self) -> Dict[str, Dict[str, Any]]:
        """Create different agent personas for collaborative workflows."""
        return {
            "creative_director": {
                "name": "Creative Director",
                "role": "Provides creative vision and brand alignment guidance",
                "system_message": """You are a Creative Director specializing in visual marketing strategy.
                Your role is to ensure all generated images align with brand vision, marketing objectives,
                and target audience preferences. You provide high-level creative guidance and approve concepts.""",
                "capabilities": ["concept_approval", "brand_alignment", "creative_strategy"]
            },
            "prompt_engineer": {
                "name": "Prompt Engineer", 
                "role": "Optimizes prompts for DALL-E 3 generation",
                "system_message": """You are a Prompt Engineering Specialist for DALL-E 3.
                Your expertise lies in crafting optimal prompts that leverage DALL-E 3's capabilities.
                You enhance user prompts with technical details, style modifiers, and quality enhancers.""",
                "capabilities": ["prompt_optimization", "technical_enhancement", "style_guidance"]
            },
            "quality_reviewer": {
                "name": "Quality Reviewer",
                "role": "Reviews generated images and suggests improvements",
                "system_message": """You are a Quality Assurance Specialist for marketing visuals.
                You evaluate generated images for quality, brand compliance, and marketing effectiveness.
                You provide specific feedback for improvements and approve final outputs.""",
                "capabilities": ["quality_assessment", "improvement_suggestions", "final_approval"]
            }
        }
    
    def _load_conversation_templates(self) -> Dict[str, str]:
        """Load conversation templates for different scenarios."""
        return {
            "initial_request": """
            I'd like to help you create a marketing image. Let me understand your needs:
            
            1. **What is the primary purpose** of this image? (e.g., social media post, website banner, advertisement)
            2. **What should the image show** or convey?
            3. **Who is your target audience**?
            4. **Any specific style preferences** or brand guidelines?
            5. **Where will this be used** (platform/medium)?
            
            Based on your answers, I can coordinate with my specialist agents to create the perfect image for you.
            """,
            
            "collaboration_start": """
            Starting collaborative image generation workflow for: {request_description}
            
            Participants: {participants}
            Workflow Type: {workflow_type}
            
            Let's begin by having our Creative Director review the concept...
            """,
            
            "refinement_request": """
            Based on the initial generation, I've identified areas for improvement:
            
            Current Issues: {issues}
            Suggested Refinements: {suggestions}
            
            Would you like me to regenerate with these enhancements or would you prefer different modifications?
            """,
            
            "workflow_complete": """
            ✅ **Image Generation Workflow Completed**
            
            **Final Results:**
            - Images Generated: {count}
            - Workflow Type: {workflow_type}
            - Participants: {participants}
            - Total Refinements: {refinements}
            
            **Files Created:**
            {file_list}
            
            The images are ready for your marketing campaigns!
            """
        }
    
    def _register_enhanced_functions(self) -> None:
        """Register enhanced functions with AutoGen agent."""
        if not self._agent:
            return
            
        # Core image generation functions
        self._register_function(
            "generate_image_with_workflow",
            self.generate_image_with_workflow,
            "Generate images using collaborative multi-agent workflow"
        )
        
        self._register_function(
            "start_collaborative_session", 
            self.start_collaborative_session,
            "Start a collaborative image generation session with specialist agents"
        )
        
        self._register_function(
            "refine_image_concept",
            self.refine_image_concept,
            "Refine an image concept through agent collaboration"
        )
        
        self._register_function(
            "review_and_iterate",
            self.review_and_iterate, 
            "Review generated images and iterate improvements"
        )
        
        # Enhanced conversation management
        self._register_function(
            "manage_group_conversation",
            self.manage_group_conversation,
            "Manage group conversations between multiple agents"
        )
        
        self._register_function(
            "get_conversation_context",
            self.get_conversation_context,
            "Retrieve current conversation context and history"
        )
    
    def _register_function(
        self, 
        name: str, 
        func: Callable, 
        description: str
    ) -> None:
        """Register a function with the AutoGen agent."""
        self.function_registry[name] = func
        
        # Create function schema
        schema = self._create_function_schema(name, func, description)
        
        # Register with AutoGen
        self._agent.register_for_execution(name)(func)
        self._agent.register_for_llm(name)(lambda: schema)
    
    def _create_function_schema(
        self, 
        name: str, 
        func: Callable, 
        description: str
    ) -> Dict[str, Any]:
        """Create function schema for AutoGen registration."""
        # This would include detailed parameter schemas based on function signatures
        # Simplified version for demonstration
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": self._extract_function_parameters(func),
                    "required": []
                }
            }
        }
    
    def _extract_function_parameters(self, func: Callable) -> Dict[str, Any]:
        """Extract function parameters for schema generation."""
        # Simplified parameter extraction - in practice, would use inspection
        return {
            "request": {
                "type": "string", 
                "description": "The image generation request or command"
            },
            "context": {
                "type": "object",
                "description": "Additional context for the request"
            }
        }
    
    def _setup_conversation_handlers(self) -> None:
        """Set up conversation-specific message handlers."""
        if not self._agent:
            return
        
        # Add custom reply function for enhanced conversation handling
        self._agent.register_reply(
            trigger=lambda sender, message, recipient: True,
            reply_func=self._enhanced_reply_handler,
            position=0  # Highest priority
        )
    
    async def _enhanced_reply_handler(
        self, 
        recipient: Agent, 
        messages: Optional[List[Dict]] = None, 
        sender: Optional[Agent] = None,
        config: Optional[Any] = None
    ) -> Union[str, Dict, None]:
        """Enhanced reply handler for better conversation management."""
        try:
            if not messages:
                return None
                
            last_message = messages[-1]["content"] if messages else ""
            
            # Determine conversation type and route appropriately
            conversation_type = self._detect_conversation_type(last_message, sender)
            
            if conversation_type == "collaborative_workflow":
                return await self._handle_collaborative_workflow(last_message, sender, messages)
            elif conversation_type == "image_generation":
                return await self._handle_image_generation_request(last_message, sender, messages)
            elif conversation_type == "refinement":
                return await self._handle_refinement_request(last_message, sender, messages)
            else:
                return await self._handle_general_conversation(last_message, sender, messages)
                
        except Exception as e:
            self.logger.error(f"Enhanced reply handler error: {e}")
            return f"I encountered an error processing your request: {str(e)}"
    
    def _detect_conversation_type(
        self, 
        message: str, 
        sender: Optional[Agent] = None
    ) -> str:
        """Detect the type of conversation to route appropriately."""
        message_lower = message.lower()
        
        # Detection logic based on keywords and context
        if any(word in message_lower for word in ["collaborate", "workflow", "team", "specialists"]):
            return "collaborative_workflow"
        elif any(word in message_lower for word in ["generate", "create image", "dall-e"]):
            return "image_generation" 
        elif any(word in message_lower for word in ["refine", "improve", "modify", "change"]):
            return "refinement"
        else:
            return "general_conversation"
    
    async def _handle_collaborative_workflow(
        self, 
        message: str, 
        sender: Optional[Agent], 
        messages: List[Dict]
    ) -> str:
        """Handle collaborative workflow requests."""
        try:
            # Create collaborative session
            session_id = f"collab_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Initialize workflow
            workflow_result = await self.start_collaborative_session(
                request=message,
                workflow_type="collaborative_generation",
                context={"session_id": session_id, "sender": sender.name if sender else "unknown"}
            )
            
            return workflow_result.get("response", "Collaborative workflow initiated successfully.")
            
        except Exception as e:
            self.logger.error(f"Collaborative workflow handling error: {e}")
            return f"Error starting collaborative workflow: {str(e)}"
    
    async def _handle_image_generation_request(
        self, 
        message: str, 
        sender: Optional[Agent], 
        messages: List[Dict]
    ) -> str:
        """Handle direct image generation requests."""
        try:
            # Generate image using enhanced workflow
            result = await self.generate_image_with_workflow(
                request=message,
                context={
                    "sender": sender.name if sender else "unknown",
                    "conversation_history": messages
                }
            )
            
            return result.get("response", "Image generation completed.")
            
        except Exception as e:
            self.logger.error(f"Image generation handling error: {e}")
            return f"Error generating image: {str(e)}"
    
    async def _handle_refinement_request(
        self, 
        message: str, 
        sender: Optional[Agent], 
        messages: List[Dict]
    ) -> str:
        """Handle image refinement requests."""
        try:
            # Find the most recent image generation request to refine
            request_id = self._find_latest_request_id()
            
            if request_id and request_id in self.active_requests:
                result = await self.refine_image_concept(
                    request_id=request_id,
                    refinement_instructions=message,
                    context={"sender": sender.name if sender else "unknown"}
                )
                return result.get("response", "Image refinement completed.")
            else:
                return "No active image generation request found to refine. Please start a new generation first."
                
        except Exception as e:
            self.logger.error(f"Refinement handling error: {e}")
            return f"Error refining image: {str(e)}"
    
    async def _handle_general_conversation(
        self, 
        message: str, 
        sender: Optional[Agent], 
        messages: List[Dict]
    ) -> str:
        """Handle general marketing consultation."""
        consultation_prompt = f"""
        As a marketing image generation specialist, provide helpful guidance for: "{message}"
        
        Consider:
        - Image types for different marketing objectives
        - Best practices for visual marketing
        - Platform-specific recommendations
        - Creative and technical suggestions
        - Collaborative workflow options available
        
        If they want to generate images, suggest using my collaborative workflow capabilities.
        """
        
        # Use the base agent's LLM for consultation
        if self._agent:
            response = await self._agent.a_generate_reply(
                messages=[{"role": "user", "content": consultation_prompt}],
                sender=self._agent
            )
            return response
        
        return self.conversation_templates["initial_request"]
    
    # === Core Workflow Functions ===
    
    async def generate_image_with_workflow(
        self, 
        request: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate images using collaborative multi-agent workflow."""
        try:
            context = context or {}
            request_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # Create structured request
            image_request = ImageRequest(
                id=request_id,
                prompt=request,
                requester_agent=context.get("sender", "unknown"),
                context=context
            )
            
            self.active_requests[request_id] = image_request
            
            # Stage 1: Concept Development with Creative Director
            concept_result = await self._concept_development_stage(image_request)
            
            # Stage 2: Prompt Engineering
            prompt_result = await self._prompt_engineering_stage(image_request)
            
            # Stage 3: Image Generation
            generation_result = await self._generation_stage(image_request)
            
            # Stage 4: Quality Review
            review_result = await self._quality_review_stage(image_request)
            
            # Stage 5: Finalization
            final_result = await self._finalization_stage(image_request)
            
            return {
                "success": True,
                "request_id": request_id,
                "workflow_stages": {
                    "concept": concept_result,
                    "prompt_engineering": prompt_result,
                    "generation": generation_result,
                    "review": review_result,
                    "finalization": final_result
                },
                "generated_images": image_request.generated_images,
                "response": self._format_workflow_response(image_request)
            }
            
        except Exception as e:
            self.logger.error(f"Workflow generation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"Workflow failed: {str(e)}"
            }
    
    async def start_collaborative_session(
        self, 
        request: str, 
        workflow_type: str = "standard",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Start a collaborative image generation session."""
        try:
            context = context or {}
            session_id = context.get("session_id", f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            # Create conversation context
            conv_context = ConversationContext(
                tenant_id=context.get("tenant_id", "default"),
                session_id=session_id,
                workflow_type=workflow_type,
                participants=["image_generator", "creative_director", "prompt_engineer", "quality_reviewer"],
                metadata=context
            )
            
            self.conversation_contexts[session_id] = conv_context
            
            # Create group chat with specialist agents
            group_chat = await self._create_specialist_group_chat(conv_context)
            
            # Start the collaborative conversation
            initial_message = f"""
            Starting collaborative image generation session for: "{request}"
            
            Session ID: {session_id}
            Workflow Type: {workflow_type}
            
            Let's work together to create the perfect marketing image.
            """
            
            # Initiate group conversation
            group_result = await self._run_group_conversation(group_chat, initial_message, conv_context)
            
            return {
                "success": True,
                "session_id": session_id,
                "participants": conv_context.participants,
                "group_result": group_result,
                "response": f"Collaborative session started successfully. Session ID: {session_id}"
            }
            
        except Exception as e:
            self.logger.error(f"Collaborative session error: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"Failed to start collaborative session: {str(e)}"
            }
    
    async def refine_image_concept(
        self, 
        request_id: str, 
        refinement_instructions: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Refine an image concept through agent collaboration."""
        try:
            if request_id not in self.active_requests:
                return {
                    "success": False,
                    "error": "Request not found",
                    "response": f"No active request found with ID: {request_id}"
                }
            
            image_request = self.active_requests[request_id]
            image_request.refinement_feedback.append(refinement_instructions)
            image_request.state = ImageGenerationState.REFINEMENT
            image_request.updated_at = datetime.now()
            
            # Process refinement through specialist agents
            refinement_result = await self._process_refinement(image_request, refinement_instructions)
            
            return {
                "success": True,
                "request_id": request_id,
                "refinement_result": refinement_result,
                "response": self._format_refinement_response(image_request, refinement_result)
            }
            
        except Exception as e:
            self.logger.error(f"Refinement error: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"Refinement failed: {str(e)}"
            }
    
    async def review_and_iterate(
        self, 
        request_id: str, 
        review_criteria: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Review generated images and iterate improvements."""
        try:
            if request_id not in self.active_requests:
                return {
                    "success": False,
                    "error": "Request not found"
                }
            
            image_request = self.active_requests[request_id]
            image_request.state = ImageGenerationState.REVIEW
            
            # Perform automated quality review
            review_result = await self._automated_quality_review(image_request, review_criteria)
            
            # If improvements needed, iterate
            if review_result.get("needs_improvement", False):
                iteration_result = await self._iterate_improvements(image_request, review_result)
                review_result["iteration_result"] = iteration_result
            
            return {
                "success": True,
                "request_id": request_id,
                "review_result": review_result,
                "response": self._format_review_response(image_request, review_result)
            }
            
        except Exception as e:
            self.logger.error(f"Review and iterate error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def manage_group_conversation(
        self, 
        session_id: str, 
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Manage group conversations between multiple agents."""
        try:
            if session_id not in self.conversation_contexts:
                return {
                    "success": False,
                    "error": "Session not found"
                }
            
            conv_context = self.conversation_contexts[session_id]
            
            # Create or retrieve group chat
            group_chat = await self._get_or_create_group_chat(conv_context)
            
            # Process message through group
            group_result = await self._process_group_message(group_chat, message, conv_context)
            
            return {
                "success": True,
                "session_id": session_id,
                "group_result": group_result,
                "response": group_result.get("final_response", "Group conversation processed.")
            }
            
        except Exception as e:
            self.logger.error(f"Group conversation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # === Implementation Methods ===
    
    async def process_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        sender: Optional[Agent] = None
    ) -> str:
        """Enhanced message processing with workflow coordination."""
        try:
            context = context or {}
            
            # The enhanced reply handler will route this appropriately
            # This method serves as a fallback for direct calls
            
            conversation_type = self._detect_conversation_type(message, sender)
            
            if conversation_type == "collaborative_workflow":
                result = await self.start_collaborative_session(
                    request=message,
                    context=context
                )
                return result.get("response", "Collaborative workflow initiated.")
            
            elif conversation_type == "image_generation":
                result = await self.generate_image_with_workflow(
                    request=message,
                    context=context
                )
                return result.get("response", "Image generation completed.")
            
            else:
                return await self._handle_general_conversation(message, sender, [])
                
        except Exception as e:
            self.logger.error(f"Message processing failed: {e}")
            return f"I encountered an error: {str(e)}. Please try again."
    
    def _find_latest_request_id(self) -> Optional[str]:
        """Find the most recent active request ID."""
        if not self.active_requests:
            return None
        
        # Return the most recently updated request
        return max(
            self.active_requests.keys(),
            key=lambda k: self.active_requests[k].updated_at
        )
    
    def _format_workflow_response(self, image_request: ImageRequest) -> str:
        """Format workflow completion response."""
        return self.conversation_templates["workflow_complete"].format(
            count=len(image_request.generated_images),
            workflow_type="Multi-Agent Collaborative",
            participants=", ".join(image_request.collaborating_agents),
            refinements=len(image_request.refinement_feedback),
            file_list="\n".join([f"- {img.get('filename', 'N/A')}" for img in image_request.generated_images])
        )
    
    def _format_refinement_response(self, image_request: ImageRequest, refinement_result: Dict) -> str:
        """Format refinement completion response."""
        return f"""
        ✅ **Image Refinement Completed**
        
        Request ID: {image_request.id}
        Refinements Applied: {len(image_request.refinement_feedback)}
        
        **Latest Refinement:**
        {image_request.refinement_feedback[-1] if image_request.refinement_feedback else 'None'}
        
        **Result:**
        {refinement_result.get('summary', 'Refinement processing completed')}
        """
    
    def _format_review_response(self, image_request: ImageRequest, review_result: Dict) -> str:
        """Format review completion response."""
        quality_score = review_result.get("quality_score", 0)
        improvements = review_result.get("suggested_improvements", [])
        
        response = f"""
        📊 **Quality Review Completed**
        
        Request ID: {image_request.id}
        Quality Score: {quality_score}/10
        
        """
        
        if improvements:
            response += "**Suggested Improvements:**\n"
            for improvement in improvements:
                response += f"- {improvement}\n"
        
        if review_result.get("needs_improvement"):
            response += "\n🔄 Improvements will be applied automatically."
        else:
            response += "\n✅ Images meet quality standards!"
        
        return response
    
    # === Workflow Stage Implementations ===
    
    async def _concept_development_stage(self, image_request: ImageRequest) -> Dict[str, Any]:
        """Concept development with Creative Director persona."""
        try:
            creative_director = self.agent_personas["creative_director"]
            
            # Simulate Creative Director analysis
            concept_prompt = f"""
            As a Creative Director, analyze this image request: "{image_request.prompt}"
            
            Provide:
            1. Creative concept evaluation
            2. Brand alignment suggestions
            3. Target audience considerations
            4. Visual style recommendations
            
            Context: {image_request.context}
            """
            
            # In a full implementation, this would create an actual Creative Director agent
            # For now, we'll simulate the response
            concept_result = {
                "stage": "concept_development",
                "agent": creative_director["name"],
                "analysis": "Concept approved with strategic enhancements",
                "recommendations": [
                    "Align with brand guidelines",
                    "Consider target audience demographics",
                    "Ensure visual impact for marketing effectiveness"
                ],
                "approval_status": "approved"
            }
            
            image_request.collaborating_agents.append(creative_director["name"])
            image_request.conversation_history.append({
                "stage": "concept",
                "agent": creative_director["name"],
                "result": concept_result
            })
            
            return concept_result
            
        except Exception as e:
            self.logger.error(f"Concept development error: {e}")
            return {"stage": "concept_development", "error": str(e)}
    
    async def _prompt_engineering_stage(self, image_request: ImageRequest) -> Dict[str, Any]:
        """Prompt engineering with specialist persona."""
        try:
            prompt_engineer = self.agent_personas["prompt_engineer"]
            
            # Enhance the original prompt
            enhanced_prompt = await self._enhance_prompt_with_specialist(
                image_request.prompt,
                image_request.context
            )
            
            prompt_result = {
                "stage": "prompt_engineering",
                "agent": prompt_engineer["name"],
                "original_prompt": image_request.prompt,
                "enhanced_prompt": enhanced_prompt,
                "enhancements_applied": [
                    "Technical quality modifiers",
                    "Style optimization",
                    "Marketing effectiveness terms"
                ]
            }
            
            # Update the request with enhanced prompt
            image_request.prompt = enhanced_prompt
            image_request.collaborating_agents.append(prompt_engineer["name"])
            image_request.conversation_history.append({
                "stage": "prompt_engineering",
                "agent": prompt_engineer["name"],
                "result": prompt_result
            })
            
            return prompt_result
            
        except Exception as e:
            self.logger.error(f"Prompt engineering error: {e}")
            return {"stage": "prompt_engineering", "error": str(e)}
    
    async def _generation_stage(self, image_request: ImageRequest) -> Dict[str, Any]:
        """Actual image generation using DALL-E tool."""
        try:
            generation_params = {
                "prompt": image_request.prompt,
                "size": image_request.context.get("size", "1024x1024"),
                "quality": image_request.context.get("quality", "standard"),
                "style": image_request.context.get("style", "vivid"),
                "n": image_request.context.get("quantity", 1),
                "save_to_file": True,
                "filename_prefix": f"enhanced_{image_request.id}"
            }
            
            # Execute DALL-E generation
            generation_result = await self.dalle_tool.execute(
                generation_params, 
                image_request.context
            )
            
            if generation_result.status.value == "success" and generation_result.data:
                # Store generated images in request
                for img_data in generation_result.data.get("images", []):
                    image_request.generated_images.append(img_data)
            
            stage_result = {
                "stage": "generation", 
                "agent": "DALL-E_Generator",
                "success": generation_result.status.value == "success",
                "images_generated": len(image_request.generated_images),
                "dalle_result": generation_result.data if generation_result.data else None,
                "error": generation_result.error
            }
            
            image_request.state = ImageGenerationState.GENERATION
            image_request.conversation_history.append({
                "stage": "generation",
                "agent": "DALL-E_Generator", 
                "result": stage_result
            })
            
            return stage_result
            
        except Exception as e:
            self.logger.error(f"Generation stage error: {e}")
            return {"stage": "generation", "error": str(e)}
    
    async def _quality_review_stage(self, image_request: ImageRequest) -> Dict[str, Any]:
        """Quality review with reviewer persona."""
        try:
            quality_reviewer = self.agent_personas["quality_reviewer"]
            
            # Perform quality assessment
            quality_assessment = await self._assess_image_quality(image_request)
            
            review_result = {
                "stage": "quality_review",
                "agent": quality_reviewer["name"],
                "quality_score": quality_assessment.get("score", 7),
                "assessment": quality_assessment.get("assessment", "Images meet quality standards"),
                "suggestions": quality_assessment.get("improvements", []),
                "approval_status": "approved" if quality_assessment.get("score", 0) >= 7 else "needs_improvement"
            }
            
            image_request.collaborating_agents.append(quality_reviewer["name"])
            image_request.conversation_history.append({
                "stage": "quality_review",
                "agent": quality_reviewer["name"],
                "result": review_result
            })
            
            return review_result
            
        except Exception as e:
            self.logger.error(f"Quality review error: {e}")
            return {"stage": "quality_review", "error": str(e)}
    
    async def _finalization_stage(self, image_request: ImageRequest) -> Dict[str, Any]:
        """Finalization stage - prepare deliverables."""
        try:
            finalization_result = {
                "stage": "finalization",
                "agent": "Image_Generator_Coordinator",
                "total_images": len(image_request.generated_images),
                "workflow_participants": image_request.collaborating_agents,
                "total_refinements": len(image_request.refinement_feedback),
                "final_status": "completed",
                "deliverables": [img.get("filename") for img in image_request.generated_images if img.get("filename")]
            }
            
            image_request.state = ImageGenerationState.COMPLETED
            image_request.updated_at = datetime.now()
            
            return finalization_result
            
        except Exception as e:
            self.logger.error(f"Finalization error: {e}")
            return {"stage": "finalization", "error": str(e)}
    
    # === Helper Methods ===
    
    async def _enhance_prompt_with_specialist(
        self, 
        original_prompt: str, 
        context: Dict[str, Any]
    ) -> str:
        """Enhance prompt using prompt engineering expertise."""
        # Simulate prompt engineering enhancement
        enhancements = [
            "professional marketing quality",
            "commercial photography lighting", 
            "high resolution",
            "brand-appropriate styling"
        ]
        
        enhanced = f"{original_prompt}, {', '.join(enhancements)}"
        
        # Ensure within limits
        if len(enhanced) > 3900:
            enhanced = enhanced[:3900] + "..."
        
        return enhanced
    
    async def _assess_image_quality(self, image_request: ImageRequest) -> Dict[str, Any]:
        """Assess quality of generated images."""
        # Simulate quality assessment
        # In practice, this could use image analysis APIs or human review
        
        base_score = 8  # Assume good quality
        improvements = []
        
        # Check for common issues
        if len(image_request.prompt) < 20:
            base_score -= 1
            improvements.append("Consider more detailed prompt")
        
        if not any(keyword in image_request.prompt.lower() for keyword in ["professional", "high quality", "commercial"]):
            improvements.append("Add professional quality modifiers")
        
        return {
            "score": base_score,
            "assessment": "Quality assessment completed",
            "improvements": improvements
        }
    
    async def _create_specialist_group_chat(
        self, 
        conv_context: ConversationContext
    ) -> GroupChat:
        """Create a group chat with specialist agents."""
        # In a full implementation, this would create actual ConversableAgent instances
        # For demonstration, we'll create a simplified group structure
        
        agents = []
        for persona_key, persona in self.agent_personas.items():
            # Create mock agent (in practice, would be real ConversableAgent)
            mock_agent = type('MockAgent', (), {
                'name': persona["name"],
                'role': persona["role"],
                'system_message': persona["system_message"]
            })()
            agents.append(mock_agent)
        
        # Create group chat structure
        group_chat = type('GroupChat', (), {
            'agents': agents,
            'messages': [],
            'max_round': 10
        })()
        
        return group_chat
    
    async def _run_group_conversation(
        self, 
        group_chat, 
        initial_message: str, 
        conv_context: ConversationContext
    ) -> Dict[str, Any]:
        """Run a group conversation simulation."""
        # Simulate group conversation
        # In practice, this would use AutoGen's GroupChatManager
        
        conversation_log = [
            {"agent": "Coordinator", "message": initial_message},
            {"agent": "Creative Director", "message": "I'll review the creative concept and brand alignment."},
            {"agent": "Prompt Engineer", "message": "I'll optimize the prompt for DALL-E 3 generation."},
            {"agent": "Quality Reviewer", "message": "I'll assess the final images for quality and compliance."}
        ]
        
        return {
            "conversation_log": conversation_log,
            "participants": conv_context.participants,
            "final_response": "Group conversation completed successfully."
        }
    
    async def _get_or_create_group_chat(self, conv_context: ConversationContext):
        """Get existing or create new group chat."""
        # Implementation would manage persistent group chats
        return await self._create_specialist_group_chat(conv_context)
    
    async def _process_group_message(
        self, 
        group_chat, 
        message: str, 
        conv_context: ConversationContext
    ) -> Dict[str, Any]:
        """Process a message through the group chat."""
        # Simulate group message processing
        return {
            "message_processed": message,
            "group_response": "Group has processed the message collaboratively.",
            "final_response": "Group conversation updated successfully."
        }
    
    async def _process_refinement(
        self, 
        image_request: ImageRequest, 
        refinement_instructions: str
    ) -> Dict[str, Any]:
        """Process refinement through specialist agents."""
        # Simulate refinement processing
        return {
            "refinement_applied": refinement_instructions,
            "processing_agent": "Refinement Coordinator",
            "status": "completed",
            "summary": "Refinement instructions have been processed and applied to the image generation workflow."
        }
    
    async def _automated_quality_review(
        self, 
        image_request: ImageRequest, 
        review_criteria: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform automated quality review."""
        quality_assessment = await self._assess_image_quality(image_request)
        
        return {
            "quality_score": quality_assessment["score"],
            "assessment": quality_assessment["assessment"],
            "suggested_improvements": quality_assessment["improvements"],
            "needs_improvement": quality_assessment["score"] < 7,
            "review_criteria": review_criteria or "Standard quality assessment"
        }
    
    async def _iterate_improvements(
        self, 
        image_request: ImageRequest, 
        review_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply iterative improvements based on review."""
        improvements = review_result.get("suggested_improvements", [])
        
        if improvements:
            # Apply improvements to prompt
            improvement_text = ", ".join(improvements)
            image_request.prompt = f"{image_request.prompt}, {improvement_text}"
            
            # Re-generate with improvements
            regeneration_result = await self._generation_stage(image_request)
            
            return {
                "improvements_applied": improvements,
                "regeneration_result": regeneration_result,
                "status": "completed"
            }
        
        return {"status": "no_improvements_needed"}
    
    def get_conversation_context(self, session_id: str) -> Optional[ConversationContext]:
        """Get conversation context for a session."""
        return self.conversation_contexts.get(session_id)
    
    async def cleanup(self) -> None:
        """Clean up enhanced agent resources."""
        try:
            # Clean up active requests
            self.active_requests.clear()
            self.conversation_contexts.clear()
            
            # Clean up DALL-E tool
            if self.dalle_tool:
                await self.dalle_tool.cleanup()
            
            await super().cleanup()
            self.logger.info("Enhanced Image Generator Agent cleaned up successfully")
            
        except Exception as e:
            self.logger.error(f"Enhanced Image Generator Agent cleanup failed: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get enhanced agent metrics."""
        base_metrics = super().get_metrics()
        
        # Add enhanced metrics
        total_collaborative_sessions = len(self.conversation_contexts)
        active_requests_count = len(self.active_requests)
        completed_workflows = len([
            r for r in self.active_requests.values() 
            if r.state == ImageGenerationState.COMPLETED
        ])
        
        base_metrics.update({
            "active_requests": active_requests_count,
            "collaborative_sessions": total_collaborative_sessions,
            "completed_workflows": completed_workflows,
            "average_collaborators_per_request": sum(
                len(r.collaborating_agents) for r in self.active_requests.values()
            ) / max(len(self.active_requests), 1),
            "workflow_success_rate": completed_workflows / max(len(self.active_requests), 1)
        })
        
        return base_metrics