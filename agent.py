#!/usr/bin/env python3
"""
Cross-Platform Action Agent CLI
Main entry point for the automation system
"""

import os
import sys
import asyncio
from typing import Optional
from dotenv import load_dotenv
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.core.agent import GenericUIAgent
from src.core.config import Config
from src.utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Initialize CLI app
app = typer.Typer(
    name="action-agent",
    help="Cross-platform action agent for web automation",
    add_completion=False
)

console = Console()
logger = setup_logger()

@app.command()
def main(
    instruction: str = typer.Argument(..., help="Natural language instruction to execute"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Email provider (gmail/outlook)"),
    headless: bool = typer.Option(True, "--headless/--no-headless", help="Run browser in headless mode"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
    timeout: int = typer.Option(30, "--timeout", "-t", help="Timeout in seconds for operations"),
    retries: int = typer.Option(3, "--retries", "-r", help="Number of retry attempts")
):
    """
    Execute a natural language instruction across web services.
    
    Examples:
        action-agent "send email to alice@example.com saying 'Hello from automation'"
        action-agent "send email to team@company.com with subject 'Update' saying 'Project complete'" --provider gmail
        action-agent "send email to joe@example.com saying 'Meeting at 2pm'" --provider outlook --no-headless
    """
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    # Configure settings
    config = Config(
        headless=headless,
        timeout=timeout,
        retry_attempts=retries,
        verbose=verbose,
        default_provider=provider
    )
    
    # Display welcome message
    console.print(Panel.fit(
        "[bold blue]Cross-Platform Action Agent[/bold blue]\n"
        f"[dim]Instruction:[/dim] {instruction}\n"
        f"[dim]Provider:[/dim] {provider or 'auto-detect'}\n"
        f"[dim]Mode:[/dim] {'Headless' if headless else 'Visible'}",
        title="🤖 Agent Ready",
        border_style="blue"
    ))
    
    # Execute the instruction
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("Processing instruction...", total=None)
            
            # Run the agent
            result = asyncio.run(run_agent(instruction, config))
            
            progress.update(task, description="✅ Task completed successfully!")
        
        # Display results
        display_results(result)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error: {str(e)}[/red]")
        if verbose:
            logger.exception("Agent execution failed")
        sys.exit(1)

async def run_agent(instruction: str, config: Config):
    """Run the agent with the given instruction and configuration."""
    agent = GenericUIAgent(config)
    return await agent.execute(instruction)

def validate_environment() -> bool:
    """Validate that required environment variables are set."""
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        console.print(f"[red]Missing required environment variables: {', '.join(missing_vars)}[/red]")
        console.print("[yellow]Please create a .env file with the required variables.[/yellow]")
        return False
    
    return True

def display_results(result: dict):
    """Display the results of the agent execution."""
    console.print("\n" + "="*60)
    console.print("[bold green]✅ Task Completed Successfully![/bold green]")
    console.print("="*60)
    
    # Display execution summary
    console.print(f"[bold]Provider:[/bold] {result.get('provider', 'Unknown')}")
    console.print(f"[bold]Task:[/bold] {result.get('task_type', 'Unknown')}")
    console.print(f"[bold]Duration:[/bold] {result.get('duration', 0):.2f} seconds")
    
    # Display action log
    if result.get('actions'):
        console.print("\n[bold]Actions Performed:[/bold]")
        for i, action in enumerate(result['actions'], 1):
            status = "✅" if action.get('success', False) else "❌"
            console.print(f"  {i}. {status} {action.get('description', 'Unknown action')}")
    
    # Display any warnings or notes
    if result.get('warnings'):
        console.print("\n[yellow]Warnings:[/yellow]")
        for warning in result['warnings']:
            console.print(f"  ⚠️  {warning}")
    
    console.print("\n[dim]Agent execution completed.[/dim]")

@app.command()
def setup():
    """Interactive setup wizard for configuring the agent."""
    console.print(Panel.fit(
        "[bold blue]Cross-Platform Action Agent Setup[/bold blue]\n"
        "This wizard will help you configure the agent for first use.",
        title="🔧 Setup Wizard",
        border_style="blue"
    ))
    
    # Check if .env file exists
    if os.path.exists('.env'):
        console.print("[yellow]⚠️  .env file already exists. This will overwrite existing configuration.[/yellow]")
        if not typer.confirm("Continue?"):
            return
    
    # Collect configuration
    console.print("\n[bold]Step 1: OpenAI Configuration[/bold]")
    openai_key = typer.prompt("Enter your OpenAI API key", hide_input=True)
    
    console.print("\n[bold]Step 2: Email Provider Configuration[/bold]")
    use_gmail = typer.confirm("Configure Gmail?")
    gmail_email = gmail_password = None
    if use_gmail:
        gmail_email = typer.prompt("Gmail email address")
        gmail_password = typer.prompt("Gmail app password", hide_input=True)
    
    use_outlook = typer.confirm("Configure Outlook?")
    outlook_email = outlook_password = None
    if use_outlook:
        outlook_email = typer.prompt("Outlook email address")
        outlook_password = typer.prompt("Outlook password", hide_input=True)
    
    # Write .env file
    env_content = f"""# Cross-Platform Action Agent Configuration
OPENAI_API_KEY={openai_key}
"""
    
    if gmail_email and gmail_password:
        env_content += f"""
GMAIL_EMAIL={gmail_email}
GMAIL_PASSWORD={gmail_password}
"""
    
    if outlook_email and outlook_password:
        env_content += f"""
OUTLOOK_EMAIL={outlook_email}
OUTLOOK_PASSWORD={outlook_password}
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    console.print("\n[green]✅ Configuration saved to .env file[/green]")
    console.print("[dim]You can now run the agent with: python agent.py 'your instruction'[/dim]")

@app.command()
def test():
    """Run a test to verify the agent is working correctly."""
    console.print(Panel.fit(
        "[bold blue]Agent Test Suite[/bold blue]\n"
        "Running diagnostic tests to verify agent functionality.",
        title="🧪 Test Suite",
        border_style="blue"
    ))
    
    # Test environment
    console.print("\n[bold]1. Environment Test[/bold]")
    if validate_environment():
        console.print("✅ Environment variables configured")
    else:
        console.print("❌ Environment validation failed")
        return
    
    # Test imports
    console.print("\n[bold]2. Import Test[/bold]")
    try:
        from src.core.agent import GenericUIAgent
        from src.core.config import Config
        console.print("✅ All modules imported successfully")
    except ImportError as e:
        console.print(f"❌ Import error: {e}")
        return
    
    # Test configuration
    console.print("\n[bold]3. Configuration Test[/bold]")
    try:
        config = Config()
        console.print("✅ Configuration loaded successfully")
    except Exception as e:
        console.print(f"❌ Configuration error: {e}")
        return
    
    console.print("\n[green]✅ All tests passed! Agent is ready to use.[/green]")

if __name__ == "__main__":
    app()
