"""
AutoGen-based agents for the Varga AI platform.
"""

from agents.base.base_agent import BaseAgent, AgentConfig, AgentResponse
from agents.categories.assistant.smart_assistant_agent import SmartAssistantAgent

__all__ = [
    "BaseAgent",
    "AgentConfig", 
    "AgentResponse",
    "SmartAssistantAgent"
]