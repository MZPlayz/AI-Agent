# AI Agent System

A comprehensive AI Agent system that integrates with Telegram and manages various specialized agents for different tasks.

## Features

- Telegram integration for user communication
- Multiple specialized agents for different tasks
- Uses Google's Gemini model for LLM capabilities
- Modular architecture for easy extension

## Agents

1. Personal Assistant Agent
2. Research Agent
3. Customer Support Agent
4. Data Analysis Agent
5. Content Generation Agent
6. Project Management Agent
7. Sales Agent
8. HR Agent
9. Code Assistant Agent
10. DevOps Agent
11. Security Agent
12. Social Media Influencer Agent

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your credentials:
```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GOOGLE_API_KEY=your_google_api_key
```

3. Run the main application:
```bash
python main.py
```

## Project Structure

```
├── agents/           # Individual agent implementations
├── core/            # Core system components
├── utils/           # Utility functions
├── config/          # Configuration files
└── main.py          # Main application entry point
``` 
