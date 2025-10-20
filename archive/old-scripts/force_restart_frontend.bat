@echo off
echo Killing all Node.js processes...
taskkill /F /IM node.exe 2>nul
timeout /t 2 /nobreak > nul

echo Clearing Next.js cache...
cd /d "C:\Users\John\Desktop\chilihead-opsmanager-unified\client"
rmdir /S /Q .next 2>nul

echo Starting fresh frontend server...
npm run dev
