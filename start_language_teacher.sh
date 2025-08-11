#!/bin/bash

# Language Teacher Telegram Bot Startup Script
# This script starts the AI Language Teacher Bot with proper environment setup

echo "🎓 Starting AI Language Teacher Bot 🎓"
echo "==============================================="

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "Please create a .env file with:"
    echo "TELEGRAM_BOT_TOKEN=your_bot_token_here"
    echo "OPENAI_API_KEY=your_openai_api_key_here"
    echo "ANTHROPIC_API_KEY=your_anthropic_api_key_here"
    echo ""
fi

# Check for required environment variables
echo "🔍 Checking environment setup..."

# Load environment variables if .env exists
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check Telegram Bot Token
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN is not set"
    echo "Please set your Telegram bot token in the .env file"
    exit 1
else
    echo "✅ Telegram bot token configured"
fi

# Check API Keys
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY is not set. GPT-4 features may not work."
else
    echo "✅ OpenAI API key configured"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p language_learners_data
mkdir -p temp_audio_files

# Check Python environment
echo "🐍 Checking Python environment..."

# Check if uv is available
if command -v uv &> /dev/null; then
    echo "✅ uv package manager found"
    
    # Install/sync dependencies
    echo "📦 Installing dependencies..."
    uv sync
    
    # Start the bot using uv
    echo ""
    echo "🚀 Starting Language Teacher Bot..."
    echo "Press Ctrl+C to stop the bot"
    echo ""
    
    uv run python language_teacher_bot.py
    
elif command -v python3 &> /dev/null; then
    echo "✅ Python 3 found, using direct execution"
    
    # Check if virtual environment exists
    if [ -d "venv" ]; then
        echo "📦 Activating virtual environment..."
        source venv/bin/activate
    fi
    
    # Install requirements if requirements.txt exists
    if [ -f "requirements.txt" ]; then
        echo "📦 Installing requirements..."
        pip install -r requirements.txt
    fi
    
    # Start the bot
    echo ""
    echo "🚀 Starting Language Teacher Bot..."
    echo "Press Ctrl+C to stop the bot"
    echo ""
    
    python3 language_teacher_bot.py
    
else
    echo "❌ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

echo ""
echo "👋 Language Teacher Bot has been stopped."
echo "Thank you for using the AI Language Teacher!"