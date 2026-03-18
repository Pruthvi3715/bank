@echo off
echo Starting GraphSentinel Backend...
start cmd /k "cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000"

echo Starting GraphSentinel Frontend...
start cmd /k "cd frontend && npm install && npm run dev"

echo Services are starting...
echo Backend API will be available at: http://localhost:8000/docs
echo Frontend Dashboard will be available at: http://localhost:3000
