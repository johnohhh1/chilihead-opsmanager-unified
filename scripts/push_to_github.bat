@echo off
echo ========================================
echo Git Setup for ChiliHead OpsManager
echo ========================================
echo.

cd /d "C:\Users\John\Desktop\chilihead-opsmanager-unified"

REM Initialize git if not already done
if not exist ".git" (
    echo Initializing Git repository...
    git init
    git branch -M main
)

REM Add remote if not already added
git remote get-url origin >nul 2>&1
if errorlevel 1 (
    echo Adding GitHub remote...
    git remote add origin https://github.com/johnohhh1/chilihead-opsmanager-unified.git
)

REM Add all files
echo Adding files...
git add .

REM Commit
echo.
set /p commit_msg="Enter commit message (or press Enter for default): "
if "%commit_msg%"=="" set commit_msg=Update ChiliHead OpsManager Unified

git commit -m "%commit_msg%"

REM Push to GitHub
echo.
echo Pushing to GitHub...
git push -u origin main

echo.
echo ========================================
echo Done! Check https://github.com/johnohhh1/chilihead-opsmanager-unified
echo ========================================
pause
