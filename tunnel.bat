@echo off
:loop
echo [%date% %time%] Tunnel ishga tushmoqda...
lt --port 8080 --subdomain speakbotuz
echo [%date% %time%] Tunnel to'xtadi, qayta ishga tushirilmoqda...
timeout /t 3 /nobreak >nul
goto loop
