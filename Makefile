.PHONY: dev backend frontend

dev:
    docker-compose up --build

backend:
    cd backend && uvicorn app.main:app --reload --port 8000

frontend:
    cd frontend && npm run dev
