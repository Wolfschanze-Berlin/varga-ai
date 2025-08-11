"""
Comprehensive Usage Examples for Enhanced AutoGen Image Generation Agents.
Demonstrates real-world scenarios showcasing advanced AutoGen patterns including:
- Multi-agent collaboration workflows
- Group chat management and conversation orchestration
- Complex function calling patterns
- Consensus building and decision making
- Error handling and resilience patterns
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from datetime import datetime

from autogen import (
    ConversableAgent,
    AssistantAgent,
    UserProxyAgent,
    GroupChat,
    GroupChatManager
)

from .enhanced_agent import EnhancedImageGeneratorAgent, ImageGenerationState, ImageRequest
from .workflow_orchestrator import ImageGenerationOrchestrator, WorkflowType
from .autogen_conversation_manager import AutoGenConversationManager, ConversationState
from .autogen_tools import AutoGenImageTools, AutoGenConversationPatterns
from agents.base.base_agent import AgentConfig
from src.log_service import get_logger


logger = get_logger("usage_examples")


class AutoGenImageGenerationExamples:
    """
    Comprehensive examples demonstrating AutoGen image generation capabilities.
    """
    
    def __init__(self):
        self.logger = get_logger("autogen_examples")
        
    # === Example 1: Basic Enhanced Agent Usage ===
    
    async def example_1_basic_enhanced_agent(self):
        """
        Example 1: Basic usage of EnhancedImageGeneratorAgent
        Demonstrates enhanced conversation patterns and workflow coordination.
        """
        
        print("\\n=== Example 1: Basic Enhanced Agent Usage ===\\n")
        
        # Create enhanced agent
        config = AgentConfig(
            name="enhanced_image_generator",
            description="Enhanced marketing image generator with AutoGen capabilities",
            category="marketing",
            system_message=AutoGenImageTools.create_enhanced_system_message(
                role="image_generator_coordinator",
                specialties=["image_generation", "workflow_coordination", "quality_assurance"],
                context={"example_type": "basic_usage", "user_level": "beginner"}
            )
        )
        
        agent = EnhancedImageGeneratorAgent(config)
        await agent.initialize()
        
        # Example conversations showing enhanced capabilities
        test_requests = [
            "Create a professional social media image for a tech startup launch",
            "I need help generating a series of images for a summer campaign",
            "Can you start a collaborative workflow to create website banners?"
        ]
        
        for i, request in enumerate(test_requests, 1):
            print(f"\\n--- Test Request {i}: {request} ---\\n")
            
            # Execute with enhanced agent
            response = await agent.execute(request, context={"session_id": f"example_1_{i}"})
            
            print(f"Response: {response.message}")
            print(f"Success: {response.success}")
            if response.execution_time_ms:
                print(f"Execution Time: {response.execution_time_ms:.1f}ms")
        
        # Show agent metrics
        metrics = agent.get_metrics()
        print(f"\\n--- Agent Performance Metrics ---")
        print(json.dumps(metrics, indent=2))
        
        await agent.cleanup()
        return {"status": "completed", "agent_metrics": metrics}
    
    # === Example 2: Multi-Agent Workflow Orchestration ===
    
    async def example_2_workflow_orchestration(self):
        """
        Example 2: Advanced workflow orchestration with multiple specialized agents
        Demonstrates complex multi-agent coordination patterns.
        """
        
        print("\\n=== Example 2: Multi-Agent Workflow Orchestration ===\\n")
        
        # Create workflow orchestrator
        orchestrator_config = {
            "max_concurrent_workflows": 5,
            "agent_timeout": 60,
            "performance_monitoring": True
        }
        
        orchestrator = ImageGenerationOrchestrator(orchestrator_config)
        await orchestrator.setup()
        
        # Create enhanced image generator
        agent_config = AgentConfig(
            name="workflow_coordinator",
            description="Workflow coordinating image generator", 
            category="marketing",
            system_message=AutoGenImageTools.create_enhanced_system_message(
                role="image_generator_coordinator",
                specialties=["workflow_coordination", "multi_agent_communication"],
                context={"workflow_type": "collaborative"}
            )
        )
        
        image_agent = EnhancedImageGeneratorAgent(agent_config)
        await image_agent.initialize()
        
        # Example workflows
        workflow_examples = [
            {
                "type": WorkflowType.COLLABORATIVE,
                "request": "Create a professional advertisement for a luxury car brand",
                "context": {"brand": "luxury_automotive", "target": "high_end_consumers"}
            },
            {
                "type": WorkflowType.ITERATIVE_REFINEMENT,
                "request": "Design a series of social media posts for a fitness app launch",
                "context": {"platform": "instagram", "campaign_type": "product_launch"}
            },
            {
                "type": WorkflowType.BRAND_REVIEW,
                "request": "Generate corporate headshots style images for team page",
                "context": {"brand_strict": True, "corporate_guidelines": "conservative"}
            }
        ]
        
        workflow_results = []
        
        for i, example in enumerate(workflow_examples, 1):
            print(f"\\n--- Workflow Example {i}: {example['type'].value} ---")
            print(f"Request: {example['request']}")
            
            # Create workflow
            workflow_id = await orchestrator.create_workflow(
                workflow_type=example["type"],
                request=example["request"], 
                context=example["context"]
            )
            
            print(f"Created workflow: {workflow_id}")
            
            # Execute workflow
            execution_result = await orchestrator.execute_workflow(workflow_id, image_agent)
            
            workflow_results.append({
                "workflow_id": workflow_id,
                "type": example["type"].value,
                "result": execution_result
            })
            
            print(f"Workflow Status: {execution_result.get('success', 'unknown')}")
            if execution_result.get("success"):
                print(f"Execution Time: {execution_result.get('execution_time', 0):.1f}s")
                print(f"Workflow Stages: {len(execution_result.get('results', {}).get('workflow_stages', {}))}")
        
        # Show orchestrator metrics
        orchestrator_metrics = orchestrator.get_execution_metrics()
        print(f"\\n--- Orchestrator Metrics ---")
        print(json.dumps(orchestrator_metrics, indent=2))
        
        await orchestrator.cleanup()
        await image_agent.cleanup()
        
        return {"status": "completed", "workflows": workflow_results, "metrics": orchestrator_metrics}
    
    # === Example 3: Advanced Conversation Management ===
    
    async def example_3_conversation_management(self):
        """
        Example 3: Advanced conversation management with specialized patterns
        Demonstrates sophisticated AutoGen conversation orchestration.
        """
        
        print("\\n=== Example 3: Advanced Conversation Management ===\\n")
        
        # Create conversation manager
        conv_manager_config = {
            "max_concurrent_conversations": 10,
            "context_compression": True,
            "consensus_tracking": True
        }
        
        conv_manager = AutoGenConversationManager(conv_manager_config)
        await conv_manager.setup()
        
        # Example conversation scenarios
        conversation_examples = [
            {
                "template": "image_concept_development",
                "message": "We need to create a compelling visual campaign for a sustainable fashion brand targeting Gen Z consumers",
                "participants": ["creative_director", "prompt_engineer", "brand_officer", "qa_reviewer"],
                "context": {"brand_type": "sustainable_fashion", "target_audience": "gen_z", "values": "sustainability"}
            },
            {
                "template": "collaborative_refinement", 
                "message": "The initial images don't capture the premium feel we're going for. Let's refine the approach",
                "participants": ["creative_director", "prompt_engineer", "qa_reviewer"],
                "context": {"refinement_type": "premium_positioning", "issues": ["lacks_premium_feel", "color_scheme"]}
            },
            {
                "template": "consensus_decision",
                "message": "We have three different creative directions. We need to decide which one aligns best with our campaign goals",
                "participants": ["creative_director", "brand_officer", "qa_reviewer"],
                "context": {"decision_type": "creative_direction", "options": ["modern_minimal", "bold_vibrant", "classic_elegant"]}
            }
        ]
        
        conversation_results = []
        
        for i, example in enumerate(conversation_examples, 1):
            print(f"\\n--- Conversation Example {i}: {example['template']} ---")
            print(f"Scenario: {example['message']}")
            
            # Start conversation
            thread_id = await conv_manager.start_conversation(
                template_type=example["template"],
                initial_message=example["message"],
                participants=example["participants"],
                context=example["context"],
                priority=i
            )
            
            print(f"Started conversation thread: {thread_id}")
            
            # Execute conversation
            execution_result = await conv_manager.execute_conversation(
                thread_id=thread_id,
                max_rounds=15
            )
            
            conversation_results.append({
                "thread_id": thread_id,
                "template": example["template"],
                "result": execution_result
            })
            
            # Show conversation summary
            if execution_result.get("success"):
                print(f"Conversation completed successfully")
                print(f"Duration: {execution_result.get('duration_seconds', 0):.1f}s")
                print(f"Messages: {execution_result.get('message_count', 0)}")
                print(f"Participants: {len(execution_result.get('participant_contributions', {}))}")
                
                # Show conversation outcomes
                outcomes = execution_result.get("outcomes", {})
                if outcomes.get("decisions_made"):
                    print(f"Decisions Made: {len(outcomes['decisions_made'])}")
                if outcomes.get("consensus_achieved"):
                    print(f"Consensus Items: {len(outcomes['consensus_achieved'])}")
        
        # Show conversation analytics
        conv_metrics = conv_manager.get_conversation_metrics()
        print(f"\\n--- Conversation Manager Metrics ---")
        print(json.dumps(conv_metrics, indent=2))
        
        await conv_manager.cleanup()
        
        return {"status": "completed", "conversations": conversation_results, "metrics": conv_metrics}
    
    # === Example 4: Advanced Function Calling Patterns ===
    
    async def example_4_advanced_function_calling(self):
        """
        Example 4: Advanced AutoGen function calling patterns
        Demonstrates sophisticated function calling and coordination.
        """
        
        print("\\n=== Example 4: Advanced Function Calling Patterns ===\\n")
        
        # Create coordinator agent with advanced function calling
        coordinator_config = AgentConfig(
            name="function_calling_coordinator",
            description="Advanced function calling coordinator",
            category="marketing",
            system_message=AutoGenImageTools.create_enhanced_system_message(
                role="image_generator_coordinator",
                specialties=["function_orchestration", "workflow_management", "agent_coordination"],
                context={"advanced_features": True, "function_calling": "enabled"}
            )
        )
        
        coordinator = EnhancedImageGeneratorAgent(coordinator_config)
        await coordinator.initialize()
        
        # Implementation examples for the function schemas
        async def generate_marketing_image_impl(**kwargs) -> Dict[str, Any]:
            """Implementation of generate_marketing_image function."""
            prompt = kwargs.get("prompt", "")
            marketing_context = kwargs.get("marketing_context", {})
            technical_specs = kwargs.get("technical_specs", {})
            workflow_options = kwargs.get("workflow_options", {})
            
            print(f"Generating marketing image with:")
            print(f"  Prompt: {prompt}")
            print(f"  Campaign Type: {marketing_context.get('campaign_type', 'general')}")
            print(f"  Size: {technical_specs.get('size', '1024x1024')}")
            print(f"  Collaboration: {workflow_options.get('enable_collaboration', False)}")
            
            # Simulate image generation
            result = {
                "success": True,
                "images_generated": technical_specs.get("quantity", 1),
                "campaign_type": marketing_context.get("campaign_type"),
                "collaboration_enabled": workflow_options.get("enable_collaboration", False),
                "generated_files": [f"marketing_image_{i}.png" for i in range(technical_specs.get("quantity", 1))]
            }
            
            return result
        
        async def start_collaborative_review_impl(**kwargs) -> Dict[str, Any]:
            """Implementation of collaborative review function."""
            review_subject = kwargs.get("review_subject", "")
            participants = kwargs.get("participants", [])
            review_type = kwargs.get("review_type", "concept_review")
            
            print(f"Starting collaborative review:")
            print(f"  Subject: {review_subject}")
            print(f"  Type: {review_type}")
            print(f"  Participants: {', '.join(participants)}")
            
            # Simulate collaborative review
            review_result = {
                "review_initiated": True,
                "review_id": f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "participants": participants,
                "review_type": review_type,
                "estimated_duration": "15-30 minutes"
            }
            
            return review_result
        
        async def coordinate_agent_workflow_impl(**kwargs) -> Dict[str, Any]:
            """Implementation of workflow coordination function."""
            workflow_type = kwargs.get("workflow_type", "sequential")
            workflow_steps = kwargs.get("workflow_steps", [])
            
            print(f"Coordinating {workflow_type} workflow with {len(workflow_steps)} steps:")
            for step in workflow_steps:
                print(f"  - {step.get('step_id')}: {step.get('agent_name')} -> {step.get('action')}")
            
            # Simulate workflow coordination
            coordination_result = {
                "workflow_initiated": True,
                "workflow_id": f"wf_{workflow_type}_{datetime.now().strftime('%H%M%S')}",
                "workflow_type": workflow_type,
                "total_steps": len(workflow_steps),
                "estimated_completion": "5-10 minutes"
            }
            
            return coordination_result
        
        # Register function implementations
        function_implementations = {
            "generate_marketing_image": generate_marketing_image_impl,
            "start_collaborative_review": start_collaborative_review_impl,
            "coordinate_agent_workflow": coordinate_agent_workflow_impl
        }
        
        AutoGenImageTools.register_functions_with_agent(
            coordinator.get_agent(), 
            function_implementations
        )
        
        # Test complex function calling scenarios
        function_calling_examples = [
            {
                "name": "Complex Marketing Campaign",
                "request": """I need to create a comprehensive marketing campaign for a luxury hotel.
                Please generate high-quality images for:
                1. Social media posts (Instagram/Facebook)
                2. Website hero banners 
                3. Print advertisements
                
                Enable collaboration with brand review and ensure premium quality.
                Use the collaborative workflow with all specialist agents."""
            },
            {
                "name": "Multi-Stage Workflow Coordination",
                "request": """Coordinate a multi-stage workflow for creating product catalog images.
                We need:
                1. Concept development with creative director
                2. Technical optimization with prompt engineer  
                3. Quality review and brand compliance check
                4. Final approval and delivery
                
                Use iterative refinement if needed."""
            },
            {
                "name": "Consensus-Based Decision Making",
                "request": """We have multiple creative directions for our new campaign.
                Please start a collaborative review to evaluate:
                - Modern minimalist approach
                - Bold and vibrant style
                - Classic elegant design
                
                Get consensus from creative director, brand officer, and QA reviewer."""
            }
        ]
        
        function_results = []
        
        for i, example in enumerate(function_calling_examples, 1):
            print(f"\\n--- Function Calling Example {i}: {example['name']} ---")
            print(f"Request: {example['request']}")
            
            # Execute with function calling
            response = await coordinator.execute(
                example["request"], 
                context={
                    "enable_function_calling": True,
                    "example_name": example["name"],
                    "session_id": f"func_example_{i}"
                }
            )
            
            function_results.append({
                "example_name": example["name"],
                "success": response.success,
                "response": response.message,
                "execution_time": response.execution_time_ms
            })
            
            print(f"Function Calling Result: {response.success}")
            print(f"Response: {response.message[:200]}...")
            if response.execution_time_ms:
                print(f"Execution Time: {response.execution_time_ms:.1f}ms")
        
        await coordinator.cleanup()
        
        return {"status": "completed", "function_examples": function_results}
    
    # === Example 5: Group Chat and Consensus Building ===
    
    async def example_5_group_chat_consensus(self):
        """
        Example 5: Advanced group chat patterns with consensus building
        Demonstrates sophisticated group conversation management.
        """
        
        print("\\n=== Example 5: Group Chat and Consensus Building ===\\n")
        
        # Create specialized agents for group chat
        agents = []
        
        # Creative Director
        creative_director = AssistantAgent(
            name="creative_director",
            system_message=AutoGenImageTools.create_enhanced_system_message(
                role="creative_director",
                specialties=["creative_vision", "brand_strategy", "decision_leadership"],
                context={"group_chat": True, "role": "decision_leader"}
            ),
            llm_config=self._get_llm_config(),
            human_input_mode="NEVER"
        )
        agents.append(creative_director)
        
        # Prompt Engineer
        prompt_engineer = AssistantAgent(
            name="prompt_engineer",
            system_message=AutoGenImageTools.create_enhanced_system_message(
                role="prompt_engineer", 
                specialties=["prompt_optimization", "technical_expertise", "ai_generation"],
                context={"group_chat": True, "role": "technical_specialist"}
            ),
            llm_config=self._get_llm_config(),
            human_input_mode="NEVER"
        )
        agents.append(prompt_engineer)
        
        # QA Reviewer
        qa_reviewer = AssistantAgent(
            name="qa_reviewer",
            system_message=AutoGenImageTools.create_enhanced_system_message(
                role="qa_reviewer",
                specialties=["quality_assurance", "improvement_feedback", "standard_compliance"],
                context={"group_chat": True, "role": "quality_specialist"}
            ),
            llm_config=self._get_llm_config(),
            human_input_mode="NEVER"
        )
        agents.append(qa_reviewer)
        
        # Brand Officer
        brand_officer = AssistantAgent(
            name="brand_officer",
            system_message=AutoGenImageTools.create_enhanced_system_message(
                role="brand_officer",
                specialties=["brand_compliance", "guideline_enforcement", "consistency_check"],
                context={"group_chat": True, "role": "brand_guardian"}
            ),
            llm_config=self._get_llm_config(),
            human_input_mode="NEVER"
        )
        agents.append(brand_officer)
        
        # Create group chat scenarios
        group_chat_scenarios = [
            {
                "name": "Creative Direction Consensus",
                "topic": "We need to choose the creative direction for a tech startup's visual identity. Options are: futuristic/high-tech, clean/minimal, or warm/human-centered.",
                "consensus_method": "majority",
                "participants": ["creative_director", "brand_officer", "qa_reviewer"]
            },
            {
                "name": "Quality Standards Agreement",
                "topic": "Establishing quality standards for AI-generated marketing images including resolution, style consistency, and brand compliance requirements.", 
                "consensus_method": "unanimous",
                "participants": ["qa_reviewer", "brand_officer", "prompt_engineer"]
            },
            {
                "name": "Campaign Strategy Alignment",
                "topic": "Aligning on the visual strategy for a multi-platform marketing campaign including social media, web, and print requirements.",
                "consensus_method": "weighted",
                "participants": ["creative_director", "brand_officer", "prompt_engineer", "qa_reviewer"]
            }
        ]
        
        group_chat_results = []
        
        for i, scenario in enumerate(group_chat_scenarios, 1):
            print(f"\\n--- Group Chat Scenario {i}: {scenario['name']} ---")
            print(f"Topic: {scenario['topic']}")
            print(f"Consensus Method: {scenario['consensus_method']}")
            
            # Filter agents based on participants
            scenario_agents = [
                agent for agent in agents 
                if agent.name in scenario["participants"]
            ]
            
            # Create group chat
            group_chat = GroupChat(
                agents=scenario_agents,
                messages=[],
                max_round=12,
                speaker_selection_method="auto"
            )
            
            # Create group manager
            group_manager = GroupChatManager(
                groupchat=group_chat,
                llm_config=self._get_llm_config(),
                system_message=f"""You are managing a group discussion on: {scenario['topic']}

                Participants: {', '.join(scenario['participants'])}
                Goal: Reach {scenario['consensus_method']} consensus

                Guide the discussion to:
                1. Ensure all participants contribute their expertise
                2. Facilitate productive dialogue
                3. Identify areas of agreement and disagreement
                4. Drive toward consensus using {scenario['consensus_method']} approach
                5. Summarize final decisions

                Keep the discussion focused and productive."""
            )
            
            try:
                # Execute group consensus
                consensus_result = await AutoGenConversationPatterns.facilitate_group_consensus(
                    group_chat=group_chat,
                    group_manager=group_manager,
                    consensus_topic=scenario["topic"],
                    consensus_method=scenario["consensus_method"]
                )
                
                group_chat_results.append({
                    "scenario_name": scenario["name"],
                    "consensus_result": consensus_result,
                    "success": consensus_result.get("consensus_reached", False)
                })
                
                print(f"Consensus Reached: {consensus_result.get('consensus_reached', False)}")
                print(f"Participants: {consensus_result.get('total_participants', 0)}")
                print(f"Positive Votes: {consensus_result.get('positive_votes', 0)}")
                print(f"Consensus Ratio: {consensus_result.get('consensus_ratio', 0):.2f}")
                
            except Exception as e:
                print(f"Group chat scenario failed: {e}")
                group_chat_results.append({
                    "scenario_name": scenario["name"], 
                    "error": str(e),
                    "success": False
                })
        
        return {"status": "completed", "group_chat_results": group_chat_results}
    
    # === Example 6: Error Handling and Resilience ===
    
    async def example_6_error_handling_resilience(self):
        """
        Example 6: Error handling and resilience patterns
        Demonstrates robust AutoGen system design with error recovery.
        """
        
        print("\\n=== Example 6: Error Handling and Resilience ===\\n")
        
        from .autogen_tools import AutoGenErrorHandling, AutoGenPerformanceOptimization
        
        # Create base agents
        base_agent = AssistantAgent(
            name="resilient_agent",
            system_message="You are a resilient image generation agent with error handling capabilities.",
            llm_config=self._get_llm_config(),
            human_input_mode="NEVER"
        )
        
        # Apply resilience patterns
        retry_config = {
            "max_retries": 3,
            "retry_delay": 1.0,
            "fallback_response": "I encountered an error but will continue working on your request."
        }
        
        resilient_agent = AutoGenErrorHandling.create_resilient_agent_wrapper(
            base_agent, 
            retry_config
        )
        
        # Add performance monitoring
        monitored_agent = AutoGenPerformanceOptimization.create_performance_monitoring_wrapper(
            resilient_agent
        )
        
        # Create group chat with circuit breaker
        agents = [monitored_agent]
        
        group_chat = GroupChat(
            agents=agents,
            messages=[],
            max_round=10
        )
        
        # Apply circuit breaker
        protected_group_chat = AutoGenErrorHandling.create_circuit_breaker_for_group_chat(
            group_chat,
            failure_threshold=2,
            recovery_timeout=30
        )
        
        # Test error handling scenarios
        error_scenarios = [
            {
                "name": "Network Timeout Simulation",
                "request": "Generate an image with a very complex prompt that might cause timeout issues",
                "expect_error": False,  # Should be handled gracefully
            },
            {
                "name": "Invalid Parameter Handling", 
                "request": "Create image with invalid parameters: size=invalid, quality=bad",
                "expect_error": False,  # Should provide helpful error message
            },
            {
                "name": "Resource Exhaustion Recovery",
                "request": "Generate 10 high-resolution images simultaneously",
                "expect_error": False,  # Should handle resource limits gracefully
            }
        ]
        
        error_handling_results = []
        
        for i, scenario in enumerate(error_scenarios, 1):
            print(f"\\n--- Error Handling Scenario {i}: {scenario['name']} ---")
            print(f"Request: {scenario['request']}")
            
            try:
                # Test the resilient agent
                response = await monitored_agent.a_generate_reply(
                    messages=[{"role": "user", "content": scenario["request"]}],
                    sender=monitored_agent
                )
                
                error_handling_results.append({
                    "scenario_name": scenario["name"],
                    "success": True,
                    "response": response[:100] + "..." if len(response) > 100 else response,
                    "handled_gracefully": True
                })
                
                print(f"Response: {response[:100]}...")
                print("✅ Handled gracefully")
                
            except Exception as e:
                error_handling_results.append({
                    "scenario_name": scenario["name"],
                    "success": False,
                    "error": str(e),
                    "handled_gracefully": False
                })
                
                print(f"❌ Error: {str(e)}")
        
        # Show performance metrics
        if hasattr(monitored_agent, 'performance_metrics'):
            performance_metrics = monitored_agent.performance_metrics
            print(f"\\n--- Performance Metrics ---")
            print(json.dumps(performance_metrics, indent=2))
        
        return {
            "status": "completed", 
            "error_scenarios": error_handling_results,
            "performance_metrics": getattr(monitored_agent, 'performance_metrics', {})
        }
    
    # === Utility Methods ===
    
    def _get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration for examples."""
        try:
            from src.config.config_manager import get_config
            config_manager = get_config()
            return config_manager.get_llm_config()
        except:
            # Fallback configuration
            return {
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 1000,
                "config_list": [{"model": "gpt-4", "api_key": "fallback"}]
            }
    
    # === Main Example Runner ===
    
    async def run_all_examples(self) -> Dict[str, Any]:
        """
        Run all examples in sequence.
        Provides comprehensive demonstration of AutoGen capabilities.
        """
        
        print("\\n" + "="*80)
        print("COMPREHENSIVE AUTOGEN IMAGE GENERATION EXAMPLES")
        print("="*80)
        
        all_results = {}
        
        try:
            # Example 1: Basic Enhanced Agent
            print("\\n🚀 Running Example 1: Basic Enhanced Agent Usage...")
            all_results["example_1"] = await self.example_1_basic_enhanced_agent()
            
            # Example 2: Workflow Orchestration
            print("\\n🚀 Running Example 2: Multi-Agent Workflow Orchestration...")
            all_results["example_2"] = await self.example_2_workflow_orchestration()
            
            # Example 3: Conversation Management
            print("\\n🚀 Running Example 3: Advanced Conversation Management...")
            all_results["example_3"] = await self.example_3_conversation_management()
            
            # Example 4: Function Calling
            print("\\n🚀 Running Example 4: Advanced Function Calling Patterns...")
            all_results["example_4"] = await self.example_4_advanced_function_calling()
            
            # Example 5: Group Chat Consensus
            print("\\n🚀 Running Example 5: Group Chat and Consensus Building...")
            all_results["example_5"] = await self.example_5_group_chat_consensus()
            
            # Example 6: Error Handling
            print("\\n🚀 Running Example 6: Error Handling and Resilience...")
            all_results["example_6"] = await self.example_6_error_handling_resilience()
            
            print("\\n" + "="*80)
            print("✅ ALL EXAMPLES COMPLETED SUCCESSFULLY")
            print("="*80)
            
            # Summary
            successful_examples = len([r for r in all_results.values() if r.get("status") == "completed"])
            total_examples = len(all_results)
            
            print(f"\\n📊 SUMMARY:")
            print(f"Total Examples: {total_examples}")
            print(f"Successful: {successful_examples}")
            print(f"Success Rate: {(successful_examples/total_examples)*100:.1f}%")
            
            return {
                "overall_status": "completed",
                "total_examples": total_examples,
                "successful_examples": successful_examples,
                "success_rate": (successful_examples/total_examples)*100,
                "detailed_results": all_results
            }
            
        except Exception as e:
            self.logger.error(f"Example execution failed: {e}")
            return {
                "overall_status": "failed",
                "error": str(e),
                "completed_results": all_results
            }


