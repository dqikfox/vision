@echo off
title VISION — RAG Knowledge Engine
color 0B

echo.
echo  ============================================================
echo   VISION — RAG KNOWLEDGE ENGINE
echo  ============================================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Please install Python 3.10+.
    pause
    exit /b 1
)

:: Check / install dependencies
echo  [*] Checking dependencies...
python -c "import chromadb" >nul 2>&1
if errorlevel 1 (
    echo  [*] Installing ChromaDB...
    pip install chromadb --quiet
)
python -c "import sentence_transformers" >nul 2>&1
if errorlevel 1 (
    echo  [*] Installing sentence-transformers...
    pip install sentence-transformers --quiet
)
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo  [*] Installing FastAPI / uvicorn...
    pip install fastapi uvicorn aiofiles python-multipart httpx --quiet
)

echo.
echo  [*] Starting RAG engine on http://localhost:8766
echo  [*] Data directory : %RAG_PLUGIN_WORKSPACE%
if "%RAG_PLUGIN_WORKSPACE%"=="" (
    echo  [!] RAG_PLUGIN_WORKSPACE not set — defaulting to F:\rag-v1\data\
)
echo.

:: Open browser after short delay (background job)
start "" /b cmd /c "timeout /t 4 /nobreak >nul && start http://localhost:8766/rag_ui.html"

:: Launch server
cd /d "%~dp0"
python rag_engine.py

pause
