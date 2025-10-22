# Changelog

All notable changes to Thurup will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-10-22

### Added

#### Features
- **Round History Persistence**: Complete database persistence of all rounds with trick-by-trick details
- **Admin Game History Browser**: Web UI for browsing all games with round-by-round playback
- **Multiple Rounds Support**: "Start Next Round" button enables continuous gameplay without recreating games
- **Session Management**: LocalStorage-based session persistence with 24-hour expiry and page refresh recovery
- **Visual Enhancements**:
  - Real playing card images from Deck of Cards API
  - Trick cards display with actual card images
  - Last trick display showing previous trick winner and cards
  - Lead suit indicator during play phase
  - Team scores with bid targets and success/failure indicators
  - Responsive layout with percentage-based positioning

#### Admin Panel
- HTTP Basic Auth protected admin dashboard
- Server health metrics monitoring
- Active sessions list with connection status
- Database statistics viewer
- Manual save/delete/cleanup triggers
- Short code display throughout admin interface

#### Testing & Quality
- Comprehensive test suite: 584 total tests (331 backend + 253 frontend)
- Integration tests for all API modules
- End-to-end tests with Playwright
- Test coverage increased from 68% to 76%
- Testing documentation with examples and patterns

#### Documentation
- Complete documentation reorganization into subdirectories:
  - `docs/getting-started/` - Quickstart and installation guides
  - `docs/development/` - Developer guide, architecture, API reference, contributing
  - `docs/testing/` - Testing guide and running tests
  - `docs/planning/` - Technical debt and legacy docs
  - `docs/implementation/` - Implementation details
- Eliminated duplicate documentation (merged 6 files)
- Created comprehensive guides: Quickstart, Installation, Contributing, Testing
- Updated root README.md with working links

#### Docker
- Production-ready Docker configuration
- Multi-stage builds for frontend optimization
- Health checks for both services
- Complete environment variable configuration
- Service dependencies with health conditions
- Resource limits and restart policies
- Separate production compose file (`docker-compose.prod.yml`)
- `.dockerignore` for build optimization

### Fixed

#### Critical Bugs
- **Multiplayer Hand Visibility**: Fixed WebSocket race condition preventing players 2-4 from seeing their hands
  - Root cause: WebSocket connected before session restoration, never re-identified
  - Solution: Added reactive useEffect to re-identify when seat/playerId changes
- **Dealer Rotation**: Fixed incorrect dealer rotation and first bidder assignment
  - Dealer now rotates counter-clockwise following official 28 card game rules
  - First bidder correctly set to player to dealer's right
  - Dealer badge displays on correct seat (not leader)

#### Persistence Bugs
- **Player Persistence**: Fixed bug where players weren't saved to database on game updates
  - Players now persist correctly on every game save
  - Enables proper name display in history instead of "Seat X"
- **Round History Saving**: Fixed rounds only saving when starting next round
  - Rounds now save immediately when completed (SCORING state)
  - First/only round no longer lost

#### UI Bugs
- **WebSocket Connection**: Fixed connection not establishing on GamePage initial render
- **Admin Navigation**: Fixed `navigate is not defined` error in admin dashboard
- **Player Names Display**: Fixed React rendering error when API returned player objects instead of strings

### Changed

#### Refactoring (Technical Debt)
- Extracted `TrickManager` class from `GameSession` (TD-005 Phase 2)
- Extracted `BiddingManager` class from `GameSession` (TD-005 Phase 3)
- Extracted `HiddenTrumpManager` class from `GameSession` (TD-005 Phase 1)
- Encapsulated global state in `GameServer` singleton (TD-006)
- Fixed test cases for dealer rotation changes (TD-013)
- Completed technical debt items: TD-002, TD-005, TD-006

#### Improvements
- Responsive GameBoard layout with aspect-square container
- Team-based scoring display (even vs odd seats)
- Trump reveal feedback with context-aware hints
- CORS configuration moved to environment variables
- Auto-fill bots when starting game with fewer than 4 players
- Trick view delay with visual layer approach
- Improved E2E test reliability with better timing and selectors

### Project Metadata
- **Total Lines of Code**: ~15,000 (backend: 8,500, frontend: 6,500)
- **Test Coverage**: 76% backend, comprehensive frontend coverage
- **Docker Support**: Production-ready with health checks and resource limits
- **Documentation**: 15+ comprehensive guides and references
- **License**: MIT License

---

## [0.1.0] - 2025-10-08

### Added
- Initial release of Thurup 28/56 card game
- FastAPI backend with WebSocket support
- React frontend with real-time gameplay
- Database persistence with SQLModel and SQLite
- Bot AI opponents
- Structured logging with JSON output
- Basic game modes: 28 and 56 card variants
- Bidding, trump selection, and trick-taking gameplay
- Team-based scoring system
- Background cleanup task for old games

### Technical Stack
- Backend: Python 3.11+, FastAPI, SQLModel, Alembic, Structlog
- Frontend: React 18.3+, TypeScript, Vite, TailwindCSS, Zustand
- Database: SQLite with async support (aiosqlite)
- Testing: Pytest, Vitest, Playwright

---

## [Unreleased]

### Planned
- Audio feedback for game events (card play, trick winner, turn notifications)
- Bot action timing improvements (realistic delays)
- Visual countdown timers for trick completion
- PostgreSQL support for production deployments
- Redis caching for session management
- Advanced bot AI difficulty levels
- Tournament mode
- Player statistics and leaderboards

[0.2.0]: https://github.com/yourusername/thurup/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/yourusername/thurup/releases/tag/v0.1.0
