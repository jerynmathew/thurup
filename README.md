# Thurup - 28/56 Card Game

A modern, real-time multiplayer implementation of the classic 28/56 card game.

## 🎮 Features

- **Real-time Multiplayer**: Play with friends via WebSocket connections
- **Bot AI**: Add computer opponents with configurable difficulty
- **Game History**: Review past games with complete replay functionality
- **Admin Dashboard**: Monitor server health and manage active games
- **Persistent State**: Automatic game state saving and recovery
- **Modern UI**: Beautiful, responsive interface built with React and TailwindCSS

## 🚀 Quick Start

**New to Thurup?** Follow the [Quickstart Guide](./docs/getting-started/QUICKSTART.md) to get running in 5 minutes.

**Detailed setup?** See the [Installation Guide](./docs/getting-started/INSTALLATION.md).

### Quick Commands

**Backend:**
```bash
cd backend
uv sync                                    # Install dependencies
uv run alembic upgrade head                # Run migrations
uv run uvicorn app.main:app --reload --port 18081
```

**Frontend:**
```bash
cd frontend
npm install                                # Install dependencies
npm run dev                                # Start dev server
```

**Access the app**: http://localhost:5173

## 📚 Documentation

Complete documentation is organized in the [`docs/`](./docs/) folder:

### Getting Started
- **[Quickstart Guide](./docs/getting-started/QUICKSTART.md)** - Get up and running in 5 minutes
- **[Installation Guide](./docs/getting-started/INSTALLATION.md)** - Comprehensive setup instructions
- **[Deployment Guide](./docs/getting-started/DEPLOYMENT.md)** - Production deployment strategies

### Development
- **[Developer Guide](./docs/development/DEVELOPER_GUIDE.md)** - Development workflow and best practices
- **[Architecture](./docs/development/ARCHITECTURE.md)** - System design and structure
- **[API Reference](./docs/development/API_REFERENCE.md)** - Complete backend API documentation
- **[Contributing](./docs/development/CONTRIBUTING.md)** - How to contribute to the project

### Testing
- **[Testing Guide](./docs/testing/TESTING_GUIDE.md)** - Comprehensive testing documentation
- **[Running Tests](./docs/testing/RUNNING_TESTS.md)** - Quick command reference

### Planning & Implementation
- **[Requirements](./docs/planning/REQUIREMENTS.md)** - Feature requirements and specifications
- **[Roadmap](./docs/planning/ROADMAP.md)** - Development roadmap and milestones
- **[Technical Debt](./docs/planning/TECHNICAL_DEBT_TODO.md)** - Known issues and improvements
- **[Known Bugs](./docs/planning/KNOWN_BUGS.md)** - Bug tracking and status
- **[Technical Review](./docs/planning/TECHNICAL_REVIEW.md)** - Code review and priorities
- **[Round History Implementation](./docs/implementation/ROUND_HISTORY_IMPLEMENTATION.md)** - Game history system

### Component Logs (for Claude Code)
- **[backend/CLAUDE.md](./backend/CLAUDE.md)** - Backend development log with technical details
- **[frontend/CLAUDE.md](./frontend/CLAUDE.md)** - Frontend development log with UI/UX changes

## 🏗️ Project Structure

```
thurup/
├── backend/              # FastAPI backend with WebSocket support
│   ├── app/
│   │   ├── api/v1/       # Modular API endpoints
│   │   │   ├── router.py              # Main router and shared state
│   │   │   ├── rest.py                # REST endpoints
│   │   │   ├── websocket.py           # WebSocket handler
│   │   │   ├── broadcast.py           # State broadcasting
│   │   │   ├── bot_runner.py          # Bot AI orchestration
│   │   │   ├── connection_manager.py  # WebSocket connections
│   │   │   ├── persistence_integration.py  # Database integration
│   │   │   ├── history.py             # Game history endpoints
│   │   │   └── admin.py               # Admin endpoints
│   │   ├── game/         # Game logic and state management
│   │   └── db/           # Database models and persistence
│   ├── tests/            # Unit, integration, and E2E tests
│   └── alembic/          # Database migrations
│
├── frontend/             # React + TypeScript frontend
│   ├── src/
│   │   ├── api/          # API service layer
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── stores/       # Zustand state management
│   │   └── types/        # TypeScript type definitions
│   └── tests/e2e/        # Playwright E2E tests
│
├── docs/                 # Organized documentation
│   ├── getting-started/  # Setup and installation
│   ├── development/      # Architecture, API, contributing
│   ├── testing/          # Testing strategies
│   ├── planning/         # Roadmap, requirements, technical debt
│   └── implementation/   # Feature implementation guides
│
└── docker-compose.yml    # Container orchestration
```

