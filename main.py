#!/usr/bin/env python3
"""
Varga AI - AutoGen SME Platform
Main entry point for demonstrating all implemented agents.
"""

import os
import sys
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path

# Add project root and src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Configure environment
os.environ.setdefault('PYTHONPATH', f"{project_root}:{project_root / 'src'}")

# Import logging first
from src.log_service import get_logger

# Import configuration
from src.config.settings import PlatformSettings
from src.config.config_manager import ConfigManager

# Import agents
try:
    from agents.categories.education.language_teacher.agent import LanguageTeacherAgent
    from agents.categories.marketing.image_generator.agent import ImageGeneratorAgent
    from agents.categories.assistant.smart_assistant_orchestrator import SmartAssistantOrchestrator
    AGENTS_AVAILABLE = True
except ImportError as e:
    AGENTS_AVAILABLE = False
    AGENT_IMPORT_ERROR = str(e)

# Import tools
try:
    from src.tools.tool_initializer import initialize_tools, get_tool
    from src.tools.web_search_tool import WebSearchTool
    from src.tools.text_generation_tool import TextGenerationTool
    from src.tools.chatbot_interface_tool import ChatbotInterfaceTool
    TOOLS_AVAILABLE = True
except ImportError as e:
    TOOLS_AVAILABLE = False
    TOOLS_IMPORT_ERROR = str(e)

# Initialize logger
logger = get_logger("main")


