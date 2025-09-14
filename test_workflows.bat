@echo off
echo ========================================
echo    N8N MCP WORKFLOWS TEST SUITE
echo ========================================
echo.

REM Activate virtual environment
call .venv\Scripts\activate

REM Install required dependencies
echo Installing dependencies...
python -m pip install requests --quiet

REM Set environment variables if needed
set N8N_BASE_URL=http://localhost:5678
set BACKEND_URL=http://localhost:8000
set YOUTUBE_API_KEY=AIzaSyBy4nQXiHuslrLgQwnqi0W-GuC1tb4WFTA

REM Run the test suite
python test_all_mcp_workflows.py %*

echo.
echo ========================================
echo    TEST COMPLETE
echo ========================================
pause