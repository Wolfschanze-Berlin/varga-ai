"""
Centralized Configuration Manager for Varga AI Platform.

Handles all environment variables and configuration loading
for the entire application.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass
from enum import Enum

from dotenv import load_dotenv
from loguru import logger


class Environment(Enum):
    """Application environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str
    redis_url: str
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create from environment variables."""
        return cls(
            url=os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/varga_ai"),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379")
        )


@dataclass
class TelegramConfig:
    """Telegram bot configuration."""
    bot_token: str
    chat_id: Optional[int] = None
    
    @classmethod
    def from_env(cls) -> "TelegramConfig":
        """Create from environment variables."""
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        return cls(
            bot_token=bot_token,
            chat_id=int(chat_id) if chat_id else None
        )


@dataclass
class OpenAIConfig:
    """OpenAI configuration."""
    api_key: str
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2000
    
    @classmethod
    def from_env(cls) -> "OpenAIConfig":
        """Create from environment variables."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required")
        
        return cls(
            api_key=api_key,
            model=os.getenv("OPENAI_MODEL", "gpt-4"),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
        )


@dataclass
class AppConfig:
    """Main application configuration."""
    environment: Environment
    debug: bool
    log_level: str
    log_file: str
    secret_key: str
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create from environment variables."""
        return cls(
            environment=Environment(os.getenv("ENVIRONMENT", "development")),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("LOG_FILE", "logs/varga-ai.log"),
            secret_key=os.getenv("SECRET_KEY", "your-secret-key-here")
        )


class ConfigManager:
    """
    Centralized configuration manager for the entire application.
    
    This is a singleton class that loads configuration once and provides
    it to all components of the application.
    """
    
    _instance: Optional["ConfigManager"] = None
    _initialized: bool = False
    
    def __new__(cls) -> "ConfigManager":
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize configuration manager."""
        if not self._initialized:
            self._load_environment()
            self._initialized = True
    
    def _load_environment(self) -> None:
        """Load environment variables from .env file."""
        # Find .env file - check multiple possible locations
        possible_paths = [
            Path.cwd() / ".env",
            Path(__file__).parent.parent.parent / ".env",
            Path.home() / ".env"
        ]
        
        env_loaded = False
        for env_path in possible_paths:
            if env_path.exists():
                load_dotenv(env_path, override=True)
                logger.debug(f"Loaded environment from: {env_path}")
                env_loaded = True
                break
        
        if not env_loaded:
            logger.warning("No .env file found, using system environment variables")
        
        # Load configurations
        try:
            self.app = AppConfig.from_env()
            self.database = DatabaseConfig.from_env()
            self.openai = OpenAIConfig.from_env()
            
            # Optional configurations
            try:
                self.telegram = TelegramConfig.from_env()
            except ValueError as e:
                logger.warning(f"Telegram config not available: {e}")
                self.telegram = None
            
            logger.info("Configuration loaded successfully")
            
            # Log configuration (without sensitive data)
            logger.debug(f"Environment: {self.app.environment.value}")
            logger.debug(f"Debug mode: {self.app.debug}")
            logger.debug(f"OpenAI Model: {self.openai.model}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def get_llm_config(self) -> Dict[str, Any]:
        """
        Get LLM configuration for AutoGen agents.
        
        Returns:
            Dictionary with LLM configuration
        """
        return {
            "model": self.openai.model,
            "temperature": self.openai.temperature,
            "max_tokens": self.openai.max_tokens,
            "config_list": [
                {
                    "model": self.openai.model,
                    "api_key": self.openai.api_key,
                }
            ]
        }
    
    def get_telegram_config(self) -> Dict[str, Any]:
        """
        Get Telegram bot configuration.
        
        Returns:
            Dictionary with Telegram configuration
        """
        if not self.telegram:
            raise ValueError("Telegram configuration not available")
        
        return {
            "bot_token": self.telegram.bot_token,
            "default_chat_id": self.telegram.chat_id
        }
    
    def reload(self) -> None:
        """Reload configuration from environment."""
        self._initialized = False
        self._load_environment()
        logger.info("Configuration reloaded")
    
    @classmethod
    def get_instance(cls) -> "ConfigManager":
        """
        Get the singleton instance of ConfigManager.
        
        Returns:
            ConfigManager instance
        """
        return cls()


# Convenience function for easy access
def get_config() -> ConfigManager:
    """
    Get the global configuration manager instance.
    
    Returns:
        ConfigManager instance
    """
    return ConfigManager.get_instance()