#!/bin/bash

# Telegram Bot Runner Script
# This script starts the Telegram AutoGen Assistant Bot

echo "=========================================="
echo "  Telegram AutoGen Assistant Bot"
echo "  Powered by Microsoft AutoGen & GPT-4"
echo "=========================================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create a .env file with your credentials."
    exit 1
fi

# Check for required environment variables
source .env

if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ Error: TELEGRAM_BOT_TOKEN not set in .env"
    echo "Get your bot token from @BotFather on Telegram"
    exit 1
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not set in .env"
    echo "The bot will run but won't be able to generate responses."
    echo "Get your API key from https://platform.openai.com/api-keys"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "✓ Environment variables loaded"
echo "✓ Bot Token: ${TELEGRAM_BOT_TOKEN:0:10}..."

if [ ! -z "$TELEGRAM_CHAT_ID" ]; then
    echo "✓ Default Chat ID: $TELEGRAM_CHAT_ID"
fi

echo ""
echo "Starting bot..."
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

# Run the bot using uv
uv run python telegram_bot_main.py