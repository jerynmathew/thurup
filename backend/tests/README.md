# Thurup Backend - Test Suite

Comprehensive test suite organized by test type: unit, integration, and end-to-end.

## Test Structure

```
tests/
├── unit/              # Unit tests (isolated, fast, no external dependencies)
├── integration/       # Integration tests (API tests with TestClient)
├── e2e/              # End-to-end tests (full system, requires running server)
├── conftest.py       # Shared pytest fixtures
└── README.md         # This file
```

## Test Types

### Unit Tests (`tests/unit/`)

**Purpose**: Test individual components in isolation

**Characteristics**:
- Fast execution (< 1 second total)
- No external dependencies
- Mock/stub external services
- Test single functions/classes

**Files**:
- `test_bidding.py` - Bidding logic and validation
- `test_hidden_trump.py` - Hidden trump reveal mechanics
- `test_rules.py` - Card game rules
- `test_scoring.py` - Score calculation
- `test_session.py` - GameSession class
- `test_phase1_fixes.py` - Phase 1 bug fixes
- `test_persistence.py` - Database persistence layer

**Run**:
```bash
# Run all unit tests
uv run pytest tests/unit/ -v

# Run specific test file
uv run pytest tests/unit/test_bidding.py -v

# Run with coverage
uv run pytest tests/unit/ --cov=app --cov-report=term-missing
```

### Integration Tests (`tests/integration/`)

**Purpose**: Test how components work together via APIs

**Characteristics**:
- Uses FastAPI TestClient (no server required)
- Tests REST and WebSocket endpoints
- In-memory database
- Tests full API flows

**Files**:
- `test_api_integration.py` - Complete API integration tests (24 tests)
  - REST endpoints
  - WebSocket communication
  - History endpoints
  - Admin endpoints
  - Persistence flows
  - End-to-end scenarios

**Run**:
```bash
# Run all integration tests
uv run pytest tests/integration/ -v

# Run specific test class
uv run pytest tests/integration/test_api_integration.py::TestRESTIntegration -v
```

### End-to-End Tests (`tests/e2e/`)

**Purpose**: Test the complete system as a user would

**Characteristics**:
- Requires running server
- Real HTTP requests
- Tests full user workflows
- Simulates production usage

**Files**:
- `test_complete_flow.py` - Complete game lifecycle tests
  - Full game flow (create → join → play → history)
  - Multiple concurrent games
  - Authentication security
  - Error handling

**Run**:
```bash
# Step 1: Start the server in one terminal
uv run uvicorn app.main:app --reload --port 8000

# Step 2: Run E2E tests in another terminal
uv run pytest tests/e2e/ -v -s

# With output visible
uv run pytest tests/e2e/test_complete_flow.py::TestCompleteGameFlow -v -s
```

## Running All Tests

```bash
# Run everything
uv run pytest

# Run with summary
uv run pytest --tb=short -q

# Run with verbose output
uv run pytest -v

# Run specific test type
uv run pytest tests/unit/ -v
uv run pytest tests/integration/ -v
uv run pytest tests/e2e/ -v  # Requires server

# Run with markers (coming soon)
uv run pytest -m unit
uv run pytest -m integration
uv run pytest -m e2e
```

## Test Statistics

### Current Test Count
- **Unit Tests**: 32 tests
- **Integration Tests**: 24 tests
- **E2E Tests**: 5 test classes (15+ scenarios)
- **Total**: 56+ tests

### Coverage
- Core game logic: ✅ Comprehensive
- API endpoints: ✅ All endpoints tested
- WebSocket: ✅ Connection, messages, broadcasting
- Persistence: ✅ Save, load, restore
- History: ✅ Query, replay, stats
- Admin: ✅ All admin operations

## Writing New Tests

### Unit Test Template

```python
"""
Unit tests for [component name].
"""

import pytest
from app.game.session import GameSession


class TestMyComponent:
    """Test suite for MyComponent."""

    def test_basic_functionality(self):
        """Test basic functionality."""
        # Arrange
        session = GameSession(mode="28", seats=4)

        # Act
        result = session.some_method()

        # Assert
        assert result is not None
```

### Integration Test Template

```python
"""
Integration tests for [API endpoint].
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestMyEndpoint:
    """Integration tests for my endpoint."""

    def test_endpoint_success(self, client):
        """Test successful endpoint call."""
        response = client.post("/api/v1/my/endpoint", json={"data": "value"})
        assert response.status_code == 200
```

### E2E Test Template

```python
"""
E2E tests for [user workflow].
"""

import pytest
import requests

BASE_URL = "http://localhost:8000/api/v1"


@pytest.fixture(scope="module")
def check_server():
    """Verify server is running."""
    try:
        requests.get("http://localhost:8000/", timeout=2)
    except requests.exceptions.ConnectionError:
        pytest.skip("Server not running")


class TestMyWorkflow:
    """E2E test for my workflow."""

    def test_complete_workflow(self, check_server):
        """Test complete user workflow."""
        # Step 1: Create resource
        resp = requests.post(f"{BASE_URL}/resource", json={})
        assert resp.status_code == 200

        # Step 2: Interact with resource
        # ...
```

## Best Practices

### General
- ✅ Write descriptive test names
- ✅ One assertion per test (when possible)
- ✅ Arrange-Act-Assert pattern
- ✅ Clean up after tests (fixtures handle this)
- ✅ Test both success and failure cases

### Unit Tests
- ✅ No I/O operations
- ✅ Fast execution (< 0.01s per test)
- ✅ Use mocks for external dependencies
- ✅ Test edge cases and boundary conditions

### Integration Tests
- ✅ Use TestClient (no server needed)
- ✅ Test API contracts
- ✅ Verify error responses
- ✅ Test authentication/authorization

### E2E Tests
- ✅ Test complete user journeys
- ✅ Use realistic data
- ✅ Verify system behavior
- ✅ Check for race conditions

## Continuous Integration

```yaml
# Example GitHub Actions workflow
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install uv
        run: pip install uv
      - name: Install dependencies
        run: uv sync
      - name: Run unit tests
        run: uv run pytest tests/unit/ -v
      - name: Run integration tests
        run: uv run pytest tests/integration/ -v
      - name: Start server for E2E
        run: uv run uvicorn app.main:app &
      - name: Wait for server
        run: sleep 5
      - name: Run E2E tests
        run: uv run pytest tests/e2e/ -v
```

## Troubleshooting

### "Server not running" error in E2E tests
**Solution**: Start server first: `uv run uvicorn app.main:app --reload`

### "Database locked" errors
**Solution**: Use separate test database or in-memory SQLite

### Slow tests
**Solution**:
- Check if E2E tests are running (they're slower)
- Profile with: `uv run pytest --durations=10`

### Import errors
**Solution**:
- Ensure you're in the backend directory
- Run: `uv sync` to install dependencies

## Debugging Tests

```bash
# Run with print statements visible
uv run pytest -v -s

# Run single test
uv run pytest tests/unit/test_bidding.py::test_sequential_bidding -v

# Drop into debugger on failure
uv run pytest --pdb

# Show full traceback
uv run pytest --tb=long

# Run last failed tests
uv run pytest --lf
```

## Test Coverage

```bash
# Generate coverage report
uv run pytest --cov=app --cov-report=html

# View coverage (opens in browser)
open htmlcov/index.html

# Show missing lines
uv run pytest --cov=app --cov-report=term-missing
```

---

**Last Updated**: 2025-10-13
**Total Tests**: 56+
**Test Pass Rate**: 100% ✅
