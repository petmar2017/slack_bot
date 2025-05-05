# Setting Up Your Slack Bot

This guide will walk you through the process of creating a Slack app and bot, obtaining necessary credentials, and configuring permissions for your Atlas Support Bot.

## 1. Create a Slack App

1. Go to the [Slack API website](https://api.slack.com/apps)
2. Click "Create New App"
3. Choose "From scratch"
4. Enter a name for your app (e.g., "Atlas Support Bot")
5. Select the workspace where you want to use the bot
6. Click "Create App"

## 2. Configure Bot Features

### Basic Information
1. Under "Display Information", add:
   - App icon (optional)
   - Short description: "A support bot that uses AI to triage requests and route them to SMEs"
   - Background color (optional)

### Bot User
1. Navigate to "App Home" in the sidebar
2. Under "App Display Name", set the name to "Atlas Support"
3. Turn on "Always Show My Bot as Online"

### Event Subscriptions
1. Navigate to "Event Subscriptions" in the sidebar
2. Turn on "Enable Events"
3. In the "Subscribe to bot events" section, add the following bot events:
   - `app_mention`
   - `message.im`
4. Click "Save Changes"

### OAuth & Permissions
1. Navigate to "OAuth & Permissions" in the sidebar
2. Under "Scopes", add the following Bot Token Scopes:
   - `app_mentions:read`
   - `channels:history`
   - `channels:read`
   - `chat:write`
   - `commands`
   - `im:history`
   - `im:read`
   - `im:write`
   - `users:read`
   - `users:read.email`

### Slash Commands
1. Navigate to "Slash Commands" in the sidebar
2. Click "Create New Command"
3. Fill in the details:
   - Command: `/claim`
   - Description: "Claim a support ticket as an SME"
   - Usage hint: `ticket-id`
4. Click "Save"

### App Home
1. Navigate to "App Home" in the sidebar
2. Under "Show Tabs", enable "Home Tab" and "Messages Tab"
3. Check "Allow users to send Slash commands and messages from the messages tab"

## 3. Install App to Workspace

1. Navigate to "Install App" in the sidebar
2. Click "Install to Workspace"
3. Review permissions and click "Allow"

## 4. Collect Credentials

You'll need three key credentials to configure your bot:

1. **Bot User OAuth Token**:
   - Go to "OAuth & Permissions"
   - Copy the "Bot User OAuth Token" (starts with `xoxb-`)

2. **Signing Secret**:
   - Go to "Basic Information"
   - Under "App Credentials", copy the "Signing Secret"

3. **App-Level Token**:
   - Go to "Basic Information"
   - Under "App-Level Tokens", click "Generate Token"
   - Name: "socket-token"
   - Scopes: `connections:write`
   - Click "Generate"
   - Copy the generated token (starts with `xapp-`)

## 5. Configure Your Environment

Add these credentials to your `.env` file:

```
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_APP_TOKEN=xapp-your-app-token
```

## 6. Testing Your Bot

1. Invite your bot to a channel by typing `/invite @Atlas Support`
2. Mention your bot with `@Atlas Support hello`
3. Send a direct message to your bot

The bot should respond according to the implementation.

## Troubleshooting

- If your bot doesn't respond to mentions, make sure:
  - The bot is invited to the channel
  - Event subscriptions are properly configured
  - Your bot is running with valid credentials
  - Your bot has the necessary permissions

- If slash commands don't work, ensure:
  - You've correctly configured the command in the Slack API dashboard
  - Your bot has the `commands` scope
  - Your bot is running with valid credentials

- If you get authentication errors, double-check:
  - Your environment variables contain the correct values
  - You copied the tokens exactly without any extra spaces
  - You're using the correct token types in the right places 