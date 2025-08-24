"""
Generic UI Agent
Main agent class that orchestrates the automation process
"""

import time
import asyncio
from typing import Dict, List, Any, Optional
from src.core.config import Config
from src.services.llm_service import LLMService
from src.automation.browser_manager import BrowserManager
from src.providers.gmail_adapter import GmailAdapter
from src.providers.outlook_adapter import OutlookAdapter
from src.utils.logger import get_logger, ActionLogger

logger = get_logger(__name__)

class GenericUIAgent:
    """Main agent class for cross-platform web automation."""
    
    def __init__(self, config: Config):
        self.config = config
        self.llm_service = LLMService(config)
        self.action_logger = ActionLogger(logger)
        self.browser_manager = None
        self.providers = {}
        
        # Validate configuration
        try:
            config.validate()
        except ValueError as e:
            logger.error(f"Configuration validation failed: {e}")
            raise
    
    async def execute(self, instruction: str) -> Dict[str, Any]:
        """
        Execute a natural language instruction.
        
        Args:
            instruction: Natural language instruction to execute
            
        Returns:
            Dictionary with execution results
        """
        start_time = time.time()
        
        try:
            self.action_logger.log_step("Starting instruction execution", instruction)
            
            # Step 1: Interpret the instruction
            task_info = await self._interpret_instruction(instruction)
            if not task_info:
                return self._create_error_result("Failed to interpret instruction")
            
            # Step 2: Select provider
            provider = await self._select_provider(task_info)
            if not provider:
                return self._create_error_result("No suitable provider available")
            
            # Step 3: Initialize browser
            await self._initialize_browser()
            
            # Step 4: Execute the task
            result = await self._execute_task(provider, task_info)
            
            # Step 5: Calculate duration and prepare final result
            duration = time.time() - start_time
            result["duration"] = duration
            result["task_type"] = task_info.get("task_type", "unknown")
            result["actions"] = self.action_logger.get_actions()
            
            self.action_logger.log_success(f"Task completed in {duration:.2f} seconds")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self.action_logger.log_error("Task execution failed", e)
            
            return {
                "success": False,
                "error": str(e),
                "duration": duration,
                "actions": self.action_logger.get_actions(),
                "warnings": ["Task execution failed with exception"]
            }
        
        finally:
            # Clean up browser
            await self._cleanup_browser()
    
    async def _interpret_instruction(self, instruction: str) -> Optional[Dict[str, Any]]:
        """Interpret the natural language instruction."""
        try:
            self.action_logger.log_step("Interpreting instruction")
            
            task_info = await self.llm_service.interpret_instruction(instruction)
            
            self.action_logger.log_action("Instruction interpreted", True, f"Task type: {task_info.get('task_type')}")
            return task_info
            
        except Exception as e:
            self.action_logger.log_error("Instruction interpretation failed", e)
            return None
    
    async def _select_provider(self, task_info: Dict[str, Any]) -> Optional[str]:
        """Select the appropriate provider for the task."""
        try:
            self.action_logger.log_step("Selecting provider")
            
            # Check provider preference
            preference = task_info.get("provider_preference", "auto")
            
            if preference == "auto":
                # Auto-select based on available providers
                available_providers = self.config.get_available_providers()
                
                if not available_providers:
                    self.action_logger.log_error("No providers configured")
                    return None
                
                # For now, prefer Gmail if available
                if "gmail" in available_providers:
                    selected = "gmail"
                else:
                    selected = available_providers[0]
                    
            elif preference in ["gmail", "outlook"]:
                if self.config.is_provider_configured(preference):
                    selected = preference
                else:
                    self.action_logger.log_warning(f"Preferred provider '{preference}' not configured")
                    available_providers = self.config.get_available_providers()
                    selected = available_providers[0] if available_providers else None
            else:
                self.action_logger.log_error(f"Unknown provider preference: {preference}")
                return None
            
            if selected:
                self.action_logger.log_action("Provider selected", True, f"Selected: {selected}")
                return selected
            else:
                self.action_logger.log_error("No suitable provider found")
                return None
                
        except Exception as e:
            self.action_logger.log_error("Provider selection failed", e)
            return None
    
    async def _initialize_browser(self):
        """Initialize the browser manager."""
        try:
            self.action_logger.log_step("Initializing browser")
            
            self.browser_manager = BrowserManager(self.config)
            await self.browser_manager.start()
            
            self.action_logger.log_action("Browser initialized", True)
            
        except Exception as e:
            self.action_logger.log_error("Browser initialization failed", e)
            raise
    
    async def _execute_task(self, provider_name: str, task_info: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the task using the selected provider."""
        try:
            self.action_logger.log_step(f"Executing task with {provider_name}")
            
            # Get or create provider adapter
            provider = await self._get_provider_adapter(provider_name)
            if not provider:
                return self._create_error_result(f"Failed to create provider adapter for {provider_name}")
            
            # Execute the task
            result = await provider.execute_task(task_info)
            
            if result.get("success"):
                self.action_logger.log_success(f"Task completed successfully with {provider_name}")
            else:
                self.action_logger.log_error(f"Task failed with {provider_name}: {result.get('error')}")
            
            return result
            
        except Exception as e:
            self.action_logger.log_error("Task execution failed", e)
            return self._create_error_result(str(e))
    
    async def _get_provider_adapter(self, provider_name: str):
        """Get or create a provider adapter."""
        if provider_name in self.providers:
            return self.providers[provider_name]
        
        try:
            if provider_name == "gmail":
                adapter = GmailAdapter(self.config, self.browser_manager)
            elif provider_name == "outlook":
                adapter = OutlookAdapter(self.config, self.browser_manager)
            else:
                self.action_logger.log_error(f"Unknown provider: {provider_name}")
                return None
            
            self.providers[provider_name] = adapter
            return adapter
            
        except Exception as e:
            self.action_logger.log_error(f"Failed to create {provider_name} adapter", e)
            return None
    
    async def _cleanup_browser(self):
        """Clean up browser resources."""
        try:
            if self.browser_manager:
                await self.browser_manager.stop()
                self.browser_manager = None
                self.action_logger.log_action("Browser cleanup completed", True)
        except Exception as e:
            logger.error(f"Browser cleanup failed: {e}")
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create a standardized error result."""
        return {
            "success": False,
            "error": error_message,
            "duration": 0,
            "actions": self.action_logger.get_actions(),
            "warnings": [error_message]
        }
    
    async def execute_with_dom_analysis(self, instruction: str) -> Dict[str, Any]:
        """
        Execute instruction with advanced DOM analysis.
        This is an experimental feature that uses LLM to analyze DOM structure.
        """
        try:
            self.action_logger.log_step("Starting advanced execution with DOM analysis")
            
            # Interpret instruction
            task_info = await self._interpret_instruction(instruction)
            if not task_info:
                return self._create_error_result("Failed to interpret instruction")
            
            # Select provider
            provider_name = await self._select_provider(task_info)
            if not provider_name:
                return self._create_error_result("No suitable provider available")
            
            # Initialize browser
            await self._initialize_browser()
            
            # Get provider adapter
            provider = await self._get_provider_adapter(provider_name)
            if not provider:
                return self._create_error_result(f"Failed to create provider adapter")
            
            # Navigate to service
            service_url = provider.get_service_url()
            if not await self.browser_manager.navigate(service_url):
                return self._create_error_result("Failed to navigate to service")
            
            # Get page content for DOM analysis
            html_content = await self.browser_manager.get_page_content()
            
            # Analyze DOM structure
            dom_analysis = await self.llm_service.analyze_dom_structure(html_content, task_info)
            
            # Generate action plan
            action_plan = await self.llm_service.generate_action_plan(task_info, dom_analysis)
            
            # Execute action plan
            result = await self.browser_manager.execute_action_plan(action_plan)
            
            # Add additional context
            result["provider"] = provider_name
            result["task_type"] = task_info.get("task_type", "unknown")
            result["actions"] = self.action_logger.get_actions()
            
            return result
            
        except Exception as e:
            self.action_logger.log_error("Advanced execution failed", e)
            return self._create_error_result(str(e))
        
        finally:
            await self._cleanup_browser()
    
    def get_supported_tasks(self) -> List[str]:
        """Get list of supported task types."""
        return ["email", "upload", "schedule", "ticket", "post"]
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers."""
        return self.config.get_available_providers()
    
    def get_action_log(self) -> List[Dict[str, Any]]:
        """Get the action log."""
        return self.action_logger.get_actions()
    
    def clear_action_log(self):
        """Clear the action log."""
        self.action_logger.clear_actions()
