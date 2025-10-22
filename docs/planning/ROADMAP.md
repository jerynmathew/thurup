# Thurup - Feature Roadmap & Development Plan

**Last Updated**: 2025-10-14

---

## Vision

Thurup aims to be the premier online platform for playing the 28/56 card game with friends and AI opponents. Our goal is to deliver a polished, scalable, and feature-rich gaming experience.

---

## Current Status

### ✅ Completed Features

**Core Gameplay**
- [x] 28 and 56 game modes
- [x] 4 and 6 player support
- [x] Complete bidding phase with sequential turns
- [x] Trump selection and hidden trump modes
- [x] Card play with follow-suit rules
- [x] Trick tracking and scoring
- [x] Team-based scoring (even vs odd seats)

**Multiplayer**
- [x] Real-time WebSocket communication
- [x] Player join/leave with seat assignment
- [x] AI bot opponents
- [x] Short code game URLs (e.g., royal-turtle-65)
- [x] Session persistence across page refreshes
- [x] Lobby system for game creation

**UI/UX**
- [x] Responsive design (mobile, tablet, desktop)
- [x] Circular game board with player positions
- [x] Interactive card hand with playable card indicators
- [x] Current trick and last trick display
- [x] Lead suit indicator
- [x] Team scores with bid targets
- [x] Real-time turn indicators
- [x] Toast notifications for actions

**Infrastructure**
- [x] SQLite database with async support
- [x] Database migrations (Alembic)
- [x] Game state persistence and recovery
- [x] Structured logging with structlog
- [x] Comprehensive test suite (60 tests)
- [x] API history and admin endpoints

---

## 🎯 Current Sprint (Q4 2025)

### Refactoring & Technical Debt
**Priority**: 🔴 Critical

**Issues to Address**:
1. Remove dual WebSocket connection tracking
2. Extract resolve_game_id to shared utility
3. Add WebSocket message validation
4. Fix useGame hook dependencies
5. Add error boundaries to frontend

**Timeline**: 2-3 weeks
**Assignee**: TBD

**Success Criteria**:
- [ ] All critical issues from TECHNICAL_REVIEW.md resolved
- [ ] Test coverage maintained or improved
- [ ] No regressions in existing functionality
- [ ] Documentation updated

---

## 🚀 Q1 2026 - Core Features & Polish

### 1. Game Settings & Customization
**Priority**: 🟡 High
**Estimated Effort**: 2 weeks

**Features**:
- [ ] Configurable hidden trump modes
  - [ ] On first non-follow
  - [ ] On first trump play
  - [ ] On bidder non-follow
  - [ ] Open immediately
- [ ] Configurable minimum bid
- [ ] Game speed settings (bot delay)
- [ ] Optional kitty reveal rules
- [ ] Custom team names

**User Story**: As a player, I want to customize game rules to match my preferred play style.

---

### 2. Enhanced Multiplayer Experience
**Priority**: 🟡 High
**Estimated Effort**: 3 weeks

**Features**:
- [ ] **Spectator Mode**
  - [ ] Watch ongoing games
  - [ ] Spectator chat
  - [ ] Live updates without seat assignment

- [ ] **Player Presence**
  - [ ] Online/offline indicators
  - [ ] Connection status badges
  - [ ] Reconnection notifications

- [ ] **Game Invitations**
  - [ ] Shareable game links with preview
  - [ ] Copy-to-clipboard button
  - [ ] QR code generation for mobile

- [ ] **Player Profiles**
  - [ ] Avatars (upload or generated)
  - [ ] Display names
  - [ ] Basic stats (games played, win rate)

**User Story**: As a player, I want to invite friends easily and see who's connected.

---

### 3. Chat & Communication
**Priority**: 🟡 Medium
**Estimated Effort**: 2 weeks

**Features**:
- [ ] **In-Game Chat**
  - [ ] Text chat during game
  - [ ] Team-only chat option
  - [ ] Emojis/reactions
  - [ ] Chat history

- [ ] **Quick Reactions**
  - [ ] Thumbs up/down
  - [ ] Celebrations (GG, Nice play)
  - [ ] Animated reactions on game board

**User Story**: As a player, I want to communicate with teammates and opponents.

---

### 4. Game History & Replays
**Priority**: 🟡 Medium
**Estimated Effort**: 2 weeks

**Features**:
- [ ] **Game History Page**
  - [ ] List of completed games
  - [ ] Filter by date, mode, players
  - [ ] Search by game code

- [ ] **Replay System**
  - [ ] Step-by-step replay
  - [ ] Jump to specific trick
  - [ ] Show all hands (post-game)
  - [ ] Download replay data

