#!/bin/bash

# DocSynapse Code Formatting Script
# Formats all code using project standards

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

main() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                        DocSynapse Code Formatter                            ║"
    echo "║                        Formatting All Code                                  ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    # Check if we're in the right directory
    if [ ! -f "README.md" ] || [ ! -d "frontend" ] || [ ! -d "backend" ]; then
        log_error "Please run this script from the DocSynapse root directory"
        exit 1
    fi

    # Format Backend Code
    log_info "Formatting Python backend code..."
    cd backend

    if [ -d "venv" ]; then
        source venv/bin/activate

        # Install formatting tools if not present
        pip install black isort autoflake

        # Remove unused imports
        log_info "Removing unused imports..."
        autoflake --remove-all-unused-imports --recursive --in-place app/ tests/ || true

        # Sort imports
        log_info "Sorting imports..."
        isort app/ tests/ --profile=black

        # Format with Black
        log_info "Formatting with Black..."
        black app/ tests/ --line-length=88

        log_success "Backend code formatted!"
        deactivate
    else
        log_error "Backend virtual environment not found. Run ./scripts/setup.sh first."
        exit 1
    fi

    cd ..

    # Format Frontend Code
    log_info "Formatting frontend code..."
    cd frontend

    if [ -d "node_modules" ]; then
        # Install Prettier if not present
        if ! command -v prettier >/dev/null 2>&1; then
            npm install --save-dev prettier
        fi

        # Format with Prettier
        log_info "Formatting with Prettier..."
        npx prettier --write src/ --config .prettierrc 2>/dev/null || npx prettier --write src/

        # Format package.json
        npx prettier --write package.json

        log_success "Frontend code formatted!"
    else
        log_error "Frontend dependencies not found. Run ./scripts/setup.sh first."
        exit 1
    fi

    cd ..

    # Format Configuration Files
    log_info "Formatting configuration files..."

    # Format JSON files
    if command -v jq >/dev/null 2>&1; then
        find . -name "*.json" -not -path "*/node_modules/*" -not -path "*/venv/*" -exec sh -c 'jq . "$1" > "$1.tmp" && mv "$1.tmp" "$1"' _ {} \; 2>/dev/null || true
        log_success "JSON files formatted"
    else
        log_info "jq not found, skipping JSON formatting"
    fi

    # Format Docker files (basic cleanup)
    find . -name "Dockerfile*" -exec sed -i.bak 's/[[:space:]]*$//' {} \; -exec rm {}.bak \; 2>/dev/null || true
    find . -name "docker-compose*.yml" -exec sed -i.bak 's/[[:space:]]*$//' {} \; -exec rm {}.bak \; 2>/dev/null || true

    log_success "Configuration files formatted"

    # Format Shell Scripts
    log_info "Formatting shell scripts..."
    if command -v shfmt >/dev/null 2>&1; then
        find scripts/ -name "*.sh" -exec shfmt -w -i 4 {} \;
        log_success "Shell scripts formatted with shfmt"
    else
        # Basic shell script cleanup
        find scripts/ -name "*.sh" -exec sed -i.bak 's/[[:space:]]*$//' {} \; -exec rm {}.bak \; 2>/dev/null || true
        log_info "Basic shell script cleanup done (install shfmt for better formatting)"
    fi

    # Format Markdown files
    if command -v prettier >/dev/null 2>&1; then
        log_info "Formatting Markdown files..."
        npx prettier --write "*.md" "documentation/*.md" 2>/dev/null || true
        log_success "Markdown files formatted"
    fi

    # Display completion message
    echo ""
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                        🎨 Formatting Complete! 🎨                          ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    log_success "All code has been formatted according to project standards!"
    echo ""
    echo -e "${BLUE}📝 What was formatted:${NC}"
    echo "  • Python code with Black (88 char line length)"
    echo "  • Python imports with isort (Black-compatible profile)"
    echo "  • JavaScript/TypeScript/Svelte with Prettier"
    echo "  • JSON configuration files"
    echo "  • Markdown documentation"
    echo "  • Shell scripts and Docker files"
    echo ""
    echo -e "${YELLOW}💡 Pro Tips:${NC}"
    echo "  • Configure your editor to format on save"
    echo "  • Run this script before committing changes"
    echo "  • Consider setting up pre-commit hooks"
    echo ""
    log_info "Happy coding with beautifully formatted code! ✨"
}

# Run main function
main "$@"
