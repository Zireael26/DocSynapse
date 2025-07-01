# DocSynapse

> Transform any software documentation into LLM-friendly formats with intelligent crawling and optimization.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![macOS](https://img.shields.io/badge/macOS-supported-lightgrey.svg)](https://www.apple.com/macos/)

DocSynapse bridges the gap between traditional documentation and AI consumption by transforming scattered documentation websites into single, optimized markdown files that LLMs and AI agents can efficiently process.

## ✨ Features

- **🤖 AI-Optimized Output**: Generates markdown files specifically structured for LLM consumption
- **🕷️ Smart Crawling**: Handles JavaScript-heavy documentation sites with Playwright
- **🧹 Intelligent Deduplication**: Removes navigation, headers, footers, and repeated content
- **🔗 Link Resolution**: Converts relative links to absolute URLs
- **💻 Code Preservation**: Maintains syntax highlighting and code block integrity
- **📊 Real-time Progress**: WebSocket-powered live progress tracking
- **🛡️ Respectful Crawling**: Respects robots.txt and implements proper rate limiting
- **📈 Rich Metadata**: Comprehensive metadata about documentation structure and content

## 🚀 Quick Start

### Automated Setup (macOS)

```bash
# Clone the repository
git clone https://github.com/Zireael26/docsynapse.git
cd docsynapse

# Run the automated setup script
./scripts/setup.sh

# Start development servers
./scripts/dev.sh

# Access the application
open http://localhost:5173
```

### Docker Setup (All Platforms)

```bash
# Clone and start with Docker
git clone https://github.com/Zireael26/docsynapse.git
cd docsynapse

# Start with Docker Compose
docker-compose up -d

# Access the application
open http://localhost:5173
```

### Manual Setup

<details>
<summary>Click to expand manual setup instructions</summary>

#### Prerequisites
- **Node.js 18+** and npm
- **Python 3.11+** and pip
- **Docker** (optional, for containerized deployment)

#### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install

# Start the backend
uvicorn app.main:app --reload
```

#### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start the frontend
npm run dev
```

#### Access the Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

</details>

## 🎯 How It Works

1. **Enter Documentation URL**: Paste any documentation website URL
2. **Configure Options**: Set crawling preferences (optional)
3. **Watch Real-time Progress**: Monitor page discovery and processing
4. **Download Optimized File**: Get a single markdown file with all documentation

### Example Usage

```bash
# Input: https://docs.sveltekit.dev
# Output: docsynapse_docs_sveltekit_dev_20250701_022901.md

# The generated file contains:
# - Complete documentation from all pages
# - Rich metadata about site structure
# - Cleaned content without navigation/boilerplate
# - Preserved code blocks with syntax highlighting
# - Resolved absolute links
```

## 🛠️ Development Tools

### Available Scripts

```bash
# Development workflow
./scripts/setup.sh    # Complete environment setup (macOS optimized)
./scripts/dev.sh      # Start development servers with hot reload
./scripts/build.sh    # Build for production deployment
./scripts/test.sh     # Run comprehensive test suite
./scripts/format.sh   # Format all code with Black/Prettier
./scripts/lint.sh     # Run all linting and quality checks
./scripts/clean.sh    # Clean all build artifacts and caches

# Docker commands
npm run docker:dev    # Start development with Docker
npm run docker:prod   # Start production with Docker
npm run docker:down   # Stop all Docker services

# Quick commands
npm run health        # Check if services are running
npm run logs          # View Docker logs
```

### VS Code Integration

The project includes comprehensive VS Code configuration:

- **Integrated Debugging**: Debug both frontend and backend simultaneously
- **Compound Launch Configurations**: Start full stack with one click
- **Intelligent Tasks**: Run common operations via Command Palette
- **Extensions Recommendations**: Auto-suggests essential extensions
- **Python Virtual Environment**: Automatically uses project's venv

**VS Code Tasks** (Cmd+Shift+P → Tasks: Run Task):
- 🛠️ Setup Development Environment
- 🚀 Start Development Servers
- 🏗️ Build Production
- 🧪 Run All Tests
- 🧹 Format Code
- 🔍 Lint Code
- 🐳 Docker Development
- 🧽 Clean All

## 📁 Project Structure

```
docsynapse/
├── frontend/                 # SvelteKit application
│   ├── src/
│   │   ├── lib/             # Components and utilities
│   │   └── routes/          # Application routes
│   └── package.json
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── api/             # API endpoints
│   │   ├── core/            # Configuration and utilities
│   │   ├── models/          # Pydantic models
│   │   └── services/        # Business logic services
│   └── requirements.txt
├── scripts/                  # Development and deployment scripts
│   ├── setup.sh             # Environment setup (macOS optimized)
│   ├── dev.sh               # Development servers
│   ├── build.sh             # Production build
│   ├── test.sh              # Test suite
│   ├── format.sh            # Code formatting
│   ├── lint.sh              # Code quality
│   └── clean.sh             # Cleanup utility
├── .vscode/                  # VS Code configuration
│   ├── settings.json        # Editor settings
│   ├── launch.json          # Debug configurations
│   ├── tasks.json           # Task definitions
│   └── extensions.json      # Recommended extensions
├── documentation/            # Implementation guides
├── docker-compose.yml        # Development Docker setup
├── .gitignore               # Git ignore rules
└── README.md
```

## 🛠️ Technology Stack

### Frontend
- **SvelteKit 2.0+** with Runes for reactivity
- **TailwindCSS** for styling
- **TypeScript** for type safety
- **WebSockets** for real-time updates

### Backend
- **FastAPI** for high-performance API
- **Playwright** for browser automation
- **Python 3.11+** with async/await
- **Pydantic** for data validation

### Infrastructure
- **Docker** for containerization
- **Redis** (optional) for job queues
- **Nginx** for reverse proxy

### Development Tools
- **Black** & **isort** for Python formatting
- **Prettier** & **ESLint** for frontend formatting
- **pytest** for Python testing
- **Vitest** for frontend testing
- **MyPy** for type checking
- **Pre-commit hooks** for code quality

## 🔧 Configuration

### Environment Variables

Create `.env` files in both frontend and backend directories:

**Backend (.env)**
```env
# Application Settings
APP_NAME=DocSynapse
DEBUG=True

# Crawler Settings
MAX_CONCURRENT_REQUESTS=5
REQUEST_DELAY=1.0
MAX_PAGES=1000

# Optional Redis
REDIS_URL=redis://localhost:6379
USE_REDIS=false
```

**Frontend (.env)**
```env
PUBLIC_API_BASE_URL=http://localhost:8000
PUBLIC_WS_BASE_URL=ws://localhost:8000
```

## 📚 Documentation

Comprehensive implementation guides are available in the [`documentation/`](./documentation/) directory:

- **[Project Guide](./documentation/01-project-guide.md)** - Setup and architecture overview
- **[Backend Implementation](./documentation/02-backend-implementation.md)** - FastAPI backend details
- **[Frontend Implementation](./documentation/03-frontend-implementation.md)** - SvelteKit frontend details
- **[Core Features](./documentation/04-core-features.md)** - Advanced crawling and processing
- **[Deployment & Testing](./documentation/05-deployment-testing.md)** - Production deployment guide

## 🧪 Testing

### Running Tests

```bash
# Run all tests
./scripts/test.sh

# Individual test suites
cd backend && pytest                    # Backend tests
cd frontend && npm run test            # Frontend tests

# With coverage
cd backend && pytest --cov=app        # Backend coverage
cd frontend && npm run test:coverage   # Frontend coverage

# End-to-end tests
npm run test:e2e

# Docker tests
docker-compose -f docker-compose.test.yml up
```

### Code Quality

```bash
# Format all code
./scripts/format.sh

# Lint all code
./scripts/lint.sh

# Pre-commit checks (automatic)
git commit -m "Your changes"  # Runs formatting and linting automatically
```

## 🚀 Deployment

### Docker Deployment
```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# With Redis for scaling
docker-compose -f docker-compose.prod.yml -f docker-compose.redis.yml up -d
```

### Cloud Deployment
- **AWS**: Use ECS or EC2 with the provided configurations
- **Google Cloud**: Deploy with Cloud Run or GKE
- **DigitalOcean**: Use App Platform or Droplets
- **Railway/Render**: Platform-as-a-Service deployment

See [deployment documentation](./documentation/05-deployment-testing.md) for detailed instructions.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](./CONTRIBUTING.md) for details.