# === Quick Usage Function ===

async def run_autogen_examples():
    """
    Quick function to run all AutoGen examples.
    Can be called directly for demonstrations.
    """
    
    examples = AutoGenImageGenerationExamples()
    results = await examples.run_all_examples()
    return results


# === Individual Example Functions ===

async def demo_basic_enhanced_agent():
    """Quick demo of basic enhanced agent."""
    examples = AutoGenImageGenerationExamples()
    return await examples.example_1_basic_enhanced_agent()

async def demo_workflow_orchestration():
    """Quick demo of workflow orchestration.""" 
    examples = AutoGenImageGenerationExamples()
    return await examples.example_2_workflow_orchestration()

async def demo_conversation_management():
    """Quick demo of conversation management."""
    examples = AutoGenImageGenerationExamples()
    return await examples.example_3_conversation_management()

async def demo_function_calling():
    """Quick demo of function calling patterns."""
    examples = AutoGenImageGenerationExamples()
    return await examples.example_4_advanced_function_calling()

async def demo_group_chat_consensus():
    """Quick demo of group chat and consensus."""
    examples = AutoGenImageGenerationExamples()
    return await examples.example_5_group_chat_consensus()

async def demo_error_handling():
    """Quick demo of error handling and resilience."""
    examples = AutoGenImageGenerationExamples()
    return await examples.example_6_error_handling_resilience()


# === Example Usage in Scripts ===

if __name__ == "__main__":
    """
    Example of how to run the demonstrations.
    """
    
    async def main():
        print("Starting AutoGen Image Generation Examples...")
        
        # Run all examples
        results = await run_autogen_examples()
        
        print("\\nExample execution completed!")
        print(f"Overall Status: {results.get('overall_status')}")
        
        if results.get('overall_status') == 'completed':
            print(f"Success Rate: {results.get('success_rate', 0):.1f}%")
        
        return results
    
    # Run the examples
    import asyncio
    results = asyncio.run(main())