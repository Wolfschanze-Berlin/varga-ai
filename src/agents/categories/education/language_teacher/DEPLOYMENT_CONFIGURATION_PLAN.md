# Deployment and Configuration Management Plan

## Overview
Comprehensive deployment strategy for the Language Teacher Bot system, including environment management, configuration, monitoring, and production deployment procedures.

## Deployment Architecture

### Production Environment Structure
```mermaid
graph TB
    subgraph "Load Balancer Layer"
        LB[Load Balancer]
    end
    
    subgraph "Application Layer"
        APP1[Language Teacher Bot Instance 1]
        APP2[Language Teacher Bot Instance 2]
        APP3[Language Teacher Bot Instance N]
    end
    
    subgraph "Service Layer"
        TG[Telegram Service]
        AI[AI Service]
        VOICE[Voice Processing]
        CACHE[Redis Cache]
    end
    
    subgraph "Data Layer"
        DB[(PostgreSQL)]
        BACKUP[(Backup Storage)]
        LOGS[(Log Storage)]
    end
    
    subgraph "External Services"
        OPENAI[OpenAI API]
        TELEGRAM_API[Telegram API]
        MONITORING[Monitoring Services]
    end
    
    LB --> APP1
    LB --> APP2
    LB --> APP3
    
    APP1 --> TG
    APP1 --> AI
    APP1 --> VOICE
    APP1 --> CACHE
    
    TG --> DB
    AI --> DB
    CACHE --> DB
    
    APP1 --> OPENAI
    APP1 --> TELEGRAM_API
    APP1 --> MONITORING
    
    DB --> BACKUP
    APP1 --> LOGS
```

## Environment Configuration

### Development Environment
```yaml
# config/environments/development.yaml
environment: development

database:
  type: sqlite
  path: "./language_teacher_dev.db"
  echo_sql: true
  
telegram:
  bot_token: "${TELEGRAM_BOT_TOKEN_DEV}"
  webhook_url: null  # Use polling in development
  polling_interval: 1
  
openai:
  api_key: "${OPENAI_API_KEY_DEV}"
  model: "gpt-3.5-turbo"  # Cheaper for development
  max_tokens: 1000
  temperature: 0.7
  
voice_processing:
  enabled: false  # Disable voice in development
  transcription_service: "mock"
  
logging:
  level: DEBUG
  format: detailed
  handlers:
    - console
    - file
  
redis:
  enabled: false  # Use in-memory cache for development
  
monitoring:
  enabled: false
  
rate_limiting:
  messages_per_minute: 100  # Relaxed for development
  
features:
  achievements: true
  voice_messages: false
  spaced_repetition: true
  analytics: true
```

### Staging Environment
```yaml
# config/environments/staging.yaml
environment: staging

database:
  type: postgresql
  host: "${DB_HOST_STAGING}"
  port: 5432
  name: "language_teacher_staging"
  username: "${DB_USER_STAGING}"
  password: "${DB_PASSWORD_STAGING}"
  pool_size: 10
  echo_sql: false
  
telegram:
  bot_token: "${TELEGRAM_BOT_TOKEN_STAGING}"
  webhook_url: "${WEBHOOK_URL_STAGING}"
  webhook_secret: "${WEBHOOK_SECRET_STAGING}"
  
openai:
  api_key: "${OPENAI_API_KEY_STAGING}"
  model: "gpt-4"
  max_tokens: 2000
  temperature: 0.7
  rate_limit_rpm: 1000
  
voice_processing:
  enabled: true
  transcription_service: "openai_whisper"
  max_file_size_mb: 25
  
logging:
  level: INFO
  format: json
  handlers:
    - console
    - file
    - remote
  remote_endpoint: "${LOG_ENDPOINT_STAGING}"
  
redis:
  enabled: true
  host: "${REDIS_HOST_STAGING}"
  port: 6379
  password: "${REDIS_PASSWORD_STAGING}"
  
monitoring:
  enabled: true
  service: "datadog"
  api_key: "${DATADOG_API_KEY_STAGING}"
  
rate_limiting:
  messages_per_minute: 60
  messages_per_hour: 1000
  
features:
  achievements: true
  voice_messages: true
  spaced_repetition: true
  analytics: true
```

