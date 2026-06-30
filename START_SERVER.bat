@echo off
title Assetdigit CMMS
echo.
echo  =========================================
echo   Assetdigit CMMS - Starting...
echo  =========================================
echo.
echo  Your data is safe. Starting server...
echo.
cd /d "%~dp0"
python manage.py runserver
pause
