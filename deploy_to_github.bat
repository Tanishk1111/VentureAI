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

REM Prompt for GitHub repository URL
set /p repo_url=Enter your GitHub repository URL (e.g., https://github.com/username/repo.git): 

if "%repo_url%"=="" (
    echo No repository URL provided. Exiting.
    exit /b 1
)

REM Add remote and push
git remote add origin %repo_url%
git branch -M main
git push -u origin main

echo Code pushed to GitHub repository: %repo_url%
echo GitHub Actions will automatically deploy your application to Google Cloud Run.
echo Make sure you've set up the GitHub secrets as described in the README.md file.

pause 