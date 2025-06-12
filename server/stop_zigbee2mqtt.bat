@echo off
echo [INFO] Попытка завершить окно Zigbee2MQTT...
taskkill /FI "WINDOWTITLE eq Zigbee2MQTT*" /F
echo [INFO] Zigbee2MQTT остановлен.
pause
