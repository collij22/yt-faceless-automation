@echo off
echo ========================================
echo n8n Workflow Deployment for Windows
echo ========================================

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and add it to your PATH
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo WARNING: No .env file found
    echo Make sure to configure your n8n API settings:
    echo - N8N_API_KEY
    echo - N8N_API_URL
    echo.
    echo Copy .env.example to .env and edit with your values
    pause
)

echo Step 1: Validating workflow files...
echo ====================================
python validate_workflows.py
if %errorlevel% neq 0 (
    echo.
    echo Validation failed! Please fix the errors above.
    pause
    exit /b 1
)

echo.
echo Step 2: Deploying workflows to n8n...
echo =====================================
python deploy_n8n_workflows_windows.py
if %errorlevel% neq 0 (
    echo.
    echo Deployment failed! Please check the errors above.
    pause
    exit /b 1
)

echo.
echo Step 3: Testing webhook endpoints...
echo ===================================
python test_n8n_webhooks.py
if %errorlevel% neq 0 (
    echo.
    echo Some webhook tests failed. Check n8n workflow status.
)

echo.
echo ========================================
echo Deployment process completed!
echo ========================================
echo.
echo Next steps:
echo 1. Check n8n web interface for deployed workflows
echo 2. Configure API keys in n8n (ElevenLabs, YouTube, etc.)
echo 3. Test the full pipeline with the Python orchestrator
echo.
pause