@echo off
echo ========================================
echo   Fix Git and Push to GitHub
echo ========================================
echo.

cd /d "C:\Users\John\Desktop\chilihead-opsmanager-unified"

echo Removing large GGUF file from git...
git rm --cached gemma-3n.gguf
echo.

echo Creating .gitignore to prevent future issues...
echo # Large model files >> .gitignore
echo *.gguf >> .gitignore
echo *.bin >> .gitignore
echo *.safetensors >> .gitignore
echo # Modelfiles >> .gitignore
echo *.modelfile >> .gitignore
echo # Batch scripts for local use >> .gitignore
echo OLLAMA_START.bat >> .gitignore
echo PERMANENT_OLLAMA_FIX.bat >> .gitignore
echo RESET_OLLAMA.bat >> .gitignore
echo WORKING_START.bat >> .gitignore
echo start_ollama*.bat >> .gitignore
echo.

echo Committing the cleanup...
git add .gitignore
git commit -m "Remove large files and add gitignore"

echo.
echo Pushing to correct branch (master)...
git push origin master

echo.
echo ========================================
echo   Push Complete!
echo ========================================
pause
