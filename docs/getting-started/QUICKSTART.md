# Quickstart Guide

Get Thurup up and running in 5 minutes.

## Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.11+
- **uv** (Python package manager) - [Install from uv.dev](https://github.com/astral-sh/uv)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/thurup.git
cd thurup
```

### 2. Backend Setup

```bash
cd backend

# Install dependencies
uv sync

# Run database migrations
uv run alembic upgrade head
```

### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install
```

## Running the Application

### Start Backend Server

```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 18081
```

Backend will be available at: **http://localhost:18081**

### Start Frontend Development Server

In a new terminal:

```bash
cd frontend
npm run dev
```

Frontend will be available at: **http://localhost:5173**

## Your First Game

1. **Open your browser**: Navigate to http://localhost:5173

2. **Create a game**:
   - Enter your name (e.g., "Player 1")
   - Select game mode: "28 (4 Players)"
   - Click "Create Game"

3. **Add bot players**:
   - Click "Add Bot Player" three times to fill the lobby

4. **Start playing**:
   - Click "Start Game"
   - Place your bid or pass
   - If you win bidding, choose a trump suit
   - Play cards from your hand

5. **Enjoy**! The bots will play automatically, and you'll see the game flow.

## Testing the Application

### Backend Tests

```bash
cd backend
uv run pytest -v
```

### Frontend Tests

```bash
cd frontend

# Unit/component tests
npm test

# E2E tests (requires backend running)
npm run test:e2e
```

## What's Next?

- **Multiplayer**: Share the game URL with friends to play together
- **Game History**: View past games by clicking "Game History" on the home page
- **Admin Panel**: Access server management at "Admin Panel" (default login: admin/admin)

## Need Help?

- **Detailed setup**: See [INSTALLATION.md](./INSTALLATION.md)
- **Architecture**: See [ARCHITECTURE.md](../development/ARCHITECTURE.md)
- **Development**: See [DEVELOPER_GUIDE.md](../development/DEVELOPER_GUIDE.md)
- **Testing**: See [TESTING_GUIDE.md](../testing/TESTING_GUIDE.md)

## Troubleshooting

### Backend won't start

```bash
# Check if port 18081 is in use
lsof -i :18081

# Reinstall dependencies
uv sync

# Rebuild database
rm thurup.db
uv run alembic upgrade head
```

### Frontend won't start

```bash
# Check if port 5173 is in use
lsof -i :5173

# Clear cache and reinstall
rm -rf node_modules .vite
npm install
npm run dev
```

### Can't connect to backend

- Ensure backend is running on port 18081
- Check firewall settings
- Verify CORS configuration in `backend/.env`

---

**Happy Gaming! 🎮**