### Production Environment
```yaml
# config/environments/production.yaml
environment: production

database:
  type: postgresql
  host: "${DB_HOST_PROD}"
  port: 5432
  name: "language_teacher_prod"
  username: "${DB_USER_PROD}"
  password: "${DB_PASSWORD_PROD}"
  pool_size: 20
  pool_timeout: 30
  echo_sql: false
  ssl_mode: require
  
telegram:
  bot_token: "${TELEGRAM_BOT_TOKEN_PROD}"
  webhook_url: "${WEBHOOK_URL_PROD}"
  webhook_secret: "${WEBHOOK_SECRET_PROD}"
  drop_pending_updates: false
  
openai:
  api_key: "${OPENAI_API_KEY_PROD}"
  model: "gpt-4"
  max_tokens: 2000
  temperature: 0.7
  rate_limit_rpm: 3000
  timeout_seconds: 30
  
voice_processing:
  enabled: true
  transcription_service: "openai_whisper"
  max_file_size_mb: 25
  pronunciation_analysis: true
  
logging:
  level: INFO
  format: json
  handlers:
    - file
    - remote
  remote_endpoint: "${LOG_ENDPOINT_PROD}"
  max_log_size_mb: 100
  backup_count: 7
  
redis:
  enabled: true
  host: "${REDIS_HOST_PROD}"
  port: 6379
  password: "${REDIS_PASSWORD_PROD}"
  ssl: true
  pool_size: 10
  
monitoring:
  enabled: true
  service: "datadog"
  api_key: "${DATADOG_API_KEY_PROD}"
  custom_metrics: true
  alerts: true
  
rate_limiting:
  messages_per_minute: 30
  messages_per_hour: 500
  concurrent_sessions_per_user: 1
  
security:
  encryption_key: "${ENCRYPTION_KEY_PROD}"
  jwt_secret: "${JWT_SECRET_PROD}"
  allowed_origins: ["https://yourdomain.com"]
  
features:
  achievements: true
  voice_messages: true
  spaced_repetition: true
  analytics: true
  advanced_ai: true
  
performance:
  max_concurrent_users: 10000
  session_timeout_minutes: 30
  cache_ttl_seconds: 300
```

## Configuration Management System

### Configuration Manager
```python
# config/configuration_manager.py
class ConfigurationManager:
    """Centralized configuration management."""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from multiple sources."""
        
        # 1. Load base configuration
        base_config = self._load_yaml_config("config/base.yaml")
        
        # 2. Load environment-specific configuration
        env_config = self._load_yaml_config(f"config/environments/{self.environment}.yaml")
        
        # 3. Override with environment variables
        env_vars = self._load_env_variables()
        
        # 4. Merge configurations
        config = self._merge_configs(base_config, env_config, env_vars)
        
        # 5. Validate configuration
        self._validate_config(config)
        
        return config
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Validate configuration completeness and correctness."""
        required_keys = [
            "telegram.bot_token",
            "openai.api_key", 
            "database.host",
            "database.name"
        ]
        
        for key in required_keys:
            if not self._get_nested_value(config, key):
                raise ConfigurationError(f"Required configuration missing: {key}")
        
        # Validate specific values
        if config["environment"] == "production":
            self._validate_production_config(config)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with dot notation."""
        return self._get_nested_value(self.config, key, default)
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return self.config["database"]
    
    def get_telegram_config(self) -> Dict[str, Any]:
        """Get Telegram configuration."""
        return self.config["telegram"]
    
    def get_openai_config(self) -> Dict[str, Any]:
        """Get OpenAI configuration."""
        return self.config["openai"]
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if feature is enabled."""
        return self.config.get("features", {}).get(feature, False)

# Global configuration instance
config_manager = ConfigurationManager(os.getenv("ENVIRONMENT", "development"))
```

### Secret Management
```python
# config/secret_manager.py
class SecretManager:
    """Manages sensitive configuration data."""
    
    def __init__(self, provider: str = "env"):
        self.provider = provider
        self.secrets = {}
        
    async def get_secret(self, key: str) -> Optional[str]:
        """Get secret value from configured provider."""
        if self.provider == "env":
            return os.getenv(key)
        elif self.provider == "vault":
            return await self._get_from_vault(key)
        elif self.provider == "aws_secrets":
            return await self._get_from_aws_secrets(key)
        
    async def _get_from_vault(self, key: str) -> Optional[str]:
        """Get secret from HashiCorp Vault."""
        # Implementation for Vault integration
        pass
        
    async def _get_from_aws_secrets(self, key: str) -> Optional[str]:
        """Get secret from AWS Secrets Manager."""
        # Implementation for AWS Secrets Manager
        pass
```

## Docker Configuration

### Dockerfile
```dockerfile
# Dockerfile
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application
CMD ["python", "-m", "agents.categories.education.language_teacher.main"]
```