class VargaAIPlatform:
    """
    Main platform class for Varga AI SME Automation.
    """
    
    def __init__(self):
        """Initialize the platform."""
        self.logger = get_logger("varga_platform")
        self.config = None
        self.config_manager = None
        self.agents = {}
        self.tools = {}
        
    async def initialize(self) -> bool:
        """
        Initialize platform components.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.info("="*60)
            self.logger.info("🚀 Initializing Varga AI Platform")
            self.logger.info("="*60)
            
            # Load configuration
            self.logger.info("Loading configuration...")
            self.config = PlatformSettings()
            self.config_manager = ConfigManager()  # ConfigManager is a singleton, no args needed
            
            # Initialize tools if available
            if TOOLS_AVAILABLE:
                self.logger.info("Initializing tools...")
                await self._initialize_tools()
            else:
                self.logger.warning(f"Tools not available: {TOOLS_IMPORT_ERROR if 'TOOLS_IMPORT_ERROR' in globals() else 'Unknown error'}")
            
            # Initialize agents if available
            if AGENTS_AVAILABLE:
                self.logger.info("Initializing agents...")
                await self._initialize_agents()
            else:
                self.logger.warning(f"Agents not available: {AGENT_IMPORT_ERROR if 'AGENT_IMPORT_ERROR' in globals() else 'Unknown error'}")
            
            self.logger.info("✅ Platform initialization complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize platform: {e}", exc_info=True)
            return False
    
    async def _initialize_tools(self) -> None:
        """
        Initialize available tools.
        """
        try:
            # Initialize all tools
            await initialize_tools()
            
            # Get references to initialized tools
            tool_types = ['web_search', 'text_generation', 'chatbot_interface']
            for tool_type in tool_types:
                tool = get_tool(tool_type)
                if tool:
                    self.tools[tool_type] = tool
                    self.logger.info(f"  ✓ {tool_type} tool initialized")
                else:
                    self.logger.warning(f"  ✗ {tool_type} tool not available")
                    
        except Exception as e:
            self.logger.error(f"Error initializing tools: {e}")
    
    async def _initialize_agents(self) -> None:
        """
        Initialize available agents.
        """
        try:
            # Initialize Language Teacher Agent
            try:
                language_teacher = LanguageTeacherAgent({
                    'target_language': 'english',
                    'agent_name': 'LanguageTeacher'
                })
                self.agents['language_teacher'] = language_teacher
                self.logger.info("  ✓ Language Teacher Agent initialized")
            except Exception as e:
                self.logger.error(f"  ✗ Failed to initialize Language Teacher: {e}")
            
            # Initialize Image Generator Agent
            try:
                image_generator = ImageGeneratorAgent()
                self.agents['image_generator'] = image_generator
                self.logger.info("  ✓ Image Generator Agent initialized")
            except Exception as e:
                self.logger.error(f"  ✗ Failed to initialize Image Generator: {e}")
            
            # Initialize Smart Assistant Orchestrator
            try:
                smart_assistant = SmartAssistantOrchestrator()
                self.agents['smart_assistant'] = smart_assistant
                self.logger.info("  ✓ Smart Assistant Orchestrator initialized")
            except Exception as e:
                self.logger.error(f"  ✗ Failed to initialize Smart Assistant: {e}")
                
        except Exception as e:
            self.logger.error(f"Error initializing agents: {e}")
    
    def display_menu(self) -> None:
        """
        Display the main menu.
        """
        print("\n" + "="*60)
        print("🤖 VARGA AI - SME AUTOMATION PLATFORM")
        print("="*60)
        print("\n📊 Platform Status:")
        print(f"  • Tools Available: {len(self.tools)} of 3")
        print(f"  • Agents Available: {len(self.agents)} of 3")
        print(f"  • Environment: {self.config.environment if self.config else 'Unknown'}")
        
        print("\n🔧 Available Tools:")
        for tool_name in self.tools:
            print(f"  • {tool_name.replace('_', ' ').title()}")
        
        print("\n🤖 Available Agents:")
        for agent_name in self.agents:
            print(f"  • {agent_name.replace('_', ' ').title()}")
        
        print("\n📋 Menu Options:")
        print("  1. Test Language Teacher Agent")
        print("  2. Test Image Generator Agent")
        print("  3. Test Smart Assistant Orchestrator")
        print("  4. Test Web Search Tool")
        print("  5. Test Text Generation Tool")
        print("  6. Test Chatbot Interface Tool")
        print("  7. Show Platform Statistics")
        print("  8. Show Configuration")
        print("  0. Exit")
        print("\n" + "="*60)
    
    async def test_language_teacher(self) -> None:
        """
        Test the Language Teacher Agent.
        """
        if 'language_teacher' not in self.agents:
            print("❌ Language Teacher Agent not available")
            return
        
        print("\n🎓 Testing Language Teacher Agent")
        print("Type 'exit' to return to menu\n")
        
        agent = self.agents['language_teacher']
        
        while True:
            user_input = input("Student: ")
            if user_input.lower() == 'exit':
                break
            
            try:
                # Process the message
                response = await agent.process_message(
                    user_id="test_user",
                    message=user_input,
                    context={}
                )
                print(f"Teacher: {response.get('response', 'No response')}")
                
            except Exception as e:
                print(f"Error: {e}")
    
    async def test_image_generator(self) -> None:
        """
        Test the Image Generator Agent.
        """
        if 'image_generator' not in self.agents:
            print("❌ Image Generator Agent not available")
            return
        
        print("\n🎨 Testing Image Generator Agent")
        print("Describe an image to generate (or 'exit' to return):\n")
        
        agent = self.agents['image_generator']
        
        prompt = input("Image description: ")
        if prompt.lower() == 'exit':
            return
        
        try:
            print("Generating image...")
            result = await agent.generate_image(
                prompt=prompt,
                style="realistic",
                size="1024x1024"
            )
            
            if result.get('success'):
                print(f"✅ Image generated successfully!")
                print(f"URL: {result.get('url', 'N/A')}")
            else:
                print(f"❌ Failed to generate image: {result.get('error')}")
                
        except Exception as e:
            print(f"Error: {e}")
    
    async def test_smart_assistant(self) -> None:
        """
        Test the Smart Assistant Orchestrator.
        """
        if 'smart_assistant' not in self.agents:
            print("❌ Smart Assistant Orchestrator not available")
            return
        
        print("\n🤖 Testing Smart Assistant Orchestrator")
        print("Ask anything (or 'exit' to return):\n")
        
        agent = self.agents['smart_assistant']
        
        while True:
            user_input = input("You: ")
            if user_input.lower() == 'exit':
                break
            
            try:
                response = await agent.process(
                    message=user_input,
                    chat_id=123456,
                    context={}
                )
                print(f"Assistant: {response.content if hasattr(response, 'content') else response}")
                
            except Exception as e:
                print(f"Error: {e}")
    
    async def test_web_search(self) -> None:
        """
        Test the Web Search Tool.
        """
        if 'web_search' not in self.tools:
            print("❌ Web Search Tool not available")
            return
        
        print("\n🔍 Testing Web Search Tool")
        query = input("Enter search query (or 'exit' to return): ")
        
        if query.lower() == 'exit':
            return
        
        try:
            tool = self.tools['web_search']
            result = await tool.execute({"query": query, "max_results": 5})
            
            if result.success:
                print(f"\n✅ Search Results:")
                for i, item in enumerate(result.data.get('results', []), 1):
                    print(f"\n{i}. {item.get('title', 'No title')}")
                    print(f"   {item.get('snippet', 'No snippet')}")
                    print(f"   URL: {item.get('link', 'No URL')}")
            else:
                print(f"❌ Search failed: {result.error}")
                
        except Exception as e:
            print(f"Error: {e}")
    
    async def test_text_generation(self) -> None:
        """
        Test the Text Generation Tool.
        """
        if 'text_generation' not in self.tools:
            print("❌ Text Generation Tool not available")
            return
        
        print("\n✍️ Testing Text Generation Tool")
        print("Content types: email, document, summary, proposal, marketing_copy")
        
        content_type = input("Enter content type: ")
        topic = input("Enter topic/subject: ")
        
        try:
            tool = self.tools['text_generation']
            result = await tool.execute({
                "content_type": content_type,
                "parameters": {"topic": topic}
            })
            
            if result.success:
                print(f"\n✅ Generated Content:")
                print(result.data.get('content', 'No content generated'))
            else:
                print(f"❌ Generation failed: {result.error}")
                
        except Exception as e:
            print(f"Error: {e}")
    
    async def test_chatbot(self) -> None:
        """
        Test the Chatbot Interface Tool.
        """
        if 'chatbot_interface' not in self.tools:
            print("❌ Chatbot Interface Tool not available")
            return
        
        print("\n💬 Testing Chatbot Interface Tool")
        print("Chat with the bot (or 'exit' to return):\n")
        
        tool = self.tools['chatbot_interface']
        session_id = "test_session"
        
        while True:
            user_input = input("You: ")
            if user_input.lower() == 'exit':
                break
            
            try:
                result = await tool.execute({
                    "message": user_input,
                    "session_id": session_id
                })
                
                if result.success:
                    print(f"Bot: {result.data.get('response', 'No response')}")
                else:
                    print(f"❌ Chat failed: {result.error}")
                    
            except Exception as e:
                print(f"Error: {e}")
    
    def show_statistics(self) -> None:
        """
        Show platform statistics.
        """
        print("\n📊 Platform Statistics")
        print("="*40)
        print(f"Tools Loaded: {len(self.tools)}")
        print(f"Agents Loaded: {len(self.agents)}")
        
        if self.tools:
            print("\nTool Status:")
            for tool_name, tool in self.tools.items():
                health = tool.health_check()
                status = "✅ Healthy" if health.get('healthy', False) else "❌ Unhealthy"
                print(f"  • {tool_name}: {status}")
        
        if self.agents:
            print("\nAgent Status:")
            for agent_name in self.agents:
                print(f"  • {agent_name}: ✅ Ready")
    
    def show_configuration(self) -> None:
        """
        Show current configuration.
        """
        if not self.config:
            print("❌ Configuration not loaded")
            return
        
        print("\n⚙️ Platform Configuration")
        print("="*40)
        print(f"Environment: {self.config.environment}")
        print(f"Debug Mode: {self.config.debug}")
        print(f"Log Level: {self.config.log_level}")
        
        if self.config.tool_configs:
            print("\nTool Configurations:")
            for tool_name, enabled in [
                ('web_search', self.config.tool_configs.web_search.enabled),
                ('text_generation', self.config.tool_configs.text_generation.enabled),
                ('chatbot_interface', self.config.tool_configs.chatbot_interface.enabled)
            ]:
                status = "✅" if enabled else "❌"
                print(f"  • {tool_name}: {status}")
    
    async def run(self) -> None:
        """
        Run the main platform loop.
        """
        # Initialize platform
        if not await self.initialize():
            print("❌ Failed to initialize platform")
            return
        
        # Main loop
        while True:
            try:
                self.display_menu()
                choice = input("\nSelect an option: ")
                
                if choice == '0':
                    print("\n👋 Goodbye!")
                    break
                elif choice == '1':
                    await self.test_language_teacher()
                elif choice == '2':
                    await self.test_image_generator()
                elif choice == '3':
                    await self.test_smart_assistant()
                elif choice == '4':
                    await self.test_web_search()
                elif choice == '5':
                    await self.test_text_generation()
                elif choice == '6':
                    await self.test_chatbot()
                elif choice == '7':
                    self.show_statistics()
                elif choice == '8':
                    self.show_configuration()
                else:
                    print("❌ Invalid option")
                
                if choice != '0':
                    input("\nPress Enter to continue...")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}", exc_info=True)
                print(f"\n❌ An error occurred: {e}")


async def main():
    """
    Main entry point.
    """
    try:
        # Print welcome banner
        print("\n" + "="*60)
        print("🚀 VARGA AI - AUTOGEN SME AUTOMATION PLATFORM")
        print("   Democratizing AI for Small & Medium Enterprises")
        print("="*60)
        
        # Create and run platform
        platform = VargaAIPlatform()
        await platform.run()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the async main function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
