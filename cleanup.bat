@echo off
echo VentureAI - Cleaning up development files
echo =============================================
echo.

REM Create backup directory
if not exist backup mkdir backup

REM Move test files to backup folder
echo Moving test files to backup...
move test_*.py backup\ 2>nul
move local_test.py backup\ 2>nul
move simple_client.py backup\ 2>nul
move interview_client.py backup\ 2>nul
move interactive_interview.py backup\ 2>nul
move fixed_client.py backup\ 2>nul

REM Move documentation that's not needed in production
echo Moving development documentation...
move FIXES.md backup\ 2>nul
move client_readme.md backup\ 2>nul
move gcp_setup.md backup\ 2>nul

REM Clear out session data
echo Cleaning session data...
if exist sessions\ (
    rd /s /q sessions
    mkdir sessions
)

REM Clear out uploads
echo Cleaning uploads folder...
if exist uploads\ (
    rd /s /q uploads
    mkdir uploads
)

REM Create empty .gitkeep files
echo > sessions\.gitkeep
echo > uploads\.gitkeep

echo.
echo Cleanup complete! Development files moved to backup folder.
echo You can now proceed with deployment.
echo.
echo To restore backed up files later, run: move backup\* .
echo.

pause 