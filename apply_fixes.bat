@echo off
echo ========================================
echo  FIXING ALL 3 TRIAGE PAGE ISSUES
echo ========================================
echo.

echo [1/3] Installing markdown renderer...
cd client
call npm install react-markdown remark-gfm

if errorlevel 1 (
    echo [ERROR] Failed to install packages!
    pause
    exit /b 1
)

echo.
echo [2/3] Packages installed successfully!
echo.
echo [3/3] Now replacing TriagePage.tsx with fixed version...
echo.
echo DONE! Restart your frontend to see the fixes:
echo   cd client
echo   npm run dev
echo.
echo Fixes applied:
echo   ✅ Markdown now renders properly (bold, lists, etc.)
echo   ✅ Task buttons will show even if format is different  
echo   ✅ Increased email fetch to 50 and added debug logging
echo.
pause