- [ ] **Game Statistics**
  - [ ] Per-game stats (tricks won, points)
  - [ ] Player performance metrics
  - [ ] Team collaboration stats

**User Story**: As a player, I want to review past games to improve my strategy.

---

## 🚀 Q2 2026 - Advanced Features

### 5. Enhanced AI Opponents
**Priority**: 🟡 High
**Estimated Effort**: 3 weeks

**Features**:
- [ ] **AI Difficulty Levels**
  - [ ] Easy (random play)
  - [ ] Medium (basic strategy)
  - [ ] Hard (advanced strategy)
  - [ ] Expert (near-optimal play)

- [ ] **AI Personalities**
  - [ ] Aggressive bidder
  - [ ] Conservative bidder
  - [ ] Trump hoarder
  - [ ] Team player

- [ ] **AI Training Mode**
  - [ ] Practice against AI
  - [ ] Hints and suggestions
  - [ ] Explain AI decisions

**User Story**: As a player, I want challenging AI opponents to practice against.

---

### 6. Tournaments & Competitions
**Priority**: 🟢 Medium
**Estimated Effort**: 4 weeks

**Features**:
- [ ] **Tournament System**
  - [ ] Single-elimination brackets
  - [ ] Round-robin tournaments
  - [ ] Swiss system
  - [ ] Tournament brackets visualization

- [ ] **Matchmaking**
  - [ ] Skill-based matching
  - [ ] Quick play queue
  - [ ] Ranked mode

- [ ] **Leaderboards**
  - [ ] Global rankings
  - [ ] Monthly/weekly leaderboards
  - [ ] ELO rating system
  - [ ] Achievement badges

**User Story**: As a competitive player, I want to participate in tournaments and climb rankings.

---

### 7. Social Features
**Priority**: 🟢 Low-Medium
**Estimated Effort**: 3 weeks

**Features**:
- [ ] **Friends System**
  - [ ] Add/remove friends
  - [ ] Friend requests
  - [ ] Friends list
  - [ ] Online status

- [ ] **Clubs/Teams**
  - [ ] Create/join clubs
  - [ ] Club chat
  - [ ] Club tournaments
  - [ ] Club leaderboards

- [ ] **Achievements**
  - [ ] Win streaks
  - [ ] Perfect bids
  - [ ] Comeback victories
  - [ ] Achievement showcase

**User Story**: As a social player, I want to connect with other players and form communities.

---

## 🚀 Q3 2026 - Monetization & Growth

### 8. Premium Features
**Priority**: 🟢 Medium
**Estimated Effort**: 4 weeks

**Features**:
- [ ] **Subscription Tiers**
  - [ ] Free tier (basic features)
  - [ ] Premium tier (advanced features)
  - [ ] Pro tier (all features + perks)

- [ ] **Premium Features**
  - [ ] Ad-free experience
  - [ ] Custom themes
  - [ ] Advanced statistics
  - [ ] Priority matchmaking
  - [ ] Exclusive avatars
  - [ ] Game history unlimited

- [ ] **Payment Integration**
  - [ ] Stripe integration
  - [ ] Subscription management
  - [ ] Gift subscriptions

**User Story**: As a dedicated player, I want to support the platform and unlock premium features.

---

### 9. Mobile Apps
**Priority**: 🟢 High
**Estimated Effort**: 8 weeks

**Features**:
- [ ] **Native Mobile Apps**
  - [ ] iOS app (React Native / Flutter)
  - [ ] Android app (React Native / Flutter)
  - [ ] Push notifications
  - [ ] Offline mode support

- [ ] **Progressive Web App (PWA)**
  - [ ] Install on home screen
  - [ ] Offline gameplay against AI
  - [ ] Background sync

**User Story**: As a mobile user, I want a native app experience for gaming on the go.

---

### 10. Internationalization
**Priority**: 🟢 Medium
**Estimated Effort**: 2 weeks

**Features**:
- [ ] **Multi-Language Support**
  - [ ] English
  - [ ] Hindi
  - [ ] Spanish
  - [ ] Portuguese
  - [ ] Others based on demand

- [ ] **Localization**
  - [ ] Currency conversion
  - [ ] Date/time formats
  - [ ] Cultural adaptations

**User Story**: As a non-English speaker, I want to use the platform in my native language.

---

## 🚀 Q4 2026 - Scale & Performance

### 11. Infrastructure Improvements
**Priority**: 🔴 Critical
**Estimated Effort**: 6 weeks

