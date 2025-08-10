"""
Centralized logging service using loguru for the AutoGen SME platform.
Provides structured logging with correlation IDs and tenant isolation.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger
import json


class LoggerService:
    """Centralized logging service with tenant isolation and structured logging."""
    
    def __init__(self, log_level: str = "INFO", log_file: Optional[str] = None):
        """
        Initialize the logger service.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional file path for log output
        """
        self.log_level = log_level
        self.log_file = log_file
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        """Configure loguru logger with custom formatting."""
        # Remove default handler
        logger.remove()
        
        # Custom format for structured logging
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        
        # Console handler
        logger.add(
            sys.stderr,
            format=log_format,
            level=self.log_level,
            colorize=True,
            backtrace=True,
            diagnose=True
        )
        
        # File handler if specified
        if self.log_file:
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.add(
                self.log_file,
                format=log_format,
                level=self.log_level,
                rotation="10 MB",
                retention="30 days",
                compression="gz",
                serialize=False,
                backtrace=True,
                diagnose=True
            )
    
    def get_logger(self, name: str) -> "LoggerService":
        """Get a logger instance with the specified name."""
        return logger.bind(name=name)
    
    def log_agent_action(
        self, 
        tenant_id: str,
        agent_name: str, 
        action: str, 
        details: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Log agent actions with structured data.
        
        Args:
            tenant_id: Tenant identifier for isolation
            agent_name: Name of the agent performing the action
            action: Action being performed
            details: Additional details about the action
            correlation_id: Optional correlation ID for request tracking
        """
        log_data = {
            "tenant_id": tenant_id,
            "agent_name": agent_name,
            "action": action,
            "details": details,
            "correlation_id": correlation_id
        }
        
        logger.bind(**log_data).info(f"Agent action: {action}")
    
    def log_tool_execution(
        self,
        tenant_id: str,
        tool_name: str,
        method: str,
        status: str,
        duration_ms: float,
        error: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Log tool execution metrics.
        
        Args:
            tenant_id: Tenant identifier
            tool_name: Name of the tool
            method: Method being executed
            status: Execution status (success/error)
            duration_ms: Execution duration in milliseconds
            error: Error message if status is error
            correlation_id: Optional correlation ID
        """
        log_data = {
            "tenant_id": tenant_id,
            "tool_name": tool_name,
            "method": method,
            "status": status,
            "duration_ms": duration_ms,
            "error": error,
            "correlation_id": correlation_id
        }
        
        if status == "error":
            logger.bind(**log_data).error(f"Tool execution failed: {tool_name}.{method}")
        else:
            logger.bind(**log_data).info(f"Tool execution completed: {tool_name}.{method}")
    
    def log_workflow_event(
        self,
        tenant_id: str,
        workflow_id: str,
        event_type: str,
        details: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Log workflow events for orchestration tracking.
        
        Args:
            tenant_id: Tenant identifier
            workflow_id: Workflow identifier
            event_type: Type of workflow event
            details: Event details
            correlation_id: Optional correlation ID
        """
        log_data = {
            "tenant_id": tenant_id,
            "workflow_id": workflow_id,
            "event_type": event_type,
            "details": details,
            "correlation_id": correlation_id
        }
        
        logger.bind(**log_data).info(f"Workflow event: {event_type}")


# Global logger instance
_logger_service = LoggerService()

# Export convenient functions
def get_logger(name: str = "varga-ai"):
    """Get a logger instance."""
    return _logger_service.get_logger(name)

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """Setup logging configuration."""
    global _logger_service
    _logger_service = LoggerService(log_level=log_level, log_file=log_file)
    return _logger_service