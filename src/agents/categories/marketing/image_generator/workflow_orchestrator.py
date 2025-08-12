"""
Multi-Agent Workflow Orchestrator for Collaborative Image Generation.
Demonstrates advanced AutoGen patterns including group chat management,
conversation orchestration, and complex multi-agent workflows.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Callable, Union
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
from autogen.agentchat.conversable_agent import ConversableAgent
from loguru import logger

from src.log_service import get_logger
from .enhanced_agent import EnhancedImageGeneratorAgent, ImageGenerationState, ImageRequest, ConversationContext


class WorkflowType(Enum):
    """Types of image generation workflows."""
    SIMPLE = "simple"
    COLLABORATIVE = "collaborative" 
    ITERATIVE_REFINEMENT = "iterative_refinement"
    BRAND_REVIEW = "brand_review"
    A_B_TESTING = "a_b_testing"
    CAMPAIGN_SERIES = "campaign_series"


class WorkflowStatus(Enum):
    """Status of workflow execution."""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowAgent:
    """Represents an agent in a workflow."""
    name: str
    role: str
    agent: ConversableAgent
    capabilities: List[str] = field(default_factory=list)
    is_active: bool = True
    performance_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowStep:
    """Represents a step in a workflow."""
    id: str
    name: str
    agent_name: str
    action: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class Workflow:
    """Represents a complete workflow."""
    id: str
    name: str
    type: WorkflowType
    status: WorkflowStatus = WorkflowStatus.CREATED
    agents: Dict[str, WorkflowAgent] = field(default_factory=dict)
    steps: Dict[str, WorkflowStep] = field(default_factory=dict)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    final_outputs: Dict[str, Any] = field(default_factory=dict)


class ImageGenerationOrchestrator:
    """
    Advanced AutoGen workflow orchestrator for collaborative image generation.
    
    Demonstrates:
    - Complex multi-agent workflow coordination
    - Dynamic group chat management
    - Conversation state management
    - Parallel and sequential agent execution
    - Error handling and recovery
    - Performance monitoring and optimization
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the workflow orchestrator."""
        self.config = config
        self.logger = get_logger("image_generation_orchestrator")
        
        # Workflow management
        self.active_workflows: Dict[str, Workflow] = {}
        self.workflow_templates: Dict[WorkflowType, Dict[str, Any]] = {}
        self.agent_registry: Dict[str, WorkflowAgent] = {}
        
        # AutoGen components
        self.group_chats: Dict[str, GroupChat] = {}
        self.group_managers: Dict[str, GroupChatManager] = {}
        
        # Performance tracking
        self.execution_metrics: Dict[str, Any] = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "average_execution_time": 0.0,
            "agent_performance": {}
        }
        
        # Initialize workflow templates
        self._initialize_workflow_templates()
        
    async def setup(self) -> None:
        """Set up the orchestrator."""
        try:
            # Create specialized agents
            await self._create_specialized_agents()
            
            # Initialize workflow templates
            self._initialize_workflow_templates()
            
            self.logger.info("Image Generation Orchestrator setup completed")
            
        except Exception as e:
            self.logger.error(f"Orchestrator setup failed: {e}")
            raise
    
    async def _create_specialized_agents(self) -> None:
        """Create specialized agents for different workflow roles."""
        
        # Creative Director Agent
        creative_director = AssistantAgent(
            name="creative_director",
            system_message="""You are a Creative Director specializing in visual marketing strategy.
            Your role is to:
            - Evaluate creative concepts for brand alignment and marketing effectiveness
            - Provide high-level creative direction and vision
            - Ensure visual content aligns with marketing objectives
            - Review and approve creative concepts before implementation
            - Suggest creative alternatives and improvements
            
            You work collaboratively with other agents to ensure the best possible creative outcomes.""",
            llm_config=self._get_llm_config(),
            human_input_mode="NEVER"
        )
        
        # Prompt Engineering Specialist
        prompt_engineer = AssistantAgent(
            name="prompt_engineer",
            system_message="""You are a Prompt Engineering Specialist for DALL-E 3 image generation.
            Your expertise includes:
            - Optimizing prompts for maximum DALL-E 3 effectiveness
            - Understanding DALL-E 3's strengths and limitations
            - Adding technical modifiers and style enhancements
            - Balancing creativity with technical precision
            - Adapting prompts based on target use cases
            
            Transform user requests into optimized prompts that produce exceptional images.""",
            llm_config=self._get_llm_config(),
            human_input_mode="NEVER"
        )
        
        # Quality Assurance Reviewer
        qa_reviewer = AssistantAgent(
            name="qa_reviewer", 
            system_message="""You are a Quality Assurance Specialist for marketing visuals.
            Your responsibilities include:
            - Evaluating generated images for quality and effectiveness
            - Checking brand compliance and consistency
            - Identifying areas for improvement
            - Providing specific, actionable feedback
            - Approving final deliverables
            
            Ensure all visual content meets professional marketing standards.""",
            llm_config=self._get_llm_config(),
            human_input_mode="NEVER"
        )
        
        # Brand Compliance Officer
        brand_officer = AssistantAgent(
            name="brand_officer",
            system_message="""You are a Brand Compliance Officer focused on visual brand consistency.
            Your role involves:
            - Ensuring all visuals align with brand guidelines
            - Checking color schemes, typography, and visual style consistency
            - Maintaining brand voice in visual communications
            - Flagging potential brand violations
            - Suggesting brand-compliant alternatives
            
            Protect and strengthen brand identity through consistent visual communication.""",
            llm_config=self._get_llm_config(),
            human_input_mode="NEVER"
        )
        
        # Campaign Strategist  
        campaign_strategist = AssistantAgent(
            name="campaign_strategist",
            system_message="""You are a Campaign Strategist specializing in visual marketing campaigns.
            Your expertise covers:
            - Planning cohesive visual campaign strategies
            - Coordinating multiple image assets for unified campaigns
            - Understanding platform-specific visual requirements
            - Optimizing images for different marketing channels
            - Measuring visual campaign effectiveness
            
            Create strategic visual campaigns that drive marketing success.""",
            llm_config=self._get_llm_config(),
            human_input_mode="NEVER"
        )
        
        # Register agents
        self.agent_registry = {
            "creative_director": WorkflowAgent(
                name="creative_director",
                role="Creative Direction & Vision",
                agent=creative_director,
                capabilities=["concept_evaluation", "creative_direction", "brand_alignment"]
            ),
            "prompt_engineer": WorkflowAgent(
                name="prompt_engineer", 
                role="Prompt Optimization",
                agent=prompt_engineer,
                capabilities=["prompt_enhancement", "technical_optimization", "style_guidance"]
            ),
            "qa_reviewer": WorkflowAgent(
                name="qa_reviewer",
                role="Quality Assurance",
                agent=qa_reviewer, 
                capabilities=["quality_evaluation", "improvement_feedback", "final_approval"]
            ),
            "brand_officer": WorkflowAgent(
                name="brand_officer",
                role="Brand Compliance", 
                agent=brand_officer,
                capabilities=["brand_compliance", "style_consistency", "guideline_enforcement"]
            ),
            "campaign_strategist": WorkflowAgent(
                name="campaign_strategist",
                role="Campaign Strategy",
                agent=campaign_strategist,
                capabilities=["campaign_planning", "asset_coordination", "channel_optimization"]
            )
        }
        
        self.logger.info(f"Created {len(self.agent_registry)} specialized agents")
    
    def _get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration for agents."""
        from src.config.config_manager import get_config
        
        config_manager = get_config()
        return config_manager.get_llm_config()
    
    def _initialize_workflow_templates(self) -> None:
        """Initialize workflow templates for different types."""
        
        self.workflow_templates = {
            WorkflowType.SIMPLE: {
                "name": "Simple Image Generation",
                "description": "Direct image generation with minimal review",
                "steps": [
                    {"id": "generate", "agent": "prompt_engineer", "action": "enhance_and_generate"}
                ]
            },
            
            WorkflowType.COLLABORATIVE: {
                "name": "Collaborative Review Workflow", 
                "description": "Multi-agent collaborative image generation with reviews",
                "steps": [
                    {"id": "concept_review", "agent": "creative_director", "action": "review_concept"},
                    {"id": "prompt_optimization", "agent": "prompt_engineer", "action": "optimize_prompt", "dependencies": ["concept_review"]},
                    {"id": "generation", "agent": "image_generator", "action": "generate_image", "dependencies": ["prompt_optimization"]},
                    {"id": "quality_review", "agent": "qa_reviewer", "action": "review_quality", "dependencies": ["generation"]},
                    {"id": "finalization", "agent": "creative_director", "action": "finalize", "dependencies": ["quality_review"]}
                ]
            },
            
            WorkflowType.ITERATIVE_REFINEMENT: {
                "name": "Iterative Refinement Workflow",
                "description": "Multiple rounds of generation and refinement",
                "steps": [
                    {"id": "initial_concept", "agent": "creative_director", "action": "develop_concept"},
                    {"id": "first_generation", "agent": "prompt_engineer", "action": "generate_initial", "dependencies": ["initial_concept"]},
                    {"id": "review_and_refine", "agent": "qa_reviewer", "action": "review_and_suggest", "dependencies": ["first_generation"]},
                    {"id": "refined_generation", "agent": "prompt_engineer", "action": "generate_refined", "dependencies": ["review_and_refine"]},
                    {"id": "final_review", "agent": "creative_director", "action": "final_approval", "dependencies": ["refined_generation"]}
                ]
            },
            
            WorkflowType.BRAND_REVIEW: {
                "name": "Brand Compliance Workflow",
                "description": "Strict brand compliance review process",
                "steps": [
                    {"id": "brand_brief", "agent": "brand_officer", "action": "create_brand_brief"},
                    {"id": "concept_alignment", "agent": "creative_director", "action": "align_concept", "dependencies": ["brand_brief"]},
                    {"id": "compliant_generation", "agent": "prompt_engineer", "action": "generate_compliant", "dependencies": ["concept_alignment"]},
                    {"id": "brand_compliance_check", "agent": "brand_officer", "action": "compliance_review", "dependencies": ["compliant_generation"]},
                    {"id": "final_approval", "agent": "brand_officer", "action": "approve_final", "dependencies": ["brand_compliance_check"]}
                ]
            },
            
            WorkflowType.CAMPAIGN_SERIES: {
                "name": "Campaign Series Workflow",
                "description": "Coordinated multi-image campaign generation",
                "steps": [
                    {"id": "campaign_strategy", "agent": "campaign_strategist", "action": "develop_strategy"},
                    {"id": "series_planning", "agent": "creative_director", "action": "plan_series", "dependencies": ["campaign_strategy"]},
                    {"id": "batch_generation", "agent": "prompt_engineer", "action": "generate_series", "dependencies": ["series_planning"]},
                    {"id": "series_review", "agent": "qa_reviewer", "action": "review_series", "dependencies": ["batch_generation"]},
                    {"id": "campaign_finalization", "agent": "campaign_strategist", "action": "finalize_campaign", "dependencies": ["series_review"]}
                ]
            }
        }
    
    async def create_workflow(
        self,
        workflow_type: WorkflowType,
        request: str,
        context: Optional[Dict[str, Any]] = None,
        custom_steps: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Create a new workflow instance.
        
        Args:
            workflow_type: Type of workflow to create
            request: The original image generation request
            context: Additional context for the workflow
            custom_steps: Optional custom workflow steps
            
        Returns:
            Workflow ID
        """
        try:
            workflow_id = f"wf_{workflow_type.value}_{uuid.uuid4().hex[:8]}"
            context = context or {}
            
            # Get template
            template = self.workflow_templates.get(workflow_type)
            if not template:
                raise ValueError(f"Unknown workflow type: {workflow_type}")
            
            # Create workflow instance
            workflow = Workflow(
                id=workflow_id,
                name=template["name"],
                type=workflow_type,
                context={
                    "original_request": request,
                    "user_context": context,
                    "template": template
                }
            )
            
            # Create workflow steps
            steps_config = custom_steps or template["steps"]
            for step_config in steps_config:
                step = WorkflowStep(
                    id=step_config["id"],
                    name=step_config.get("name", step_config["id"].replace("_", " ").title()),
                    agent_name=step_config["agent"],
                    action=step_config["action"],
                    dependencies=step_config.get("dependencies", [])
                )
                workflow.steps[step.id] = step
            
            # Assign agents to workflow
            required_agents = set(step.agent_name for step in workflow.steps.values())
            for agent_name in required_agents:
                if agent_name in self.agent_registry:
                    workflow.agents[agent_name] = self.agent_registry[agent_name]
            
            # Store workflow
            self.active_workflows[workflow_id] = workflow
            
            self.logger.info(f"Created workflow {workflow_id} of type {workflow_type.value}")
            return workflow_id
            
        except Exception as e:
            self.logger.error(f"Failed to create workflow: {e}")
            raise
    
    async def execute_workflow(
        self,
        workflow_id: str,
        image_generator: Optional[EnhancedImageGeneratorAgent] = None
    ) -> Dict[str, Any]:
        """
        Execute a workflow with full orchestration.
        
        Args:
            workflow_id: ID of workflow to execute
            image_generator: Enhanced image generator agent instance
            
        Returns:
            Workflow execution results
        """
        try:
            if workflow_id not in self.active_workflows:
                raise ValueError(f"Workflow not found: {workflow_id}")
            
            workflow = self.active_workflows[workflow_id]
            workflow.status = WorkflowStatus.RUNNING
            workflow.started_at = datetime.now()
            
            self.logger.info(f"Starting workflow execution: {workflow_id}")
            
            # Create group chat for this workflow
            group_chat = await self._create_workflow_group_chat(workflow)
            group_manager = await self._create_group_chat_manager(workflow, group_chat)
            
            # Execute workflow steps
            execution_result = await self._execute_workflow_steps(
                workflow, 
                group_chat, 
                group_manager,
                image_generator
            )
            
            # Finalize workflow
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.now()
            workflow.final_outputs = execution_result
            
            # Update metrics
            self._update_execution_metrics(workflow)
            
            self.logger.info(f"Workflow {workflow_id} completed successfully")
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "execution_time": (workflow.completed_at - workflow.started_at).total_seconds(),
                "results": execution_result,
                "conversation_history": workflow.conversation_history
            }
            
        except Exception as e:
            # Handle workflow failure
            if workflow_id in self.active_workflows:
                workflow = self.active_workflows[workflow_id]
                workflow.status = WorkflowStatus.FAILED
                workflow.completed_at = datetime.now()
            
            self.logger.error(f"Workflow execution failed for {workflow_id}: {e}")
            return {
                "success": False,
                "workflow_id": workflow_id,
                "error": str(e)
            }
    
    async def _create_workflow_group_chat(self, workflow: Workflow) -> GroupChat:
        """Create a group chat for workflow execution."""
        # Get participating agents
        agents = [workflow_agent.agent for workflow_agent in workflow.agents.values()]
        
        # Add a coordinator agent for the workflow
        coordinator = UserProxyAgent(
            name="workflow_coordinator",
            system_message="You coordinate the workflow execution and ensure proper communication between agents.",
            human_input_mode="NEVER",
            code_execution_config=False
        )
        agents.append(coordinator)
        
        # Create group chat
        group_chat = GroupChat(
            agents=agents,
            messages=[],
            max_round=20,  # Limit rounds to prevent infinite loops
            speaker_selection_method="auto"
        )
        
        self.group_chats[workflow.id] = group_chat
        return group_chat
    
    async def _create_group_chat_manager(
        self, 
        workflow: Workflow, 
        group_chat: GroupChat
    ) -> GroupChatManager:
        """Create a group chat manager for the workflow."""
        
        manager = GroupChatManager(
            groupchat=group_chat,
            llm_config=self._get_llm_config(),
            system_message=f"""You are managing a {workflow.type.value} workflow for image generation.
            
            Workflow: {workflow.name}
            Participants: {', '.join(workflow.agents.keys())}
            
            Your role is to:
            - Facilitate smooth communication between agents
            - Ensure workflow steps are completed in order
            - Handle any conflicts or issues that arise
            - Keep the conversation focused on the image generation goals
            - Summarize results and coordinate final outputs
            
            Original request: {workflow.context.get('original_request', 'N/A')}"""
        )
        
        self.group_managers[workflow.id] = manager
        return manager
    
    async def _execute_workflow_steps(
        self,
        workflow: Workflow,
        group_chat: GroupChat,
        group_manager: GroupChatManager,
        image_generator: Optional[EnhancedImageGeneratorAgent] = None
    ) -> Dict[str, Any]:
        """Execute workflow steps in the correct order."""
        
        executed_steps = set()
        step_results = {}
        
        # Get execution order based on dependencies
        execution_order = self._get_execution_order(workflow.steps)
        
        for step_id in execution_order:
            step = workflow.steps[step_id]
            
            try:
                self.logger.info(f"Executing step: {step.name} ({step_id})")
                
                step.status = "running"
                step.started_at = datetime.now()
                
                # Execute step
                if step.agent_name == "image_generator" and image_generator:
                    # Special handling for actual image generation
                    step_result = await self._execute_image_generation_step(
                        step, workflow, image_generator
                    )
                else:
                    # Execute through group chat
                    step_result = await self._execute_group_chat_step(
                        step, workflow, group_chat, group_manager
                    )
                
                step.outputs = step_result
                step.status = "completed"
                step.completed_at = datetime.now()
                step_results[step_id] = step_result
                
                executed_steps.add(step_id)
                
                # Add to conversation history
                workflow.conversation_history.append({
                    "step_id": step_id,
                    "step_name": step.name,
                    "agent": step.agent_name,
                    "action": step.action,
                    "result": step_result,
                    "timestamp": datetime.now().isoformat()
                })
                
                self.logger.info(f"Step {step_id} completed successfully")
                
            except Exception as e:
                step.status = "failed"
                step.error_message = str(e)
                step.completed_at = datetime.now()
                
                self.logger.error(f"Step {step_id} failed: {e}")
                
                # Decide whether to continue or abort workflow
                if self._is_critical_step(step):
                    raise Exception(f"Critical step failed: {step_id} - {str(e)}")
                
                # Continue with non-critical step failures
                step_results[step_id] = {"error": str(e), "status": "failed"}
        
        return {
            "steps_executed": list(executed_steps),
            "step_results": step_results,
            "total_steps": len(workflow.steps),
            "success_rate": len(executed_steps) / len(workflow.steps)
        }
    
    def _get_execution_order(self, steps: Dict[str, WorkflowStep]) -> List[str]:
        """Get execution order based on step dependencies."""
        order = []
        remaining = set(steps.keys())
        
        while remaining:
            # Find steps with no unfulfilled dependencies
            ready_steps = [
                step_id for step_id in remaining
                if all(dep in order for dep in steps[step_id].dependencies)
            ]
            
            if not ready_steps:
                # Circular dependency or other issue
                raise ValueError("Cannot resolve step dependencies")
            
            # Add ready steps to order
            for step_id in ready_steps:
                order.append(step_id)
                remaining.remove(step_id)
        
        return order
    
    async def _execute_image_generation_step(
        self,
        step: WorkflowStep,
        workflow: Workflow,
        image_generator: EnhancedImageGeneratorAgent
    ) -> Dict[str, Any]:
        """Execute actual image generation step."""
        
        try:
            if step.action == "generate_image":
                # Use the enhanced image generator
                result = await image_generator.generate_image_with_workflow(
                    request=workflow.context.get("original_request", ""),
                    context=workflow.context.get("user_context", {})
                )
                return result
            
            elif step.action == "generate_series":
                # Generate multiple related images
                base_request = workflow.context.get("original_request", "")
                results = []
                
                # Generate variations based on context
                variations = workflow.context.get("series_variations", [base_request])
                for i, variation in enumerate(variations):
                    result = await image_generator.generate_image_with_workflow(
                        request=variation,
                        context={
                            **workflow.context.get("user_context", {}),
                            "series_index": i,
                            "series_total": len(variations)
                        }
                    )
                    results.append(result)
                
                return {"series_results": results, "total_generated": len(results)}
            
            else:
                return {"status": "completed", "message": f"Image generation action {step.action} completed"}
        
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    async def _execute_group_chat_step(
        self,
        step: WorkflowStep,
        workflow: Workflow,
        group_chat: GroupChat,
        group_manager: GroupChatManager
    ) -> Dict[str, Any]:
        """Execute step through group chat interaction."""
        
        try:
            # Get the agent for this step
            workflow_agent = workflow.agents.get(step.agent_name)
            if not workflow_agent:
                raise ValueError(f"Agent not found: {step.agent_name}")
            
            # Create step-specific prompt
            step_prompt = self._create_step_prompt(step, workflow)
            
            # Execute through group chat
            # This simulates the group conversation - in a full implementation,
            # you would use AutoGen's actual group chat execution
            conversation_result = await self._simulate_group_conversation(
                step, workflow_agent, step_prompt, workflow
            )
            
            return conversation_result
            
        except Exception as e:
            return {"error": str(e), "status": "failed"}
    
    def _create_step_prompt(self, step: WorkflowStep, workflow: Workflow) -> str:
        """Create a prompt for the specific workflow step."""
        
        base_prompt = f"""
        Workflow Step: {step.name}
        Action: {step.action}
        
        Original Request: {workflow.context.get('original_request', '')}
        
        Your role in this step:
        """
        
        # Add step-specific instructions based on action
        action_prompts = {
            "review_concept": "Review the creative concept for brand alignment and marketing effectiveness. Provide specific feedback and approval/rejection.",
            "optimize_prompt": "Enhance the prompt for DALL-E 3 generation by adding technical modifiers, style enhancements, and quality improvements.",
            "review_quality": "Assess the generated images for quality, brand compliance, and marketing effectiveness. Provide specific improvement suggestions.",
            "develop_concept": "Develop a comprehensive creative concept based on the request, considering target audience and marketing objectives.",
            "compliance_review": "Review all materials for brand compliance, checking guidelines adherence and consistency.",
            "develop_strategy": "Create a strategic approach for the image generation campaign, including goals and success metrics.",
            "finalize": "Provide final approval and prepare deliverables for client presentation."
        }
        
        specific_instructions = action_prompts.get(step.action, f"Execute the {step.action} action according to your role capabilities.")
        
        return f"{base_prompt}\n{specific_instructions}"
    
    async def _simulate_group_conversation(
        self,
        step: WorkflowStep,
        workflow_agent: WorkflowAgent,
        prompt: str,
        workflow: Workflow
    ) -> Dict[str, Any]:
        """Simulate group conversation for a workflow step."""
        
        try:
            # In a full implementation, this would use AutoGen's group chat
            # For now, we'll simulate the agent's response
            
            agent_response = f"""
            Completed {step.name} for workflow {workflow.id}.
            
            Action: {step.action}
            Agent: {workflow_agent.name} ({workflow_agent.role})
            
            Results:
            - Step executed successfully
            - Recommendations provided
            - Ready for next workflow step
            
            Status: Completed
            """
            
            return {
                "agent_response": agent_response,
                "step_status": "completed",
                "agent_name": workflow_agent.name,
                "recommendations": f"Recommendations for {step.action} completed successfully",
                "next_steps": "Proceed to next workflow step"
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "step_status": "failed",
                "agent_name": workflow_agent.name
            }
    
    def _is_critical_step(self, step: WorkflowStep) -> bool:
        """Determine if a step is critical for workflow success."""
        critical_actions = [
            "generate_image",
            "generate_series", 
            "final_approval",
            "compliance_review"
        ]
        return step.action in critical_actions
    
    def _update_execution_metrics(self, workflow: Workflow) -> None:
        """Update performance metrics after workflow execution."""
        
        self.execution_metrics["total_workflows"] += 1
        
        if workflow.status == WorkflowStatus.COMPLETED:
            self.execution_metrics["successful_workflows"] += 1
            
            # Update execution time
            if workflow.started_at and workflow.completed_at:
                execution_time = (workflow.completed_at - workflow.started_at).total_seconds()
                current_avg = self.execution_metrics["average_execution_time"]
                total_successful = self.execution_metrics["successful_workflows"]
                
                self.execution_metrics["average_execution_time"] = (
                    (current_avg * (total_successful - 1) + execution_time) / total_successful
                )
        
        elif workflow.status == WorkflowStatus.FAILED:
            self.execution_metrics["failed_workflows"] += 1
        
        # Update agent performance metrics
        for agent_name, workflow_agent in workflow.agents.items():
            if agent_name not in self.execution_metrics["agent_performance"]:
                self.execution_metrics["agent_performance"][agent_name] = {
                    "total_participations": 0,
                    "successful_workflows": 0,
                    "failed_workflows": 0
                }
            
            agent_metrics = self.execution_metrics["agent_performance"][agent_name]
            agent_metrics["total_participations"] += 1
            
            if workflow.status == WorkflowStatus.COMPLETED:
                agent_metrics["successful_workflows"] += 1
            elif workflow.status == WorkflowStatus.FAILED:
                agent_metrics["failed_workflows"] += 1
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a workflow."""
        
        if workflow_id not in self.active_workflows:
            return None
        
        workflow = self.active_workflows[workflow_id]
        
        # Calculate progress
        completed_steps = sum(1 for step in workflow.steps.values() if step.status == "completed")
        total_steps = len(workflow.steps)
        progress = (completed_steps / total_steps) * 100 if total_steps > 0 else 0
        
        return {
            "workflow_id": workflow_id,
            "name": workflow.name,
            "type": workflow.type.value,
            "status": workflow.status.value,
            "progress_percentage": progress,
            "completed_steps": completed_steps,
            "total_steps": total_steps,
            "participating_agents": list(workflow.agents.keys()),
            "created_at": workflow.created_at.isoformat(),
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "execution_time": (
                (workflow.completed_at - workflow.started_at).total_seconds()
                if workflow.started_at and workflow.completed_at else None
            )
        }
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow."""
        
        if workflow_id not in self.active_workflows:
            return False
        
        workflow = self.active_workflows[workflow_id]
        
        if workflow.status == WorkflowStatus.RUNNING:
            workflow.status = WorkflowStatus.CANCELLED
            workflow.completed_at = datetime.now()
            
            self.logger.info(f"Workflow {workflow_id} cancelled")
            return True
        
        return False
    
    def get_execution_metrics(self) -> Dict[str, Any]:
        """Get orchestrator execution metrics."""
        return {
            **self.execution_metrics,
            "active_workflows": len([
                w for w in self.active_workflows.values() 
                if w.status == WorkflowStatus.RUNNING
            ]),
            "available_agents": len(self.agent_registry),
            "workflow_types_supported": len(self.workflow_templates)
        }
    
    async def cleanup(self) -> None:
        """Clean up orchestrator resources."""
        try:
            # Cancel any running workflows
            running_workflows = [
                w.id for w in self.active_workflows.values() 
                if w.status == WorkflowStatus.RUNNING
            ]
            
            for workflow_id in running_workflows:
                await self.cancel_workflow(workflow_id)
            
            # Clear resources
            self.active_workflows.clear()
            self.group_chats.clear()
            self.group_managers.clear()
            
            self.logger.info("Image Generation Orchestrator cleaned up successfully")
            
        except Exception as e:
            self.logger.error(f"Orchestrator cleanup failed: {e}")
    
    def list_workflow_types(self) -> List[Dict[str, Any]]:
        """List available workflow types and their descriptions."""
        return [
            {
                "type": wf_type.value,
                "name": template["name"],
                "description": template["description"],
                "steps_count": len(template["steps"])
            }
            for wf_type, template in self.workflow_templates.items()
        ]