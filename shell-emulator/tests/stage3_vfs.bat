@echo off
rem Этап 3 (Windows). Запуск из корня репозитория: tests\stage3_vfs.bat
chcp 65001 >nul
if "%PYTHON%"=="" set PYTHON=python
cd /d "%~dp0.."
%PYTHON% tools\make_vfs.py

for %%Z in (minimal files deep) do (
  echo ===== VFS: %%Z.zip =====
  (echo ls& echo ls -la /& echo cd /& echo ls /& echo exit) | %PYTHON% main.py --headless --vfs vfs\%%Z.zip
)

echo ===== Вложенность ^>= 3 уровней =====
(echo ls /home/user/docs/archive/2024/final& echo cat /home/user/docs/archive/2024/final/summary.txt& echo exit) | %PYTHON% main.py --headless --vfs vfs\deep.zip

echo ===== Ошибки загрузки VFS =====
for %%B in (no_such not_a_zip truncated empty) do (
  %PYTHON% main.py --headless --vfs vfs\%%B.zip
  echo [код возврата: %ERRORLEVEL%]
)

echo ===== Полный стартовый скрипт =====
%PYTHON% main.py --headless --vfs vfs\deep.zip --script scripts\full_test.emu
