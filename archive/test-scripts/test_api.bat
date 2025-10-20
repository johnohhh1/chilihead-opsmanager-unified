@echo off
echo ========================================
echo  Testing API Routes with Database
echo ========================================
echo.

cd server
call .venv\Scripts\activate

echo [1/5] Testing database connection...
curl -s http://localhost:8002/db/health
echo.
echo.

echo [2/5] Testing tasks endpoints...
echo Creating a test task...
curl -X POST http://localhost:8002/tasks ^
  -H "Content-Type: application/json" ^
  -d "{\"title\":\"Test Database Task\",\"priority\":\"high\",\"source\":\"manual\"}"
echo.
echo.

echo Fetching all tasks...
curl -s http://localhost:8002/tasks
echo.
echo.

echo [3/5] Testing task stats...
curl -s http://localhost:8002/tasks/stats/summary
echo.
echo.

echo [4/5] Testing email state...
curl -X POST http://localhost:8002/email/track ^
  -H "Content-Type: application/json" ^
  -d "{\"email_id\":\"test_email_123\",\"subject\":\"Test Email\",\"sender\":\"test@example.com\"}"
echo.
echo.

echo [5/5] Testing delegations...
curl -s http://localhost:8002/delegations
echo.
echo.

echo ========================================
echo  Test Complete!
echo ========================================
echo.
echo If you saw JSON responses above, everything is working!
echo.
pause
