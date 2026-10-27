"""Виртуальная файловая система в памяти. Источник — ZIP-архив.

Архив читается один раз; на диск ничего не распаковывается и не записывается.
Содержимое файлов хранится как bytes (двоичные данные при выводе кодируются в base64).
"""
import posixpath
import zipfile
import zlib

NOENT = "No such file or directory"
NOTDIR = "Not a directory"
ISDIR = "Is a directory"


class VFSError(Exception):
    """Ошибка загрузки VFS."""


class FSError(Exception):
    """Ошибка операции над путём внутри VFS (msg — текст в стиле strerror)."""

    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg


class File:
    __slots__ = ("data",)

    def __init__(self, data=b""):
        self.data = data


class Dir:
    __slots__ = ("children",)

    def __init__(self):
        self.children = {}


def resolve(cwd, path):
    """Абсолютный нормализованный путь для path относительно cwd."""
    if path == "":
        raise FSError(NOENT)
    p = posixpath.normpath(posixpath.join(cwd, path))
    return "/" + p.lstrip("/")


class VFS:
    def __init__(self):
        self.root = Dir()

    def lookup(self, abspath):
        node = self.root
        for part in abspath.split("/"):
            if not part:
                continue
            if not isinstance(node, Dir):
                raise FSError(NOTDIR)
            node = node.children.get(part)
            if node is None:
                raise FSError(NOENT)
        return node

    @classmethod
    def from_zip(cls, path):
        vfs = cls()
        try:
            zf = zipfile.ZipFile(path)
        except FileNotFoundError:
            raise VFSError("файл не найден: '%s'" % path)
        except IsADirectoryError:
            raise VFSError("'%s' — каталог, а не ZIP-архив" % path)
        except PermissionError:
            raise VFSError("нет доступа к файлу: '%s'" % path)
        except zipfile.BadZipFile:
            raise VFSError("неверный формат (не ZIP-архив или архив повреждён): '%s'" % path)
        except OSError as e:
            raise VFSError("не удалось открыть '%s': %s" % (path, e.strerror or e))
        with zf:
            for info in zf.infolist():
                parts = [p for p in info.filename.split("/") if p not in ("", ".")]
                if ".." in parts:
                    raise VFSError("небезопасный путь в архиве: '%s'" % info.filename)
                is_dir = info.is_dir()
                node = vfs.root
                for d in (parts if is_dir else parts[:-1]):
                    nxt = node.children.get(d)
                    if nxt is None:
                        nxt = node.children[d] = Dir()
                    elif isinstance(nxt, File):
                        raise VFSError("конфликт имён в архиве: '%s'" % info.filename)
                    node = nxt
                if is_dir or not parts:
                    continue
                try:
                    data = zf.read(info)
                except (zipfile.BadZipFile, RuntimeError, NotImplementedError,
                        zlib.error, EOFError) as e:
                    raise VFSError("повреждённые данные в архиве ('%s'): %s" % (info.filename, e))
                if isinstance(node.children.get(parts[-1]), Dir):
                    raise VFSError("конфликт имён в архиве: '%s'" % info.filename)
                node.children[parts[-1]] = File(data)
        return vfs
