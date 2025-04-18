@echo off
echo Initializing GitHub deployment for VentureAI

REM Check if git is installed
where git >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Git is not installed. Please install git first.
    exit /b 1
)

REM Initialize git if not already initialized
if not exist .git (
    git init
    echo Git repository initialized.
) else (
    echo Git repository already exists.
)

REM Add all files
git add .

REM Commit changes
git commit -m "Initial commit for VentureAI deployment"

REM Set default repository URL
set default_repo_url=https://github.com/Tanishk1111/VentureAI.git
set /p repo_url=Enter your GitHub repository URL (default: %default_repo_url%): 

REM Use default if empty
if "%repo_url%"=="" (
    set repo_url=%default_repo_url%
    echo Using default repository: %repo_url%
)

REM Add remote and push
git remote add origin %repo_url%
git branch -M main
git push -u origin main

echo Code pushed to GitHub repository: %repo_url%
echo GitHub Actions will automatically deploy your application to Google Cloud Run.
echo Make sure you've set up the GitHub secrets as described in the README.md file.

pause 