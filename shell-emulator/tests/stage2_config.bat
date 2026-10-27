@echo off
rem Этап 2 (Windows). Запуск из корня репозитория: tests\stage2_config.bat
chcp 65001 >nul
if "%PYTHON%"=="" set PYTHON=python
cd /d "%~dp0.."

echo == 1. Без параметров ==
(echo whoami& echo exit) | %PYTHON% main.py --headless
echo == 2. Только --vfs ==
echo exit | %PYTHON% main.py --headless --vfs vfs\minimal.zip
echo == 3. Только --script ==
%PYTHON% main.py --headless --script scripts\stage2_config.emu < nul
echo == 4. --vfs и --script ==
%PYTHON% main.py --headless --vfs vfs\files.zip --script scripts\stage3_vfs.emu < nul
echo == 5. Несуществующий скрипт ==
%PYTHON% main.py --headless --script scripts\no_such.emu
echo [код возврата: %ERRORLEVEL%]
echo == 6. Несуществующая VFS ==
%PYTHON% main.py --headless --vfs vfs\no_such.zip
echo [код возврата: %ERRORLEVEL%]
echo == 7. Неизвестный параметр ==
%PYTHON% main.py --bogus
echo [код возврата: %ERRORLEVEL%]
echo == 8. Справка ==
%PYTHON% main.py --help
