"""
Example usage of the browser automation integration.
Demonstrates how to use the orchestrator and components.
"""

import asyncio
from typing import Dict, Any

from .config import get_browser_automation_config
from .browser_orchestrator import BrowserOrchestrator
from .browser_use_wrapper import BrowserUseWrapper
from .task_classifier import TaskClassifier
from ....log_service import get_logger


async def example_orchestrator_usage():
    """Example of using the browser orchestrator."""
    logger = get_logger("browser_automation_example")
    
    try:
        # Get configuration
        config = get_browser_automation_config()
        
        # Create orchestrator
        orchestrator_config = config.get_component_config("orchestrator")
        orchestrator = BrowserOrchestrator(orchestrator_config)
        
        # Setup orchestrator
        logger.info("Setting up browser orchestrator...")
        success = await orchestrator.setup()
        
        if not success:
            logger.error("Failed to setup orchestrator")
            return
        
        # Example task: Navigate to a website
        task_data = {
            "description": "Navigate to google.com and take a screenshot",
            "url": "https://google.com",
            "parameters": {
                "wait_for_load": True,
                "take_screenshot": True
            },
            "timeout_seconds": 60
        }
        
        context = {
            "tenant_id": "example_tenant",
            "correlation_id": "example_001"
        }
        
        logger.info("Executing browser automation task...")
        result = await orchestrator.execute(task_data, context)
        
        if result.status.value == "success":
            logger.info("Task completed successfully!")
            logger.info(f"Result data: {result.data}")
        else:
            logger.error(f"Task failed: {result.error}")
        
        # Get metrics
        metrics = await orchestrator.get_metrics()
        logger.info(f"Orchestrator metrics: {metrics}")
        
    except Exception as e:
        logger.error(f"Example failed: {e}")
    
    finally:
        # Cleanup
        try:
            await orchestrator.cleanup()
            logger.info("Orchestrator cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


async def example_task_classification():
    """Example of using the task classifier."""
    logger = get_logger("task_classifier_example")
    
    try:
        # Get configuration
        config = get_browser_automation_config()
        classifier_config = config.get_component_config("task_classifier")
        
        # Create classifier
        classifier = TaskClassifier(classifier_config)
        await classifier.setup()
        
        # Test different task types
        test_tasks = [
            {
                "description": "Navigate to google.com",
                "url": "https://google.com"
            },
            {
                "description": "Extract product prices from an e-commerce website", 
                "url": "https://example-store.com/products"
            },
            {
                "description": "Fill out a contact form with my information",
                "parameters": {"name": "John Doe", "email": "john@example.com"}
            },
            {
                "description": "Search for laptops under $1000 and compare features",
                "url": "https://example-electronics.com"
            },
            {
                "description": "Login to my account using two-factor authentication",
                "url": "https://secure-app.com/login"
            }
        ]
        
        logger.info("Classifying different types of browser tasks:")
        
        for i, task in enumerate(test_tasks, 1):
            classification = await classifier.classify_task(**task)
            
            logger.info(f"\nTask {i}: {task['description'][:50]}...")
            logger.info(f"  Type: {classification['task_type']}")
            logger.info(f"  Complexity: {classification['complexity']}")
            logger.info(f"  Confidence: {classification['confidence']:.2f}")
            logger.info(f"  Suggested tool: {classification['suggested_tool']}")
            logger.info(f"  Duration estimate: {classification['estimated_duration_seconds']}s")
            
            if classification.get('reasoning'):
                logger.info(f"  Reasoning: {'; '.join(classification['reasoning'])}")
        
        # Get classifier metrics
        metrics = await classifier.get_metrics()
        logger.info(f"\nClassifier metrics: {metrics}")
        
    except Exception as e:
        logger.error(f"Classification example failed: {e}")
    
    finally:
        try:
            await classifier.cleanup()
        except Exception as e:
            logger.error(f"Classifier cleanup failed: {e}")


async def example_browser_use_wrapper():
    """Example of using the browser-use wrapper directly."""
    logger = get_logger("browser_use_example")
    
    try:
        # Get configuration
        config = get_browser_automation_config()
        wrapper_config = config.get_component_config("browser_use")
        
        # Create wrapper (note: requires browser-use library to be properly installed)
        wrapper = BrowserUseWrapper(wrapper_config)
        
        # Check if browser-use is available
        if not wrapper._is_browser_use_available():
            logger.warning("Browser-use library not available, skipping wrapper example")
            return
        
        await wrapper.setup()
        
        # Example task
        result = await wrapper.execute_task(
            description="Go to google.com and search for 'AutoGen framework'",
            url="https://google.com",
            parameters={"search_query": "AutoGen framework"},
            timeout_seconds=30
        )
        
        logger.info("Browser-use task completed!")
        logger.info(f"Result data: {result.get('data')}")
        logger.info(f"Screenshots: {result.get('screenshots')}")
        logger.info(f"Metadata: {result.get('metadata')}")
        
        # Get wrapper stats
        stats = await wrapper.get_stats()
        logger.info(f"Wrapper stats: {stats}")
        
    except ImportError:
        logger.warning("Browser-use library not available, skipping wrapper example")
    except Exception as e:
        logger.error(f"Browser-use example failed: {e}")
    
    finally:
        try:
            await wrapper.cleanup()
        except Exception as e:
            logger.error(f"Wrapper cleanup failed: {e}")


async def main():
    """Run all examples."""
    logger = get_logger("browser_automation_examples")
    
    logger.info("Starting browser automation integration examples...")
    
    # Example 1: Task Classification
    logger.info("\n" + "="*60)
    logger.info("EXAMPLE 1: Task Classification")
    logger.info("="*60)
    await example_task_classification()
    
    # Example 2: Browser-Use Wrapper (if available)
    logger.info("\n" + "="*60)
    logger.info("EXAMPLE 2: Browser-Use Wrapper")
    logger.info("="*60)
    await example_browser_use_wrapper()
    
    # Example 3: Full Orchestrator (requires setup)
    logger.info("\n" + "="*60)
    logger.info("EXAMPLE 3: Browser Orchestrator")
    logger.info("="*60)
    await example_orchestrator_usage()
    
    logger.info("\n" + "="*60)
    logger.info("All examples completed!")
    logger.info("="*60)


if __name__ == "__main__":
    asyncio.run(main())