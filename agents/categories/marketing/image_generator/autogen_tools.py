"""
AutoGen-Specific Tools and Utilities for Enhanced Image Generation Workflows.
Provides specialized tools that leverage AutoGen's unique capabilities for 
conversation management, function calling, and multi-agent coordination.
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
from autogen.agentchat.conversable_agent import ConversableAgent
from autogen.code_utils import execute_code
from loguru import logger

from src.log_service import get_logger


class AutoGenImageTools:
    """
    AutoGen-specific tools for image generation workflows.
    Demonstrates advanced AutoGen patterns including function calling,
    message handling, and conversation orchestration.
    """
    
    @staticmethod
    def create_function_calling_schema() -> Dict[str, Any]:
        """
        Create comprehensive function calling schemas for image generation.
        Demonstrates AutoGen's function calling capabilities.
        """
        
        return {
            "generate_marketing_image": {
                "type": "function",
                "function": {
                    "name": "generate_marketing_image",
                    "description": "Generate marketing images using advanced AI with collaborative review",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "Detailed description of the image to generate"
                            },
                            "marketing_context": {
                                "type": "object",
                                "properties": {
                                    "campaign_type": {"type": "string", "enum": ["social_media", "web_banner", "print", "advertisement"]},
                                    "target_audience": {"type": "string", "description": "Description of target audience"},
                                    "brand_guidelines": {"type": "string", "description": "Brand guidelines to follow"},
                                    "call_to_action": {"type": "string", "description": "Desired call to action"}
                                }
                            },
                            "technical_specs": {
                                "type": "object", 
                                "properties": {
                                    "size": {"type": "string", "enum": ["1024x1024", "1024x1792", "1792x1024"]},
                                    "quality": {"type": "string", "enum": ["standard", "hd"]},
                                    "style": {"type": "string", "enum": ["vivid", "natural"]},
                                    "quantity": {"type": "integer", "minimum": 1, "maximum": 4}
                                }
                            },
                            "workflow_options": {
                                "type": "object",
                                "properties": {
                                    "enable_collaboration": {"type": "boolean", "description": "Enable multi-agent collaboration"},
                                    "require_brand_review": {"type": "boolean", "description": "Require brand compliance review"},
                                    "enable_iterative_refinement": {"type": "boolean", "description": "Allow iterative improvements"},
                                    "consensus_threshold": {"type": "number", "minimum": 0.5, "maximum": 1.0}
                                }
                            }
                        },
                        "required": ["prompt", "marketing_context", "technical_specs"]
                    }
                }
            },
            
            "start_collaborative_review": {
                "type": "function",
                "function": {
                    "name": "start_collaborative_review",
                    "description": "Start collaborative review process with multiple specialist agents",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "review_subject": {"type": "string", "description": "What is being reviewed"},
                            "review_criteria": {"type": "array", "items": {"type": "string"}},
                            "participants": {"type": "array", "items": {"type": "string"}},
                            "review_type": {"type": "string", "enum": ["concept_review", "quality_assessment", "brand_compliance", "final_approval"]}
                        },
                        "required": ["review_subject", "participants", "review_type"]
                    }
                }
            },
            
            "coordinate_agent_workflow": {
                "type": "function", 
                "function": {
                    "name": "coordinate_agent_workflow",
                    "description": "Coordinate complex multi-agent workflows with dependencies",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "workflow_type": {"type": "string", "enum": ["sequential", "parallel", "conditional", "iterative"]},
                            "workflow_steps": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "step_id": {"type": "string"},
                                        "agent_name": {"type": "string"},
                                        "action": {"type": "string"},
                                        "dependencies": {"type": "array", "items": {"type": "string"}},
                                        "timeout_seconds": {"type": "integer", "minimum": 30, "maximum": 300}
                                    }
                                }
                            },
                            "success_criteria": {"type": "string", "description": "Criteria for workflow success"},
                            "failure_handling": {"type": "string", "enum": ["abort", "retry", "skip", "escalate"]}
                        },
                        "required": ["workflow_type", "workflow_steps"]
                    }
                }
            },
            
            "manage_conversation_context": {
                "type": "function",
                "function": {
                    "name": "manage_conversation_context", 
                    "description": "Manage conversation context and memory across long interactions",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "context_action": {"type": "string", "enum": ["compress", "summarize", "extract_key_points", "maintain_focus"]},
                            "context_scope": {"type": "string", "enum": ["current_conversation", "session_history", "project_context"]},
                            "retention_policy": {
                                "type": "object",
                                "properties": {
                                    "keep_recent_messages": {"type": "integer", "minimum": 5, "maximum": 50},
                                    "preserve_decisions": {"type": "boolean"},
                                    "compress_technical_details": {"type": "boolean"}
                                }
                            }
                        },
                        "required": ["context_action", "context_scope"]
                    }
                }
            },
            
            "facilitate_consensus_building": {
                "type": "function",
                "function": {
                    "name": "facilitate_consensus_building",
                    "description": "Facilitate consensus building among multiple agents",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "consensus_topic": {"type": "string", "description": "Topic requiring consensus"},
                            "participants": {"type": "array", "items": {"type": "string"}},
                            "consensus_method": {"type": "string", "enum": ["unanimous", "majority", "weighted", "delegated"]},
                            "voting_weights": {
                                "type": "object",
                                "description": "Agent voting weights for weighted consensus"
                            },
                            "timeout_minutes": {"type": "integer", "minimum": 5, "maximum": 60}
                        },
                        "required": ["consensus_topic", "participants", "consensus_method"]
                    }
                }
            }
        }
    
    @staticmethod
    def register_functions_with_agent(
        agent: ConversableAgent, 
        function_implementations: Dict[str, Callable]
    ) -> None:
        """
        Register functions with an AutoGen agent using proper patterns.
        Demonstrates best practices for function registration.
        """
        
        schemas = AutoGenImageTools.create_function_calling_schema()
        
        for func_name, func_impl in function_implementations.items():
            if func_name in schemas:
                # Register for execution (actual function call)
                agent.register_for_execution(func_name)(func_impl)
                
                # Register for LLM (function schema)
                agent.register_for_llm(func_name)(lambda: schemas[func_name])
    
    @staticmethod
    def create_enhanced_system_message(
        role: str, 
        specialties: List[str], 
        context: Dict[str, Any]
    ) -> str:
        """
        Create enhanced system messages that leverage AutoGen's capabilities.
        """
        
        base_templates = {
            "image_generator_coordinator": """You are an Image Generation Coordinator specializing in orchestrating complex multi-agent image creation workflows.

