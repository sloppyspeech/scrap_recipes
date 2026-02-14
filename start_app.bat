@echo off
echo ====================================
echo Starting RecipeLens...
echo ====================================

echo 1. Cleanup: Stopping existing processes...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM node.exe /T >nul 2>&1
timeout /t 3 /nobreak >nul

echo 2. Launching Backend...
start "RecipeLens Backend" .euv_scrap_recipes\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

echo 3. Launching Frontend...
cd frontend
start "RecipeLens Frontend" npm run dev

echo ====================================
echo App Launched! Opening Browser...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo ====================================
timeout /t 5 >nul
start http://localhost:5173
