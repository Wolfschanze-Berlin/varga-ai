"""
Web search tool for gathering information from the internet.
"""

import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import quote_plus

from src.tools.base import BaseTool, ToolResult, ToolStatus, ToolMetadata, ToolCapability
from src.log_service import get_logger
from src.config import settings


class WebSearchTool(BaseTool):
    """
    Tool for searching the web and retrieving information.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize web search tool.
        
        Args:
            config: Tool configuration
        """
        super().__init__(config)
        
        # API configuration (can be extended with real search APIs)
        self.search_api_url = config.get("search_api_url", "https://duckduckgo.com/")
        self.max_results = config.get("max_results", 10)
        
        # Session for HTTP requests
        self._session: Optional[aiohttp.ClientSession] = None
        
        self.logger = get_logger("web_search_tool")
        
        # Tool metadata
        self._metadata = ToolMetadata(
            name="web_search",
            version="1.0.0",
            description="Search the web for information using various search providers",
            capabilities=[
                ToolCapability.SEARCH,
                ToolCapability.RESEARCH
            ],
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "description": "Maximum number of results"},
                    "search_type": {"type": "string", "enum": ["web", "news", "images", "videos"]}
                },
                "required": ["query"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "results": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "url": {"type": "string"},
                                "snippet": {"type": "string"}
                            }
                        }
                    },
                    "total_results": {"type": "integer"}
                }
            },
            tags=["search", "web", "research", "information"]
        )
    
    @property
    def metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return self._metadata
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if valid
        """
        query = input_data.get("query")
        
        if not query or not query.strip():
            self.logger.error("No search query provided")
            return False
        
        return True
    
    async def setup(self) -> bool:
        """Set up the web search tool."""
        try:
            # Create aiohttp session
            if not self._session:
                self._session = aiohttp.ClientSession()
            
            self.logger.info("Web search tool setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup web search tool: {e}")
            return False
    
    async def search_duckduckgo(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search using DuckDuckGo (basic implementation).
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of search results
        """
        try:
            # For a real implementation, you would use DuckDuckGo's API
            # This is a simplified version for demonstration
            
            results = []
            
            # Simulate search results based on query
            if "python" in query.lower():
                results.append({
                    "title": "Python Programming Language",
                    "url": "https://www.python.org",
                    "snippet": "Python is a high-level, interpreted programming language with dynamic semantics."
                })
            
            if "machine learning" in query.lower():
                results.append({
                    "title": "Introduction to Machine Learning",
                    "url": "https://en.wikipedia.org/wiki/Machine_learning",
                    "snippet": "Machine learning is a subset of artificial intelligence that enables systems to learn from data."
                })
            
            if "autogen" in query.lower():
                results.append({
                    "title": "Microsoft AutoGen Framework",
                    "url": "https://github.com/microsoft/autogen",
                    "snippet": "AutoGen is a framework for building multi-agent conversational systems."
                })
            
            # Default result if no specific match
            if not results:
                results.append({
                    "title": f"Search results for: {query}",
                    "url": "https://duckduckgo.com/?q=" + quote_plus(query),
                    "snippet": f"Web search results for '{query}'. Visit the link for more information."
                })
            
            return results[:max_results]
            
        except Exception as e:
            self.logger.error(f"Error searching DuckDuckGo: {e}")
            return []
    
    async def search_wikipedia(self, query: str) -> List[Dict[str, Any]]:
        """
        Search Wikipedia for information.
        
        Args:
            query: Search query
            
        Returns:
            List of Wikipedia results
        """
        try:
            # Wikipedia API endpoint
            api_url = "https://en.wikipedia.org/w/api.php"
            
            params = {
                "action": "opensearch",
                "search": query,
                "limit": 5,
                "format": "json"
            }
            
            async with self._session.get(api_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Parse Wikipedia response
                    titles = data[1] if len(data) > 1 else []
                    descriptions = data[2] if len(data) > 2 else []
                    urls = data[3] if len(data) > 3 else []
                    
                    results = []
                    for i in range(len(titles)):
                        results.append({
                            "title": titles[i],
                            "url": urls[i] if i < len(urls) else "",
                            "snippet": descriptions[i] if i < len(descriptions) else ""
                        })
                    
                    return results
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error searching Wikipedia: {e}")
            return []
    
    async def search_news(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for news articles.
        
        Args:
            query: Search query
            
        Returns:
            List of news results
        """
        # This would integrate with a news API
        # For now, return simulated results
        
        return [{
            "title": f"Latest news about {query}",
            "url": f"https://news.google.com/search?q={quote_plus(query)}",
            "snippet": f"Recent news and updates about {query}",
            "source": "Google News",
            "date": datetime.now().isoformat()
        }]
    
    async def aggregate_search(self, query: str, search_types: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Perform multiple types of searches and aggregate results.
        
        Args:
            query: Search query
            search_types: List of search types to perform
            
        Returns:
            Aggregated search results
        """
        results = {}
        
        tasks = []
        
        if "web" in search_types:
            tasks.append(("web", self.search_duckduckgo(query)))
        
        if "wikipedia" in search_types:
            tasks.append(("wikipedia", self.search_wikipedia(query)))
        
        if "news" in search_types:
            tasks.append(("news", self.search_news(query)))
        
        # Execute searches in parallel
        if tasks:
            search_results = await asyncio.gather(
                *[task[1] for task in tasks],
                return_exceptions=True
            )
            
            for i, (search_type, _) in enumerate(tasks):
                if not isinstance(search_results[i], Exception):
                    results[search_type] = search_results[i]
                else:
                    self.logger.error(f"Error in {search_type} search: {search_results[i]}")
                    results[search_type] = []
        
        return results
    
    async def _do_execute(
        self,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ToolResult:
        """
        Execute web search.
        
        Args:
            input_data: Input parameters
            context: Execution context
            
        Returns:
            Search results
        """
        query = input_data.get("query", "")
        max_results = input_data.get("max_results", self.max_results)
        search_type = input_data.get("search_type", "web")
        
        try:
            self.logger.info(f"Searching for: {query} (type: {search_type})")
            
            if search_type == "all":
                # Aggregate multiple search types
                results = await self.aggregate_search(
                    query,
                    ["web", "wikipedia", "news"]
                )
                
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "query": query,
                        "results": results,
                        "total_results": sum(len(r) for r in results.values())
                    }
                )
            
            elif search_type == "wikipedia":
                results = await self.search_wikipedia(query)
            
            elif search_type == "news":
                results = await self.search_news(query)
            
            else:  # Default to web search
                results = await self.search_duckduckgo(query, max_results)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "query": query,
                    "results": results,
                    "total_results": len(results),
                    "search_type": search_type
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error executing search: {e}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error=str(e)
            )
    
    async def cleanup(self) -> bool:
        """Clean up resources."""
        try:
            # Close session
            if self._session:
                await self._session.close()
                self._session = None
            
            return await super().cleanup()
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            return False
    
    def format_results(self, results: List[Dict[str, Any]]) -> str:
        """
        Format search results as readable text.
        
        Args:
            results: Search results
            
        Returns:
            Formatted text
        """
        if not results:
            return "No results found."
        
        formatted = []
        for i, result in enumerate(results, 1):
            formatted.append(f"{i}. **{result.get('title', 'No title')}**")
            if result.get('snippet'):
                formatted.append(f"   {result['snippet']}")
            if result.get('url'):
                formatted.append(f"   Link: {result['url']}")
            formatted.append("")
        
        return "\n".join(formatted)