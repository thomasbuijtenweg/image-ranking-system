"""Export Preview Window for the Image Ranking System.

Shows a two-panel window before an Export Top N operation:
  Left  — scrollable grid of small thumbnails with ✓/✗ badges.
           Click to toggle inclusion.  Default: all included.
  Right — large preview of the currently hovered thumbnail.

Calls on_confirm(selected_images: list[str]) when the user
clicks Export, or nothing when they cancel.
"""

import os
import tkinter as tk
from tkinter import ttk
from typing import List, Tuple, Optional, Callable

from PIL import Image, ImageTk

from config import Colors

# ── thumbnail grid constants ──────────────────────────────────────────────────
THUMB_SIZE   = 110          # pixels, square
THUMB_PAD    = 6            # gap between thumbnails
COLS         = 3            # thumbnails per row
BADGE_R      = 13           # badge circle radius
BADGE_OFFSET = 6            # inset from corner

# ── badge colours ─────────────────────────────────────────────────────────────
BADGE_IN_FILL   = '#2ecc71'   # green  – included
BADGE_IN_TEXT   = '#ffffff'
BADGE_OUT_FILL  = '#e74c3c'   # red    – excluded
BADGE_OUT_TEXT  = '#ffffff'
BADGE_FONT      = ('Arial', 10, 'bold')


