"""
Text Generation Tool for AutoGen SME platform.
Provides AI-powered text generation capabilities for various content types.
"""

import json
from typing import Any, Dict, List, Optional, Union
from enum import Enum
import httpx
from jinja2 import Template

from .base import BaseTool, ToolResult, ToolStatus, ToolMetadata, ToolCapability
from ..log_service import get_logger
from ..config import get_tool_config, TextGenerationConfig


class ContentType(str, Enum):
    """Content types for text generation."""
    EMAIL = "email"
    DOCUMENT = "document"
    SUMMARY = "summary"
    PROPOSAL = "proposal"
    RESPONSE = "response"
    DESCRIPTION = "description"
    MARKETING_COPY = "marketing_copy"
    BLOG_POST = "blog_post"
    PRODUCT_DESCRIPTION = "product_description"
    SOCIAL_MEDIA = "social_media"
    REPORT = "report"
    LETTER = "letter"
    CUSTOM = "custom"


class TextGenerationTool(BaseTool):
    """Tool for generating various types of text content using AI."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the text generation tool.
        
        Args:
            config: Tool configuration
        """
        super().__init__(config)
        self.generation_config = TextGenerationConfig(**config)
        self.logger = get_logger("text_generation_tool")
        
        # API endpoints for different providers
        self.api_endpoints = {
            "openai": "https://api.openai.com/v1/chat/completions",
            "anthropic": "https://api.anthropic.com/v1/messages",
            "azure_openai": config.get("azure_endpoint", "")
        }
        
        # Content templates
        self.content_templates = {
            ContentType.EMAIL: {
                "system_prompt": "You are a professional email writer. Write clear, concise, and appropriate business emails.",
                "user_template": "Write a {tone} email about: {topic}\nRecipient: {recipient}\nAdditional context: {context}"
            },
            ContentType.DOCUMENT: {
                "system_prompt": "You are a professional document writer. Create well-structured, informative documents.",
                "user_template": "Create a {document_type} document about: {topic}\nTarget audience: {audience}\nKey points: {key_points}\nAdditional context: {context}"
            },
            ContentType.SUMMARY: {
                "system_prompt": "You are an expert at creating clear, concise summaries that capture key information.",
                "user_template": "Summarize the following content in {length} style:\n\n{content}"
            },
            ContentType.PROPOSAL: {
                "system_prompt": "You are a business proposal writer. Create compelling, professional proposals.",
                "user_template": "Write a business proposal for: {service_or_product}\nClient: {client}\nBudget range: {budget}\nDeadline: {deadline}\nAdditional requirements: {requirements}"
            },
            ContentType.MARKETING_COPY: {
                "system_prompt": "You are a marketing copywriter. Create engaging, persuasive marketing content.",
                "user_template": "Write marketing copy for: {product_or_service}\nTarget audience: {audience}\nTone: {tone}\nKey benefits: {benefits}\nCall to action: {cta}"
            }
        }
    
    @property
    def metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        if self._metadata is None:
            self._metadata = ToolMetadata(
                name="text_generation",
                description="Generate various types of text content using AI language models",
                version="1.0.0",
                capabilities=[ToolCapability.GENERATION],
                input_schema={
                    "type": "object",
                    "properties": {
                        "content_type": {
                            "type": "string",
                            "enum": [ct.value for ct in ContentType],
                            "description": "Type of content to generate"
                        },
                        "prompt": {
                            "type": "string",
                            "description": "Main prompt for content generation"
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Template parameters for structured content types",
                            "properties": {
                                "topic": {"type": "string"},
                                "tone": {"type": "string", "enum": ["professional", "casual", "friendly", "formal", "persuasive"]},
                                "audience": {"type": "string"},
                                "length": {"type": "string", "enum": ["brief", "moderate", "detailed"]},
                                "context": {"type": "string"}
                            }
                        },
                        "max_tokens": {
                            "type": "integer",
                            "description": "Maximum tokens to generate",
                            "default": 2000,
                            "minimum": 10,
                            "maximum": 4000
                        },
                        "temperature": {
                            "type": "number",
                            "description": "Creativity level (0.0-2.0)",
                            "default": 0.7,
                            "minimum": 0.0,
                            "maximum": 2.0
                        },
                        "custom_system_prompt": {
                            "type": "string",
                            "description": "Optional custom system prompt override"
                        }
                    },
                    "required": ["content_type", "prompt"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "generated_text": {"type": "string"},
                        "content_type": {"type": "string"},
                        "word_count": {"type": "integer"},
                        "character_count": {"type": "integer"},
                        "tokens_used": {"type": "integer"},
                        "model_used": {"type": "string"}
                    }
                },
                rate_limits={
                    "per_minute": self.generation_config.rate_limit_per_minute,
                    "per_hour": self.generation_config.rate_limit_per_hour
                },
                dependencies=["httpx", "jinja2"],
                tags=["ai", "generation", "content", "writing", "nlp"]
            )
        return self._metadata
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate text generation input data.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            if "content_type" not in input_data or "prompt" not in input_data:
                self.logger.warning("Missing required fields: content_type or prompt")
                return False
            
            content_type = input_data["content_type"]
            if content_type not in [ct.value for ct in ContentType]:
                self.logger.warning(f"Invalid content_type: {content_type}")
                return False
            
            prompt = input_data["prompt"].strip()
            if len(prompt) < 5:
                self.logger.warning("Prompt is too short")
                return False
            
            # Validate optional parameters
            max_tokens = input_data.get("max_tokens", self.generation_config.max_tokens)
            if not isinstance(max_tokens, int) or max_tokens < 10 or max_tokens > 4000:
                self.logger.warning(f"Invalid max_tokens: {max_tokens}")
                return False
            
            temperature = input_data.get("temperature", self.generation_config.temperature)
            if not isinstance(temperature, (int, float)) or temperature < 0.0 or temperature > 2.0:
                self.logger.warning(f"Invalid temperature: {temperature}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Input validation failed: {e}")
            return False
    
    async def _do_execute(
        self, 
        input_data: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> ToolResult:
        """
        Execute text generation.
        
        Args:
            input_data: Generation parameters
            context: Execution context
            
        Returns:
            Generated text result
        """
        content_type = ContentType(input_data["content_type"])
        prompt = input_data["prompt"]
        parameters = input_data.get("parameters", {})
        max_tokens = input_data.get("max_tokens", self.generation_config.max_tokens)
        temperature = input_data.get("temperature", self.generation_config.temperature)
        custom_system_prompt = input_data.get("custom_system_prompt")
        
        self.logger.info(f"Generating {content_type.value} content")
        
        try:
            # Build the full prompt
            system_prompt, user_prompt = await self._build_prompt(
                content_type, prompt, parameters, custom_system_prompt
            )
            
            # Generate text using configured provider
            if self.generation_config.model_provider == "openai":
                result = await self._generate_openai(
                    system_prompt, user_prompt, max_tokens, temperature
                )
            elif self.generation_config.model_provider == "anthropic":
                result = await self._generate_anthropic(
                    system_prompt, user_prompt, max_tokens, temperature
                )
            elif self.generation_config.model_provider == "azure_openai":
                result = await self._generate_azure_openai(
                    system_prompt, user_prompt, max_tokens, temperature
                )
            else:
                raise ValueError(f"Unsupported model provider: {self.generation_config.model_provider}")
            
            # Post-process the generated text
            generated_text = result["text"].strip()
            word_count = len(generated_text.split())
            character_count = len(generated_text)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "generated_text": generated_text,
                    "content_type": content_type.value,
                    "word_count": word_count,
                    "character_count": character_count,
                    "tokens_used": result.get("tokens_used", 0),
                    "model_used": result.get("model_used", self.generation_config.model_name)
                },
                metadata={
                    "provider": self.generation_config.model_provider,
                    "model": self.generation_config.model_name,
                    "prompt_tokens": result.get("prompt_tokens", 0),
                    "completion_tokens": result.get("completion_tokens", 0)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Text generation failed: {e}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Generation failed: {str(e)}"
            )
    
    async def _build_prompt(
        self,
        content_type: ContentType,
        user_prompt: str,
        parameters: Dict[str, Any],
        custom_system_prompt: Optional[str] = None
    ) -> tuple[str, str]:
        """
        Build system and user prompts based on content type.
        
        Args:
            content_type: Type of content to generate
            user_prompt: User's main prompt
            parameters: Template parameters
            custom_system_prompt: Optional custom system prompt
            
        Returns:
            Tuple of (system_prompt, formatted_user_prompt)
        """
        # Get template for content type
        template_info = self.content_templates.get(content_type)
        
        if custom_system_prompt:
            system_prompt = custom_system_prompt
        elif template_info:
            system_prompt = template_info["system_prompt"]
        else:
            system_prompt = "You are a helpful AI assistant that generates high-quality text content."
        
        # Format user prompt with parameters if template exists
        if template_info and "user_template" in template_info:
            try:
                # Merge prompt into parameters
                all_params = {**parameters, "topic": user_prompt}
                
                # Use Jinja2 template for flexible parameter substitution
                template = Template(template_info["user_template"])
                formatted_prompt = template.render(**all_params)
            except Exception as e:
                self.logger.warning(f"Template rendering failed, using original prompt: {e}")
                formatted_prompt = user_prompt
        else:
            formatted_prompt = user_prompt
        
        return system_prompt, formatted_prompt
    
    async def _generate_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Generate text using OpenAI API."""
        headers = {
            "Authorization": f"Bearer {self.generation_config.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.generation_config.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": self.generation_config.top_p,
            "frequency_penalty": self.generation_config.frequency_penalty,
            "presence_penalty": self.generation_config.presence_penalty
        }
        
        async with self.http_client as client:
            response = await client.post(
                self.api_endpoints["openai"],
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
        
        usage = data.get("usage", {})
        return {
            "text": data["choices"][0]["message"]["content"],
            "model_used": data.get("model", self.generation_config.model_name),
            "tokens_used": usage.get("total_tokens", 0),
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0)
        }
    
    async def _generate_anthropic(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Generate text using Anthropic API."""
        headers = {
            "x-api-key": self.generation_config.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": self.generation_config.model_name,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        async with self.http_client as client:
            response = await client.post(
                self.api_endpoints["anthropic"],
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
        
        usage = data.get("usage", {})
        return {
            "text": data["content"][0]["text"],
            "model_used": data.get("model", self.generation_config.model_name),
            "tokens_used": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            "prompt_tokens": usage.get("input_tokens", 0),
            "completion_tokens": usage.get("output_tokens", 0)
        }
    
    async def _generate_azure_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Generate text using Azure OpenAI API."""
        headers = {
            "api-key": self.generation_config.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": self.generation_config.top_p,
            "frequency_penalty": self.generation_config.frequency_penalty,
            "presence_penalty": self.generation_config.presence_penalty
        }
        
        # Azure endpoint includes deployment name
        endpoint = f"{self.api_endpoints['azure_openai']}/openai/deployments/{self.generation_config.model_name}/chat/completions"
        
        async with self.http_client as client:
            response = await client.post(
                endpoint,
                headers=headers,
                json=payload,
                params={"api-version": "2023-12-01-preview"}
            )
            response.raise_for_status()
            data = response.json()
        
        usage = data.get("usage", {})
        return {
            "text": data["choices"][0]["message"]["content"],
            "model_used": self.generation_config.model_name,
            "tokens_used": usage.get("total_tokens", 0),
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0)
        }
    
    async def health_check(self) -> bool:
        """
        Check if the text generation service is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try a simple test generation
            test_result = await self._do_execute(
                {
                    "content_type": "custom",
                    "prompt": "Say 'Hello, world!'",
                    "max_tokens": 10
                },
                {}
            )
            return test_result.is_success and "hello" in test_result.data.get("generated_text", "").lower()
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False