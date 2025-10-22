
# ⚙️ Thurup Developer Guide

## 1. Environment Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- `uv` or `pip` for Python dependency management

### Backend
```bash
cd backend
uv sync   # or pip install -r requirements.txt
uv run uvicorn app.main:app --reload --port 18081
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 2. Environment Variables

Create a .env in both backend and frontend root directories.

### Backend .env
```bash
HOST=0.0.0.0
PORT=18081
DEBUG=true
CORS_ORIGINS=http://localhost:5173
```

### Frontend .env
```bash
VITE_API_BASE=http://localhost:18081
```

---

## 3. Testing

### Backend Tests
```bash
cd backend
uv run pytest -v
```

### Frontend

Unit tests (optional, via Vitest or Jest):
```bash
cd frontend
npm test
```

### E2E Tests (Playwright)

End-to-end tests require both backend and frontend running:

```bash
# Terminal 1 - Start backend
cd backend
uv run uvicorn app.main:app --reload --port 18081

# Terminal 2 - Start frontend
cd frontend
npm run dev

# Terminal 3 - Run E2E tests
cd frontend
npm run test:e2e
```

**Interactive mode:**
```bash
npm run test:e2e:ui
```

**Current status:** 10/13 tests passing (3 timing-related failures)

---

## 4. Git Workflow

### Branch Strategy

- **main**: Stable, production-ready branch
  - Contains only squash-merged features
  - Each commit = complete, tested feature
  - Tagged releases (v0.1.0, v0.2.0, etc.)

- **play**: Development and experimentation branch
  - All active development happens here
  - Detailed commit history preserved
  - Free to experiment, iterate, and refactor

### Workflow Process

1. **Development:**
   ```bash
   git checkout play
   # Make changes, commit frequently
   git add .
   git commit -m "Description of changes"
   ```

2. **When feature is stable:**
   ```bash
   # Run all tests
   cd backend && uv run pytest -v
   cd ../frontend && npm run test:e2e

   # Switch to main
   git checkout main

   # Squash merge from play
   git merge --squash play

   # Create comprehensive commit message
   git commit -m "Add feature X with comprehensive tests

   - Feature details
   - Test coverage
   - Documentation updates
   - Backend: 331 tests passing
   - E2E: 10/13 tests passing"
   ```

3. **Tag releases:**
   ```bash
   git tag -a v0.1.0 -m "Release v0.1.0 - Feature X"
   git push origin main --tags
   ```

4. **Continue development:**
   ```bash
   git checkout play
   # Continue work...
   ```

### Pre-Merge Checklist

Before squash merging to main, ensure:

- [ ] All backend tests passing (`uv run pytest -v`)
- [ ] E2E tests passing or failures documented (`npm run test:e2e`)
- [ ] Code reviewed for quality and standards
- [ ] Documentation updated (if needed)
- [ ] Breaking changes documented
- [ ] Commit message follows professional standards (no AI/tool references)

---

## 5. Running the Full Stack

1.  Start backend:
```bash
uv run uvicorn app.main:app --reload --port 18081
```

2. Start frontend:
```bash
npm run dev
```

3. Open in browser:
👉 http://localhost:5173

---

## 6. Troubleshooting

| Problem                   | Cause                        | Fix                                      |
| ------------------------- | ---------------------------- | ---------------------------------------- |
| `WebSocket not connected` | UI reconnected too fast      | Apply updated `useGameSocket`            |
| CORS blocked              | Backend missing CORS origins | Ensure CORS middleware in `main.py`      |
| Port in use               | Previous instance not killed | `lsof -i :18081` → kill PID              |
| UI blank                  | Incorrect mount point        | Ensure `div#root` and correct `main.tsx` |


---

## 7. Contribution Guidelines

- Work in `play` branch for development
- Write tests for each backend function
- Run tests before committing (`pytest`, `npm run test:e2e`)
- Follow commit message standards (no AI/tool references)
- Squash merge to `main` when feature is stable
- Update documentation for significant changes

---

## 8. Deployment Plan

- Deploy FastAPI backend via Docker or Kubernetes.
- Use KEDA for autoscaling.
- Host frontend on static CDN (Vercel, Netlify, etc.).
- WebSocket URL configurable via .env.

---