### Docker Compose for Development
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  language-teacher-bot:
    build: .
    environment:
      - ENVIRONMENT=development
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DB_HOST=postgres
      - DB_NAME=language_teacher
      - DB_USER=postgres
      - DB_PASSWORD=postgres
      - REDIS_HOST=redis
    volumes:
      - .:/app
      - ./logs:/app/logs
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: language_teacher
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/schema.sql:/docker-entrypoint-initdb.d/schema.sql
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

volumes:
  postgres_data:
  redis_data:
```

### Production Docker Compose
```yaml
# docker-compose.prod.yml  
version: '3.8'

services:
  language-teacher-bot:
    image: language-teacher-bot:${VERSION}
    environment:
      - ENVIRONMENT=production
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DB_HOST=${DB_HOST}
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - REDIS_HOST=${REDIS_HOST}
      - REDIS_PASSWORD=${REDIS_PASSWORD}
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
      restart_policy:
        condition: any
        delay: 5s
        max_attempts: 3
        window: 120s
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
        monitor: 60s
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"

networks:
  default:
    driver: overlay
    attachable: true
```

## CI/CD Pipeline

### GitHub Actions Workflow
```yaml
# .github/workflows/deploy.yml
name: Deploy Language Teacher Bot

on:
  push:
    branches: [main, develop]
    paths: 
      - 'agents/categories/education/language_teacher/**'
      - '.github/workflows/deploy.yml'
  pull_request:
    branches: [main]
    paths:
      - 'agents/categories/education/language_teacher/**'

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_DB: test_db
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
        
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-test.txt
        
    - name: Run linting
      run: |
        flake8 agents/categories/education/language_teacher/
        black --check agents/categories/education/language_teacher/
        mypy agents/categories/education/language_teacher/
        
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
      run: |
        pytest agents/categories/education/language_teacher/tests/ \
          --cov=agents/categories/education/language_teacher \
          --cov-report=xml \
          --cov-fail-under=80
        
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      
  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
      
    - name: Login to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ secrets.CONTAINER_REGISTRY }}
        username: ${{ secrets.REGISTRY_USERNAME }}
        password: ${{ secrets.REGISTRY_PASSWORD }}
        
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: |
          ${{ secrets.CONTAINER_REGISTRY }}/language-teacher-bot:${{ github.sha }}
          ${{ secrets.CONTAINER_REGISTRY }}/language-teacher-bot:latest
        cache-from: type=gha
        cache-to: type=gha,mode=max
        
  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    environment: staging
    
    steps:
    - name: Deploy to staging
      run: |
        # Deploy to staging environment
        echo "Deploying to staging..."
        # Add staging deployment commands
        
  deploy-production:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production
    
    steps:
    - name: Deploy to production
      run: |
        # Deploy to production environment  
        echo "Deploying to production..."
        # Add production deployment commands
```

## Monitoring and Observability

### Application Monitoring
```python
# monitoring/app_monitor.py
class ApplicationMonitor:
    """Application monitoring and metrics collection."""
    
    def __init__(self, monitoring_service: str = "datadog"):
        self.monitoring_service = monitoring_service
        self.metrics_client = self._init_metrics_client()
        
    def _init_metrics_client(self):
        """Initialize metrics client based on service."""
        if self.monitoring_service == "datadog":
            from datadog import statsd
            return statsd
        # Add other monitoring services as needed
        
    async def track_user_interaction(self, user_id: int, interaction_type: str):
        """Track user interaction metrics."""
        self.metrics_client.increment(
            'language_teacher.user_interactions',
            tags=[f'type:{interaction_type}']
        )
        
    async def track_response_time(self, endpoint: str, duration_ms: float):
        """Track API response time."""
        self.metrics_client.histogram(
            'language_teacher.response_time',
            duration_ms,
            tags=[f'endpoint:{endpoint}']
        )
        
    async def track_error(self, error_type: str, severity: str):
        """Track application errors."""
        self.metrics_client.increment(
            'language_teacher.errors',
            tags=[f'type:{error_type}', f'severity:{severity}']
        )
        
    async def track_learning_progress(self, user_id: int, skill_type: str, score: float):
        """Track learning progress metrics."""
        self.metrics_client.gauge(
            'language_teacher.learning_score',
            score,
            tags=[f'skill:{skill_type}']
        )
