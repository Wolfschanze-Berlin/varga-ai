"""
Configuration management for browser automation integration.
Provides centralized configuration handling for all browser automation components.
"""

from __future__ import annotations
import os
from typing import Any, Dict, List, Optional
from pathlib import Path

from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings

from ....log_service import get_logger


class BrowserUseConfig(BaseModel):
    """Configuration for browser-use wrapper."""
    
    headless: bool = True
    browser_type: str = "chromium"
    viewport_width: int = 1920
    viewport_height: int = 1080
    timeout_seconds: int = 30
    max_sessions: int = 5
    session_timeout_minutes: int = 30
    screenshots_enabled: bool = True
    screenshots_dir: str = "screenshots"
    user_agent: Optional[str] = None
    proxy: Optional[str] = None
    extra_args: List[str] = Field(default_factory=list)
    
    @validator('browser_type')
    def validate_browser_type(cls, v):
        allowed_types = ['chromium', 'firefox', 'webkit']
        if v not in allowed_types:
            raise ValueError(f'Browser type must be one of {allowed_types}')
        return v
    
    @validator('timeout_seconds')
    def validate_timeout(cls, v):
        if v <= 0 or v > 300:
            raise ValueError('Timeout must be between 1 and 300 seconds')
        return v


class SessionManagerConfig(BaseModel):
    """Configuration for browser session manager."""
    
    storage_dir: str = "browser_sessions"
    max_sessions: int = 100
    session_timeout_minutes: int = 60
    cleanup_interval_seconds: int = 300
    enable_persistence: bool = True
    max_result_age_days: int = 7
    
    @validator('max_sessions')
    def validate_max_sessions(cls, v):
        if v <= 0 or v > 1000:
            raise ValueError('Max sessions must be between 1 and 1000')
        return v


class TaskClassifierConfig(BaseModel):
    """Configuration for task classifier."""
    
    confidence_threshold: float = 0.7
    enable_url_analysis: bool = True
    enable_site_profiling: bool = True
    cache_site_profiles: bool = True
    
    @validator('confidence_threshold')
    def validate_confidence(cls, v):
        if v < 0.0 or v > 1.0:
            raise ValueError('Confidence threshold must be between 0.0 and 1.0')
        return v


class OrchestratorConfig(BaseModel):
    """Configuration for browser orchestrator."""
    
    routing_strategy: str = "best_fit"
    default_timeout_seconds: int = 300
    max_concurrent_sessions: int = 5
    enable_screenshots: bool = True
    screenshot_on_error: bool = True
    
    @validator('routing_strategy')
    def validate_routing_strategy(cls, v):
        allowed_strategies = ['browser_use_first', 'playwright_first', 'best_fit', 'parallel']
        if v not in allowed_strategies:
            raise ValueError(f'Routing strategy must be one of {allowed_strategies}')
        return v


class BrowserAutomationConfig(BaseSettings):
    """Main configuration class for browser automation."""
    
    # Component configurations
    browser_use: BrowserUseConfig = Field(default_factory=BrowserUseConfig)
    session_manager: SessionManagerConfig = Field(default_factory=SessionManagerConfig)
    task_classifier: TaskClassifierConfig = Field(default_factory=TaskClassifierConfig)
    orchestrator: OrchestratorConfig = Field(default_factory=OrchestratorConfig)
    
    # Global settings
    enabled: bool = True
    log_level: str = "INFO"
    debug_mode: bool = False
    performance_monitoring: bool = True
    
    # Resource limits
    max_memory_mb: int = 2048
    max_cpu_percent: int = 80
    
    # Integration settings
    playwright_mcp_enabled: bool = True
    fallback_to_playwright: bool = True
    
    class Config:
        env_prefix = "BROWSER_AUTOMATION_"
        env_nested_delimiter = "__"
        case_sensitive = False
    
    def get_component_config(self, component: str) -> Dict[str, Any]:
        """
        Get configuration for a specific component.
        
        Args:
            component: Component name (browser_use, session_manager, task_classifier, orchestrator)
            
        Returns:
            Configuration dictionary for the component
        """
        component_configs = {
            "browser_use": self.browser_use.dict(),
            "session_manager": self.session_manager.dict(),
            "task_classifier": self.task_classifier.dict(),
            "orchestrator": self.orchestrator.dict()
        }
        
        if component not in component_configs:
            raise ValueError(f"Unknown component: {component}")
        
        return component_configs[component]
    
    def validate_configuration(self) -> List[str]:
        """
        Validate the entire configuration and return any issues.
        
        Returns:
            List of validation issues (empty if no issues)
        """
        issues = []
        
        # Check storage directories
        storage_dir = Path(self.session_manager.storage_dir)
        if not storage_dir.parent.exists():
            issues.append(f"Parent directory of storage_dir does not exist: {storage_dir.parent}")
        
        # Check screenshot directory
        if self.browser_use.screenshots_enabled:
            screenshot_dir = Path(self.browser_use.screenshots_dir)
            if not screenshot_dir.parent.exists():
                issues.append(f"Parent directory of screenshots_dir does not exist: {screenshot_dir.parent}")
        
        # Validate resource limits
        if self.max_memory_mb < 512:
            issues.append("max_memory_mb should be at least 512MB for browser automation")
        
        if self.max_cpu_percent < 20:
            issues.append("max_cpu_percent should be at least 20% for browser automation")
        
        # Check session limits consistency
        if self.orchestrator.max_concurrent_sessions > self.session_manager.max_sessions:
            issues.append("orchestrator.max_concurrent_sessions exceeds session_manager.max_sessions")
        
        return issues


