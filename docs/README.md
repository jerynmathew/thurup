# Thurup Documentation

Welcome to the Thurup project documentation! This guide helps you navigate all available documentation for the 28/56 card game application.

## Quick Links

- **New to Thurup?** Start with the [Quickstart Guide](./getting-started/QUICKSTART.md)
- **Installing from scratch?** See [Installation Guide](./getting-started/INSTALLATION.md)
- **Want to contribute?** Read [Contributing Guide](./development/CONTRIBUTING.md)
- **Need to run tests?** Check [Running Tests](./testing/RUNNING_TESTS.md)

---

## Documentation Structure

The documentation is organized into the following categories:

### 📚 Getting Started

Start here if you're new to the project.

- **[Quickstart Guide](./getting-started/QUICKSTART.md)** - Get up and running in 5 minutes
- **[Installation Guide](./getting-started/INSTALLATION.md)** - Comprehensive installation instructions
- **[Deployment Guide](./getting-started/DEPLOYMENT.md)** - Production deployment strategies

### 🛠️ Development

Essential guides for developers working on the project.

- **[Developer Guide](./development/DEVELOPER_GUIDE.md)** - Development workflow and best practices
- **[Architecture Documentation](./development/ARCHITECTURE.md)** - System design and structure
- **[API Reference](./development/API_REFERENCE.md)** - Complete backend API documentation
- **[Contributing Guide](./development/CONTRIBUTING.md)** - How to contribute to the project

### 🧪 Testing

Everything you need to know about testing.

- **[Testing Guide](./testing/TESTING_GUIDE.md)** - Comprehensive testing documentation
- **[Running Tests](./testing/RUNNING_TESTS.md)** - Quick command reference

### 📋 Planning

Project planning and roadmap documents.

- **[Requirements](./planning/REQUIREMENTS.md)** - Feature requirements and specifications
- **[Roadmap](./planning/ROADMAP.md)** - Development roadmap and milestones
- **[Technical Debt](./planning/TECHNICAL_DEBT_TODO.md)** - Known issues and improvements
- **[Known Bugs](./planning/KNOWN_BUGS.md)** - Bug tracking and status
- **[Technical Review](./planning/TECHNICAL_REVIEW.md)** - Code review notes
- **[Legacy Documentation](./planning/CLAUDE_LEGACY.md)** - Historical reference (outdated)

### 🔧 Implementation

Detailed implementation guides for specific features.

- **[Round History Implementation](./implementation/ROUND_HISTORY_IMPLEMENTATION.md)** - Game history and replay system

---

## Documentation by Task

### I want to...

**...get started quickly**
→ [Quickstart Guide](./getting-started/QUICKSTART.md)

**...install from scratch**
→ [Installation Guide](./getting-started/INSTALLATION.md)

**...understand the architecture**
→ [Architecture Documentation](./development/ARCHITECTURE.md)

**...use the API**
→ [API Reference](./development/API_REFERENCE.md)

**...run tests**
→ [Running Tests](./testing/RUNNING_TESTS.md)

**...write tests**
→ [Testing Guide](./testing/TESTING_GUIDE.md)

**...contribute code**
→ [Contributing Guide](./development/CONTRIBUTING.md)

**...understand development workflow**
→ [Developer Guide](./development/DEVELOPER_GUIDE.md)

**...deploy to production**
→ [Deployment Guide](./getting-started/DEPLOYMENT.md)

**...see what's planned**
→ [Roadmap](./planning/ROADMAP.md)

**...report a bug**
→ [Known Bugs](./planning/KNOWN_BUGS.md) (check first) or open a GitHub issue

---

## Documentation Standards

All documentation in this project follows these standards:

- **Markdown format** - All docs are written in GitHub-flavored Markdown
- **Clear structure** - Headings, sections, and navigation
- **Code examples** - Practical examples for all technical concepts
- **Up-to-date** - Documentation is kept in sync with code changes
- **Zero duplication** - Single source of truth for each topic

### Contributing to Documentation

When updating documentation:

1. Keep it concise and clear
2. Include code examples where relevant
3. Update related documents if needed
4. Test all commands and examples
5. Follow the existing structure

See [Contributing Guide](./development/CONTRIBUTING.md) for more details.

---

## Project Overview

**Thurup** is a real-time multiplayer card game (28/56 variant) built with:

- **Backend**: FastAPI + Python 3.11+ (async/await architecture)
- **Frontend**: React + TypeScript + Vite
- **Database**: SQLite with Alembic migrations
- **Real-time**: WebSocket for live game updates
- **Testing**: Pytest (backend) + Vitest + Playwright (frontend)

### Key Features

- ✅ Real-time multiplayer gameplay
- ✅ AI bot opponents
- ✅ Game history and replay system
- ✅ Admin dashboard for server management
- ✅ Session persistence (survives page refresh)
- ✅ Responsive UI for mobile and desktop
- ✅ Comprehensive test coverage

---

## Quick Commands Reference

### Backend

```bash
cd backend

# Install dependencies
uv sync

# Run development server
uv run uvicorn app.main:app --reload --port 18081

# Run tests
uv run pytest -v

# Run with coverage
uv run pytest --cov=app
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Run tests
npm test

# Run E2E tests
npm run test:e2e
```

For more commands, see [Running Tests](./testing/RUNNING_TESTS.md).

---

## Getting Help

- **Documentation**: Search this docs folder
- **Issues**: Check [GitHub Issues](https://github.com/yourusername/thurup/issues)
- **Questions**: Open a GitHub Discussion
- **Bugs**: See [Known Bugs](./planning/KNOWN_BUGS.md) first

---

## Documentation Changelog

- **2025-10-22**: Major reorganization into structured subdirectories
- **2025-10-19**: Added E2E testing documentation
- **2025-10-15**: Updated with Round History implementation
- **2025-10-13**: Added admin panel and game history docs

---

**Last Updated**: 2025-10-22
