#!/bin/bash

# DocSynapse Linting Script
# Runs all linting and code quality checks

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

# Track results
BACKEND_LINT_PASSED=true
FRONTEND_LINT_PASSED=true
OVERALL_PASSED=true

main() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                        DocSynapse Code Quality Check                        ║"
    echo "║                        Running All Linters                                  ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    # Check if we're in the right directory
    if [ ! -f "README.md" ] || [ ! -d "frontend" ] || [ ! -d "backend" ]; then
        log_error "Please run this script from the DocSynapse root directory"
        exit 1
    fi

    # Lint Backend
    log_info "Linting Python backend code..."
    cd backend

    if [ -d "venv" ]; then
        source venv/bin/activate

        # Install linting tools if not present
        pip install black isort flake8 mypy bandit safety

        # Check code formatting
        log_info "Checking Python code formatting..."
        if ! black --check app/ tests/ --diff; then
            log_error "Code formatting issues found - run './scripts/format.sh'"
            BACKEND_LINT_PASSED=false
        else
            log_success "Python code formatting is correct"
        fi

        # Check import sorting
        log_info "Checking import sorting..."
        if ! isort --check-only app/ tests/ --diff; then
            log_error "Import sorting issues found - run './scripts/format.sh'"
            BACKEND_LINT_PASSED=false
        else
            log_success "Python imports are sorted correctly"
        fi

        # Flake8 linting
        log_info "Running flake8 linting..."
        if ! flake8 app/ tests/ --max-line-length=88 --extend-ignore=E203,W503; then
            log_error "Flake8 linting issues found"
            BACKEND_LINT_PASSED=false
        else
            log_success "Flake8 linting passed"
        fi

        # Type checking with mypy
        log_info "Running type checking..."
        if ! mypy app/ --ignore-missing-imports --strict-optional; then
            log_warning "Type checking found issues (non-blocking)"
        else
            log_success "Type checking passed"
        fi

        # Security check with bandit
        log_info "Running security analysis..."
        if ! bandit -r app/ -ll; then
            log_warning "Security analysis found potential issues"
        else
            log_success "Security analysis passed"
        fi

        # Dependency security check
        log_info "Checking dependency security..."
        if ! safety check --json > /dev/null 2>&1; then
            log_warning "Dependency security check found issues"
        else
            log_success "Dependency security check passed"
        fi

        deactivate
    else
        log_error "Backend virtual environment not found. Run ./scripts/setup.sh first."
        BACKEND_LINT_PASSED=false
    fi

    cd ..

    # Lint Frontend
    log_info "Linting frontend code..."
    cd frontend

    if [ -d "node_modules" ]; then
        # Install linting tools if not present
        if [ ! -f ".eslintrc.js" ] && [ ! -f ".eslintrc.json" ] && [ ! -f "eslint.config.js" ]; then
            log_info "Setting up ESLint configuration..."
            npm install --save-dev eslint @typescript-eslint/eslint-plugin @typescript-eslint/parser eslint-plugin-svelte3

            cat > .eslintrc.json << 'EOF'
{
  "root": true,
  "extends": [
    "eslint:recommended",
    "@typescript-eslint/recommended"
  ],
  "parser": "@typescript-eslint/parser",
  "plugins": ["@typescript-eslint", "svelte3"],
  "overrides": [
    {
      "files": ["*.svelte"],
      "processor": "svelte3/svelte3"
    }
  ],
  "parserOptions": {
    "sourceType": "module",
    "ecmaVersion": 2020
  },
  "env": {
    "browser": true,
    "es2017": true,
    "node": true
  }
}
EOF
        fi

        # ESLint checking
        log_info "Running ESLint..."
        if ! npx eslint src/ --ext .js,.ts,.svelte; then
            log_error "ESLint found issues"
            FRONTEND_LINT_PASSED=false
        else
            log_success "ESLint passed"
        fi

        # TypeScript checking
        log_info "Running TypeScript checking..."
        if ! npx tsc --noEmit; then
            log_error "TypeScript checking found issues"
            FRONTEND_LINT_PASSED=false
        else
            log_success "TypeScript checking passed"
        fi

        # Prettier formatting check
        if command -v prettier >/dev/null 2>&1; then
            log_info "Checking code formatting..."
            if ! npx prettier --check src/; then
                log_error "Code formatting issues found - run './scripts/format.sh'"
                FRONTEND_LINT_PASSED=false
            else
                log_success "Code formatting is correct"
            fi
        fi

        # Package.json validation
        log_info "Validating package.json..."
        if ! npm ls --depth=0 > /dev/null 2>&1; then
            log_warning "Package.json validation found issues"
        else
            log_success "Package.json is valid"
        fi

        # Audit dependencies
        log_info "Auditing dependencies..."
        if ! npm audit --audit-level=high; then
            log_warning "Dependency audit found issues"
        else
            log_success "Dependency audit passed"
        fi

    else
        log_error "Frontend dependencies not found. Run ./scripts/setup.sh first."
        FRONTEND_LINT_PASSED=false
    fi

    cd ..

    # Additional project-wide checks
    log_info "Running project-wide checks..."

    # Check for TODO/FIXME comments
    log_info "Checking for TODO/FIXME comments..."
    if grep -r "TODO\|FIXME" --include="*.py" --include="*.js" --include="*.ts" --include="*.svelte" . | head -10; then
        log_info "Found TODO/FIXME comments (review recommended)"
    else
        log_success "No TODO/FIXME comments found"
    fi

    # Check for console.log statements
    log_info "Checking for console.log statements..."
    if grep -r "console\.log" --include="*.js" --include="*.ts" --include="*.svelte" frontend/src/ 2>/dev/null; then
        log_warning "Found console.log statements - consider using proper logging"
    else
        log_success "No console.log statements found"
    fi

    # Check for hardcoded URLs/secrets
    log_info "Checking for potential hardcoded secrets..."
    if grep -r -i "password\|secret\|key\|token" --include="*.py" --include="*.js" --include="*.ts" --exclude-dir=node_modules --exclude-dir=venv . | grep -v "# " | head -5; then
        log_warning "Found potential hardcoded secrets - please review"
    else
        log_success "No obvious hardcoded secrets found"
    fi

    # Markdown linting
    if command -v markdownlint >/dev/null 2>&1; then
        log_info "Linting Markdown files..."
        if ! markdownlint README.md documentation/*.md; then
            log_warning "Markdown linting found issues"
        else
            log_success "Markdown linting passed"
        fi
    fi

    # Final assessment
    if [ "$BACKEND_LINT_PASSED" = false ]; then
        OVERALL_PASSED=false
    fi

    if [ "$FRONTEND_LINT_PASSED" = false ]; then
        OVERALL_PASSED=false
    fi

    # Display Results
    echo ""
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                        📋 Linting Results Summary                           ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    echo -e "${BLUE}🔍 Linting Results:${NC}"
    echo "  • Backend Linting:  $([ "$BACKEND_LINT_PASSED" = true ] && echo -e "${GREEN}✅ PASSED${NC}" || echo -e "${RED}❌ FAILED${NC}")"
    echo "  • Frontend Linting: $([ "$FRONTEND_LINT_PASSED" = true ] && echo -e "${GREEN}✅ PASSED${NC}" || echo -e "${RED}❌ FAILED${NC}")"
    echo "  • Overall Status:   $([ "$OVERALL_PASSED" = true ] && echo -e "${GREEN}✅ PASSED${NC}" || echo -e "${RED}❌ FAILED${NC}")"

    echo ""
    if [ "$OVERALL_PASSED" = true ]; then
        log_success "All linting checks passed! 🎉 Code quality looks great!"
        echo ""
        echo -e "${GREEN}💡 Your code meets all quality standards!${NC}"
    else
        log_error "Some linting checks failed. Please address the issues above."
        echo ""
        echo -e "${YELLOW}🛠️  Quick fixes:${NC}"
        echo "  • Run './scripts/format.sh' to fix formatting issues"
        echo "  • Review and fix linting errors manually"
        echo "  • Check for hardcoded secrets and TODO comments"
        echo "  • Update dependencies if audit found vulnerabilities"
    fi

    # Exit with appropriate code
    if [ "$OVERALL_PASSED" = true ]; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"
