# Thurup - 28/56 Card Game

A modern, real-time multiplayer implementation of the classic 28/56 card game.

## 🎮 Features

- **Real-time Multiplayer**: Play with friends via WebSocket connections
- **Bot AI**: Add computer opponents with configurable difficulty
- **Game History**: Review past games with complete replay functionality
- **Admin Dashboard**: Monitor server health and manage active games
- **Persistent State**: Automatic game state saving and recovery
- **Modern UI**: Beautiful, responsive interface built with React and TailwindCSS

## 📚 Documentation

### Core Documentation
- **[TECHNICAL_REVIEW.md](./docs/TECHNICAL_REVIEW.md)** - 🔍 Comprehensive codebase review, architecture analysis, and refactoring priorities
- **[ROADMAP.md](./docs/ROADMAP.md)** - 🗺️ Feature roadmap and development milestones

### Project Documentation
Complete project documentation is available in the [`docs/`](./docs/) folder:

- **[ARCHITECTURE.md](./docs/ARCHITECTURE.md)** - Complete system architecture (backend + frontend)
- **[PROJECT_LOG.md](./docs/PROJECT_LOG.md)** - Development history and progress
- **[REQUIREMENTS.md](./docs/REQUIREMENTS.md)** - Feature requirements and specifications
- **[DEVELOPER_GUIDE.md](./docs/DEVELOPER_GUIDE.md)** - Setup and development instructions
- **[API.md](./docs/API.md)** - API endpoint documentation

### Component Logs
- **[backend/CLAUDE.md](./backend/CLAUDE.md)** - Backend development log with technical details
- **[frontend/CLAUDE.md](./frontend/CLAUDE.md)** - Frontend development log with UI/UX changes

## 🚀 Quick Start

### Prerequisites

