# Running Tests - Quick Reference

Quick command reference for running tests in the Thurup project.

For detailed testing documentation, see [TESTING_GUIDE.md](./TESTING_GUIDE.md).

---

## Backend Tests (pytest)

### Run All Tests

```bash
cd backend
uv run pytest -v
```

### Run by Type

```bash
# Unit tests only
uv run pytest tests/unit/ -v

# Integration tests only
uv run pytest tests/integration/ -v

# E2E tests (requires running server on port 8000)
uv run pytest tests/e2e/ -v -s
```

### Run Specific Tests

```bash
# Specific file
uv run pytest tests/unit/test_bidding.py -v

# Specific test
uv run pytest tests/unit/test_bidding.py::test_sequential_bidding -v

# By keyword
uv run pytest -k "bidding" -v
```

### Coverage

```bash
# Run with coverage report
uv run pytest --cov=app --cov-report=term-missing

# Generate HTML coverage report
uv run pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

### Debugging

```bash
# Show print statements
uv run pytest -v -s

# Stop at first failure
uv run pytest -x

# Drop into debugger on failure
uv run pytest --pdb

# Show full traceback
uv run pytest --tb=long

# Re-run last failed tests
uv run pytest --lf
```

---

## Frontend Tests

### Unit & Component Tests (Vitest)

```bash
cd frontend

# Run all tests
npm test

# Run in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage

# Run specific test
npm test -- Badge.test.tsx
```

### E2E Tests (Playwright)

**Prerequisites**: Backend must be running on port 18081

```bash
cd frontend

# Run all E2E tests (headless)
npm run test:e2e

# Run with UI mode (interactive, recommended for development)
npm run test:e2e:ui

# Run in headed mode (see browser)
npm run test:e2e:headed

# Run in debug mode
npm run test:e2e:debug
```

### Run Specific E2E Tests

```bash
# Specific file
npx playwright test home-page.spec.ts

# Specific test by name
npx playwright test --grep "can create a new game"

# Run in specific browser
npx playwright test --project=chromium
```

### E2E Debugging

```bash
# View test report
npx playwright show-report

# View trace file
npx playwright show-trace test-results/.../trace.zip
```

---

## Common Workflows

### Full Test Suite

```bash
# Terminal 1: Start backend
cd backend
uv run uvicorn app.main:app --reload --port 18081

# Terminal 2: Run backend tests
cd backend
uv run pytest -v

# Terminal 3: Run frontend tests
cd frontend
npm test
npm run test:e2e
```

### Before Committing

```bash
# Run backend tests with coverage
cd backend
uv run pytest --cov=app --cov-report=term-missing

# Run frontend tests
cd frontend
npm test
```

### CI/CD Simulation

```bash
# Backend
cd backend
uv run pytest tests/unit/ tests/integration/ -v --cov=app

# Frontend (requires backend running)
cd frontend
npm test
npm run test:e2e
```

---

## Test Count Summary

- **Backend**: 331 tests (76% coverage)
  - Unit: 32 tests
  - Integration: 24 tests
  - E2E: 5 test classes
- **Frontend**: 253 component tests + 13 E2E scenarios
  - Component/Unit: 26.8% coverage
  - UI Components: 100% coverage
  - API Clients: 82% coverage

---

## Troubleshooting

### Backend

```bash
# Server not running (for E2E tests)
uv run uvicorn app.main:app --reload --port 8000

# Database issues
rm backend/thurup.db
uv run alembic upgrade head

# Dependencies
uv sync
```

### Frontend

```bash
# Install Playwright browsers
npx playwright install

# Port in use
lsof -i :5173  # Check what's using the port
lsof -i :18081 # Check backend port

# Clear cache
rm -rf node_modules/.vite
npm run dev
```

---

For detailed testing strategies, best practices, and writing new tests, see [TESTING_GUIDE.md](./TESTING_GUIDE.md).
