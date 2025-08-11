---
sidebar_position: 2
title: Setup & Configuration
---

# Smart Assistant Bot Setup

Deploy your AutoGen-powered Telegram bot for intelligent business automation.

## 🔧 System Requirements

### Minimum Requirements
- **OS**: Linux, macOS, or Windows
- **Python**: 3.12 or higher
- **Memory**: 2GB RAM
- **Storage**: 500MB free space
- **Network**: Stable internet connection

### Recommended Specifications
- **Memory**: 4GB+ RAM
- **CPU**: 2+ cores
- **Storage**: 2GB+ for logs and cache
- **Network**: High-speed connection

## 🚀 Quick Start

### Step 1: Create Telegram Bot

1. Open [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` command
3. Choose bot name (e.g., "Smart Business Assistant")
4. Choose username (must end with 'bot')
5. Save the bot token

### Step 2: Get OpenAI API Key

1. Visit [OpenAI Platform](https://platform.openai.com)
2. Create account or sign in
3. Navigate to API Keys
4. Create new secret key
5. Save the API key

### Step 3: Clone Repository

```bash
# Clone via HTTPS
git clone https://github.com/yourusername/varga-ai.git
cd varga-ai

# Or clone via SSH
git clone git@github.com:yourusername/varga-ai.git
cd varga-ai
```

### Step 4: Environment Setup

```bash
# Copy environment template
cp .env.template .env

# Edit configuration
nano .env  # or vim, code, etc.
```

Configure essential variables:
```env
# Required
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key

# Optional
TELEGRAM_CHAT_ID=default_chat_id
BOT_NAME=SmartAssistant
LOG_LEVEL=INFO
```

### Step 5: Install Dependencies

#### Option A: Using UV (Recommended)
```bash
# Install uv
pip install uv

# Install dependencies
uv sync

# Activate environment
uv shell
```

#### Option B: Using Pip
```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 6: Launch Bot

```bash
# Run the bot
python telegram_bot_main.py

# Or with UV
uv run python telegram_bot_main.py
```

## ⚙️ Advanced Configuration

### AutoGen Configuration

Customize AutoGen agent behavior:

```python
# config/autogen_config.py
AUTOGEN_CONFIG = {
    "assistant_agent": {
        "name": "smart_assistant",
        "system_message": """You are a helpful business assistant...""",
        "llm_config": {
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 0.95,
            "frequency_penalty": 0,
            "presence_penalty": 0
        }
    },
    "research_agent": {
        "name": "researcher",
        "system_message": """You are a research specialist...""",
        "llm_config": {
            "model": "gpt-4",
            "temperature": 0.3
        }
    }
}
```

### Multi-Agent Setup

Configure multiple specialized agents:

```python
# agents/config.py
AGENT_REGISTRY = {
    "customer_service": {
        "class": "CustomerServiceAgent",
        "config": {
            "response_style": "friendly",
            "escalation_threshold": 0.3
        }
    },
    "sales_support": {
        "class": "SalesAgent",
        "config": {
            "product_catalog": "products.json",
            "pricing_rules": "pricing.yaml"
        }
    },
    "technical_support": {
        "class": "TechSupportAgent",
        "config": {
            "knowledge_base": "kb/",
            "ticket_system": "jira"
        }
    }
}
```

### Database Configuration

#### SQLite (Default)
```env
DATABASE_TYPE=sqlite
DATABASE_PATH=./data/bot.db
```

#### PostgreSQL
```env
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:pass@localhost:5432/bot_db
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

#### MongoDB
```env
DATABASE_TYPE=mongodb
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=smart_bot
```

### Redis Cache Configuration

```env
# Redis for caching and session management
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
REDIS_DB=0
CACHE_TTL=3600
```

### Rate Limiting

```env
# Rate limiting configuration
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_USER=60  # messages per minute
RATE_LIMIT_PER_CHAT=100  # messages per minute
RATE_LIMIT_GLOBAL=1000  # total messages per minute
RATE_LIMIT_BURST=10  # burst allowance
```

## 🐳 Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run bot
CMD ["python", "telegram_bot_main.py"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  bot:
    build: .
    container_name: smart_assistant_bot
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - REDIS_HOST=redis
      - DATABASE_URL=postgresql://postgres:password@db:5432/bot
    depends_on:
      - redis
      - db
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data

  redis:
    image: redis:7-alpine
    container_name: bot_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  db:
    image: postgres:14
    container_name: bot_postgres
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=bot
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  redis_data:
  postgres_data:
```

Launch with Docker:
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f bot

# Stop services
docker-compose down
```

## ☁️ Cloud Deployment

### AWS Deployment

#### Using EC2
```bash
# Launch EC2 instance (Amazon Linux 2)
aws ec2 run-instances \
  --image-id ami-0123456789 \
  --instance-type t3.medium \
  --key-name your-key \
  --security-groups bot-sg

# SSH to instance
ssh -i your-key.pem ec2-user@instance-ip

# Setup bot
git clone <repository>
cd varga-ai
./scripts/setup_aws.sh
```

#### Using ECS
```yaml
# task-definition.json
{
  "family": "smart-assistant-bot",
  "taskRoleArn": "arn:aws:iam::123456:role/ecsTaskRole",
  "executionRoleArn": "arn:aws:iam::123456:role/ecsExecutionRole",
  "networkMode": "awsvpc",
  "containerDefinitions": [
    {
      "name": "bot",
      "image": "your-ecr-repo/smart-bot:latest",
      "memory": 2048,
      "cpu": 1024,
      "environment": [
        {"name": "TELEGRAM_BOT_TOKEN", "value": "from-secrets"},
        {"name": "OPENAI_API_KEY", "value": "from-secrets"}
      ]
    }
  ]
}
```

### Google Cloud Deployment

```bash
# Deploy to Cloud Run
gcloud run deploy smart-assistant-bot \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars TELEGRAM_BOT_TOKEN=$TOKEN,OPENAI_API_KEY=$KEY
```

### Kubernetes Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: smart-assistant-bot
spec:
  replicas: 3
  selector:
    matchLabels:
      app: smart-bot
  template:
    metadata:
      labels:
        app: smart-bot
    spec:
      containers:
      - name: bot
        image: your-registry/smart-bot:latest
        env:
        - name: TELEGRAM_BOT_TOKEN
          valueFrom:
            secretKeyRef:
              name: bot-secrets
              key: telegram-token
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: bot-secrets
              key: openai-key
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
```

## 🔍 Testing & Validation

### Test Bot Connection

```python
# test_bot.py
import asyncio
from telegram_bot import TelegramBot

async def test_connection():
    bot = TelegramBot()
    await bot.initialize()
    
    # Test connection
    info = await bot.get_me()
    print(f"✅ Bot connected: @{info.username}")
    
    # Test message sending
    await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text="Test message"
    )
    print("✅ Message sent successfully")

asyncio.run(test_connection())
```

### Health Check Endpoint

```python
# healthcheck.py
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "bot": check_bot_status(),
        "database": check_db_status(),
        "cache": check_redis_status()
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

## 🔧 Troubleshooting

### Common Issues

#### Bot Not Responding
```bash
# Check process
ps aux | grep telegram_bot

# Check logs
tail -f logs/bot.log

# Test token
curl https://api.telegram.org/bot${TOKEN}/getMe
```

#### OpenAI API Errors
```bash
# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Check rate limits
python -c "import openai; print(openai.RateLimitError)"
```

#### Database Connection Issues
```bash
# Test PostgreSQL
psql -h localhost -U postgres -d bot_db

# Test Redis
redis-cli ping

# Check connections
netstat -an | grep ESTABLISHED
```

### Error Recovery

```python
# Auto-restart on failure
while true; do
    python telegram_bot_main.py
    echo "Bot crashed. Restarting in 5 seconds..."
    sleep 5
done
```

## 📊 Monitoring

### Logging Configuration

```python
# config/logging.py
LOGGING_CONFIG = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/bot.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'detailed'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        }
    },
    'formatters': {
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'simple': {
            'format': '%(levelname)s - %(message)s'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['file', 'console']
    }
}
```

### Metrics Collection

```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
messages_processed = Counter('bot_messages_processed', 'Total messages processed')
response_time = Histogram('bot_response_time', 'Response time in seconds')
active_users = Gauge('bot_active_users', 'Number of active users')

# Use in code
@messages_processed.count_exceptions()
async def process_message(message):
    with response_time.time():
        # Process message
        pass
```

## 🔐 Security Configuration

### Environment Security
```bash
# Secure .env file
chmod 600 .env

# Use secrets manager
aws secretsmanager get-secret-value --secret-id bot-secrets

# Rotate keys regularly
python scripts/rotate_keys.py
```

### Network Security
```nginx
# nginx.conf for reverse proxy
server {
    listen 443 ssl;
    server_name bot.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

Need help? Check our [Troubleshooting Guide](./troubleshooting) or join the [Community](https://community.varga-ai.com) →