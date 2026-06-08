from __future__ import annotations

import math
import tkinter as tk
from tkinter import messagebox, ttk
from typing import List, Optional, Tuple

from demoucron import DemoucronResult, build_path, demoucron_max, demoucron_min

# ═══════════════════════════════════════════════════════════════
#  PALETTE — Charte Data Terra 2020
# ═══════════════════════════════════════════════════════════════
C = {
    "violet":       "#2E2253",
    "violet_l":     "#3D2F70",
    "cyan":         "#08B0A0",
    "cyan_l":       "#0ACFBC",
    "cyan_bg":      "#E6F7F6",
    "bg":           "#F4F5F7",
    "surface":      "#FAFBFC",
    "surface2":     "#F0F1F4",
    "border":       "#D8DAE5",
    "text":         "#2E2253",
    "text2":        "#5A5870",
    "text3":        "#9896A8",
    "red":          "#BA3718",
    "orange":       "#EE7412",
    "blue":         "#23609F",
    "lightblue":    "#4CB4E7",
    "path_hl":      "#08B0A0",
    "path_bg":      "#C8F0EC",
    "white":        "#FFFFFF",
}

INF_STR = "∞"


def _fmt(v: float) -> str:
    if v == float("inf"):  return INF_STR
    if v == float("-inf"): return f"-{INF_STR}"
    return str(int(round(v))) if abs(v - round(v)) < 1e-9 else f"{v:.1f}"


def _alpha(i: int) -> str:
    s, n = "", i
    while True:
        n, r = divmod(n, 26)
        s = chr(65 + r) + s
        if n == 0: break
        n -= 1
    return s


def _make_labels(n: int, mode: str, prefix: str = "X") -> List[str]:
    """mode: 'num'=1,2,3  'alpha'=A,B,C  'prefix'=X1,X2,..."""
    if mode == "alpha":
        return [_alpha(i) for i in range(n)]
    elif mode == "prefix":
        return [f"{prefix}{i+1}" for i in range(n)]
    else:
        return [str(i+1) for i in range(n)]


# ═══════════════════════════════════════════════════════════════
#  Bouton stylé — Simple & moderne
# ═══════════════════════════════════════════════════════════════
class ModernBtn(tk.Button):
    """Bouton simple avec border-radius, effet hover fluide."""
    STYLES = {
        "primary": (C["violet"],  C["violet_l"],  C["white"]),
        "cyan":    (C["cyan"],    C["cyan_l"],     C["white"]),
        "ghost":   (C["surface"], C["surface2"],   C["violet"]),
        "danger":  (C["red"],     "#9A2D14",       C["white"]),
        "warn":    (C["orange"],  "#D0650F",       C["white"]),
    }
    
    def __init__(self, parent, text, cmd=None, style="primary", width=None, **kw):
        bg, hov, fg = self.STYLES.get(style, self.STYLES["primary"])
        cfg = dict(
            font=("Segoe UI", 9),
            fg=fg,
            bg=bg,
            activebackground=hov,
            activeforeground=fg,
            relief="flat",
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            highlightthickness=0,
            overrelief="flat"
        )
        if width:
            cfg["width"] = width
        super().__init__(parent, text=text, command=cmd, **cfg, **kw)
        self._bg, self._hov, self._fg = bg, hov, fg
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, _):
        self.config(bg=self._hov)

    def _on_leave(self, _):
        self.config(bg=self._bg)

    def flash(self):
        orig = self._bg
        self.config(bg=C["cyan"])
        self.after(150, lambda: self.config(bg=orig))


# ═══════════════════════════════════════════════════════════════
#  Éditeur de matrice
# ═══════════════════════════════════════════════════════════════
class MatrixEditor(tk.Frame):
    def __init__(self, parent, n=4, labels=None):
        super().__init__(parent, bg=C["surface"])
        self.n = n
        self.labels: List[str] = labels or _make_labels(n, "num")
        self.entries: List[List[tk.Entry]] = []
        self._on_change_cb = None
        self._build()

    def set_change_callback(self, cb):
        self._on_change_cb = cb

    def _snap(self):
        return [[c.get() for c in row] for row in self.entries] if self.entries else []

    def _build(self):
        prev = self._snap()
        for w in self.winfo_children():
            w.destroy()
        self.entries = []
        n = self.n
        ef = ("Consolas", 9)
        ew = 6

        tk.Label(self, text="", bg=C["surface2"], width=4, relief="flat").grid(
            row=0, column=0, padx=1, pady=1)

        for j in range(n):
            h = self.labels[j] if j < len(self.labels) else str(j+1)
            tk.Label(self, text=h, bg=C["violet"], fg=C["white"],
                     font=("Segoe UI", 9, "bold"), width=ew,
                     relief="flat", padx=2, pady=4).grid(
                row=0, column=j+1, padx=1, pady=1, sticky="nsew")

        for i in range(n):
            h = self.labels[i] if i < len(self.labels) else str(i+1)
            tk.Label(self, text=h, bg=C["violet"], fg=C["white"],
                     font=("Segoe UI", 9, "bold"), width=4,
                     relief="flat", padx=2, pady=4).grid(
                row=i+1, column=0, padx=1, pady=1, sticky="nsew")

            row_e: List[tk.Entry] = []
            for j in range(n):
                diag = (i == j)
                var = tk.StringVar()
                e = tk.Entry(self, textvariable=var, width=ew, justify="center",
                             relief="flat", font=ef,
                             bg=C["surface2"] if diag else C["surface"],
                             fg=C["text3"] if diag else C["text"],
                             disabledbackground=C["surface2"],
                             highlightthickness=1,
                             highlightbackground=C["border"],
                             highlightcolor=C["cyan"],
                             state="disabled" if diag else "normal")
                e.grid(row=i+1, column=j+1, padx=1, pady=1, ipady=4)
                if not diag:
                    p = prev[i][j] if i < len(prev) and j < len(prev[i]) else ""
                    if p:
                        e.insert(0, p)
                    if self._on_change_cb:
                        var.trace_add("write", lambda *_, ii=i, jj=j: self._cell_changed(ii, jj))
                row_e.append(e)
            self.entries.append(row_e)

    def _cell_changed(self, i, j):
        if self._on_change_cb:
            self.after(300, self._on_change_cb)

    def rebuild(self, n, labels):
        self.n = n
        self.labels = labels[:]
        self._build()

    def set_labels(self, labels):
        self.labels = labels[:]
        self._build()

    def get_matrix(self) -> List[List[Optional[float]]]:
        out = []
        for i in range(self.n):
            row = []
            for j in range(self.n):
                if i == j:
                    row.append(None)
                    continue
                raw = self.entries[i][j].get().strip()
                if raw == "":
                    row.append(None)
                    continue
                try:
                    v = int(raw)
                    row.append(float(v))
                except ValueError:
                    raise ValueError(f"Cellule ({self.labels[i]}→{self.labels[j]}): entier requis, reçu '{raw}'")
            out.append(row)
        return out

    def set_from_matrix(self, m: List[List[Optional[float]]]):
        if not m:
            return
        for i in range(min(self.n, len(m))):
            for j in range(min(self.n, len(m[i]))):
                if i == j:
                    continue
                v = m[i][j]
                self.entries[i][j].delete(0, tk.END)
                if v is not None:
                    self.entries[i][j].insert(0, _fmt(v))

    def set_edge(self, i, j, value: Optional[float]):
        if 0 <= i < self.n and 0 <= j < self.n and i != j:
            self.entries[i][j].delete(0, tk.END)
            if value is not None:
                self.entries[i][j].insert(0, _fmt(value))


