#!/usr/bin/env python3
"""
Setup script for the Cross-Platform Action Agent
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_banner():
    """Print setup banner."""
    print("=" * 60)
    print("🤖 Cross-Platform Action Agent Setup")
    print("=" * 60)
    print()

def check_python_version():
    """Check if Python version is compatible."""
    print("Checking Python version...")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version.split()[0]} is compatible")
    return True

def install_dependencies():
    """Install required dependencies."""
    print("\nInstalling dependencies...")
    
    try:
        # Install Python packages
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Python dependencies installed successfully")
        
        # Install Playwright browsers
        print("Installing Playwright browsers...")
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("✅ Playwright browsers installed successfully")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_directories():
    """Create necessary directories."""
    print("\nCreating directories...")
    
    directories = ["logs", "screenshots"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def setup_environment():
    """Set up environment configuration."""
    print("\nSetting up environment...")
    
    env_file = Path(".env")
    example_file = Path("env.example")
    
    if env_file.exists():
        print("⚠️  .env file already exists")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("Skipping environment setup")
            return True
    
    if not example_file.exists():
        print("❌ env.example file not found")
        return False
    
    # Copy example file
    with open(example_file, 'r') as f:
        content = f.read()
    
    with open(env_file, 'w') as f:
        f.write(content)
    
    print("✅ Created .env file from template")
    print("⚠️  Please edit .env file with your actual credentials")
    return True

def check_system_requirements():
    """Check system requirements."""
    print("\nChecking system requirements...")
    
    # Check OS
    system = platform.system()
    print(f"✅ Operating system: {system}")
    
    # Check available memory (rough estimate)
    try:
        import psutil
        memory_gb = psutil.virtual_memory().total / (1024**3)
        print(f"✅ Available memory: {memory_gb:.1f} GB")
        
        if memory_gb < 2:
            print("⚠️  Warning: Less than 2GB RAM available")
    except ImportError:
        print("⚠️  Could not check memory (psutil not installed)")
    
    return True

def run_tests():
    """Run basic tests to verify installation."""
    print("\nRunning basic tests...")
    
    try:
        # Test imports
        import src.core.config
        import src.core.agent
        import src.services.llm_service
        import src.automation.browser_manager
        print("✅ All modules imported successfully")
        
        # Test configuration
        config = src.core.config.Config()
        print("✅ Configuration loaded successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def print_next_steps():
    """Print next steps for the user."""
    print("\n" + "=" * 60)
    print("🎉 Setup completed successfully!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Edit the .env file with your credentials:")
    print("   - Set your OpenAI API key")
    print("   - Configure Gmail and/or Outlook credentials")
    print()
    print("2. Test the installation:")
    print("   python agent.py test")
    print()
    print("3. Run the demo:")
    print("   python demo.py")
    print()
    print("4. Use the agent:")
    print("   python agent.py 'send email to test@example.com saying Hello'")
    print()
    print("For more information, see README.md")

def main():
    """Main setup function."""
    print_banner()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check system requirements
    if not check_system_requirements():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed during dependency installation")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Setup environment
    if not setup_environment():
        print("\n❌ Setup failed during environment setup")
        sys.exit(1)
    
    # Run tests
    if not run_tests():
        print("\n⚠️  Setup completed with warnings")
        print("Some tests failed, but the installation may still work")
    else:
        print("\n✅ All tests passed")
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nSetup failed with error: {e}")
        sys.exit(1)
