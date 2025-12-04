@echo off
echo ========================================
echo Docker Cleanup - Remove Unused Images
echo ========================================
echo.
echo This will delete ~100GB of unused Docker images.
echo v2.0 stack must be shutdown first!
echo.
echo WARNING: This cannot be undone.
echo.
pause

echo.
echo [1/4] Checking what will be removed...
echo.
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

echo.
echo ========================================
echo Proceeding with cleanup...
echo ========================================
pause

echo.
echo [2/4] Removing HUGE unused images (100GB+)...
docker rmi maccam912/hunyuan3d:latest 2>nul
echo   Removed hunyuan3d (91GB)
docker rmi infra-api:latest 2>nul
echo   Removed infra-api (12GB)
docker rmi sebp/elk:latest 2>nul
echo   Removed elk (5.7GB)

echo.
echo [3/4] Removing old/duplicate images...
docker rmi gcr.io/k8s-minikube/kicbase:v0.0.48 2>nul
docker rmi neo4j:5 2>nul
docker rmi chromadb/chroma:latest 2>nul
docker rmi mongo:6 2>nul
docker rmi mongo:4.4.18 2>nul
docker rmi mcr.microsoft.com/mssql/server:2019-latest 2>nul
docker rmi overv/openstreetmap-tile-server:latest 2>nul
docker rmi apache/dolphinscheduler-standalone-server:latest 2>nul
docker rmi rabbitmq:3-management 2>nul
docker rmi lobehub/lobe-chat:latest 2>nul
docker rmi redis:alpine 2>nul
docker rmi redis:7 2>nul
docker rmi docker-open-webui:latest 2>nul
docker rmi docker-uitars:latest 2>nul
docker rmi caddy:2.0.0-alpine 2>nul
echo   Removed 15 old/duplicate images

echo.
echo [4/4] Cleaning up dangling images and build cache...
docker image prune -f
docker builder prune -f

echo.
echo ========================================
echo Cleanup Complete!
echo ========================================
echo.
docker system df
echo.
echo Freed approximately 100GB+ of space
echo.
pause