# ═══════════════════════════════════════════════════════════════
#  Canvas interactif du graphe
# ═══════════════════════════════════════════════════════════════
class GraphCanvas(tk.Canvas):
    NODE_R = 22

    def __init__(self, parent, on_node_click=None):
        super().__init__(parent, bg=C["bg"], highlightthickness=0, cursor="arrow")
        self.n = 0
        self.labels: List[str] = []
        self.matrix: List[List[Optional[float]]] = []
        self.positions: List[Tuple[float, float]] = []
        self.path: Optional[List[int]] = None
        self._drag_idx: Optional[int] = None
        self._zoom = 1.0
        self._pending = False
        self._on_node_click = on_node_click

        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._end_drag)
        self.bind("<MouseWheel>", lambda e: self.yview_scroll(-1 if e.delta > 0 else 1, "units"))

    def draw(self, matrix, labels, path=None, preserve=True):
        self.matrix = [row[:] for row in matrix]
        self.labels = labels[:]
        self.n = len(matrix)
        self.path = path
        if not preserve or len(self.positions) != self.n:
            self._place_nodes()
        if not self._pending:
            self._pending = True
            self.after(20, self._render)

    def _place_nodes(self):
        self.update_idletasks()
        w = max(self.winfo_width(), 500)
        h = max(self.winfo_height(), 380)
        cx, cy = w / 2, h / 2
        n = self.n
        if n == 0:
            self.positions = []
            return
        if n == 1:
            self.positions = [(cx, cy)]
            return
        rx = min(w * 0.36, max(160, n * 32))
        ry = min(h * 0.33, max(120, n * 22))
        self.positions = [
            (cx + rx * math.cos(2*math.pi*i/n - math.pi/2),
             cy + ry * math.sin(2*math.pi*i/n - math.pi/2))
            for i in range(n)
        ]

    def _render(self):
        self._pending = False
        self.delete("all")
        n = self.n
        if n == 0:
            return

        self.update_idletasks()
        vw = max(self.winfo_width(), 500)
        vh = max(self.winfo_height(), 380)
        # Garder l'espace canevas en accord avec le contenu
        self.configure(scrollregion=self.bbox("all") or (0, 0, vw, vh))

        r = self.NODE_R
        path_set = set()
        if self.path and len(self.path) >= 2:
            for i in range(len(self.path)-1):
                path_set.add((self.path[i], self.path[i+1]))

        pos = self.positions

        # ── Arcs ─────────────────────────────────────────
        for i in range(n):
            for j in range(n):
                w = self.matrix[i][j]
                if w is None or i == j:
                    continue
                ip = (i, j) in path_set
                x1, y1 = pos[i]
                x2, y2 = pos[j]

                opp = self.matrix[j][i] if j < len(self.matrix) else None
                curved = (opp is not None)
                self._draw_arc(x1, y1, x2, y2, r, ip, curved)

                mx = (x1+x2)/2 + (y1-y2)*0.12 * (1 if curved else 0.5)
                my = (y1+y2)/2 + (x2-x1)*0.12 * (1 if curved else 0.5)
                fc = C["cyan"] if ip else C["text2"]
                fw = "bold" if ip else "normal"
                self.create_text(mx, my, text=_fmt(w), fill=fc,
                                 font=("Segoe UI", 8, fw))

        # ── Nœuds ────────────────────────────────────────
        for i, (x, y) in enumerate(pos):
            in_path = self.path and i in self.path
            fill = C["cyan"] if in_path else C["violet"]
            out = C["cyan_l"] if in_path else C["violet_l"]
            self.create_oval(x-r+2, y-r+2, x+r+2, y+r+2,
                             fill="#E8E8E8", outline="")
            self.create_oval(x-r, y-r, x+r, y+r,
                             fill=fill, outline=out, width=2,
                             tags=("node", f"n{i}"))
            lbl = self.labels[i] if i < len(self.labels) else str(i+1)
            self.create_text(x, y, text=lbl, fill=C["white"],
                             font=("Segoe UI", 9, "bold"),
                             tags=("node", f"n{i}"))
            if self.path and i in self.path:
                order = self.path.index(i)+1
                self.create_text(x+r-2, y-r+4, text=str(order),
                                 fill=C["orange"], font=("Segoe UI", 7, "bold"))

        self.tag_bind("node", "<ButtonPress-1>", self._start_drag)
        self.tag_bind("node", "<Double-Button-1>", self._node_dblclick)

    def _draw_arc(self, x1, y1, x2, y2, r, is_path, curved):
        dx, dy = x2-x1, y2-y1
        d = math.hypot(dx, dy)
        if d < 1e-6:
            return
        ux, uy = dx/d, dy/d
        sx, sy = x1 + ux*r, y1 + uy*r
        ex, ey = x2 - ux*r, y2 - uy*r

        color = C["cyan"] if is_path else C["border"]
        lw = 2.5 if is_path else 1.5

        if curved:
            px = (sx+ex)/2 - uy * 28
            py = (sy+ey)/2 + ux * 28
            self.create_line(sx, sy, px, py, ex, ey,
                             fill=color, width=lw, smooth=True,
                             arrow=tk.LAST, arrowshape=(9, 11, 3))
        else:
            self.create_line(sx, sy, ex, ey,
                             fill=color, width=lw,
                             arrow=tk.LAST, arrowshape=(9, 11, 3))

    def _start_drag(self, event):
        item = self.find_withtag("current")
        if not item:
            return
        for t in self.gettags(item[0]):
            if t.startswith("n") and t[1:].isdigit():
                self._drag_idx = int(t[1:])
                self.configure(cursor="fleur")
                return

    def _on_drag(self, event):
        if self._drag_idx is None:
            return
        x, y = self.canvasx(event.x), self.canvasy(event.y)
        if 0 <= self._drag_idx < len(self.positions):
            self.positions[self._drag_idx] = (x, y)
            if not self._pending:
                self._pending = True
                self.after(16, self._render)

    def _end_drag(self, _):
        self._drag_idx = None
        self.configure(cursor="arrow")

    def _node_dblclick(self, event):
        item = self.find_withtag("current")
        if not item:
            return
        for t in self.gettags(item[0]):
            if t.startswith("n") and t[1:].isdigit():
                idx = int(t[1:])
                if self._on_node_click:
                    self._on_node_click(idx)
                return

    def set_zoom(self, z):
        self._zoom = max(0.5, min(2.5, z))
        if self.matrix:
            self.draw(self.matrix, self.labels, self.path, preserve=True)


# ═══════════════════════════════════════════════════════════════
#  Popup utilitaire
# ═══════════════════════════════════════════════════════════════
def popup_base(master, title, w=380, h=None):
    """Crée une popup centrée sur la fenêtre parent."""
    p = tk.Toplevel(master)
    p.title(title)
    p.transient(master)
    p.grab_set()
    p.configure(bg=C["surface"])
    p.resizable(False, False)
    
    if h is None:
        h = 300
    p.geometry(f"{w}x{h}")
    
    p.update_idletasks()
    mx = master.winfo_x() + (master.winfo_width() - w) // 2
    my = master.winfo_y() + (master.winfo_height() - h) // 2
    p.geometry(f"+{max(0, mx)}+{max(0, my)}")
    
    return p