class ConfigurationManager:
    """Manager for browser automation configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.logger = get_logger("browser_automation_config")
        self.config_path = config_path
        self._config: Optional[BrowserAutomationConfig] = None
    
    def load_config(self) -> BrowserAutomationConfig:
        """
        Load configuration from environment variables and/or config file.
        
        Returns:
            Loaded configuration
        """
        try:
            # Load from environment variables
            config = BrowserAutomationConfig()
            
            # Validate configuration
            issues = config.validate_configuration()
            if issues:
                self.logger.warning(f"Configuration validation issues: {issues}")
                for issue in issues:
                    self.logger.warning(f"  - {issue}")
            
            self._config = config
            
            self.logger.info("Browser automation configuration loaded successfully")
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise
    
    def get_config(self) -> BrowserAutomationConfig:
        """
        Get current configuration, loading if necessary.
        
        Returns:
            Current configuration
        """
        if self._config is None:
            self._config = self.load_config()
        
        return self._config
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """
        Update configuration with new values.
        
        Args:
            updates: Dictionary of configuration updates
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            if self._config is None:
                self.load_config()
            
            # Apply updates (this is a simplified implementation)
            # In a full implementation, you'd want to handle nested updates properly
            for key, value in updates.items():
                if hasattr(self._config, key):
                    setattr(self._config, key, value)
            
            # Validate updated configuration
            issues = self._config.validate_configuration()
            if issues:
                self.logger.error(f"Configuration validation failed after update: {issues}")
                return False
            
            self.logger.info("Configuration updated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update configuration: {e}")
            return False
    
    def export_config(self) -> Dict[str, Any]:
        """
        Export current configuration as dictionary.
        
        Returns:
            Configuration dictionary
        """
        if self._config is None:
            self.load_config()
        
        return self._config.dict()


# Global configuration manager instance
_config_manager = ConfigurationManager()

def get_browser_automation_config() -> BrowserAutomationConfig:
    """Get the global browser automation configuration."""
    return _config_manager.get_config()

def update_browser_automation_config(updates: Dict[str, Any]) -> bool:
    """Update the global browser automation configuration."""
    return _config_manager.update_config(updates)

def get_component_config(component: str) -> Dict[str, Any]:
    """Get configuration for a specific component."""
    config = get_browser_automation_config()
    return config.get_component_config(component)


# Environment variable examples for documentation
ENVIRONMENT_VARIABLE_EXAMPLES = {
    "BROWSER_AUTOMATION_ENABLED": "true",
    "BROWSER_AUTOMATION_LOG_LEVEL": "INFO",
    "BROWSER_AUTOMATION_DEBUG_MODE": "false",
    "BROWSER_AUTOMATION_BROWSER_USE__HEADLESS": "true",
    "BROWSER_AUTOMATION_BROWSER_USE__BROWSER_TYPE": "chromium",
    "BROWSER_AUTOMATION_BROWSER_USE__TIMEOUT_SECONDS": "30",
    "BROWSER_AUTOMATION_SESSION_MANAGER__MAX_SESSIONS": "100",
    "BROWSER_AUTOMATION_SESSION_MANAGER__STORAGE_DIR": "browser_sessions",
    "BROWSER_AUTOMATION_ORCHESTRATOR__ROUTING_STRATEGY": "best_fit",
    "BROWSER_AUTOMATION_ORCHESTRATOR__MAX_CONCURRENT_SESSIONS": "5",
    "BROWSER_AUTOMATION_TASK_CLASSIFIER__CONFIDENCE_THRESHOLD": "0.7"
}