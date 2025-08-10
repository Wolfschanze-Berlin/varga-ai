---
sidebar_position: 2
---

# Development Setup

Learn how to set up and contribute to the Varga AI Platform development environment.

## Prerequisites

Before getting started, ensure you have the following installed:

- **Python 3.12+**: Required for the backend platform
- **Node.js 18+**: Required for the documentation site
- **uv**: Python package manager for dependency management
- **Git**: Version control

## Project Structure

The project is organized as follows:

```
varga-ai/
├── src/                       # Python backend source
├── gutenberg/                 # Docusaurus documentation
├── pyproject.toml            # Python dependencies
├── main.py                   # Application entry point
└── .claude/                  # Claude Code configuration
```

## Backend Development Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd varga-ai
```

### 2. Install Python Dependencies

```bash
# Install dependencies using uv
uv sync

# Activate the virtual environment
uv shell
```

### 3. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your configuration
# Add your API keys and settings
```

### 4. Run the Application

```bash
# Run the main application
uv run python main.py

# Or run with the virtual environment activated
python main.py
```

## Documentation Development

### 1. Navigate to Documentation Directory

```bash
cd gutenberg
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Start Development Server

```bash
npm start
```

The documentation site will be available at [http://localhost:3000](http://localhost:3000).

## Development Guidelines

### Code Structure
- Follow the 1-file-1-class principle
- Maximum 400 lines per file
- Use centralized logging with loguru
- Implement comprehensive error handling

### Python Development
- Use type hints for all functions
- Follow PEP 8 style guidelines
- Write comprehensive docstrings
- Include unit tests for new features

### Documentation
- Use clear, concise language
- Include code examples
- Update documentation with code changes
- Follow Docusaurus markdown conventions
