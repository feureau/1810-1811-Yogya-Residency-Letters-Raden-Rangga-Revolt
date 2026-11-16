@echo off
setlocal
cd /d "%~dp0"

echo ======================================================================
echo  1810-1811 Yogya Residency Letters: Raden Rangga Revolt
echo  Local Static Web Server (GitHub Pages Preview)
echo ======================================================================
echo.
echo  Starting local HTTP server on port 8000...
echo.
echo  Available Pages:
echo    * Portal:              http://localhost:8000/
echo    * Side-by-Side Viewer: http://localhost:8000/transcriptions.html
echo    * Full Transcriptions: http://localhost:8000/full.html
echo    * Keyword Dictionary:  http://localhost:8000/dictionary.html
echo.
echo  Press Ctrl+C to stop the server at any time.
echo ======================================================================
echo.

:: Launch the default web browser after 1 second
start "" cmd /c "timeout /t 1 /nobreak >nul & start http://localhost:8000/"

:: Launch Python's built-in HTTP server
python -m http.server 8000

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Python failed to start the server.
    echo Please ensure Python is installed and added to your system PATH.
    pause
)
