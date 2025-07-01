#!/bin/bash

# DocSynapse Production Build Script
# Builds both frontend and backend for production deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

# Function to show build stats
show_build_stats() {
    local path=$1
    local name=$2

    if [ -d "$path" ]; then
        local size=$(du -sh "$path" | cut -f1)
        local files=$(find "$path" -type f | wc -l | xargs)
        log_info "$name build size: $size ($files files)"
    fi
}

main() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                        DocSynapse Production Build                          ║"
    echo "║                        Building All Components                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    # Check if we're in the right directory
    if [ ! -f "README.md" ] || [ ! -d "frontend" ] || [ ! -d "backend" ]; then
        log_error "Please run this script from the DocSynapse root directory"
        exit 1
    fi

    # Clean previous builds
    log_info "Cleaning previous builds..."
    rm -rf frontend/build frontend/dist frontend/.svelte-kit
    rm -rf backend/dist backend/build
    log_success "Previous builds cleaned"

    # Build Backend
    log_info "Building FastAPI backend..."
    cd backend

    # Activate virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate

        # Create production requirements if not exists
        if [ ! -f "requirements-prod.txt" ]; then
            log_info "Creating production requirements..."
            cat > requirements-prod.txt << EOF
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
EOF
            log_success "Production requirements created"
        fi

        # Install production dependencies
        log_info "Installing production dependencies..."
        pip install -r requirements-prod.txt

        # Create build directory and copy necessary files
        mkdir -p dist
        cp -r app dist/
        cp requirements-prod.txt dist/
        cp .env.example dist/ 2>/dev/null || true

        # Create startup script
        cat > dist/start.sh << EOF
#!/bin/bash
# DocSynapse Production Startup Script

export PYTHONPATH=\$PYTHONPATH:/app
cd /app

# Install Playwright browsers if not present
if [ ! -d "/home/playwright" ]; then
    playwright install chromium
fi

# Start the application
exec uvicorn app.main:app --host 0.0.0.0 --port \${PORT:-8000} --workers \${WORKERS:-1}
EOF
        chmod +x dist/start.sh

        deactivate
        log_success "Backend build completed"
    else
        log_error "Backend virtual environment not found. Run ./scripts/setup.sh first."
        exit 1
    fi

    cd ..

    # Build Frontend
    log_info "Building SvelteKit frontend..."
    cd frontend

    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        log_error "Frontend dependencies not found. Run ./scripts/setup.sh first."
        exit 1
    fi

    # Create production environment file
    if [ ! -f ".env.production" ]; then
        log_info "Creating production environment file..."
        cat > .env.production << EOF
PUBLIC_API_BASE_URL=http://localhost:8000
PUBLIC_WS_BASE_URL=ws://localhost:8000
NODE_ENV=production
EOF
        log_success "Production environment file created"
    fi

    # Build the application
    log_info "Running SvelteKit build..."
    NODE_ENV=production npm run build

    # Check if build was successful
    if [ -d "build" ]; then
        log_success "Frontend build completed"
        show_build_stats "build" "Frontend"
    else
        log_error "Frontend build failed"
        exit 1
    fi

    cd ..

    # Create Docker images
    log_info "Building Docker images..."

    # Build backend Docker image
    if [ -f "backend/Dockerfile" ]; then
        log_info "Building backend Docker image..."
        docker build -t docsynapse-backend:latest ./backend
        log_success "Backend Docker image built"
    else
        log_warning "Backend Dockerfile not found, skipping Docker build"
    fi

    # Build frontend Docker image
    if [ -f "frontend/Dockerfile" ]; then
        log_info "Building frontend Docker image..."
        docker build -t docsynapse-frontend:latest ./frontend
        log_success "Frontend Docker image built"
    else
        log_warning "Frontend Dockerfile not found, skipping Docker build"
    fi

    # Create deployment package
    log_info "Creating deployment package..."
    mkdir -p dist/deployment

    # Copy built applications
    cp -r backend/dist dist/deployment/backend
    cp -r frontend/build dist/deployment/frontend

    # Copy deployment files
    cp docker-compose.prod.yml dist/deployment/ 2>/dev/null || cp docker-compose.yml dist/deployment/
    cp -r scripts dist/deployment/

    # Create deployment README
    cat > dist/deployment/README.md << EOF
# DocSynapse Production Deployment

This directory contains the production build of DocSynapse.

## Quick Start

1. **Docker Deployment (Recommended)**
   \`\`\`bash
   docker-compose up -d
   \`\`\`

2. **Manual Deployment**
   \`\`\`bash
   # Backend
   cd backend
   pip install -r requirements-prod.txt
   ./start.sh

   # Frontend (serve static files)
   cd frontend
   # Serve the 'build' directory with your web server
   \`\`\`

## Configuration

- Copy and modify \`.env.example\` files for your environment
- Update \`docker-compose.yml\` with your specific settings
- Configure reverse proxy if needed

## Services

- Backend API: Port 8000
- Frontend: Port 5173 (or serve statically)
- Redis (optional): Port 6379

Built on: $(date)
Version: $(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
EOF

    # Create archive
    if command -v tar >/dev/null 2>&1; then
        log_info "Creating deployment archive..."
        cd dist
        tar -czf docsynapse-$(date +%Y%m%d-%H%M%S).tar.gz deployment/
        cd ..
        log_success "Deployment archive created"
    fi

    # Show build summary
    echo ""
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                        🎉 Build Complete! 🎉                               ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    log_success "Production build completed successfully!"
    echo ""
    echo -e "${BLUE}📦 Build Artifacts:${NC}"
    echo "  • Backend build:     backend/dist/"
    echo "  • Frontend build:    frontend/build/"
    echo "  • Deployment package: dist/deployment/"
    echo "  • Docker images:     docsynapse-backend:latest, docsynapse-frontend:latest"

    show_build_stats "backend/dist" "Backend"
    show_build_stats "frontend/build" "Frontend"

    if [ -f "dist/docsynapse-"*".tar.gz" ]; then
        local archive=$(ls dist/docsynapse-*.tar.gz | head -1)
        local archive_size=$(du -sh "$archive" | cut -f1)
        echo "  • Deployment archive: $archive ($archive_size)"
    fi

    echo ""
    echo -e "${YELLOW}🚀 Next Steps:${NC}"
    echo "  1. Test the build locally: docker-compose -f docker-compose.prod.yml up"
    echo "  2. Deploy the dist/deployment/ directory to your server"
    echo "  3. Configure environment variables for production"
    echo "  4. Set up reverse proxy (nginx/caddy) if needed"
    echo ""
    log_info "Build artifacts are ready for deployment! 🎯"
}

# Run main function
main "$@"
