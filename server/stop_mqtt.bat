@echo off
echo [INFO] Завершение работы Mosquitto...
taskkill /F /IM mosquitto.exe >nul 2>&1

IF %ERRORLEVEL% EQU 0 (
    echo [OK] Mosquitto остановлен.
) ELSE (
    echo [WARNING] Mosquitto не найден или уже остановлен.
)
pause
