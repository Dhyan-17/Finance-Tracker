@echo off
echo =============================================
echo    Smart Finance Tracker - Startup
echo =============================================
echo.

REM Check if requirements are installed
python -c "import streamlit" 2>NUL
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Initialize database if not exists
if not exist "data\fintech.db" (
    echo.
    echo Initializing database...
    python setup.py
)

echo.
echo Starting application...
echo.
echo App will open at: http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo =============================================
echo.

streamlit run app.py
