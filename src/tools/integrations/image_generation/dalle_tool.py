"""
DALL-E 3 Image Generation Tool.
Provides integration with OpenAI's DALL-E 3 model for generating high-quality images.
"""

import base64
import asyncio
from io import BytesIO
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import json

import httpx
from PIL import Image

from ...base.base_tool import BaseTool
from ...base.tool_interface import ToolResult, ToolStatus, ToolMetadata
from ....config.config_manager import get_config


@dataclass
class ImageGenerationRequest:
    """Request structure for image generation."""
    prompt: str
    size: str = "1024x1024"
    quality: str = "standard"
    style: str = "vivid"
    n: int = 1
    response_format: str = "b64_json"


@dataclass
class GeneratedImage:
    """Generated image data."""
    image_data: bytes
    revised_prompt: Optional[str] = None
    size: str = "1024x1024"
    filename: Optional[str] = None
    url: Optional[str] = None


class DalleTool(BaseTool):
    """DALL-E 3 image generation tool with enhanced capabilities."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize DALL-E tool.
        
        Args:
            config: Tool configuration
        """
        super().__init__(config)
        
        # Set up metadata
        self.metadata = ToolMetadata(
            name="dalle_image_generator",
            description="Generate high-quality images using OpenAI's DALL-E 3",
            version="1.0.0",
            category="image_generation",
            required_params=["prompt"],
            optional_params=[
                "size", "quality", "style", "n", "response_format", 
                "save_to_file", "filename_prefix"
            ]
        )
        
        # Configuration
        self.api_key = self._get_api_key()
        self.base_url = "https://api.openai.com/v1/images/generations"
        self.save_directory = Path(config.get("save_directory", "./generated_images"))
        self.max_prompt_length = config.get("max_prompt_length", 4000)
        self.supported_sizes = ["1024x1024", "1024x1792", "1792x1024"]
        self.supported_qualities = ["standard", "hd"]
        self.supported_styles = ["vivid", "natural"]
        
        # Ensure save directory exists
        self.save_directory.mkdir(parents=True, exist_ok=True)
        
    def _get_api_key(self) -> str:
        """Get OpenAI API key from configuration."""
        config_manager = get_config()
        if not config_manager.openai.api_key:
            raise ValueError("OpenAI API key not configured")
        return config_manager.openai.api_key
    
    async def setup(self) -> bool:
        """Set up the DALL-E tool."""
        try:
            # Test API connectivity
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with self._http_session() as client:
                # Make a test request to verify API access
                test_response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers=headers
                )
                
                if test_response.status_code != 200:
                    self.logger.error(f"API test failed: {test_response.status_code}")
                    return False
                
            self.logger.info("DALL-E tool setup completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"DALL-E tool setup failed: {e}")
            return False
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input parameters for image generation.
        
        Args:
            input_data: Input parameters to validate
            
        Returns:
            True if input is valid
        """
        # Check required parameters
        if "prompt" not in input_data:
            self.logger.error("Missing required parameter: prompt")
            return False
        
        prompt = input_data["prompt"]
        if not isinstance(prompt, str) or len(prompt.strip()) == 0:
            self.logger.error("Prompt must be a non-empty string")
            return False
        
        if len(prompt) > self.max_prompt_length:
            self.logger.error(f"Prompt too long: {len(prompt)} > {self.max_prompt_length}")
            return False
        
        # Validate optional parameters
        if "size" in input_data and input_data["size"] not in self.supported_sizes:
            self.logger.error(f"Unsupported size: {input_data['size']}")
            return False
        
        if "quality" in input_data and input_data["quality"] not in self.supported_qualities:
            self.logger.error(f"Unsupported quality: {input_data['quality']}")
            return False
        
        if "style" in input_data and input_data["style"] not in self.supported_styles:
            self.logger.error(f"Unsupported style: {input_data['style']}")
            return False
        
        if "n" in input_data:
            n = input_data["n"]
            if not isinstance(n, int) or n < 1 or n > 10:
                self.logger.error(f"Parameter 'n' must be between 1 and 10, got: {n}")
                return False
        
        return True
    
    async def _do_execute(
        self,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ToolResult:
        """
        Execute image generation with DALL-E 3.
        
        Args:
            input_data: Input parameters
            context: Execution context
            
        Returns:
            Tool execution result
        """
        try:
            # Create generation request
            request = self._create_request(input_data)
            
            # Generate images
            images = await self._generate_images(request, context)
            
            # Save images if requested
            saved_files = []
            if input_data.get("save_to_file", True):
                saved_files = await self._save_images(images, input_data, context)
            
            # Prepare result data
            result_data = {
                "images_generated": len(images),
                "prompt": request.prompt,
                "size": request.size,
                "quality": request.quality,
                "style": request.style,
                "saved_files": saved_files,
                "images": [
                    {
                        "revised_prompt": img.revised_prompt,
                        "size": img.size,
                        "filename": img.filename,
                        "url": img.url,
                        "image_data_base64": base64.b64encode(img.image_data).decode() if not input_data.get("save_to_file", True) else None
                    }
                    for img in images
                ]
            }
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=result_data,
                message=f"Successfully generated {len(images)} image(s) using DALL-E 3"
            )
            
        except Exception as e:
            self.logger.error(f"Image generation failed: {e}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Image generation failed: {str(e)}"
            )
    
    def _create_request(self, input_data: Dict[str, Any]) -> ImageGenerationRequest:
        """Create image generation request from input data."""
        return ImageGenerationRequest(
            prompt=input_data["prompt"],
            size=input_data.get("size", "1024x1024"),
            quality=input_data.get("quality", "standard"),
            style=input_data.get("style", "vivid"),
            n=input_data.get("n", 1),
            response_format=input_data.get("response_format", "b64_json")
        )
    
    async def _generate_images(
        self,
        request: ImageGenerationRequest,
        context: Dict[str, Any]
    ) -> List[GeneratedImage]:
        """
        Generate images using DALL-E 3 API.
        
        Args:
            request: Generation request
            context: Execution context
            
        Returns:
            List of generated images
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "dall-e-3",
            "prompt": request.prompt,
            "size": request.size,
            "quality": request.quality,
            "style": request.style,
            "n": request.n,
            "response_format": request.response_format
        }
        
        tenant_id = context.get("tenant_id", "unknown")
        self.logger.info(
            f"Generating image for tenant {tenant_id}",
            extra={
                "prompt_length": len(request.prompt),
                "size": request.size,
                "quality": request.quality,
                "style": request.style,
                "n": request.n
            }
        )
        
        async with self._http_session() as client:
            response = await client.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=120.0  # DALL-E can take a while
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                error_message = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
                raise RuntimeError(f"DALL-E API error: {error_message}")
            
            response_data = response.json()
            
            images = []
            for img_data in response_data.get("data", []):
                if request.response_format == "b64_json":
                    image_bytes = base64.b64decode(img_data["b64_json"])
                else:
                    # For URL format, download the image
                    img_response = await client.get(img_data["url"])
                    image_bytes = img_response.content
                
                images.append(GeneratedImage(
                    image_data=image_bytes,
                    revised_prompt=img_data.get("revised_prompt"),
                    size=request.size,
                    url=img_data.get("url")
                ))
            
            return images
    
    async def _save_images(
        self,
        images: List[GeneratedImage],
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[str]:
        """
        Save generated images to files.
        
        Args:
            images: Generated images
            input_data: Input parameters
            context: Execution context
            
        Returns:
            List of saved file paths
        """
        saved_files = []
        tenant_id = context.get("tenant_id", "unknown")
        prefix = input_data.get("filename_prefix", "dalle_generated")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create tenant-specific directory
        tenant_dir = self.save_directory / tenant_id
        tenant_dir.mkdir(exist_ok=True)
        
        for i, image in enumerate(images):
            try:
                # Generate filename
                suffix = f"_{i+1}" if len(images) > 1 else ""
                filename = f"{prefix}_{timestamp}{suffix}.png"
                filepath = tenant_dir / filename
                
                # Save image
                with open(filepath, "wb") as f:
                    f.write(image.image_data)
                
                # Update image object
                image.filename = str(filepath)
                saved_files.append(str(filepath))
                
                # Also save metadata
                metadata_file = filepath.with_suffix(".json")
                metadata = {
                    "original_prompt": input_data["prompt"],
                    "revised_prompt": image.revised_prompt,
                    "size": image.size,
                    "generated_at": datetime.now().isoformat(),
                    "tenant_id": tenant_id,
                    "filename": filename
                }
                
                with open(metadata_file, "w") as f:
                    json.dump(metadata, f, indent=2)
                
                self.logger.info(f"Saved image: {filepath}")
                
            except Exception as e:
                self.logger.error(f"Failed to save image {i}: {e}")
        
        return saved_files
    
    async def get_image_info(self, filepath: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a saved image.
        
        Args:
            filepath: Path to the image file
            
        Returns:
            Image information or None if not found
        """
        try:
            path = Path(filepath)
            if not path.exists():
                return None
            
            # Load metadata if available
            metadata_file = path.with_suffix(".json")
            metadata = {}
            if metadata_file.exists():
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
            
            # Get image properties
            with Image.open(path) as img:
                width, height = img.size
                format_type = img.format
                mode = img.mode
            
            return {
                "filepath": str(path),
                "filename": path.name,
                "size": f"{width}x{height}",
                "format": format_type,
                "mode": mode,
                "file_size_bytes": path.stat().st_size,
                **metadata
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get image info for {filepath}: {e}")
            return None
    
    async def list_generated_images(
        self,
        tenant_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List generated images for a tenant.
        
        Args:
            tenant_id: Tenant ID
            limit: Maximum number of images to return
            
        Returns:
            List of image information
        """
        try:
            tenant_dir = self.save_directory / tenant_id
            if not tenant_dir.exists():
                return []
            
            image_files = list(tenant_dir.glob("*.png"))
            image_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            images = []
            for img_file in image_files[:limit]:
                info = await self.get_image_info(str(img_file))
                if info:
                    images.append(info)
            
            return images
            
        except Exception as e:
            self.logger.error(f"Failed to list images for tenant {tenant_id}: {e}")
            return []
    
    async def cleanup(self) -> bool:
        """Clean up resources."""
        try:
            await super().cleanup()
            self.logger.info("DALL-E tool cleaned up successfully")
            return True
        except Exception as e:
            self.logger.error(f"DALL-E tool cleanup failed: {e}")
            return False