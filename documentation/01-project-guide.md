---
title: "DocSynapse - Project Guide"
purpose: "Complete project overview, architecture, and development setup"
author: "Generated for AI Agent Implementation"
date: "2025-07-01"
version: "1.0"
---

# DocSynapse - Project Guide

## Project Overview

### Purpose
DocSynapse transforms traditional software documentation into LLM-friendly formats by crawling documentation websites, processing content, and generating optimized markdown files that AI agents and language models can efficiently consume.

### Core Problem
- Most software documentation is designed for human consumption with complex navigation, repeated elements, and formatting that's inefficient for LLMs
- AI agents struggle to process scattered documentation across multiple pages
- Developers need a way to quickly make any documentation "AI-ready"

### Solution
DocSynapse provides a web application where users can:
1. Input a base URL of any software documentation
2. Automatically crawl and process all documentation pages
3. Generate a single, optimized markdown file with structured metadata
4. Download the LLM-friendly documentation for immediate use

### Key Features
- **Smart Web Crawling**: Uses Playwright to handle JavaScript-rendered content
- **Intelligent Deduplication**: Removes navigation, headers, footers, and repeated content
- **Code Preservation**: Maintains syntax highlighting and code block integrity
- **Link Resolution**: Converts relative links to absolute URLs
- **Progress Tracking**: Real-time progress updates during crawling
- **Rate Limiting**: Respects robots.txt and implements crawling delays
- **Metadata Generation**: Rich metadata including site structure and extraction details

## Architecture Overview

### System Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   SvelteKit     │    │    FastAPI      │    │   Playwright    │
│   Frontend      │◄──►│    Backend      │◄──►│   Browser       │
│                 │    │                 │    │   Automation    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   TailwindCSS   │    │     Redis       │    │   Target Docs   │
│   UI Library    │    │    Queue/Cache  │    │    Websites     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Data Flow
1. **User Input**: User enters documentation base URL in SvelteKit frontend
2. **Validation**: Frontend validates URL and sends to FastAPI backend
3. **Crawling**: Backend uses Playwright to discover and crawl all documentation pages
4. **Processing**: Content is cleaned, deduplicated, and optimized
5. **Generation**: Markdown file is generated with metadata
6. **Progress Updates**: Real-time progress sent via WebSocket to frontend
7. **Download**: Processed file is made available for download

### Component Responsibilities

**Frontend (SvelteKit)**
- User interface for URL input and configuration
- Real-time progress display
- File download handling
- WebSocket connection management

**Backend (FastAPI)**
- URL validation and robots.txt checking
- Crawling orchestration and management
- Content processing and optimization
- Progress tracking and WebSocket communication
- File generation and serving

**Crawler (Playwright)**
- Page discovery and navigation
- Content extraction from JavaScript-heavy sites
- Handling of dynamic content and SPAs
- Screenshot capabilities for debugging

## Technology Stack

### Frontend Stack
- **SvelteKit 2.0+**: Modern framework with file-based routing
- **Svelte 5 Runes**: Latest reactivity system for state management
- **TailwindCSS 3.4+**: Utility-first CSS framework
- **TypeScript**: Type safety and better development experience
- **Vite**: Fast build tool and development server

### Backend Stack
- **FastAPI 0.104+**: Modern Python web framework
- **Python 3.11+**: Latest Python with performance improvements
- **Playwright**: Browser automation for content extraction
- **Pydantic 2.0+**: Data validation and serialization
- **asyncio**: Asynchronous programming support
- **aiofiles**: Async file operations

### Supporting Technologies
- **Redis**: Optional caching and job queue management
- **Docker**: Containerization for deployment
- **WebSockets**: Real-time communication
- **Uvicorn**: ASGI server for FastAPI

### Development Tools
- **ESLint + Prettier**: Code formatting and linting
- **Black + isort**: Python code formatting
- **pytest**: Python testing framework
- **Vitest**: JavaScript/TypeScript testing
- **Docker Compose**: Local development orchestration

## Development Environment Setup

### Prerequisites
Ensure you have the following installed:
- **Node.js 18+** and **npm/pnpm**
- **Python 3.11+** and **pip**
- **Docker** and **Docker Compose**
- **Git**

### System Requirements
- **RAM**: Minimum 8GB (16GB recommended)
- **Storage**: 2GB free space
- **OS**: Windows 10+, macOS 10.15+, or Linux

### Environment Setup

#### 1. Clone Repository and Setup Structure
```bash
# Create project directory
mkdir docsynapse
cd docsynapse

# Initialize git repository
git init

# Create project structure
mkdir -p frontend backend shared documentation
mkdir -p backend/app/{api,core,models,services}
mkdir -p backend/app/api/endpoints
mkdir -p frontend/src/{lib,routes}
mkdir -p frontend/src/lib/{components,stores}
```

