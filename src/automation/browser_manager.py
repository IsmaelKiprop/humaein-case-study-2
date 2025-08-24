"""
Browser Manager for Playwright automation
"""

import asyncio
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from src.core.config import Config
from src.utils.logger import get_logger, ActionLogger

logger = get_logger(__name__)

class BrowserManager:
    """Manages browser automation sessions with Playwright."""
    
    def __init__(self, config: Config):
        self.config = config
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.action_logger = ActionLogger(logger)
        
        # Create screenshots directory
        self.screenshots_dir = Path("screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
    
    async def start(self):
        """Start the browser session."""
        try:
            self.action_logger.log_step("Starting browser session")
            
            self.playwright = await async_playwright().start()
            
            # Launch browser
            self.browser = await self.playwright.chromium.launch(
                headless=self.config.headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # Create context
            self.context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            
            # Create page
            self.page = await self.context.new_page()
            
            # Set timeouts
            self.page.set_default_timeout(self.config.timeout * 1000)
            self.page.set_default_navigation_timeout(self.config.timeout * 1000)
            
            self.action_logger.log_success("Browser session started successfully")
            
        except Exception as e:
            self.action_logger.log_error("Failed to start browser session", e)
            raise
    
    async def stop(self):
        """Stop the browser session."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            
            self.action_logger.log_success("Browser session stopped")
            
        except Exception as e:
            logger.error(f"Error stopping browser: {e}")
    
    async def navigate(self, url: str) -> bool:
        """Navigate to a URL."""
        try:
            self.action_logger.log_step(f"Navigating to {url}")
            
            await self.page.goto(url, wait_until='networkidle')
            
            self.action_logger.log_action(f"Navigated to {url}", True)
            return True
            
        except Exception as e:
            self.action_logger.log_action(f"Navigate to {url}", False, str(e))
            return False
    
    async def click_element(self, selector: str, fallback_selectors: List[str] = None) -> bool:
        """Click an element with fallback selectors."""
        selectors_to_try = [selector] + (fallback_selectors or [])
        
        for i, sel in enumerate(selectors_to_try):
            try:
                self.action_logger.log_step(f"Attempting to click element: {sel}")
                
                # Wait for element to be visible and clickable
                await self.page.wait_for_selector(sel, state='visible', timeout=5000)
                
                # Click the element
                await self.page.click(sel)
                
                self.action_logger.log_action(f"Clicked element: {sel}", True)
                return True
                
            except Exception as e:
                if i == len(selectors_to_try) - 1:  # Last attempt
                    self.action_logger.log_action(f"Click element: {sel}", False, str(e))
                    return False
                else:
                    logger.warning(f"Failed to click {sel}, trying fallback: {e}")
        
        return False
    
    async def type_text(self, selector: str, text: str, fallback_selectors: List[str] = None) -> bool:
        """Type text into an element with fallback selectors."""
        selectors_to_try = [selector] + (fallback_selectors or [])
        
        for i, sel in enumerate(selectors_to_try):
            try:
                self.action_logger.log_step(f"Attempting to type in element: {sel}")
                
                # Wait for element to be visible
                await self.page.wait_for_selector(sel, state='visible', timeout=5000)
                
                # Clear existing content and type
                await self.page.fill(sel, text)
                
                self.action_logger.log_action(f"Typed text in element: {sel}", True)
                return True
                
            except Exception as e:
                if i == len(selectors_to_try) - 1:  # Last attempt
                    self.action_logger.log_action(f"Type text in element: {sel}", False, str(e))
                    return False
                else:
                    logger.warning(f"Failed to type in {sel}, trying fallback: {e}")
        
        return False
    
    async def wait_for_element(self, selector: str, timeout: int = None) -> bool:
        """Wait for an element to appear."""
        try:
            timeout_ms = (timeout or self.config.max_wait_time) * 1000
            await self.page.wait_for_selector(selector, state='visible', timeout=timeout_ms)
            
            self.action_logger.log_action(f"Waited for element: {selector}", True)
            return True
            
        except Exception as e:
            self.action_logger.log_action(f"Wait for element: {selector}", False, str(e))
            return False
    
    async def get_page_content(self) -> str:
        """Get the current page's HTML content."""
        try:
            content = await self.page.content()
            return content
        except Exception as e:
            logger.error(f"Failed to get page content: {e}")
            return ""
    
    async def take_screenshot(self, filename: str = None) -> Optional[str]:
        """Take a screenshot of the current page."""
        try:
            if filename is None:
                timestamp = int(time.time())
                filename = f"screenshot_{timestamp}.png"
            
            filepath = self.screenshots_dir / filename
            await self.page.screenshot(path=str(filepath))
            
            self.action_logger.log_action(f"Took screenshot: {filename}", True)
            return str(filepath)
            
        except Exception as e:
            self.action_logger.log_action("Take screenshot", False, str(e))
            return None
    
    async def save_page_html(self, filename: str = None) -> Optional[str]:
        """Save the current page's HTML."""
        try:
            if filename is None:
                timestamp = int(time.time())
                filename = f"page_{timestamp}.html"
            
            filepath = self.screenshots_dir / filename
            content = await self.page.content()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.action_logger.log_action(f"Saved HTML: {filename}", True)
            return str(filepath)
            
        except Exception as e:
            self.action_logger.log_action("Save HTML", False, str(e))
            return None
    
    async def execute_action_plan(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a list of actions."""
        results = {
            "success": True,
            "actions": [],
            "errors": [],
            "screenshots": []
        }
        
        for action in actions:
            try:
                step = action.get("step", 0)
                action_type = action.get("action", "")
                target = action.get("target", "")
                value = action.get("value", "")
                description = action.get("description", "")
                fallback_actions = action.get("fallback_actions", [])
                
                self.action_logger.log_step(f"Step {step}: {description}")
                
                success = False
                
                if action_type == "navigate":
                    success = await self.navigate(target)
                
                elif action_type == "click":
                    fallback_selectors = [fa.get("target") for fa in fallback_actions]
                    success = await self.click_element(target, fallback_selectors)
                
                elif action_type == "type":
                    fallback_selectors = [fa.get("target") for fa in fallback_actions]
                    success = await self.type_text(target, value, fallback_selectors)
                
                elif action_type == "wait":
                    success = await self.wait_for_element(target)
                
                elif action_type == "verify":
                    # Simple verification - check if element exists
                    success = await self.wait_for_element(target, timeout=5)
                
                # Record action result
                action_result = {
                    "step": step,
                    "action": action_type,
                    "target": target,
                    "description": description,
                    "success": success
                }
                
                results["actions"].append(action_result)
                
                if not success:
                    results["success"] = False
                    results["errors"].append(f"Step {step} failed: {description}")
                    
                    # Take screenshot on failure if enabled
                    if self.config.screenshot_on_error:
                        screenshot_path = await self.take_screenshot(f"error_step_{step}.png")
                        if screenshot_path:
                            results["screenshots"].append(screenshot_path)
                    
                    # Save HTML on failure if enabled
                    if self.config.save_html_on_error:
                        html_path = await self.save_page_html(f"error_step_{step}.html")
                        if html_path:
                            results["screenshots"].append(html_path)
                
                # Small delay between actions
                await asyncio.sleep(0.5)
                
            except Exception as e:
                results["success"] = False
                results["errors"].append(f"Step {step} exception: {str(e)}")
                self.action_logger.log_error(f"Action execution failed at step {step}", e)
        
        return results
    
    async def login_to_service(self, service_url: str, credentials: Dict[str, str], selectors: Dict[str, str]) -> bool:
        """Login to a service using provided credentials and selectors."""
        try:
            self.action_logger.log_step(f"Logging into service at {service_url}")
            
            # Navigate to service
            if not await self.navigate(service_url):
                return False
            
            # Wait for login form
            email_selector = selectors.get("email_field")
            password_selector = selectors.get("password_field")
            submit_selector = selectors.get("submit_button")
            
            if not all([email_selector, password_selector, submit_selector]):
                self.action_logger.log_error("Missing required login selectors")
                return False
            
            # Fill email
            if not await self.type_text(email_selector, credentials["email"]):
                return False
            
            # Fill password
            if not await self.type_text(password_selector, credentials["password"]):
                return False
            
            # Submit form
            if not await self.click_element(submit_selector):
                return False
            
            # Wait for login to complete (look for inbox or compose button)
            await asyncio.sleep(3)
            
            self.action_logger.log_success("Login completed successfully")
            return True
            
        except Exception as e:
            self.action_logger.log_error("Login failed", e)
            return False
    
    def get_action_log(self) -> List[Dict[str, Any]]:
        """Get the action log."""
        return self.action_logger.get_actions()
