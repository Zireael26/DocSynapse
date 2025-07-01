#!/bin/bash

# DocSynapse Testing Script
# Runs all tests for both frontend and backend

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

# Test results tracking
BACKEND_TESTS_PASSED=false
FRONTEND_TESTS_PASSED=false
LINT_PASSED=false

main() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                        DocSynapse Test Suite                                ║"
    echo "║                        Running All Tests                                    ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    # Check if we're in the right directory
    if [ ! -f "README.md" ] || [ ! -d "frontend" ] || [ ! -d "backend" ]; then
        log_error "Please run this script from the DocSynapse root directory"
        exit 1
    fi

    # Create test results directory
    mkdir -p test-results

    # Run Backend Tests
    log_info "Running backend tests..."
    cd backend

    if [ -d "venv" ]; then
        source venv/bin/activate

        # Install test dependencies if not present
        pip install pytest pytest-asyncio pytest-cov pytest-mock httpx

        # Run tests with coverage
        log_info "Running Python unit tests..."
        if pytest tests/ -v --cov=app --cov-report=html --cov-report=term --cov-report=xml --junitxml=../test-results/backend-results.xml; then
            BACKEND_TESTS_PASSED=true
            log_success "Backend tests passed!"
        else
            log_error "Backend tests failed!"
        fi

        # Type checking with mypy
        log_info "Running type checking..."
        if command -v mypy >/dev/null 2>&1; then
            if mypy app/ --ignore-missing-imports; then
                log_success "Type checking passed!"
            else
                log_warning "Type checking found issues"
            fi
        else
            log_warning "mypy not installed, skipping type checking"
        fi

        deactivate
    else
        log_error "Backend virtual environment not found. Run ./scripts/setup.sh first."
    fi

    cd ..

    # Run Frontend Tests
    log_info "Running frontend tests..."
    cd frontend

    if [ -d "node_modules" ]; then
        # Install test dependencies if not present
        npm install --save-dev vitest @testing-library/svelte @testing-library/jest-dom jsdom

        # Run unit tests
        log_info "Running JavaScript/TypeScript unit tests..."
        if npm run test 2>/dev/null || npx vitest run; then
            FRONTEND_TESTS_PASSED=true
            log_success "Frontend tests passed!"
        else
            log_error "Frontend tests failed!"
        fi

        # Type checking
        log_info "Running TypeScript checking..."
        if npx tsc --noEmit; then
            log_success "TypeScript checking passed!"
        else
            log_warning "TypeScript checking found issues"
        fi

    else
        log_error "Frontend dependencies not found. Run ./scripts/setup.sh first."
    fi

    cd ..

    # Linting and Code Quality
    log_info "Running code quality checks..."

    # Backend linting
    log_info "Checking backend code quality..."
    cd backend

    if [ -d "venv" ]; then
        source venv/bin/activate

        # Install linting tools if not present
        pip install black isort flake8 mypy

        # Check formatting
        if black --check app/ tests/; then
            log_success "Backend code formatting is correct"
        else
            log_warning "Backend code needs formatting (run ./scripts/format.sh)"
        fi

        # Check import sorting
        if isort --check-only app/ tests/; then
            log_success "Backend imports are sorted correctly"
        else
            log_warning "Backend imports need sorting (run ./scripts/format.sh)"
        fi

        # Flake8 linting
        if flake8 app/ tests/ --max-line-length=88 --extend-ignore=E203,W503; then
            log_success "Backend linting passed"
            LINT_PASSED=true
        else
            log_warning "Backend linting found issues"
        fi

        deactivate
    fi

    cd ..

    # Frontend linting
    log_info "Checking frontend code quality..."
    cd frontend

    if [ -d "node_modules" ]; then
        # Check if we have ESLint configured
        if [ -f ".eslintrc.js" ] || [ -f ".eslintrc.json" ] || [ -f "eslint.config.js" ]; then
            if npm run lint 2>/dev/null || npx eslint src/; then
                log_success "Frontend linting passed"
            else
                log_warning "Frontend linting found issues"
            fi
        else
            log_info "ESLint not configured, skipping frontend linting"
        fi

        # Check formatting with Prettier if available
        if command -v prettier >/dev/null 2>&1; then
            if prettier --check src/; then
                log_success "Frontend code formatting is correct"
            else
                log_warning "Frontend code needs formatting (run ./scripts/format.sh)"
            fi
        else
            log_info "Prettier not found, skipping format checking"
        fi
    fi

    cd ..

    # Integration Tests (if available)
    if [ -f "tests/integration/test_api.py" ]; then
        log_info "Running integration tests..."
        cd tests/integration
        if python -m pytest -v; then
            log_success "Integration tests passed!"
        else
            log_warning "Integration tests failed"
        fi
        cd ../..
    fi

    # Generate Test Report
    log_info "Generating test report..."
    cat > test-results/summary.md << EOF
