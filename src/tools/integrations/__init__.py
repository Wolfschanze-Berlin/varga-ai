"""
Tools Integrations Package.

This package contains integrations with external services and tools
for the AutoGen SME automation platform.

Available integrations:
- browser_automation: Browser automation using browser-use and playwright
- Future integrations: CRM tools, accounting software, communication platforms
"""

# Import browser automation integration
try:
    from .browser_automation import (
        BrowserOrchestrator,
        BrowserUseWrapper,
        BrowserSessionManager,
        TaskClassifier,
        get_browser_automation_config,
        create_browser_orchestrator,
        create_browser_use_wrapper
    )
    BROWSER_AUTOMATION_AVAILABLE = True
except ImportError as e:
    # Browser automation not available, log but don't fail
    import warnings
    warnings.warn(f"Browser automation integration not available: {e}", ImportWarning)
    BROWSER_AUTOMATION_AVAILABLE = False

__version__ = "0.1.0"
__author__ = "Varga AI Team"

# Export available integrations
__all__ = []

if BROWSER_AUTOMATION_AVAILABLE:
    __all__.extend([
        "BrowserOrchestrator",
        "BrowserUseWrapper",
        "BrowserSessionManager",
        "TaskClassifier",
        "get_browser_automation_config",
        "create_browser_orchestrator",
        "create_browser_use_wrapper"
    ])

# Metadata about available integrations
AVAILABLE_INTEGRATIONS = {
    "browser_automation": {
        "available": BROWSER_AUTOMATION_AVAILABLE,
        "description": "Browser automation using browser-use and playwright",
        "version": "0.1.0",
        "components": [
            "BrowserOrchestrator",
            "BrowserUseWrapper", 
            "BrowserSessionManager",
            "TaskClassifier"
        ]
    }
}

def get_available_integrations():
    """Get information about available integrations."""
    return AVAILABLE_INTEGRATIONS

def is_integration_available(integration_name: str) -> bool:
    """Check if a specific integration is available."""
    return AVAILABLE_INTEGRATIONS.get(integration_name, {}).get("available", False)