class ExportPreviewWindow:
    """Interactive preview window shown before exporting top-N images."""

    def __init__(
        self,
        parent: tk.Tk,
        image_folder: str,
        image_list: List[Tuple[str, int, int, int]],   # (name, tier, votes, wins)
        on_confirm: Callable[[List[str]], None],
    ):
        self.parent        = parent
        self.image_folder  = image_folder
        self.on_confirm    = on_confirm

        # State ─────────────────────────────────────────────────────────────
        self.names: List[str] = [row[0] for row in image_list]
        self.stats: dict      = {row[0]: row[1:] for row in image_list}  # name→(tier,votes,wins)
        self.included: dict   = {name: True for name in self.names}      # default all-in

        # Image caches (keep refs to prevent GC) ────────────────────────────
        self._thumb_photos: dict  = {}   # name → PhotoImage (thumb)
        self._large_photos: dict  = {}   # name → PhotoImage (large preview)
        self._raw_images:   dict  = {}   # name → PIL Image (for large resize)

        # Canvas refs per thumbnail ─────────────────────────────────────────
        self._canvases:     dict  = {}   # name → tk.Canvas
        self._badge_ids:    dict  = {}   # name → canvas item id of badge oval

        # Currently previewed image ─────────────────────────────────────────
        self._previewed: Optional[str] = None

        self._build_window()
        self._load_all_thumbnails()
        self._populate_grid()
        if self.names:
            self._show_large_preview(self.names[0])
        self._update_count_label()


    # ── Window construction ───────────────────────────────────────────────────

    def _build_window(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title(f"Export Preview  —  {len(self.names)} images")
        self.window.geometry("1100x720")
        self.window.configure(bg=Colors.BG_PRIMARY)
        self.window.grab_set()
        self.window.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # ── outer layout: left panel | right panel ────────────────────────
        pane = tk.PanedWindow(self.window, orient=tk.HORIZONTAL,
                              bg=Colors.BG_PRIMARY, sashwidth=6,
                              sashrelief=tk.FLAT)
        pane.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        left_outer = tk.Frame(pane, bg=Colors.BG_PRIMARY, width=390)
        right_outer = tk.Frame(pane, bg=Colors.BG_PRIMARY)
        pane.add(left_outer,  minsize=280, stretch='never')
        pane.add(right_outer, minsize=400, stretch='always')

        self._build_left_panel(left_outer)
        self._build_right_panel(right_outer)
        self._build_bottom_bar()

    def _build_left_panel(self, parent: tk.Frame):
        """Scrollable canvas that will hold the thumbnail grid."""
        tk.Label(parent, text="Click image to include / exclude",
                 font=('Arial', 9, 'italic'), fg=Colors.TEXT_SECONDARY,
                 bg=Colors.BG_PRIMARY).pack(side=tk.TOP, pady=(6, 2))

        scroll_frame = tk.Frame(parent, bg=Colors.BG_PRIMARY)
        scroll_frame.pack(fill=tk.BOTH, expand=True)

        self._scroll_canvas = tk.Canvas(scroll_frame, bg=Colors.BG_SECONDARY,
                                        highlightthickness=0)
        vbar = ttk.Scrollbar(scroll_frame, orient=tk.VERTICAL,
                              command=self._scroll_canvas.yview)
        self._scroll_canvas.configure(yscrollcommand=vbar.set)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._grid_frame = tk.Frame(self._scroll_canvas, bg=Colors.BG_SECONDARY)
        self._grid_window = self._scroll_canvas.create_window(
            (0, 0), window=self._grid_frame, anchor='nw')

        self._grid_frame.bind('<Configure>', self._on_grid_resize)
        self._scroll_canvas.bind('<Configure>', self._on_canvas_resize)

        # Mouse-wheel scrolling
        self._scroll_canvas.bind('<MouseWheel>',
                                 lambda e: self._scroll_canvas.yview_scroll(
                                     int(-1 * (e.delta / 120)), 'units'))


    def _build_right_panel(self, parent: tk.Frame):
        """Large preview area for the hovered image."""
        self._preview_label = tk.Label(
            parent, bg=Colors.BG_TERTIARY, text="Hover over an image",
            fg=Colors.TEXT_SECONDARY, font=('Arial', 13))
        self._preview_label.pack(fill=tk.BOTH, expand=True, padx=8, pady=(8, 4))

        self._preview_info = tk.Label(
            parent, text="", font=('Arial', 10),
            fg=Colors.TEXT_SECONDARY, bg=Colors.BG_PRIMARY,
            justify=tk.CENTER)
        self._preview_info.pack(side=tk.BOTTOM, pady=(2, 6))

        # Bind resize so the large preview scales with the panel
        self._preview_label.bind('<Configure>', self._on_preview_resize)

    def _build_bottom_bar(self):
        """Count label + Export / Cancel buttons across the full window bottom."""
        bar = tk.Frame(self.window, bg=Colors.BG_SECONDARY, pady=8)
        bar.pack(side=tk.BOTTOM, fill=tk.X)

        self._count_label = tk.Label(
            bar, text="", font=('Arial', 11, 'bold'),
            fg=Colors.TEXT_PRIMARY, bg=Colors.BG_SECONDARY)
        self._count_label.pack(side=tk.LEFT, padx=20)

        tk.Button(bar, text="Cancel", command=self._on_cancel,
                  bg=Colors.BUTTON_NEUTRAL, fg='white',
                  relief=tk.FLAT, font=('Arial', 11), width=10).pack(
            side=tk.RIGHT, padx=10)

        tk.Button(bar, text="Export Selected", command=self._on_export,
                  bg=Colors.BUTTON_SECONDARY, fg='white',
                  relief=tk.FLAT, font=('Arial', 11), width=16).pack(
            side=tk.RIGHT, padx=6)

    # ── Scrollable canvas helpers ─────────────────────────────────────────────

    def _on_grid_resize(self, _event):
        self._scroll_canvas.configure(
            scrollregion=self._scroll_canvas.bbox('all'))

    def _on_canvas_resize(self, event):
        self._scroll_canvas.itemconfig(
            self._grid_window, width=event.width)


    # ── Image loading ─────────────────────────────────────────────────────────

    def _load_all_thumbnails(self):
        """Load and cache all thumbnail images.  Done once at open time."""
        for name in self.names:
            path = os.path.join(self.image_folder, name)
            try:
                with Image.open(path) as img:
                    img.thumbnail((THUMB_SIZE, THUMB_SIZE), Image.Resampling.LANCZOS)
                    self._thumb_photos[name] = ImageTk.PhotoImage(img)
                    # Keep a raw copy for the large preview
                    raw = img.copy()
                self._raw_images[name] = raw
            except Exception as e:
                print(f"[ExportPreview] Could not load {name}: {e}")
                self._thumb_photos[name] = None
                self._raw_images[name]   = None

    def _make_large_photo(self, name: str,
                          max_w: int, max_h: int) -> Optional[ImageTk.PhotoImage]:
        """Resize raw image to fit (max_w, max_h) and return a PhotoImage."""
        raw = self._raw_images.get(name)
        if raw is None:
            return None
        # Re-open at full size for quality
        path = os.path.join(self.image_folder, name)
        try:
            with Image.open(path) as img:
                img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
            return photo
        except Exception:
            return None

    # ── Thumbnail grid ────────────────────────────────────────────────────────

    def _populate_grid(self):
        """Create one Canvas widget per image, arranged in a COLS-wide grid."""
        for idx, name in enumerate(self.names):
            row, col = divmod(idx, COLS)
            c = tk.Canvas(self._grid_frame,
                          width=THUMB_SIZE, height=THUMB_SIZE,
                          bg=Colors.BG_SECONDARY, highlightthickness=2,
                          highlightbackground=Colors.BORDER)
            c.grid(row=row, column=col,
                   padx=THUMB_PAD, pady=THUMB_PAD, sticky='nw')
            self._canvases[name] = c

            photo = self._thumb_photos.get(name)
            if photo:
                # Centre image on canvas
                c.create_image(THUMB_SIZE // 2, THUMB_SIZE // 2,
                               image=photo, anchor='center', tags='img')
            else:
                c.create_text(THUMB_SIZE // 2, THUMB_SIZE // 2,
                              text='?', fill=Colors.TEXT_SECONDARY, tags='img')

            # Draw badge (✓ or ✗) – stored so we can redraw on toggle
            self._draw_badge(name)

            # Bind events
            c.bind('<Button-1>', lambda e, n=name: self._toggle(n))
            c.bind('<Enter>',    lambda e, n=name: self._on_hover_enter(n))
            c.bind('<Leave>',    lambda e, n=name: self._on_hover_leave(n))


    # ── Badge drawing ─────────────────────────────────────────────────────────

    def _draw_badge(self, name: str):
        """Draw (or redraw) the ✓/✗ badge on the thumbnail canvas."""
        c = self._canvases.get(name)
        if c is None:
            return

        # Remove old badge items
        c.delete('badge')

        included = self.included[name]
        fill  = BADGE_IN_FILL  if included else BADGE_OUT_FILL
        glyph = '✓'            if included else '✗'

        # Position: bottom-right corner inset by BADGE_OFFSET
        x1 = THUMB_SIZE - BADGE_OFFSET - BADGE_R * 2
        y1 = THUMB_SIZE - BADGE_OFFSET - BADGE_R * 2
        x2 = THUMB_SIZE - BADGE_OFFSET
        y2 = THUMB_SIZE - BADGE_OFFSET

        # Shadow / outline circle for contrast
        c.create_oval(x1 - 1, y1 - 1, x2 + 1, y2 + 1,
                      fill='#000000', outline='', tags='badge')
        c.create_oval(x1, y1, x2, y2,
                      fill=fill, outline='', tags='badge')
        c.create_text((x1 + x2) // 2, (y1 + y2) // 2,
                      text=glyph, fill='white',
                      font=BADGE_FONT, tags='badge')

    # ── Interaction ───────────────────────────────────────────────────────────

    def _toggle(self, name: str):
        """Toggle included/excluded state and refresh badge + border."""
        self.included[name] = not self.included[name]
        self._draw_badge(name)
        # Highlight border: green if in, dim if out
        c = self._canvases[name]
        if self.included[name]:
            c.configure(highlightbackground=BADGE_IN_FILL, highlightthickness=2)
        else:
            c.configure(highlightbackground=BADGE_OUT_FILL, highlightthickness=2)
        self._update_count_label()

    def _on_hover_enter(self, name: str):
        """Show large preview on right panel when hovering over a thumbnail."""
        self._show_large_preview(name)
        c = self._canvases.get(name)
        if c:
            c.configure(highlightthickness=3)

    def _on_hover_leave(self, name: str):
        c = self._canvases.get(name)
        if c:
            c.configure(highlightthickness=2)

    # ── Large preview ─────────────────────────────────────────────────────────

    def _show_large_preview(self, name: str):
        """Render the image at maximum size in the right panel."""
        self._previewed = name
        self._refresh_large_preview()

    def _refresh_large_preview(self):
        """(Re)render the large preview at the current panel dimensions."""
        name = self._previewed
        if name is None:
            return
        label = self._preview_label
        w = label.winfo_width()  or 500
        h = label.winfo_height() or 500
        pad = 16
        max_w, max_h = max(w - pad, 100), max(h - pad, 100)

        photo = self._make_large_photo(name, max_w, max_h)
        if photo:
            label.configure(image=photo, text='')
            self._large_photos[name] = photo   # keep ref
        else:
            label.configure(image='', text='Could not load image')

        # Info text below large preview
        tier, votes, wins = self.stats.get(name, (0, 0, 0))
        loss = votes - wins
        wr   = f"{wins/votes*100:.0f}%" if votes else "—"
        self._preview_info.configure(
            text=f"{name}\n"
                 f"Tier {tier:+d}  |  {votes} votes  |  {wins}W / {loss}L  |  Win rate {wr}")

    def _on_preview_resize(self, _event):
        """Re-render large preview if the panel is resized."""
        if self._previewed:
            self.window.after(80, self._refresh_large_preview)


    # ── Bottom bar helpers ────────────────────────────────────────────────────

    def _update_count_label(self):
        total    = len(self.names)
        selected = sum(1 for v in self.included.values() if v)
        excluded = total - selected
        self._count_label.configure(
            text=f"{selected} of {total} selected for export  "
                 f"({excluded} excluded)")

    # ── Confirm / cancel ──────────────────────────────────────────────────────

    def _on_export(self):
        selected = [n for n in self.names if self.included[n]]
        if not selected:
            import tkinter.messagebox as mb
            mb.showwarning("Nothing selected",
                           "All images are excluded — nothing to export.",
                           parent=self.window)
            return
        self.window.destroy()
        self.on_confirm(selected)

    def _on_cancel(self):
        self.window.destroy()
