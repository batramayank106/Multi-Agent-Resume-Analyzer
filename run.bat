@echo off
cd /d "%~dp0"

echo Starting CV Chacha Backend...
start "CV Chacha Backend" cmd /k "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo Starting CV Chacha Frontend...
start "CV Chacha Frontend" cmd /k "python -m streamlit run frontend/app.py"

echo.
echo CV Chacha is starting up!
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:8501
echo.
pause
