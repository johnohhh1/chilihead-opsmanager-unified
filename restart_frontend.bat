@echo off
echo ========================================
echo RESTARTING FRONTEND WITH MODEL FIX
echo ========================================
echo.

REM Kill any existing Next.js process
taskkill /F /IM node.exe /T 2>nul

echo Clearing Next.js cache...
cd client
rmdir /S /Q .next 2>nul

echo.
echo Starting frontend with fresh build...
start /B npm run dev

echo.
echo ========================================
echo FRONTEND RESTARTED!
echo ========================================
echo.
echo Please:
echo 1. Open browser to http://localhost:3001
echo 2. Open browser console (F12)
echo 3. Go to Operations Chat
echo 4. Click the refresh icon next to Model Selection
echo 5. Check console for model loading logs
echo.
echo You should see:
echo - Claude models (6 total)
echo - GPT-4o with Vision
echo.
pause