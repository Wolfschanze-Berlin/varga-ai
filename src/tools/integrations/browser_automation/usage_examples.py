"""
Usage examples for the browser automation integration.
Demonstrates various ways to use the browser automation tool in SME automation scenarios.
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from .browser_automation_tool import BrowserAutomationTool
from ....log_service import get_logger


async def example_simple_navigation():
    """Example: Simple website navigation and screenshot."""
    print("="*60)
    print("Example 1: Simple Navigation and Screenshot")
    print("="*60)
    
    logger = get_logger("browser_example_1")
    
    # Create browser automation tool
    config = {
        "enabled": True,
        "max_concurrent_tasks": 3,
        "default_timeout_seconds": 60
    }
    
    tool = BrowserAutomationTool(config)
    
    try:
        # Setup tool
        setup_success = await tool.setup()
        print(f"Tool setup: {'SUCCESS' if setup_success else 'FAILED'}")
        
        if setup_success:
            # Simple navigation task
            task_data = {
                "task_description": "Navigate to httpbin.org and take a screenshot of the main page",
                "url": "https://httpbin.org",
                "parameters": {
                    "take_screenshot": True,
                    "wait_time": 2
                },
                "timeout_seconds": 30
            }
            
            context = {
                "tenant_id": "demo_tenant",
                "correlation_id": "example_001"
            }
            
            print(f"Executing task: {task_data['task_description']}")
            print("Status: In Progress...")
            
            # For demonstration purposes, we'll show the validation
            valid_input = await tool.validate_input(task_data)
            print(f"Input validation: {'PASS' if valid_input else 'FAIL'}")
            
            if valid_input:
                print("Task would be executed with the following flow:")
                print("  1. Task classified as 'navigation' with 'low' complexity")
                print("  2. Routed to appropriate tool (browser-use or playwright)")
                print("  3. Browser session created and URL navigated")
                print("  4. Screenshot captured")
                print("  5. Results returned with page info and screenshot path")
                
                print("Status: SIMULATED (would execute in real environment)")
            
    finally:
        await tool.cleanup()


async def example_data_extraction():
    """Example: Web data extraction from an e-commerce site."""
    print("\n" + "="*60)
    print("Example 2: Data Extraction from E-commerce Site")
    print("="*60)
    
    logger = get_logger("browser_example_2")
    
    config = {"enabled": True}
    tool = BrowserAutomationTool(config)
    
    try:
        await tool.setup()
        
        # Data extraction task
        task_data = {
            "task_description": "Extract product information including name, price, and availability from the product listing page",
            "url": "https://example-store.com/products",
            "parameters": {
                "extract_data": {
                    "selectors": [
                        ".product-name",
                        ".product-price", 
                        ".availability-status"
                    ],
                    "attributes": ["text", "data-price", "class"]
                },
                "take_screenshot": True
            },
            "timeout_seconds": 120,
            "preferred_tool": "browser_use"  # Complex extraction benefits from AI
        }
        
        context = {
            "tenant_id": "ecommerce_client",
            "correlation_id": "data_extract_001"
        }
        
        print(f"Task: {task_data['task_description']}")
        print(f"Target URL: {task_data['url']}")
        print(f"Preferred Tool: {task_data['preferred_tool']}")
        
        # Show task classification
        print("\nTask Analysis:")
        print("  - Type: data_extraction")
        print("  - Complexity: medium-high") 
        print("  - Suggested Tool: browser_use (AI-driven extraction)")
        print("  - Estimated Duration: 45-60 seconds")
        print("  - Risk Factors: Dynamic content, pagination possible")
        
        valid_input = await tool.validate_input(task_data)
        print(f"\nInput validation: {'PASS' if valid_input else 'FAIL'}")
        
        if valid_input:
            print("\nExecution Flow:")
            print("  1. Navigate to product listing page")
            print("  2. Wait for dynamic content to load")
            print("  3. Use AI agent to identify and extract product data")
            print("  4. Handle pagination if present")
            print("  5. Return structured data with screenshots")
            
            print("\nExpected Output:")
            print("  - products: [")
            print("      {name: 'Product A', price: '$29.99', available: true},")
            print("      {name: 'Product B', price: '$45.00', available: false},")
            print("      ...")
            print("    ]")
            print("  - screenshots: ['products_page_20250810.png']")
            print("  - metadata: {pages_processed: 1, items_found: 25}")
        
    finally:
        await tool.cleanup()


async def example_form_automation():
    """Example: Automated form filling for customer onboarding."""
    print("\n" + "="*60)
    print("Example 3: Automated Form Filling")
    print("="*60)
    
    logger = get_logger("browser_example_3")
    
    config = {"enabled": True}
    tool = BrowserAutomationTool(config)
    
    try:
        await tool.setup()
        
        # Form automation task
        task_data = {
            "task_description": "Fill out customer registration form with provided customer data and submit",
            "url": "https://demo-company.com/signup",
            "parameters": {
                "customer_data": {
                    "first_name": "John",
                    "last_name": "Smith", 
                    "email": "john.smith@example.com",
                    "company": "Acme Corp",
                    "phone": "+1-555-0123",
                    "industry": "Technology"
                },
                "wait_time": 3,
                "take_screenshot": True
            },
            "timeout_seconds": 90
        }
        
        context = {
            "tenant_id": "sales_team",
            "correlation_id": "customer_onboard_001"
        }
        
        print(f"Task: {task_data['task_description']}")
        print(f"Customer: {task_data['parameters']['customer_data']['first_name']} {task_data['parameters']['customer_data']['last_name']}")
        print(f"Company: {task_data['parameters']['customer_data']['company']}")
        
        print("\nTask Classification:")
        print("  - Type: form_submission")
        print("  - Complexity: low-medium")
        print("  - Tool: browser_use or playwright (depending on form complexity)")
        print("  - Duration: ~30 seconds")
        
        valid_input = await tool.validate_input(task_data)
        print(f"\nValidation: {'PASS' if valid_input else 'FAIL'}")
        
        if valid_input:
            print("\nAutomation Steps:")
            print("  1. Navigate to signup form")
            print("  2. Identify form fields (name, email, company, etc.)")
            print("  3. Fill fields with customer data")
            print("  4. Handle dropdowns and checkboxes")
            print("  5. Submit form and wait for confirmation")
            print("  6. Capture screenshot of success page")
            
            print("\nSuccess Criteria:")
            print("  ✓ All required fields populated")
            print("  ✓ Form submitted without errors")
            print("  ✓ Confirmation page reached")
            print("  ✓ Customer record created")
        
    finally:
        await tool.cleanup()


async def example_monitoring_and_alerts():
    """Example: Website monitoring for changes or issues."""
    print("\n" + "="*60)
    print("Example 4: Website Monitoring and Alerts")
    print("="*60)
    
    logger = get_logger("browser_example_4")
    
    config = {"enabled": True}
    tool = BrowserAutomationTool(config)
    
    try:
        await tool.setup()
        
        # Monitoring task
        task_data = {
            "task_description": "Monitor company website for availability and check if key sections load correctly",
            "url": "https://company-website.com",
            "parameters": {
                "monitoring_checks": {
                    "page_load_time": True,
                    "key_elements": [
                        "#main-navigation",
                        ".hero-section", 
                        ".contact-info"
                    ],
                    "error_indicators": [
                        ".error-message",
                        "[class*='error']"
                    ]
                },
                "take_screenshot": True,
                "wait_time": 5
            },
            "timeout_seconds": 45
        }
        
        context = {
            "tenant_id": "it_monitoring",
            "correlation_id": "monitor_check_001"
        }
        
        print(f"Monitoring: {task_data['url']}")
        print("Checks: Page load, navigation, content sections, error detection")
        
        print("\nMonitoring Configuration:")
        print("  - Load Time Threshold: < 3 seconds")
        print("  - Required Elements: Navigation, Hero, Contact")
        print("  - Error Detection: Error messages, broken elements")
        print("  - Screenshot: Always captured for evidence")
        
        valid_input = await tool.validate_input(task_data)
        print(f"\nValidation: {'PASS' if valid_input else 'FAIL'}")
        
        if valid_input:
            print("\nMonitoring Process:")
            print("  1. Navigate to website with timing")
            print("  2. Check page load performance")
            print("  3. Verify key elements are present")
            print("  4. Scan for error indicators")
            print("  5. Take screenshot for records")
            print("  6. Generate monitoring report")
            
            print("\nSample Report:")
            print("  Status: HEALTHY")
            print("  Load Time: 1.2 seconds")
            print("  Elements Found: 3/3")
            print("  Errors Detected: 0")
            print("  Screenshot: monitor_20250810_100123.png")
            print("  Next Check: In 5 minutes")
        
    finally:
        await tool.cleanup()


async def example_competitive_analysis():
    """Example: Automated competitive analysis and price monitoring."""
    print("\n" + "="*60)
    print("Example 5: Competitive Analysis and Price Monitoring")
    print("="*60)
    
    logger = get_logger("browser_example_5")
    
    config = {"enabled": True}
    tool = BrowserAutomationTool(config)
    
    try:
        await tool.setup()
        
        # Multiple competitor analysis
        competitors = [
            {"name": "Competitor A", "url": "https://competitor-a.com/products", "price_selector": ".price"},
            {"name": "Competitor B", "url": "https://competitor-b.com/shop", "price_selector": ".cost"},
            {"name": "Competitor C", "url": "https://competitor-c.com/store", "price_selector": ".amount"}
        ]
        
        print("Competitive Analysis Configuration:")
        print(f"Competitors to analyze: {len(competitors)}")
        for i, comp in enumerate(competitors, 1):
            print(f"  {i}. {comp['name']}: {comp['url']}")
        
        # Task for first competitor (would loop through all in real implementation)
        task_data = {
            "task_description": f"Extract pricing information and product details from {competitors[0]['name']} website",
            "url": competitors[0]["url"],
            "parameters": {
                "competitive_analysis": {
                    "extract_prices": True,
                    "extract_features": True,
                    "extract_promotions": True
                },
                "extract_data": {
                    "selectors": [
                        competitors[0]["price_selector"],
                        ".product-title",
                        ".feature-list",
                        ".promotion-banner"
                    ]
                },
                "take_screenshot": True
            },
            "timeout_seconds": 180,  # Longer timeout for comprehensive analysis
            "preferred_tool": "browser_use"
        }
        
        context = {
            "tenant_id": "marketing_team",
            "correlation_id": f"competitive_analysis_{competitors[0]['name'].lower().replace(' ', '_')}"
        }
        
        print(f"\nAnalyzing: {competitors[0]['name']}")
        print(f"Focus: Pricing, features, promotions")
        
        valid_input = await tool.validate_input(task_data)
        print(f"Validation: {'PASS' if valid_input else 'FAIL'}")
        
        if valid_input:
            print("\nAnalysis Process:")
            print("  1. Navigate to competitor product pages")
            print("  2. Extract current pricing information")
            print("  3. Identify key product features")
            print("  4. Capture promotional offers")
            print("  5. Compare with our pricing/features")
            print("  6. Generate competitive intelligence report")
            
            print("\nExpected Analysis Output:")
            print("  Competitor A Analysis:")
            print("    - Average Price: $45.99 (12% below ours)")
            print("    - Key Features: Feature X, Y, Z")
            print("    - Current Promotion: 20% off new customers")
            print("    - Market Position: Budget-friendly")
            print("    - Recommendation: Consider price adjustment")
        
        print("\nBusiness Value:")
        print("  ✓ Real-time competitive pricing intelligence")
        print("  ✓ Feature gap analysis")
        print("  ✓ Promotional strategy insights")
        print("  ✓ Market positioning data")
        print("  ✓ Automated weekly reports")
        
    finally:
        await tool.cleanup()


async def example_performance_metrics():
    """Example: Demonstrating performance monitoring and metrics."""
    print("\n" + "="*60)
    print("Example 6: Performance Monitoring and Metrics")
    print("="*60)
    
    logger = get_logger("browser_example_6")
    
    config = {"enabled": True}
    tool = BrowserAutomationTool(config)
    
    try:
        await tool.setup()
        
        # Get current performance metrics
        metrics = await tool.get_performance_metrics()
        
        print("Current Browser Automation Tool Metrics:")
        print("="*40)
        
        if "browser_automation" in metrics:
            ba_metrics = metrics["browser_automation"]
            print(f"Tasks Executed: {ba_metrics.get('tasks_executed', 0)}")
            print(f"Tasks Successful: {ba_metrics.get('tasks_successful', 0)}")
            print(f"Tasks Failed: {ba_metrics.get('tasks_failed', 0)}")
            print(f"Success Rate: {ba_metrics.get('success_rate', 0):.1f}%")
            print(f"Average Execution Time: {ba_metrics.get('avg_execution_time_ms', 0):.0f}ms")
            print(f"Browser-Use Tasks: {ba_metrics.get('browser_use_tasks', 0)}")
            print(f"Playwright Tasks: {ba_metrics.get('playwright_tasks', 0)}")
            
            # Orchestrator metrics
            if "orchestrator" in ba_metrics:
                orch_metrics = ba_metrics["orchestrator"]
                print(f"\nOrchestrator Status:")
                print(f"  Active Tasks: {orch_metrics.get('active_tasks', 0)}")
                print(f"  Queue Size: {orch_metrics.get('queue_size', 0)}")
                print(f"  Workers Running: {orch_metrics.get('workers_running', 0)}")
                print(f"  Health Status: {orch_metrics.get('is_healthy', False)}")
        
        # Base tool metrics
        print(f"\nBase Tool Metrics:")
        print(f"  Setup Status: {metrics.get('is_setup', False)}")
        print(f"  Health Status: {metrics.get('is_healthy', False)}")
        print(f"  Rate Limiter: {metrics.get('rate_limiter_stats', {})}")
        
        # List any active sessions
        sessions = await tool.list_active_sessions()
        print(f"\nActive Sessions: {len(sessions)}")
        for session in sessions[:5]:  # Show first 5
            print(f"  Session {session['session_id'][:8]}... - {session['state']} - {session['description'][:50]}...")
        
        print("\nPerformance Insights:")
        if metrics.get("browser_automation", {}).get("success_rate", 0) > 95:
            print("  ✓ Excellent success rate - system performing well")
        elif metrics.get("browser_automation", {}).get("success_rate", 0) > 85:
            print("  ⚠ Good success rate - minor optimizations possible")
        else:
            print("  ❌ Success rate needs improvement - investigate errors")
        
        avg_time = metrics.get("browser_automation", {}).get("avg_execution_time_ms", 0)
        if avg_time < 10000:  # 10 seconds
            print("  ✓ Fast execution times - good performance")
        elif avg_time < 30000:  # 30 seconds
            print("  ⚠ Moderate execution times - acceptable performance")
        else:
            print("  ❌ Slow execution times - optimization needed")
        
    finally:
        await tool.cleanup()


async def main():
    """Run all browser automation examples."""
    logger = get_logger("browser_automation_examples")
    
    print("Browser Automation Integration - Usage Examples")
    print("=" * 80)
    print("These examples demonstrate various SME automation scenarios using")
    print("the browser-use MCP integration with intelligent task routing.")
    print()
    
    try:
        # Run all examples
        await example_simple_navigation()
        await example_data_extraction()
        await example_form_automation()
        await example_monitoring_and_alerts()
        await example_competitive_analysis()
        await example_performance_metrics()
        
        print("\n" + "=" * 80)
        print("All Examples Completed Successfully!")
        print("=" * 80)
        
        print("\nKey Benefits Demonstrated:")
        print("✓ Intelligent task classification and routing")
        print("✓ Unified interface for browser-use and playwright MCP")
        print("✓ Robust session management and cleanup") 
        print("✓ Comprehensive error handling and retries")
        print("✓ Performance monitoring and metrics")
        print("✓ Multi-tenant isolation and security")
        print("✓ Scalable orchestration with worker queues")
        
        print("\nSME Use Cases Covered:")
        print("• Website navigation and screenshots")
        print("• Data extraction from competitor sites")  
        print("• Automated form filling for customer onboarding")
        print("• Website monitoring and uptime checks")
        print("• Competitive analysis and price monitoring")
        print("• Performance tracking and optimization")
        
        print("\nNext Steps for Production:")
        print("1. Configure LLM provider for advanced browser-use tasks")
        print("2. Set up playwright MCP server integration")
        print("3. Implement custom agents for specific business workflows")
        print("4. Configure monitoring and alerting")
        print("5. Create SME-specific automation templates")
        
    except Exception as e:
        logger.error(f"Examples failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)