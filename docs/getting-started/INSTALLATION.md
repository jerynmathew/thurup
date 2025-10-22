# Installation Guide

Comprehensive installation instructions for the Thurup card game application.

## System Requirements

### Minimum Requirements

- **Operating System**: macOS, Linux, or Windows (with WSL2)
- **RAM**: 2 GB minimum, 4 GB recommended
- **Disk Space**: 500 MB for dependencies and build artifacts
- **Network**: Internet connection for initial dependency download

### Required Software

- **Node.js**: Version 18.0 or higher ([Download](https://nodejs.org/))
- **npm**: Version 9.0 or higher (comes with Node.js)
- **Python**: Version 3.11 or higher ([Download](https://www.python.org/))
- **uv**: Python package manager ([Install from uv.dev](https://github.com/astral-sh/uv))

### Optional Software

- **Git**: For version control ([Download](https://git-scm.com/))
- **VS Code**: Recommended editor with extensions:
  - Python (ms-python.python)
  - ESLint (dbaeumer.vscode-eslint)
  - Prettier (esbenp.prettier-vscode)

---

## Installation Steps

### 1. Install System Dependencies

#### macOS

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Node.js and Python
brew install node python@3.11

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Linux (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Windows (WSL2)

```bash
# Follow Linux instructions above in WSL2 terminal
# Or use Windows Subsystem for Linux with Ubuntu
```

### 2. Verify Installations

```bash
# Check Node.js version
node --version  # Should be 18.0 or higher

# Check npm version
npm --version   # Should be 9.0 or higher

# Check Python version
python3 --version  # Should be 3.11 or higher

# Check uv installation
uv --version
```

### 3. Clone the Repository

```bash
# Clone from GitHub
git clone https://github.com/yourusername/thurup.git
cd thurup
```

Or download and extract the ZIP file from the repository.

---

## Backend Setup

### 1. Navigate to Backend Directory

```bash
cd backend
```

### 2. Install Python Dependencies

```bash
# Install dependencies using uv
uv sync

# This creates a virtual environment and installs all packages from pyproject.toml
```

The following packages will be installed:
- **FastAPI**: Web framework
- **Uvicorn**: ASGI server
- **SQLModel**: Database ORM
- **Alembic**: Database migrations
- **Structlog**: Structured logging
- **Pytest**: Testing framework
- **Ruff**: Linter
- **Black**: Code formatter

### 3. Database Setup

```bash
# Run database migrations
uv run alembic upgrade head
```

This creates `thurup.db` (SQLite database) with all required tables:
- `games` - Game metadata
- `players` - Player information
- `game_state_snapshots` - Game state history
- `round_history` - Round-by-round game history

### 4. Environment Configuration (Optional)

Create `.env` file in the backend directory:

```bash
# Copy template
cp .env.template .env

# Edit with your preferred settings
nano .env
```

**Available Configuration**:

```env
# Server
HOST=0.0.0.0
PORT=18081

# CORS (comma-separated origins)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Admin Authentication
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin

# Database
DATABASE_URL=sqlite+aiosqlite:///./thurup.db

# Cleanup Task
CLEANUP_LOBBY_TIMEOUT_HOURS=1
CLEANUP_ACTIVE_TIMEOUT_HOURS=2
CLEANUP_COMPLETED_RETENTION_HOURS=24
CLEANUP_INTERVAL_MINUTES=30
```

### 5. Verify Backend Installation

```bash
# Run tests
uv run pytest -v

# All tests should pass (331 tests)
```

---

## Frontend Setup

### 1. Navigate to Frontend Directory

```bash
cd frontend  # From project root
```

### 2. Install Node Dependencies

```bash
# Install dependencies from package.json
npm install
```

This will install:
- **React** 18: UI framework
- **Vite**: Build tool and dev server
- **TypeScript**: Type safety
- **TailwindCSS**: Styling framework
- **Zustand**: State management
- **React Router**: Routing
- **Axios**: HTTP client
- **Vitest**: Testing framework
- **Playwright**: E2E testing

### 3. Environment Configuration (Optional)

Create `.env` file in the frontend directory:

```bash
# Example .env
VITE_API_BASE_URL=http://localhost:18081
VITE_WS_BASE_URL=ws://localhost:18081
```

Default values work for local development, so this step is optional.

### 4. Install Playwright Browsers (for E2E tests)

```bash
# Install Chromium browser for E2E tests
npx playwright install chromium
```

### 5. Verify Frontend Installation

```bash
# Run unit/component tests
npm test

# Tests should pass (253 tests)
```

---

## Running the Application

### Development Mode

**Terminal 1 - Backend:**
```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 18081
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:18081
- **API Documentation**: http://localhost:18081/docs (Swagger UI)

### Production Build

**Backend:**
```bash
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 18081
```

**Frontend:**
```bash
cd frontend

# Build production assets
npm run build

# Preview production build
npm run preview
```

---

## Post-Installation Steps

### 1. Run End-to-End Tests

```bash
# Terminal 1: Start backend
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 18081

# Terminal 2: Run E2E tests
cd frontend
npm run test:e2e
```

### 2. Create Your First Game

1. Open http://localhost:5173
2. Enter your name
3. Select game mode (28 or 56)
4. Click "Create Game"
5. Add bot players
6. Start playing!

### 3. Explore Admin Panel

1. Navigate to http://localhost:5173
2. Click "Admin Panel"
3. Login with default credentials:
   - Username: `admin`
   - Password: `admin`
4. View server health, active sessions, and game history

---

## Troubleshooting

### Common Issues

#### "uv: command not found"

```bash
# Add uv to PATH (Linux/macOS)
export PATH="$HOME/.cargo/bin:$PATH"

# Or reinstall uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Port Already in Use

```bash
# Check what's using port 18081
lsof -i :18081

# Kill the process
kill -9 <PID>

# Or use a different port
uv run uvicorn app.main:app --port 8080
```

#### Database Migration Errors

```bash
# Reset database
rm backend/thurup.db

# Re-run migrations
cd backend
uv run alembic upgrade head
```

#### Frontend Build Errors

```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules .vite
npm install
npm run dev
```

#### CORS Errors

Update `backend/.env`:
```env
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

Restart backend server.

### Getting Help

- **Documentation**: See [docs/README.md](../README.md) for all guides
- **Issues**: Check existing GitHub issues
- **Developer Guide**: See [DEVELOPER_GUIDE.md](../development/DEVELOPER_GUIDE.md)

---

## Uninstallation

### Remove Application Files

```bash
# Remove entire project
cd ..
rm -rf thurup
```

### Remove Dependencies (Optional)

**Python (uv):**
```bash
# uv manages isolated virtual environments, so just removing the project is enough
# Optionally remove uv itself:
rm -rf ~/.cargo/bin/uv
```

**Node.js:**
```bash
# Remove Node.js (macOS)
brew uninstall node

# Remove Node.js (Linux)
sudo apt remove nodejs npm
```

---

## Next Steps

After successful installation:

1. **Quickstart**: See [QUICKSTART.md](./QUICKSTART.md) for a 5-minute getting started guide
2. **Development**: See [DEVELOPER_GUIDE.md](../development/DEVELOPER_GUIDE.md) for development workflow
3. **Architecture**: See [ARCHITECTURE.md](../development/ARCHITECTURE.md) to understand the system design
4. **Testing**: See [TESTING_GUIDE.md](../testing/TESTING_GUIDE.md) for testing strategies
5. **API Reference**: See [API_REFERENCE.md](../development/API_REFERENCE.md) for API documentation

---

**Installation Complete! 🎉**