```

### Health Check Endpoints
```python
# monitoring/health_checks.py
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "healthy", "timestamp": datetime.now().isoformat()}
    )

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with component status."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }
    
    # Check database connectivity
    try:
        await check_database_connection()
        health_status["components"]["database"] = "healthy"
    except Exception as e:
        health_status["components"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis connectivity
    try:
        await check_redis_connection()
        health_status["components"]["redis"] = "healthy"
    except Exception as e:
        health_status["components"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check external services
    try:
        await check_openai_service()
        health_status["components"]["openai"] = "healthy"
    except Exception as e:
        health_status["components"]["openai"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    status_code = status.HTTP_200_OK if health_status["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(
        status_code=status_code,
        content=health_status
    )

@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus-style metrics endpoint."""
    # Return application metrics in Prometheus format
    pass
```

## Deployment Scripts

### Deployment Automation
```bash
#!/bin/bash
# scripts/deploy.sh

set -e

ENVIRONMENT=${1:-staging}
VERSION=${2:-latest}

echo "Deploying Language Teacher Bot to $ENVIRONMENT..."

# Pre-deployment checks
echo "Running pre-deployment checks..."
./scripts/pre_deploy_checks.sh $ENVIRONMENT

# Database migrations
echo "Running database migrations..."
./scripts/migrate.sh $ENVIRONMENT

# Deploy application
echo "Deploying application version $VERSION..."
case $ENVIRONMENT in
    staging)
        docker-compose -f docker-compose.staging.yml up -d
        ;;
    production)
        docker stack deploy -c docker-compose.prod.yml language-teacher-stack
        ;;
esac

# Post-deployment verification
echo "Running post-deployment verification..."
./scripts/post_deploy_verification.sh $ENVIRONMENT

# Health check
echo "Waiting for service to be healthy..."
./scripts/wait_for_health.sh $ENVIRONMENT

echo "Deployment completed successfully!"
```

### Database Migration Script
```bash
#!/bin/bash
# scripts/migrate.sh

ENVIRONMENT=${1:-development}

echo "Running database migrations for $ENVIRONMENT..."

case $ENVIRONMENT in
    development)
        export DATABASE_URL="sqlite:///language_teacher_dev.db"
        ;;
    staging)
        export DATABASE_URL="postgresql://$DB_USER_STAGING:$DB_PASSWORD_STAGING@$DB_HOST_STAGING:5432/language_teacher_staging"
        ;;
    production)
        export DATABASE_URL="postgresql://$DB_USER_PROD:$DB_PASSWORD_PROD@$DB_HOST_PROD:5432/language_teacher_prod"
        ;;
esac

# Run migrations
python -m alembic upgrade head

echo "Database migrations completed."
```

## Configuration Validation

### Validation Script
```python
# scripts/validate_config.py
"""Configuration validation script."""

import sys
from agents.categories.education.language_teacher.config.configuration_manager import ConfigurationManager

def validate_environment_config(environment: str) -> bool:
    """Validate configuration for specific environment."""
    try:
        config_manager = ConfigurationManager(environment)
        
        # Test database connection
        db_config = config_manager.get_database_config()
        # Add database connection test
        
        # Test external services
        openai_config = config_manager.get_openai_config()
        # Add OpenAI API test
        
        telegram_config = config_manager.get_telegram_config()
        # Add Telegram bot token validation
        
        print(f"✅ Configuration for {environment} is valid")
        return True
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False

if __name__ == "__main__":
    environment = sys.argv[1] if len(sys.argv) > 1 else "development"
    
    if not validate_environment_config(environment):
        sys.exit(1)
    
    print("All configuration validations passed!")
```

## Backup and Recovery

### Database Backup Strategy
```bash
#!/bin/bash
# scripts/backup_database.sh

ENVIRONMENT=${1:-production}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "Creating database backup for $ENVIRONMENT..."

case $ENVIRONMENT in
    production)
        pg_dump -h $DB_HOST_PROD -U $DB_USER_PROD -d language_teacher_prod \
            > "backups/language_teacher_prod_${TIMESTAMP}.sql"
        ;;
    staging)
        pg_dump -h $DB_HOST_STAGING -U $DB_USER_STAGING -d language_teacher_staging \
            > "backups/language_teacher_staging_${TIMESTAMP}.sql"
        ;;
esac

# Upload to cloud storage
aws s3 cp "backups/language_teacher_${ENVIRONMENT}_${TIMESTAMP}.sql" \
    s3://your-backup-bucket/database-backups/

echo "Database backup completed: ${TIMESTAMP}"
```

This comprehensive deployment plan ensures reliable, scalable, and maintainable production deployment of the Language Teacher Bot system.