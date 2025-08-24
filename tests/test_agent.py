"""
Basic tests for the Cross-Platform Action Agent
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.core.config import Config
from src.core.agent import GenericUIAgent
from src.services.llm_service import LLMService

class TestGenericUIAgent:
    """Test cases for the GenericUIAgent class."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        config = Mock(spec=Config)
        config.openai_api_key = "test_key"
        config.gmail_email = "test@gmail.com"
        config.gmail_password = "test_password"
        config.get_available_providers.return_value = ["gmail"]
        config.is_provider_configured.return_value = True
        config.get_provider_credentials.return_value = {
            "email": "test@gmail.com",
            "password": "test_password"
        }
        config.validate.return_value = True
        return config
    
    @pytest.fixture
    def agent(self, mock_config):
        """Create an agent instance for testing."""
        return GenericUIAgent(mock_config)
    
    def test_agent_initialization(self, mock_config):
        """Test that the agent initializes correctly."""
        agent = GenericUIAgent(mock_config)
        assert agent.config == mock_config
        assert agent.llm_service is not None
        assert agent.action_logger is not None
    
    @pytest.mark.asyncio
    async def test_instruction_interpretation(self, agent):
        """Test instruction interpretation."""
        # Mock the LLM service response
        mock_task_info = {
            "task_type": "email",
            "action": "send",
            "recipients": ["test@example.com"],
            "subject": "Test Subject",
            "content": "Test content",
            "provider_preference": "auto"
        }
        
        agent.llm_service.interpret_instruction = AsyncMock(return_value=mock_task_info)
        
        result = await agent._interpret_instruction("send email to test@example.com")
        
        assert result == mock_task_info
        agent.llm_service.interpret_instruction.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_provider_selection(self, agent):
        """Test provider selection logic."""
        # Test auto selection
        task_info = {"provider_preference": "auto"}
        provider = await agent._select_provider(task_info)
        assert provider == "gmail"
        
        # Test specific provider selection
        task_info = {"provider_preference": "gmail"}
        provider = await agent._select_provider(task_info)
        assert provider == "gmail"
    
    def test_error_result_creation(self, agent):
        """Test error result creation."""
        error_message = "Test error"
        result = agent._create_error_result(error_message)
        
        assert result["success"] is False
        assert result["error"] == error_message
        assert result["duration"] == 0
        assert "warnings" in result
    
    def test_supported_tasks(self, agent):
        """Test supported tasks list."""
        tasks = agent.get_supported_tasks()
        expected_tasks = ["email", "upload", "schedule", "ticket", "post"]
        assert tasks == expected_tasks
    
    def test_available_providers(self, agent):
        """Test available providers list."""
        providers = agent.get_available_providers()
        assert providers == ["gmail"]

class TestLLMService:
    """Test cases for the LLMService class."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        config = Mock(spec=Config)
        config.openai_api_key = "test_key"
        config.openai_model = "gpt-4"
        return config
    
    @pytest.fixture
    def llm_service(self, mock_config):
        """Create an LLM service instance for testing."""
        return LLMService(mock_config)
    
    @pytest.mark.asyncio
    async def test_instruction_interpretation(self, llm_service):
        """Test instruction interpretation."""
        # Mock the OpenAI client response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"task_type": "email", "action": "send", "recipients": ["test@example.com"], "subject": "Test", "content": "Test content"}'
        
        with patch.object(llm_service.client.chat.completions, 'create', return_value=mock_response):
            result = await llm_service.interpret_instruction("send email to test@example.com")
            
            assert result["task_type"] == "email"
            assert result["action"] == "send"
            assert "test@example.com" in result["recipients"]
    
    def test_task_info_validation(self, llm_service):
        """Test task info validation."""
        # Valid task info
        valid_task_info = {
            "task_type": "email",
            "recipients": ["test@example.com"],
            "content": "Test content"
        }
        result = llm_service._validate_task_info(valid_task_info)
        assert result is True
        
        # Invalid task info (missing recipients)
        invalid_task_info = {
            "task_type": "email",
            "content": "Test content"
        }
        result = llm_service._validate_task_info(invalid_task_info)
        assert result is False
    
    def test_recipient_formatting(self, llm_service):
        """Test recipient formatting."""
        # List of recipients
        recipients = ["test1@example.com", "test2@example.com"]
        formatted = llm_service._format_recipients(recipients)
        assert formatted == "test1@example.com, test2@example.com"
        
        # Single string
        recipients = "test@example.com"
        formatted = llm_service._format_recipients(recipients)
        assert formatted == "test@example.com"

if __name__ == "__main__":
    pytest.main([__file__])
