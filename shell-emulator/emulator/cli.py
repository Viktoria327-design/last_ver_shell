"""Точка входа: параметры командной строки, отладочный вывод, запуск GUI / консоли."""
import argparse
import getpass
import os
import socket
import sys

from .shell import Shell
from .vfs import VFS, VFSError


def real_identity():
    try:
        user = getpass.getuser()
    except Exception:
        user = os.environ.get("USER") or os.environ.get("USERNAME") or "user"
    return user, socket.gethostname() or "localhost"


def build_parser():
    p = argparse.ArgumentParser(
        prog="emulator",
        description="Эмулятор оболочки UNIX-подобной ОС (GUI) с виртуальной ФС из ZIP-архива.")
    p.add_argument("--vfs", metavar="PATH", help="путь к ZIP-архиву с VFS (по умолчанию — пустая ФС)")
    p.add_argument("--script", metavar="PATH", help="путь к стартовому скрипту с командами эмулятора")
    p.add_argument("--headless", action="store_true",
                   help="консольный режим без окна (для автоматических тестов)")
    return p


def fail(msg, headless):
    sys.stderr.write("emulator: %s\n" % msg)
    if not headless:
        try:
            import tkinter
            from tkinter import messagebox
            r = tkinter.Tk()
            r.withdraw()
            messagebox.showerror("Эмулятор — ошибка", msg)
            r.destroy()
        except Exception:
            pass
    return 1


def console_sink(text, kind):
    stream = sys.stderr if kind == "err" else sys.stdout
    stream.write(text)
    stream.flush()


def run_headless(shell, debug_lines, script_lines):
    shell.sink = console_sink
    for d in debug_lines:
        console_sink(d + "\n", "dbg")
    for line in script_lines:
        console_sink(shell.prompt() + line + "\n", "out")
        shell.execute(line)
        if not shell.running:
            return shell.exit_code
    tty = sys.stdin.isatty()
    while shell.running:
        if tty:
            try:
                line = input(shell.prompt())
            except EOFError:
                print()
                break
        else:
            console_sink(shell.prompt(), "out")
            line = sys.stdin.readline()
            if not line:
                console_sink("\n", "out")
                break
            line = line.rstrip("\r\n")
            console_sink(line + "\n", "out")
        shell.execute(line)
    return shell.exit_code


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    args = build_parser().parse_args(argv)
    user, host = real_identity()
    title = "Эмулятор - [%s@%s]" % (user, host)

    debug = [
        "[debug] Параметры запуска:",
        "[debug]   --vfs      = %s" % (os.path.abspath(args.vfs) if args.vfs else "(не задан — пустая VFS)"),
        "[debug]   --script   = %s" % (os.path.abspath(args.script) if args.script else "(не задан)"),
        "[debug]   --headless = %s" % args.headless,
        "[debug]   пользователь ОС = %s, хост = %s" % (user, host),
        "[debug]   заголовок окна  = %s" % title,
    ]

    if args.vfs:
        try:
            vfs = VFS.from_zip(args.vfs)
        except VFSError as e:
            return fail("ошибка загрузки VFS: %s" % e, args.headless)
        debug.append("[debug]   VFS загружена в память из ZIP-архива")
    else:
        vfs = VFS()

    script_lines = []
    if args.script:
        try:
            with open(args.script, encoding="utf-8-sig", errors="replace") as f:
                script_lines = Shell.script_lines(f.read())
        except OSError as e:
            return fail("не удалось прочитать скрипт '%s': %s" % (args.script, e.strerror or e),
                        args.headless)

    shell = Shell(vfs, user, host)
    if args.headless:
        return run_headless(shell, debug, script_lines)
    try:
        from .gui import run_gui
    except ImportError:
        return fail("tkinter недоступен; запустите с параметром --headless", True)
    return run_gui(shell, title, debug, script_lines)
