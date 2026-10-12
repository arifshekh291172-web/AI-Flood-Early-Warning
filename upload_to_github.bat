@echo off
title Push to GitHub - Theem-Warrior-AI-Flood-Early-Warning
color 0A

echo ===============================================================================
echo   Pushing NE-SHIELD to GitHub: arifshekh291172-web / Theem-Warrior-AI-Flood
echo ===============================================================================
echo.

echo Staging any modified files...
git add .
git commit -m "Complete NE-SHIELD AI Landslide & Flood Warning with Bhuvan Satellite & GIS Command Center" >nul 2>&1

echo.
echo Setting remote to https://github.com/arifshekh291172-web/Theem-Warrior-AI-Flood-Early-Warning.git ...
git remote set-url origin https://github.com/arifshekh291172-web/Theem-Warrior-AI-Flood-Early-Warning.git

echo.
echo Pushing to GitHub (A browser window will open if sign-in is required)...
echo.
git push -u origin main --force

if %errorlevel% equ 0 (
    echo.
    echo ===============================================================================
    echo   [SUCCESS] Code successfully pushed to GitHub!
    echo   Repository URL: https://github.com/arifshekh291172-web/Theem-Warrior-AI-Flood-Early-Warning
    echo ===============================================================================
) else (
    echo.
    echo ===============================================================================
    echo   [NOTICE] If GitHub asked for authentication, please sign in with:
    echo   Account: arifshekh291172-web (arifshekh291172@gmail.com)
    echo ===============================================================================
)

echo.
pause
