"""
Base Provider Adapter
Abstract interface for email service providers
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from src.core.config import Config
from src.automation.browser_manager import BrowserManager
from src.utils.logger import get_logger
import asyncio

logger = get_logger(__name__)

class ProviderAdapter(ABC):
    """Abstract base class for email provider adapters."""
    
    def __init__(self, config: Config, browser_manager: BrowserManager):
        self.config = config
        self.browser_manager = browser_manager
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def login(self, credentials: Dict[str, str]) -> bool:
        """
        Login to the email service.
        
        Args:
            credentials: Dictionary containing email and password
            
        Returns:
            True if login successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def send_email(self, task_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send an email using the provider.
        
        Args:
            task_info: Structured task information containing recipients, subject, content, etc.
            
        Returns:
            Dictionary with execution results
        """
        pass
    
    @abstractmethod
    def get_service_url(self) -> str:
        """Get the service URL for this provider."""
        pass
    
    @abstractmethod
    def get_login_selectors(self) -> Dict[str, str]:
        """Get the CSS selectors for login form elements."""
        pass
    
    @abstractmethod
    def get_compose_selectors(self) -> Dict[str, str]:
        """Get the CSS selectors for compose form elements."""
        pass
    
    @abstractmethod
    def get_navigation_selectors(self) -> Dict[str, str]:
        """Get the CSS selectors for navigation elements."""
        pass
    
    async def execute_task(self, task_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a complete task (login + send email).
        
        Args:
            task_info: Structured task information
            
        Returns:
            Dictionary with execution results
        """
        try:
            self.logger.info(f"Starting task execution for {self.__class__.__name__}")
            
            # Get credentials
            provider_name = self.get_provider_name()
            credentials = self.config.get_provider_credentials(provider_name)
            
            # Login
            login_success = await self.login(credentials)
            if not login_success:
                return {
                    "success": False,
                    "error": "Login failed",
                    "provider": provider_name
                }
            
            # Send email
            result = await self.send_email(task_info)
            result["provider"] = provider_name
            
            return result
            
        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": self.get_provider_name()
            }
    
    def get_provider_name(self) -> str:
        """Get the provider name."""
        return self.__class__.__name__.lower().replace("adapter", "")
    
    async def _wait_for_page_load(self, timeout: int = 10) -> bool:
        """Wait for page to load completely."""
        try:
            await self.browser_manager.page.wait_for_load_state('networkidle', timeout=timeout * 1000)
            return True
        except Exception as e:
            self.logger.warning(f"Page load wait failed: {e}")
            return False
    
    async def _take_error_screenshot(self, step_name: str) -> Optional[str]:
        """Take a screenshot for error debugging."""
        if self.config.screenshot_on_error:
            return await self.browser_manager.take_screenshot(f"error_{step_name}.png")
        return None
    
    async def _save_error_html(self, step_name: str) -> Optional[str]:
        """Save HTML for error debugging."""
        if self.config.save_html_on_error:
            return await self.browser_manager.save_page_html(f"error_{step_name}.html")
        return None
    
    def _validate_task_info(self, task_info: Dict[str, Any]) -> bool:
        """Validate that task info contains required fields."""
        required_fields = ["recipients", "content"]
        
        for field in required_fields:
            if not task_info.get(field):
                self.logger.error(f"Missing required field: {field}")
                return False
        
        if not task_info.get("recipients"):
            self.logger.error("No recipients specified")
            return False
        
        return True
    
    def _format_recipients(self, recipients: List[str]) -> str:
        """Format recipients list for input field."""
        if isinstance(recipients, str):
            return recipients
        return ", ".join(recipients)
    
    async def _retry_action(self, action_func, max_retries: int = None) -> bool:
        """Retry an action with exponential backoff."""
        max_retries = max_retries or self.config.retry_attempts
        
        for attempt in range(max_retries):
            try:
                result = await action_func()
                if result:
                    return True
            except Exception as e:
                self.logger.warning(f"Action attempt {attempt + 1} failed: {e}")
            
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return False