def make_field(parent, label, row, var=None, values=None, placeholder=""):
    """Crée un label + widget d'entrée avec style moderne."""
    tk.Label(parent, text=label, bg=C["surface"], fg=C["violet"],
             font=("Segoe UI", 10, "bold")).grid(row=row, column=0, sticky="w",
                                        padx=(0, 14), pady=(10, 6))
    if var is None:
        var = tk.StringVar(value=placeholder)
    if values:
        w = ttk.Combobox(parent, textvariable=var, state="readonly",
                         values=values, width=22)
    else:
        w = tk.Entry(parent, textvariable=var, width=26,
                     font=("Segoe UI", 10), relief="flat",
                     bg=C["surface2"], fg=C["text"],
                     insertbackground=C["cyan"],
                     insertwidth=2,
                     highlightthickness=2,
                     highlightbackground=C["border"],
                     highlightcolor=C["cyan"])
        
        # Focus effects
        def on_focus_in(event, w=w):
            w.config(bg=C["cyan_bg"], highlightbackground=C["cyan"], 
                    highlightcolor=C["cyan"], highlightthickness=2)
        
        def on_focus_out(event, w=w):
            w.config(bg=C["surface2"], highlightbackground=C["border"],
                    highlightcolor=C["cyan"], highlightthickness=2)
        
        w.bind("<FocusIn>", on_focus_in)
        w.bind("<FocusOut>", on_focus_out)
    
    w.grid(row=row, column=1, sticky="ew", pady=(10, 6), padx=(0, 0))
    return var, w


