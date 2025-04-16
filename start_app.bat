@echo off
echo Starting VC Interview Application...

echo Starting backend API...
start cmd /k "cd /d %~dp0 && python main.py"

echo Waiting for API to initialize...
timeout /t 5 /nobreak

echo Starting frontend...
start cmd /k "cd /d %~dp0\vc-interview-frontend && npm start"

echo VC Interview Application started!
echo Backend API: http://localhost:8000
echo Frontend: http://localhost:3000 