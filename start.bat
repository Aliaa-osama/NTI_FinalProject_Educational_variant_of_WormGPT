@echo off
echo Starting Cybersecurity RAG System...
echo.

echo Starting Backend API...
cd backend
start /B python -m uvicorn main:app --reload --port 8000

echo.
echo Waiting for backend to initialize...
timeout /t 5 /nobreak

echo.
echo Starting Frontend...
cd ..
cd frontend
python -m streamlit run UI.py

echo.
echo Both services are starting...
echo Backend: http://127.0.0.1:8000
echo Frontend: http://localhost:8501
pause