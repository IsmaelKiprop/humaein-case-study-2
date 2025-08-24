"""
Logging utilities for the Cross-Platform Action Agent
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from rich.logging import RichHandler
from rich.console import Console
from rich.theme import Theme

# Create logs directory
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Custom theme for rich logging
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red",
    "success": "green",
    "debug": "dim"
})

console = Console(theme=custom_theme)

def setup_logger(
    name: str = "action_agent",
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up a logger with rich formatting and file output.
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Optional log file path
    
    Returns:
        Configured logger instance
    """
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatters
    console_formatter = logging.Formatter(
        "%(message)s",
        datefmt="[%X]"
    )
    
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler with rich formatting
    console_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        markup=True,
        rich_tracebacks=True
    )
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"agent_{timestamp}.log"
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str = "action_agent") -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)

class ActionLogger:
    """Specialized logger for action execution tracking."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.actions = []
    
    def log_action(self, action: str, success: bool = True, details: Optional[str] = None):
        """Log an action with success/failure status."""
        status = "✅" if success else "❌"
        message = f"{status} {action}"
        
        if details:
            message += f" - {details}"
        
        self.logger.info(message)
        
        # Store action for reporting
        self.actions.append({
            "action": action,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def log_step(self, step: str, description: Optional[str] = None):
        """Log a step in the process."""
        message = f"🔹 {step}"
        if description:
            message += f": {description}"
        
        self.logger.info(message)
    
    def log_warning(self, message: str):
        """Log a warning."""
        self.logger.warning(f"⚠️  {message}")
    
    def log_error(self, message: str, exception: Optional[Exception] = None):
        """Log an error."""
        error_msg = f"❌ {message}"
        if exception:
            error_msg += f" - {str(exception)}"
        
        self.logger.error(error_msg, exc_info=exception is not None)
    
    def log_success(self, message: str):
        """Log a success message."""
        self.logger.info(f"✅ {message}")
    
    def get_actions(self) -> list:
        """Get all logged actions."""
        return self.actions.copy()
    
    def clear_actions(self):
        """Clear the action log."""
        self.actions.clear()
