#!/bin/bash

# DocSynapse Development Server Script
# Starts both frontend and backend development servers concurrently

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

# Function to cleanup background processes
cleanup() {
    log_info "Shutting down development servers..."

    # Kill all background jobs
    jobs -p | xargs -r kill 2>/dev/null || true

    # Kill processes on specific ports if they're still running
    lsof -ti:8000 | xargs -r kill -9 2>/dev/null || true
    lsof -ti:5173 | xargs -r kill -9 2>/dev/null || true

    log_success "Development servers stopped"
    exit 0
}

# Trap signals to cleanup on exit
trap cleanup SIGINT SIGTERM EXIT

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null; then
        return 1
    else
        return 0
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1

    log_info "Waiting for $service_name to be ready..."

    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" >/dev/null 2>&1; then
            log_success "$service_name is ready!"
            return 0
        fi

        if [ $((attempt % 5)) -eq 0 ]; then
            log_info "Still waiting for $service_name... (attempt $attempt/$max_attempts)"
        fi

        sleep 1
        attempt=$((attempt + 1))
    done

    log_error "$service_name failed to start within expected time"
    return 1
}

main() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                        DocSynapse Development Mode                          ║"
    echo "║                          Starting All Services                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    # Check if we're in the right directory
    if [ ! -f "README.md" ] || [ ! -d "frontend" ] || [ ! -d "backend" ]; then
        log_error "Please run this script from the DocSynapse root directory"
        exit 1
    fi

    # Check if ports are available
    if ! check_port 8000; then
        log_error "Port 8000 is already in use. Please free the port and try again."
        log_info "You can kill the process with: lsof -ti:8000 | xargs kill -9"
        exit 1
    fi

    if ! check_port 5173; then
        log_error "Port 5173 is already in use. Please free the port and try again."
        log_info "You can kill the process with: lsof -ti:5173 | xargs kill -9"
        exit 1
    fi

    # Start Redis if available (optional)
    if command -v redis-server >/dev/null 2>&1; then
        if ! check_port 6379; then
            log_info "Redis is already running on port 6379"
        else
            log_info "Starting Redis server..."
            redis-server --daemonize yes --port 6379 >/dev/null 2>&1 || {
                log_warning "Could not start Redis server (this is optional)"
            }
        fi
    else
        log_info "Redis not found - continuing without caching (optional feature)"
    fi

    # Create log directory
    mkdir -p logs

    # Start Backend Server
    log_info "Starting FastAPI backend server..."
    cd backend

    # Activate virtual environment and start server
    if [ -d "venv" ]; then
        source venv/bin/activate

        # Start FastAPI server in background
        {
            echo -e "${CYAN}[BACKEND]${NC} Starting FastAPI server on http://localhost:8000"
            uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 2>&1 | while read line; do
                echo -e "${CYAN}[BACKEND]${NC} $line"
            done
        } &

        BACKEND_PID=$!
        echo $BACKEND_PID > ../logs/backend.pid

        deactivate
    else
        log_error "Backend virtual environment not found. Run ./scripts/setup.sh first."
        exit 1
    fi

    cd ..

    # Wait for backend to be ready
    wait_for_service "http://localhost:8000/health" "Backend API" || {
        log_error "Backend failed to start"
        exit 1
    }

    # Start Frontend Server
    log_info "Starting SvelteKit frontend server..."
    cd frontend

    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        log_error "Frontend dependencies not found. Run ./scripts/setup.sh first."
        exit 1
    fi

    # Start SvelteKit server in background
    {
        echo -e "${GREEN}[FRONTEND]${NC} Starting SvelteKit server on http://localhost:5173"
        npm run dev -- --host 0.0.0.0 --port 5173 2>&1 | while read line; do
            echo -e "${GREEN}[FRONTEND]${NC} $line"
        done
    } &

    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../logs/frontend.pid

    cd ..

    # Wait for frontend to be ready
    wait_for_service "http://localhost:5173" "Frontend App" || {
        log_error "Frontend failed to start"
        exit 1
    }

    # Display success message and URLs
    echo ""
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                     🚀 Development Servers Running! 🚀                     ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    log_success "All services are running!"
    echo ""
    echo -e "${BLUE}📱 Application URLs:${NC}"
    echo "  • Frontend:      http://localhost:5173"
    echo "  • Backend API:   http://localhost:8000"
    echo "  • API Docs:      http://localhost:8000/docs"
    echo "  • Redoc:         http://localhost:8000/redoc"
    echo ""
    echo -e "${YELLOW}🛠️  Development Tools:${NC}"
    echo "  • Hot reload enabled for both frontend and backend"
    echo "  • TypeScript checking active"
    echo "  • TailwindCSS with JIT compilation"
    echo "  • Python debugging available on port 8000"
    echo ""
    echo -e "${PURPLE}⌨️  Keyboard Shortcuts:${NC}"
    echo "  • Ctrl+C: Stop all servers"
    echo "  • Cmd+Click: Open URLs in browser"
    echo ""
    log_info "Watching for changes... Press Ctrl+C to stop all servers"

    # Open browser (optional)
    if command -v open >/dev/null 2>&1; then
        sleep 2
        log_info "Opening browser..."
        open http://localhost:5173
    fi

    # Keep script running and show logs
    echo ""
    echo -e "${CYAN}📋 Live Logs (Ctrl+C to stop):${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Wait for all background processes
    wait
}

# Run main function
main "$@"
