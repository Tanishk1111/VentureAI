@echo off
echo VentureAI - Cleaning up development files
echo =============================================
echo.

REM Create backup directory
if not exist backup mkdir backup

REM Move test files to backup folder
echo Moving test files to backup...
if exist test_*.py (
    move test_*.py backup\
)
if exist local_test.py (
    move local_test.py backup\
)
if exist simple_client.py (
    move simple_client.py backup\
)
if exist interview_client.py (
    move interview_client.py backup\
)
if exist interactive_interview.py (
    move interactive_interview.py backup\
)
if exist fixed_client.py (
    move fixed_client.py backup\
)

REM Move documentation that's not needed in production
echo Moving development documentation...
if exist FIXES.md (
    move FIXES.md backup\
)
if exist client_readme.md (
    move client_readme.md backup\
)
if exist gcp_setup.md (
    move gcp_setup.md backup\
)

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