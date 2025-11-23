@echo off
REM Scheduled Memory Cleanup
REM Run this daily to keep memory system clean

echo ========================================
echo Memory System Maintenance
echo ========================================

cd /d "C:\Users\John\Desktop\chilihead-opsmanager-unified\server"

REM Activate virtual environment
call .venv\Scripts\activate

echo.
echo Running memory maintenance...
python memory_maintenance.py --all

echo.
echo Memory maintenance complete!
echo.

pause