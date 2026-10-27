"""Ядро оболочки: не зависит от GUI. Вывод идёт через self.sink(text, kind)."""
import base64
import posixpath

from .parser import parse, ParseError
from .vfs import Dir, File, FSError, resolve, NOENT, NOTDIR, ISDIR


class OptError(Exception):
    pass


class Shell:
    def __init__(self, vfs, username, hostname):
        self.vfs = vfs
        self.username = username
        self.hostname = hostname
        self.cwd = "/"
        self.sink = lambda text, kind: None   # kind: 'out' | 'err' | 'dbg'
        self.running = True
        self.exit_code = 0
        self.status = 0
        self.commands = {
            "ls": self.cmd_ls, "cd": self.cmd_cd, "whoami": self.cmd_whoami,
            "cat": self.cmd_cat, "mv": self.cmd_mv, "exit": self.cmd_exit,
        }

    # ---------- вывод ----------
    def out(self, s=""):
        self.sink(s + "\n", "out")

    def err(self, s):
        self.sink(s + "\n", "err")

    def prompt(self):
        return "%s@%s:%s$ " % (self.username, self.hostname, self.cwd)

    # ---------- выполнение ----------
    def execute(self, line):
        """Выполняет одну строку. Возвращает True при успехе."""
        try:
            argv = parse(line)
        except ParseError as e:
            self.err("emulator: %s" % e)
            self.status = 2
            return False
        if not argv:
            return True
        handler = self.commands.get(argv[0])
        if handler is None:
            self.err("%s: command not found" % argv[0])
            self.status = 127
            return False
        self.status = handler(argv[1:]) or 0
        return self.status == 0

    @staticmethod
    def script_lines(text):
        """Строки стартового скрипта без пустых."""
        return [l.rstrip("\r") for l in text.splitlines() if l.strip()]

    # ---------- вспомогательное ----------
    @staticmethod
    def _opts(cmd, args, allowed):
        opts, rest = set(), []
        for i, a in enumerate(args):
            if a == "--":
                rest.extend(args[i + 1:])
                break
            if a.startswith("--"):
                raise OptError("%s: unrecognized option '%s'" % (cmd, a))
            if a.startswith("-") and len(a) > 1:
                for ch in a[1:]:
                    if ch not in allowed:
                        raise OptError("%s: invalid option -- '%s'" % (cmd, ch))
                    opts.add(ch)
            else:
                rest.append(a)
        return opts, rest

    def _abs(self, path):
        return resolve(self.cwd, path)

    # ---------- ls ----------
    def cmd_ls(self, args):
        try:
            opts, paths = self._opts("ls", args, "la")
        except OptError as e:
            self.err(str(e))
            return 2
        paths = paths or ["."]
        status, files, dirs = 0, [], []
        for p in paths:
            try:
                ab = self._abs(p)
                node = self.vfs.lookup(ab)
            except FSError as e:
                self.err("ls: cannot access '%s': %s" % (p, e.msg))
                status = 2
                continue
            (dirs if isinstance(node, Dir) else files).append((p, ab, node))
        first = True
        if files:
            self._ls_print([(p, n) for p, _, n in sorted(files, key=lambda t: t[0])], "l" in opts)
            first = False
        for p, ab, node in sorted(dirs, key=lambda t: t[0]):
            if not first:
                self.out()
            if len(paths) > 1:
                self.out("%s:" % p)
            names = sorted(node.children, key=lambda n: (n.lower(), n))
            if "a" in opts:
                parent = self.vfs.lookup(resolve(ab, "..")) if ab != "/" else node
                entries = [(".", node), ("..", parent)]
                entries += [(n, node.children[n]) for n in names]
            else:
                entries = [(n, node.children[n]) for n in names if not n.startswith(".")]
            self._ls_print(entries, "l" in opts)
            first = False
        return status

    def _ls_print(self, entries, long):
        if not entries:
            return
        if not long:
            self.out("  ".join(n for n, _ in entries))
            return
        sizes = [str(len(nd.data)) if isinstance(nd, File) else "0" for _, nd in entries]
        w = max(len(s) for s in sizes)
        for (name, nd), size in zip(entries, sizes):
            perm = "drwxr-xr-x" if isinstance(nd, Dir) else "-rw-r--r--"
            self.out("%s %*s %s" % (perm, w, size, name))

    # ---------- cd ----------
    def cmd_cd(self, args):
        if len(args) > 1:
            self.err("cd: too many arguments")
            return 1
        target = args[0] if args else "/"
        if target == "~":
            target = "/"
        try:
            ab = self._abs(target)
            node = self.vfs.lookup(ab)
        except FSError as e:
            self.err("cd: %s: %s" % (target, e.msg))
            return 1
        if not isinstance(node, Dir):
            self.err("cd: %s: %s" % (target, NOTDIR))
            return 1
        self.cwd = ab
        return 0

    # ---------- whoami ----------
    def cmd_whoami(self, args):
        if args:
            self.err("whoami: extra operand '%s'" % args[0])
            return 1
        self.out(self.username)
        return 0

    # ---------- cat ----------
    def cmd_cat(self, args):
        try:
            opts, files = self._opts("cat", args, "n")
        except OptError as e:
            self.err(str(e))
            return 1
        if not files:
            self.err("cat: missing file operand")
            return 1
        status, num = 0, 1
        for f in files:
            try:
                node = self.vfs.lookup(self._abs(f))
            except FSError as e:
                self.err("cat: %s: %s" % (f, e.msg))
                status = 1
                continue
            if isinstance(node, Dir):
                self.err("cat: %s: %s" % (f, ISDIR))
                status = 1
                continue
            data = node.data
            try:
                if b"\0" in data:
                    raise UnicodeDecodeError("utf-8", b"", 0, 1, "nul")
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                self.sink("cat: %s: двоичный файл, содержимое показано в base64\n" % f, "dbg")
                b64 = base64.b64encode(data).decode("ascii")
                text = "\n".join(b64[i:i + 76] for i in range(0, len(b64), 76)) + "\n"
            if not text:
                continue
            if "n" in opts:
                out = []
                for line in text.splitlines(True):
                    out.append("%6d\t%s" % (num, line))
                    num += 1
                text = "".join(out)
            if not text.endswith("\n"):
                text += "\n"
            self.sink(text, "out")
        return status

    # ---------- mv ----------
    def cmd_mv(self, args):
        try:
            opts, ops = self._opts("mv", args, "vnf")
        except OptError as e:
            self.err(str(e))
            return 1
        if not ops:
            self.err("mv: missing file operand")
            return 1
        if len(ops) == 1:
            self.err("mv: missing destination file operand after '%s'" % ops[0])
            return 1
        srcs, dst = ops[:-1], ops[-1]
        try:
            dst_ab = self._abs(dst)
        except FSError:
            self.err("mv: cannot move to '%s': %s" % (dst, NOENT))
            return 1
        dst_node, dst_err = None, NOENT
        try:
            dst_node = self.vfs.lookup(dst_ab)
        except FSError as e:
            dst_err = e.msg
        dst_is_dir = isinstance(dst_node, Dir)
        if len(srcs) > 1 and not dst_is_dir:
            self.err("mv: target '%s': %s" % (dst, NOTDIR if dst_node is not None else dst_err))
            return 1
        status = 0
        for src in srcs:
            if not self._mv_one(src, dst, dst_ab, dst_is_dir, opts):
                status = 1
        return status

    def _mv_one(self, src, dst, dst_ab, dst_is_dir, opts):
        try:
            s_ab = self._abs(src)
            s_node = self.vfs.lookup(s_ab)
        except FSError as e:
            self.err("mv: cannot stat '%s': %s" % (src, e.msg))
            return False
        if s_ab == "/":
            self.err("mv: cannot move '%s' to '%s': Device or resource busy" % (src, dst))
            return False
        base = posixpath.basename(s_ab)
        target = posixpath.join(dst_ab, base) if dst_is_dir else dst_ab
        shown = posixpath.join(dst, base) if dst_is_dir else dst
        if target == s_ab:
            self.err("mv: '%s' and '%s' are the same file" % (src, shown))
            return False
        if isinstance(s_node, Dir) and target.startswith(s_ab.rstrip("/") + "/"):
            self.err("mv: cannot move '%s' to a subdirectory of itself, '%s'" % (src, shown))
            return False
        try:
            t_parent = self.vfs.lookup(posixpath.dirname(target))
            if not isinstance(t_parent, Dir):
                raise FSError(NOTDIR)
        except FSError as e:
            self.err("mv: cannot move '%s' to '%s': %s" % (src, dst, e.msg))
            return False
        t_name = posixpath.basename(target)
        existing = t_parent.children.get(t_name)
        if existing is not None:
            if "n" in opts:
                return True
            if isinstance(s_node, Dir) and not isinstance(existing, Dir):
                self.err("mv: cannot overwrite non-directory '%s' with directory '%s'" % (shown, src))
                return False
            if not isinstance(s_node, Dir) and isinstance(existing, Dir):
                self.err("mv: cannot overwrite directory '%s' with non-directory '%s'" % (shown, src))
                return False
            if isinstance(existing, Dir) and existing.children:
                self.err("mv: cannot move '%s' to '%s': Directory not empty" % (src, shown))
                return False
        s_parent = self.vfs.lookup(posixpath.dirname(s_ab))
        del s_parent.children[base]
        t_parent.children[t_name] = s_node
        if self.cwd == s_ab or self.cwd.startswith(s_ab + "/"):
            self.cwd = target + self.cwd[len(s_ab):]
        if "v" in opts:
            self.out("renamed '%s' -> '%s'" % (src, shown))
        return True

    # ---------- exit ----------
    def cmd_exit(self, args):
        if len(args) > 1:
            self.err("exit: too many arguments")
            return 1
        code = 0
        if args:
            try:
                code = int(args[0]) & 0xFF
            except ValueError:
                self.err("exit: %s: numeric argument required" % args[0])
                code = 2
        self.exit_code = code
        self.running = False
        return code
