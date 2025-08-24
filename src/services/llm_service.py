"""
LLM Service for instruction interpretation and UI reasoning
"""

import json
import re
from typing import Dict, List, Optional, Any
from openai import OpenAI
from src.core.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)

class LLMService:
    """Service for LLM-powered instruction interpretation and reasoning."""
    
    def __init__(self, config: Config):
        self.config = config
        # Temporarily disable OpenAI client initialization
        # self.client = OpenAI(
        #     api_key=config.openai_api_key
        # )
        self.client = None
        self.model = config.openai_model
    
    async def interpret_instruction(self, instruction: str) -> Dict[str, Any]:
        """
        Interpret a natural language instruction and extract structured information.
        
        Args:
            instruction: Natural language instruction
            
        Returns:
            Structured task information
        """
        
        prompt = f"""
        You are an AI assistant that interprets natural language instructions for web automation tasks.
        
        Given the instruction: "{instruction}"
        
        Please extract the following information in JSON format:
        {{
            "task_type": "email|upload|schedule|ticket|post",
            "action": "send|upload|schedule|submit|post",
            "recipients": ["email1@example.com", "email2@example.com"],
            "subject": "email subject if specified",
            "content": "main content/message",
            "attachments": ["file1.pdf", "file2.jpg"],
            "provider_preference": "gmail|outlook|auto",
            "urgency": "high|medium|low",
            "additional_context": "any other relevant information"
        }}
        
        Rules:
        - For email tasks, extract recipients, subject, and content
        - If no subject is mentioned, use a default based on content
        - If multiple recipients are mentioned, include all
        - If no provider preference is mentioned, use "auto"
        - For non-email tasks, adapt the structure appropriately
        
        Return only valid JSON.
        """
        
        try:
            response = self._call_llm(prompt)
            result = json.loads(response)
            
            # Validate and clean the result
            result = self._validate_task_info(result)
            
            logger.info(f"Interpreted instruction: {result['task_type']} task")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            # Fallback to basic parsing
            return self._fallback_parsing(instruction)
        except Exception as e:
            logger.error(f"LLM interpretation failed: {e}")
            return self._fallback_parsing(instruction)
    
    async def analyze_dom_structure(self, html_content: str, task_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze DOM structure to identify relevant elements for the task.
        
        Args:
            html_content: HTML content of the page
            task_context: Context about the task being performed
            
        Returns:
            Analysis results with element selectors and actions
        """
        
        # Truncate HTML if too long
        if len(html_content) > 8000:
            html_content = html_content[:8000] + "..."
        
        prompt = f"""
        You are analyzing a web page's DOM structure to identify elements for automation.
        
        Task Context: {json.dumps(task_context, indent=2)}
        
        HTML Content:
        {html_content}
        
        Please identify the following elements and provide CSS selectors or XPath expressions:
        {{
            "login_form": {{
                "email_field": "selector for email input",
                "password_field": "selector for password input",
                "submit_button": "selector for login button"
            }},
            "compose_form": {{
                "to_field": "selector for recipient field",
                "subject_field": "selector for subject field",
                "content_field": "selector for message content",
                "send_button": "selector for send button"
            }},
            "navigation": {{
                "compose_button": "selector for compose/new message button",
                "inbox_link": "selector for inbox navigation"
            }},
            "page_state": {{
                "is_logged_in": "true/false based on page content",
                "current_page": "login|compose|inbox|other"
            }}
        }}
        
        Provide the most reliable selectors possible. Prefer:
        1. IDs
        2. Unique class names
        3. Data attributes
        4. Semantic selectors
        
        Return only valid JSON.
        """
        
        try:
            response = self._call_llm(prompt)
            result = json.loads(response)
            
            logger.info("DOM structure analysis completed")
            return result
            
        except Exception as e:
            logger.error(f"DOM analysis failed: {e}")
            return self._get_fallback_selectors()
    
    async def generate_action_plan(self, task_info: Dict[str, Any], dom_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate a step-by-step action plan based on task and DOM analysis.
        
        Args:
            task_info: Structured task information
            dom_analysis: DOM structure analysis
            
        Returns:
            List of actions to perform
        """
        
        prompt = f"""
        You are generating a step-by-step action plan for web automation.
        
        Task Information: {json.dumps(task_info, indent=2)}
        DOM Analysis: {json.dumps(dom_analysis, indent=2)}
        
        Generate a list of actions in JSON format:
        [
            {{
                "step": 1,
                "action": "navigate|click|type|wait|verify",
                "target": "selector or URL",
                "value": "text to type or expected value",
                "description": "human readable description",
                "fallback_actions": [
                    {{
                        "action": "alternative action if primary fails",
                        "target": "alternative selector"
                    }}
                ]
            }}
        ]
        
        Include actions for:
        1. Navigation to the service
        2. Authentication (if needed)
        3. Finding and clicking compose/new button
        4. Filling form fields
        5. Submitting the form
        6. Verification of success
        
        Return only valid JSON array.
        """
        
        try:
            response = self._call_llm(prompt)
            actions = json.loads(response)
            
            logger.info(f"Generated action plan with {len(actions)} steps")
            return actions
            
        except Exception as e:
            logger.error(f"Action plan generation failed: {e}")
            return self._get_default_action_plan(task_info)
    
    def _call_llm(self, prompt: str) -> str:
        """Make a call to the LLM API."""
        try:
            # For now, let's use a mock response to test the system
            logger.warning("Using mock LLM response for testing")
            return self._get_mock_response(prompt)
            
            # Uncomment below when OpenAI client issue is resolved
            # response = self.client.chat.completions.create(
            #     model=self.model,
            #     messages=[
            #         {"role": "system", "content": "You are a helpful AI assistant for web automation tasks."},
            #         {"role": "user", "content": prompt}
            #     ],
            #     temperature=0.1,
            #     max_tokens=2000
            # )
            # 
            # return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise
    
    def _get_mock_response(self, prompt: str) -> str:
        """Get a mock response for testing purposes."""
        if "interpret" in prompt.lower():
            return '''{
                "task_type": "email",
                "action": "send",
                "recipients": ["demo@example.com"],
                "subject": "Test email from automation",
                "content": "This is a test email from the automation system",
                "attachments": [],
                "provider_preference": "auto",
                "urgency": "medium",
                "additional_context": ""
            }'''
        elif "analyze" in prompt.lower():
            return '''{
                "login_form": {
                    "email_field": "input[type='email']",
                    "password_field": "input[type='password']",
                    "submit_button": "button[type='submit']"
                },
                "compose_form": {
                    "to_field": "input[name*='to']",
                    "subject_field": "input[name*='subject']",
                    "content_field": "textarea",
                    "send_button": "button:contains('Send')"
                },
                "navigation": {
                    "compose_button": "button:contains('Compose')",
                    "inbox_link": "a:contains('Inbox')"
                },
                "page_state": {
                    "is_logged_in": "false",
                    "current_page": "login"
                }
            }'''
        else:
            return '''[
                {
                    "step": 1,
                    "action": "navigate",
                    "target": "https://gmail.com",
                    "value": "",
                    "description": "Navigate to Gmail",
                    "fallback_actions": []
                }
            ]'''
    
    def _validate_task_info(self, task_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean task information."""
        
        # Ensure required fields exist
        defaults = {
            "task_type": "email",
            "action": "send",
            "recipients": [],
            "subject": "",
            "content": "",
            "attachments": [],
            "provider_preference": "auto",
            "urgency": "medium",
            "additional_context": ""
        }
        
        for key, default_value in defaults.items():
            if key not in task_info:
                task_info[key] = default_value
        
        # Clean recipients
        if isinstance(task_info["recipients"], str):
            # Extract emails from string
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', task_info["recipients"])
            task_info["recipients"] = emails
        
        # Generate subject if missing
        if not task_info["subject"] and task_info["content"]:
            task_info["subject"] = self._generate_subject(task_info["content"])
        
        return task_info
    
    def _generate_subject(self, content: str) -> str:
        """Generate a subject line from content."""
        # Simple subject generation
        words = content.split()[:5]  # First 5 words
        subject = " ".join(words)
        if len(subject) > 50:
            subject = subject[:47] + "..."
        return subject
    
    def _fallback_parsing(self, instruction: str) -> Dict[str, Any]:
        """Fallback parsing when LLM fails."""
        logger.warning("Using fallback parsing for instruction")
        
        # Basic email detection
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', instruction)
        
        return {
            "task_type": "email",
            "action": "send",
            "recipients": emails,
            "subject": "Message from automation system",
            "content": instruction,
            "attachments": [],
            "provider_preference": "auto",
            "urgency": "medium",
            "additional_context": ""
        }
    
    def _get_fallback_selectors(self) -> Dict[str, Any]:
        """Get fallback selectors when DOM analysis fails."""
        return {
            "login_form": {
                "email_field": "input[type='email'], input[name*='email'], input[id*='email']",
                "password_field": "input[type='password']",
                "submit_button": "button[type='submit'], input[type='submit']"
            },
            "compose_form": {
                "to_field": "input[name*='to'], input[id*='to'], textarea[name*='to']",
                "subject_field": "input[name*='subject'], input[id*='subject']",
                "content_field": "textarea, div[contenteditable='true'], iframe[title*='Message']",
                "send_button": "button[type='submit'], input[type='submit'], button:contains('Send')"
            },
            "navigation": {
                "compose_button": "button:contains('Compose'), button:contains('New'), a:contains('Compose')",
                "inbox_link": "a:contains('Inbox'), a[href*='inbox']"
            },
            "page_state": {
                "is_logged_in": "false",
                "current_page": "unknown"
            }
        }
    
    def _get_default_action_plan(self, task_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get default action plan when generation fails."""
        return [
            {
                "step": 1,
                "action": "navigate",
                "target": "https://gmail.com",
                "value": "",
                "description": "Navigate to Gmail",
                "fallback_actions": []
            },
            {
                "step": 2,
                "action": "click",
                "target": "button:contains('Compose')",
                "value": "",
                "description": "Click compose button",
                "fallback_actions": []
            },
            {
                "step": 3,
                "action": "type",
                "target": "input[name*='to']",
                "value": ", ".join(task_info.get("recipients", [])),
                "description": "Enter recipient email",
                "fallback_actions": []
            },
            {
                "step": 4,
                "action": "type",
                "target": "input[name*='subject']",
                "value": task_info.get("subject", ""),
                "description": "Enter subject",
                "fallback_actions": []
            },
            {
                "step": 5,
                "action": "type",
                "target": "textarea, div[contenteditable='true']",
                "value": task_info.get("content", ""),
                "description": "Enter message content",
                "fallback_actions": []
            },
            {
                "step": 6,
                "action": "click",
                "target": "button:contains('Send')",
                "value": "",
                "description": "Send the email",
                "fallback_actions": []
            }
        ]
