@echo off
echo ================================================
echo EMERGENCY RESTORE - Copying from Original
echo ================================================

REM Copy the ORIGINAL working files back
xcopy "C:\Users\John\Desktop\openinbox-opsmanager\client\*" "C:\Users\John\Desktop\chilihead-opsmanager-unified\client\" /E /I /Y /H

xcopy "C:\Users\John\Desktop\openinbox-opsmanager\server\*" "C:\Users\John\Desktop\chilihead-opsmanager-unified\server\" /E /I /Y /H

echo.
echo ================================================
echo RESTORED! Original files copied back.
echo ================================================
echo.
echo Now restart the app with start_unified.bat
pause
