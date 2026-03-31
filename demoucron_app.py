from __future__ import annotations

import math
import os
import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from typing import List, Optional, Tuple

from demoucron import DemoucronResult, build_path, demoucron_max, demoucron_min


PALETTE = {
    "primary": "#00C21C",
    "primary_dark": "#098E00",
    "path": "#0B5FFF",
    "path_node": "#0B5FFF",
    "bg": "#FFFFFF",
    "text": "#333333",
    "text_secondary": "#666666",
    "text_light": "#999999",
    "panel": "#FFFFFF",
    "line": "#E0E0E0",
    "button_hover": "#00A017",
}


def _format_number(v: float) -> str:
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:.3f}"


def _alpha_label(index: int) -> str:
    """Convertit 0->A, 1->B, ..., 25->Z, 26->AA, etc."""
    if index < 0:
        return "?"
    s = ""
    n = index
    while True:
        n, r = divmod(n, 26)
        s = chr(ord("A") + r) + s
        if n == 0:
            break
        n -= 1
    return s


class AnimatedButton(tk.Button):
    """Bouton avec changement de couleur au survol."""
    def __init__(self, master: tk.Widget, text: str, command=None, **kwargs) -> None:
        super().__init__(master, text=text, command=command, **kwargs)
        self.config(
            font=("Segoe UI", 9, "bold"),
            fg="white",
            bg=PALETTE["primary"],
            activebackground=PALETTE["primary_dark"],
            activeforeground="white",
            relief="solid",
            bd=0,
            padx=8,
            pady=4,
            cursor="hand2",
            highlightthickness=0,
        )
        self._base_bg = PALETTE["primary"]
        self._hover_bg = PALETTE["button_hover"]
        
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, _event: tk.Event) -> None:
        """Change couleur au survol."""
        self.config(bg=self._hover_bg)
    
    def _on_leave(self, _event: tk.Event) -> None:
        """Retour à l'état normal."""
        self.config(bg=self._base_bg)


class MatrixEditor(tk.Frame):
    def __init__(self, master: tk.Widget, rows: int = 5, cols: int = 5) -> None:
        super().__init__(master, bg=PALETTE["bg"], highlightthickness=1, highlightbackground=PALETTE["line"])
        self.rows = rows
        self.cols = cols
        self.entries: List[List[tk.Entry]] = []
        self.labels: List[str] = [str(i + 1) for i in range(min(rows, cols))]
        self.zoom_factor: float = 1.0
        self._build_grid()

    def _snapshot_values(self) -> List[List[str]]:
        if not self.entries:
            return []
        snap: List[List[str]] = []
        for row in self.entries:
            snap.append([cell.get() for cell in row])
        return snap

    def _build_grid(self) -> None:
        previous_values = self._snapshot_values()

        for child in self.winfo_children():
            child.destroy()

        self.entries = []

        for j in range(self.cols):
            header = self.labels[j] if j < len(self.labels) else str(j + 1)
            header_font_size = max(8, int(10 * self.zoom_factor))
            lbl = tk.Label(self, text=header, bg=PALETTE["bg"], fg=PALETTE["text"], font=("Segoe UI", header_font_size, "bold"))
            lbl.grid(row=0, column=j + 1, padx=2, pady=2)

        for i in range(self.rows):
            header = self.labels[i] if i < len(self.labels) else str(i + 1)
            header_font_size = max(8, int(10 * self.zoom_factor))
            lbl = tk.Label(self, text=header, bg=PALETTE["bg"], fg=PALETTE["text"], font=("Segoe UI", header_font_size, "bold"))
            lbl.grid(row=i + 1, column=0, padx=2, pady=2)

            row_entries: List[tk.Entry] = []
            for j in range(self.cols):
                # Pour des petites matrices (<=8), on garde des cellules lisibles sur un seul ecran.
                small_grid = max(self.rows, self.cols) <= 8
                base_width = 7 if small_grid else 6
                base_font = 10 if small_grid else 9
                entry_width = max(4, int(round(base_width * self.zoom_factor)))
                entry_font = ("Consolas", max(8, int(base_font * self.zoom_factor)))
                e = tk.Entry(self, width=entry_width, justify="center", relief="solid", bd=1, font=entry_font)
                e.grid(row=i + 1, column=j + 1, padx=1, pady=1, ipady=max(2, int(4 * self.zoom_factor)))

                prev = ""
                if i < len(previous_values) and j < len(previous_values[i]):
                    prev = previous_values[i][j]
                if prev:
                    e.insert(0, prev)
                elif i == j:
                    e.configure(bg="#F1FDF2")
                row_entries.append(e)
            self.entries.append(row_entries)

    def resize(self, rows: int, cols: int) -> None:
        self.rows = rows
        self.cols = cols
        if len(self.labels) != min(rows, cols):
            self.labels = [str(i + 1) for i in range(min(rows, cols))]
        self._build_grid()

    def set_labels(self, labels: List[str]) -> None:
        self.labels = labels[:]
        self._build_grid()

    def set_zoom(self, zoom_factor: float) -> None:
        self.zoom_factor = max(0.7, min(1.8, zoom_factor))
        self._build_grid()

    def get_matrix(self) -> List[List[Optional[float]]]:
        values: List[List[Optional[float]]] = []
        for i in range(self.rows):
            row: List[Optional[float]] = []
            for j in range(self.cols):
                raw = self.entries[i][j].get().strip()
                if raw == "":
                    row.append(None)
                    continue
                try:
                    # On accepte uniquement des entiers dans le tableau.
                    val = int(raw)
                    if val > 1000:
                        raise ValueError(
                            f"Cellule ({i + 1},{j + 1}) invalide: '{raw}'. "
                            "La valeur ne doit pas dépasser 1000."
                        )
                except ValueError as exc:
                    raise ValueError(
                        f"Cellule ({i + 1},{j + 1}) invalide: '{raw}'. "
                        "Saisis uniquement des chiffres entiers de 0 à 1000 ou laisse vide."
                    ) from exc
                row.append(float(val))
            values.append(row)
        return values

    def set_from_matrix(self, matrix: List[List[Optional[float]]]) -> None:
        if not matrix or not matrix[0]:
            return
        self.resize(len(matrix), len(matrix[0]))
        for i in range(self.rows):
            for j in range(self.cols):
                self.entries[i][j].delete(0, tk.END)
                v = matrix[i][j]
                if i == j and (v is None or abs(v) < 1e-9):
                    continue
                if v is None:
                    continue
                self.entries[i][j].insert(0, _format_number(v))


