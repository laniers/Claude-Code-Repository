#!/usr/bin/env python3
"""One-click GUI launcher. No terminal needed.

Double-click run.bat (Windows) or run.sh (Mac/Linux) to start.
Shows a simple window where you type your search query, then
handles everything from there.
"""

import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, filedialog
from pathlib import Path


def install_dependencies():
    """Install pip requirements if needed."""
    req_file = Path(__file__).parent.parent / "requirements.txt"
    if req_file.exists():
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-q", "-r", str(req_file)],
            stdout=subprocess.DEVNULL,
        )


def launch():
    # -- Start screen: ask for search query --
    root = tk.Tk()
    root.title("Street View Scraper")
    root.configure(bg="#1e1e1e")
    root.resizable(False, False)

    # Center the window
    w, h = 520, 300
    sx = root.winfo_screenwidth() // 2 - w // 2
    sy = root.winfo_screenheight() // 2 - h // 2
    root.geometry(f"{w}x{h}+{sx}+{sy}")

    tk.Label(
        root,
        text="Street View Scraper",
        fg="#ffffff",
        bg="#1e1e1e",
        font=("Helvetica", 20, "bold"),
    ).pack(pady=(30, 5))

    tk.Label(
        root,
        text="Search for places, pick from Street View images,\nand save locations to a spreadsheet.",
        fg="#999999",
        bg="#1e1e1e",
        font=("Helvetica", 11),
    ).pack(pady=(0, 20))

    tk.Label(
        root,
        text="What are you looking for?",
        fg="#cccccc",
        bg="#1e1e1e",
        font=("Helvetica", 12),
    ).pack()

    query_var = tk.StringVar()
    entry = tk.Entry(
        root,
        textvariable=query_var,
        font=("Helvetica", 14),
        width=40,
        bg="#2a2a2a",
        fg="#ffffff",
        insertbackground="#ffffff",
        relief=tk.FLAT,
    )
    entry.pack(pady=10, ipady=6)
    entry.focus_set()

    tk.Label(
        root,
        text='Example: "coffee shops in downtown Austin"',
        fg="#666666",
        bg="#1e1e1e",
        font=("Helvetica", 9),
    ).pack()

    result = {}

    def on_search(event=None):
        q = query_var.get().strip()
        if not q:
            messagebox.showwarning("Empty query", "Please enter a search query.")
            return
        result["query"] = q
        root.destroy()

    entry.bind("<Return>", on_search)

    tk.Button(
        root,
        text="Search",
        command=on_search,
        bg="#2d7d46",
        fg="#ffffff",
        font=("Helvetica", 13, "bold"),
        relief=tk.FLAT,
        padx=30,
        pady=6,
        cursor="hand2",
    ).pack(pady=(10, 0))

    root.mainloop()

    if "query" not in result:
        return

    query = result["query"]

    # -- Run the scraper --
    from .api import search_places, fetch_street_view_image, quit_driver
    from .grid_ui import GridSelector
    from .export import save_to_spreadsheet

    # Progress window
    progress_root = tk.Tk()
    progress_root.title("Searching...")
    progress_root.configure(bg="#1e1e1e")
    progress_root.resizable(False, False)
    pw, ph = 420, 120
    px = progress_root.winfo_screenwidth() // 2 - pw // 2
    py = progress_root.winfo_screenheight() // 2 - ph // 2
    progress_root.geometry(f"{pw}x{ph}+{px}+{py}")

    status_label = tk.Label(
        progress_root,
        text=f'Searching for "{query}"...',
        fg="#cccccc",
        bg="#1e1e1e",
        font=("Helvetica", 12),
    )
    status_label.pack(pady=(25, 5))

    detail_label = tk.Label(
        progress_root,
        text="Starting Chrome browser — this may take a minute",
        fg="#666666",
        bg="#1e1e1e",
        font=("Helvetica", 10),
    )
    detail_label.pack()

    progress_root.update()

    try:
        # 1. Search
        places = search_places(query)
        if not places:
            progress_root.destroy()
            messagebox.showinfo("No results", f'No places found for "{query}".')
            return

        # 2. Capture Street View images
        status_label.config(text=f"Found {len(places)} places. Capturing images...")
        progress_root.update()

        images = []
        for i, place in enumerate(places):
            detail_label.config(text=f"[{i+1}/{len(places)}] {place['name']}")
            progress_root.update()
            img = fetch_street_view_image(place["lat"], place["lng"])
            images.append(img)

        progress_root.destroy()

        # 3. Grid selection
        selector = GridSelector(places, images)
        selected = selector.run()

        if not selected:
            messagebox.showinfo("Nothing selected", "No places were selected.")
            return

        # 4. Ask where to save
        output_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            title="Save spreadsheet as...",
            initialfile=f"{query[:30].replace(' ', '_')}.xlsx",
        )

        if not output_path:
            return

        selected_places = [places[i] for i in selected]
        save_to_spreadsheet(selected_places, query, output_path)

        messagebox.showinfo(
            "Saved!",
            f"Saved {len(selected_places)} place(s) to:\n{output_path}"
        )

    except Exception as e:
        try:
            progress_root.destroy()
        except Exception:
            pass
        messagebox.showerror("Error", str(e))

    finally:
        quit_driver()


if __name__ == "__main__":
    launch()
