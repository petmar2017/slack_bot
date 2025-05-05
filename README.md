# Atlas Support Bot for Slack

A comprehensive Slack bot designed to facilitate technical support requests, provide intelligent AI-powered initial responses, and efficiently route urgent issues to the most appropriate team members based on expertise and user priority levels.

![Atlas Support Bot](https://example.com/bot-screenshot.png) *(Replace with your bot's screenshot)*

## Table of Contents
- [Overview](#overview)
- [Core Features](#core-features)
- [Architecture](#architecture)
- [Code Structure](#code-structure)
- [Setup and Installation](#setup-and-installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Development](#development)
- [Security Considerations](#security-considerations)
- [License](#license)

## Overview

Atlas Support Bot acts as an intelligent first responder for technical support requests in Slack. It leverages an LLM (Large Language Model) to analyze incoming requests, determine urgency, extract relevant information, and provide appropriate initial responses. For urgent or complex issues, the bot employs a "hunt" mechanism to find and notify the most suitable Subject Matter Experts (SMEs) based on their expertise and availability, taking into account the user's priority level (VIP, standard, or regular).

## Core Features

### 1. LLM-Based Initial Response
- **Intelligent Request Analysis**: Classifies requests into categories (technical issues, general questions, urgent issues, etc.)
- **Information Extraction**: Identifies key information like system, topic, error details
- **Appropriate Response Generation**: Provides initial support, instructions, or escalation notifications
- **Urgency Assessment**: Calculates an urgency score to prioritize critical issues

### 2. SME Hunt Functionality
- **Expertise Matching**: Finds team members with relevant expertise
- **User Priority Consideration**: Prioritizes VIP users' requests
- **Availability Tracking**: Considers current load and availability of SMEs
- **Timeout Handling**: Manages unresponded requests appropriately
- **Acknowledgment System**: Tracks which SME accepted responsibility

### 3. User Priority System
- **Tiered Support Levels**: Differentiates between VIP, standard, and regular users
- **Priority-Based Routing**: Ensures VIP users receive faster responses
- **Custom Handling Rules**: Applies different response strategies based on user level

### 4. Slack Integration
- **Responds to Direct Messages**: Processes support requests sent as DMs
- **Responds to Mentions**: Handles mentions in channels
- **Thread-Based Responses**: Keeps conversations organized in threads
- **Slash Commands**: Enables `/claim` command for SMEs to pick up tickets

## Architecture

The bot follows a modular, service-oriented architecture with clean separation of concerns:

```
┌─────────────────┐      ┌───────────────┐      ┌──────────────────┐
│                 │      │               │      │                  │
│  Slack Events   │─────▶│  Application  │─────▶│  LLM Service     │
│  & Commands     │      │  Controller   │      │                  │
│                 │      │               │      └──────────────────┘
└─────────────────┘      │               │
                         │               │      ┌──────────────────┐
                         │               │─────▶│  Hunt Service    │
┌─────────────────┐      │               │      │                  │
│                 │      │               │      └──────────────────┘
│  Data Stores    │◀────▶│               │
│  (JSON Files)   │      │               │      ┌──────────────────┐
│                 │      │               │─────▶│  Storage Service │
└─────────────────┘      └───────────────┘      │                  │
                                                └──────────────────┘
```

The application:
1. Receives events from Slack (messages, mentions, commands)
2. Processes them through the appropriate service
3. Stores/retrieves data as needed
4. Returns appropriate responses to users

## Code Structure

### Models
- **`src/models/user.py`**: User and UserLevel models 
- **`src/models/sme.py`**: Subject Matter Expert model and database
- **`src/models/ticket.py`**: Support ticket model with status tracking

### Services
- **`src/services/llm_service.py`**: Handles LLM interaction for query analysis and response generation
- **`src/services/hunt_service.py`**: Manages finding and notifying appropriate SMEs

### Config and Utils
- **`src/config/settings.py`**: Configuration management using environment variables
- **`src/utils/storage.py`**: Data persistence utilities for SMEs and user levels

### Main Application
- **`src/app.py`**: Main application with Slack event handlers and business logic

## Setup and Installation

### Prerequisites
- Python 3.8+
- Slack workspace with admin rights
- OpenAI API key or access to another LLM provider

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/atlas-support-bot.git
   cd atlas-support-bot
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Use the installation script (recommended):
   ```bash
   chmod +x install.sh
   ./install.sh
   ```
   
   Or manually install:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

4. Set up your Slack App (see `SLACK_SETUP.md` for detailed instructions)

5. Configure your environment variables (copy `env.example` to `.env` and edit)

6. Start the bot:
   ```bash
   python src/app.py
   ```

## Configuration

The bot is configured using environment variables, which can be set in a `.env` file:

```
# Slack API Credentials
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_APP_TOKEN=xapp-your-app-token

# OpenAI API Credentials
OPENAI_API_KEY=your-openai-api-key

# Bot Configuration
LOG_LEVEL=INFO
BOT_NAME=Atlas Support
DEFAULT_RESPONSE_CHANNEL=support-requests
HUNT_TIMEOUT_MINUTES=30
SME_DATABASE_PATH=data/sme_database.json
USER_LEVELS_PATH=data/user_levels.json
```

### SME Database

The SME database is stored in a JSON file (`data/sme_database.json`) with the following structure:

```json
{
  "experts": [
    {
      "slack_id": "U01ABCDEFG",
      "name": "Alex Johnson",
      "expertise": ["network security", "vpn", "firewall"],
      "availability": true,
      "skills_rating": {
        "network security": 5,
        "vpn": 4,
        "firewall": 5
      },
      "current_load": 1,
      "max_concurrent_issues": 3
    },
    ...
  ]
}
```

### User Levels Database

User priority levels are stored in a JSON file (`data/user_levels.json`):

```json
{
  "U101ABCDE": {
    "level": "vip",
    "tags": ["executive", "leadership"],
    "notes": "CEO, respond with highest priority"
  },
  ...
}
```

## Usage

### For Users

#### Getting Support
- **Direct Message**: Send a DM to the bot describing your issue
- **Channel Mention**: Mention the bot in a channel using `@Atlas Support [your issue]`

#### Example Interactions
```
User: @Atlas Support I can't access the database server
Bot: I'm analyzing your request...
Bot: I understand you're having trouble accessing the database server. 
     Could you provide more details such as:
     1. Which database server are you trying to access?
     2. What error message are you seeing?
     3. When did this issue start?
     
     This will help me better assist you.
```

For urgent issues or when the bot determines human help is needed:
```
User: @Atlas Support URGENT: The main production database is down and customers can't log in!
Bot: I'm analyzing your request...
Bot: I understand this is an urgent issue with the production database affecting customer logins. 
     I've notified our support team and a database specialist will assist you shortly.
```

### For Support Team Members (SMEs)

Support team members can claim tickets using the `/claim` command:

```
/claim ticket-abc123
```

When a ticket is claimed, the user will be notified that a specific team member is now handling their request.

## Development

### Adding New Features

To add new features to the bot:

1. **New Query Type**: Add to `QueryType` enum in `src/services/llm_service.py`
2. **New Response Type**: Add to `ResponseType` enum in `src/services/llm_service.py`
3. **New Ticket Status**: Add to `TicketStatus` enum in `src/models/ticket.py`

### Testing

Run tests with pytest:
```bash
pytest
```

### OpenAI API Considerations

The bot uses OpenAI's API for analyzing requests and generating responses. Be mindful of:
- API costs (adjust model usage as needed)
- Rate limits
- API key security

## Security Considerations

- **API Keys**: Never commit API keys to version control
- **User Data**: Be mindful of data retention policies
- **Permissions**: Use the principle of least privilege for Slack bot permissions

## License

This project is licensed under the MIT License - see the LICENSE file for details.