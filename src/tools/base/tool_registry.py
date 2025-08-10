"""
Tool registry for managing and discovering tools in the AutoGen SME platform.
Handles tool registration, discovery, and lifecycle management with async patterns.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Type, Any, Set, Final, TYPE_CHECKING
from abc import ABC
import importlib
import inspect
import asyncio
import weakref
from pathlib import Path
from collections import defaultdict
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from .tool_interface import BaseToolInterface, ToolMetadata, ToolCapability, ToolObserver
from .base_tool import BaseTool
from ...log_service import get_logger

if TYPE_CHECKING:
    from collections.abc import Mapping, AsyncIterator


@dataclass(frozen=True)
class ToolRegistrationInfo:
    """Information about a registered tool."""
    tool_class: Type[BaseToolInterface]
    config: Dict[str, Any]
    registration_time: float = field(default_factory=lambda: asyncio.get_event_loop().time())
    usage_count: int = 0
    last_used: Optional[float] = None


class ToolRegistrationError(Exception):
    """Raised when tool registration fails."""
    
    def __init__(self, message: str, tool_name: Optional[str] = None, cause: Optional[Exception] = None):
        super().__init__(message)
        self.tool_name = tool_name
        self.cause = cause


class AsyncToolRegistry(ToolObserver):
    """Async-optimized registry for managing platform tools."""
    
    def __init__(self):
        """Initialize the tool registry with async support."""
        self.logger = get_logger("tool_registry")
        
        # Thread-safe storage for tool information
        self._tools: Dict[str, ToolRegistrationInfo] = {}
        self._tool_instances: Dict[str, BaseToolInterface] = {}
        self._tool_metadata_cache: Dict[str, ToolMetadata] = {}
        
        # Locks for thread safety (using regular locks since RWLock is not in stdlib)
        self._registry_lock = asyncio.Lock()
        self._instance_lock = asyncio.Lock()
        
        # Lifecycle management
        self._cleanup_tasks: Set[asyncio.Task] = set()
        self._is_shutting_down = False
        
        # Statistics tracking
        self._stats = {
            'registrations': 0,
            'instance_creations': 0,
            'cleanup_operations': 0,
            'errors': 0
        }
    
    async def register_tool(
        self, 
        tool_class: Type[BaseToolInterface],
        config: Optional[Mapping[str, Any]] = None
    ) -> None:
        """
        Register a tool class in the registry with comprehensive validation.
        
        Args:
            tool_class: Tool class to register
            config: Optional configuration for the tool
            
        Raises:
            ToolRegistrationError: If registration fails
        """
        if self._is_shutting_down:
            raise ToolRegistrationError("Registry is shutting down")
        
        config_dict = dict(config) if config else {}
        
        async with self._registry_lock:
            try:
                # Comprehensive validation
                await self._validate_tool_class(tool_class, config_dict)
                
                # Create temporary instance to get metadata and validate config
                temp_instance = tool_class(config_dict)
                metadata = temp_instance.metadata
                
                # Validate metadata
                self._validate_metadata(metadata)
                
                # Check for name conflicts with enhanced checking
                await self._check_name_conflicts(metadata.name, tool_class)
                
                # Register the tool with usage tracking
                registration_info = ToolRegistrationInfo(
                    tool_class=tool_class,
                    config=config_dict
                )
                
                self._tools[metadata.name] = registration_info
                self._tool_metadata_cache[metadata.name] = metadata
                self._stats['registrations'] += 1
                
                self.logger.info(
                    f"Registered tool successfully",
                    extra={
                        "tool_name": metadata.name,
                        "tool_version": metadata.version,
                        "capabilities": [c.value for c in metadata.capabilities],
                        "config_keys": list(config_dict.keys()) if config_dict else []
                    }
                )
                
                # Cleanup temporary instance
                await temp_instance.cleanup()
                
            except Exception as e:
                self._stats['errors'] += 1
                tool_name = getattr(tool_class, '__name__', 'Unknown')
                self.logger.error(
                    f"Failed to register tool: {tool_name}",
                    extra={"error": str(e), "tool_class": tool_name}
                )
                raise ToolRegistrationError(
                    f"Failed to register tool {tool_name}: {e}",
                    tool_name=tool_name,
                    cause=e
                )
    
    async def _validate_tool_class(
        self, 
        tool_class: Type[BaseToolInterface], 
        config: Dict[str, Any]
    ) -> None:
        """Validate tool class comprehensively."""
        if not inspect.isclass(tool_class):
            raise ToolRegistrationError("Tool must be a class")
        
        if not issubclass(tool_class, BaseToolInterface):
            raise ToolRegistrationError(
                f"Tool class {tool_class.__name__} must inherit from BaseToolInterface"
            )
        
        if inspect.isabstract(tool_class):
            raise ToolRegistrationError(
                f"Tool class {tool_class.__name__} cannot be abstract"
            )
        
        # Validate required methods are implemented
        required_methods = ['metadata', 'execute', 'validate_input', 'health_check']
        for method_name in required_methods:
            if not hasattr(tool_class, method_name):
                raise ToolRegistrationError(
                    f"Tool class {tool_class.__name__} missing required method: {method_name}"
                )
    
    def _validate_metadata(self, metadata: ToolMetadata) -> None:
        """Validate tool metadata."""
        if not metadata.name or len(metadata.name.strip()) == 0:
            raise ToolRegistrationError("Tool name cannot be empty")
        
        if not metadata.capabilities:
            raise ToolRegistrationError("Tool must have at least one capability")
        
        # Validate schema structure
        if not isinstance(metadata.input_schema, dict):
            raise ToolRegistrationError("Input schema must be a dictionary")
        
        if not isinstance(metadata.output_schema, dict):
            raise ToolRegistrationError("Output schema must be a dictionary")
    
    async def _check_name_conflicts(self, name: str, tool_class: Type[BaseToolInterface]) -> None:
        """Check for naming conflicts."""
        if name in self._tools:
            existing_class = self._tools[name].tool_class
            if existing_class != tool_class:
                raise ToolRegistrationError(
                    f"Tool with name '{name}' is already registered "
                    f"with class {existing_class.__name__}"
                )
    
    async def unregister_tool(self, tool_name: str) -> bool:
        """
        Unregister a tool from the registry with proper cleanup.
        
        Args:
            tool_name: Name of the tool to unregister
            
        Returns:
            True if successful, False if tool not found
        """
        async with self._registry_lock:
            if tool_name not in self._tools:
                return False
            
            try:
                # Cleanup instance if exists
                await self._cleanup_tool_instance(tool_name)
                
                # Remove from registry
                del self._tools[tool_name]
                self._tool_metadata_cache.pop(tool_name, None)
                
                self.logger.info(f"Unregistered tool: {tool_name}")
                return True
                
            except Exception as e:
                self._stats['errors'] += 1
                self.logger.error(f"Failed to unregister tool {tool_name}: {e}")
                return False
    
    async def _cleanup_tool_instance(self, tool_name: str) -> None:
        """Cleanup a specific tool instance."""
        async with self._instance_lock:
            if tool_name in self._tool_instances:
                instance = self._tool_instances[tool_name]
                try:
                    await instance.cleanup()
                except Exception as e:
                    self.logger.warning(f"Error during cleanup of {tool_name}: {e}")
                finally:
                    del self._tool_instances[tool_name]
                    self._stats['cleanup_operations'] += 1
    
    async def get_tool_instance(
        self,
        tool_name: str,
        config_override: Optional[Mapping[str, Any]] = None,
        force_new: bool = False
    ) -> Optional[BaseToolInterface]:
        """
        Get a tool instance with enhanced caching and lifecycle management.
        
        Args:
            tool_name: Name of the tool
            config_override: Optional configuration override
            force_new: Force creation of new instance
            
        Returns:
            Tool instance or None if not found
        """
        async with self._registry_lock:
            if tool_name not in self._tools:
                return None
            
            registration_info = self._tools[tool_name]
        
        # Handle instance creation/retrieval
        async with self._instance_lock:
            # Use existing instance if no config override and not forcing new
            if (not force_new and 
                config_override is None and 
                tool_name in self._tool_instances):
                
                instance = self._tool_instances[tool_name]
                await self._update_usage_stats(tool_name)
                return instance
            
            try:
                # Create new instance
                config = registration_info.config.copy()
                if config_override:
                    config.update(config_override)
                
                instance = registration_info.tool_class(config)
                
                # Add registry as observer for cleanup notifications
                instance.add_observer(self)
                
                # Cache instance if no config override
                if not config_override:
                    self._tool_instances[tool_name] = instance
                
                self._stats['instance_creations'] += 1
                await self._update_usage_stats(tool_name)
                
                return instance
                
            except Exception as e:
                self._stats['errors'] += 1
                self.logger.error(
                    f"Failed to create tool instance: {tool_name}",
                    extra={"error": str(e)}
                )
                return None
    
    async def _update_usage_stats(self, tool_name: str) -> None:
        """Update usage statistics for a tool."""
        if tool_name in self._tools:
            current_info = self._tools[tool_name]
            # Create new immutable instance with updated stats
            updated_info = ToolRegistrationInfo(
                tool_class=current_info.tool_class,
                config=current_info.config,
                registration_time=current_info.registration_time,
                usage_count=current_info.usage_count + 1,
                last_used=asyncio.get_event_loop().time()
            )
            self._tools[tool_name] = updated_info
    
    @asynccontextmanager
    async def get_tool_context(
        self,
        tool_name: str,
        config_override: Optional[Mapping[str, Any]] = None
    ) -> AsyncIterator[BaseToolInterface]:
        """
        Async context manager for tool instances with automatic cleanup.
        
        Args:
            tool_name: Name of the tool
            config_override: Optional configuration override
            
        Yields:
            Tool instance
        """
        instance = await self.get_tool_instance(
            tool_name, 
            config_override, 
            force_new=True  # Always create new for context manager
        )
        
        if instance is None:
            raise ToolRegistrationError(f"Tool '{tool_name}' not found or failed to create")
        
        try:
            async with instance:  # Use tool's context manager
                yield instance
        finally:
            # Instance cleanup is handled by the tool's context manager
            pass
    
    async def list_tools(
        self,
        capability_filter: Optional[Set[ToolCapability]] = None,
        enabled_only: bool = True
    ) -> List[ToolMetadata]:
        """
        List registered tools with optional filtering.
        
        Args:
            capability_filter: Optional set of capabilities to filter by
            enabled_only: Whether to include only enabled tools
            
        Returns:
            List of tool metadata
        """
        async with self._registry_lock:
            tools = []
            
            for tool_name in self._tools:
                metadata = self._tool_metadata_cache[tool_name]
                config = self._tools[tool_name].config
                
                # Check if enabled
                if enabled_only and not config.get("enabled", True):
                    continue
                
                # Check capabilities filter
                if capability_filter:
                    tool_capabilities = set(metadata.capabilities)
                    if not capability_filter.intersection(tool_capabilities):
                        continue
                
                tools.append(metadata)
            
            return sorted(tools, key=lambda x: x.name)
    
    async def search_tools(self, query: str) -> List[ToolMetadata]:
        """
        Search tools by name, description, or tags with fuzzy matching.
        
        Args:
            query: Search query
            
        Returns:
            List of matching tool metadata sorted by relevance
        """
        query_lower = query.lower()
        matching_tools = []
        
        async with self._registry_lock:
            for metadata in self._tool_metadata_cache.values():
                relevance_score = 0
                
                # Name match (highest weight)
                if query_lower in metadata.name.lower():
                    relevance_score += 10
                
                # Description match
                if query_lower in metadata.description.lower():
                    relevance_score += 5
                
                # Tag matches
                for tag in metadata.tags:
                    if query_lower in tag.lower():
                        relevance_score += 3
                
                # Capability matches
                for capability in metadata.capabilities:
                    if query_lower in capability.value.lower():
                        relevance_score += 2
                
                if relevance_score > 0:
                    matching_tools.append((relevance_score, metadata))
        
        # Sort by relevance score (descending) then by name
        matching_tools.sort(key=lambda x: (-x[0], x[1].name))
        return [metadata for _, metadata in matching_tools]
    
    async def get_tool_metadata(self, tool_name: str) -> Optional[ToolMetadata]:
        """
        Get metadata for a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool metadata or None if not found
        """
        async with self._registry_lock:
            return self._tool_metadata_cache.get(tool_name)
    
    async def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get AutoGen schema for a tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool schema or None if not found
        """
        metadata = await self.get_tool_metadata(tool_name)
        if metadata:
            return {
                "name": metadata.name,
                "description": metadata.description,
                "parameters": metadata.input_schema,
                "returns": metadata.output_schema
            }
        return None
    
    async def auto_discover_tools(self, package_path: str) -> int:
        """
        Automatically discover and register tools in a package.
        
        Args:
            package_path: Python package path to scan
            
        Returns:
            Number of tools discovered and registered
        """
        discovered_count = 0
        
        try:
            # Import the package
            package = importlib.import_module(package_path)
            if not hasattr(package, '__file__') or package.__file__ is None:
                raise ImportError(f"Cannot locate package: {package_path}")
            
            package_dir = Path(package.__file__).parent
            
            # Scan Python files in the package
            for py_file in package_dir.rglob("*.py"):
                if py_file.name.startswith("__"):
                    continue
                
                discovered_count += await self._scan_module_for_tools(py_file, package_dir.parent)
        
        except Exception as e:
            self.logger.error(f"Auto-discovery failed for {package_path}: {e}")
        
        self.logger.info(f"Auto-discovered {discovered_count} tools from {package_path}")
        return discovered_count
    
    async def _scan_module_for_tools(self, py_file: Path, base_dir: Path) -> int:
        """Scan a module file for tool classes."""
        count = 0
        
        try:
            # Convert file path to module name
            relative_path = py_file.relative_to(base_dir)
            module_name = str(relative_path.with_suffix("")).replace("/", ".")
            
            # Import the module
            module = importlib.import_module(module_name)
            
            # Find tool classes
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, BaseToolInterface) and 
                    obj != BaseToolInterface and 
                    obj != BaseTool and
                    not inspect.isabstract(obj) and
                    obj.__module__ == module_name):  # Only classes defined in this module
                    
                    try:
                        await self.register_tool(obj)
                        count += 1
                    except ToolRegistrationError as e:
                        self.logger.warning(f"Failed to register {name}: {e}")
        
        except Exception as e:
            self.logger.debug(f"Could not scan {py_file}: {e}")
        
        return count
    
    async def cleanup_all_instances(self) -> None:
        """Cleanup all tool instances with proper error handling."""
        self._is_shutting_down = True
        cleanup_tasks = []
        
        async with self._instance_lock:
            for tool_name, instance in list(self._tool_instances.items()):
                task = asyncio.create_task(self._safe_cleanup_instance(tool_name, instance))
                cleanup_tasks.append(task)
            
            self._tool_instances.clear()
        
        # Wait for all cleanups to complete with timeout
        if cleanup_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*cleanup_tasks, return_exceptions=True),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                self.logger.warning("Tool cleanup timed out")
    
    async def _safe_cleanup_instance(self, tool_name: str, instance: BaseToolInterface) -> None:
        """Safely cleanup a tool instance with error handling."""
        try:
            await instance.cleanup()
            self._stats['cleanup_operations'] += 1
        except Exception as e:
            self.logger.error(f"Failed to cleanup {tool_name}: {e}")
    
    async def on_tool_cleanup(self, tool: BaseToolInterface) -> None:
        """Handle tool cleanup notifications."""
        # Find and remove the tool from our instance cache
        async with self._instance_lock:
            for tool_name, cached_instance in list(self._tool_instances.items()):
                if cached_instance is tool:
                    del self._tool_instances[tool_name]
                    break
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive registry statistics.
        
        Returns:
            Dictionary with registry statistics
        """
        capabilities_count = defaultdict(int)
        enabled_count = 0
        usage_stats = {
            'total_usage': 0,
            'most_used': None,
            'least_used': None
        }
        
        for tool_name, registration_info in self._tools.items():
            metadata = self._tool_metadata_cache[tool_name]
            config = registration_info.config
            
            if config.get("enabled", True):
                enabled_count += 1
            
            for capability in metadata.capabilities:
                capabilities_count[capability.value] += 1
            
            # Track usage statistics
            usage_stats['total_usage'] += registration_info.usage_count
            if (usage_stats['most_used'] is None or 
                registration_info.usage_count > self._tools[usage_stats['most_used']].usage_count):
                usage_stats['most_used'] = tool_name
            
            if (usage_stats['least_used'] is None or 
                registration_info.usage_count < self._tools[usage_stats['least_used']].usage_count):
                usage_stats['least_used'] = tool_name
        
        return {
            "total_tools": len(self._tools),
            "enabled_tools": enabled_count,
            "active_instances": len(self._tool_instances),
            "capabilities_distribution": dict(capabilities_count),
            "usage_statistics": usage_stats,
            "internal_stats": self._stats.copy(),
            "is_shutting_down": self._is_shutting_down
        }
    
    async def __aenter__(self) -> AsyncToolRegistry:
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit with cleanup."""
        await self.cleanup_all_instances()


# Global tool registry instance
_tool_registry: Optional[AsyncToolRegistry] = None
_registry_lock = asyncio.Lock()


async def get_tool_registry() -> AsyncToolRegistry:
    """Get the global tool registry instance with thread safety."""
    global _tool_registry
    
    if _tool_registry is None:
        async with _registry_lock:
            if _tool_registry is None:
                _tool_registry = AsyncToolRegistry()
    
    return _tool_registry


async def register_tool(
    tool_class: Type[BaseToolInterface], 
    config: Optional[Mapping[str, Any]] = None
) -> None:
    """Register a tool in the global registry."""
    registry = await get_tool_registry()
    await registry.register_tool(tool_class, config)


async def get_tool(
    tool_name: str, 
    config_override: Optional[Mapping[str, Any]] = None
) -> Optional[BaseToolInterface]:
    """Get a tool instance from the global registry."""
    registry = await get_tool_registry()
    return await registry.get_tool_instance(tool_name, config_override)


async def cleanup_registry() -> None:
    """Cleanup the global registry."""
    global _tool_registry
    
    if _tool_registry:
        await _tool_registry.cleanup_all_instances()
        _tool_registry = None