"""GUI-терминал на tkinter."""
import tkinter as tk
import tkinter.font as tkfont

SCRIPT_DELAY_MS = 150


def run_gui(shell, title, debug_lines, script_lines):
    root = tk.Tk()
    root.title(title)
    root.geometry("900x560")
    root.configure(bg="#1e1e1e")

    fams = set(tkfont.families())
    family = next((f for f in ("Consolas", "DejaVu Sans Mono", "Menlo", "Courier New")
                   if f in fams), "TkFixedFont")
    font = (family, 11)

    frame = tk.Frame(root, bg="#1e1e1e")
    frame.pack(fill="both", expand=True)
    text = tk.Text(frame, bg="#1e1e1e", fg="#d4d4d4", font=font, wrap="word",
                   state="disabled", relief="flat", padx=8, pady=6, cursor="arrow")
    sb = tk.Scrollbar(frame, command=text.yview)
    text.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    text.pack(side="left", fill="both", expand=True)
    text.tag_configure("err", foreground="#f48771")
    text.tag_configure("dbg", foreground="#808080")
    text.tag_configure("prompt", foreground="#6a9955")
    text.tag_configure("cmd", foreground="#ffffff")

    bottom = tk.Frame(root, bg="#252526")
    bottom.pack(fill="x")
    prompt_lbl = tk.Label(bottom, text=shell.prompt(), bg="#252526", fg="#6a9955", font=font)
    prompt_lbl.pack(side="left", padx=(8, 0))
    entry = tk.Entry(bottom, bg="#252526", fg="#ffffff", insertbackground="#ffffff",
                     font=font, relief="flat")
    entry.pack(side="left", fill="x", expand=True, padx=4, pady=6)

    def write(txt, kind="out"):
        text.configure(state="normal")
        text.insert("end", txt, kind if kind != "out" else ())
        text.see("end")
        text.configure(state="disabled")

    shell.sink = write
    history, pos = [], [0]

    def echo(line):
        write(shell.prompt(), "prompt")
        write(line + "\n", "cmd")

    def after_command():
        prompt_lbl.configure(text=shell.prompt())
        if not shell.running:
            write("logout\n", "dbg")
            entry.configure(state="disabled")
            root.after(700, root.destroy)

    def on_enter(_event=None):
        line = entry.get()
        entry.delete(0, "end")
        echo(line)
        if line.strip():
            history.append(line)
        pos[0] = len(history)
        shell.execute(line)
        after_command()

    def hist(delta):
        if not history:
            return "break"
        pos[0] = max(0, min(len(history), pos[0] + delta))
        entry.delete(0, "end")
        if pos[0] < len(history):
            entry.insert(0, history[pos[0]])
        return "break"

    entry.bind("<Return>", on_enter)
    entry.bind("<Up>", lambda e: hist(-1))
    entry.bind("<Down>", lambda e: hist(1))
    text.bind("<Button-1>", lambda e: (entry.focus_set(), "break")[1])

    for d in debug_lines:
        write(d + "\n", "dbg")

    if script_lines:
        entry.configure(state="disabled")
        it = iter(script_lines)

        def step():
            if not shell.running:
                return
            line = next(it, None)
            if line is None:
                entry.configure(state="normal")
                entry.focus_set()
                return
            echo(line)
            shell.execute(line)
            after_command()
            root.after(SCRIPT_DELAY_MS, step)

        root.after(300, step)
    else:
        entry.focus_set()
    root.mainloop()
    return shell.exit_code
