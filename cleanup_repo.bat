@echo off
echo Cleaning up repository before GitHub push...
echo.
echo WARNING: This will remove all fix scripts, content files, and temporary files.
echo Important core files like main.py, routers/, utils/, and requirements.txt will be preserved.
echo test_interview.py will also be preserved for testing purposes.
echo.
set /p confirm=Are you sure you want to proceed? (Y/N): 

if /i "%confirm%" neq "Y" (
    echo Operation cancelled.
    goto :end
)

echo.
echo Removing fix scripts...
del /q fix_*.py
del /q fix_*.py.bak
del /q *_content.py

echo Removing apply scripts...
del /q apply_*.py

echo Removing Python cache files...
rmdir /s /q __pycache__
rmdir /s /q routers\__pycache__
rmdir /s /q utils\__pycache__

echo Removing other temporary files...
del /q cloud_error_check.py

echo Clean up complete!
echo.
echo Ready for GitHub push. Core files have been preserved.
echo The following steps will now add, commit, and push changes:
echo.
echo git add .
echo git commit -m "Clean up repository and prepare for deployment"
echo git push

:end
pause 