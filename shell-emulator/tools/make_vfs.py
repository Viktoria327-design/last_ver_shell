"""Генерирует тестовые VFS-архивы в каталоге vfs/ (запускать из корня репозитория).

minimal.zip  — минимальная VFS (один файл)
files.zip    — несколько файлов в корне (есть скрытый, пустой и с пробелом в имени)
deep.zip     — вложенность более 3 уровней, пустой каталог и двоичный файл
not_a_zip.zip, truncated.zip, empty.zip — заведомо некорректные архивы для проверки ошибок
"""
import base64
import os
import zipfile

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vfs")
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")


def make(name, entries):
    with zipfile.ZipFile(os.path.join(OUT, name), "w", zipfile.ZIP_DEFLATED) as z:
        for path, data in entries.items():
            z.writestr(path, data)


def main():
    os.makedirs(OUT, exist_ok=True)
    make("minimal.zip", {"readme.txt": "Minimal VFS\n"})
    make("files.zip", {
        "hello.txt": "Hello, world!\n",
        "notes.txt": "line one\nline two\nline three\n",
        "todo.md": "# TODO\n- write tests\n- commit\n",
        "data.csv": "id,name\n1,alpha\n2,beta\n",
        ".hidden": "secret\n",
        "empty.txt": "",
        "my file.txt": "file with a space in its name\n",
    })
    make("deep.zip", {
        "home/user/docs/report.txt": "Quarterly report\n",
        "home/user/docs/archive/2024/q1.txt": "Q1 numbers\n",
        "home/user/docs/archive/2024/q2.txt": "Q2 numbers\n",
        "home/user/docs/archive/2024/final/summary.txt": "Summary (5 levels deep)\n",
        "home/user/pictures/logo.png": PNG,
        "home/user/.config/settings.ini": "[ui]\ntheme=dark\n",
        "etc/hostname": "vfs-host\n",
        "etc/motd": "Welcome to the virtual file system!\n",
        "var/log/system.log": "boot ok\nservice started\n",
        "tmp/": b"",
    })
    with open(os.path.join(OUT, "not_a_zip.zip"), "w") as f:
        f.write("this is plain text, not a ZIP archive\n")
    with open(os.path.join(OUT, "deep.zip"), "rb") as f:
        raw = f.read()
    with open(os.path.join(OUT, "truncated.zip"), "wb") as f:
        f.write(raw[:len(raw) // 2])
    open(os.path.join(OUT, "empty.zip"), "wb").close()
    print("VFS archives written to", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
