@echo off
echo ========================================
echo  Fixing Triage Page Issues
echo ========================================
echo.

echo [1/2] Installing react-markdown...
cd client
call npm install react-markdown remark-gfm --save

echo.
echo [2/2] Markdown library installed!
echo.
echo Next: I'll update the TriagePage.tsx file to use it
echo.
pause
