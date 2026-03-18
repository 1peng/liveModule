@echo off
echo Starting LiveModules...

call .\.rag\Scripts\activate.bat
echo Running start_all..py...
start "start_all" cmd /k python start_all.py

echo start all services started!
pause
