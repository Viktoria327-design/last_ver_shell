# Эмулятор оболочки UNIX (GUI)

Python 3.8+, tkinter (в стандартной поставке; на Debian/Ubuntu: `sudo apt install python3-tk`).
Внешних зависимостей нет.

## Запуск
```
python main.py                                   # окно, пустая VFS
python main.py --vfs vfs/deep.zip                # VFS из ZIP-архива
python main.py --script scripts/full_test.emu    # стартовый скрипт
python main.py --vfs vfs/deep.zip --script scripts/full_test.emu
python main.py --headless ...                    # консольный режим без окна (автотесты)
```
Заголовок окна: `Эмулятор - [username@hostname]` (реальные данные ОС). При запуске в терминал
выводятся отладочные строки `[debug]` со всеми параметрами.

## Структура
| Путь | Назначение |
|---|---|
| `emulator/parser.py` | разбор строки: кавычки `'..'`/`".."`, `\` , комментарии `#` |
| `emulator/vfs.py` | VFS в памяти из ZIP; ошибки загрузки (нет файла, неверный формат) |
| `emulator/shell.py` | ядро: `ls [-la]`, `cd`, `whoami`, `cat [-n]`, `mv [-vnf]`, `exit [N]` |
| `emulator/gui.py`, `cli.py` | окно tkinter; параметры `--vfs`, `--script`, `--headless` |
| `tools/make_vfs.py` | генерирует `vfs/*.zip` (минимальный, несколько файлов, 5 уровней, битые) |
| `scripts/*.emu` | стартовые скрипты эмулятора по этапам и `full_test.emu` |
| `tests/*.sh`, `tests/*.bat` | скрипты реальной ОС (Linux/macOS и Windows) с вызовами эмулятора |
| `docs/demo_*.txt` | записанные прогоны (ввод + вывод, включая ошибки) |

## Поведение
* Всё в памяти: ZIP читается один раз, ничего не распаковывается и не записывается. `mv` меняет только
  дерево в памяти. Двоичные файлы (не UTF-8 / с NUL) `cat` показывает в base64.
* Стартовый скрипт: каждая строка выводится как ввод (с приглашением), затем вывод; ошибочные строки
  дают сообщение и пропускаются. Пустые строки пропускаются, `# ...` — комментарий.
* Коды: ошибка загрузки VFS или чтения скрипта — сообщение + код 1; `exit N` — код N.
* Прав доступа в VFS нет: `ls -l` показывает условные `drwxr-xr-x` / `-rw-r--r--` и размер в байтах.

## Проверка
```
bash tests/stage2_config.sh        # параметры командной строки
bash tests/stage3_vfs.sh           # варианты VFS, ошибки загрузки, полный скрипт
python main.py --headless --vfs vfs/deep.zip --script scripts/stage4_basic.emu
python main.py --headless --vfs vfs/deep.zip --script scripts/stage5_mv.emu
```
(на Windows: `tests\stage2_config.bat`, `tests\stage3_vfs.bat`)

## Коммиты по этапам (Conventional Commits)
1. `feat(repl): GUI-терминал, заголовок из данных ОС, парсер с кавычками, ls/cd-заглушки, exit`
2. `feat(config): параметры --vfs/--script, стартовые скрипты, отладочный вывод, тесты ОС-скриптами`
3. `feat(vfs): VFS из ZIP в памяти, ошибки загрузки, тестовые архивы и скрипты`
4. `feat(commands): ls, cd, whoami, cat и скрипт проверки`
5. `feat(mv): команда mv (только в памяти) и скрипт проверки`
