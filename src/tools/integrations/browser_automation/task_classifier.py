"""
Task Classifier for browser automation tasks.
Analyzes and classifies browser tasks to determine optimal routing and execution strategy.
"""

from __future__ import annotations
import re
import asyncio
from typing import Any, Dict, List, Optional, Tuple, Pattern
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel

from ....log_service import get_logger


class TaskType(str, Enum):
    """Types of browser automation tasks."""
    
    NAVIGATION = "navigation"
    DATA_EXTRACTION = "data_extraction"
    FORM_SUBMISSION = "form_submission"
    SEARCH_AND_FILTER = "search_and_filter"
    AUTHENTICATION = "authentication"
    FILE_DOWNLOAD = "file_download"
    FILE_UPLOAD = "file_upload"
    SCREENSHOT_CAPTURE = "screenshot_capture"
    PAGE_MONITORING = "page_monitoring"
    COMPLEX_INTERACTION = "complex_interaction"
    API_TESTING = "api_testing"
    UNKNOWN = "unknown"


class TaskComplexity(str, Enum):
    """Complexity levels for browser tasks."""
    
    VERY_LOW = "very_low"      # Simple page loads, basic navigation
    LOW = "low"                # Simple forms, basic interactions
    MEDIUM = "medium"          # Multi-step workflows, moderate logic
    HIGH = "high"              # Complex workflows, conditional logic
    VERY_HIGH = "very_high"    # AI-driven tasks, dynamic adaptation


@dataclass
class ClassificationRule:
    """Rule for classifying tasks."""
    
    patterns: List[str]
    task_type: TaskType
    complexity: TaskComplexity
    confidence: float
    conditions: Optional[Dict[str, Any]] = None


@dataclass
class SiteProfile:
    """Profile information for specific websites."""
    
    domain: str
    common_tasks: List[TaskType]
    complexity_bias: int  # -2 to +2, adjusts complexity rating
    requires_auth: bool
    has_dynamic_content: bool
    performance_notes: List[str]


class TaskClassificationResult(BaseModel):
    """Result of task classification."""
    
    task_type: TaskType
    complexity: TaskComplexity
    confidence: float
    reasoning: List[str]
    suggested_tool: str  # "browser_use" or "playwright"
    estimated_duration_seconds: int
    risk_factors: List[str]
    metadata: Dict[str, Any] = {}