Your core responsibilities:
- Coordinate between specialist agents (Creative Directors, Prompt Engineers, QA Reviewers)
- Manage workflow execution and ensure quality outcomes
- Facilitate communication and consensus building
- Handle function calls for image generation and review processes

Capabilities you can utilize:
{capabilities}

Available functions:
{available_functions}

Your approach:
1. Analyze user requests comprehensively
2. Determine the optimal workflow and participants
3. Coordinate function calls and agent interactions
4. Ensure quality through collaborative review
5. Deliver exceptional marketing images

Context: {context}

Always maintain professional communication while leveraging your coordination and technical capabilities.""",
            
            "creative_director": """You are a Creative Director with expertise in visual marketing strategy and brand development.

Your specialties: {specialties}

Your role in AutoGen workflows:
- Provide creative vision and strategic direction
- Evaluate concepts for brand alignment and marketing effectiveness
- Participate in collaborative reviews and consensus building
- Make final creative decisions when designated

Available functions you can call:
{available_functions}

Your decision-making approach:
1. Consider brand alignment and marketing objectives
2. Evaluate creative merit and visual impact
3. Ensure consistency with campaign goals
4. Provide constructive feedback and direction
5. Facilitate consensus when needed

Context: {context}

Use your creative expertise to drive exceptional visual outcomes through collaborative workflows.""",
            
            "prompt_engineer": """You are a Prompt Engineering Specialist with deep expertise in DALL-E 3 optimization and AI image generation.