### Development Workflow

1. **Fork** the repository
2. **Clone** your fork: `git clone https://github.com/yourusername/docsynapse.git`
3. **Setup** environment: `./scripts/setup.sh`
4. **Create** feature branch: `git checkout -b feature/amazing-feature`
5. **Develop** with hot reload: `./scripts/dev.sh`
6. **Test** your changes: `./scripts/test.sh`
7. **Format** code: `./scripts/format.sh`
8. **Commit** changes: `git commit -m 'Add amazing feature'`
9. **Push** to branch: `git push origin feature/amazing-feature`
10. **Open** a Pull Request

### Development Commands

```bash
# Quick development cycle
./scripts/dev.sh      # Start development servers
./scripts/test.sh     # Run tests
./scripts/format.sh   # Format code
./scripts/lint.sh     # Check code quality

# VS Code integration
# Use Cmd+Shift+P → Tasks: Run Task for GUI access to all scripts
```

## 🔧 Troubleshooting

### Common Issues

**Port already in use**
```bash
# Kill processes on ports 8000 and 5173
lsof -ti:8000,5173 | xargs kill -9
```

**Permission denied on scripts**
```bash
# Make scripts executable
chmod +x scripts/*.sh
```

**Python/Node version issues**
```bash
# Use setup script to install correct versions
./scripts/setup.sh
```

