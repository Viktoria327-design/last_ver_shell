#!/usr/bin/env bash
# Этап 3: разные варианты VFS. Запуск из корня репозитория: bash tests/stage3_vfs.sh
PY=${PYTHON:-python3}
run() { echo; echo "\$ $*"; "$@"; echo "[код возврата: $?]"; }
cd "$(dirname "$0")/.." || exit 1
$PY tools/make_vfs.py

for z in minimal files deep; do
  echo; echo "===== VFS: $z.zip ====="
  printf 'ls\nls -la /\ncd /\nls /\nexit\n' | run $PY main.py --headless --vfs vfs/$z.zip
done

echo; echo "===== VFS с вложенностью >= 3 уровней ====="
printf 'ls /home/user/docs/archive/2024/final\ncat /home/user/docs/archive/2024/final/summary.txt\ncd /home/user/docs/archive/2024/final\ncd ../../../..\nls\nexit\n' \
  | run $PY main.py --headless --vfs vfs/deep.zip

echo; echo "===== Ошибки загрузки VFS ====="
for bad in no_such.zip not_a_zip.zip truncated.zip empty.zip; do
  run $PY main.py --headless --vfs vfs/$bad
done
run $PY main.py --headless --vfs vfs

echo; echo "===== Стартовый скрипт для всех команд ====="
run $PY main.py --headless --vfs vfs/deep.zip --script scripts/full_test.emu
