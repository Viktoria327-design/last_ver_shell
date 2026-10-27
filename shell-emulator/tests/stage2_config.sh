#!/usr/bin/env bash
# Этап 2: проверка параметров командной строки. Запуск из корня репозитория: bash tests/stage2_config.sh
PY=${PYTHON:-python3}
run() { echo; echo "\$ $*"; "$@"; echo "[код возврата: $?]"; }
cd "$(dirname "$0")/.." || exit 1

echo "== 1. Без параметров (интерактивный ввод из stdin) =="
printf 'whoami\nexit\n' | run $PY main.py --headless
echo "== 2. Только --vfs =="
printf 'exit\n' | run $PY main.py --headless --vfs vfs/minimal.zip
echo "== 3. Только --script =="
run $PY main.py --headless --script scripts/stage2_config.emu </dev/null
echo "== 4. --vfs и --script вместе =="
run $PY main.py --headless --vfs vfs/files.zip --script scripts/stage3_vfs.emu </dev/null
echo "== 5. Несуществующий скрипт (ошибка) =="
run $PY main.py --headless --script scripts/no_such.emu
echo "== 6. Несуществующая VFS (ошибка) =="
run $PY main.py --headless --vfs vfs/no_such.zip
echo "== 7. Неизвестный параметр =="
run $PY main.py --bogus
echo "== 8. Справка =="
run $PY main.py --help
echo
echo "GUI-режим (откроет окно): $PY main.py --vfs vfs/deep.zip --script scripts/full_test.emu"
