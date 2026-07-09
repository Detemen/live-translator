import queue
import tkinter as tk
from tkinter import font as tkfont


class FloatingWindow:
    """Always-on-top floating subtitle window with two translation channels."""

    def __init__(self):
        self.root = tk.Tk()
        self._q: queue.Queue = queue.Queue()
        self._build()
        self._poll()

    def _build(self):
        r = self.root
        r.title("Live Translator")
        r.geometry("660x200+300+820")
        r.attributes("-topmost", True)
        r.attributes("-alpha", 0.93)
        r.configure(bg="#0d1117")
        r.resizable(True, False)

        # Dragging
        r.bind("<ButtonPress-1>", lambda e: setattr(self, "_dx", e.x) or setattr(self, "_dy", e.y))
        r.bind("<B1-Motion>", lambda e: r.geometry(
            f"+{r.winfo_x() + e.x - self._dx}+{r.winfo_y() + e.y - self._dy}"))
        self._dx = self._dy = 0

        FONT_LABEL = ("Helvetica Neue", 9, "bold")
        FONT_ORIG   = ("Helvetica Neue", 9)
        FONT_TRANS  = ("Helvetica Neue", 12)
        BG_IN  = "#161b22"
        BG_OUT = "#0d2137"

        # ── Incoming (other person → Ukrainian) ──
        f_in = tk.Frame(r, bg=BG_IN, padx=8, pady=5)
        f_in.pack(fill="x", padx=5, pady=(5, 2))

        tk.Label(f_in, text="🎧 Співрозмовник → Українська",
                 font=FONT_LABEL, bg=BG_IN, fg="#58a6ff").pack(anchor="w")

        self._in_orig  = tk.StringVar(value="—")
        self._in_trans = tk.StringVar(value="—")

        tk.Label(f_in, textvariable=self._in_orig, font=FONT_ORIG,
                 bg=BG_IN, fg="#8b949e", wraplength=640, justify="left").pack(anchor="w")
        tk.Label(f_in, textvariable=self._in_trans, font=FONT_TRANS,
                 bg=BG_IN, fg="#e6edf3", wraplength=640, justify="left").pack(anchor="w")

        # ── Outgoing (user Ukrainian → target lang) ──
        f_out = tk.Frame(r, bg=BG_OUT, padx=8, pady=5)
        f_out.pack(fill="x", padx=5, pady=(2, 5))

        tk.Label(f_out, text="🎤 Ти → Переклад",
                 font=FONT_LABEL, bg=BG_OUT, fg="#f85149").pack(anchor="w")

        self._out_orig  = tk.StringVar(value="—")
        self._out_trans = tk.StringVar(value="—")

        tk.Label(f_out, textvariable=self._out_orig, font=FONT_ORIG,
                 bg=BG_OUT, fg="#8b949e", wraplength=640, justify="left").pack(anchor="w")
        tk.Label(f_out, textvariable=self._out_trans, font=FONT_TRANS,
                 bg=BG_OUT, fg="#e6edf3", wraplength=640, justify="left").pack(anchor="w")

        # Status bar
        self._status_var = tk.StringVar(value="● Ready")
        tk.Label(r, textvariable=self._status_var, font=("Helvetica Neue", 8),
                 bg="#0d1117", fg="#3fb950", anchor="e").pack(fill="x", padx=8)

    def update_incoming(self, original: str, translation: str):
        self._q.put(("in", original, translation))

    def update_outgoing(self, original: str, translation: str):
        self._q.put(("out", original, translation))

    def set_status(self, text: str):
        self._q.put(("status", text))

    def _poll(self):
        try:
            while True:
                item = self._q.get_nowait()
                if item[0] == "in":
                    self._in_orig.set(item[1][:140])
                    self._in_trans.set(item[2][:140])
                elif item[0] == "out":
                    self._out_orig.set(item[1][:140])
                    self._out_trans.set(item[2][:140])
                elif item[0] == "status":
                    self._status_var.set(item[1])
        except queue.Empty:
            pass
        self.root.after(80, self._poll)

    def run(self):
        self.root.mainloop()
