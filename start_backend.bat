@echo off
echo Starting Home Loan Assistant Backend...
cd backend
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
echo.
echo Backend dependencies installed!
echo Starting FastAPI server...
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
