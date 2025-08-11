"""
Configuration management for the AutoGen SME platform.
Handles environment variables, API keys, and tool configurations.
"""

from __future__ import annotations
import os
from typing import Optional, Dict, Any, List, Annotated
from pathlib import Path
from pydantic import BaseModel, Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import secrets


class ToolConfig(BaseSettings):
    """Base configuration for tool settings."""
    model_config = ConfigDict(
        env_prefix="TOOL_",
        case_sensitive=False,
        validate_default=True,
        extra='ignore'  # Changed to allow flexibility
    )
    
    name: str
    enabled: bool = True
    rate_limit_per_minute: Annotated[int, Field(ge=1, le=10000)] = 60
    rate_limit_per_hour: Annotated[int, Field(ge=1, le=100000)] = 1000
    timeout_seconds: Annotated[int, Field(ge=1, le=300)] = 30
    retry_attempts: Annotated[int, Field(ge=0, le=10)] = 3
    retry_delay_seconds: Annotated[float, Field(ge=0.1, le=60.0)] = 1.0


class WebSearchConfig(ToolConfig):
    """Configuration for web search tool."""
    
    name: str = "web_search"
    search_engine: Annotated[str, Field(pattern=r'^(serpapi|google_search_api|bing)$')] = "serpapi"
    api_key: Optional[str] = Field(None, env="SERPAPI_API_KEY", exclude=True)  # Exclude from serialization for security
    max_results: Annotated[int, Field(ge=1, le=100)] = 10
    safe_search: bool = True
    language: Annotated[str, Field(min_length=2, max_length=5)] = "en"
    country: Annotated[str, Field(min_length=2, max_length=5)] = "us"
    
    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v: Optional[str], info) -> Optional[str]:
        # Only require API key if tool is enabled
        if info.data.get('enabled', True) and not v:
            raise ValueError("API key is required for web search when enabled")
        return v


class TextGenerationConfig(ToolConfig):
    """Configuration for text generation tool."""
    
    name: str = "text_generation"
    model_provider: Annotated[str, Field(pattern=r'^(openai|anthropic|azure_openai)$')] = "openai"
    model_name: str = "gpt-4"
    api_key: Optional[str] = Field(None, env="OPENAI_API_KEY", exclude=True)
    max_tokens: Annotated[int, Field(ge=1, le=32000)] = 2000
    temperature: Annotated[float, Field(ge=0.0, le=2.0)] = 0.7
    top_p: Annotated[float, Field(ge=0.0, le=1.0)] = 1.0
    frequency_penalty: Annotated[float, Field(ge=-2.0, le=2.0)] = 0.0
    presence_penalty: Annotated[float, Field(ge=-2.0, le=2.0)] = 0.0
    
    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v: Optional[str], info) -> Optional[str]:
        # Only require API key if tool is enabled
        if info.data.get('enabled', True) and not v:
            raise ValueError("API key is required for text generation when enabled")
        return v


class ChatbotConfig(ToolConfig):
    """Configuration for chatbot interface tool."""
    
    name: str = "chatbot_interface"
    model_provider: Annotated[str, Field(pattern=r'^(openai|anthropic)$')] = "openai"
    model_name: str = "gpt-4"
    api_key: Optional[str] = Field(None, env="OPENAI_API_KEY", exclude=True)
    max_conversation_length: Annotated[int, Field(ge=5, le=200)] = 50
    context_window_tokens: Annotated[int, Field(ge=1000, le=128000)] = 8000
    system_prompt_template: Annotated[str, Field(min_length=10)] = "You are a helpful AI assistant for {business_name}."
    fallback_responses: List[str] = Field(default_factory=lambda: [
        "I apologize, but I'm having trouble processing that request. Please try again.",
        "Let me connect you with a human agent who can better assist you.",
        "I'm experiencing some technical difficulties. Please contact our support team."
    ])
    
    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v: Optional[str], info) -> Optional[str]:
        # Only require API key if tool is enabled
        if info.data.get('enabled', True) and not v:
            raise ValueError("API key is required for chatbot when enabled")
        return v