class GraphCanvas(tk.Canvas):
    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master, bg=PALETTE["bg"], highlightthickness=1, highlightbackground=PALETTE["line"])
        self.node_positions: List[Tuple[float, float]] = []
        self.current_matrix: List[List[Optional[float]]] = []
        self.current_path: Optional[List[int]] = None
        self.current_title: str = "Graphe"
        self.current_labels: List[str] = []
        self._drag_node_idx: Optional[int] = None
        self.zoom_factor: float = 1.0

        self.bind("<MouseWheel>", self._on_mousewheel)
        # Drag global: le clic demarre sur un sommet, puis le mouvement reste actif
        # meme si le curseur sort de la forme.
        self.bind("<B1-Motion>", self._drag_node)
        self.bind("<ButtonRelease-1>", self._end_drag)

    def draw_graph(
        self,
        matrix: List[List[Optional[float]]],
        highlighted_path: Optional[List[int]] = None,
        title: str = "Graphe",
        preserve_positions: bool = True,
        node_labels: Optional[List[str]] = None,
    ) -> None:
        self.delete("all")
        n = len(matrix)
        if n == 0:
            return

        self.current_matrix = matrix
        self.current_path = highlighted_path
        self.current_title = title
        self.current_labels = node_labels[:] if node_labels else [str(i + 1) for i in range(n)]

        self.update_idletasks()
        view_w = max(self.winfo_width(), 500)
        view_h = max(self.winfo_height(), 400)
        virtual_w = max(view_w, int(900 * self.zoom_factor), int(n * 140 * self.zoom_factor))
        virtual_h = max(view_h, int(700 * self.zoom_factor), int(n * 120 * self.zoom_factor))
        self.configure(scrollregion=(0, 0, virtual_w, virtual_h))

        cx, cy = virtual_w / 2, virtual_h / 2
        radius = min(virtual_w, virtual_h) * 0.35
        radius = min(radius, max(220, n * 26))
        node_r = int(max(14, 18 * self.zoom_factor))

        self.create_text(10, 10, anchor="nw", text=title, fill=PALETTE["text"], font=("Segoe UI", 11, "bold"))

        if preserve_positions and len(self.node_positions) == n:
            positions = self.node_positions[:]
        else:
            positions = []
            # Disposition "comme avant" (en boucle), mais orientee horizontalement.
            # On utilise une ellipse plus large que haute pour une lecture horizontale.
            if n == 1:
                positions.append((cx, cy))
            else:
                rx = min(virtual_w * 0.40, max(220, n * 36))
                ry = min(virtual_h * 0.24, max(120, n * 14))
                for i in range(n):
                    angle = (2 * math.pi * i / n) - (math.pi / 2)
                    x = cx + rx * math.cos(angle)
                    y = cy + ry * math.sin(angle)
                    positions.append((x, y))

        path_edges = set()
        if highlighted_path and len(highlighted_path) >= 2:
            for i in range(len(highlighted_path) - 1):
                path_edges.add((highlighted_path[i], highlighted_path[i + 1]))

        # 1) Dessiner d'abord les arcs non-chemin, puis 2) les arcs du chemin
        # pour garantir que le surlignage reste visible au-dessus des autres arcs.
        def draw_edges(only_path: bool) -> None:
            for i in range(n):
                for j in range(n):
                    weight = matrix[i][j]
                    if weight is None or i == j:
                        continue
                    is_path_edge = (i, j) in path_edges
                    if only_path != is_path_edge:
                        continue

                    x1, y1 = positions[i]
                    x2, y2 = positions[j]
                    color = PALETTE["path"] if is_path_edge else "#7A7A7A"
                    width = 3 if is_path_edge else 1.5

                    self._draw_arrow(x1, y1, x2, y2, node_r, color, width)

                    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                    offset_x = (y1 - y2) * 0.03
                    offset_y = (x2 - x1) * 0.03
                    txt = _format_number(weight)
                    self.create_text(
                        mx + offset_x,
                        my + offset_y,
                        text=txt,
                        fill=color,
                        font=("Consolas", max(8, int(9 * self.zoom_factor)), "bold"),
                    )

        draw_edges(only_path=False)
        draw_edges(only_path=True)

        for i, (x, y) in enumerate(positions):
            fill = PALETTE["primary"] if not highlighted_path or i not in highlighted_path else PALETTE["path_node"]
            self.create_oval(
                x - node_r,
                y - node_r,
                x + node_r,
                y + node_r,
                fill=fill,
                outline=PALETTE["primary_dark"],
                width=2,
                tags=("node", f"node_{i}"),
            )
            txt = self.current_labels[i] if i < len(self.current_labels) else str(i + 1)
            self.create_text(
                x,
                y,
                text=txt,
                fill="white",
                font=("Segoe UI", max(8, int(10 * self.zoom_factor)), "bold"),
                tags=("node", f"node_{i}"),
            )

        self.node_positions = positions
        self.tag_bind("node", "<ButtonPress-1>", self._start_drag)

    def _draw_arrow(self, x1: float, y1: float, x2: float, y2: float, node_r: float, color: str, width: float) -> None:
        dx = x2 - x1
        dy = y2 - y1
        dist = math.hypot(dx, dy)
        if dist < 1e-6:
            return

        ux = dx / dist
        uy = dy / dist

        start_x = x1 + ux * node_r
        start_y = y1 + uy * node_r
        end_x = x2 - ux * node_r
        end_y = y2 - uy * node_r

        self.create_line(
            start_x,
            start_y,
            end_x,
            end_y,
            fill=color,
            width=width,
            arrow=tk.LAST,
            arrowshape=(10, 12, 4),
            smooth=True,
        )

    def _start_drag(self, event: tk.Event) -> None:
        item = self.find_withtag("current")
        if not item:
            return
        tags = self.gettags(item[0])
        for tag in tags:
            if tag.startswith("node_"):
                self._drag_node_idx = int(tag.split("_", 1)[1])
                self.configure(cursor="fleur")
                return

    def _drag_node(self, event: tk.Event) -> None:
        if self._drag_node_idx is None:
            return
        x = self.canvasx(event.x)
        y = self.canvasy(event.y)
        idx = self._drag_node_idx
        if 0 <= idx < len(self.node_positions):
            self.node_positions[idx] = (x, y)
            self.draw_graph(
                self.current_matrix,
                self.current_path,
                self.current_title,
                preserve_positions=True,
                node_labels=self.current_labels,
            )

    def _end_drag(self, _event: tk.Event) -> None:
        self._drag_node_idx = None
        self.configure(cursor="")

    def _on_mousewheel(self, event: tk.Event) -> None:
        # Shift + molette: horizontal, sinon vertical.
        delta = -1 if event.delta > 0 else 1
        if (event.state & 0x0001) != 0:
            self.xview_scroll(delta, "units")
        else:
            self.yview_scroll(delta, "units")

    def set_zoom(self, zoom_factor: float) -> None:
        self.zoom_factor = max(0.6, min(2.0, zoom_factor))
        if self.current_matrix:
            self.draw_graph(
                self.current_matrix,
                self.current_path,
                self.current_title,
                preserve_positions=False,
                node_labels=self.current_labels,
            )


class DemoucronApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Demoucron Studio - Min/Max")
        self.geometry("1400x860")
        self.minsize(1200, 760)
        self.configure(bg=PALETTE["bg"])
        
        # Charger et configurer l'icône de l'application
        self._setup_icon()

        # Header fixe (titre + filtres) et body scrollable (tableau/graphe/resultats).
        self.fixed_header = tk.Frame(self, bg=PALETTE["bg"])
        self.fixed_header.pack(side="top", fill="x")

        # Content area (canvas + scrollbar)
        content_frame = tk.Frame(self, bg=PALETTE["bg"])
        content_frame.pack(side="top", fill="both", expand=True)
        
        self.root_canvas = tk.Canvas(content_frame, bg=PALETTE["bg"], highlightthickness=0)
        self.root_scroll_y = tk.Scrollbar(content_frame, orient="vertical", command=self.root_canvas.yview)
        self.root_canvas.configure(yscrollcommand=self.root_scroll_y.set)
        self.root_canvas.pack(side="left", fill="both", expand=True)
        self.root_scroll_y.pack(side="right", fill="y")
        
        # Footer au bas de la fenêtre
        self.fixed_footer = tk.Frame(self, bg=PALETTE["bg"], highlightbackground=PALETTE["line"], highlightthickness=1)
        self.fixed_footer.pack(side="bottom", fill="x")

        self.page = tk.Frame(self.root_canvas, bg=PALETTE["bg"])
        self.page_window = self.root_canvas.create_window((0, 0), window=self.page, anchor="nw")
        self.page.bind("<Configure>", self._on_page_configure)
        self.root_canvas.bind("<Configure>", self._on_root_canvas_configure)
        self.root_canvas.bind("<MouseWheel>", self._on_global_mousewheel)

        self.current_matrix: List[List[Optional[float]]] = []
        self.node_labels: List[str] = [str(i + 1) for i in range(6)]
        self.label_to_index: dict[str, int] = {}
        self.table_zoom: float = 1.0
        self.graph_zoom: float = 1.0
        self._last_label_mode: str = "Chiffres"
        self.last_result: Optional[DemoucronResult] = None
        self.last_mode: Optional[str] = None

        self._build_ui()
        self.after(50, lambda: self.root_canvas.yview_moveto(0.0))

    def _center_popup(self, popup: tk.Toplevel) -> None:
        """Centre un popup par rapport a la fenetre principale."""
        popup.update_idletasks()
        root_x = self.winfo_rootx()
        root_y = self.winfo_rooty()
        root_w = self.winfo_width()
        root_h = self.winfo_height()
        w = popup.winfo_reqwidth()
        h = popup.winfo_reqheight()
        x = root_x + max(0, (root_w - w) // 2)
        y = root_y + max(0, (root_h - h) // 2)
        popup.geometry(f"+{x}+{y}")

    def _setup_icon(self) -> None:
        """Configure l'icône pour la fenêtre et la barre des tâches."""
        app_dir = os.path.dirname(__file__)
        png_path = os.path.join(app_dir, "algorithme.png")
        ico_path = os.path.join(app_dir, "algorithme.ico")
        
        # Créer le fichier .ico à partir du .png s'il n'existe pas
        if os.path.exists(png_path) and not os.path.exists(ico_path):
            try:
                from PIL import Image
                img = Image.open(png_path)
                # Convertir en RGB si nécessaire (PNG peut avoir canal alpha)
                if img.mode in ("RGBA", "LA", "P"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                    img = background
                # Créer des icônes de différentes tailles pour une meilleure qualité
                img.save(ico_path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
            except Exception:
                pass
        
        # Utiliser l'icône .ico pour la barre des tâches (Windows)
        if os.path.exists(ico_path):
            try:
                self.wm_iconbitmap(ico_path)
            except Exception:
                pass
        
        # Utiliser l'icône PNG pour la fenêtre (tous les systèmes)
        if os.path.exists(png_path):
            try:
                from PIL import Image, ImageTk
                img = Image.open(png_path)
                img.thumbnail((32, 32), Image.Resampling.LANCZOS)
                self.icon_image = ImageTk.PhotoImage(img)
                self.wm_iconphoto(False, self.icon_image)
            except Exception:
                pass

    def _on_page_configure(self, _event: tk.Event) -> None:
        self.root_canvas.configure(scrollregion=self.root_canvas.bbox("all"))

    def _on_root_canvas_configure(self, event: tk.Event) -> None:
        # Conserve la largeur de la page egale a la largeur visible.
        self.root_canvas.itemconfigure(self.page_window, width=event.width)

    def _on_global_mousewheel(self, event: tk.Event) -> None:
        self.root_canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")

    def _build_ui(self) -> None:
        # Header épuré
        top = tk.Frame(self.fixed_header, bg=PALETTE["bg"])
        top.pack(fill="x", padx=16, pady=(10, 8))

        title = tk.Label(
            top,
            text="Algorithme de Demoucron",
            bg=PALETTE["bg"],
            fg=PALETTE["primary"],
            font=("Segoe UI", 20, "bold"),
        )
        title.pack(side="left")

        # Contrôles resserrés avec meilleur style
        controls = tk.Frame(
            self.fixed_header, 
            bg=PALETTE["bg"], 
            highlightbackground=PALETTE["line"],
            highlightthickness=1,
            relief="flat"
        )
        controls.pack(fill="x", padx=16, pady=(0, 8))

        tk.Label(controls, text="Lignes", bg=PALETTE["bg"], fg=PALETTE["text"], font=("Segoe UI", 9)).grid(row=0, column=0, padx=6, pady=6)
        self.rows_var = tk.StringVar(value="6")
        rows_spin = tk.Spinbox(controls, from_=2, to=20, textvariable=self.rows_var, width=4, font=("Segoe UI", 9), bg=PALETTE["bg"], relief="solid", bd=1)
        rows_spin.grid(row=0, column=1, padx=2, pady=6)

        tk.Label(controls, text="Colonnes", bg=PALETTE["bg"], fg=PALETTE["text"], font=("Segoe UI", 9)).grid(row=0, column=2, padx=6, pady=6)
        self.cols_var = tk.StringVar(value="6")
        cols_spin = tk.Spinbox(controls, from_=2, to=20, textvariable=self.cols_var, width=4, font=("Segoe UI", 9), bg=PALETTE["bg"], relief="solid", bd=1)
        cols_spin.grid(row=0, column=3, padx=2, pady=6)

        tk.Label(controls, text="Étiquettes", bg=PALETTE["bg"], fg=PALETTE["text"], font=("Segoe UI", 9)).grid(row=0, column=4, padx=(12, 6), pady=6)
        self.label_mode_var = tk.StringVar(value="Chiffres")
        self.label_mode_combo = ttk.Combobox(
            controls,
            textvariable=self.label_mode_var,
            width=8,
            state="readonly",
            values=["Chiffres", "Lettres"],
        )
        self.label_mode_combo.grid(row=0, column=5, padx=2, pady=6)
        self.label_mode_combo.bind("<<ComboboxSelected>>", self.on_label_mode_change)

        self.src_var = tk.StringVar(value="1")
        self.dst_var = tk.StringVar(value="6")

        tk.Label(controls, text="Source", bg=PALETTE["bg"], fg=PALETTE["text"], font=("Segoe UI", 9)).grid(row=0, column=6, padx=(12, 6), pady=6)
        self.src_combo = ttk.Combobox(controls, textvariable=self.src_var, width=5, state="readonly")
        self.src_combo.grid(row=0, column=7, padx=2, pady=6)

        tk.Label(controls, text="Destination", bg=PALETTE["bg"], fg=PALETTE["text"], font=("Segoe UI", 9)).grid(row=0, column=8, padx=6, pady=6)
        self.dst_combo = ttk.Combobox(controls, textvariable=self.dst_var, width=5, state="readonly")
        self.dst_combo.grid(row=0, column=9, padx=2, pady=6)

        self._make_button(controls, "Créer", self.create_table).grid(row=0, column=10, padx=4, pady=6)
        self._make_button(controls, "Actualiser", self.refresh_all).grid(row=0, column=11, padx=4, pady=6)
        self._make_button(controls, "Graphe", self.generate_graph).grid(row=0, column=12, padx=4, pady=6)
        self._make_button(controls, "Min", self.compute_min).grid(row=0, column=13, padx=4, pady=6)
        self._make_button(controls, "Max", self.compute_max).grid(row=0, column=14, padx=4, pady=6)

        body = tk.Frame(self.page, bg=PALETTE["bg"])
        body.pack(fill="both", expand=True, padx=12, pady=(6, 10))
        body.grid_rowconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=0)
        body.grid_columnconfigure(0, weight=1)

        content = tk.PanedWindow(body, orient=tk.HORIZONTAL, sashrelief=tk.FLAT, bg=PALETTE["bg"], sashwidth=8)
        content.grid(row=0, column=0, sticky="nsew", pady=(0, 8))

        left = tk.Frame(content, bg=PALETTE["bg"])
        right = tk.Frame(content, bg=PALETTE["bg"])
        content.add(left, minsize=360)
        content.add(right, minsize=700)

        # Titre du panneau gauche avec accent
        left_title = tk.Label(
            left, 
            text="Matrice d'adjacence",
            bg=PALETTE["bg"], 
            fg=PALETTE["primary"],
            font=("Segoe UI", 12, "bold")
        )
        left_title.pack(anchor="w", pady=(0, 8))
        
        # Descriptif
        left_desc = tk.Label(
            left,
            text="Saisissez les poids des arcs",
            bg=PALETTE["bg"],
            fg=PALETTE["text_light"],
            font=("Segoe UI", 9)
        )
        left_desc.pack(anchor="w", pady=(0, 6))

        table_container = tk.Frame(left, bg=PALETTE["bg"], relief="flat")
        table_container.pack(fill="both", expand=True, pady=(0, 8))

        self.table_canvas = tk.Canvas(table_container, bg=PALETTE["bg"], highlightthickness=0)
        self.table_scroll_y = tk.Scrollbar(table_container, orient="vertical", command=self.table_canvas.yview)
        self.table_scroll_x = tk.Scrollbar(table_container, orient="horizontal", command=self.table_canvas.xview)
        self.table_canvas.configure(yscrollcommand=self.table_scroll_y.set, xscrollcommand=self.table_scroll_x.set)

        self.table_canvas.grid(row=0, column=0, sticky="nsew")
        self.table_scroll_y.grid(row=0, column=1, sticky="ns")
        self.table_scroll_x.grid(row=1, column=0, sticky="ew")
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        self.table_frame_holder = tk.Frame(self.table_canvas, bg=PALETTE["bg"])
        self.table_canvas.create_window((0, 0), window=self.table_frame_holder, anchor="nw")

        self.matrix_editor = MatrixEditor(self.table_frame_holder, 6, 6)
        self.matrix_editor.pack(anchor="nw", pady=4)

        self.table_frame_holder.bind("<Configure>", self._on_table_configure)

        # Zoom controls avec meilleur style
        table_zoom_frame = tk.Frame(left, bg=PALETTE["bg"])
        table_zoom_frame.pack(fill="x", pady=(4, 0))
        tk.Label(table_zoom_frame, text="Zoom", bg=PALETTE["bg"], fg=PALETTE["text"], font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 10))
        self._make_button(table_zoom_frame, "+", self.zoom_table_in).pack(side="left", padx=3)
        self._make_button(table_zoom_frame, "-", self.zoom_table_out).pack(side="left", padx=3)
        self._make_button(table_zoom_frame, "100%", self.zoom_table_reset).pack(side="left", padx=4)

        self.info_label = tk.Label(
            left,
            text="Entrez des nombres entiers. Cellule vide = pas d'arc.",
            bg=PALETTE["bg"],
            fg=PALETTE["text_light"],
            justify="left",
            font=("Segoe UI", 8),
            wraplength=280,
        )
        self.info_label.pack(anchor="w", pady=(10, 0))

        right_top = tk.Frame(right, bg=PALETTE["bg"])
        right_top.pack(fill="both", expand=True)

        # Titre du graphe avec accent
        graph_label = tk.Label(
            right_top, 
            text="Graphe Orienté",
            bg=PALETTE["bg"], 
            fg=PALETTE["primary"],
            font=("Segoe UI", 12, "bold")
        )
        graph_label.pack(anchor="w", pady=(0, 6))
        
        # Descriptif graphe
        graph_desc = tk.Label(
            right_top,
            text="Visualisation et édition du graphe",
            bg=PALETTE["bg"],
            fg=PALETTE["text_light"],
            font=("Segoe UI", 9)
        )
        graph_desc.pack(anchor="w", pady=(0, 8))

        graph_frame = tk.Frame(right_top, bg=PALETTE["bg"])
        graph_frame.pack(fill="both", expand=True)

        self.graph_canvas = GraphCanvas(graph_frame)
        graph_scroll_y = tk.Scrollbar(graph_frame, orient="vertical", command=self.graph_canvas.yview)
        graph_scroll_x = tk.Scrollbar(graph_frame, orient="horizontal", command=self.graph_canvas.xview)
        self.graph_canvas.configure(yscrollcommand=graph_scroll_y.set, xscrollcommand=graph_scroll_x.set)

        self.graph_canvas.grid(row=0, column=0, sticky="nsew")
        graph_scroll_y.grid(row=0, column=1, sticky="ns")
        graph_scroll_x.grid(row=1, column=0, sticky="ew")

        graph_frame.grid_rowconfigure(0, weight=1)
        graph_frame.grid_columnconfigure(0, weight=1)

        # Zoom controls pour le graphe
        graph_zoom_frame = tk.Frame(right_top, bg=PALETTE["bg"])
        graph_zoom_frame.pack(fill="x", pady=(4, 8))
        tk.Label(graph_zoom_frame, text="Zoom", bg=PALETTE["bg"], fg=PALETTE["text"], font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 10))
        self._make_button(graph_zoom_frame, "+", self.zoom_graph_in).pack(side="left", padx=3)
        self._make_button(graph_zoom_frame, "-", self.zoom_graph_out).pack(side="left", padx=3)
        self._make_button(graph_zoom_frame, "100%", self.zoom_graph_reset).pack(side="left", padx=3)

        # Outils d'édition du graphe avec meilleur style
        graph_tools = tk.Frame(
            right_top, 
            bg=PALETTE["panel"], 
            highlightbackground=PALETTE["line"],
            highlightthickness=1,
            relief="flat"
        )
        graph_tools.pack(fill="x", pady=(0, 0))
        tk.Label(
            graph_tools, 
            text="Outils d'édition",
            bg=PALETTE["panel"], 
            fg=PALETTE["primary"],
            font=("Segoe UI", 10, "bold")
        ).grid(row=0, column=0, columnspan=6, sticky="w", padx=10, pady=(8, 8))

        self._make_button(graph_tools, "+ Nœud", self.add_vertex_graph).grid(row=1, column=0, padx=6, pady=6)
        self._make_button(graph_tools, "- Nœud", self.delete_vertex_graph).grid(row=1, column=1, padx=6, pady=6)
        self._make_button(graph_tools, "Renommer", self.rename_vertex_graph).grid(row=1, column=2, padx=6, pady=6)
        self._make_button(graph_tools, "+ Arc", self.add_or_edit_edge_graph).grid(row=1, column=3, padx=6, pady=6)
        self._make_button(graph_tools, "- Arc", self.delete_edge_graph).grid(row=1, column=4, padx=6, pady=6)

        bottom = tk.Frame(body, bg=PALETTE["bg"])
        bottom.grid(row=1, column=0, sticky="nsew")

        # Panneau de résultat amélioré
        result_panel = tk.Frame(
            bottom, 
            bg=PALETTE["panel"],
            highlightbackground=PALETTE["line"],
            highlightthickness=1,
            relief="flat"
        )
        result_panel.pack(side="left", fill="both", expand=True, padx=(0, 8))

        tk.Label(
            result_panel,
            text="Résultat",
            bg=PALETTE["panel"],
            fg=PALETTE["primary"],
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=12, pady=(10, 6))
        
        self.result_text = tk.Label(
            result_panel,
            text="Aucun calcul lancé.",
            bg=PALETTE["panel"],
            fg=PALETTE["text"],
            justify="left",
            font=("Segoe UI", 10)
        )
        self.result_text.pack(anchor="w", padx=12, pady=(0, 12))

        # Panneau d'étapes amélioré
        steps_panel = tk.Frame(
            bottom,
            bg=PALETTE["panel"],
            highlightbackground=PALETTE["line"],
            highlightthickness=1,
            relief="flat"
        )
        steps_panel.pack(side="left", fill="both", expand=True, padx=(8, 0))

        tk.Label(
            steps_panel,
            text="Étapes de Calcul",
            bg=PALETTE["panel"],
            fg=PALETTE["primary"],
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=12, pady=(10, 6))
        
        self.steps_text = ScrolledText(
            steps_panel,
            wrap="none",
            height=18,
            font=("Consolas", 9),
            relief="flat",
            bg=PALETTE["bg"],
            fg=PALETTE["text"],
            insertbackground=PALETTE["primary"]
        )
        self.steps_text.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.steps_text.configure(state="disabled")

        # Footer
        footer_content = tk.Frame(self.fixed_footer, bg=PALETTE["bg"])
        footer_content.pack(fill="x", padx=16, pady=6)
        
        footer_label = tk.Label(
            footer_content,
            text="@ 2026 Demoucron Algorithm Suite",
            bg=PALETTE["bg"],
            fg=PALETTE["text_light"],
            font=("Segoe UI", 8),
        )
        footer_label.pack(side="left")

        self._sync_node_selectors(6, regenerate_labels=True)
        self._adapt_table_view(6, 6)

    def _make_button(self, master: tk.Widget, text: str, command) -> tk.Button:
        return AnimatedButton(
            master,
            text=text,
            command=command,
        )


    def _on_table_configure(self, event: tk.Event) -> None:
        self.table_canvas.configure(scrollregion=self.table_canvas.bbox("all"))

    def _adapt_table_view(self, rows: int, cols: int) -> None:
        """Ajuste l'affichage pour tout voir en une fois si la matrice est <= 8x8."""
        zoom = self.table_zoom
        if max(rows, cols) <= 8:
            # Taille estimee pour afficher toute la grille avec en-tetes.
            width = int((90 + cols * 84) * zoom)
            width = min(width, 620)
            height = int((70 + rows * 34) * zoom)
            self.table_canvas.configure(width=width, height=height)
        else:
            # Redonne un comportement flexible et scrollable pour les grandes matrices.
            self.table_canvas.configure(width=int(420 * zoom), height=int(380 * zoom))

    def _default_label(self, index: int) -> str:
        if self.label_mode_var.get() == "Lettres":
            return _alpha_label(index)
        return str(index + 1)

    def _fit_labels_to_size(self, n: int, regenerate: bool) -> None:
        if regenerate or not self.node_labels:
            self.node_labels = [self._default_label(i) for i in range(n)]
            return
        if len(self.node_labels) > n:
            self.node_labels = self.node_labels[:n]
        elif len(self.node_labels) < n:
            start = len(self.node_labels)
            self.node_labels.extend(self._default_label(i) for i in range(start, n))

    def on_label_mode_change(self, _event: tk.Event | None = None) -> None:
        self._last_label_mode = self.label_mode_var.get()
        try:
            matrix = self._read_square_matrix()
            n = len(matrix)
        except Exception:
            n = min(self.matrix_editor.rows, self.matrix_editor.cols)
        self._sync_node_selectors(n, regenerate_labels=True)
        self.generate_graph(show_message=False)

    def on_graph_zoom_change(self, raw_value: str) -> None:
        try:
            pct = float(raw_value)
        except ValueError:
            return
        self.graph_zoom = max(0.6, min(2.0, pct / 100.0))
        self.graph_canvas.set_zoom(self.graph_zoom)

    def zoom_graph_in(self) -> None:
        self.graph_zoom = min(2.0, self.graph_zoom + 0.1)
        self.graph_canvas.set_zoom(self.graph_zoom)

    def zoom_graph_out(self) -> None:
        self.graph_zoom = max(0.6, self.graph_zoom - 0.1)
        self.graph_canvas.set_zoom(self.graph_zoom)

    def zoom_graph_reset(self) -> None:
        self.graph_zoom = 1.0
        self.graph_canvas.set_zoom(self.graph_zoom)

    def _apply_table_zoom(self) -> None:
        self.matrix_editor.set_zoom(self.table_zoom)
        self._adapt_table_view(self.matrix_editor.rows, self.matrix_editor.cols)
        self._on_table_configure(None)

    def zoom_table_in(self) -> None:
        self.table_zoom = min(1.8, self.table_zoom + 0.1)
        self._apply_table_zoom()

    def zoom_table_out(self) -> None:
        self.table_zoom = max(0.7, self.table_zoom - 0.1)
        self._apply_table_zoom()

    def zoom_table_reset(self) -> None:
        self.table_zoom = 1.0
        self._apply_table_zoom()

    def _sync_node_selectors(self, n: int, regenerate_labels: bool = False) -> None:
        self._fit_labels_to_size(n, regenerate_labels)
        values = self.node_labels[:]
        self.label_to_index = {label: idx for idx, label in enumerate(values)}
        self.matrix_editor.set_labels(self.node_labels)

        self.src_combo["values"] = values
        self.dst_combo["values"] = values
        if values:
            if self.src_var.get() not in values:
                self.src_var.set(values[0])
            if self.dst_var.get() not in values:
                self.dst_var.set(values[-1])

    def _ensure_square_from_table(self) -> bool:
        try:
            self.current_matrix = self._read_square_matrix()
            return True
        except ValueError as exc:
            messagebox.showerror("Erreur", str(exc))
            return False

    def sync_graph_to_table(self) -> None:
        if not self.current_matrix:
            if not self._ensure_square_from_table():
                return
        self.matrix_editor.set_from_matrix(self.current_matrix)
        self.matrix_editor.set_labels(self.node_labels)
        n = len(self.current_matrix)
        self._adapt_table_view(n, n)
        self._on_table_configure(None)

    def add_vertex_graph(self) -> None:
        if not self.current_matrix:
            if not self._ensure_square_from_table():
                return
        n = len(self.current_matrix)
        for row in self.current_matrix:
            row.append(None)
        new_row = [None] * (n + 1)
        self.current_matrix.append(new_row)

        self.node_labels.append(self._default_label(n))
        self._sync_node_selectors(len(self.current_matrix), regenerate_labels=False)
        self.sync_graph_to_table()
        self.generate_graph(show_message=False)
        self._set_result("Sommet ajoute depuis le graphe.")

    def delete_vertex_graph(self) -> None:
        if not self.current_matrix:
            if not self._ensure_square_from_table():
                return
        n = len(self.current_matrix)
        if n <= 2:
            messagebox.showwarning("Suppression impossible", "Il faut conserver au moins 2 sommets.")
            return
        target_label = self.src_var.get().strip()
        if target_label not in self.label_to_index:
            messagebox.showerror("Erreur", "Selectionne un sommet valide dans Source.")
            return
        idx = self.label_to_index[target_label]

        self.current_matrix.pop(idx)
        for row in self.current_matrix:
            row.pop(idx)
        if idx < len(self.node_labels):
            self.node_labels.pop(idx)

        self._sync_node_selectors(len(self.current_matrix), regenerate_labels=False)
        self.sync_graph_to_table()
        self.generate_graph(show_message=False)
        self._set_result(f"Sommet {target_label} supprime.")

    def rename_vertex_graph(self) -> None:
        if not self.current_matrix:
            if not self._ensure_square_from_table():
                return
        old_label = self.src_var.get().strip()
        if old_label not in self.label_to_index:
            messagebox.showerror("Erreur", "Selectionne un sommet valide dans Source.")
            return
        idx = self.label_to_index[old_label]
        new_label = simpledialog.askstring("Renommer sommet", f"Nouveau nom pour {old_label}:", parent=self)
        if new_label is None:
            return
        new_label = new_label.strip()
        if not new_label:
            messagebox.showerror("Erreur", "Le label ne peut pas etre vide.")
            return
        if new_label in self.label_to_index and new_label != old_label:
            messagebox.showerror("Erreur", "Ce label existe deja.")
            return
        self.node_labels[idx] = new_label
        self._sync_node_selectors(len(self.current_matrix), regenerate_labels=False)
        self.sync_graph_to_table()
        self.generate_graph(show_message=False)
        self._set_result(f"Sommet {old_label} renomme en {new_label}.")

    def _edge_popup(self) -> Optional[Tuple[str, str, Optional[int]]]:
        if not self.node_labels:
            return None

        popup = tk.Toplevel(self)
        popup.title("Relation entre sommets")
        popup.transient(self)
        popup.grab_set()
        popup.configure(bg=PALETTE["bg"])
        popup.resizable(False, False)
        popup.geometry("380x280")

        container = tk.Frame(popup, bg=PALETTE["bg"], padx=16, pady=12)
        container.pack(fill="both", expand=True)

        # Titre dans le popup
        title_lbl = tk.Label(
            container,
            text="Créer ou modifier un arc",
            bg=PALETTE["bg"],
            fg=PALETTE["primary"],
            font=("Segoe UI", 12, "bold")
        )
        title_lbl.pack(anchor="w", pady=(0, 12))

        # Départ
        tk.Label(container, text="Départ", bg=PALETTE["bg"], fg=PALETTE["text"], font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))
        src_var = tk.StringVar(value=self.src_var.get() if self.src_var.get() in self.node_labels else self.node_labels[0])
        src_box = ttk.Combobox(container, textvariable=src_var, state="readonly", values=self.node_labels, width=25)
        src_box.pack(anchor="w", pady=(0, 10), fill="x")

        # Arrivée
        tk.Label(container, text="Arrivée", bg=PALETTE["bg"], fg=PALETTE["text"], font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))
        dst_var = tk.StringVar(value=self.dst_var.get() if self.dst_var.get() in self.node_labels else self.node_labels[-1])
        dst_box = ttk.Combobox(container, textvariable=dst_var, state="readonly", values=self.node_labels, width=25)
        dst_box.pack(anchor="w", pady=(0, 10), fill="x")

        # Poids
        tk.Label(container, text="Poids (nombre entier)", bg=PALETTE["bg"], fg=PALETTE["text"], font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))
        weight_var = tk.StringVar(value="")
        weight_entry = tk.Entry(
            container,
            textvariable=weight_var,
            width=25,
            justify="center",
            font=("Consolas", 10),
            relief="solid",
            bd=1
        )
        weight_entry.pack(anchor="w", pady=(0, 4), fill="x")
        
        # Info
        info_lbl = tk.Label(
            container,
            text="Laisse vide pour supprimer l'arc",
            bg=PALETTE["bg"],
            fg=PALETTE["text_light"],
            font=("Segoe UI", 8)
        )
        info_lbl.pack(anchor="w", pady=(0, 10))

        if src_var.get() in self.label_to_index and dst_var.get() in self.label_to_index and self.current_matrix:
            s = self.label_to_index[src_var.get()]
            d = self.label_to_index[dst_var.get()]
            current = self.current_matrix[s][d]
            if current is not None:
                weight_var.set(str(int(current)) if abs(current - round(current)) < 1e-9 else "")

        result: dict[str, Optional[Tuple[str, str, Optional[int]]]] = {"value": None}

        def submit() -> None:
            src_label = src_var.get().strip()
            dst_label = dst_var.get().strip()
            raw = weight_var.get().strip()
            if src_label not in self.label_to_index or dst_label not in self.label_to_index:
                messagebox.showerror("Erreur", "Sélection départ/arrivée invalide.", parent=popup)
                return
            if raw == "":
                result["value"] = (src_label, dst_label, None)
                popup.destroy()
                return
            try:
                w = int(raw)
                if w > 1000:
                    messagebox.showerror(
                        "Erreur",
                        "Le poids ne doit pas dépasser 1000.",
                        parent=popup,
                    )
                    return
            except ValueError:
                messagebox.showerror(
                    "Erreur",
                    "Le poids doit contenir uniquement des chiffres entiers de 0 à 1000.",
                    parent=popup,
                )
                return
            result["value"] = (src_label, dst_label, w)
            popup.destroy()

        # Boutons avec meilleur style
        actions = tk.Frame(container, bg=PALETTE["bg"])
        actions.pack(fill="x", pady=(8, 0))
        
        cancel_btn = tk.Button(
            actions,
            text="Annuler",
            command=popup.destroy,
            relief="solid",
            bd=1,
            bg=PALETTE["line"],
            fg=PALETTE["text"],
            padx=12,
            pady=6,
            font=("Segoe UI", 10, "bold")
        )
        cancel_btn.pack(side="right", padx=(4, 0))
        
        validate_btn = AnimatedButton(
            actions,
            text="Valider",
            command=submit,
        )
        validate_btn.pack(side="right", padx=4)

        self._center_popup(popup)
        popup.wait_window()
        return result["value"]

    def _edge_delete_popup(self) -> Optional[Tuple[str, str]]:
        if not self.node_labels:
            return None

        popup = tk.Toplevel(self)
        popup.title("Supprimer un arc")
        popup.transient(self)
        popup.grab_set()
        popup.configure(bg=PALETTE["bg"])
        popup.resizable(False, False)
        popup.geometry("330x220")

        container = tk.Frame(popup, bg=PALETTE["bg"], padx=16, pady=12)
        container.pack(fill="both", expand=True)

        # Titre
        title_lbl = tk.Label(
            container,
            text="Sélectionner l'arc à supprimer",
            bg=PALETTE["bg"],
            fg=PALETTE["primary"],
            font=("Segoe UI", 12, "bold")
        )
        title_lbl.pack(anchor="w", pady=(0, 12))

        # Départ
        tk.Label(container, text="Départ", bg=PALETTE["bg"], fg=PALETTE["text"], font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))
        src_var = tk.StringVar(value=self.src_var.get() if self.src_var.get() in self.node_labels else self.node_labels[0])
        src_box = ttk.Combobox(container, textvariable=src_var, state="readonly", values=self.node_labels, width=22)
        src_box.pack(anchor="w", pady=(0, 10), fill="x")

        # Arrivée
        tk.Label(container, text="Arrivée", bg=PALETTE["bg"], fg=PALETTE["text"], font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))
        dst_var = tk.StringVar(value=self.dst_var.get() if self.dst_var.get() in self.node_labels else self.node_labels[-1])
        dst_box = ttk.Combobox(container, textvariable=dst_var, state="readonly", values=self.node_labels, width=22)
        dst_box.pack(anchor="w", pady=(0, 14), fill="x")

        result: dict[str, Optional[Tuple[str, str]]] = {"value": None}

        def submit() -> None:
            src_label = src_var.get().strip()
            dst_label = dst_var.get().strip()
            if src_label not in self.label_to_index or dst_label not in self.label_to_index:
                messagebox.showerror("Erreur", "Sélection départ/arrivée invalide.", parent=popup)
                return
            result["value"] = (src_label, dst_label)
            popup.destroy()

        # Boutons
        actions = tk.Frame(container, bg=PALETTE["bg"])
        actions.pack(fill="x")
        
        cancel_btn = tk.Button(
            actions,
            text="Annuler",
            command=popup.destroy,
            relief="solid",
            bd=1,
            bg=PALETTE["line"],
            fg=PALETTE["text"],
            padx=12,
            pady=6,
            font=("Segoe UI", 10, "bold")
        )
        cancel_btn.pack(side="right", padx=(4, 0))
        
        delete_btn = AnimatedButton(
            actions,
            text="Supprimer",
            command=submit,
        )
        delete_btn.pack(side="right", padx=4)

        self._center_popup(popup)
        popup.wait_window()
        return result["value"]

    def add_or_edit_edge_graph(self) -> None:
        if not self.current_matrix:
            if not self._ensure_square_from_table():
                return
        payload = self._edge_popup()
        if payload is None:
            return
        src_label, dst_label, weight = payload

        src = self.label_to_index[src_label]
        dst = self.label_to_index[dst_label]

        if weight is None:
            self.current_matrix[src][dst] = None
        else:
            self.current_matrix[src][dst] = float(weight)
        self.sync_graph_to_table()
        self.generate_graph(show_message=False)
        self._set_result(f"Arc {src_label} -> {dst_label} mis a jour.")

    def delete_edge_graph(self) -> None:
        if not self.current_matrix:
            if not self._ensure_square_from_table():
                return
        payload = self._edge_delete_popup()
        if payload is None:
            return
        src_label, dst_label = payload

        src = self.label_to_index[src_label]
        dst = self.label_to_index[dst_label]
        self.current_matrix[src][dst] = None
        self.sync_graph_to_table()
        self.generate_graph(show_message=False)
        self._set_result(f"Arc {src_label} -> {dst_label} supprime.")

    def _read_dimensions(self) -> Tuple[int, int]:
        try:
            rows = int(self.rows_var.get())
            cols = int(self.cols_var.get())
        except ValueError as exc:
            raise ValueError("Lignes/colonnes doivent etre des entiers.") from exc
        if rows < 2 or cols < 2 or rows > 20 or cols > 20:
            raise ValueError("Lignes/colonnes doivent etre entre 2 et 20.")
        return rows, cols

    def create_table(self) -> None:
        try:
            rows, cols = self._read_dimensions()
        except ValueError as exc:
            messagebox.showerror("Erreur", str(exc))
            return

        self.matrix_editor.resize(rows, cols)
        self._adapt_table_view(rows, cols)
        self._sync_node_selectors(min(rows, cols), regenerate_labels=True)
        self.current_matrix = []
        self.last_result = None
        self.last_mode = None
        self._set_result("Tableau recree.")
        self._set_steps("Les etapes apparaitront ici apres calcul MIN ou MAX.")

    def _read_square_matrix(self) -> List[List[Optional[float]]]:
        matrix = self.matrix_editor.get_matrix()
        rows = len(matrix)
        cols = len(matrix[0]) if rows else 0
        if rows != cols:
            raise ValueError("Pour Demoucron ici, il faut une matrice carree (lignes = colonnes).")
        return matrix

    def refresh_all(self) -> None:
        # Si des modifications ont ete faites depuis le graphe, on les reporte
        # d'abord dans le tableau avant de relire/actualiser tout.
        if self.current_matrix:
            self.sync_graph_to_table()

        try:
            self.current_matrix = self._read_square_matrix()
        except ValueError as exc:
            messagebox.showerror("Erreur de matrice", str(exc))
            return

        self._sync_node_selectors(len(self.current_matrix))
        self._adapt_table_view(len(self.current_matrix), len(self.current_matrix[0]))
        self.generate_graph(show_message=False)

        # Si on avait deja un mode calcule, on recalcul automatiquement.
        if self.last_mode == "min":
            self.compute_min(show_message=False)
        elif self.last_mode == "max":
            self.compute_max(show_message=False)
        else:
            self._set_result("Matrice mise a jour. Clique sur Calcul MIN ou Calcul MAX.")

    def generate_graph(self, show_message: bool = True) -> None:
        try:
            self.current_matrix = self._read_square_matrix()
        except ValueError as exc:
            messagebox.showerror("Erreur de matrice", str(exc))
            return

        self.graph_canvas.draw_graph(self.current_matrix, None, "Graphe courant", node_labels=self.node_labels)
        if show_message:
            self._set_result("Graphe genere. Lance MIN ou MAX pour voir le chemin optimal en couleur.")

    def _get_src_dst(self, n: int) -> Tuple[int, int]:
        src_label = self.src_var.get().strip()
        dst_label = self.dst_var.get().strip()
        if src_label not in self.label_to_index or dst_label not in self.label_to_index:
            raise ValueError("Source/Destination invalides.")
        src = self.label_to_index[src_label]
        dst = self.label_to_index[dst_label]
        if src < 0 or dst < 0 or src >= n or dst >= n:
            raise ValueError("Source/Destination hors limites.")
        return src, dst

    def _path_labels(self, path: List[int]) -> str:
        return " -> ".join(self.node_labels[idx] if idx < len(self.node_labels) else str(idx + 1) for idx in path)

    def compute_min(self, show_message: bool = True) -> None:
        try:
            self.current_matrix = self._read_square_matrix()
            n = len(self.current_matrix)
            src, dst = self._get_src_dst(n)
            result = demoucron_min(self.current_matrix)
            path = build_path(result.next_node, src, dst)
            value = result.values[src][dst]
        except Exception as exc:
            messagebox.showerror("Erreur MIN", str(exc))
            return

        self.last_result = result
        self.last_mode = "min"

        src_lbl = self.node_labels[src] if src < len(self.node_labels) else str(src + 1)
        dst_lbl = self.node_labels[dst] if dst < len(self.node_labels) else str(dst + 1)

        title = f"Graphe - Chemin MIN ({src_lbl} -> {dst_lbl})"
        self.graph_canvas.draw_graph(self.current_matrix, path, title, node_labels=self.node_labels)

        if not path:
            summary = f"MIN: aucun chemin de {src_lbl} vers {dst_lbl}."
        else:
            summary = (
                f"MIN {src_lbl}->{dst_lbl} | Cout optimal: {_format_number(value)}\n"
                f"Chemin: {self._path_labels(path)}"
            )
        self._set_result(summary)
        self._set_steps(self._format_steps(result, "MIN"))

        if show_message:
            self.info_label.configure(text="MIN calcule. Le chemin optimal est surligne en bleu.")

    def compute_max(self, show_message: bool = True) -> None:
        try:
            self.current_matrix = self._read_square_matrix()
            n = len(self.current_matrix)
            src, dst = self._get_src_dst(n)
            result = demoucron_max(self.current_matrix)
            path = build_path(result.next_node, src, dst)
            value = result.values[src][dst]
        except Exception as exc:
            messagebox.showerror("Erreur MAX", str(exc))
            return

        self.last_result = result
        self.last_mode = "max"

        src_lbl = self.node_labels[src] if src < len(self.node_labels) else str(src + 1)
        dst_lbl = self.node_labels[dst] if dst < len(self.node_labels) else str(dst + 1)

        title = f"Graphe - Chemin MAX ({src_lbl} -> {dst_lbl})"
        self.graph_canvas.draw_graph(self.current_matrix, path, title, node_labels=self.node_labels)

        if not path:
            summary = f"MAX: aucun chemin de {src_lbl} vers {dst_lbl}."
        else:
            summary = (
                f"MAX {src_lbl}->{dst_lbl} | Valeur optimale: {_format_number(value)}\n"
                f"Chemin: {self._path_labels(path)}"
            )
        self._set_result(summary)
        self._set_steps(self._format_steps(result, "MAX"))

        if show_message:
            self.info_label.configure(text="MAX calcule. Le chemin optimal est surligne en bleu.")

    def _set_result(self, text: str) -> None:
        """Affiche le résultat avec une animation progressive."""
        self.result_text.configure(text="")
        self._animate_result_text(text, 0)
    
    def _animate_result_text(self, text: str, index: int) -> None:
        """Animation progressive du texte du résultat."""
        if index < len(text):
            current = self.result_text.cget("text")
            self.result_text.configure(text=current + text[index])
            self.after(2, lambda: self._animate_result_text(text, index + 1))
        else:
            # Animation terminée
            pass

    def _set_steps(self, text: str) -> None:
        self.steps_text.configure(state="normal")
        self.steps_text.delete("1.0", tk.END)
        self.steps_text.insert(tk.END, text)
        self.steps_text.configure(state="disabled")

    def _format_steps(self, result: DemoucronResult, mode: str) -> str:
        lines: List[str] = []
        lines.append(f"Mode: {mode}")
        lines.append("Les matrices Dk incluent D0 (initiale), puis D1..Dn apres iteration de chaque k.")
        lines.append("")

        for idx, matrix in enumerate(result.history):
            lines.append(f"D{idx}")
            for i, row in enumerate(matrix):
                formatted = []
                for j, val in enumerate(row):
                    if i == j:
                        formatted.append(" inf")
                        continue
                    if val == float("inf"):
                        formatted.append(" inf")
                    else:
                        formatted.append(f"{_format_number(val):>4}")
                lines.append(" ".join(formatted))
            lines.append("")

        return "\n".join(lines)


def main() -> None:
    app = DemoucronApp()
    app.mainloop()


if __name__ == "__main__":
    main()