#### 2. Backend Environment Setup
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Create requirements.txt
cat > requirements.txt << EOF
fastapi==0.104.1
uvicorn[standard]==0.24.0
playwright==1.40.0
pydantic==2.5.0
aiofiles==23.2.1
python-multipart==0.0.6
websockets==12.0
redis==5.0.1
beautifulsoup4==4.12.2
lxml==4.9.3
requests==2.31.0
python-dotenv==1.0.0
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
isort==5.12.0
EOF

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install

# Create .env file
cat > .env << EOF
# Application Settings
APP_NAME=DocSynapse
APP_VERSION=1.0.0
DEBUG=True

# Server Settings
HOST=0.0.0.0
PORT=8000

# CORS Settings
ALLOWED_ORIGINS=["http://localhost:5173"]

# Crawler Settings
MAX_CONCURRENT_REQUESTS=5
REQUEST_DELAY=1.0
TIMEOUT=30
MAX_PAGES=1000

# Redis Settings (optional)
REDIS_URL=redis://localhost:6379
USE_REDIS=False

# File Settings
MAX_FILE_SIZE=100MB
OUTPUT_DIR=./output
EOF
```

#### 3. Frontend Environment Setup
```bash
cd ../frontend

# Initialize SvelteKit project
npm create svelte@latest . --template skeleton --types typescript --no-eslint --no-prettier --no-playwright --no-vitest

# Install additional dependencies
npm install tailwindcss @tailwindcss/typography @tailwindcss/forms autoprefixer
npm install @types/node
npm install -D @tailwindcss/typography @tailwindcss/forms

# Initialize Tailwind
npx tailwindcss init -p

# Update tailwind.config.js
cat > tailwind.config.js << EOF
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        }
      }
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
    require('@tailwindcss/forms'),
  ],
}
EOF

# Create app.css
cat > src/app.css << EOF
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  html {
    font-family: system-ui, sans-serif;
  }
}

@layer components {
  .btn {
    @apply px-4 py-2 rounded-lg font-medium transition-colors;
  }
  
  .btn-primary {
    @apply bg-primary-600 text-white hover:bg-primary-700;
  }
  
  .btn-secondary {
    @apply bg-gray-200 text-gray-900 hover:bg-gray-300;
  }
}
EOF

# Update src/app.html
cat > src/app.html << EOF
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%sveltekit.assets%/favicon.png" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>DocSynapse - Transform Documentation for AI</title>
    %sveltekit.head%
  </head>
  <body data-sveltekit-preload-data="hover" class="bg-gray-50">
    <div style="display: contents">%sveltekit.body%</div>
  </body>
</html>
EOF

# Create environment file
cat > .env << EOF
# API Configuration
PUBLIC_API_BASE_URL=http://localhost:8000
PUBLIC_WS_BASE_URL=ws://localhost:8000
EOF
```

#### 4. Root Configuration Files

```bash
cd ..

# Create docker-compose.yml
cat > docker-compose.yml << EOF
version: '3.8'

services:
  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DEBUG=True
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./backend:/app
      - ./output:/app/output
    depends_on:
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev -- --host 0.0.0.0

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
EOF

# Create .gitignore
cat > .gitignore << EOF
# Dependencies
node_modules/
__pycache__/
*.pyc
venv/
.venv/

# Build outputs
/frontend/build/
/frontend/.svelte-kit/
/backend/output/
dist/
*.egg-info/

# Environment files
.env
.env.local
.env.production

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Temporary files
*.tmp
*.temp
.cache/

# Docker
docker-compose.override.yml

# Playwright
test-results/
playwright-report/
EOF

# Create README.md
cat > README.md << EOF
# DocSynapse

Transform any software documentation into LLM-friendly format.

## Quick Start

1. **Clone and Setup**
   \`\`\`bash
   git clone <repository-url>
   cd docsynapse
   \`\`\`

2. **Backend Setup**
   \`\`\`bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   playwright install
   \`\`\`

3. **Frontend Setup**
   \`\`\`bash
   cd frontend
   npm install
   \`\`\`

4. **Run Development**
   \`\`\`bash
   # Terminal 1 - Backend
   cd backend && uvicorn app.main:app --reload
   
   # Terminal 2 - Frontend
   cd frontend && npm run dev
   \`\`\`

5. **Access Application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Features

- ✅ Smart web crawling with Playwright
- ✅ Intelligent content deduplication
- ✅ Code block preservation
- ✅ Link resolution
- ✅ Real-time progress tracking
- ✅ Rate limiting and robots.txt respect
- ✅ LLM-optimized markdown generation

## Documentation

See \`documentation/\` folder for comprehensive implementation guides.

## Contributing

1. Fork the repository
2. Create feature branch: \`git checkout -b feature/new-feature\`
3. Commit changes: \`git commit -am 'Add new feature'\`
4. Push to branch: \`git push origin feature/new-feature\`
5. Submit pull request

## License

MIT License - see LICENSE file for details.
EOF
```

