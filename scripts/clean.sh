#!/bin/bash

# DocSynapse Cleanup Script
# Cleans all build artifacts, caches, and temporary files

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

# Function to safely remove directory/file
safe_remove() {
    local path=$1
    local desc=$2

    if [ -e "$path" ]; then
        rm -rf "$path"
        log_success "Removed $desc"
    else
        log_info "$desc not found (already clean)"
    fi
}

# Function to show space saved
show_space_saved() {
    local space_before=$1
    local space_after=$(df -h . | tail -1 | awk '{print $3}')

    # Note: This is a simplified calculation
    log_info "Cleanup completed - temporary files and caches removed"
}

main() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                        DocSynapse Cleanup Utility                           ║"
    echo "║                        Cleaning All Artifacts                               ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    # Check if we're in the right directory
    if [ ! -f "README.md" ] || [ ! -d "frontend" ] || [ ! -d "backend" ]; then
        log_error "Please run this script from the DocSynapse root directory"
        exit 1
    fi

    # Get initial disk usage
    local space_before=$(df -h . | tail -1 | awk '{print $3}')

    # Stop any running development servers
    log_info "Stopping any running development servers..."
    lsof -ti:8000 | xargs -r kill -9 2>/dev/null || true
    lsof -ti:5173 | xargs -r kill -9 2>/dev/null || true
    lsof -ti:6379 | xargs -r kill -9 2>/dev/null || true
    log_success "Development servers stopped"

    # Clean Backend
    log_info "Cleaning backend artifacts..."
    cd backend

    safe_remove "__pycache__" "Python cache directories"
    safe_remove "*.pyc" "Python compiled files"
    safe_remove "*.pyo" "Python optimized files"
    safe_remove ".pytest_cache" "Pytest cache"
    safe_remove ".coverage" "Coverage data"
    safe_remove "htmlcov" "Coverage HTML reports"
    safe_remove ".mypy_cache" "MyPy cache"
    safe_remove "dist" "Distribution directory"
    safe_remove "build" "Build directory"
    safe_remove "*.egg-info" "Egg info directories"
    safe_remove "output/*" "Generated documentation files"
    safe_remove "logs/*" "Log files"

    # Clean Python cache recursively
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "*.pyo" -delete 2>/dev/null || true
    find . -name "*.pyd" -delete 2>/dev/null || true

    cd ..

    # Clean Frontend
    log_info "Cleaning frontend artifacts..."
    cd frontend

    safe_remove "node_modules" "Node.js dependencies (will need reinstall)"
    safe_remove "build" "SvelteKit build directory"
    safe_remove "dist" "Distribution directory"
    safe_remove ".svelte-kit" "SvelteKit cache"
    safe_remove ".turbo" "Turbo cache"
    safe_remove "coverage" "Test coverage reports"
    safe_remove "playwright-report" "Playwright test reports"
    safe_remove "test-results" "Test result files"

    # Clean package manager caches
    if [ -d ".npm" ]; then
        safe_remove ".npm" "NPM cache"
    fi

    cd ..

    # Clean Root Directory
    log_info "Cleaning root directory artifacts..."
    safe_remove "dist" "Root distribution directory"
    safe_remove "test-results" "Test results directory"
    safe_remove "logs" "Log directory"
    safe_remove ".DS_Store" "macOS system files"

    # Clean Docker artifacts (optional)
    if command -v docker >/dev/null 2>&1; then
        log_info "Cleaning Docker artifacts..."

        # Remove DocSynapse containers
        docker ps -a --format "table {{.Names}}" | grep -E "(docsynapse|frontend|backend)" | xargs -r docker rm -f 2>/dev/null || true

        # Remove DocSynapse images
        docker images --format "table {{.Repository}}:{{.Tag}}" | grep docsynapse | xargs -r docker rmi -f 2>/dev/null || true

        # Clean up dangling images and volumes
        docker image prune -f 2>/dev/null || true
        docker volume prune -f 2>/dev/null || true

        log_success "Docker artifacts cleaned"
    else
        log_info "Docker not found, skipping Docker cleanup"
    fi

    # Clean temporary files
    log_info "Cleaning temporary files..."
    find . -name "*.tmp" -delete 2>/dev/null || true
    find . -name "*.temp" -delete 2>/dev/null || true
    find . -name "*.bak" -delete 2>/dev/null || true
    find . -name "*.orig" -delete 2>/dev/null || true
    find . -name "*~" -delete 2>/dev/null || true
    find . -name ".DS_Store" -delete 2>/dev/null || true

    # Clean IDE files (optional)
    read -p "$(echo -e ${YELLOW}Do you want to clean IDE configuration files? [y/N]:${NC} )" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        safe_remove ".vscode/settings.json" "VS Code settings (will reset to defaults)"
        safe_remove ".idea" "IntelliJ IDEA configuration"
        log_warning "IDE configurations cleaned - you may need to reconfigure your editor"
    fi

    # Clean Git artifacts (be very careful)
    read -p "$(echo -e ${YELLOW}Do you want to clean Git cache and untracked files? [y/N]:${NC} )" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git clean -fd 2>/dev/null || true
        git gc --prune=now 2>/dev/null || true
        log_success "Git cache cleaned and untracked files removed"
    fi

    # Reset file permissions (macOS specific)
    log_info "Resetting file permissions..."
    chmod +x scripts/*.sh 2>/dev/null || true
    log_success "Script permissions reset"

    # Final summary
    echo ""
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                        🧹 Cleanup Complete! 🧹                             ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    log_success "DocSynapse cleanup completed successfully!"
    echo ""
    echo -e "${BLUE}🗑️  What was cleaned:${NC}"
    echo "  • Python cache files and directories (__pycache__, *.pyc)"
    echo "  • Node.js build artifacts and caches"
    echo "  • Test results and coverage reports"
    echo "  • Generated documentation files"
    echo "  • Log files and temporary files"
    echo "  • Docker containers and images (DocSynapse related)"
    echo "  • System files (.DS_Store, backup files)"
    echo ""
    echo -e "${YELLOW}⚠️  What you may need to do next:${NC}"
    echo "  • Run './scripts/setup.sh' to reinstall dependencies"
    echo "  • Reconfigure your IDE if you cleaned configuration files"
    echo "  • Restart Docker Desktop if you cleaned Docker artifacts"
    echo ""
    echo -e "${GREEN}💡 Pro Tip:${NC} Regular cleanup keeps your development environment fast and clean!"

    show_space_saved "$space_before"
}

# Run main function
main "$@"
