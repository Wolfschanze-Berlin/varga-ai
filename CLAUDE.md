# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive AutoGen-based SaaS platform for AI automation with focus on education and SME solutions:

1. **Python Backend**: Core AutoGen-based automation platform (`main.py`, dependencies in `pyproject.toml`)
2. **AI Agent Library**: Pre-built specialized agents for various domains:
   - **Education**: Advanced Language Teacher Agent with adaptive learning AI
   - **SME Automation**: Business agents for customer service, invoicing, and scheduling
3. **Documentation Site**: Docusaurus-based documentation in `gutenberg/` directory
4. **Telegram Bot Integration**: Multi-agent conversational interfaces

### Key AI Implementation: Language Teacher Agent

The project features a comprehensive AI-powered language learning system (`agents/categories/education/language_teacher/`) including:

- **Adaptive Learning Engine**: IRT/BKT models for personalized difficulty adjustment
- **Natural Language Processing**: Grammar error detection, semantic analysis, complexity assessment
- **Spaced Repetition System**: SM-2+ algorithm for optimal retention scheduling  
- **Learning Analytics**: Progress tracking, learning style identification, performance forecasting
- **Content Generation**: Dynamic exercise creation with personalized scenarios
- **AutoGen Multi-Agent Framework**: Teacher, Assessment, and Content Creation agents

The system provides production-ready AI components with proper error handling, performance optimization, and Telegram bot integration.

## Development Commands

### Python Development (Root Directory)
```bash
# Install dependencies using uv
uv sync

# Run the main application
uv run python main.py

# Enter Python environment
uv shell
```

### Documentation Development (Docusaurus)
```bash
cd gutenberg

# Install dependencies
npm install

# Start development server (http://localhost:3000)
npm start

# Build for production
npm run build

# Serve production build
npm run serve

# Type checking
npm run typecheck

# Clear cache
npm run clear
```

## Architecture

### Python Components
- **main.py**: Entry point with basic Hello World functionality
- **Dependencies**: AutoGen AgentChat (>=0.7.2), AutoGen Extensions with OpenAI (>=0.7.2), AutoGen Studio (>=0.1.5)
- **Python Version**: Requires Python >=3.12

### Documentation Structure (gutenberg/)
- **Docusaurus 3.8.1** with TypeScript support
- **React 19** for custom components
- **Preset Classic** configuration
- **MDX** support for enhanced markdown

### Key Directories
```
varga-ai/
├── main.py                     # Python entry point
├── pyproject.toml              # Python dependencies
├── projectBrief.md             # Comprehensive project specification
├── gutenberg/                  # Docusaurus documentation site
│   ├── docs/                   # Documentation pages
│   ├── blog/                   # Blog posts
│   ├── src/                    # React components and pages
│   │   ├── components/         # Reusable React components
│   │   ├── css/               # Global styles
│   │   └── pages/             # Custom pages
│   ├── static/                # Static assets
│   ├── docusaurus.config.ts   # Main Docusaurus configuration
│   ├── sidebars.ts            # Navigation configuration
│   └── package.json           # Node.js dependencies
└── .claude/                   # Claude Code configuration (git submodules)
```

## Configuration Details

### Docusaurus Configuration
- **Title**: Currently "My Site" (needs customization for project)
- **TypeScript**: Full TypeScript support enabled
- **Future v4**: Enabled for forward compatibility
- **Themes**: GitHub light theme and Dracula dark theme for code highlighting
- **Plugins**: Classic preset with docs, blog, and theme

### Python Project Structure
- **Package Management**: Uses `uv` for dependency management
- **AutoGen Focus**: Built specifically for AutoGen framework integration
- **Minimal Setup**: Currently basic Hello World implementation

## Development Patterns

### Adding Documentation
1. Create markdown files in `gutenberg/docs/`
2. Update `gutenberg/sidebars.ts` for navigation
3. Use TypeScript for custom React components

### Python Development
1. Use `uv` for all package management
2. Follow AutoGen framework patterns for agent development
3. Maintain Python >=3.12 compatibility

### Component Development (Docusaurus)
1. Place custom components in `gutenberg/src/components/`
2. Use TypeScript interfaces for props
3. Follow React 19 best practices
4. Import components in MDX files with standard ES6 imports

## Technical Requirements

### Node.js Environment
- **Node Version**: >=18.0 (specified in package.json engines)
- **Package Manager**: npm (lockfile present)
- **TypeScript**: ~5.6.2

### Python Environment
- **Python Version**: >=3.12
- **Package Manager**: uv
- **Key Framework**: AutoGen for multi-agent systems

### Browser Support
- **Production**: >0.5%, not dead, not op_mini all
- **Development**: Last 3 versions of Chrome, Firefox, and last 5 Safari versions

## Project Context

This project is in early development phase. The `projectBrief.md` contains comprehensive specifications for:
- Multi-tenant SaaS platform architecture
- 25-30 pre-built AutoGen agents for SME automation
- Integration with popular SME tools (Gmail, Slack, QuickBooks, etc.)
- Visual workflow builder and analytics dashboard
- Targets 1,000 SME signups and $500K revenue in Year 1

The documentation site (gutenberg/) will serve as both project documentation and potential customer-facing content for the SaaS platform.
- FOLLOW STRICTLY @projectBrief.md
- ULTRA IMPORTANT ALL DOCS NEEDS TO BE WRITTE IN gutenberg/ with proper folder structure
- Everytime when compact you create/update a file in .claude/context/history.json file and write all impoortant fixes and learned know how in it. important do not delete previous data.
- ALWAYS before you start read the .claude/context/ folder and read all files and ultrathink it.
- When you start pls output what you files you read
- Before you start always use context7 mcp tool to get the latest docs