# Cross-Platform Action Agent

A sophisticated automation system that can perform generic user tasks across multiple web services with different UI layouts. This agent uses LLM reasoning and browser automation to execute tasks like sending emails across Gmail and Outlook.

## Features

- **Natural Language Processing**: Accepts human-like instructions and converts them to actionable steps
- **Multi-Provider Support**: Works with Gmail and Outlook (easily extensible to other services)
- **LLM-Powered Reasoning**: Uses AI to interpret instructions and identify UI elements
- **Browser Automation**: Reliable cross-browser automation using Playwright
- **Dynamic DOM Parsing**: Automatically identifies form fields and buttons
- **Error Recovery**: Handles minor DOM changes and edge cases
- **Comprehensive Logging**: Detailed step-by-step execution logs
- **CLI Interface**: Easy command-line usage

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

2. **Set up environment variables** (create `.env` file):
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   GMAIL_EMAIL=your_email@gmail.com
   GMAIL_PASSWORD=your_app_password
   OUTLOOK_EMAIL=your_email@outlook.com
   OUTLOOK_PASSWORD=your_password
   ```

3. **Run the agent**:
   ```bash
   python agent.py "send email to alice@example.com saying 'Hello from my automation system'"
   ```

## Usage Examples

```bash
# Send a simple email
python agent.py "send email to joe@example.com saying 'Hello from my automation system'"

# Send email with subject
python agent.py "send email to alice@example.com with subject 'Meeting Tomorrow' saying 'Let's meet at 2pm'"

# Send to multiple recipients
python agent.py "send email to team@company.com and manager@company.com saying 'Project update attached'"
```

## Architecture

### Core Components

1. **GenericUIAgent**: Main agent class that orchestrates the automation
2. **ProviderAdapter**: Abstract interface for different email services
3. **GmailAdapter**: Gmail-specific implementation
4. **OutlookAdapter**: Outlook-specific implementation
5. **LLMService**: Handles AI reasoning and instruction interpretation
6. **DOMParser**: Parses and identifies UI elements dynamically
7. **BrowserManager**: Manages browser automation sessions

### Key Design Principles

- **Abstraction**: Provider-specific logic is abstracted behind unified interfaces
- **Modularity**: Each component has a single responsibility
- **Extensibility**: Easy to add new providers or tasks
- **Reliability**: Robust error handling and recovery mechanisms
- **Observability**: Comprehensive logging and debugging capabilities

## Supported Tasks

Currently supports:
- **Email Sending**: Send emails via Gmail and Outlook

Easily extensible to:
- Document uploads (Google Drive, Dropbox)
- Calendar scheduling (Google Calendar, Outlook Calendar)
- Support ticket submission (Zendesk, Freshdesk)
- Forum posting (Reddit, Discourse)

## Configuration

The system can be configured through environment variables or a config file:

- `DEFAULT_PROVIDER`: Which email service to use by default
- `HEADLESS_MODE`: Run browser in headless mode (true/false)
- `TIMEOUT_SECONDS`: Maximum time to wait for elements
- `RETRY_ATTEMPTS`: Number of retry attempts for failed actions

## Error Handling

The agent includes sophisticated error handling:

- **Element Not Found**: Retries with different selectors
- **Authentication Issues**: Clear error messages and guidance
- **Network Problems**: Automatic retry with exponential backoff
- **DOM Changes**: Dynamic field identification and fallback strategies

## Development

### Adding a New Provider

1. Create a new adapter class inheriting from `ProviderAdapter`
2. Implement the required methods
3. Register the provider in the agent factory
4. Add configuration options

### Adding a New Task

1. Extend the `TaskParser` to handle new task types
2. Create task-specific action classes
3. Update the agent to route to appropriate handlers

## License

MIT License - see LICENSE file for details.