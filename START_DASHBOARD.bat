@echo off
echo ============================================
echo  TWIN RANGE FILTER BOT - WEB DASHBOARD
echo ============================================
echo.
echo Installing required packages...
py -m pip install flask flask-cors
echo.
echo Starting dashboard...
echo.
py web_dashboard.py
pause
