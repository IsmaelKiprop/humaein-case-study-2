#!/usr/bin/env python3
"""
Demo script for the Cross-Platform Action Agent
Showcases the agent's capabilities with example usage
"""

import asyncio
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.core.agent import GenericUIAgent
from src.core.config import Config

# Load environment variables
load_dotenv()

console = Console()

def print_banner():
    """Print the demo banner."""
    banner = """
    🤖 Cross-Platform Action Agent Demo
    
    This demo showcases the agent's ability to:
    • Interpret natural language instructions
    • Automate tasks across different web services
    • Handle Gmail and Outlook email sending
    • Provide detailed logging and error recovery
    """
    
    console.print(Panel(banner, title="🚀 Demo Mode", border_style="blue"))

def print_capabilities():
    """Print the agent's capabilities."""
    capabilities = Table(title="Agent Capabilities")
    capabilities.add_column("Feature", style="cyan")
    capabilities.add_column("Description", style="white")
    
    capabilities.add_row("Natural Language Processing", "Understands human-like instructions")
    capabilities.add_row("Multi-Provider Support", "Works with Gmail and Outlook")
    capabilities.add_row("LLM-Powered Reasoning", "Uses AI for instruction interpretation")
    capabilities.add_row("Browser Automation", "Reliable cross-browser automation")
    capabilities.add_row("Dynamic DOM Parsing", "Automatically identifies UI elements")
    capabilities.add_row("Error Recovery", "Handles failures and retries")
    capabilities.add_row("Comprehensive Logging", "Detailed step-by-step execution logs")
    
    console.print(capabilities)

def print_example_instructions():
    """Print example instructions."""
    examples = Table(title="Example Instructions")
    examples.add_column("Instruction", style="cyan")
    examples.add_column("Description", style="white")
    
    examples.add_row(
        "send email to alice@example.com saying 'Hello from automation'",
        "Simple email with auto-generated subject"
    )
    examples.add_row(
        "send email to team@company.com with subject 'Project Update' saying 'The project is complete'",
        "Email with custom subject"
    )
    examples.add_row(
        "send email to joe@example.com and jane@example.com saying 'Meeting at 2pm'",
        "Email to multiple recipients"
    )
    examples.add_row(
        "send email to manager@company.com with subject 'Weekly Report' saying 'Please find attached the weekly report'",
        "Professional email with specific subject"
    )
    
    console.print(examples)

async def run_demo_instruction(agent: GenericUIAgent, instruction: str, description: str):
    """Run a demo instruction and display results."""
    console.print(f"\n[bold cyan]Demo: {description}[/bold cyan]")
    console.print(f"[dim]Instruction: {instruction}[/dim]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("Executing instruction...", total=None)
        
        # Execute the instruction
        result = await agent.execute(instruction)
        
        progress.update(task, description="✅ Demo completed!")
    
    # Display results
    if result.get("success"):
        console.print(f"[green]✅ Success![/green] Task completed in {result.get('duration', 0):.2f} seconds")
        console.print(f"[dim]Provider used: {result.get('provider', 'Unknown')}[/dim]")
    else:
        console.print(f"[red]❌ Failed: {result.get('error', 'Unknown error')}[/red]")
    
    # Show action log
    if result.get("actions"):
        console.print("\n[bold]Actions performed:[/bold]")
        for i, action in enumerate(result["actions"][-5:], 1):  # Show last 5 actions
            status = "✅" if action.get("success", False) else "❌"
            console.print(f"  {i}. {status} {action.get('description', 'Unknown action')}")

async def interactive_demo():
    """Run an interactive demo."""
    console.print("\n[bold yellow]Interactive Demo Mode[/bold yellow]")
    console.print("Enter your own instructions to test the agent!")
    console.print("Type 'quit' to exit the demo.\n")
    
    # Initialize agent
    config = Config()
    agent = GenericUIAgent(config)
    
    while True:
        try:
            instruction = console.input("[bold cyan]Enter instruction: [/bold cyan]")
            
            if instruction.lower() in ['quit', 'exit', 'q']:
                console.print("[yellow]Exiting demo...[/yellow]")
                break
            
            if not instruction.strip():
                continue
            
            await run_demo_instruction(agent, instruction, "Custom instruction")
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Demo interrupted by user[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")

async def automated_demo():
    """Run an automated demo with predefined examples."""
    console.print("\n[bold yellow]Automated Demo Mode[/bold yellow]")
    console.print("Running predefined examples to showcase the agent...\n")
    
    # Initialize agent
    config = Config()
    agent = GenericUIAgent(config)
    
    # Demo instructions
    demo_instructions = [
        {
            "instruction": "send email to demo@example.com saying 'This is a test email from the automation agent'",
            "description": "Basic email sending"
        },
        {
            "instruction": "send email to test@example.com with subject 'Demo Test' saying 'Testing the automation system'",
            "description": "Email with custom subject"
        }
    ]
    
    for demo in demo_instructions:
        await run_demo_instruction(agent, demo["instruction"], demo["description"])
        await asyncio.sleep(2)  # Brief pause between demos

def check_environment():
    """Check if the environment is properly configured."""
    console.print("[bold]Environment Check[/bold]")
    
    # Check OpenAI API key
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        console.print("✅ OpenAI API key configured")
    else:
        console.print("❌ OpenAI API key not found")
        console.print("[yellow]Please set OPENAI_API_KEY in your .env file[/yellow]")
        return False
    
    # Check email providers
    gmail_email = os.getenv("GMAIL_EMAIL")
    gmail_password = os.getenv("GMAIL_PASSWORD")
    outlook_email = os.getenv("OUTLOOK_EMAIL")
    outlook_password = os.getenv("OUTLOOK_PASSWORD")
    
    if gmail_email and gmail_password:
        console.print("✅ Gmail credentials configured")
    else:
        console.print("⚠️  Gmail credentials not configured")
    
    if outlook_email and outlook_password:
        console.print("✅ Outlook credentials configured")
    else:
        console.print("⚠️  Outlook credentials not configured")
    
    if not any([gmail_email and gmail_password, outlook_email and outlook_password]):
        console.print("[yellow]Warning: No email providers configured. Demo will show interpretation only.[/yellow]")
    
    return True

async def main():
    """Main demo function."""
    print_banner()
    
    # Check environment
    if not check_environment():
        console.print("\n[red]Environment not properly configured. Please set up your .env file.[/red]")
        return
    
    print_capabilities()
    print_example_instructions()
    
    # Ask user for demo mode
    console.print("\n[bold]Choose demo mode:[/bold]")
    console.print("1. Automated demo (predefined examples)")
    console.print("2. Interactive demo (enter your own instructions)")
    
    choice = console.input("\n[bold cyan]Enter choice (1 or 2): [/bold cyan]")
    
    if choice == "1":
        await automated_demo()
    elif choice == "2":
        await interactive_demo()
    else:
        console.print("[yellow]Invalid choice. Running automated demo...[/yellow]")
        await automated_demo()
    
    console.print("\n[green]Demo completed![/green]")
    console.print("[dim]For more information, see the README.md file.[/dim]")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Demo failed: {str(e)}[/red]")
