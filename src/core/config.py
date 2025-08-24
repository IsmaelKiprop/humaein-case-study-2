"""
Configuration management for the Cross-Platform Action Agent
"""

import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config(BaseModel):
    """Configuration settings for the action agent."""
    
    # OpenAI Configuration
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = Field(default="gpt-4", description="OpenAI model to use")
    
    # Browser Configuration
    headless: bool = Field(default=True, description="Run browser in headless mode")
    timeout: int = Field(default=30, description="Timeout in seconds for operations")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    
    # Email Provider Configuration
    gmail_email: Optional[str] = Field(default_factory=lambda: os.getenv("GMAIL_EMAIL"))
    gmail_password: Optional[str] = Field(default_factory=lambda: os.getenv("GMAIL_PASSWORD"))
    outlook_email: Optional[str] = Field(default_factory=lambda: os.getenv("OUTLOOK_EMAIL"))
    outlook_password: Optional[str] = Field(default_factory=lambda: os.getenv("OUTLOOK_PASSWORD"))
    
    # Agent Configuration
    default_provider: Optional[str] = Field(default=None, description="Default email provider")
    verbose: bool = Field(default=False, description="Enable verbose logging")
    
    # Advanced Configuration
    screenshot_on_error: bool = Field(default=True, description="Take screenshot on error")
    save_html_on_error: bool = Field(default=True, description="Save HTML on error")
    max_wait_time: int = Field(default=10, description="Maximum wait time for elements")
    
    class Config:
        env_prefix = "AGENT_"
        case_sensitive = False
    
    def validate(self) -> bool:
        """Validate the configuration."""
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required")
        
        # Check if at least one email provider is configured
        gmail_configured = bool(self.gmail_email and self.gmail_password)
        outlook_configured = bool(self.outlook_email and self.outlook_password)
        
        if not gmail_configured and not outlook_configured:
            raise ValueError("At least one email provider must be configured")
        
        return True
    
    def get_available_providers(self) -> list[str]:
        """Get list of available email providers."""
        providers = []
        
        if self.gmail_email and self.gmail_password:
            providers.append("gmail")
        
        if self.outlook_email and self.outlook_password:
            providers.append("outlook")
        
        return providers
    
    def get_provider_credentials(self, provider: str) -> dict:
        """Get credentials for a specific provider."""
        if provider == "gmail":
            return {
                "email": self.gmail_email,
                "password": self.gmail_password
            }
        elif provider == "outlook":
            return {
                "email": self.outlook_email,
                "password": self.outlook_password
            }
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def is_provider_configured(self, provider: str) -> bool:
        """Check if a provider is configured."""
        return provider in self.get_available_providers()
