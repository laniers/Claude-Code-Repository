"""Tkinter grid UI for browsing and selecting Street View results."""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

# Grid layout constants
COLS = 4
THUMB_W = 320
THUMB_H = 240
PAD = 8


class GridSelector:
    """Display places with Street View thumbnails in a scrollable grid.

    After the window is closed, `selected_indices` contains the indices
    of all places the user checked.
    """

    def __init__(self, places: list[dict], images: list[Image.Image | None]):
        self.places = places
        self.images = images
        self.selected_indices: list[int] = []

        self._build_ui()

    # ------------------------------------------------------------------ #
    #  UI construction
    # ------------------------------------------------------------------ #

    def _build_ui(self):
        self.root = tk.Tk()
        self.root.title("Street View Grid — select places to save")
        self.root.configure(bg="#1e1e1e")

        # Top bar
        top = tk.Frame(self.root, bg="#1e1e1e")
        top.pack(fill=tk.X, padx=PAD, pady=(PAD, 0))

        tk.Label(
            top,
            text=f"{len(self.places)} results — check the ones you want to keep",
            fg="#cccccc",
            bg="#1e1e1e",
            font=("Helvetica", 13),
        ).pack(side=tk.LEFT)

        select_all_btn = tk.Button(
            top, text="Select All", command=self._select_all,
            bg="#333333", fg="#ffffff", relief=tk.FLAT, padx=10,
        )
        select_all_btn.pack(side=tk.RIGHT, padx=(4, 0))

        deselect_btn = tk.Button(
            top, text="Deselect All", command=self._deselect_all,
            bg="#333333", fg="#ffffff", relief=tk.FLAT, padx=10,
        )
        deselect_btn.pack(side=tk.RIGHT, padx=(4, 0))

        # Scrollable canvas
        container = tk.Frame(self.root, bg="#1e1e1e")
        container.pack(fill=tk.BOTH, expand=True, padx=PAD, pady=PAD)

        self.canvas = tk.Canvas(container, bg="#1e1e1e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.inner = tk.Frame(self.canvas, bg="#1e1e1e")
        self.canvas.create_window((0, 0), window=self.inner, anchor=tk.NW)
        self.inner.bind("<Configure>", lambda _: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")
        ))

        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(
            int(-1 * (e.delta / 120)), "units"
        ))
        self.canvas.bind_all("<Button-4>", lambda _: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind_all("<Button-5>", lambda _: self.canvas.yview_scroll(1, "units"))

        # Populate grid cells
        self._check_vars: list[tk.BooleanVar] = []
        self._photo_refs: list[ImageTk.PhotoImage | None] = []  # prevent GC

        for idx, place in enumerate(self.places):
            row, col = divmod(idx, COLS)
            cell = tk.Frame(self.inner, bg="#2a2a2a", padx=4, pady=4)
            cell.grid(row=row, column=col, padx=PAD // 2, pady=PAD // 2, sticky="nsew")

            # Thumbnail
            img = self.images[idx]
            if img is not None:
                thumb = img.copy()
                thumb.thumbnail((THUMB_W, THUMB_H))
                photo = ImageTk.PhotoImage(thumb)
                self._photo_refs.append(photo)
                lbl = tk.Label(cell, image=photo, bg="#2a2a2a")
            else:
                self._photo_refs.append(None)
                lbl = tk.Label(
                    cell, text="No Street View", width=THUMB_W // 8,
                    height=THUMB_H // 16, bg="#444444", fg="#aaaaaa",
                )
            lbl.pack()

            # Name + address
            tk.Label(
                cell,
                text=place["name"],
                fg="#ffffff",
                bg="#2a2a2a",
                font=("Helvetica", 11, "bold"),
                wraplength=THUMB_W,
                justify=tk.LEFT,
            ).pack(anchor=tk.W, pady=(4, 0))

            tk.Label(
                cell,
                text=place["address"],
                fg="#999999",
                bg="#2a2a2a",
                font=("Helvetica", 9),
                wraplength=THUMB_W,
                justify=tk.LEFT,
            ).pack(anchor=tk.W)

            # Checkbox
            var = tk.BooleanVar(value=False)
            self._check_vars.append(var)
            cb = tk.Checkbutton(
                cell, text="Save this place", variable=var,
                bg="#2a2a2a", fg="#ffffff", selectcolor="#444444",
                activebackground="#2a2a2a", activeforeground="#ffffff",
            )
            cb.pack(anchor=tk.W, pady=(2, 0))

        # Confirm button
        btn_frame = tk.Frame(self.root, bg="#1e1e1e")
        btn_frame.pack(fill=tk.X, padx=PAD, pady=PAD)

        tk.Button(
            btn_frame,
            text="Save Selected to Spreadsheet",
            command=self._confirm,
            bg="#2d7d46",
            fg="#ffffff",
            font=("Helvetica", 12, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=8,
        ).pack()

    # ------------------------------------------------------------------ #
    #  Actions
    # ------------------------------------------------------------------ #

    def _select_all(self):
        for var in self._check_vars:
            var.set(True)

    def _deselect_all(self):
        for var in self._check_vars:
            var.set(False)

    def _confirm(self):
        self.selected_indices = [
            i for i, var in enumerate(self._check_vars) if var.get()
        ]
        self.root.destroy()

    def run(self) -> list[int]:
        """Show the window and block until closed. Returns selected indices."""
        self.root.mainloop()
        return self.selected_indices
