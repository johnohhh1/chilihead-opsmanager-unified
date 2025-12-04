@echo off
echo ========================================
echo Migrating SnappyMail from v2.0 to Unified
echo ========================================
echo.

REM Step 1: Backup v2.0 SnappyMail data
echo [1/5] Backing up v2.0 SnappyMail data...
docker cp chilihead-snappymail:/var/lib/snappymail "%~dp0..\snappymail-backup\"
if errorlevel 1 (
    echo [ERROR] Failed to backup SnappyMail data
    pause
    exit /b 1
)
echo [SUCCESS] Backup completed

echo.
echo [2/5] Starting unified SnappyMail container...
cd /d "%~dp0.."
docker-compose up -d snappymail
if errorlevel 1 (
    echo [ERROR] Failed to start unified SnappyMail
    pause
    exit /b 1
)

echo Waiting for container to initialize...
timeout /t 5 /nobreak > nul

echo.
echo [3/5] Copying data to unified SnappyMail...
docker cp "%~dp0..\snappymail-backup\snappymail\." unified-snappymail:/var/lib/snappymail/
if errorlevel 1 (
    echo [ERROR] Failed to copy data
    pause
    exit /b 1
)

echo.
echo [4/5] Restarting unified SnappyMail with migrated data...
docker restart unified-snappymail
timeout /t 5 /nobreak > nul

echo.
echo [5/5] Verifying migration...
docker ps | findstr unified-snappymail
if errorlevel 1 (
    echo [ERROR] Container not running
    pause
    exit /b 1
)

echo.
echo ========================================
echo Migration Complete!
echo ========================================
echo.
echo SnappyMail is now running at: http://localhost:8888
echo Data backed up to: %~dp0..\snappymail-backup\
echo.
echo Next steps:
echo   1. Test SnappyMail at http://localhost:8888
echo   2. If working, shut down v2.0 stack
echo.
pause
