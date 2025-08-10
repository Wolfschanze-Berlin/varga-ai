"""
Browser Automation Integration Package.

This package provides browser automation capabilities using browser-use library
integrated with the existing playwright MCP functionality. It includes:

- BrowserOrchestrator: Main orchestration and routing logic
- BrowserUseWrapper: Wrapper for browser-use library
- BrowserSessionManager: Session lifecycle and result management
- TaskClassifier: AI-powered task classification and routing
- Configuration management for all components

Usage:
    from src.tools.integrations.browser_automation import (
        BrowserOrchestrator,
        BrowserUseWrapper,
        BrowserSessionManager,
        TaskClassifier,
        get_browser_automation_config
    )
    
    # Initialize with configuration
    config = get_browser_automation_config()
    orchestrator = BrowserOrchestrator(config.get_component_config("orchestrator"))
    
    # Setup and execute tasks
    await orchestrator.setup()
    result = await orchestrator.execute({
        "description": "Extract product prices from ecommerce site",
        "url": "https://example-store.com/products",
        "parameters": {"category": "electronics"}
    })
"""

from .browser_orchestrator import (
    BrowserOrchestrator,
    RoutingStrategy,
    BrowserTask,
    BrowserTaskResult
)
from .browser_use_wrapper import (
    BrowserUseWrapper,
    BrowserSession,
    BrowserUseConfig
)
from .session_manager import (
    BrowserSessionManager,
    SessionState,
    SessionInfo,
    TaskResultStorage
)
from .task_classifier import (
    TaskClassifier,
    TaskType,
    TaskComplexity,
    TaskClassificationResult,
    ClassificationRule,
    SiteProfile
)
from .config import (
    BrowserAutomationConfig,
    ConfigurationManager,
    get_browser_automation_config,
    update_browser_automation_config,
    get_component_config
)

# Version information
__version__ = "0.1.0"
__author__ = "Varga AI Team"
__description__ = "Browser automation integration for AutoGen SME platform"

# Package metadata
__all__ = [
    # Main classes
    "BrowserOrchestrator",
    "BrowserUseWrapper", 
    "BrowserSessionManager",
    "TaskClassifier",
    
    # Configuration
    "BrowserAutomationConfig",
    "ConfigurationManager",
    "get_browser_automation_config",
    "update_browser_automation_config",
    "get_component_config",
    
    # Enums and data classes
    "RoutingStrategy",
    "TaskType",
    "TaskComplexity",
    "SessionState",
    
    # Data models
    "BrowserTask",
    "BrowserTaskResult",
    "BrowserSession",
    "BrowserUseConfig",
    "SessionInfo",
    "TaskResultStorage",
    "TaskClassificationResult",
    "ClassificationRule",
    "SiteProfile",
    
    # Package metadata
    "__version__",
    "__author__",
    "__description__"
]

# Package-level initialization
def _check_dependencies():
    """Check if required dependencies are available."""
    import importlib
    
    dependencies = {
        "browser_use": "browser-use library for AI browser automation",
        "playwright": "Playwright for browser control",
        "pydantic": "Data validation and settings management",
        "pydantic_settings": "Settings management for Pydantic",
        "aiofiles": "Asynchronous file operations",
        "httpx": "HTTP client library"
    }
    
    missing_deps = []
    for dep, description in dependencies.items():
        try:
            importlib.import_module(dep.replace("-", "_"))
        except ImportError:
            missing_deps.append(f"{dep} ({description})")
    
    if missing_deps:
        import warnings
        warnings.warn(
            f"Browser automation integration has missing dependencies: {', '.join(missing_deps)}. "
            f"Some functionality may not be available.",
            ImportWarning,
            stacklevel=2
        )

# Check dependencies on import
_check_dependencies()

# Convenience functions for quick setup
async def create_browser_orchestrator(config_overrides=None):
    """
    Create and setup a browser orchestrator with default configuration.
    
    Args:
        config_overrides: Optional dictionary to override default config values
        
    Returns:
        Configured and initialized BrowserOrchestrator instance
    """
    from .config import get_browser_automation_config
    
    config = get_browser_automation_config()
    
    if config_overrides:
        # Apply config overrides
        orchestrator_config = config.get_component_config("orchestrator")
        orchestrator_config.update(config_overrides)
    else:
        orchestrator_config = config.get_component_config("orchestrator")
    
    orchestrator = BrowserOrchestrator(orchestrator_config)
    await orchestrator.setup()
    
    return orchestrator

async def create_browser_use_wrapper(config_overrides=None):
    """
    Create and setup a browser-use wrapper with default configuration.
    
    Args:
        config_overrides: Optional dictionary to override default config values
        
    Returns:
        Configured and initialized BrowserUseWrapper instance
    """
    from .config import get_browser_automation_config
    
    config = get_browser_automation_config()
    
    if config_overrides:
        # Apply config overrides
        wrapper_config = config.get_component_config("browser_use")
        wrapper_config.update(config_overrides)
    else:
        wrapper_config = config.get_component_config("browser_use")
    
    wrapper = BrowserUseWrapper(wrapper_config)
    await wrapper.setup()
    
    return wrapper

# Package-level logger
def get_package_logger():
    """Get logger for browser automation package."""
    from ....log_service import get_logger
    return get_logger("browser_automation")

# Export logger for convenience
logger = get_package_logger()