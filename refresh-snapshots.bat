@echo off
setlocal
cd /d "%~dp0"
"%~dp0.venv\Scripts\python.exe" "%~dp0refresh_qdb_snapshot.py"
set "refresh_exit=%errorlevel%"
if not "%refresh_exit%"=="0" echo Refresh failed. See logs\refresh-qdb-snapshot.log for details.
if /I not "%~1"=="--no-pause" pause
exit /b %refresh_exit%
