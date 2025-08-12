"""
Image Generator Agent for Marketing Campaigns.
Uses DALL-E 3 to generate high-quality images based on text prompts.
"""

import json
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

from autogen import Agent
from loguru import logger

from agents.base.base_agent import BaseAgent, AgentConfig, AgentResponse
from src.tools.integrations.image_generation.dalle_tool import DalleTool
from src.log_service import get_logger


class ImageGeneratorAgent(BaseAgent):
    """
    AutoGen agent for generating marketing images using DALL-E 3.
    
    This agent specializes in creating visually appealing images for marketing
    campaigns, social media posts, advertisements, and other promotional materials.
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the Image Generator Agent.
        
        Args:
            config: Agent configuration
        """
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
        self.image_generation_history: List[Dict[str, Any]] = []
        
        # Agent capabilities
        self.supported_styles = ["vivid", "natural"]
        self.supported_sizes = ["1024x1024", "1024x1792", "1792x1024"]
        self.supported_qualities = ["standard", "hd"]
        
        # Marketing-specific prompts and templates
        self.marketing_templates = self._load_marketing_templates()
        
    async def setup(self) -> None:
        """Set up the Image Generator Agent."""
        try:
            # Set up DALL-E tool
            if not await self.dalle_tool.setup():
                raise RuntimeError("Failed to initialize DALL-E tool")
            
            # Register tool functions for AutoGen
            self._register_tool_functions()
            
            self.logger.info("Image Generator Agent setup completed")
            
        except Exception as e:
            self.logger.error(f"Image Generator Agent setup failed: {e}")
            raise
    
    def _register_tool_functions(self) -> None:
        """Register tool functions with AutoGen agent."""
        if self._agent:
            # Register image generation function
            self._agent.register_for_execution("generate_image")(self._generate_image_wrapper)
            self._agent.register_for_llm("generate_image")(self._get_generate_image_schema())
            
            # Register image management functions
            self._agent.register_for_execution("list_images")(self._list_images_wrapper)
            self._agent.register_for_llm("list_images")(self._get_list_images_schema())
            
            self._agent.register_for_execution("get_image_info")(self._get_image_info_wrapper)
            self._agent.register_for_llm("get_image_info")(self._get_image_info_schema())
    
    def _load_marketing_templates(self) -> Dict[str, str]:
        """Load marketing-specific prompt templates."""
        return {
            "product_showcase": "A professional product photography style image of {product} with {background} background, high quality, commercial photography lighting",
            "social_media_post": "A vibrant and engaging {style} illustration for social media showing {subject}, modern design, eye-catching colors",
            "advertisement": "A compelling advertisement image for {product_service} featuring {key_message}, professional marketing design, clean layout",
            "brand_identity": "A minimalist and professional logo-style image representing {concept}, clean design, corporate branding style",
            "hero_banner": "A stunning hero banner image for {business_type} website featuring {main_element}, modern web design, high impact visual",
            "infographic_element": "A clean and informative illustration showing {data_concept}, infographic style, professional data visualization",
            "event_promotion": "An exciting promotional image for {event_type} event featuring {theme}, vibrant colors, celebration atmosphere",
            "seasonal_campaign": "A {season} themed marketing image for {campaign_type}, seasonal colors and elements, festive atmosphere"
        }
    
    async def process_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        sender: Optional[Agent] = None
    ) -> str:
        """
        Process image generation requests and marketing consultations.
        
        Args:
            message: User message with image generation request
            context: Execution context
            sender: Sender agent
            
        Returns:
            Response message
        """
        try:
            context = context or {}
            
            # Parse the message for image generation intent
            generation_request = await self._parse_generation_request(message, context)
            
            if generation_request:
                # Generate images
                result = await self._handle_image_generation(generation_request, context)
                return self._format_generation_response(result, generation_request)
            
            else:
                # Handle general marketing image consultation
                return await self._handle_consultation(message, context)
            
        except Exception as e:
            self.logger.error(f"Message processing failed: {e}")
            return f"I encountered an error while processing your request: {str(e)}. Please try again or rephrase your request."
    
    async def _parse_generation_request(
        self,
        message: str,
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Parse message for image generation parameters.
        
        Args:
            message: User message
            context: Context
            
        Returns:
            Generation request parameters or None
        """
        # Use LLM to extract generation parameters
        extraction_prompt = f"""
        Extract image generation parameters from this message: "{message}"
        
        Look for:
        1. Main subject/prompt (required)
        2. Style preference (vivid/natural)
        3. Size preference (1024x1024, 1024x1792, 1792x1024)
        4. Quality preference (standard/hd)
        5. Quantity (1-10)
        6. Marketing template type (if any)
        7. Additional specifications
        
        If this appears to be an image generation request, respond with JSON:
        {{
            "is_generation_request": true,
            "prompt": "extracted main prompt",
            "style": "vivid or natural",
            "size": "size preference",
            "quality": "standard or hd",
            "quantity": number,
            "template_type": "template name if applicable",
            "additional_specs": "any additional requirements"
        }}
        
        If this is NOT an image generation request, respond with:
        {{"is_generation_request": false}}
        """
        
        if self._agent:
            response = await self._agent.a_generate_reply(
                messages=[{"role": "user", "content": extraction_prompt}],
                sender=self._agent
            )
            
            try:
                # Extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    params = json.loads(json_match.group())
                    if params.get("is_generation_request"):
                        return params
            except (json.JSONDecodeError, AttributeError):
                pass
        
        return None
    
    async def _handle_image_generation(
        self,
        request: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle image generation with DALL-E.
        
        Args:
            request: Generation request parameters
            context: Execution context
            
        Returns:
            Generation result
        """
        # Enhance prompt with marketing expertise
        enhanced_prompt = await self._enhance_marketing_prompt(request, context)
        
        # Prepare generation parameters
        generation_params = {
            "prompt": enhanced_prompt,
            "size": request.get("size", "1024x1024"),
            "quality": request.get("quality", "standard"),
            "style": request.get("style", "vivid"),
            "n": min(request.get("quantity", 1), 4),  # Limit to 4 for cost control
            "save_to_file": True,
            "filename_prefix": f"marketing_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
        # Execute generation
        result = await self.dalle_tool.execute(generation_params, context)
        
        # Record in history
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "original_request": request,
            "enhanced_prompt": enhanced_prompt,
            "generation_params": generation_params,
            "result": result.data if result.status.value == "success" else None,
            "error": result.error if result.error else None,
            "tenant_id": context.get("tenant_id", "unknown")
        }
        
        self.image_generation_history.append(history_entry)
        
        return {
            "success": result.status.value == "success",
            "result": result.data,
            "error": result.error,
            "enhanced_prompt": enhanced_prompt,
            "original_request": request
        }
    
    async def _enhance_marketing_prompt(
        self,
        request: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """
        Enhance the prompt with marketing expertise.
        
        Args:
            request: Generation request
            context: Context
            
        Returns:
            Enhanced prompt
        """
        base_prompt = request["prompt"]
        template_type = request.get("template_type")
        additional_specs = request.get("additional_specs", "")
        
        # Apply template if specified
        if template_type and template_type in self.marketing_templates:
            template = self.marketing_templates[template_type]
            # This is a simplified template application - in practice you'd use more sophisticated prompt engineering
            enhanced_prompt = f"{template.replace('{subject}', base_prompt)}"
        else:
            enhanced_prompt = base_prompt
        
        # Add marketing-specific enhancements
        marketing_enhancements = [
            "professional marketing photography quality",
            "commercial grade lighting",
            "high resolution",
            "suitable for marketing materials"
        ]
        
        if additional_specs:
            enhanced_prompt = f"{enhanced_prompt}, {additional_specs}"
        
        # Add quality modifiers based on request
        if request.get("quality") == "hd":
            enhanced_prompt = f"{enhanced_prompt}, ultra high quality, 4K resolution"
        
        # Ensure prompt doesn't exceed limits
        if len(enhanced_prompt) > 3900:  # Leave some buffer
            enhanced_prompt = enhanced_prompt[:3900] + "..."
        
        return enhanced_prompt
    
    async def _handle_consultation(
        self,
        message: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Handle general marketing image consultation.
        
        Args:
            message: User message
            context: Context
            
        Returns:
            Consultation response
        """
        consultation_prompt = f"""
        As a marketing image generation specialist, provide helpful advice for this request:
        "{message}"
        
        Consider:
        - Image types that work best for different marketing goals
        - Composition and style recommendations
        - Size and format suggestions for different platforms
        - Brand consistency considerations
        - Current visual marketing trends
        
        Provide practical, actionable advice for creating effective marketing visuals.
        """
        
        if self._agent:
            response = await self._agent.a_generate_reply(
                messages=[{"role": "user", "content": consultation_prompt}],
                sender=self._agent
            )
            return response
        
        return "I'd be happy to help with marketing image advice. Could you provide more specific details about your needs?"
    
    def _format_generation_response(
        self,
        result: Dict[str, Any],
        request: Dict[str, Any]
    ) -> str:
        """
        Format the image generation response.
        
        Args:
            result: Generation result
            request: Original request
            
        Returns:
            Formatted response
        """
        if not result["success"]:
            return f"I encountered an error generating your image: {result.get('error', 'Unknown error')}. Please try adjusting your prompt or try again."
        
        data = result["result"]
        images_count = data.get("images_generated", 0)
        saved_files = data.get("saved_files", [])
        
        response = f"✅ Successfully generated {images_count} marketing image(s)!\n\n"
        
        if result["enhanced_prompt"] != request["prompt"]:
            response += f"📝 Enhanced your prompt for better marketing results:\n\"{result['enhanced_prompt']}\"\n\n"
        
        response += f"🎨 **Image Details:**\n"
        response += f"- Size: {data.get('size', 'Unknown')}\n"
        response += f"- Quality: {data.get('quality', 'Unknown')}\n"
        response += f"- Style: {data.get('style', 'Unknown')}\n\n"
        
        if saved_files:
            response += f"💾 **Saved Files:**\n"
            for file_path in saved_files:
                response += f"- {file_path}\n"
        
        response += f"\n🚀 Your images are ready for use in marketing campaigns, social media, or any promotional materials!"
        
        return response
    
    # Tool wrapper functions for AutoGen
    async def _generate_image_wrapper(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid",
        quantity: int = 1
    ) -> Dict[str, Any]:
        """Wrapper for generate_image function."""
        params = {
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "style": style,
            "n": quantity,
            "save_to_file": True
        }
        
        result = await self.dalle_tool.execute(params, {"tenant_id": "autogen"})
        return {
            "success": result.status.value == "success",
            "data": result.data,
            "error": result.error
        }
    
    async def _list_images_wrapper(self, tenant_id: str = "autogen", limit: int = 10) -> List[Dict[str, Any]]:
        """Wrapper for list_images function."""
        return await self.dalle_tool.list_generated_images(tenant_id, limit)
    
    async def _get_image_info_wrapper(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Wrapper for get_image_info function."""
        return await self.dalle_tool.get_image_info(filepath)
    
    def _get_generate_image_schema(self) -> Dict[str, Any]:
        """Get schema for generate_image function."""
        return {
            "type": "function",
            "function": {
                "name": "generate_image",
                "description": "Generate marketing images using DALL-E 3",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "Text description of the image to generate"
                        },
                        "size": {
                            "type": "string",
                            "enum": ["1024x1024", "1024x1792", "1792x1024"],
                            "description": "Image size"
                        },
                        "quality": {
                            "type": "string",
                            "enum": ["standard", "hd"],
                            "description": "Image quality"
                        },
                        "style": {
                            "type": "string",
                            "enum": ["vivid", "natural"],
                            "description": "Image style"
                        },
                        "quantity": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 4,
                            "description": "Number of images to generate"
                        }
                    },
                    "required": ["prompt"]
                }
            }
        }
    
    def _get_list_images_schema(self) -> Dict[str, Any]:
        """Get schema for list_images function."""
        return {
            "type": "function",
            "function": {
                "name": "list_images",
                "description": "List previously generated images",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tenant_id": {
                            "type": "string",
                            "description": "Tenant ID to filter images"
                        },
                        "limit": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 50,
                            "description": "Maximum number of images to return"
                        }
                    }
                }
            }
        }
    
    def _get_image_info_schema(self) -> Dict[str, Any]:
        """Get schema for get_image_info function."""
        return {
            "type": "function",
            "function": {
                "name": "get_image_info",
                "description": "Get detailed information about a specific image",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filepath": {
                            "type": "string",
                            "description": "Path to the image file"
                        }
                    },
                    "required": ["filepath"]
                }
            }
        }
    
    async def get_generation_history(
        self,
        tenant_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get image generation history.
        
        Args:
            tenant_id: Optional tenant ID filter
            limit: Maximum number of records
            
        Returns:
            Generation history
        """
        history = self.image_generation_history
        
        if tenant_id:
            history = [h for h in history if h.get("tenant_id") == tenant_id]
        
        return history[-limit:] if limit else history
    
    async def cleanup(self) -> None:
        """Clean up agent resources."""
        try:
            if self.dalle_tool:
                await self.dalle_tool.cleanup()
            
            await super().cleanup()
            self.logger.info("Image Generator Agent cleaned up successfully")
            
        except Exception as e:
            self.logger.error(f"Image Generator Agent cleanup failed: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics including image generation stats."""
        base_metrics = super().get_metrics()
        
        # Add image generation specific metrics
        total_images = sum(
            h.get("result", {}).get("images_generated", 0) 
            for h in self.image_generation_history 
            if h.get("result")
        )
        
        successful_generations = len([
            h for h in self.image_generation_history 
            if h.get("result") is not None
        ])
        
        base_metrics.update({
            "total_images_generated": total_images,
            "successful_generations": successful_generations,
            "failed_generations": len(self.image_generation_history) - successful_generations,
            "generation_history_size": len(self.image_generation_history),
            "dalle_tool_healthy": getattr(self.dalle_tool, '_health_status', False)
        })
        
        return base_metrics