**Features**:
- [ ] **Horizontal Scaling**
  - [ ] Redis for session storage
  - [ ] Redis pub/sub for WebSockets
  - [ ] Load balancer with sticky sessions
  - [ ] Multi-region deployment

- [ ] **Performance Optimization**
  - [ ] Database query optimization
  - [ ] Caching layer (Redis)
  - [ ] CDN for static assets
  - [ ] WebSocket message compression

- [ ] **Monitoring & Observability**
  - [ ] Prometheus metrics
  - [ ] Grafana dashboards
  - [ ] Sentry error tracking
  - [ ] Logging aggregation (ELK/Loki)

**User Story**: As a platform operator, I need the system to scale to thousands of concurrent games.

---

### 12. Advanced Analytics
**Priority**: 🟢 Low-Medium
**Estimated Effort**: 3 weeks

**Features**:
- [ ] **Player Analytics**
  - [ ] Win rate by position
  - [ ] Bidding patterns
  - [ ] Trump selection analysis
  - [ ] Card play heatmaps

- [ ] **Game Analytics**
  - [ ] Most played game modes
  - [ ] Peak hours analysis
  - [ ] Retention metrics
  - [ ] Engagement funnels

- [ ] **Admin Dashboard**
  - [ ] Real-time game monitoring
  - [ ] User management
  - [ ] Content moderation tools
  - [ ] Revenue analytics

**User Story**: As a platform operator, I want insights into player behavior and system health.

---

## 🎁 Bonus Features (Backlog)

### Nice-to-Have Features

**Gameplay Enhancements**:
- [ ] Practice mode with hints
- [ ] Tutorial for new players
- [ ] Game variations (different scoring rules)
- [ ] Tournament replay broadcasts
- [ ] Commentated games

**Social**:
- [ ] Player blocking/reporting
- [ ] Friend recommendations
- [ ] Social media sharing
- [ ] Twitch integration
- [ ] Discord bot

**Technical**:
- [ ] API for third-party integrations
- [ ] Webhooks for events
- [ ] Data export for players
- [ ] GDPR compliance tools
- [ ] Two-factor authentication

---

## 📊 Success Metrics

### Key Performance Indicators (KPIs)

**User Engagement**:
- Daily Active Users (DAU)
- Monthly Active Users (MAU)
- Average session duration
- Games completed per day
- Player retention (D1, D7, D30)

**Technical**:
- 99.9% uptime
- < 100ms API response time
- < 5% error rate
- < 1s game state sync
- Support 10,000+ concurrent games

**Business** (Post-monetization):
- Conversion rate (free → paid)
- Monthly Recurring Revenue (MRR)
- Customer Lifetime Value (LTV)
- Churn rate
- Net Promoter Score (NPS)

---

## 🛠️ Technical Milestones

### Infrastructure Roadmap

**Q4 2025**: Foundation Cleanup
- ✅ Resolve critical technical debt
- ✅ Improve test coverage
- ✅ Optimize performance bottlenecks

**Q1 2026**: Production Ready
- [ ] Add rate limiting
- [ ] Implement proper logging
- [ ] Add monitoring dashboards
- [ ] Security audit

**Q2 2026**: Scale Preparation
- [ ] Move to Redis for sessions
- [ ] Implement Redis pub/sub
- [ ] Add connection pooling
- [ ] Load testing

**Q3 2026**: Scale Deployment
- [ ] Multi-region deployment
- [ ] CDN integration
- [ ] Horizontal scaling verified
- [ ] Performance benchmarks met

**Q4 2026**: Global Scale
- [ ] Support 10,000+ concurrent games
- [ ] Multi-region active-active
- [ ] 99.99% uptime SLA
- [ ] Auto-scaling infrastructure

---

## 📝 Notes

### Dependencies

- **Q1 2026 features** depend on technical debt resolution (Q4 2025)
- **Tournaments** depend on player profiles and matchmaking
- **Mobile apps** depend on API stabilization
- **Scaling** depends on Redis migration

### Assumptions

- Development team size: 2-3 developers
- Sprint length: 2 weeks
- Testing and QA included in estimates
- Design and UX work estimated separately

### Risks

- **Technical debt** may take longer than estimated
- **Scaling challenges** may require architecture changes
- **Monetization** depends on user growth
- **Mobile apps** require separate expertise

---

## 🤝 Contributing

Want to contribute? Check out:
- **TECHNICAL_REVIEW.md** - Current issues and priorities
- **CLAUDE.md** (frontend/backend) - Development history
- **GitHub Issues** - Specific tasks and bugs

---

_This roadmap is a living document and will be updated as priorities shift and new features are proposed._
