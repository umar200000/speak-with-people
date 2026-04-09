@echo off
echo ========================================
echo   Speak Bot ishga tushmoqda...
echo ========================================

:: Python serverlarni ishga tushirish
start /B "" "C:\Users\Umar\AppData\Local\Programs\Python\Python312\python.exe" "C:\Users\Umar\Desktop\speak\admin.py"
start /B "" "C:\Users\Umar\AppData\Local\Programs\Python\Python312\python.exe" "C:\Users\Umar\Desktop\speak\webapp.py"
start /B "" "C:\Users\Umar\AppData\Local\Programs\Python\Python312\python.exe" "C:\Users\Umar\Desktop\speak\bot.py"

:: 3 soniya kutish
timeout /t 3 /nobreak >nul

:: Cloudflare tunnel ishga tushirish
echo.
echo   Cloudflare tunnel ishga tushmoqda...
echo   Admin panel: http://localhost:3000
echo ========================================
"C:\Users\Umar\Desktop\cloudflared.exe" tunnel --url http://localhost:8080