**Dependencies out of sync**
```bash
# Clean and reinstall everything
./scripts/clean.sh
./scripts/setup.sh
```

### macOS Specific

The project is optimized for macOS development with:
- Homebrew integration for dependency management
- M1/M2 Mac compatibility
- Proper PATH configuration for Apple Silicon
- macOS-specific file system optimizations

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Playwright** team for excellent browser automation
- **FastAPI** for the high-performance Python framework
- **SvelteKit** for the modern frontend framework
- **TailwindCSS** for utility-first styling
- Open source community for inspiration and support

## 📞 Support

- **Documentation**: Check the [documentation](./documentation/) directory
- **Issues**: [GitHub Issues](https://github.com/Zireael26/docsynapse/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Zireael26/docsynapse/discussions)
- **Email**: support@docsynapse.dev

## 🗺️ Roadmap

- [ ] **Authentication System** - User accounts and API keys
- [ ] **Batch Processing** - Process multiple documentation sites
- [ ] **Cloud Storage** - Integration with S3, GCS, and Azure Storage
- [ ] **API Integration** - RESTful API for programmatic access
- [ ] **Custom Templates** - Customizable output formats
- [ ] **Webhooks** - Notifications for job completion
- [ ] **Analytics Dashboard** - Usage statistics and insights
- [ ] **Browser Extension** - One-click documentation transformation
- [ ] **CLI Tool** - Command-line interface for automation
- [ ] **Kubernetes Operator** - Cloud-native deployment

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Zireael26/docsynapse&type=Date)](https://star-history.com/#Zireael26/docsynapse&Date)

---

<div align="center">

**Built with ❤️ for the AI and developer community**

**Author**: [Zireael26](https://github.com/Zireael26) | **Created**: July 1, 2025

[Website](https://docsynapse.dev) • [Documentation](./documentation/) • [Examples](./examples/) • [Blog](https://blog.docsynapse.dev)

</div>
