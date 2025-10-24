@echo off
echo ========================================
echo   Push ChiliHead OpsManager to GitHub
echo ========================================
echo.

cd /d "C:\Users\John\Desktop\chilihead-opsmanager-unified"

echo Checking current status...
git status
echo.

echo Adding all changes...
git add .

echo.
echo Creating commit...
git commit -m "Major updates: Fixed Ollama model routing, added OSS thought suppression, dark mode deadline UI"

echo.
echo Pushing to GitHub...
git push origin main

echo.
echo ========================================
echo   Push Complete!
echo ========================================
echo.
echo Your changes have been pushed to GitHub.
echo.
pause