## 📊 Development Status

**Backend**: ✅ Complete (331 tests, 76% coverage)
- Core game logic and rules
- Database persistence with SQLite + Alembic
- REST API and WebSocket communication
- Admin endpoints with authentication
- Round history and replay system
- Comprehensive testing

**Frontend**: ✅ Production Ready (253 tests, 26.8% coverage)
- ✅ Project setup and infrastructure
- ✅ Type system and state management
- ✅ API integration layer
- ✅ Complete UI component library
- ✅ Game board and gameplay UI (fully responsive)
- ✅ Real-time WebSocket communication
- ✅ Session persistence and recovery
- ✅ Game history and replay viewer
- ✅ Admin dashboard
- ✅ E2E testing with Playwright (13 scenarios, 77% pass rate)

## 🧪 Testing

**Backend:**
```bash
cd backend
uv run pytest                    # All tests (331 tests)
uv run pytest tests/unit/        # Unit tests (32 tests)
uv run pytest tests/integration/ # Integration tests (24 tests)
uv run pytest --cov=app          # With coverage report
```

**Frontend:**
```bash
cd frontend
npm test                         # Unit/component tests (253 tests)
npm run test:coverage            # With coverage report
npm run test:e2e                 # E2E tests (requires backend running)
npm run test:e2e:ui              # E2E in interactive mode
```

See [Running Tests](./docs/testing/RUNNING_TESTS.md) for more commands.

## 🎯 Game Rules

Thurup is a trick-taking card game for 4-6 players:
- **28 Mode**: 32 cards (7-A), 4 players, 2 teams
- **56 Mode**: 64 cards (2 decks), 4-6 players, 2-3 teams
- Bidding phase to determine trump suit
- Trick-taking with trump and suit following rules
- Points awarded based on card values and tricks won

See [Requirements](./docs/planning/REQUIREMENTS.md) for detailed game rules.

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. Review the [Architecture](./docs/development/ARCHITECTURE.md) to understand the system design
2. Check [Contributing Guide](./docs/development/CONTRIBUTING.md) for guidelines
3. Follow [Developer Guide](./docs/development/DEVELOPER_GUIDE.md) for setup instructions
4. Add tests for new features
5. Update documentation as needed

See [Contributing Guide](./docs/development/CONTRIBUTING.md) for detailed contribution guidelines.

## 📝 License

[Add your license here]

## 🙏 Acknowledgments

Built with modern technologies:
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [React](https://react.dev/) - Frontend framework
- [SQLModel](https://sqlmodel.tiangolo.com/) - Database ORM
- [Zustand](https://zustand-demo.pmnd.rs/) - State management
- [TailwindCSS](https://tailwindcss.com/) - Styling
- [Playwright](https://playwright.dev/) - E2E testing

---

**Last Updated**: 2025-10-22
**Status**: Production Ready
**Version**: 0.2.0

## 📋 Recent Changes

### 2025-10-22: Documentation Reorganization
- ✅ Restructured all documentation into organized subdirectories
- ✅ Eliminated duplicate documentation (6 files merged)
- ✅ Created comprehensive guides: Quickstart, Installation, Contributing
- ✅ Added quick reference for running tests
- ✅ Updated navigation with task-based "I want to..." guide
- ✅ Single source of truth for all documentation topics

### Week 7: Critical Bug Fixes (2025-10-15)
- ✅ Fixed multiplayer hand visibility (WebSocket re-identification)
- ✅ Fixed dealer rotation to follow official 28 rules
- ✅ Improved trick card display with actual card images
- ✅ Enhanced visual spacing and layout

### Week 6: Round History Persistence (2025-10-14)
- ✅ Implemented comprehensive round history database persistence
- ✅ Created admin game history browser with round-by-round playback
- ✅ Fixed player name persistence bug
- ✅ Added "Start Next Round" button for multi-round gameplay
- ✅ Enhanced admin panel with short code display

### Week 5: Session Management & Visual Enhancements (2025-10-13)
- ✅ Frontend LocalStorage persistence for player sessions
- ✅ Modal-based join flow consistent across all entry points
- ✅ Page refresh recovery with automatic session restoration
- ✅ WebSocket short code resolution bug fix (critical)
- ✅ Playing card images from Deck of Cards API
- ✅ Responsive GameBoard layout with percentage-based positioning
- ✅ Team-based scoring display with bid targets
- ✅ Lead suit indicator and last trick display
- ✅ Context-aware trump reveal feedback

---

For detailed technical documentation and development logs, see:
- [Backend Development Log](./backend/CLAUDE.md)
- [Frontend Development Log](./frontend/CLAUDE.md)
- [Documentation Hub](./docs/README.md)
