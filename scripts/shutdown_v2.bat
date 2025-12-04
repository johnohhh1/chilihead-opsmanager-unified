@echo off
echo ========================================
echo Shutting Down v2.0 Stack
echo ========================================
echo.
echo This will stop all v2.0 containers but preserve data.
echo You can restart them later if needed.
echo.
pause

cd /d "C:\Users\John\ohhhmail\infrastructure\docker"

echo.
echo [1/3] Stopping all v2.0 containers...
docker-compose down

echo.
echo [2/3] Verifying shutdown...
docker ps -a | findstr chilihead

echo.
echo [3/3] Creating archive marker...
echo v2.0 stack frozen on %date% at %time% > "%~dp0..\V2_FROZEN.txt"
echo Reason: Migrated to simplified unified architecture >> "%~dp0..\V2_FROZEN.txt"
echo Data preserved for future reference >> "%~dp0..\V2_FROZEN.txt"

echo.
echo ========================================
echo v2.0 Stack Shutdown Complete
echo ========================================
echo.
echo What was stopped:
echo   - chilihead-ollama
echo   - chilihead-qdrant
echo   - chilihead-redis
echo   - chilihead-nats
echo   - chilihead-aubs
echo   - chilihead-email-ingestion
echo   - chilihead-snappymail (migrated to unified)
echo   - chilihead-openwebui-backend
echo   - chilihead-postgres
echo   - chilihead-zookeeper
echo.
echo All data preserved in Docker volumes.
echo To restart: cd C:\Users\John\ohhhmail\infrastructure\docker ^&^& docker-compose up -d
echo.
pause