# DocSynapse Test Results

Generated on: $(date)

## Test Summary

- **Backend Tests**: $([ "$BACKEND_TESTS_PASSED" = true ] && echo "✅ PASSED" || echo "❌ FAILED")
- **Frontend Tests**: $([ "$FRONTEND_TESTS_PASSED" = true ] && echo "✅ PASSED" || echo "❌ FAILED")
- **Code Quality**: $([ "$LINT_PASSED" = true ] && echo "✅ PASSED" || echo "⚠️  ISSUES FOUND")

## Coverage Reports

- Backend coverage: \`backend/htmlcov/index.html\`
- Frontend coverage: Available after running \`npm run test:coverage\`

## Next Steps

$(if [ "$BACKEND_TESTS_PASSED" = false ] || [ "$FRONTEND_TESTS_PASSED" = false ]; then
    echo "- Fix failing tests before deploying"
fi)
$(if [ "$LINT_PASSED" = false ]; then
    echo "- Run \`./scripts/format.sh\` to fix code formatting issues"
    echo "- Address linting issues manually where needed"
fi)
$(if [ "$BACKEND_TESTS_PASSED" = true ] && [ "$FRONTEND_TESTS_PASSED" = true ] && [ "$LINT_PASSED" = true ]; then
    echo "- All tests passed! Ready for deployment 🚀"
fi)
EOF

    # Display Results
    echo ""
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                        📊 Test Results Summary                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    echo -e "${BLUE}🧪 Test Results:${NC}"
    echo "  • Backend Tests:    $([ "$BACKEND_TESTS_PASSED" = true ] && echo -e "${GREEN}✅ PASSED${NC}" || echo -e "${RED}❌ FAILED${NC}")"
    echo "  • Frontend Tests:   $([ "$FRONTEND_TESTS_PASSED" = true ] && echo -e "${GREEN}✅ PASSED${NC}" || echo -e "${RED}❌ FAILED${NC}")"
    echo "  • Code Quality:     $([ "$LINT_PASSED" = true ] && echo -e "${GREEN}✅ PASSED${NC}" || echo -e "${YELLOW}⚠️  ISSUES FOUND${NC}")"

    echo ""
    echo -e "${BLUE}📁 Test Artifacts:${NC}"
    echo "  • Test summary:     test-results/summary.md"
    echo "  • Backend coverage: backend/htmlcov/index.html"
    echo "  • Test results:     test-results/backend-results.xml"

    if [ "$BACKEND_TESTS_PASSED" = true ] && [ "$FRONTEND_TESTS_PASSED" = true ] && [ "$LINT_PASSED" = true ]; then
        echo ""
        log_success "All tests passed! 🎉 Ready for deployment!"
        exit 0
    else
        echo ""
        log_warning "Some tests failed or issues were found. Please review and fix before deploying."
        exit 1
    fi
}

# Run main function
main "$@"
