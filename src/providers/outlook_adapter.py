"""
Outlook Provider Adapter
Handles Outlook-specific automation
"""

import asyncio
from typing import Dict, List, Any, Optional
from src.providers.base_provider import ProviderAdapter
from src.core.config import Config
from src.automation.browser_manager import BrowserManager
from src.utils.logger import get_logger

logger = get_logger(__name__)

class OutlookAdapter(ProviderAdapter):
    """Outlook-specific provider adapter."""
    
    def __init__(self, config: Config, browser_manager: BrowserManager):
        super().__init__(config, browser_manager)
        self.service_url = "https://outlook.live.com"
    
    def get_service_url(self) -> str:
        return self.service_url
    
    def get_login_selectors(self) -> Dict[str, str]:
        """Get Outlook-specific login selectors."""
        return {
            "email_field": "input[type='email'], input[name='loginfmt']",
            "password_field": "input[type='password'], input[name='passwd']",
            "submit_button": "input[type='submit'], button[type='submit']",
            "next_button": "input[type='submit'], #idSIButton9",
            "stay_signed_in": "#idBtn_Back"
        }
    
    def get_compose_selectors(self) -> Dict[str, str]:
        """Get Outlook-specific compose selectors."""
        return {
            "to_field": "input[aria-label*='To'], input[placeholder*='To'], .ms-TextField-input",
            "subject_field": "input[aria-label*='Subject'], input[placeholder*='Subject'], .ms-TextField-input",
            "content_field": "div[contenteditable='true'], .ms-Editor-content, iframe[title*='Message']",
            "send_button": "button[aria-label*='Send'], .ms-Button--primary",
            "compose_button": "button[aria-label*='New message'], .ms-Button--primary",
            "compose_area": ".ms-ComposeHeader"
        }
    
    def get_navigation_selectors(self) -> Dict[str, str]:
        """Get Outlook-specific navigation selectors."""
        return {
            "compose_button": "button[aria-label*='New message'], .ms-Button--primary",
            "inbox_link": "a[href*='inbox'], button[aria-label*='Inbox']",
            "sent_link": "a[href*='sent'], button[aria-label*='Sent']",
            "drafts_link": "a[href*='drafts'], button[aria-label*='Drafts']"
        }
    
    async def login(self, credentials: Dict[str, str]) -> bool:
        """Login to Outlook."""
        try:
            self.logger.info("Starting Outlook login process")
            
            # Navigate to Outlook
            if not await self.browser_manager.navigate(self.service_url):
                return False
            
            # Wait for page to load
            await self._wait_for_page_load()
            
            # Check if already logged in
            if await self._is_already_logged_in():
                self.logger.info("Already logged into Outlook")
                return True
            
            # Handle Outlook login process
            login_success = await self._handle_outlook_login(credentials)
            
            if login_success:
                self.logger.info("Outlook login successful")
                return True
            else:
                self.logger.error("Outlook login failed")
                await self._take_error_screenshot("outlook_login_failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Outlook login exception: {e}")
            await self._take_error_screenshot("outlook_login_exception")
            return False
    
    async def send_email(self, task_info: Dict[str, Any]) -> Dict[str, Any]:
        """Send email via Outlook."""
        try:
            self.logger.info("Starting Outlook email send process")
            
            # Validate task info
            if not self._validate_task_info(task_info):
                return {"success": False, "error": "Invalid task information"}
            
            # Navigate to Outlook if not already there
            current_url = self.browser_manager.page.url
            if "outlook.live.com" not in current_url:
                if not await self.browser_manager.navigate(self.service_url):
                    return {"success": False, "error": "Failed to navigate to Outlook"}
            
            # Wait for page to load
            await self._wait_for_page_load()
            
            # Click compose button
            compose_selectors = self.get_compose_selectors()
            compose_button = compose_selectors["compose_button"]
            
            if not await self.browser_manager.click_element(compose_button):
                return {"success": False, "error": "Failed to click compose button"}
            
            # Wait for compose area to load
            await asyncio.sleep(3)
            
            # Fill recipient field
            to_field = compose_selectors["to_field"]
            recipients = self._format_recipients(task_info["recipients"])
            
            if not await self.browser_manager.type_text(to_field, recipients):
                return {"success": False, "error": "Failed to fill recipient field"}
            
            # Press Tab to move to subject field
            await self.browser_manager.page.keyboard.press("Tab")
            await asyncio.sleep(1)
            
            # Fill subject field
            subject = task_info.get("subject", "Message from automation system")
            subject_field = compose_selectors["subject_field"]
            
            if not await self.browser_manager.type_text(subject_field, subject):
                return {"success": False, "error": "Failed to fill subject field"}
            
            # Press Tab to move to content field
            await self.browser_manager.page.keyboard.press("Tab")
            await asyncio.sleep(1)
            
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
            
            self.logger.info("Outlook email sent successfully")
            return {"success": True, "message": "Email sent successfully"}
            
        except Exception as e:
            self.logger.error(f"Outlook send email exception: {e}")
            await self._take_error_screenshot("outlook_send_failed")
            return {"success": False, "error": str(e)}
    
    async def _handle_outlook_login(self, credentials: Dict[str, str]) -> bool:
        """Handle Outlook login process."""
        try:
            # Step 1: Enter email
            login_selectors = self.get_login_selectors()
            email_field = login_selectors["email_field"]
            
            if not await self.browser_manager.type_text(email_field, credentials["email"]):
                return False
            
            # Click next/submit
            next_button = login_selectors["next_button"]
            if not await self.browser_manager.click_element(next_button):
                return False
            
            # Wait for password field to appear
            await asyncio.sleep(2)
            
            # Step 2: Enter password
            password_field = login_selectors["password_field"]
            
            if not await self.browser_manager.type_text(password_field, credentials["password"]):
                return False
            
            # Click sign in
            submit_button = login_selectors["submit_button"]
            if not await self.browser_manager.click_element(submit_button):
                return False
            
            # Handle "Stay signed in" prompt if it appears
            await asyncio.sleep(2)
            try:
                stay_signed_in = login_selectors["stay_signed_in"]
                await self.browser_manager.click_element(stay_signed_in)
            except:
                # Stay signed in prompt might not appear
                pass
            
            # Wait for login to complete
            await asyncio.sleep(5)
            
            # Check if login was successful
            return await self._is_already_logged_in()
            
        except Exception as e:
            self.logger.error(f"Outlook login process failed: {e}")
            return False
    
    async def _is_already_logged_in(self) -> bool:
        """Check if already logged into Outlook."""
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