Your specialties: {specialties}

Your technical capabilities:
- Optimize prompts for maximum DALL-E 3 effectiveness
- Understand technical parameters and their impact
- Enhance descriptions with quality modifiers
- Adapt prompts based on marketing requirements

Available functions:
{available_functions}

Your optimization process:
1. Analyze original prompts for improvement opportunities
2. Add technical modifiers and style enhancements
3. Consider marketing context and target audience
4. Optimize for specific use cases and platforms
5. Collaborate with other agents for best results

Context: {context}

Transform user ideas into optimized prompts that produce exceptional marketing visuals.""",
            
            "qa_reviewer": """You are a Quality Assurance Specialist focused on ensuring exceptional standards for marketing visuals.

Your specialties: {specialties}

Your QA responsibilities:
- Evaluate generated images for quality and effectiveness
- Provide specific improvement recommendations
- Check compliance with brand and marketing standards
- Facilitate iterative improvement processes

Available functions:
{available_functions}

Your review methodology:
1. Assess visual quality and technical execution
2. Evaluate marketing effectiveness and audience appeal
3. Check brand compliance and consistency
4. Provide specific, actionable feedback
5. Collaborate on improvements and refinements

Context: {context}

Ensure all visual content meets professional marketing standards through thorough review and collaborative improvement."""
        }
        
        template = base_templates.get(role, base_templates["image_generator_coordinator"])
        
        # Get available functions based on role
        available_functions = AutoGenImageTools._get_role_specific_functions(role)
        
        # Format capabilities
        capabilities = AutoGenImageTools._format_capabilities_for_role(role, specialties)
        
        return template.format(
            specialties=", ".join(specialties),
            capabilities=capabilities,
            available_functions=available_functions,
            context=json.dumps(context, indent=2)
        )
    
    @staticmethod
    def _get_role_specific_functions(role: str) -> str:
        """Get role-specific available functions."""
        
        function_access = {
            "image_generator_coordinator": [
                "generate_marketing_image",
                "coordinate_agent_workflow", 
                "manage_conversation_context",
                "start_collaborative_review",
                "facilitate_consensus_building"
            ],
            "creative_director": [
                "start_collaborative_review",
                "facilitate_consensus_building"
            ],
            "prompt_engineer": [
                "generate_marketing_image"
            ],
            "qa_reviewer": [
                "start_collaborative_review"
            ]
        }
        
        functions = function_access.get(role, [])
        return "\\n".join(f"- {func}" for func in functions)
    
    @staticmethod
    def _format_capabilities_for_role(role: str, specialties: List[str]) -> str:
        """Format capabilities description for role."""
        
        capability_descriptions = {
            "image_generator_coordinator": "Multi-agent workflow coordination, function call management, conversation orchestration",
            "creative_director": "Creative vision, strategic direction, brand alignment, decision leadership",
            "prompt_engineer": "Prompt optimization, technical enhancement, DALL-E expertise",
            "qa_reviewer": "Quality assessment, improvement feedback, standard compliance"
        }
        
        base_capabilities = capability_descriptions.get(role, "Specialized agent capabilities")
        specialty_text = f"Specialized in: {', '.join(specialties)}" if specialties else ""
        
        return f"{base_capabilities}. {specialty_text}"


class AutoGenConversationPatterns:
    """
    Collection of proven conversation patterns for AutoGen multi-agent systems.
    """
    
    @staticmethod
    async def coordinate_sequential_workflow(
        agents: List[ConversableAgent],
        workflow_steps: List[Dict[str, Any]],
        initial_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Coordinate a sequential workflow between agents.
        Demonstrates sequential agent coordination patterns.
        """
        
        results = []
        current_context = initial_context.copy()
        
        for i, step in enumerate(workflow_steps):
            step_id = step.get("step_id", f"step_{i}")
            agent_name = step.get("agent_name")
            action = step.get("action", "process")
            
            # Find the agent
            agent = next((a for a in agents if a.name == agent_name), None)
            if not agent:
                results.append({
                    "step_id": step_id,
                    "status": "failed",
                    "error": f"Agent not found: {agent_name}"
                })
                continue
            
            # Prepare step context
            step_context = {
                **current_context,
                "step_info": step,
                "previous_results": results[-1] if results else None
            }
            
            # Create step prompt
            step_prompt = f"""
            Workflow Step: {step_id}
            Action: {action}
            
            Context: {json.dumps(step_context, indent=2)}
            
            Please execute this step and provide results for the next step.
            """
            
            try:
                # Execute step
                response = await agent.a_generate_reply(
                    messages=[{"role": "user", "content": step_prompt}],
                    sender=agent
                )
                
                step_result = {
                    "step_id": step_id,
                    "agent": agent_name,
                    "action": action,
                    "status": "completed",
                    "response": response,
                    "timestamp": datetime.now().isoformat()
                }
                
                results.append(step_result)
                
                # Update context for next step
                current_context["last_step_result"] = step_result
                
            except Exception as e:
                step_result = {
                    "step_id": step_id,
                    "agent": agent_name,
                    "status": "failed",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                results.append(step_result)
        
        return {
            "workflow_results": results,
            "final_context": current_context,
            "success_rate": len([r for r in results if r.get("status") == "completed"]) / len(results)
        }
    
    @staticmethod
    async def facilitate_group_consensus(
        group_chat: GroupChat,
        group_manager: GroupChatManager,
        consensus_topic: str,
        consensus_method: str = "majority"
    ) -> Dict[str, Any]:
        """
        Facilitate consensus building in a group chat.
        Demonstrates AutoGen group consensus patterns.
        """
        
        consensus_prompt = f"""
        We need to reach consensus on: {consensus_topic}
        
        Consensus Method: {consensus_method}
        Participants: {', '.join([agent.name for agent in group_chat.agents])}
        
        Process:
        1. Each participant: State your position clearly
        2. Discussion: Address different viewpoints
        3. Convergence: Find common ground
        4. Decision: Reach {consensus_method} consensus
        
        Please begin by stating your positions on: {consensus_topic}
        """
        
        # Initiate consensus conversation
        conversation_result = await group_manager.a_initiate_chat(
            message=consensus_prompt,
            clear_history=False
        )
        
        # Analyze consensus results
        consensus_analysis = AutoGenConversationPatterns._analyze_consensus_conversation(
            conversation_result,
            consensus_method
        )
        
        return consensus_analysis
    
    @staticmethod
    def _analyze_consensus_conversation(
        conversation_result: Any,
        consensus_method: str
    ) -> Dict[str, Any]:
        """Analyze consensus conversation results."""
        
        # Extract messages from conversation
        messages = getattr(conversation_result, 'chat_history', [])
        
        # Simple consensus analysis (in practice, would be more sophisticated)
        participant_positions = {}
        consensus_indicators = []
        
        for msg in messages:
            sender = msg.get('name', 'unknown')
            content = msg.get('content', '').lower()
            
            # Track positions
            if 'agree' in content or 'support' in content:
                consensus_indicators.append((sender, 'positive'))
            elif 'disagree' in content or 'oppose' in content:
                consensus_indicators.append((sender, 'negative'))
        
        # Determine consensus outcome
        positive_votes = len([x for x in consensus_indicators if x[1] == 'positive'])
        negative_votes = len([x for x in consensus_indicators if x[1] == 'negative'])
        total_participants = len(set(x[0] for x in consensus_indicators))
        
        consensus_reached = False
        if consensus_method == "majority":
            consensus_reached = positive_votes > negative_votes
        elif consensus_method == "unanimous":
            consensus_reached = negative_votes == 0 and positive_votes > 0
        
        return {
            "consensus_reached": consensus_reached,
            "consensus_method": consensus_method,
            "positive_votes": positive_votes,
            "negative_votes": negative_votes,
            "total_participants": total_participants,
            "consensus_ratio": positive_votes / max(total_participants, 1),
            "conversation_length": len(messages)
        }
    
    @staticmethod
    async def manage_conversation_memory(
        agent: ConversableAgent,
        conversation_history: List[Dict],
        memory_policy: Dict[str, Any]
    ) -> List[Dict]:
        """
        Manage conversation memory using AutoGen patterns.
        Demonstrates context compression and memory management.
        """
        
        max_messages = memory_policy.get("max_messages", 20)
        preserve_decisions = memory_policy.get("preserve_decisions", True)
        compress_technical = memory_policy.get("compress_technical", True)
        
        if len(conversation_history) <= max_messages:
            return conversation_history
        
        # Separate important messages
        important_messages = []
        regular_messages = []
        
        for msg in conversation_history:
            content = msg.get('content', '').lower()
            
            # Identify important messages
            is_important = (
                preserve_decisions and any(word in content for word in ['decision', 'approve', 'consensus']) or
                'error' in content or
                'final' in content
            )
            
            if is_important:
                important_messages.append(msg)
            else:
                regular_messages.append(msg)
        
        # Keep recent messages and important messages
        recent_count = max_messages - len(important_messages)
        recent_messages = regular_messages[-recent_count:] if recent_count > 0 else []
        
        # Compress technical details if enabled
        if compress_technical:
            recent_messages = AutoGenConversationPatterns._compress_technical_messages(recent_messages)
        
        # Combine and sort by timestamp
        final_messages = important_messages + recent_messages
        final_messages.sort(key=lambda x: x.get('timestamp', ''))
        
        return final_messages
    
    @staticmethod
    def _compress_technical_messages(messages: List[Dict]) -> List[Dict]:
        """Compress technical details in messages."""
        
        compressed = []
        
        for msg in messages:
            content = msg.get('content', '')
            
            # Identify technical messages
            if len(content) > 300 and any(word in content.lower() for word in ['parameter', 'configuration', 'technical', 'implementation']):
                # Create compressed version
                sentences = content.split('.')[:3]  # Keep first 3 sentences
                compressed_content = '. '.join(sentences) + ' [Technical details compressed]'
                
                compressed_msg = {**msg, 'content': compressed_content}
                compressed.append(compressed_msg)
            else:
                compressed.append(msg)
        
        return compressed


class AutoGenErrorHandling:
    """
    Error handling patterns for AutoGen multi-agent systems.
    """
    
    @staticmethod
    def create_resilient_agent_wrapper(
        base_agent: ConversableAgent,
        retry_config: Dict[str, Any]
    ) -> ConversableAgent:
        """
        Create a resilient agent wrapper with error handling.
        """
        
        max_retries = retry_config.get("max_retries", 3)
        retry_delay = retry_config.get("retry_delay", 1.0)
        fallback_response = retry_config.get("fallback_response", "I encountered an error and need to try again.")
        
        # Store original generate_reply method
        original_generate_reply = base_agent.generate_reply
        
        async def resilient_generate_reply(messages, sender=None, **kwargs):
            """Resilient reply generation with retries."""
            
            for attempt in range(max_retries + 1):
                try:
                    return await original_generate_reply(messages, sender, **kwargs)
                
                except Exception as e:
                    if attempt < max_retries:
                        logger.warning(f"Agent {base_agent.name} attempt {attempt + 1} failed: {e}")
                        await asyncio.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                        continue
                    else:
                        logger.error(f"Agent {base_agent.name} failed after {max_retries} retries: {e}")
                        return fallback_response
        
        # Replace the method
        base_agent.a_generate_reply = resilient_generate_reply
        
        return base_agent
    
    @staticmethod
    def create_circuit_breaker_for_group_chat(
        group_chat: GroupChat,
        failure_threshold: int = 3,
        recovery_timeout: int = 60
    ) -> GroupChat:
        """
        Add circuit breaker pattern to group chat.
        """
        
        # Track failures
        group_chat.failure_count = 0
        group_chat.circuit_open = False
        group_chat.last_failure_time = None
        
        # Store original methods
        original_select_speaker = group_chat.select_speaker
        
        def circuit_breaker_select_speaker(*args, **kwargs):
            """Select speaker with circuit breaker protection."""
            
            # Check if circuit is open and should be reset
            if group_chat.circuit_open:
                if (datetime.now() - group_chat.last_failure_time).seconds > recovery_timeout:
                    group_chat.circuit_open = False
                    group_chat.failure_count = 0
                    logger.info(f"Circuit breaker reset for group chat")
                else:
                    logger.warning("Circuit breaker is open, blocking speaker selection")
                    return None
            
            try:
                result = original_select_speaker(*args, **kwargs)
                # Reset failure count on success
                if group_chat.failure_count > 0:
                    group_chat.failure_count = 0
                return result
                
            except Exception as e:
                group_chat.failure_count += 1
                logger.error(f"Speaker selection failed (attempt {group_chat.failure_count}): {e}")
                
                if group_chat.failure_count >= failure_threshold:
                    group_chat.circuit_open = True
                    group_chat.last_failure_time = datetime.now()
                    logger.warning(f"Circuit breaker opened after {failure_threshold} failures")
                
                raise
        
        group_chat.select_speaker = circuit_breaker_select_speaker
        return group_chat


class AutoGenPerformanceOptimization:
    """
    Performance optimization utilities for AutoGen systems.
    """
    
    @staticmethod
    def create_performance_monitoring_wrapper(
        agent: ConversableAgent,
        metrics_collector: Optional[Dict[str, Any]] = None
    ) -> ConversableAgent:
        """
        Add performance monitoring to an agent.
        """
        
        if metrics_collector is None:
            metrics_collector = {
                "total_calls": 0,
                "total_time": 0.0,
                "average_time": 0.0,
                "error_count": 0
            }
        
        # Store original method
        original_generate_reply = agent.a_generate_reply
        
        async def monitored_generate_reply(messages, sender=None, **kwargs):
            """Generate reply with performance monitoring."""
            
            start_time = datetime.now()
            
            try:
                result = await original_generate_reply(messages, sender, **kwargs)
                
                # Update success metrics
                end_time = datetime.now()
                execution_time = (end_time - start_time).total_seconds()
                
                metrics_collector["total_calls"] += 1
                metrics_collector["total_time"] += execution_time
                metrics_collector["average_time"] = metrics_collector["total_time"] / metrics_collector["total_calls"]
                
                return result
                
            except Exception as e:
                # Update error metrics
                metrics_collector["error_count"] += 1
                raise
        
        agent.a_generate_reply = monitored_generate_reply
        agent.performance_metrics = metrics_collector
        
        return agent
    
    @staticmethod
    def optimize_group_chat_for_performance(
        group_chat: GroupChat,
        optimization_config: Dict[str, Any]
    ) -> GroupChat:
        """
        Optimize group chat for better performance.
        """
        
        # Set reasonable limits
        max_rounds = optimization_config.get("max_rounds", 20)
        message_limit = optimization_config.get("message_limit", 100)
        speaker_timeout = optimization_config.get("speaker_timeout", 30)
        
        group_chat.max_round = max_rounds
        
        # Add message pruning
        original_append = group_chat.messages.append
        
        def limited_append(message):
            """Append message with size limits."""
            if len(group_chat.messages) >= message_limit:
                # Remove oldest messages, keep recent and important ones
                important_messages = [
                    msg for msg in group_chat.messages[-10:]
                    if any(word in str(msg).lower() for word in ['decision', 'error', 'important'])
                ]
                recent_messages = group_chat.messages[-(message_limit//2):]
                group_chat.messages = important_messages + recent_messages
            
            return original_append(message)
        
        group_chat.messages.append = limited_append
        
        return group_chat