- **Backend**: Python 3.11+, [uv](https://github.com/astral-sh/uv) package manager
- **Frontend**: Node.js 20+, npm
- **Docker**: Optional, for containerized deployment

### Development Setup

**Backend:**
```bash
cd backend
uv sync                          # Install dependencies
uv run alembic upgrade head      # Run migrations
uv run uvicorn app.main:app --reload  # Start dev server
```

**Frontend:**
```bash
cd frontend
npm install                      # Install dependencies
npm run dev                      # Start dev server
```

**Docker:**
```bash
docker-compose up --build        # Start both services
```

## 🏗️ Project Structure

```
thurup/
├── backend/              # FastAPI backend with WebSocket support
│   ├── app/             # Application source code
│   │   ├── api/         # REST and WebSocket endpoints
│   │   ├── game/        # Game logic and state management
│   │   └── db/          # Database models and persistence
│   ├── tests/           # Unit, integration, and E2E tests
│   └── alembic/         # Database migrations
│
├── frontend/            # React + TypeScript frontend
│   ├── src/
│   │   ├── api/         # API service layer
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   ├── stores/      # Zustand state management
│   │   └── types/       # TypeScript type definitions
│   └── public/          # Static assets
│
├── docs/                # Project documentation
└── docker-compose.yml   # Container orchestration
```

## 📊 Development Status

**Backend**: ✅ Complete (Week 1-3)
- Core game logic and rules
- Database persistence
- REST API and WebSocket
- Admin endpoints
- Comprehensive testing (60 tests)

**Frontend**: ✅ Phase 4 Complete (80% complete)
- ✅ Project setup and infrastructure
- ✅ Type system and state management
- ✅ API integration layer
- ✅ Base UI components
- ✅ Game board and gameplay UI (responsive)
- ✅ Real-time WebSocket communication
- ✅ Team scoring and trick tracking
- ✅ Lead suit indicators and last trick display
- 🚧 History and replay features
- 🚧 Admin dashboard

## 🧪 Testing

**Backend:**
```bash
cd backend
uv run pytest              # Run all tests (60 tests)
uv run pytest tests/unit/  # Unit tests only (32 tests)
uv run pytest tests/integration/  # Integration tests (24 tests)
uv run pytest tests/e2e/   # E2E tests (4 test classes)
```

**Code Quality:**
```bash
cd backend
uv run ruff check app/ tests/  # Linting
uv run black app/ tests/       # Formatting
```

## 🎯 Game Rules

Thurup is a trick-taking card game for 4-6 players:
- **28 Mode**: 32 cards (7-A), 4 players, 2 teams
- **56 Mode**: 64 cards (2 decks), 4-6 players, 2-3 teams
- Bidding phase to determine trump suit
- Trick-taking with trump and suit following rules
- Points awarded based on card values and tricks won

See [REQUIREMENTS.md](./docs/REQUIREMENTS.md) for detailed game rules.

## 🤝 Contributing

1. Review the [ARCHITECTURE.md](./docs/ARCHITECTURE.md) to understand the system design
2. Check [DEVELOPER_GUIDE.md](./docs/DEVELOPER_GUIDE.md) for setup instructions
3. Review [PROJECT_LOG.md](./docs/PROJECT_LOG.md) for recent changes
4. Follow existing code style (enforced by ruff and prettier)
5. Add tests for new features
6. Update documentation as needed

## 📝 License

[Add your license here]

## 🙏 Acknowledgments

Built with modern technologies:
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [React](https://react.dev/) - Frontend framework
- [SQLModel](https://sqlmodel.tiangolo.com/) - Database ORM
- [Zustand](https://zustand-demo.pmnd.rs/) - State management
- [TailwindCSS](https://tailwindcss.com/) - Styling

---

**Last Updated**: 2025-10-14
**Status**: Active Development
**Version**: 0.1.0 (Pre-release)

## 📋 Recent Changes

### Week 5: Session Management & Technical Review (2025-10-14)

**Session Management (Completed)**
- ✅ Frontend LocalStorage persistence for player sessions (24-hour expiry)
- ✅ Modal-based join flow consistent across all entry points
- ✅ Page refresh recovery with automatic session restoration
- ✅ WebSocket short code resolution bug fix (critical)
- ✅ Race condition prevention in session loading

**Documentation (New)**
- ✅ Created comprehensive [TECHNICAL_REVIEW.md](./docs/TECHNICAL_REVIEW.md) with:
  - Architecture analysis and scoring (6.5/10 overall)
  - 13 critical/major issues identified with solutions
  - Refactoring priorities (High/Medium/Low)
  - Scalability roadmap and recommendations
- ✅ Created [ROADMAP.md](./docs/ROADMAP.md) with:
  - Q1-Q4 2026 feature milestones
  - Tournaments, mobile apps, monetization plans
  - Infrastructure scaling strategy

### Week 4: UX Improvements (2025-10-13)

**Backend**
- Added current trick and lead suit tracking to game state
- Implemented last trick persistence for history display
- Enhanced GameStateDTO with trick-related fields
- Fixed type safety issues with Pydantic models

**Frontend**
- Implemented fully responsive GameBoard layout
- Added team-based scoring display
- Created lead suit indicator for follow-suit guidance
- Added last trick display showing previous completed trick
- Improved trump reveal feedback for bid winner
- Made all components responsive with Tailwind breakpoints
- Enhanced player seat components with adaptive sizing

## 🎯 Next Steps

See [TECHNICAL_REVIEW.md](./docs/TECHNICAL_REVIEW.md) for detailed refactoring priorities:

**High Priority** (Q4 2025):
1. Remove dual WebSocket connection tracking
2. Extract `resolve_game_id` to shared utility
3. Add WebSocket message validation
4. Fix useGame hook dependencies
5. Add error boundaries to frontend

**Medium Priority** (Q1 2026):
- Refactor GameSession God class
- Encapsulate global state in GameServer
- Optimize broadcast serialization
- Add proper logging library

See complete details in the technical review document.

---

For detailed technical documentation, see [backend/CLAUDE.md](./backend/CLAUDE.md) and [frontend/CLAUDE.md](./frontend/CLAUDE.md).
