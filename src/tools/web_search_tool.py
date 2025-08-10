"""
Web Search Tool for AutoGen SME platform.
Provides internet search capabilities for agents to gather information.
"""

import json
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus
import httpx
from bs4 import BeautifulSoup

from .base import BaseTool, ToolResult, ToolStatus, ToolMetadata, ToolCapability
from ..log_service import get_logger
from ..config import get_tool_config, WebSearchConfig


class WebSearchTool(BaseTool):
    """Tool for searching the internet and extracting relevant information."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the web search tool.
        
        Args:
            config: Tool configuration
        """
        super().__init__(config)
        self.search_config = WebSearchConfig(**config)
        self.logger = get_logger("web_search_tool")
        
        # Search engine endpoints
        self.search_endpoints = {
            "serpapi": "https://serpapi.com/search",
            "google_search_api": "https://www.googleapis.com/customsearch/v1",
            "bing": "https://api.bing.microsoft.com/v7.0/search"
        }
    
    @property
    def metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        if self._metadata is None:
            self._metadata = ToolMetadata(
                name="web_search",
                description="Search the internet for information and return relevant results",
                version="1.0.0",
                capabilities=[ToolCapability.SEARCH],
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query to execute"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 50
                        },
                        "include_snippets": {
                            "type": "boolean",
                            "description": "Whether to include content snippets",
                            "default": True
                        },
                        "safe_search": {
                            "type": "boolean", 
                            "description": "Enable safe search filtering",
                            "default": True
                        }
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
                                    "snippet": {"type": "string"},
                                    "domain": {"type": "string"},
                                    "published_date": {"type": "string"}
                                }
                            }
                        },
                        "total_results": {"type": "integer"},
                        "search_time_ms": {"type": "number"}
                    }
                },
                rate_limits={
                    "per_minute": self.search_config.rate_limit_per_minute,
                    "per_hour": self.search_config.rate_limit_per_hour
                },
                dependencies=["httpx", "beautifulsoup4"],
                tags=["search", "internet", "information", "research"]
            )
        return self._metadata
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate search input data.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            query = input_data.get("query", "").strip()
            if not query or len(query) < 2:
                self.logger.warning("Search query is too short or empty")
                return False
            
            max_results = input_data.get("max_results", 10)
            if not isinstance(max_results, int) or max_results < 1 or max_results > 50:
                self.logger.warning(f"Invalid max_results: {max_results}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Input validation failed: {e}")
            return False
    
    async def _do_execute(
        self, 
        input_data: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> ToolResult:
        """
        Execute web search.
        
        Args:
            input_data: Search parameters
            context: Execution context
            
        Returns:
            Search results
        """
        query = input_data["query"]
        max_results = input_data.get("max_results", 10)
        include_snippets = input_data.get("include_snippets", True)
        safe_search = input_data.get("safe_search", True)
        
        self.logger.info(f"Executing web search for query: {query}")
        
        try:
            # Choose search method based on configuration
            if self.search_config.search_engine == "serpapi":
                results = await self._search_serpapi(
                    query, max_results, safe_search, include_snippets
                )
            elif self.search_config.search_engine == "google_search_api":
                results = await self._search_google_api(
                    query, max_results, safe_search, include_snippets
                )
            elif self.search_config.search_engine == "bing":
                results = await self._search_bing(
                    query, max_results, safe_search, include_snippets
                )
            else:
                # Fallback to basic web scraping approach
                results = await self._search_fallback(
                    query, max_results, include_snippets
                )
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=results,
                metadata={
                    "search_engine": self.search_config.search_engine,
                    "query": query,
                    "result_count": len(results.get("results", []))
                }
            )
            
        except Exception as e:
            self.logger.error(f"Web search failed: {e}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Search failed: {str(e)}"
            )
    
    async def _search_serpapi(
        self, 
        query: str, 
        max_results: int, 
        safe_search: bool,
        include_snippets: bool
    ) -> Dict[str, Any]:
        """Search using SerpAPI."""
        params = {
            "q": query,
            "api_key": self.search_config.api_key,
            "engine": "google",
            "num": min(max_results, 20),  # SerpAPI limit
            "safe": "active" if safe_search else "off",
            "hl": self.search_config.language,
            "gl": self.search_config.country
        }
        
        async with self.http_client as client:
            response = await client.get(
                self.search_endpoints["serpapi"],
                params=params
            )
            response.raise_for_status()
            data = response.json()
        
        results = []
        organic_results = data.get("organic_results", [])
        
        for result in organic_results[:max_results]:
            search_result = {
                "title": result.get("title", ""),
                "url": result.get("link", ""),
                "domain": result.get("displayed_link", ""),
                "snippet": result.get("snippet", "") if include_snippets else ""
            }
            
            # Extract published date if available
            if "date" in result:
                search_result["published_date"] = result["date"]
            
            results.append(search_result)
        
        return {
            "results": results,
            "total_results": data.get("search_information", {}).get("total_results", 0),
            "search_time_ms": data.get("search_information", {}).get("time_taken_displayed", 0) * 1000
        }
    
    async def _search_google_api(
        self, 
        query: str, 
        max_results: int, 
        safe_search: bool,
        include_snippets: bool
    ) -> Dict[str, Any]:
        """Search using Google Custom Search API."""
        params = {
            "key": self.search_config.api_key,
            "cx": self.config.get("google_cx_id"),  # Custom search engine ID
            "q": query,
            "num": min(max_results, 10),  # Google API limit per request
            "safe": "active" if safe_search else "off",
            "lr": f"lang_{self.search_config.language}",
            "gl": self.search_config.country
        }
        
        async with self.http_client as client:
            response = await client.get(
                self.search_endpoints["google_search_api"],
                params=params
            )
            response.raise_for_status()
            data = response.json()
        
        results = []
        items = data.get("items", [])
        
        for item in items[:max_results]:
            search_result = {
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "domain": item.get("displayLink", ""),
                "snippet": item.get("snippet", "") if include_snippets else ""
            }
            results.append(search_result)
        
        search_info = data.get("searchInformation", {})
        return {
            "results": results,
            "total_results": int(search_info.get("totalResults", 0)),
            "search_time_ms": float(search_info.get("searchTime", 0)) * 1000
        }
    
    async def _search_bing(
        self, 
        query: str, 
        max_results: int, 
        safe_search: bool,
        include_snippets: bool
    ) -> Dict[str, Any]:
        """Search using Bing Search API."""
        headers = {
            "Ocp-Apim-Subscription-Key": self.search_config.api_key
        }
        
        params = {
            "q": query,
            "count": min(max_results, 50),
            "safeSearch": "Strict" if safe_search else "Off",
            "mkt": f"{self.search_config.language}-{self.search_config.country}"
        }
        
        async with self.http_client as client:
            response = await client.get(
                self.search_endpoints["bing"],
                headers=headers,
                params=params
            )
            response.raise_for_status()
            data = response.json()
        
        results = []
        web_pages = data.get("webPages", {}).get("value", [])
        
        for page in web_pages[:max_results]:
            search_result = {
                "title": page.get("name", ""),
                "url": page.get("url", ""),
                "domain": page.get("displayUrl", ""),
                "snippet": page.get("snippet", "") if include_snippets else ""
            }
            
            # Extract date if available
            if "dateLastCrawled" in page:
                search_result["published_date"] = page["dateLastCrawled"]
            
            results.append(search_result)
        
        return {
            "results": results,
            "total_results": data.get("webPages", {}).get("totalEstimatedMatches", 0),
            "search_time_ms": 0  # Bing doesn't provide search time
        }
    
    async def _search_fallback(
        self, 
        query: str, 
        max_results: int,
        include_snippets: bool
    ) -> Dict[str, Any]:
        """
        Fallback search method using DuckDuckGo instant answers.
        Note: This is a basic implementation for demonstration.
        """
        self.logger.warning("Using fallback search method")
        
        # Use DuckDuckGo instant answer API (no key required)
        params = {
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1"
        }
        
        async with self.http_client as client:
            response = await client.get(
                "https://api.duckduckgo.com/",
                params=params
            )
            response.raise_for_status()
            data = response.json()
        
        results = []
        
        # Add instant answer if available
        if data.get("Abstract"):
            results.append({
                "title": data.get("Heading", query),
                "url": data.get("AbstractURL", ""),
                "domain": "duckduckgo.com",
                "snippet": data.get("Abstract", "") if include_snippets else ""
            })
        
        # Add related topics
        for topic in data.get("RelatedTopics", [])[:max_results-1]:
            if isinstance(topic, dict) and "Text" in topic:
                results.append({
                    "title": topic.get("Text", "").split(" - ")[0],
                    "url": topic.get("FirstURL", ""),
                    "domain": "duckduckgo.com",
                    "snippet": topic.get("Text", "") if include_snippets else ""
                })
        
        return {
            "results": results[:max_results],
            "total_results": len(results),
            "search_time_ms": 0
        }
    
    async def health_check(self) -> bool:
        """
        Check if the web search service is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try a simple test search
            test_result = await self._do_execute(
                {"query": "test", "max_results": 1},
                {}
            )
            return test_result.is_success
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False