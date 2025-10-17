
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

---

## 4. Running the Full Stack

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

## 5. Troubleshooting

| Problem                   | Cause                        | Fix                                      |
| ------------------------- | ---------------------------- | ---------------------------------------- |
| `WebSocket not connected` | UI reconnected too fast      | Apply updated `useGameSocket`            |
| CORS blocked              | Backend missing CORS origins | Ensure CORS middleware in `main.py`      |
| Port in use               | Previous instance not killed | `lsof -i :18081` → kill PID              |
| UI blank                  | Incorrect mount point        | Ensure `div#root` and correct `main.tsx` |


---

## 6. Contribution Guidelines

- Use feature branches (feature/<name>)
- Write tests for each backend function
- Lint with black + ruff
- Commit conventional messages (feat:, fix:, etc.)

---

## 7. Deployment Plan

- Deploy FastAPI backend via Docker or Kubernetes.
- Use KEDA for autoscaling.
- Host frontend on static CDN (Vercel, Netlify, etc.).
- WebSocket URL configurable via .env.

---

