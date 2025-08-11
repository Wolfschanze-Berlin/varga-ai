---
sidebar_position: 2
title: Setup & Installation
---

# Language Teacher Bot Setup Guide

Complete guide to setting up your AI Language Teacher Telegram Bot in under 10 minutes.

## 📋 Prerequisites

### System Requirements
- **Python**: 3.12 or higher
- **Memory**: Minimum 2GB RAM (4GB recommended)
- **Storage**: 1GB free space
- **OS**: Linux, macOS, or Windows

### Required Accounts
- **Telegram Account**: To create and manage your bot
- **Bot Token**: From [@BotFather](https://t.me/botfather)
- **OpenAI API Key**: Optional, for advanced AI features

## 🚀 Quick Setup (5 minutes)

### Step 1: Get Your Bot Token

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Choose a name for your bot (e.g., "My Language Teacher")
4. Choose a username (must end in 'bot', e.g., `mylanguageteacher_bot`)
5. Copy the bot token provided

### Step 2: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/varga-ai.git
cd varga-ai

# Or download the ZIP file
wget https://github.com/yourusername/varga-ai/archive/main.zip
unzip main.zip
cd varga-ai-main
```

### Step 3: Configure Environment

```bash
# Copy the environment template
cp .env.template .env

# Edit the configuration file
nano .env  # or use your preferred editor
```

Add your credentials:
```env
# Required Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Optional AI Features
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Bot Settings
DEFAULT_LANGUAGE=english
SUPPORTED_LANGUAGES=english,spanish,french,german,italian,portuguese
ENABLE_VOICE_FEATURES=true
ENABLE_ACHIEVEMENTS=true
DATABASE_PATH=./database.sqlite
```

### Step 4: Install Dependencies

#### Using UV (Recommended)
```bash
# Install uv if not already installed
pip install uv

# Install project dependencies
uv sync
```

#### Using Pip
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 5: Launch the Bot

```bash
# Using the startup script
chmod +x start_language_teacher.sh
./start_language_teacher.sh

# Or run directly
python language_teacher_bot.py
```

## 🔧 Advanced Configuration

### Database Configuration

The bot uses SQLite by default, but you can configure PostgreSQL for production:

```env
# PostgreSQL Configuration (Optional)
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:password@localhost:5432/language_bot
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
```

### AI Model Configuration

Customize AI behavior and model selection:

```env
# AI Model Settings
AI_MODEL=gpt-4  # or gpt-3.5-turbo, claude-2
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=2000
AI_TIMEOUT=30

# Adaptive Learning Settings
ENABLE_ADAPTIVE_LEARNING=true
IRT_DISCRIMINATION=1.5
IRT_DIFFICULTY_MIN=-3
IRT_DIFFICULTY_MAX=3
```

### Voice Processing Configuration

```env
# Voice Settings
VOICE_PROCESSING_ENABLED=true
VOICE_API=whisper  # or google, azure
WHISPER_MODEL=base  # tiny, base, small, medium, large
MAX_VOICE_DURATION=60  # seconds
VOICE_LANGUAGE_DETECTION=true
```

### Performance Tuning

```env
# Performance Settings
MAX_CONCURRENT_USERS=100
RESPONSE_TIMEOUT=10
CACHE_ENABLED=true
CACHE_TTL=3600
RATE_LIMIT_PER_USER=60  # messages per minute
RATE_LIMIT_GLOBAL=1000  # messages per minute
```

## 🐳 Docker Deployment

### Using Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  language-bot:
    build: .
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=postgresql://postgres:password@db:5432/language_bot
    depends_on:
      - db
    restart: unless-stopped
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs

  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=language_bot
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Launch with Docker:
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f language-bot

# Stop the bot
docker-compose down
```

## ☁️ Cloud Deployment

### Deploy to AWS

```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Deploy using provided script
./scripts/deploy_aws.sh
```

### Deploy to Google Cloud

```bash
# Install gcloud CLI
# https://cloud.google.com/sdk/docs/install

# Initialize gcloud
gcloud init

# Deploy
./scripts/deploy_gcp.sh
```

### Deploy to Heroku

```bash
# Install Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# Create Heroku app
heroku create your-language-bot

# Set environment variables
heroku config:set TELEGRAM_BOT_TOKEN=your_token
heroku config:set OPENAI_API_KEY=your_key

# Deploy
git push heroku main
```

## 🔍 Verification & Testing

### Test Bot Connection

```python
# Run the test script
python test_language_teacher.py

# Expected output:
# ✅ Bot connected successfully
# ✅ Database initialized
# ✅ AI models loaded
# ✅ All systems operational
```

### Manual Testing

1. Open Telegram and find your bot
2. Send `/start` - Should show welcome message
3. Send `/help` - Should show available commands
4. Try a conversation - Should get AI response
5. Check `/status` - Should show bot statistics

## 🚨 Troubleshooting

### Common Issues

#### Bot Not Responding
```bash
# Check bot is running
ps aux | grep language_teacher

# Check logs
tail -f logs/language_teacher.log

# Verify token
python -c "import os; print(os.getenv('TELEGRAM_BOT_TOKEN'))"
```

#### Database Errors
```bash
# Reset database
rm database.sqlite
python language_teacher_bot.py --init-db

# Check permissions
chmod 644 database.sqlite
```

#### API Key Issues
```bash
# Test OpenAI connection
python -c "import openai; openai.api_key='your_key'; print(openai.Model.list())"

# Check rate limits
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Error Messages

| Error | Solution |
|-------|----------|
| `Unauthorized: Invalid token` | Check bot token in .env file |
| `Connection refused` | Ensure internet connectivity |
| `Rate limit exceeded` | Wait or upgrade API plan |
| `Database locked` | Restart bot, check permissions |
| `Module not found` | Run `uv sync` or `pip install -r requirements.txt` |

## 📊 Monitoring & Logs

### Log Files
```bash
# View real-time logs
tail -f logs/language_teacher.log

# Search for errors
grep ERROR logs/language_teacher.log

# Monitor performance
grep PERFORMANCE logs/language_teacher.log
```

### Health Checks
```bash
# Check bot status
curl http://localhost:8080/health

# Database status
python -c "from database_manager import check_health; check_health()"
```

## 🔐 Security Best Practices

1. **Never commit `.env` file** to version control
2. **Use environment variables** for all secrets
3. **Enable rate limiting** to prevent abuse
4. **Regular backups** of database
5. **Monitor logs** for suspicious activity
6. **Update dependencies** regularly

```bash
# Security audit
pip audit

# Update dependencies
uv sync --upgrade
```

## 📚 Next Steps

- [User Guide](./user-guide) - Learn how to use all features
- [Admin Dashboard](./admin) - Manage your bot
- [API Reference](./api) - Integrate with other systems
- [Customization](./customization) - Modify bot behavior

---

Need help? Check our [FAQ](./faq) or join our [Community Forum](https://community.varga-ai.com) →