class PlatformSettings(BaseSettings):
    """Main platform configuration settings."""
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        validate_default=True,
        extra='ignore',  # Changed from 'forbid' to 'ignore' to allow tool-specific env vars
        secrets_dir=Path.home() / '.secrets' if Path.home().exists() else None
    )
    
    # Environment
    environment: Annotated[str, Field(pattern=r'^(development|staging|production)$')] = "development"
    debug: bool = Field(default_factory=lambda: False, env="DEBUG")
    
    # Logging
    log_level: Annotated[str, Field(pattern=r'^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$')] = "INFO"
    log_file: Optional[Path] = Field(None, env="LOG_FILE")
    
    # Database
    database_url: Optional[str] = Field(None, env="DATABASE_URL", exclude=True)
    redis_url: str = Field("redis://localhost:6379", env="REDIS_URL")
    
    # Security
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32), env="SECRET_KEY", exclude=True)
    allowed_hosts: List[str] = Field(default_factory=lambda: ["localhost", "127.0.0.1"])
    
    # AutoGen
    autogen_cache_dir: Path = Field(default_factory=lambda: Path(".cache/autogen"), env="AUTOGEN_CACHE_DIR")
    autogen_work_dir: Path = Field(default_factory=lambda: Path("./work_dir"), env="AUTOGEN_WORK_DIR")
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN: Optional[str] = Field(None, env="TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: Optional[str] = Field(None, env="TELEGRAM_CHAT_ID")
    
    # Tool Configurations (disabled by default to avoid requiring API keys)
    web_search: WebSearchConfig = Field(default_factory=lambda: WebSearchConfig(enabled=False))
    text_generation: TextGenerationConfig = Field(default_factory=lambda: TextGenerationConfig(enabled=False))
    chatbot: ChatbotConfig = Field(default_factory=lambda: ChatbotConfig(enabled=False))
    
    # Rate Limiting
    global_rate_limit_per_minute: Annotated[int, Field(ge=1, le=100000)] = 1000
    global_rate_limit_per_hour: Annotated[int, Field(ge=1, le=1000000)] = 10000
        
    @field_validator('log_file')
    @classmethod
    def validate_log_file(cls, v: Optional[Path]) -> Optional[Path]:
        if v is not None:
            v.parent.mkdir(parents=True, exist_ok=True)
        return v
    
    @field_validator('autogen_cache_dir', 'autogen_work_dir')
    @classmethod
    def validate_directories(cls, v: Path) -> Path:
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"


class ConfigManager:
    """Configuration manager for the platform."""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            env_file: Optional path to environment file
        """
        if env_file:
            load_dotenv(env_file)
        else:
            # Load from default locations
            load_dotenv()
        
        self._settings = PlatformSettings()
    
    @property
    def settings(self) -> PlatformSettings:
        """Get platform settings."""
        return self._settings
    
    def get_tool_config(self, tool_name: str) -> Optional[ToolConfig]:
        """
        Get configuration for a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool configuration or None if not found
        """
        tool_configs = {
            "web_search": self._settings.web_search,
            "text_generation": self._settings.text_generation,
            "chatbot_interface": self._settings.chatbot
        }
        return tool_configs.get(tool_name)
    
    def update_tool_config(self, tool_name: str, config_data: Dict[str, Any]) -> bool:
        """
        Update tool configuration at runtime.
        
        Args:
            tool_name: Name of the tool
            config_data: Configuration data to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            tool_config = self.get_tool_config(tool_name)
            if not tool_config:
                return False
            
            for key, value in config_data.items():
                if hasattr(tool_config, key):
                    setattr(tool_config, key, value)
            
            return True
        except Exception:
            return False
    
    def validate_configuration(self) -> Dict[str, List[str]]:
        """
        Validate all configurations and return any errors.
        
        Returns:
            Dictionary with tool names as keys and list of validation errors as values
        """
        errors = {}
        
        # Validate each tool configuration
        tools = ["web_search", "text_generation", "chatbot_interface"]
        for tool_name in tools:
            tool_config = self.get_tool_config(tool_name)
            if tool_config:
                try:
                    # Re-validate the configuration
                    tool_config.__class__(**tool_config.model_dump())
                except Exception as e:
                    errors[tool_name] = [str(e)]
        
        return errors


# Global configuration instance (lazy initialization)
_config_manager = None

def get_settings() -> PlatformSettings:
    """Get platform settings."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager.settings

def get_tool_config(tool_name: str) -> Optional[ToolConfig]:
    """Get tool configuration."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager.get_tool_config(tool_name)

def get_config_manager() -> ConfigManager:
    """Get configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

# Create singleton settings instance for easy import
settings = get_settings()