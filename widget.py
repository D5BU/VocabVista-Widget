import tkinter as tk
from pathlib import Path
import json, os

LIST_PATH = Path("oxford3000.txt")
STATE_FILE = Path("widget_state.json")

def load_items(path=LIST_PATH):
    items = []
    if path.exists():
        for raw in path.read_text(encoding="utf-8").splitlines():
            s = raw.strip()
            if not s:
                continue
            if " - " in s:
                w, m = s.split(" - ", 1)
            else:
                w, m = s, ""
            items.append((w.strip(), m.strip()))
    if not items:
        items = [("Add words to oxford3000.txt", "Format: word - meaning")]
    return items

def load_state():
    if STATE_FILE.exists():
        try:
            s = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            return s.get("index", 0), s.get("interval", 60), s.get("frameless", False), s.get("ambient", False)
        except:
            pass
    return 0, 60, False, False

def save_state(index, interval, frameless, ambient):
    try:
        STATE_FILE.write_text(json.dumps({"index": index, "interval": interval, "frameless": frameless, "ambient": ambient}), encoding="utf-8")
    except:
        pass

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.bg_steps = ["#1e1e1e","#202024","#212228","#22242c","#232531","#242736","#25283a","#262a3f","#272b43","#282c46","#272b43","#262a3f","#25283a","#242736","#232531","#22242c","#212228","#202024"]
        self.bg_i = 0
        self.items = load_items()
        self.i, self.interval, start_frameless, start_ambient = load_state()
        self.remaining = self.interval
        self.running = True

        self.configure(bg="#1e1e1e")
        self.geometry("460x260")
        self.minsize(340, 160)
        self.attributes("-topmost", True)

        self.root_frame = tk.Frame(self, bg="#1e1e1e")
        self.root_frame.pack(fill="both", expand=True, padx=14, pady=14)
        self.root_frame.bind("<Button-1>", self._start_move)
        self.root_frame.bind("<B1-Motion>", self._on_move)

        topbar = tk.Frame(self.root_frame, bg="#1e1e1e")
        topbar.pack(fill="x")
        self.close_btn = tk.Button(topbar, text="✕", command=self.destroy, width=3, bg="#333333", fg="#ffffff", relief="flat")
        self.close_btn.pack(side="right")

        self.word_lbl = tk.Label(self.root_frame, font=("Segoe UI", 22, "bold"), wraplength=420, justify="center", fg="#ffffff", bg="#1e1e1e")
        self.word_lbl.pack(pady=(10, 8), padx=6, fill="x")

        self.mean_lbl = tk.Label(self.root_frame, font=("Segoe UI", 12), wraplength=430, justify="center", fg="#cfcfcf", bg="#1e1e1e")
        self.mean_lbl.pack(pady=(0, 12), padx=6, fill="x")

        btns = tk.Frame(self.root_frame, bg="#1e1e1e")
        btns.pack(pady=(0, 8))
        tk.Button(btns, text="◀ Prev", width=8, command=self.prev_item, bg="#3a3a3a", fg="#ffffff", relief="flat").pack(side="left", padx=6)
        tk.Button(btns, text="Next ▶", width=8, command=self.next_item, bg="#3a3a3a", fg="#ffffff", relief="flat").pack(side="left", padx=6)
        self.toggle_btn = tk.Button(btns, text="⏸ Pause", width=10, command=self.toggle_run, bg="#4a4a4a", fg="#ffffff", relief="flat")
        self.toggle_btn.pack(side="left", padx=6)

        ctrl = tk.Frame(self.root_frame, bg="#1e1e1e")
        ctrl.pack()
        tk.Label(ctrl, text="Seconds:", fg="#aaaaaa", bg="#1e1e1e").pack(side="left")
        self.ent = tk.Entry(ctrl, width=5, justify="center", bg="#222222", fg="#ffffff", relief="flat")
        self.ent.insert(0, str(self.interval))
        self.ent.pack(side="left", padx=4)
        self.ent.bind("<Return>", self.set_interval)
        self.time_lbl = tk.Label(ctrl, text=f"{self.remaining}s", fg="#aaaaaa", bg="#1e1e1e")
        self.time_lbl.pack(side="left", padx=6)

        extra = tk.Frame(self.root_frame, bg="#1e1e1e")
        extra.pack(pady=(6, 0), fill="x")
        self.topmost_var = tk.BooleanVar(value=True)
        tk.Checkbutton(extra, text="Always on top", variable=self.topmost_var, command=self.apply_topmost,
                       fg="#cccccc", bg="#1e1e1e", activeforeground="#ffffff", activebackground="#1e1e1e",
                       selectcolor="#1e1e1e").pack(side="left", padx=(0,10))
        tk.Label(extra, text="Opacity:", fg="#cccccc", bg="#1e1e1e").pack(side="left")
        self.opacity_var = tk.DoubleVar(value=0.90)
        tk.Scale(extra, from_=0.5, to=1.0, resolution=0.05, orient="horizontal", variable=self.opacity_var,
                 command=self.apply_opacity, length=120, fg="#cccccc", bg="#1e1e1e",
                 troughcolor="#333333", highlightthickness=0).pack(side="left", padx=(4,16))

        self.frameless_var = tk.BooleanVar(value=start_frameless)
        tk.Checkbutton(extra, text="Frameless", variable=self.frameless_var, command=self.apply_frameless,
                       fg="#cccccc", bg="#1e1e1e", activeforeground="#ffffff", activebackground="#1e1e1e",
                       selectcolor="#1e1e1e").pack(side="left", padx=(0,12))

        self.ambient_var = tk.BooleanVar(value=start_ambient)
        tk.Checkbutton(extra, text="Ambient", variable=self.ambient_var, command=self.toggle_ambient,
                       fg="#cccccc", bg="#1e1e1e", activeforeground="#ffffff", activebackground="#1e1e1e",
                       selectcolor="#1e1e1e").pack(side="left")

        self.bind("<Left>", lambda e: self.prev_item())
        self.bind("<Right>", lambda e: self.next_item())
        self.bind("<space>", lambda e: self.toggle_run())

        self.apply_topmost()
        self.apply_opacity()
        self.apply_frameless()
        self.update_view()
        self.tick()
        if self.ambient_var.get():
            self.animate_bg()

    def update_view(self):
        w, m = self.items[self.i]
        self.word_lbl.config(text=w)
        self.mean_lbl.config(text=m)
        self.time_lbl.config(text=f"{self.remaining}s")
        save_state(self.i, self.interval, self.frameless_var.get(), self.ambient_var.get())

    def next_item(self):
        self.i = (self.i + 1) % len(self.items)
        self.remaining = self.interval
        self.update_view()

    def prev_item(self):
        self.i = (self.i - 1) % len(self.items)
        self.remaining = self.interval
        self.update_view()

    def toggle_run(self):
        self.running = not self.running
        self.toggle_btn.config(text="▶ Resume" if not self.running else "⏸ Pause")

    def set_interval(self, event=None):
        try:
            v = int(self.ent.get())
            if v < 1: raise ValueError
            self.interval = v
            self.remaining = v
        except:
            self.ent.delete(0, 'end')
            self.ent.insert(0, str(self.interval))

    def tick(self):
        if self.running:
            self.remaining -= 1
            if self.remaining <= 0:
                self.next_item()
        self.update_view()
        self.after(1000, self.tick)

    def apply_topmost(self):
        self.attributes("-topmost", bool(self.topmost_var.get()))

    def apply_opacity(self, *_):
        try:
            self.attributes("-alpha", float(self.opacity_var.get()))
        except:
            pass

    def apply_frameless(self):
        self.overrideredirect(1 if self.frameless_var.get() else 0)

    def _start_move(self, e):
        self._x = e.x_root
        self._y = e.y_root
        self._ox = self.winfo_x()
        self._oy = self.winfo_y()

    def _on_move(self, e):
        if self.frameless_var.get():
            dx = e.x_root - self._x
            dy = e.y_root - self._y
            self.geometry(f"+{self._ox + dx}+{self._oy + dy}")

    def toggle_ambient(self):
        if self.ambient_var.get():
            self.animate_bg()

    def animate_bg(self):
        if not self.ambient_var.get():
            return
        self.bg_i = (self.bg_i + 1) % len(self.bg_steps)
        c = self.bg_steps[self.bg_i]
        self.configure(bg=c)
        self.root_frame.configure(bg=c)
        for w in (self.word_lbl, self.mean_lbl, self.time_lbl):
            w.configure(bg=c)
        for child in self.root_frame.winfo_children():
            if isinstance(child, tk.Frame) or isinstance(child, tk.Checkbutton) or isinstance(child, tk.Scale) or isinstance(child, tk.Label) or isinstance(child, tk.Button):
                try: child.configure(bg=c)
                except: pass
        self.after(300, self.animate_bg)

if __name__ == "__main__":
    App().mainloop()
