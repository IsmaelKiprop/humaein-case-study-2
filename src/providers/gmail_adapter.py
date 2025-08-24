"""
Gmail Provider Adapter
Handles Gmail-specific automation
"""

import asyncio
from typing import Dict, List, Any, Optional
from src.providers.base_provider import ProviderAdapter
from src.core.config import Config
from src.automation.browser_manager import BrowserManager
from src.utils.logger import get_logger

logger = get_logger(__name__)

class GmailAdapter(ProviderAdapter):
    """Gmail-specific provider adapter."""
    
    def __init__(self, config: Config, browser_manager: BrowserManager):
        super().__init__(config, browser_manager)
        self.service_url = "https://gmail.com"
    
    def get_service_url(self) -> str:
        return self.service_url
    
    def get_login_selectors(self) -> Dict[str, str]:
        """Get Gmail-specific login selectors."""
        return {
            "email_field": "input[type='email'], input[name='identifier']",
            "password_field": "input[type='password'], input[name='password']",
            "submit_button": "button[type='submit'], input[type='submit'], #identifierNext, #passwordNext",
            "next_button": "#identifierNext, #passwordNext",
            "email_next": "#identifierNext",
            "password_next": "#passwordNext"
        }
    
    def get_compose_selectors(self) -> Dict[str, str]:
        """Get Gmail-specific compose selectors."""
        return {
            "to_field": "textarea[name='to'], input[name='to'], .aoD.az6 input",
            "subject_field": "input[name='subject'], .aoD.az6 input[placeholder*='Subject']",
            "content_field": "div[contenteditable='true'], .Am.Al.editable, iframe[title*='Message']",
            "send_button": "div[data-tooltip*='Send'], .T-I.J-J5-Ji.aoO.T-I-atl.L3",
            "compose_button": "div[data-tooltip*='Compose'], .T-I.T-I-KE.L3",
            "compose_area": ".AD"
        }
    
    def get_navigation_selectors(self) -> Dict[str, str]:
        """Get Gmail-specific navigation selectors."""
        return {
            "compose_button": "div[data-tooltip*='Compose'], .T-I.T-I-KE.L3, button[aria-label*='Compose']",
            "inbox_link": "a[href*='#inbox'], .TN.bzz.aHS-bnt",
            "sent_link": "a[href*='#sent'], .TN.bzz.aHS-bnt",
            "drafts_link": "a[href*='#draft'], .TN.bzz.aHS-bnt"
        }
    
    async def login(self, credentials: Dict[str, str]) -> bool:
        """Login to Gmail."""
        try:
            self.logger.info("Starting Gmail login process")
            
            # Navigate to Gmail
            if not await self.browser_manager.navigate(self.service_url):
                return False
            
            # Wait for page to load
            await self._wait_for_page_load()
            
            # Check if already logged in
            if await self._is_already_logged_in():
                self.logger.info("Already logged into Gmail")
                return True
            
            # Handle two-step login process
            login_success = await self._handle_gmail_login(credentials)
            
            if login_success:
                self.logger.info("Gmail login successful")
                return True
            else:
                self.logger.error("Gmail login failed")
                await self._take_error_screenshot("gmail_login_failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Gmail login exception: {e}")
            await self._take_error_screenshot("gmail_login_exception")
            return False
    
    async def send_email(self, task_info: Dict[str, Any]) -> Dict[str, Any]:
        """Send email via Gmail."""
        try:
            self.logger.info("Starting Gmail email send process")
            
            # Validate task info
            if not self._validate_task_info(task_info):
                return {"success": False, "error": "Invalid task information"}
            
            # Navigate to Gmail if not already there
            current_url = self.browser_manager.page.url
            if "gmail.com" not in current_url:
                if not await self.browser_manager.navigate(self.service_url):
                    return {"success": False, "error": "Failed to navigate to Gmail"}
            
            # Wait for page to load
            await self._wait_for_page_load()
            
            # Click compose button
            compose_selectors = self.get_compose_selectors()
            compose_button = compose_selectors["compose_button"]
            
            if not await self.browser_manager.click_element(compose_button):
                return {"success": False, "error": "Failed to click compose button"}
            
            # Wait for compose area to load
            await asyncio.sleep(2)
            
            # Fill recipient field
            to_field = compose_selectors["to_field"]
            recipients = self._format_recipients(task_info["recipients"])
            
            if not await self.browser_manager.type_text(to_field, recipients):
                return {"success": False, "error": "Failed to fill recipient field"}
            
            # Fill subject field
            subject = task_info.get("subject", "Message from automation system")
            subject_field = compose_selectors["subject_field"]
            
            if not await self.browser_manager.type_text(subject_field, subject):
                return {"success": False, "error": "Failed to fill subject field"}
            
            # Fill content field
            content = task_info["content"]
            content_field = compose_selectors["content_field"]
            
            if not await self.browser_manager.type_text(content_field, content):
                return {"success": False, "error": "Failed to fill content field"}
            
            # Send the email
            send_button = compose_selectors["send_button"]
            
            if not await self.browser_manager.click_element(send_button):
                return {"success": False, "error": "Failed to click send button"}
            
            # Wait for send to complete
            await asyncio.sleep(3)
            
            self.logger.info("Gmail email sent successfully")
            return {"success": True, "message": "Email sent successfully"}
            
        except Exception as e:
            self.logger.error(f"Gmail send email exception: {e}")
            await self._take_error_screenshot("gmail_send_failed")
            return {"success": False, "error": str(e)}
    
    async def _handle_gmail_login(self, credentials: Dict[str, str]) -> bool:
        """Handle Gmail's two-step login process."""
        try:
            # Step 1: Enter email
            email_selectors = self.get_login_selectors()
            email_field = email_selectors["email_field"]
            
            if not await self.browser_manager.type_text(email_field, credentials["email"]):
                return False
            
            # Click next for email
            email_next = email_selectors["email_next"]
            if not await self.browser_manager.click_element(email_next):
                return False
            
            # Wait for password field to appear
            await asyncio.sleep(2)
            
            # Step 2: Enter password
            password_field = email_selectors["password_field"]
            
            if not await self.browser_manager.type_text(password_field, credentials["password"]):
                return False
            
            # Click next for password
            password_next = email_selectors["password_next"]
            if not await self.browser_manager.click_element(password_next):
                return False
            
            # Wait for login to complete
            await asyncio.sleep(5)
            
            # Check if login was successful
            return await self._is_already_logged_in()
            
        except Exception as e:
            self.logger.error(f"Gmail login process failed: {e}")
            return False
    
    async def _is_already_logged_in(self) -> bool:
        """Check if already logged into Gmail."""
        try:
            # Look for compose button or inbox
            compose_selectors = self.get_compose_selectors()
            compose_button = compose_selectors["compose_button"]
            
            # Wait a bit for page to load
            await asyncio.sleep(2)
            
            # Check if compose button is visible
            element = await self.browser_manager.page.query_selector(compose_button)
            return element is not None
            
        except Exception as e:
            self.logger.warning(f"Error checking login status: {e}")
            return False
    
    async def _wait_for_compose_area(self) -> bool:
        """Wait for compose area to be ready."""
        try:
            compose_selectors = self.get_compose_selectors()
            compose_area = compose_selectors["compose_area"]
            
            await self.browser_manager.page.wait_for_selector(compose_area, timeout=10000)
            return True
            
        except Exception as e:
            self.logger.warning(f"Compose area wait failed: {e}")
            return False
