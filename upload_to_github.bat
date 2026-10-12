@echo off
title Push to GitHub - AI-Flood-Early-Warning
color 0A

echo ===============================================================================
echo   Pushing NE-SHIELD to GitHub: arifshekh291172-web / AI-Flood-Early-Warning
echo ===============================================================================
echo.

echo Staging any modified files...
git add .
git commit -m "Update NE-SHIELD repository configuration and remove legacy naming" >nul 2>&1

echo.
echo Setting remote to https://github.com/arifshekh291172-web/AI-Flood-Early-Warning.git ...
git remote set-url origin https://github.com/arifshekh291172-web/AI-Flood-Early-Warning.git

echo.
echo Pushing to GitHub...
echo.
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ===============================================================================
    echo   [SUCCESS] Code successfully pushed to GitHub!
    echo   Repository URL: https://github.com/arifshekh291172-web/AI-Flood-Early-Warning
    echo ===============================================================================
) else (
    echo.
    echo ===============================================================================
    echo   [NOTICE] Authentication required or network error.
    echo ===============================================================================
)

echo.
pause
