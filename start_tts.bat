@echo off
echo Starting LiveModules...

call .\.rag\Scripts\activate.bat
echo Running live-tts.py...
start "live-tts" cmd /k python live-tts.py

echo TTS services started!
pause
