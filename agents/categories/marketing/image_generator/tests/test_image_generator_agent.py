"""
Tests for the Image Generator Agent.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import tempfile
import json

from agents.base.base_agent import AgentConfig
from agents.categories.marketing.image_generator.agent import ImageGeneratorAgent
from src.tools.base.tool_interface import ToolResult, ToolStatus


@pytest.fixture
def agent_config():
    """Create agent configuration for testing."""
    return AgentConfig(
        name="test_image_generator",
        description="Test image generator agent",
        category="marketing",
        system_message="Test system message for image generation",
        model="gpt-4",
        temperature=0.7,
        max_tokens=2000
    )


@pytest.fixture
async def image_agent(agent_config):
    """Create image generator agent for testing."""
    agent = ImageGeneratorAgent(agent_config)
    
    # Mock the DALL-E tool setup
    agent.dalle_tool.setup = AsyncMock(return_value=True)
    agent._register_tool_functions = Mock()
    
    await agent.initialize()
    return agent


@pytest.fixture
def mock_dalle_response():
    """Mock DALL-E API response."""
    return {
        "data": [
            {
                "b64_json": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
                "revised_prompt": "A simple test image for marketing purposes"
            }
        ]
    }


class TestImageGeneratorAgent:
    """Test cases for Image Generator Agent."""

    @pytest.mark.asyncio
    async def test_agent_initialization(self, agent_config):
        """Test agent initialization."""
        agent = ImageGeneratorAgent(agent_config)
        assert agent.config.name == "test_image_generator"
        assert agent.config.category == "marketing"
        assert agent.dalle_tool is not None
        assert len(agent.marketing_templates) > 0

    @pytest.mark.asyncio
    async def test_agent_setup(self, image_agent):
        """Test agent setup process."""
        assert image_agent._is_initialized is True
        assert image_agent.dalle_tool.setup.called

    @pytest.mark.asyncio
    async def test_marketing_templates_loading(self, image_agent):
        """Test marketing templates are loaded correctly."""
        templates = image_agent.marketing_templates
        
        expected_templates = [
            "product_showcase", "social_media_post", "advertisement",
            "brand_identity", "hero_banner", "infographic_element",
            "event_promotion", "seasonal_campaign"
        ]
        
        for template in expected_templates:
            assert template in templates
            assert "{" in templates[template]  # Should contain placeholders

    @pytest.mark.asyncio
    async def test_parse_generation_request_positive(self, image_agent):
        """Test parsing valid generation requests."""
        message = "Generate a professional product image of a smartphone"
        context = {"tenant_id": "test_tenant"}
        
        # Mock LLM response
        mock_response = json.dumps({
            "is_generation_request": True,
            "prompt": "professional product image of a smartphone",
            "style": "vivid",
            "size": "1024x1024",
            "quality": "standard",
            "quantity": 1
        })
        
        with patch.object(image_agent._agent, 'a_generate_reply', return_value=mock_response):
            result = await image_agent._parse_generation_request(message, context)
        
        assert result is not None
        assert result["is_generation_request"] is True
        assert "smartphone" in result["prompt"]

    @pytest.mark.asyncio
    async def test_parse_generation_request_negative(self, image_agent):
        """Test parsing non-generation requests."""
        message = "What are the best practices for marketing?"
        context = {"tenant_id": "test_tenant"}
        
        # Mock LLM response
        mock_response = json.dumps({"is_generation_request": False})
        
        with patch.object(image_agent._agent, 'a_generate_reply', return_value=mock_response):
            result = await image_agent._parse_generation_request(message, context)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_enhance_marketing_prompt(self, image_agent):
        """Test prompt enhancement for marketing."""
        request = {
            "prompt": "product photo",
            "template_type": "product_showcase",
            "additional_specs": "high resolution"
        }
        context = {"tenant_id": "test_tenant"}
        
        enhanced = await image_agent._enhance_marketing_prompt(request, context)
        
        assert len(enhanced) > len(request["prompt"])
        assert "professional" in enhanced.lower()
        assert "high resolution" in enhanced

    @pytest.mark.asyncio
    async def test_enhance_marketing_prompt_without_template(self, image_agent):
        """Test prompt enhancement without specific template."""
        request = {
            "prompt": "creative marketing image",
            "additional_specs": "vibrant colors"
        }
        context = {"tenant_id": "test_tenant"}
        
        enhanced = await image_agent._enhance_marketing_prompt(request, context)
        
        assert "vibrant colors" in enhanced
        assert len(enhanced) > len(request["prompt"])

    @pytest.mark.asyncio
    async def test_handle_image_generation_success(self, image_agent, mock_dalle_response):
        """Test successful image generation."""
        request = {
            "prompt": "test marketing image",
            "size": "1024x1024",
            "quality": "standard",
            "style": "vivid",
            "quantity": 1
        }
        context = {"tenant_id": "test_tenant"}
        
        # Mock successful tool execution
        mock_tool_result = ToolResult(
            status=ToolStatus.SUCCESS,
            data={
                "images_generated": 1,
                "saved_files": ["/path/to/test_image.png"],
                "images": [{"revised_prompt": "Enhanced test prompt"}]
            }
        )
        
        image_agent.dalle_tool.execute = AsyncMock(return_value=mock_tool_result)
        image_agent._enhance_marketing_prompt = AsyncMock(return_value="enhanced test marketing image")
        
        result = await image_agent._handle_image_generation(request, context)
        
        assert result["success"] is True
        assert result["result"]["images_generated"] == 1
        assert len(image_agent.image_generation_history) == 1

    @pytest.mark.asyncio
    async def test_handle_image_generation_failure(self, image_agent):
        """Test failed image generation."""
        request = {
            "prompt": "test marketing image",
            "size": "1024x1024",
            "quality": "standard",
            "style": "vivid",
            "quantity": 1
        }
        context = {"tenant_id": "test_tenant"}
        
        # Mock failed tool execution
        mock_tool_result = ToolResult(
            status=ToolStatus.ERROR,
            error="API rate limit exceeded"
        )
        
        image_agent.dalle_tool.execute = AsyncMock(return_value=mock_tool_result)
        image_agent._enhance_marketing_prompt = AsyncMock(return_value="enhanced test marketing image")
        
        result = await image_agent._handle_image_generation(request, context)
        
        assert result["success"] is False
        assert "API rate limit exceeded" in result["error"]

    @pytest.mark.asyncio
    async def test_handle_consultation(self, image_agent):
        """Test marketing consultation handling."""
        message = "What image size is best for Instagram posts?"
        context = {"tenant_id": "test_tenant"}
        
        expected_response = "For Instagram posts, I recommend using 1080x1080 pixels for square posts..."
        
        with patch.object(image_agent._agent, 'a_generate_reply', return_value=expected_response):
            response = await image_agent._handle_consultation(message, context)
        
        assert response == expected_response

    @pytest.mark.asyncio
    async def test_format_generation_response_success(self, image_agent):
        """Test formatting successful generation response."""
        result = {
            "success": True,
            "result": {
                "images_generated": 2,
                "size": "1024x1024",
                "quality": "hd",
                "style": "vivid",
                "saved_files": ["/path/to/image1.png", "/path/to/image2.png"]
            },
            "enhanced_prompt": "Enhanced marketing prompt"
        }
        
        request = {"prompt": "Original prompt"}
        
        response = image_agent._format_generation_response(result, request)
        
        assert "✅" in response
        assert "2 marketing image(s)" in response
        assert "Enhanced marketing prompt" in response
        assert "/path/to/image1.png" in response
        assert "/path/to/image2.png" in response

    @pytest.mark.asyncio
    async def test_format_generation_response_failure(self, image_agent):
        """Test formatting failed generation response."""
        result = {
            "success": False,
            "error": "Invalid prompt content"
        }
        
        request = {"prompt": "Invalid prompt"}
        
        response = image_agent._format_generation_response(result, request)
        
        assert "error" in response.lower()
        assert "Invalid prompt content" in response

    @pytest.mark.asyncio
    async def test_process_message_generation_request(self, image_agent):
        """Test processing message with generation request."""
        message = "Create a product image for marketing"
        context = {"tenant_id": "test_tenant"}
        
        # Mock the parsing and generation
        mock_request = {"prompt": "product image for marketing", "quantity": 1}
        mock_result = {
            "success": True,
            "result": {"images_generated": 1, "saved_files": ["/path/to/image.png"]},
            "enhanced_prompt": "Enhanced product marketing image"
        }
        
        image_agent._parse_generation_request = AsyncMock(return_value=mock_request)
        image_agent._handle_image_generation = AsyncMock(return_value=mock_result)
        
        response = await image_agent.process_message(message, context)
        
        assert "✅" in response
        assert "marketing image" in response

    @pytest.mark.asyncio
    async def test_process_message_consultation(self, image_agent):
        """Test processing consultation message."""
        message = "What are best practices for marketing images?"
        context = {"tenant_id": "test_tenant"}
        
        expected_consultation = "Here are the best practices for marketing images..."
        
        image_agent._parse_generation_request = AsyncMock(return_value=None)
        image_agent._handle_consultation = AsyncMock(return_value=expected_consultation)
        
        response = await image_agent.process_message(message, context)
        
        assert response == expected_consultation

    @pytest.mark.asyncio
    async def test_get_generation_history(self, image_agent):
        """Test getting generation history."""
        # Add some test history
        image_agent.image_generation_history = [
            {"tenant_id": "tenant1", "timestamp": "2024-01-01T00:00:00"},
            {"tenant_id": "tenant2", "timestamp": "2024-01-02T00:00:00"},
            {"tenant_id": "tenant1", "timestamp": "2024-01-03T00:00:00"}
        ]
        
        # Test all history
        all_history = await image_agent.get_generation_history()
        assert len(all_history) == 3
        
        # Test filtered by tenant
        tenant1_history = await image_agent.get_generation_history(tenant_id="tenant1")
        assert len(tenant1_history) == 2
        
        # Test with limit
        limited_history = await image_agent.get_generation_history(limit=2)
        assert len(limited_history) == 2

    @pytest.mark.asyncio
    async def test_get_metrics_with_generation_data(self, image_agent):
        """Test metrics calculation with generation history."""
        # Add test generation history
        image_agent.image_generation_history = [
            {"result": {"images_generated": 2}},
            {"result": {"images_generated": 1}},
            {"result": None}  # Failed generation
        ]
        
        metrics = image_agent.get_metrics()
        
        assert metrics["total_images_generated"] == 3
        assert metrics["successful_generations"] == 2
        assert metrics["failed_generations"] == 1
        assert metrics["generation_history_size"] == 3

    @pytest.mark.asyncio
    async def test_tool_wrapper_functions(self, image_agent):
        """Test AutoGen tool wrapper functions."""
        # Mock tool execution
        mock_result = ToolResult(
            status=ToolStatus.SUCCESS,
            data={"images_generated": 1, "saved_files": ["test.png"]}
        )
        image_agent.dalle_tool.execute = AsyncMock(return_value=mock_result)
        
        # Test generate_image wrapper
        result = await image_agent._generate_image_wrapper(
            prompt="test prompt",
            size="1024x1024",
            quality="standard",
            style="vivid",
            quantity=1
        )
        
        assert result["success"] is True
        assert result["data"]["images_generated"] == 1

    @pytest.mark.asyncio
    async def test_tool_schemas(self, image_agent):
        """Test tool function schemas."""
        # Test generate_image schema
        schema = image_agent._get_generate_image_schema()
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "generate_image"
        assert "prompt" in schema["function"]["parameters"]["properties"]
        assert "prompt" in schema["function"]["parameters"]["required"]
        
        # Test list_images schema
        list_schema = image_agent._get_list_images_schema()
        assert list_schema["type"] == "function"
        assert list_schema["function"]["name"] == "list_images"
        
        # Test get_image_info schema
        info_schema = image_agent._get_image_info_schema()
        assert info_schema["type"] == "function"
        assert info_schema["function"]["name"] == "get_image_info"
        assert "filepath" in info_schema["function"]["parameters"]["required"]

    @pytest.mark.asyncio
    async def test_cleanup(self, image_agent):
        """Test agent cleanup."""
        image_agent.dalle_tool.cleanup = AsyncMock(return_value=True)
        
        await image_agent.cleanup()
        
        image_agent.dalle_tool.cleanup.assert_called_once()

    def test_supported_parameters(self, image_agent):
        """Test supported parameters are correctly defined."""
        assert "1024x1024" in image_agent.supported_sizes
        assert "1024x1792" in image_agent.supported_sizes
        assert "1792x1024" in image_agent.supported_sizes
        
        assert "standard" in image_agent.supported_qualities
        assert "hd" in image_agent.supported_qualities
        
        assert "vivid" in image_agent.supported_styles
        assert "natural" in image_agent.supported_styles