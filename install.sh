#!/bin/bash

# Exit on any error
set -e

# Print commands
set -x

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Install package in development mode
echo "Installing package in development mode..."
pip install -e .

# Create sample .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating sample .env file..."
    cp env.example .env
    echo "Please update the .env file with your API keys and configuration."
fi

# Create data directory if it doesn't exist
if [ ! -d "data" ]; then
    echo "Creating data directory..."
    mkdir -p data
fi

echo "Installation complete. Before running the bot, make sure to:"
echo "1. Update the .env file with your Slack and OpenAI API keys"
echo "2. Make sure your Slack bot has the necessary permissions"
echo ""
echo "To run the bot: source venv/bin/activate && python src/app.py" 