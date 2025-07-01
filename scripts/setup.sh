#!/bin/bash

# DocSynapse Development Environment Setup Script for macOS
# Author: Zireael26
# Date: 2025-07-01

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    if command_exists python3; then
        local version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        local required="3.11"
        if [ "$(printf '%s\n' "$required" "$version" | sort -V | head -n1)" = "$required" ]; then
            return 0
        fi
    fi
    return 1
}

# Function to check Node.js version
check_node_version() {
    if command_exists node; then
        local version=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
        if [ "$version" -ge 18 ]; then
            return 0
        fi
    fi
    return 1
}

# Main setup function
main() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                        DocSynapse Development Setup                          ║"
    echo "║                              macOS Edition                                   ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    # Check if we're in the right directory
    if [ ! -f "README.md" ] || [ ! -d "frontend" ] || [ ! -d "backend" ]; then
        log_error "Please run this script from the DocSynapse root directory"
        exit 1
    fi

    log_info "Starting development environment setup..."

    # Check prerequisites
    log_info "Checking prerequisites..."

    # Check Homebrew
    if ! command_exists brew; then
        log_warning "Homebrew not found. Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        # Add Homebrew to PATH for M1/M2 Macs
        if [[ $(uname -m) == "arm64" ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
        log_success "Homebrew installed"
    else
        log_success "Homebrew found"
    fi

    # Check Python
    if ! check_python_version; then
        log_warning "Python 3.11+ not found. Installing Python..."
        brew install python@3.11
        # Update PATH to use the new Python
        export PATH="/opt/homebrew/bin:$PATH"
        log_success "Python 3.11 installed"
    else
        log_success "Python 3.11+ found: $(python3 --version)"
    fi

    # Check Node.js
    if ! check_node_version; then
        log_warning "Node.js 18+ not found. Installing Node.js..."
        brew install node@18
        # Update PATH to use the new Node.js
        export PATH="/opt/homebrew/opt/node@18/bin:$PATH"
        log_success "Node.js 18 installed"
    else
        log_success "Node.js $(node --version) found"
    fi

    # Check Docker
    if ! command_exists docker; then
        log_warning "Docker not found. Please install Docker Desktop from:"
        log_warning "https://docs.docker.com/desktop/install/mac-install/"
        log_warning "After installation, restart this script."
        read -p "Press Enter after installing Docker Desktop..."
    else
        log_success "Docker found: $(docker --version)"
    fi

    # Setup Backend
    log_info "Setting up Python backend..."
    cd backend

    # Create virtual environment
    if [ ! -d "venv" ]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv venv
        log_success "Virtual environment created"
    else
        log_success "Virtual environment already exists"
    fi

    # Activate virtual environment and install dependencies
    log_info "Installing Python dependencies..."
    source venv/bin/activate

    # Upgrade pip
    pip install --upgrade pip

    # Install requirements
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log_success "Python dependencies installed"
    else
        log_warning "requirements.txt not found, creating basic requirements..."
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
        pip install -r requirements.txt
        log_success "Basic Python dependencies installed"
    fi

    # Install Playwright browsers
    log_info "Installing Playwright browsers..."
    playwright install
    log_success "Playwright browsers installed"

    # Create environment file if it doesn't exist
    if [ ! -f ".env" ]; then
        log_info "Creating backend .env file..."
        cat > .env << EOF
# Application Settings
APP_NAME=DocSynapse
APP_VERSION=1.0.0
DEBUG=True

# Server Settings
HOST=0.0.0.0
PORT=8000

# CORS Settings
ALLOWED_ORIGINS=["http://localhost:5173", "http://localhost:3000"]

# Crawler Settings
MAX_CONCURRENT_REQUESTS=5
REQUEST_DELAY=1.0
TIMEOUT=30
MAX_PAGES=1000
USER_AGENT=DocSynapse/1.0 (+https://github.com/docsynapse/docsynapse)

# File Settings
MAX_FILE_SIZE=100MB
OUTPUT_DIR=./output

# Redis Settings (optional)
REDIS_URL=redis://localhost:6379
USE_REDIS=False

# Playwright Settings
HEADLESS=True
BROWSER_TYPE=chromium
EOF
        log_success "Backend .env file created"
    else
        log_success "Backend .env file already exists"
    fi

    # Create output directory
    mkdir -p output
    mkdir -p logs

    deactivate
    cd ..

    # Setup Frontend
    log_info "Setting up SvelteKit frontend..."
    cd frontend

    # Check if package.json exists
    if [ ! -f "package.json" ]; then
        log_info "Initializing SvelteKit project..."
        npm create svelte@latest . --template skeleton --types typescript --no-eslint --no-prettier --no-playwright --no-vitest
    fi

    # Install dependencies
    log_info "Installing Node.js dependencies..."
    npm install

    # Install additional dependencies
    log_info "Installing additional frontend dependencies..."
    npm install tailwindcss @tailwindcss/typography @tailwindcss/forms autoprefixer
    npm install @types/node
    npm install -D @tailwindcss/typography @tailwindcss/forms

    # Initialize Tailwind if not exists
    if [ ! -f "tailwind.config.js" ]; then
        log_info "Initializing TailwindCSS..."
        npx tailwindcss init -p
        log_success "TailwindCSS initialized"
    fi

    # Create environment file if it doesn't exist
    if [ ! -f ".env" ]; then
        log_info "Creating frontend .env file..."
        cat > .env << EOF
# API Configuration
PUBLIC_API_BASE_URL=http://localhost:8000
PUBLIC_WS_BASE_URL=ws://localhost:8000
EOF
        log_success "Frontend .env file created"
    else
        log_success "Frontend .env file already exists"
    fi

    cd ..

    # Make scripts executable
    log_info "Making scripts executable..."
    chmod +x scripts/*.sh
    log_success "Scripts are now executable"

    # Final success message
    echo ""
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                          🎉 Setup Complete! 🎉                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    log_success "DocSynapse development environment is ready!"
    echo ""
    log_info "Next steps:"
    echo "  1. Run './scripts/dev.sh' to start development servers"
    echo "  2. Open http://localhost:5173 for the frontend"
    echo "  3. Open http://localhost:8000/docs for the API documentation"
    echo "  4. Use VS Code tasks (Cmd+Shift+P > Tasks: Run Task) for common operations"
    echo ""
    log_info "Available scripts:"
    echo "  • ./scripts/dev.sh       - Start development servers"
    echo "  • ./scripts/build.sh     - Build for production"
    echo "  • ./scripts/test.sh      - Run all tests"
    echo "  • ./scripts/format.sh    - Format all code"
    echo "  • ./scripts/lint.sh      - Lint all code"
    echo "  • ./scripts/clean.sh     - Clean build artifacts"
    echo ""
    log_info "Happy coding! 🚀"
}

# Run main function
main "$@"