class TaskClassifier:
    """
    Analyzes browser automation tasks to determine type, complexity, and optimal execution strategy.
    Uses rule-based classification with site-specific knowledge.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize task classifier.
        
        Args:
            config: Configuration dictionary for classification settings
        """
        self.logger = get_logger("task_classifier")
        
        # Configuration
        self.default_confidence_threshold = config.get("confidence_threshold", 0.7)
        self.enable_url_analysis = config.get("enable_url_analysis", True)
        self.enable_site_profiling = config.get("enable_site_profiling", True)
        self.cache_site_profiles = config.get("cache_site_profiles", True)
        
        # Classification rules
        self._classification_rules: List[ClassificationRule] = []
        self._site_profiles: Dict[str, SiteProfile] = {}
        
        # Caching
        self._classification_cache: Dict[str, TaskClassificationResult] = {}
        self._site_profile_cache: Dict[str, SiteProfile] = {}
        
        # Performance tracking
        self._metrics = {
            "classifications_performed": 0,
            "cache_hits": 0,
            "site_profiles_created": 0,
            "rule_matches": 0
        }
        
        # Initialize built-in rules and profiles
        self._setup_classification_rules()
        self._setup_site_profiles()
    
    async def setup(self) -> bool:
        """Setup task classifier."""
        try:
            self.logger.info("Setting up task classifier")
            
            # Validate classification rules
            if not self._classification_rules:
                self.logger.warning("No classification rules loaded")
            
            self.logger.info(
                f"Task classifier setup completed with {len(self._classification_rules)} rules "
                f"and {len(self._site_profiles)} site profiles"
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup task classifier: {e}")
            return False
    
    async def classify_task(
        self,
        description: str,
        url: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Classify a browser automation task.
        
        Args:
            description: Natural language description of the task
            url: Optional target URL
            parameters: Additional task parameters
            
        Returns:
            Dictionary containing classification results
        """
        try:
            # Create cache key
            cache_key = self._create_cache_key(description, url, parameters)
            
            # Check cache
            if cache_key in self._classification_cache:
                self._metrics["cache_hits"] += 1
                return self._classification_cache[cache_key].dict()
            
            # Perform classification
            result = await self._perform_classification(description, url, parameters)
            
            # Cache result
            self._classification_cache[cache_key] = result
            self._metrics["classifications_performed"] += 1
            
            self.logger.debug(
                f"Classified task as {result.task_type.value} "
                f"with {result.complexity.value} complexity",
                extra={"confidence": result.confidence}
            )
            
            return result.dict()
            
        except Exception as e:
            self.logger.error(f"Error classifying task: {e}")
            
            # Return fallback classification
            return TaskClassificationResult(
                task_type=TaskType.UNKNOWN,
                complexity=TaskComplexity.MEDIUM,
                confidence=0.0,
                reasoning=["Classification failed, using fallback"],
                suggested_tool="browser_use",
                estimated_duration_seconds=60,
                risk_factors=["Unknown task type"]
            ).dict()
    
    async def _perform_classification(
        self,
        description: str,
        url: Optional[str],
        parameters: Optional[Dict[str, Any]]
    ) -> TaskClassificationResult:
        """Perform the actual task classification."""
        
        # Initialize analysis context
        context = {
            "description": description.lower(),
            "url": url,
            "parameters": parameters or {},
            "domain": self._extract_domain(url) if url else None,
            "reasoning": [],
            "risk_factors": []
        }
        
        # Analyze URL and site characteristics
        site_profile = None
        if self.enable_url_analysis and url:
            site_profile = await self._analyze_site(url)
            if site_profile:
                context["site_profile"] = site_profile
        
        # Apply classification rules
        best_match = await self._apply_classification_rules(context)
        
        # Adjust based on site profile
        if site_profile:
            best_match = self._adjust_for_site_profile(best_match, site_profile, context)
        
        # Estimate duration and suggest tool
        duration = self._estimate_duration(best_match, context)
        suggested_tool = self._suggest_tool(best_match, context)
        
        return TaskClassificationResult(
            task_type=best_match["task_type"],
            complexity=best_match["complexity"],
            confidence=best_match["confidence"],
            reasoning=context["reasoning"],
            suggested_tool=suggested_tool,
            estimated_duration_seconds=duration,
            risk_factors=context["risk_factors"],
            metadata={
                "domain": context["domain"],
                "has_site_profile": site_profile is not None,
                "rules_matched": best_match.get("rules_matched", 0)
            }
        )
    
    def _create_cache_key(
        self,
        description: str,
        url: Optional[str],
        parameters: Optional[Dict[str, Any]]
    ) -> str:
        """Create cache key for classification."""
        import hashlib
        
        cache_data = f"{description}|{url or ''}|{str(parameters or {})}"
        return hashlib.md5(cache_data.encode()).hexdigest()
    
    def _extract_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return None
    
    async def _analyze_site(self, url: str) -> Optional[SiteProfile]:
        """Analyze website to create site profile."""
        domain = self._extract_domain(url)
        if not domain:
            return None
        
        # Check cache
        if domain in self._site_profile_cache:
            return self._site_profile_cache[domain]
        
        # Check built-in profiles
        if domain in self._site_profiles:
            profile = self._site_profiles[domain]
            self._site_profile_cache[domain] = profile
            return profile
        
        # Create dynamic profile
        if self.enable_site_profiling:
            profile = await self._create_dynamic_site_profile(url, domain)
            if profile and self.cache_site_profiles:
                self._site_profile_cache[domain] = profile
            return profile
        
        return None
    
    async def _create_dynamic_site_profile(self, url: str, domain: str) -> Optional[SiteProfile]:
        """Create site profile by analyzing the website."""
        try:
            # Basic HTTP analysis
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.head(url)
                
                # Analyze response headers
                has_dynamic_content = any([
                    "application/json" in response.headers.get("content-type", ""),
                    "javascript" in response.headers.get("content-type", ""),
                    response.headers.get("x-powered-by"),
                    response.headers.get("x-frame-options")
                ])
                
                # Check for common authentication indicators
                requires_auth = any([
                    response.status_code == 401,
                    "login" in url.lower(),
                    "auth" in url.lower(),
                    response.headers.get("www-authenticate")
                ])
                
                # Determine common tasks based on domain patterns
                common_tasks = self._infer_common_tasks(domain, url)
                
                profile = SiteProfile(
                    domain=domain,
                    common_tasks=common_tasks,
                    complexity_bias=0,
                    requires_auth=requires_auth,
                    has_dynamic_content=has_dynamic_content,
                    performance_notes=[]
                )
                
                self._metrics["site_profiles_created"] += 1
                return profile
                
        except Exception as e:
            self.logger.debug(f"Failed to create site profile for {domain}: {e}")
            return None
    
    def _infer_common_tasks(self, domain: str, url: str) -> List[TaskType]:
        """Infer common tasks for a domain based on patterns."""
        common_tasks = [TaskType.NAVIGATION]  # All sites support navigation
        
        # E-commerce patterns
        if any(keyword in domain for keyword in ["shop", "store", "cart", "buy", "commerce"]):
            common_tasks.extend([
                TaskType.SEARCH_AND_FILTER,
                TaskType.FORM_SUBMISSION,
                TaskType.AUTHENTICATION
            ])
        
        # Social media patterns
        if any(keyword in domain for keyword in ["social", "facebook", "twitter", "linkedin"]):
            common_tasks.extend([
                TaskType.AUTHENTICATION,
                TaskType.DATA_EXTRACTION,
                TaskType.COMPLEX_INTERACTION
            ])
        
        # News/content sites
        if any(keyword in domain for keyword in ["news", "blog", "article", "content"]):
            common_tasks.extend([
                TaskType.DATA_EXTRACTION,
                TaskType.SCREENSHOT_CAPTURE
            ])
        
        # File sharing/cloud storage
        if any(keyword in domain for keyword in ["drive", "dropbox", "cloud", "files"]):
            common_tasks.extend([
                TaskType.FILE_UPLOAD,
                TaskType.FILE_DOWNLOAD,
                TaskType.AUTHENTICATION
            ])
        
        return common_tasks
    
    async def _apply_classification_rules(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply classification rules to determine task type and complexity."""
        description = context["description"]
        best_match = {
            "task_type": TaskType.UNKNOWN,
            "complexity": TaskComplexity.MEDIUM,
            "confidence": 0.0,
            "rules_matched": 0
        }
        
        for rule in self._classification_rules:
            # Check if any patterns match
            pattern_matches = 0
            for pattern in rule.patterns:
                if re.search(pattern, description):
                    pattern_matches += 1
            
            if pattern_matches == 0:
                continue
            
            # Calculate confidence based on pattern matches
            match_ratio = pattern_matches / len(rule.patterns)
            rule_confidence = rule.confidence * match_ratio
            
            # Check additional conditions
            if rule.conditions:
                if not self._check_rule_conditions(rule.conditions, context):
                    continue
            
            # Update best match if this rule has higher confidence
            if rule_confidence > best_match["confidence"]:
                best_match = {
                    "task_type": rule.task_type,
                    "complexity": rule.complexity,
                    "confidence": rule_confidence,
                    "rules_matched": best_match["rules_matched"] + 1
                }
                
                context["reasoning"].append(
                    f"Matched {rule.task_type.value} pattern with {rule_confidence:.2f} confidence"
                )
        
        self._metrics["rule_matches"] += best_match["rules_matched"]
        return best_match
    
    def _check_rule_conditions(self, conditions: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if rule conditions are met."""
        for condition_key, condition_value in conditions.items():
            if condition_key == "requires_url":
                if condition_value and not context.get("url"):
                    return False
            elif condition_key == "domain_contains":
                domain = context.get("domain", "")
                if not any(keyword in domain for keyword in condition_value):
                    return False
            elif condition_key == "parameters_required":
                parameters = context.get("parameters", {})
                if not all(param in parameters for param in condition_value):
                    return False
        
        return True
    
    def _adjust_for_site_profile(
        self,
        classification: Dict[str, Any],
        site_profile: SiteProfile,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adjust classification based on site profile."""
        
        # Adjust complexity based on site characteristics
        current_complexity = classification["complexity"]
        complexity_levels = list(TaskComplexity)
        current_index = complexity_levels.index(current_complexity)
        
        # Apply site complexity bias
        new_index = max(0, min(len(complexity_levels) - 1, current_index + site_profile.complexity_bias))
        classification["complexity"] = complexity_levels[new_index]
        
        # Add site-specific risk factors
        if site_profile.requires_auth and classification["task_type"] != TaskType.AUTHENTICATION:
            context["risk_factors"].append("Site may require authentication")
        
        if site_profile.has_dynamic_content:
            context["risk_factors"].append("Site has dynamic content that may affect timing")
        
        # Adjust confidence if task type matches common tasks
        if classification["task_type"] in site_profile.common_tasks:
            classification["confidence"] = min(1.0, classification["confidence"] * 1.1)
            context["reasoning"].append("Task type is common for this site")
        
        return classification
    
    def _estimate_duration(self, classification: Dict[str, Any], context: Dict[str, Any]) -> int:
        """Estimate task duration in seconds."""
        base_duration = {
            TaskType.NAVIGATION: 10,
            TaskType.DATA_EXTRACTION: 30,
            TaskType.FORM_SUBMISSION: 20,
            TaskType.SEARCH_AND_FILTER: 25,
            TaskType.AUTHENTICATION: 15,
            TaskType.FILE_DOWNLOAD: 60,
            TaskType.FILE_UPLOAD: 45,
            TaskType.SCREENSHOT_CAPTURE: 5,
            TaskType.PAGE_MONITORING: 120,
            TaskType.COMPLEX_INTERACTION: 60,
            TaskType.API_TESTING: 30,
            TaskType.UNKNOWN: 45
        }
        
        complexity_multiplier = {
            TaskComplexity.VERY_LOW: 0.5,
            TaskComplexity.LOW: 0.75,
            TaskComplexity.MEDIUM: 1.0,
            TaskComplexity.HIGH: 1.5,
            TaskComplexity.VERY_HIGH: 2.5
        }
        
        duration = base_duration.get(classification["task_type"], 45)
        duration *= complexity_multiplier.get(classification["complexity"], 1.0)
        
        # Add buffer for site-specific factors
        if context.get("site_profile"):
            site_profile = context["site_profile"]
            if site_profile.has_dynamic_content:
                duration *= 1.2
            if site_profile.requires_auth:
                duration += 10
        
        return int(duration)
    
    def _suggest_tool(self, classification: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Suggest the best tool for the task."""
        
        # High complexity tasks generally benefit from browser-use
        if classification["complexity"] in [TaskComplexity.HIGH, TaskComplexity.VERY_HIGH]:
            return "browser_use"
        
        # Simple tasks can use playwright for speed
        simple_tasks = [TaskType.NAVIGATION, TaskType.SCREENSHOT_CAPTURE]
        if (classification["task_type"] in simple_tasks and
            classification["complexity"] in [TaskComplexity.VERY_LOW, TaskComplexity.LOW]):
            return "playwright"
        
        # Data extraction and complex interactions benefit from AI
        ai_beneficial_tasks = [
            TaskType.DATA_EXTRACTION,
            TaskType.COMPLEX_INTERACTION,
            TaskType.SEARCH_AND_FILTER
        ]
        if classification["task_type"] in ai_beneficial_tasks:
            return "browser_use"
        
        # Default to browser-use for unknown/complex scenarios
        return "browser_use"
    
    def _setup_classification_rules(self) -> None:
        """Setup built-in classification rules."""
        
        # Navigation rules
        self._classification_rules.extend([
            ClassificationRule(
                patterns=["go to", "navigate to", "visit", "open page"],
                task_type=TaskType.NAVIGATION,
                complexity=TaskComplexity.VERY_LOW,
                confidence=0.9
            ),
            ClassificationRule(
                patterns=["click.*link", "follow.*link", "navigate.*menu"],
                task_type=TaskType.NAVIGATION,
                complexity=TaskComplexity.LOW,
                confidence=0.8
            )
        ])
        
        # Data extraction rules
        self._classification_rules.extend([
            ClassificationRule(
                patterns=["extract", "scrape", "get.*data", "find.*text", "collect.*information"],
                task_type=TaskType.DATA_EXTRACTION,
                complexity=TaskComplexity.MEDIUM,
                confidence=0.85
            ),
            ClassificationRule(
                patterns=["download.*data", "export", "save.*information"],
                task_type=TaskType.DATA_EXTRACTION,
                complexity=TaskComplexity.HIGH,
                confidence=0.8
            )
        ])
        
        # Form submission rules
        self._classification_rules.extend([
            ClassificationRule(
                patterns=["fill.*form", "submit.*form", "enter.*data", "input.*information"],
                task_type=TaskType.FORM_SUBMISSION,
                complexity=TaskComplexity.LOW,
                confidence=0.9
            ),
            ClassificationRule(
                patterns=["register", "sign up", "create account", "complete.*registration"],
                task_type=TaskType.FORM_SUBMISSION,
                complexity=TaskComplexity.MEDIUM,
                confidence=0.85
            )
        ])
        
        # Search and filter rules
        self._classification_rules.extend([
            ClassificationRule(
                patterns=["search", "filter", "find.*product", "look for"],
                task_type=TaskType.SEARCH_AND_FILTER,
                complexity=TaskComplexity.MEDIUM,
                confidence=0.8
            )
        ])
        
        # Authentication rules
        self._classification_rules.extend([
            ClassificationRule(
                patterns=["log in", "login", "sign in", "authenticate"],
                task_type=TaskType.AUTHENTICATION,
                complexity=TaskComplexity.LOW,
                confidence=0.95
            ),
            ClassificationRule(
                patterns=["two.*factor", "2fa", "multi.*factor"],
                task_type=TaskType.AUTHENTICATION,
                complexity=TaskComplexity.HIGH,
                confidence=0.9
            )
        ])
        
        # File operations
        self._classification_rules.extend([
            ClassificationRule(
                patterns=["upload.*file", "attach.*file", "select.*file"],
                task_type=TaskType.FILE_UPLOAD,
                complexity=TaskComplexity.MEDIUM,
                confidence=0.9
            ),
            ClassificationRule(
                patterns=["download.*file", "save.*file", "get.*file"],
                task_type=TaskType.FILE_DOWNLOAD,
                complexity=TaskComplexity.LOW,
                confidence=0.85
            )
        ])
        
        # Screenshot rules
        self._classification_rules.extend([
            ClassificationRule(
                patterns=["screenshot", "capture.*screen", "take.*picture", "save.*image"],
                task_type=TaskType.SCREENSHOT_CAPTURE,
                complexity=TaskComplexity.VERY_LOW,
                confidence=0.95
            )
        ])
        
        # Complex interaction rules
        self._classification_rules.extend([
            ClassificationRule(
                patterns=["drag.*drop", "hover.*click", "complex.*interaction", "multi.*step"],
                task_type=TaskType.COMPLEX_INTERACTION,
                complexity=TaskComplexity.HIGH,
                confidence=0.8
            )
        ])
    
    def _setup_site_profiles(self) -> None:
        """Setup built-in site profiles for common websites."""
        
        # Social media sites
        self._site_profiles.update({
            "facebook.com": SiteProfile(
                domain="facebook.com",
                common_tasks=[TaskType.AUTHENTICATION, TaskType.DATA_EXTRACTION, TaskType.COMPLEX_INTERACTION],
                complexity_bias=1,
                requires_auth=True,
                has_dynamic_content=True,
                performance_notes=["Heavy JavaScript", "Dynamic content loading"]
            ),
            "twitter.com": SiteProfile(
                domain="twitter.com",
                common_tasks=[TaskType.AUTHENTICATION, TaskType.DATA_EXTRACTION, TaskType.FORM_SUBMISSION],
                complexity_bias=1,
                requires_auth=True,
                has_dynamic_content=True,
                performance_notes=["Real-time updates", "Infinite scroll"]
            )
        })
        
        # E-commerce sites
        self._site_profiles.update({
            "amazon.com": SiteProfile(
                domain="amazon.com",
                common_tasks=[TaskType.SEARCH_AND_FILTER, TaskType.DATA_EXTRACTION, TaskType.FORM_SUBMISSION],
                complexity_bias=0,
                requires_auth=False,
                has_dynamic_content=True,
                performance_notes=["Large product catalogs", "Dynamic pricing"]
            )
        })
    
    async def health_check(self) -> bool:
        """Check health of task classifier."""
        try:
            # Check if rules are loaded
            if not self._classification_rules:
                return False
            
            # Test classification with simple example
            test_result = await self.classify_task("navigate to google.com")
            if not test_result or test_result["task_type"] == TaskType.UNKNOWN:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    async def cleanup(self) -> bool:
        """Cleanup task classifier resources."""
        try:
            # Clear caches
            self._classification_cache.clear()
            self._site_profile_cache.clear()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            return False
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get classifier metrics and statistics."""
        return {
            **self._metrics,
            "rules_loaded": len(self._classification_rules),
            "site_profiles_loaded": len(self._site_profiles),
            "cached_classifications": len(self._classification_cache),
            "cached_site_profiles": len(self._site_profile_cache)
        }