# ═══════════════════════════════════════════════════════════════
#  Application principale
# ═══════════════════════════════════════════════════════════════
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Demoucron — Algorithme Min / Max")
        self.geometry("1500x940")
        self.minsize(1100, 700)
        
        # Icône
        try:
            from PIL import Image, ImageTk
            img = Image.open("algorithme.png")
            img = img.resize((32, 32), Image.Resampling.LANCZOS)
            self.ico = ImageTk.PhotoImage(img)
            self.wm_iconphoto(False, self.ico)
        except Exception:
            pass
        
        self.tk_setPalette(
            background=C["bg"],
            foreground=C["text"],
            activeBackground=C["violet_l"],
            activeForeground=C["white"]
        )
        self.configure(bg=C["bg"])

        self.n = 0
        self.labels: List[str] = []
        self.lbl2i: dict = {}
        self.matrix: List[List[Optional[float]]] = []
        self.last_result: Optional[DemoucronResult] = None
        self.last_mode: Optional[str] = None
        self.src_idx = 0
        self.dst_idx = 0
        self._auto_id = None
        self.auto_on = tk.BooleanVar(value=True)
        self._last_matrix_hash = None  # Cache pour éviter les redessins inutiles

        self._build_ui()
        self.after(200, self._popup_initial_setup)

    # ══════════════════════════════════════════════════════════
    #  UI
    # ══════════════════════════════════════════════════════════
    def _build_ui(self):
        self._build_header()

        # Main body avec scroll global
        body_container = tk.Frame(self, bg=C["bg"])
        body_container.pack(fill="both", expand=True)
        
        # Canvas pour scroller le contenu
        main_canvas = tk.Canvas(body_container, bg=C["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(body_container, orient="vertical", command=main_canvas.yview)
        scrollable_frame = tk.Frame(main_canvas, bg=C["bg"])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Mousewheel scroll
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        body_container.grid_rowconfigure(0, weight=1)
        body_container.grid_columnconfigure(0, weight=1)

        # Top: Matrice + Graphe côte à côte
        top = tk.Frame(scrollable_frame, bg=C["bg"])
        top.pack(fill="both", expand=True, padx=8, pady=8)
        top.grid_rowconfigure(0, weight=1)
        top.grid_columnconfigure(0, weight=1)
        top.grid_columnconfigure(1, weight=2)

        # LEFT: Matrice
        left_frame = tk.Frame(top, bg=C["bg"])
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        self._build_matrix_panel(left_frame)

        # RIGHT: Graphe
        right_frame = tk.Frame(top, bg=C["bg"])
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        self._build_graph_panel(right_frame)

        # BOTTOM: Résultats
        self._build_result_panel(scrollable_frame)
        self._build_statusbar()

    def _build_header(self):
        hdr = tk.Frame(self, bg=C["violet"])
        hdr.pack(fill="x")
        inner = tk.Frame(hdr, bg=C["violet"])
        inner.pack(fill="x", padx=16, pady=10)

        # Icône PNG si disponible
        tf = tk.Frame(inner, bg=C["violet"])
        tf.pack(side="left")
        try:
            from PIL import Image, ImageTk
            img = Image.open("algorithme.png")
            img = img.resize((40, 40), Image.Resampling.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(img)
            tk.Label(tf, image=self.logo_img, bg=C["violet"]).pack(side="left", padx=8)
        except Exception:
            pass
        
        tk.Label(tf, text="Demoucron", bg=C["violet"], fg=C["white"],
                 font=("Segoe UI", 24, "bold")).pack(side="left")

        bf = tk.Frame(inner, bg=C["violet"])
        bf.pack(side="left", padx=30)

        self._hbtns = []
        for txt, cmd, style in [
            ("⊞  Nouveau graphe", self._new_graph, "cyan"),
            ("⟳  Synchroniser", self._graph_to_matrix, "ghost"),
            ("▼  MIN", self._do_min, "warn"),
            ("▲  MAX", self._do_max, "ghost"),
            ("↺  Réinitialiser", self._reset, "danger"),
        ]:
            b = ModernBtn(bf, txt, cmd, style)
            b.pack(side="left", padx=4)
            self._hbtns.append(b)

        rf = tk.Frame(inner, bg=C["violet"])
        rf.pack(side="right")
        self.ind = tk.Label(rf, text="●", bg=C["violet"],
                            fg=C["cyan"], font=("Segoe UI", 12))
        self.ind.pack(side="right", padx=4)
        cb = tk.Checkbutton(rf, text="Auto-refresh",
                            variable=self.auto_on,
                            bg=C["violet"], fg=C["white"],
                            selectcolor=C["violet_l"],
                            activebackground=C["violet"],
                            activeforeground=C["white"],
                            font=("Segoe UI", 9), cursor="hand2",
                            command=self._toggle_auto)
        cb.pack(side="right")

    def _build_matrix_panel(self, p):
        p.columnconfigure(0, weight=1)
        p.rowconfigure(1, weight=1)
        
        tk.Label(p, text="Matrice d'adjacence",
                 bg=C["bg"], fg=C["violet"],
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 4))
        tk.Label(p, text="Cellule vide = pas d'arc  ·  entier signé",
                 bg=C["bg"], fg=C["text3"],
                 font=("Segoe UI", 8)).pack(anchor="w", pady=(0, 6))

        card = tk.Frame(p, bg=C["surface"],
                        highlightbackground=C["border"], highlightthickness=1,
                        height=350)
        card.pack(fill="both", expand=True)

        self.tcvs = tk.Canvas(card, bg=C["surface"], highlightthickness=0)
        tsy = tk.Scrollbar(card, orient="vertical", command=self.tcvs.yview)
        tsx = tk.Scrollbar(card, orient="horizontal", command=self.tcvs.xview)
        self.tcvs.configure(yscrollcommand=tsy.set, xscrollcommand=tsx.set)
        self.tcvs.grid(row=0, column=0, sticky="nsew")
        tsy.grid(row=0, column=1, sticky="ns")
        tsx.grid(row=1, column=0, sticky="ew")
        card.grid_rowconfigure(0, weight=1)
        card.grid_columnconfigure(0, weight=1)

        self.tholder = tk.Frame(self.tcvs, bg=C["surface"])
        self.tcvs.create_window((0, 0), window=self.tholder, anchor="nw")
        self.me = MatrixEditor(self.tholder, 4, ["A", "B", "C", "D"])
        self.me.pack(padx=8, pady=8)
        self.me.set_change_callback(self._on_matrix_edit)
        self.tholder.bind("<Configure>", lambda e: self.tcvs.configure(
            scrollregion=self.tcvs.bbox("all")))

        bf = tk.Frame(p, bg=C["bg"])
        bf.pack(fill="x", pady=(6, 0))
        ModernBtn(bf, "Matrice → Graphe", self._matrix_to_graph, "primary").pack(side="left", padx=2)
        ModernBtn(bf, "+ Arc", self._add_edge, "cyan").pack(side="left", padx=2)
        ModernBtn(bf, "− Arc", self._del_edge, "ghost").pack(side="left", padx=2)

    def _build_graph_panel(self, p):
        p.columnconfigure(0, weight=1)
        p.rowconfigure(1, weight=1)
        
        tk.Label(p, text="Graphe orienté",
                 bg=C["bg"], fg=C["violet"],
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 4))
        tk.Label(p, text="Drag = déplacer  ·  Double-clic = modifier sommet",
                 bg=C["bg"], fg=C["text3"],
                 font=("Segoe UI", 8)).pack(anchor="w", pady=(0, 6))

        gcard = tk.Frame(p, bg=C["surface"],
                         highlightbackground=C["border"], highlightthickness=1,
                         height=350)
        gcard.pack(fill="both", expand=True)

        self.gc = GraphCanvas(gcard, on_node_click=self._graph_node_dblclick)
        gsy = tk.Scrollbar(gcard, orient="vertical", command=self.gc.yview)
        gsx = tk.Scrollbar(gcard, orient="horizontal", command=self.gc.xview)
        self.gc.configure(yscrollcommand=gsy.set, xscrollcommand=gsx.set)
        self.gc.grid(row=0, column=0, sticky="nsew")
        gsy.grid(row=0, column=1, sticky="ns")
        gsx.grid(row=1, column=0, sticky="ew")
        gcard.grid_rowconfigure(0, weight=1)
        gcard.grid_columnconfigure(0, weight=1)

        bf = tk.Frame(p, bg=C["bg"])
        bf.pack(fill="x", pady=(6, 0))
        ModernBtn(bf, "+ Sommet", self._add_vertex, "primary").pack(side="left", padx=2)
        ModernBtn(bf, "− Sommet", self._del_vertex, "ghost").pack(side="left", padx=2)
        ModernBtn(bf, "✎ Modifier sommet", self._edit_vertex, "ghost").pack(side="left", padx=2)
        tk.Frame(bf, bg=C["border"], width=1, height=20).pack(side="left", padx=8)
        ModernBtn(bf, "+ Arc", self._add_edge, "cyan").pack(side="left", padx=2)
        ModernBtn(bf, "✎ Modifier arc", self._edit_edge, "ghost").pack(side="left", padx=2)
        ModernBtn(bf, "− Arc", self._del_edge, "ghost").pack(side="left", padx=2)

        zf = tk.Frame(p, bg=C["bg"])
        zf.pack(fill="x", pady=(4, 0))
        tk.Label(zf, text="Zoom :", bg=C["bg"], fg=C["text3"],
                 font=("Segoe UI", 8)).pack(side="left", padx=(0, 4))
        ModernBtn(zf, "+", lambda: self.gc.set_zoom(self.gc._zoom + 0.1), "ghost").pack(side="left", padx=2)
        ModernBtn(zf, "−", lambda: self.gc.set_zoom(self.gc._zoom - 0.1), "ghost").pack(side="left", padx=2)
        ModernBtn(zf, "100%", lambda: self.gc.set_zoom(1.0), "ghost").pack(side="left", padx=2)

    def _build_result_panel(self, parent):
        rs = tk.Frame(parent, bg=C["bg"])
        rs.pack(fill="both", expand=True, padx=10, pady=(8, 0))

        rp = tk.Frame(rs, bg=C["surface"],
                      highlightbackground=C["border"], highlightthickness=1)
        rp.pack(side="left", fill="both", expand=True, padx=(0, 5))

        tk.Frame(rp, bg=C["cyan"], height=3).pack(fill="x")
        rph = tk.Frame(rp, bg=C["surface"])
        rph.pack(fill="x", padx=12, pady=(8, 4))
        tk.Label(rph, text="Résultat & Chemin optimal",
                 bg=C["surface"], fg=C["violet"],
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")

        rf = tk.Frame(rp, bg=C["surface"])
        rf.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        self.res_lbl = tk.Label(rf, text="Aucun calcul lancé.",
                                bg=C["surface"], fg=C["text3"],
                                font=("Segoe UI", 10), justify="left",
                                wraplength=370)
        self.res_lbl.pack(anchor="w")
        self.path_frame = tk.Frame(rf, bg=C["surface"])
        self.path_frame.pack(fill="x", pady=(6, 0))

        sdf = tk.Frame(rp, bg=C["surface2"])
        sdf.pack(fill="x", padx=12, pady=(0, 8))
        tk.Label(sdf, text="Source :", bg=C["surface2"], fg=C["text2"],
                 font=("Segoe UI", 9)).grid(row=0, column=0, padx=4, pady=4)
        self.src_var = tk.StringVar(value="")
        self.src_cb = ttk.Combobox(sdf, textvariable=self.src_var,
                                   width=8, state="readonly")
        self.src_cb.grid(row=0, column=1, padx=4, pady=4)
        tk.Label(sdf, text="→  Dest :", bg=C["surface2"], fg=C["text2"],
                 font=("Segoe UI", 9)).grid(row=0, column=2, padx=4, pady=4)
        self.dst_var = tk.StringVar(value="")
        self.dst_cb = ttk.Combobox(sdf, textvariable=self.dst_var,
                                   width=8, state="readonly")
        self.dst_cb.grid(row=0, column=3, padx=4, pady=4)
        self.src_cb.bind("<<ComboboxSelected>>", lambda e: self._repath())
        self.dst_cb.bind("<<ComboboxSelected>>", lambda e: self._repath())

        sp = tk.Frame(rs, bg=C["surface"],
                      highlightbackground=C["border"], highlightthickness=1)
        sp.pack(side="left", fill="both", expand=True, padx=(5, 0))

        tk.Frame(sp, bg=C["cyan"], height=3).pack(fill="x")
        header_frame = tk.Frame(sp, bg=C["surface"])
        header_frame.pack(fill="x", padx=12, pady=(8, 4))
        tk.Label(header_frame, text="Matrices Dk  ( ∞ = pas de chemin  ·  / = diagonale )",
                 bg=C["surface"], fg=C["violet"],
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", side="left", fill="x", expand=True)

        # Créer le Canvas scrollable pour le contenu des matrices
        steps_container = tk.Frame(sp, bg=C["surface"], highlightthickness=0)
        steps_container.pack(fill="both", expand=True, padx=0, pady=0)

        self.steps_canvas = tk.Canvas(steps_container, bg=C["bg"], 
                                      highlightthickness=0, relief="flat")
        steps_scrollbar = tk.Scrollbar(steps_container, orient="vertical", 
                                      command=self.steps_canvas.yview)
        self.steps_scrollable_frame = tk.Frame(self.steps_canvas, bg=C["bg"])
        
        self.steps_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.steps_canvas.configure(scrollregion=self.steps_canvas.bbox("all"))
        )
        
        self.steps_canvas.create_window((0, 0), window=self.steps_scrollable_frame, anchor="nw")
        self.steps_canvas.configure(yscrollcommand=steps_scrollbar.set)
        self.steps_canvas.grid(row=0, column=0, sticky="nsew")
        steps_scrollbar.grid(row=0, column=1, sticky="ns")
        
        steps_container.grid_rowconfigure(0, weight=1)
        steps_container.grid_columnconfigure(0, weight=1)
        
        # Créer un Text widget SANS ScrolledText (pas de double scrollbar)
        self.steps_txt = tk.Text(self.steps_scrollable_frame, wrap="none", 
                                      height=11,
                                      font=("Consolas", 9), relief="flat",
                                      bg=C["bg"], fg=C["text"],
                                      insertbackground=C["cyan"])
        self.steps_txt.pack(fill="both", expand=True, padx=8, pady=8)
        self.steps_txt.configure(state="disabled")

    def _build_statusbar(self):
        sb = tk.Frame(self, bg=C["violet_l"])
        sb.pack(side="bottom", fill="x")
        i = tk.Frame(sb, bg=C["violet_l"])
        i.pack(fill="x", padx=12, pady=4)
        self.st_dot = tk.Label(i, text="●", bg=C["violet_l"],
                               fg=C["cyan"], font=("Segoe UI", 9))
        self.st_dot.pack(side="left")
        self.st_lbl = tk.Label(i, text="Prêt", bg=C["violet_l"],
                               fg=C["white"], font=("Segoe UI", 8))
        self.st_lbl.pack(side="left", padx=6)
        tk.Label(i, text="Charte graphique Data Terra 2020 — Demoucron Min/Max",
                 bg=C["violet_l"], fg=C["cyan"],
                 font=("Segoe UI", 8)).pack(side="right")

    # ══════════════════════════════════════════════════════════
    #  Popup initial
    # ══════════════════════════════════════════════════════════
    def _popup_initial_setup(self):
        """Popup au démarrage pour configurer le graphe."""
        p = popup_base(self, "Configuration initiale", w=480, h=420)

        # Top bar avec icône
        top = tk.Frame(p, bg=C["cyan"], height=60)
        top.pack(fill="x", side="top")
        top_inner = tk.Frame(top, bg=C["cyan"])
        top_inner.pack(fill="both", expand=True, padx=20, pady=12)
        
        try:
            from PIL import Image, ImageTk
            img = Image.open("algorithme.png")
            img = img.resize((48, 48), Image.Resampling.LANCZOS)
            self.popup_logo = ImageTk.PhotoImage(img)
            tk.Label(top_inner, image=self.popup_logo, bg=C["cyan"]).pack(side="left", padx=12)
        except Exception:
            pass
        
        txt_frame = tk.Frame(top_inner, bg=C["cyan"])
        txt_frame.pack(side="left", fill="both", expand=True)
        tk.Label(txt_frame, text="Configuration Demoucron",
                 bg=C["cyan"], fg=C["white"],
                 font=("Segoe UI", 14, "bold")).pack(anchor="w")
        tk.Label(txt_frame, text="Définissez les paramètres de votre graphe",
                 bg=C["cyan"], fg=C["cyan_l"],
                 font=("Segoe UI", 9)).pack(anchor="w")

        c = tk.Frame(p, bg=C["surface"], padx=20, pady=18)
        c.pack(fill="both", expand=True)

        tk.Label(c, text="Paramètres du graphe",
                 bg=C["surface"], fg=C["violet"],
                 font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))

        c.columnconfigure(1, weight=1)

        n_var, _ = make_field(c, "Nombre de sommets :", 2, placeholder="4")
        
        type_opts = ["Chiffres (1,2,3…)", "Lettres (A,B,C…)", "Préfixe personnalisé (X1,X2…)"]
        type_var, _ = make_field(c, "Type de labels :", 3, values=type_opts)
        type_var.set(type_opts[0])
        
        pfx_var, pfx_e = make_field(c, "Préfixe (si applicable) :", 4, placeholder="X")
        pfx_e.configure(state="disabled")

        def _on_type(*_):
            t = type_var.get()
            pfx_e.configure(state="normal" if "personnalisé" in t else "disabled")
        type_var.trace_add("write", _on_type)

        def submit():
            try:
                nv = int(n_var.get())
                if not (2 <= nv <= 20):
                    messagebox.showerror("Erreur", "Entre 2 et 20 sommets.", parent=p)
                    return
            except ValueError:
                messagebox.showerror("Erreur", "Nombre entier requis.", parent=p)
                return

            t = type_var.get()
            pfx = pfx_var.get().strip() or "X"
            
            if "Lettre" in t:
                mode = "alpha"
            elif "personnalisé" in t:
                mode = "prefix"
            else:
                mode = "num"

            self.n = nv
            self.labels = _make_labels(nv, mode, pfx)
            self.lbl2i = {l: i for i, l in enumerate(self.labels)}
            self.matrix = [[None]*nv for _ in range(nv)]
            self.src_idx = 0
            self.dst_idx = nv - 1
            self.last_result = None
            self.last_mode = None
            
            self.me.rebuild(nv, self.labels)
            self._sync_selectors()
            self.gc.positions = []
            self.gc.draw(self.matrix, self.labels, preserve=False)
            self._clear_res()
            self._set_steps("")
            self._status(f"Graphe créé : {nv} sommets")
            self._start_auto()
            
            p.destroy()

        # Footer avec boutons
        footer = tk.Frame(p, bg=C["border"], height=2)
        footer.pack(fill="x", side="bottom")
        
        btn_frame = tk.Frame(p, bg=C["surface2"])
        btn_frame.pack(fill="x", side="bottom", padx=16, pady=12)
        
        ModernBtn(btn_frame, "✓ Commencer", submit, "primary").pack(side="right", padx=4)
        ModernBtn(btn_frame, "✕ Annuler", lambda: p.destroy(), "ghost").pack(side="right", padx=4)

        p.wait_window()

    # ══════════════════════════════════════════════════════════
    #  Init & helpers
    # ══════════════════════════════════════════════════════════
    def _sync_selectors(self):
        self.lbl2i = {l: i for i, l in enumerate(self.labels)}
        vals = self.labels[:]
        self.src_cb["values"] = vals
        self.dst_cb["values"] = vals
        if self.src_var.get() not in vals:
            self.src_var.set(vals[0] if vals else "")
        if self.dst_var.get() not in vals:
            self.dst_var.set(vals[-1] if vals else "")

    def _status(self, msg, ok=True):
        self.st_dot.configure(fg=C["cyan"] if ok else C["orange"])
        self.st_lbl.configure(text=msg[:120])
        self.after(5000, lambda: self.st_lbl.configure(text="Prêt"))

    # ══════════════════════════════════════════════════════════
    #  Auto-refresh
    # ══════════════════════════════════════════════════════════
    def _start_auto(self):
        if self._auto_id:
            self.after_cancel(self._auto_id)
        self._auto_tick()

    def _auto_tick(self):
        if self.auto_on.get():
            self._do_auto()
        self._auto_id = self.after(1000, self._auto_tick)

    def _do_auto(self):
        try:
            m = self.me.get_matrix()
            # Calculer le hash pour détecter les changements
            m_hash = str(m)
            if m_hash == self._last_matrix_hash:
                # Rien n'a changé, pas besoin de redessiner
                return
            self._last_matrix_hash = m_hash
            
            self.matrix = m
            self.gc.draw(m, self.labels, self.gc.path, preserve=True)
            if self.last_mode:
                self._compute(self.last_mode, show=False)
            self._pulse()
        except Exception:
            pass

    def _pulse(self):
        self.ind.configure(fg=C["orange"])
        self.after(200, lambda: self.ind.configure(
            fg=C["cyan"] if self.auto_on.get() else C["text3"]))

    def _toggle_auto(self):
        self.ind.configure(fg=C["cyan"] if self.auto_on.get() else C["text3"])

    def _on_matrix_edit(self):
        self._last_matrix_hash = None  # Invalider le cache
        if self.auto_on.get():
            self._do_auto()

    # ══════════════════════════════════════════════════════════
    #  Actions boutons header
    # ══════════════════════════════════════════════════════════
    def _new_graph(self):
        """Popup de création : nb sommets + type de label."""
        self._popup_initial_setup()

    def _graph_to_matrix(self):
        """Redessine la matrice depuis le graphe courant."""
        self.me.set_from_matrix(self.matrix)
        self._status("Graphe → Matrice synchronisé.")

    def _matrix_to_graph(self):
        try:
            m = self.me.get_matrix()
            self.matrix = m
            self._last_matrix_hash = None  # Invalider le cache
            self.gc.draw(m, self.labels, preserve=True)
            self._status("Matrice → Graphe synchronisé.")
        except ValueError as ex:
            messagebox.showerror("Erreur matrice", str(ex))

    def _do_min(self):
        self._last_matrix_hash = None  # Invalider le cache après MIN
        self._compute("min", show=True)

    def _do_max(self):
        self._last_matrix_hash = None  # Invalider le cache après MAX
        self._compute("max", show=True)

    def _reset(self):
        if not messagebox.askyesno("Réinitialiser",
                                   "Effacer tout et repartir à zéro ?"):
            return
        self._popup_initial_setup()

    # ══════════════════════════════════════════════════════════
    #  Calcul
    # ══════════════════════════════════════════════════════════
    def _repath(self):
        if self.last_mode:
            self._compute(self.last_mode, show=False)

    def _compute(self, mode, show=True):
        try:
            m = self.me.get_matrix()
            self.matrix = m
            sl = self.src_var.get()
            dl = self.dst_var.get()
            if sl not in self.lbl2i or dl not in self.lbl2i:
                if show:
                    messagebox.showerror("Erreur", "Source/Destination invalide.")
                return
            s, d = self.lbl2i[sl], self.lbl2i[dl]

            result = (demoucron_min(m, detect_negative_cycles=True) if mode == "min"
                      else demoucron_max(m, detect_positive_cycles=True))
            path = build_path(result.next_node, s, d)
            value = result.values[s][d]

            self.last_result = result
            self.last_mode = mode

            self.gc.draw(m, self.labels, path, preserve=True)

            if mode == "min" and result.negative_cycle_detected:
                self._show_err("Cycle négatif — distances non définies")
            elif mode == "max" and result.positive_cycle_detected:
                self._show_err("Cycle positif — valeur arbitrairement grande")
            elif not path:
                self.res_lbl.configure(
                    text=f"Aucun chemin {mode.upper()} de {sl} vers {dl}.",
                    fg=C["text3"])
                for w in self.path_frame.winfo_children():
                    w.destroy()
            else:
                self._show_path(path, value, sl, dl, mode, m)

            self._set_steps(self._fmt_steps(result, mode.upper()))

        except Exception as ex:
            if show:
                messagebox.showerror(f"Erreur {mode.upper()}", str(ex))

    # ══════════════════════════════════════════════════════════
    #  Affichage résultat
    # ══════════════════════════════════════════════════════════
    def _clear_res(self):
        self.res_lbl.configure(text="Aucun calcul.", fg=C["text3"])
        for w in self.path_frame.winfo_children():
            w.destroy()

    def _show_err(self, msg):
        self.res_lbl.configure(text=f"⚠  {msg}", fg=C["red"])
        for w in self.path_frame.winfo_children():
            w.destroy()

    def _show_path(self, path, value, sl, dl, mode, m):
        icon = "▼" if mode == "min" else "▲"
        label = "MIN" if mode == "min" else "MAX"
        cost = "Coût minimal" if mode == "min" else "Valeur maximale"
        vs = _fmt(value)

        self.res_lbl.configure(
            text=f"{icon} {label}  {sl} → {dl}   |   {cost} : {vs}   "
                 f"({len(path)} sommets, {len(path)-1} arcs)",
            fg=C["violet"])

        for w in self.path_frame.winfo_children():
            w.destroy()

        bubble_row = tk.Frame(self.path_frame, bg=C["surface"])
        bubble_row.pack(fill="x", pady=(4, 0))

        for idx, ni in enumerate(path):
            lbl = self.labels[ni] if ni < len(self.labels) else str(ni+1)
            col = C["cyan"] if mode == "min" else C["violet"]
            tk.Label(bubble_row, text=f" {lbl} ", bg=col, fg=C["white"],
                     font=("Segoe UI", 10, "bold"),
                     relief="flat", padx=6, pady=4).pack(side="left", padx=1)
            if idx < len(path)-1:
                nxt = path[idx+1]
                w = m[ni][nxt]
                ws = _fmt(w) if w is not None else "?"
                tk.Label(bubble_row, text=f" —{ws}→ ", bg=C["surface"],
                         fg=C["text2"], font=("Consolas", 9)).pack(side="left")

        detail = tk.Frame(self.path_frame,
                          bg=C["cyan_bg"],
                          highlightbackground=C["cyan"],
                          highlightthickness=1)
        detail.pack(fill="x", pady=(8, 0))

        tk.Label(detail, text="Détail étape par étape",
                 bg=C["cyan_bg"], fg=C["violet"],
                 font=("Segoe UI", 9, "bold")).grid(
            row=0, column=0, columnspan=4, sticky="w", padx=10, pady=(8, 4))

        headers = ["Étape", "De", "Vers", "Poids"]
        for ci, h in enumerate(headers):
            tk.Label(detail, text=h, bg=C["cyan"],
                     fg=C["white"], font=("Segoe UI", 8, "bold"),
                     padx=8, pady=3).grid(row=1, column=ci, sticky="nsew",
                                          padx=1, pady=1)

        cumul = 0.0
        for step, (i, j) in enumerate(zip(path[:-1], path[1:])):
            la = self.labels[i] if i < len(self.labels) else str(i+1)
            lb = self.labels[j] if j < len(self.labels) else str(j+1)
            w = m[i][j]
            ws = _fmt(w) if w is not None else "?"
            if w is not None:
                cumul += w
            bg_row = C["surface"] if step % 2 == 0 else C["cyan_bg"]
            for ci, txt in enumerate([str(step+1), la, lb, ws]):
                tk.Label(detail, text=txt, bg=bg_row, fg=C["text"],
                         font=("Consolas", 9), padx=8, pady=3).grid(
                    row=step+2, column=ci, sticky="nsew", padx=1, pady=0)

        r_tot = len(path) + 1
        for ci, txt in enumerate(["Total", "", "", vs]):
            tk.Label(detail, text=txt, bg=C["violet"], fg=C["white"],
                     font=("Segoe UI", 9, "bold"), padx=8, pady=4).grid(
                row=r_tot, column=ci, sticky="nsew", padx=1, pady=(2, 8))

    def _fmt_steps(self, result: DemoucronResult, mode: str) -> str:
        lines = [f"Mode : {mode}  |  D0 = initiale  ·  Dk = après itération k\n"]
        if result.negative_cycle_detected:
            lines.append("⚠ Cycle négatif !\n")
        if result.positive_cycle_detected:
            lines.append("⚠ Cycle positif !\n")
        n = len(result.history[0]) if result.history else 0
        cw = max(6, max((len(l) for l in self.labels), default=2) + 2)

        for idx, mat in enumerate(result.history):
            lines.append(f"  ── D{idx} ──")
            hdr = "      " + "".join(
                (self.labels[j] if j < len(self.labels) else str(j+1)).center(cw)
                for j in range(n))
            lines.append(hdr)
            lines.append("      " + "─" * (cw * n))
            for i in range(n):
                rl = (self.labels[i] if i < len(self.labels) else str(i+1)).ljust(5)
                cells = []
                for j in range(n):
                    if i == j:
                        c = "/"
                    else:
                        v = mat[i][j]
                        c = INF_STR if v == float("inf") else (f"-{INF_STR}" if v == float("-inf") else _fmt(v))
                    cells.append(c.center(cw))
                lines.append(f"  {rl} │" + "│".join(cells))
            lines.append("")
        return "\n".join(lines)

    def _set_steps(self, text):
        self.steps_txt.configure(state="normal")
        self.steps_txt.delete("1.0", tk.END)
        if text:
            self.steps_txt.insert(tk.END, text)
        self.steps_txt.configure(state="disabled")

    # ══════════════════════════════════════════════════════════
    #  Édition graphe — sommets
    # ══════════════════════════════════════════════════════════
    def _add_vertex(self):
        if self.n >= 20:
            messagebox.showwarning("Limite", "Maximum 20 sommets.")
            return
        new_i = self.n
        if self.labels and self.labels[0][0].isalpha() and len(self.labels[0]) == 1:
            new_lbl = _alpha(new_i)
        elif self.labels and len(self.labels[0]) > 1:
            pfx = ''.join(c for c in self.labels[0] if c.isalpha())
            new_lbl = f"{pfx}{new_i+1}"
        else:
            new_lbl = str(new_i + 1)

        p = popup_base(self, "Ajouter un sommet", w=380, h=210)
        c = tk.Frame(p, bg=C["surface"], padx=20, pady=16)
        c.pack(fill="both", expand=True)
        tk.Frame(p, bg=C["cyan"], height=4).place(x=0, y=0, relwidth=1)
        tk.Label(c, text="Ajouter un sommet",
                 bg=C["surface"], fg=C["violet"],
                 font=("Segoe UI", 13, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(8, 14))
        c.columnconfigure(1, weight=1)
        lv, _ = make_field(c, "Nom du sommet :", 1, placeholder=new_lbl)

        def submit():
            lbl = lv.get().strip()
            if not lbl:
                messagebox.showerror("Erreur", "Nom vide.", parent=p)
                return
            if lbl in self.lbl2i:
                messagebox.showerror("Erreur", "Ce nom existe déjà.", parent=p)
                return
            for row in self.matrix:
                row.append(None)
            self.matrix.append([None] * (self.n + 1))
            self.labels.append(lbl)
            self.n += 1
            self.me.rebuild(self.n, self.labels)
            self._sync_selectors()
            # Mettre à jour la destination au nouveau sommet
            self.dst_var.set(lbl)
            self._last_matrix_hash = None  # Invalider le cache
            self.gc.draw(self.matrix, self.labels, preserve=True)
            self._status(f"Sommet {lbl} ajouté.")
            p.destroy()

        af = tk.Frame(c, bg=C["surface"])
        af.grid(row=3, column=0, columnspan=2, sticky="e", pady=(14, 0))
        ModernBtn(af, "Annuler", p.destroy, "ghost").pack(side="right", padx=(4, 0))
        ModernBtn(af, "✓ Ajouter", submit, "primary").pack(side="right")
        p.wait_window()

    def _del_vertex(self):
        p = popup_base(self, "Supprimer un sommet", w=380, h=230)
        c = tk.Frame(p, bg=C["surface"], padx=20, pady=16)
        c.pack(fill="both", expand=True)
        tk.Frame(p, bg=C["red"], height=4).place(x=0, y=0, relwidth=1)
        tk.Label(c, text="Supprimer un sommet",
                 bg=C["surface"], fg=C["red"],
                 font=("Segoe UI", 13, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(8, 14))
        c.columnconfigure(1, weight=1)
        lv, _ = make_field(c, "Sommet à supprimer :", 1, values=self.labels)
        lv.set(self.labels[-1] if self.labels else "")

        def submit():
            lbl = lv.get().strip()
            if lbl not in self.lbl2i:
                messagebox.showerror("Erreur", "Sommet inconnu.", parent=p)
                return
            if self.n <= 2:
                messagebox.showwarning("Impossible", "Minimum 2 sommets.", parent=p)
                return
            idx = self.lbl2i[lbl]
            self.matrix.pop(idx)
            for row in self.matrix:
                if len(row) > idx:
                    row.pop(idx)
            self.labels.pop(idx)
            self.n -= 1
            self.me.rebuild(self.n, self.labels)
            self._sync_selectors()
            self._last_matrix_hash = None  # Invalider le cache
            if idx < len(self.gc.positions):
                self.gc.positions.pop(idx)
            self.gc.draw(self.matrix, self.labels, preserve=True)
            self._status(f"Sommet {lbl} supprimé.")
            p.destroy()

        af = tk.Frame(c, bg=C["surface"])
        af.grid(row=3, column=0, columnspan=2, sticky="e", pady=(14, 0))
        ModernBtn(af, "Annuler", p.destroy, "ghost").pack(side="right", padx=(4, 0))
        ModernBtn(af, "✕ Supprimer", submit, "danger").pack(side="right")
        p.wait_window()

    def _edit_vertex(self, idx=None):
        p = popup_base(self, "Modifier un sommet", w=400, h=260)
        c = tk.Frame(p, bg=C["surface"], padx=20, pady=16)
        c.pack(fill="both", expand=True)
        tk.Frame(p, bg=C["cyan"], height=4).place(x=0, y=0, relwidth=1)
        tk.Label(c, text="Modifier un sommet",
                 bg=C["surface"], fg=C["violet"],
                 font=("Segoe UI", 13, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(8, 14))
        c.columnconfigure(1, weight=1)
        default = self.labels[idx] if idx is not None else self.labels[0]
        sv, _ = make_field(c, "Sommet :", 1, values=self.labels)
        sv.set(default)
        nv, _ = make_field(c, "Nouveau nom :", 2, placeholder=default)

        def submit():
            old = sv.get().strip()
            new = nv.get().strip()
            if old not in self.lbl2i:
                messagebox.showerror("Erreur", "Sommet inconnu.", parent=p)
                return
            if not new:
                messagebox.showerror("Erreur", "Nom vide.", parent=p)
                return
            if new != old and new in self.lbl2i:
                messagebox.showerror("Erreur", "Nom déjà utilisé.", parent=p)
                return
            oi = self.lbl2i[old]
            self.labels[oi] = new
            self.me.set_labels(self.labels)
            self._sync_selectors()
            self._last_matrix_hash = None  # Invalider le cache
            self.gc.draw(self.matrix, self.labels, preserve=True)
            self._status(f"Sommet {old} → {new}")
            p.destroy()

        af = tk.Frame(c, bg=C["surface"])
        af.grid(row=4, column=0, columnspan=2, sticky="e", pady=(14, 0))
        ModernBtn(af, "Annuler", p.destroy, "ghost").pack(side="right", padx=(4, 0))
        ModernBtn(af, "✓ Modifier", submit, "primary").pack(side="right")
        p.wait_window()

    def _graph_node_dblclick(self, idx):
        self._edit_vertex(idx)

    # ══════════════════════════════════════════════════════════
    #  Édition graphe — arcs
    # ══════════════════════════════════════════════════════════
    def _arc_popup(self, title, bar_color, confirm_text, confirm_style,
                   with_weight=True):
        """Popup générique pour créer/modifier/supprimer un arc."""
        p = popup_base(self, title, w=410, h=290 if with_weight else 250)
        c = tk.Frame(p, bg=C["surface"], padx=20, pady=16)
        c.pack(fill="both", expand=True)
        tk.Frame(p, bg=bar_color, height=4).place(x=0, y=0, relwidth=1)
        tk.Label(c, text=title, bg=C["surface"], fg=C["violet"],
                 font=("Segoe UI", 13, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(8, 14))
        c.columnconfigure(1, weight=1)
        sv, _ = make_field(c, "De :", 1, values=self.labels)
        sv.set(self.src_var.get() if self.src_var.get() in self.labels else self.labels[0])
        dv, _ = make_field(c, "Vers :", 2, values=self.labels)
        dv.set(self.dst_var.get() if self.dst_var.get() in self.labels else self.labels[-1])
        wv = None
        info_lbl = tk.Label(c, text="", bg=C["surface"], fg=C["text3"],
                            font=("Segoe UI", 8))
        info_lbl.grid(row=3, column=0, columnspan=2, sticky="w", pady=(2, 0))

        if with_weight:
            wv, _ = make_field(c, "Poids (entier) :", 4)
            def prefill(*_):
                s = sv.get()
                d = dv.get()
                if s == d:
                    info_lbl.configure(text="⚠ Boucle non autorisée")
                    if wv:
                        wv.set("")
                    return
                info_lbl.configure(text="")
                if s in self.lbl2i and d in self.lbl2i:
                    si, di = self.lbl2i[s], self.lbl2i[d]
                    v = self.matrix[si][di]
                    if wv:
                        wv.set(_fmt(v) if v is not None else "")
            sv.trace_add("write", prefill)
            dv.trace_add("write", prefill)
            prefill()
        else:
            def prefill(*_):
                s = sv.get()
                d = dv.get()
                if s == d:
                    info_lbl.configure(text="⚠ Boucle non autorisée")
                else:
                    info_lbl.configure(text="")
            sv.trace_add("write", prefill)
            dv.trace_add("write", prefill)

        result = {"v": None}
        def submit():
            s = sv.get().strip()
            d = dv.get().strip()
            if s == d:
                messagebox.showerror("Erreur", "Boucle i→i non autorisée.", parent=p)
                return
            if s not in self.lbl2i or d not in self.lbl2i:
                messagebox.showerror("Erreur", "Sommet invalide.", parent=p)
                return
            if with_weight:
                raw = wv.get().strip() if wv else ""
                if raw == "":
                    result["v"] = (s, d, None)
                else:
                    try:
                        result["v"] = (s, d, int(raw))
                    except ValueError:
                        messagebox.showerror("Erreur", "Entier requis.", parent=p)
                        return
            else:
                result["v"] = (s, d)
            p.destroy()

        af = tk.Frame(c, bg=C["surface"])
        row_af = 6 if with_weight else 4
        af.grid(row=row_af, column=0, columnspan=2, sticky="e", pady=(14, 0))
        ModernBtn(af, "Annuler", p.destroy, "ghost").pack(side="right", padx=(4, 0))
        ModernBtn(af, confirm_text, submit, confirm_style).pack(side="right")
        p.wait_window()
        return result["v"]

    def _add_edge(self):
        res = self._arc_popup("Ajouter un arc", C["cyan"], "✓ Ajouter", "cyan")
        if res is None:
            return
        sl, dl, w = res
        si, di = self.lbl2i[sl], self.lbl2i[dl]
        self.matrix[si][di] = float(w) if w is not None else None
        self.me.set_edge(si, di, self.matrix[si][di])
        self._last_matrix_hash = None  # Invalider le cache
        self.gc.draw(self.matrix, self.labels, self.gc.path, preserve=True)
        self._status(f"Arc {sl}→{dl} = {w}")

    def _edit_edge(self):
        res = self._arc_popup("Modifier un arc", C["violet"], "✓ Modifier", "primary")
        if res is None:
            return
        sl, dl, w = res
        si, di = self.lbl2i[sl], self.lbl2i[dl]
        self.matrix[si][di] = float(w) if w is not None else None
        self.me.set_edge(si, di, self.matrix[si][di])
        self._last_matrix_hash = None  # Invalider le cache
        self.gc.draw(self.matrix, self.labels, self.gc.path, preserve=True)
        self._status(f"Arc {sl}→{dl} modifié.")

    def _del_edge(self):
        res = self._arc_popup("Supprimer un arc", C["red"], "✕ Supprimer", "danger",
                              with_weight=False)
        if res is None:
            return
        sl, dl = res
        si, di = self.lbl2i[sl], self.lbl2i[dl]
        self.matrix[si][di] = None
        self.me.set_edge(si, di, None)
        self._last_matrix_hash = None  # Invalider le cache
        self.gc.draw(self.matrix, self.labels, self.gc.path, preserve=True)
        self._status(f"Arc {sl}→{dl} supprimé.")


# ═══════════════════════════════════════════════════════════════
def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
