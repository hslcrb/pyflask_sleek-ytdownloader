@echo off
setlocal
"%~dp0runtime\python.exe" "%~dp0app\launch.py" %*
set "sleek_status=%ERRORLEVEL%"
if not "%sleek_status%"=="0" if "%~1"=="" pause
exit /b %sleek_status%