## Project Structure Deep Dive

### Complete Directory Structure
```
docsynapse/
├── documentation/           # AI-friendly implementation docs
│   ├── 01-project-guide.md
│   ├── 02-backend-implementation.md
│   ├── 03-frontend-implementation.md
│   ├── 04-core-features.md
│   └── 05-deployment-testing.md
├── frontend/               # SvelteKit application
│   ├── src/
│   │   ├── lib/
│   │   │   ├── components/    # Reusable UI components
│   │   │   │   ├── CrawlForm.svelte
│   │   │   │   ├── ProgressTracker.svelte
│   │   │   │   ├── ResultsDisplay.svelte
│   │   │   │   └── Layout.svelte
│   │   │   ├── stores/        # Svelte stores for state
│   │   │   │   ├── crawler.ts
│   │   │   │   └── websocket.ts
│   │   │   ├── types/         # TypeScript type definitions
│   │   │   │   └── api.ts
│   │   │   └── utils/         # Utility functions
│   │   │       ├── api.ts
│   │   │       └── validation.ts
│   │   ├── routes/            # SvelteKit routes
│   │   │   ├── +layout.svelte
│   │   │   ├── +page.svelte
│   │   │   └── api/           # API routes (if needed)
│   │   ├── app.css           # Global styles
│   │   └── app.html          # HTML template
│   ├── static/              # Static assets
│   ├── package.json
│   ├── svelte.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── vite.config.ts
├── backend/                # FastAPI application
│   ├── app/
│   │   ├── api/
│   │   │   ├── endpoints/     # API route handlers
│   │   │   │   ├── __init__.py
│   │   │   │   ├── crawler.py
│   │   │   │   └── websocket.py
│   │   │   ├── __init__.py
│   │   │   └── deps.py        # Dependency injection
│   │   ├── core/             # Core configuration and utilities
│   │   │   ├── __init__.py
│   │   │   ├── config.py     # Application configuration
│   │   │   ├── logging.py    # Logging setup
│   │   │   └── security.py   # Security utilities
│   │   ├── models/           # Pydantic models
│   │   │   ├── __init__.py
│   │   │   ├── crawler.py    # Crawler-related models
│   │   │   └── response.py   # API response models
│   │   ├── services/         # Business logic services
│   │   │   ├── __init__.py
│   │   │   ├── crawler_service.py
│   │   │   ├── processor_service.py
│   │   │   ├── deduplication_service.py
│   │   │   ├── link_resolver_service.py
│   │   │   └── markdown_generator_service.py
│   │   ├── utils/            # Utility functions
│   │   │   ├── __init__.py
│   │   │   ├── file_utils.py
│   │   │   ├── url_utils.py
│   │   │   └── content_utils.py
│   │   ├── __init__.py
│   │   └── main.py           # FastAPI application entry point
│   ├── tests/               # Test files
│   │   ├── __init__.py
│   │   ├── test_crawler.py
│   │   └── test_processor.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
├── shared/                 # Shared code between frontend/backend
│   ├── types/              # Shared TypeScript/Python types
│   └── schemas/            # API schemas
├── output/                 # Generated documentation files
├── docker-compose.yml
├── .gitignore
├── .env.example
└── README.md
```

## Development Workflow

### Git Workflow
```bash
# Feature development
git checkout -b feature/crawler-service
# Make changes
git add .
git commit -m "feat: implement crawler service with Playwright"
git push origin feature/crawler-service

# Create pull request, merge, and cleanup
git checkout main
git pull origin main
git branch -d feature/crawler-service
```

### Development Commands

**Backend Development**
```bash
cd backend

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Format code
black .
isort .

# Type checking
mypy app/
```

**Frontend Development**
```bash
cd frontend

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run tests
npm run test

# Lint and format
npm run lint
npm run format
```

**Docker Development**
```bash
# Run entire stack
docker-compose up -d

# View logs
docker-compose logs -f

# Rebuild services
docker-compose build

# Stop services
docker-compose down
```

## Next Steps

After completing this setup:

1. **Review Backend Implementation** (02-backend-implementation.md)
2. **Review Frontend Implementation** (03-frontend-implementation.md)
3. **Implement Core Features** (04-core-features.md)
4. **Setup Deployment** (05-deployment-testing.md)

## Validation Checklist

- [ ] Node.js 18+ and Python 3.11+ installed
- [ ] Project structure created correctly
- [ ] Backend virtual environment activated
- [ ] All Python dependencies installed
- [ ] Playwright browsers installed
- [ ] Frontend dependencies installed
- [ ] TailwindCSS configured properly
- [ ] Environment files created
- [ ] Docker Compose runs without errors
- [ ] Development servers start successfully
- [ ] Basic API endpoint accessible at http://localhost:8000/docs

This completes the project setup. Proceed to the backend implementation documentation for the next phase.