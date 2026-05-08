"""
Text Line Changer v2.2
Vereisten: pip install customtkinter==5.2.2 pillow
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time
import os
import json

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".text_line_changer.json")

ACCENT     = "#e94560"
ACCENT_DIM = "#a02f43"
BG         = "#1a1a2e"
SURFACE    = "#0f3460"
SURFACE2   = "#0d1b2a"
GREEN      = "#4ecca3"
MUTED      = "#7a7a9d"
DIM_TEXT   = "#4a4a6a"
WHITE      = "#eaeaea"

FONT_SIZES = {
    "Klein":   {"ui": 11, "label": 10, "list": 11, "editor": 11, "btn": 10},
    "Normaal": {"ui": 13, "label": 11, "list": 13, "editor": 13, "btn": 11},
    "Groot":   {"ui": 15, "label": 13, "list": 15, "editor": 15, "btn": 13},
}


def _set_icon(window):
    """
    Zet het app-icoon en voorkom dat CustomTkinter het overschrijft.
    CustomTkinter slaat zijn eigen icoon over als _iconbitmap_method_called=True.
    """
    ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.ico")
    if not os.path.exists(ico_path):
        return
    try:
        # Zet de vlag VOOR iconbitmap — dan pikt CustomTkinter het op als "al ingesteld"
        window._iconbitmap_method_called = True
        window.iconbitmap(default=ico_path)
    except Exception:
        pass


class Entry:
    def __init__(self, text="Nieuwe tekst", enabled=True):
        self.text    = text
        self.enabled = enabled

    def to_dict(self):
        return {"text": self.text, "enabled": self.enabled}

    @staticmethod
    def from_dict(d):
        return Entry(d.get("text", ""), d.get("enabled", True))


# ── Settings-venster ─────────────────────────────────────────────────────────
class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Instellingen")
        self.resizable(True, False)
        self.minsize(480, 0)
        self.configure(fg_color=BG)
        self.grab_set()
        _set_icon(self)

        fs = parent._fs()

        ctk.CTkLabel(self, text="Instellingen",
                     font=ctk.CTkFont("Segoe UI", fs["ui"], "bold"),
                     text_color=WHITE).pack(anchor="w", padx=16, pady=(14, 10))
        ctk.CTkFrame(self, fg_color=SURFACE, height=1,
                     corner_radius=0).pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(self, text="Uitvoerbestand",
                     font=ctk.CTkFont("Segoe UI", fs["label"]),
                     text_color=MUTED, anchor="w").pack(fill="x", padx=16)
        out_row = ctk.CTkFrame(self, fg_color="transparent")
        out_row.pack(fill="x", padx=16, pady=(2, 12))
        ctk.CTkEntry(out_row, textvariable=parent._output,
                     fg_color=SURFACE2, border_color=SURFACE,
                     text_color=WHITE, font=ctk.CTkFont("Segoe UI", fs["ui"]),
                     height=32, corner_radius=8).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(out_row, text="Bladeren", width=90, height=32,
                      fg_color=SURFACE, hover_color=ACCENT_DIM,
                      text_color=WHITE, font=ctk.CTkFont("Segoe UI", fs["ui"]),
                      corner_radius=8, command=self._browse).pack(side="left", padx=(6, 0))

        ctk.CTkFrame(self, fg_color=SURFACE, height=1,
                     corner_radius=0).pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(self, text="Lettertypegrootte",
                     font=ctk.CTkFont("Segoe UI", fs["label"]),
                     text_color=MUTED, anchor="w").pack(fill="x", padx=16)

        self._font_var = ctk.StringVar(value=parent._font_size)
        ctk.CTkSegmentedButton(self,
                     values=list(FONT_SIZES.keys()),
                     variable=self._font_var,
                     font=ctk.CTkFont("Segoe UI", fs["ui"]),
                     fg_color=SURFACE2,
                     selected_color=ACCENT,
                     selected_hover_color=ACCENT_DIM,
                     unselected_color=SURFACE,
                     unselected_hover_color=SURFACE,
                     text_color=WHITE,
                     command=self._change_font).pack(fill="x", padx=16, pady=(4, 0))

        ctk.CTkLabel(self, text="Wordt direct toegepast.",
                     font=ctk.CTkFont("Segoe UI", fs["label"]),
                     text_color=DIM_TEXT, anchor="w").pack(fill="x", padx=16, pady=(6, 12))

        ctk.CTkFrame(self, fg_color=SURFACE, height=1,
                     corner_radius=0).pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkButton(self, text="Sluiten", width=100, height=32,
                      fg_color=SURFACE, hover_color=ACCENT_DIM,
                      text_color=WHITE, font=ctk.CTkFont("Segoe UI", fs["ui"]),
                      corner_radius=8, command=self._close).pack(anchor="e", padx=16, pady=(0, 14))

    def _browse(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Tekstbestand", "*.txt"), ("Alle bestanden", "*.*")],
            title="Kies uitvoerbestand"
        )
        if path:
            self.parent._output.set(path)
            self.parent._save_config()

    def _change_font(self, choice):
        self.parent._font_size = choice
        self.parent._save_config()
        self.parent._rebuild_ui()

    def _close(self):
        self.parent._save_config()
        self.destroy()


# ── Hoofdvenster ─────────────────────────────────────────────────────────────
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.resizable(True, False)
        self.minsize(400, 0)
        self.configure(fg_color=BG)
        _set_icon(self)

        self._entries       = []
        self._running       = False
        self._thread        = None
        self._current       = -1
        self._sel_idx       = None
        self._font_size     = "Normaal"
        self._settings_win  = None
        self._restore_width = 480

        self._output   = ctk.StringVar(value=os.path.join(
                             os.path.expanduser("~"), "Desktop", "output.txt"))
        self._interval = ctk.StringVar(value="3.0")

        self._load_config()
        self._build_ui()
        self.after(50, self._apply_width)

    def _fs(self):
        return FONT_SIZES[self._font_size]

    def _apply_width(self):
        h = self.winfo_height()
        if h > 1:
            self.geometry(f"{self._restore_width}x{h}")

    # ── UI bouwen ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.title("Text Line Changer v2.2")
        fs = self._fs()

        self._body = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self._body.pack(fill="both", expand=True, padx=14, pady=10)

        # Interval + instellingen-knop
        top_row = ctk.CTkFrame(self._body, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 8))

        iv_col = ctk.CTkFrame(top_row, fg_color="transparent")
        iv_col.pack(side="left")
        ctk.CTkLabel(iv_col, text="Interval (seconden)",
                     font=ctk.CTkFont("Segoe UI", fs["label"]),
                     text_color=MUTED, anchor="w").pack(anchor="w")
        ctk.CTkEntry(iv_col, textvariable=self._interval,
                     fg_color=SURFACE2, border_color=SURFACE,
                     text_color=WHITE, font=ctk.CTkFont("Segoe UI", fs["ui"]),
                     width=80, height=32, corner_radius=8).pack(anchor="w", pady=(2, 0))

        ctk.CTkButton(top_row, text="⚙  Instellingen",
                      width=120, height=32,
                      fg_color=SURFACE, hover_color=ACCENT_DIM,
                      text_color=MUTED, font=ctk.CTkFont("Segoe UI", fs["ui"]),
                      corner_radius=8,
                      command=self._open_settings).pack(side="right", anchor="s")

        ctk.CTkFrame(self._body, fg_color=SURFACE, height=1,
                     corner_radius=0).pack(fill="x", pady=(0, 8))

        # Tekstlijst label
        ctk.CTkLabel(self._body, text="Teksten  —  klik ☑/☐ om in/uit te schakelen",
                     font=ctk.CTkFont("Segoe UI", fs["label"]),
                     text_color=MUTED, anchor="w").pack(fill="x")

        # Lijst: gewone tk.Frame + Canvas + Scrollbar (schalen mee met venstergrootte)
        row_h  = fs["list"] + 14
        list_h = row_h * 7 + 8

        list_wrap = tk.Frame(self._body, bg=SURFACE2, height=list_h)
        list_wrap.pack(fill="x", pady=(4, 8))
        list_wrap.pack_propagate(False)

        vsb = tk.Scrollbar(list_wrap, orient="vertical", bg=SURFACE,
                           troughcolor=SURFACE2, activebackground=ACCENT,
                           relief="flat", bd=0, width=10)
        vsb.pack(side="right", fill="y")

        self._list_canvas = tk.Canvas(list_wrap, bg=SURFACE2,
                                      highlightthickness=0,
                                      yscrollcommand=vsb.set)
        self._list_canvas.pack(side="left", fill="both", expand=True)
        vsb.config(command=self._list_canvas.yview)

        self._list_inner = tk.Frame(self._list_canvas, bg=SURFACE2)
        self._list_win   = self._list_canvas.create_window(
            (0, 0), window=self._list_inner, anchor="nw")

        self._list_inner.bind("<Configure>", lambda e: self._list_canvas.configure(
            scrollregion=self._list_canvas.bbox("all")))
        self._list_canvas.bind("<Configure>", lambda e: self._list_canvas.itemconfig(
            self._list_win, width=e.width))
        self._list_canvas.bind("<MouseWheel>", lambda e: self._list_canvas.yview_scroll(
            -1 * (e.delta // 120), "units"))

        # Editor
        ctk.CTkLabel(self._body,
                     text="Bewerk geselecteerde tekst  (Enter = nieuwe regel in uitvoer)",
                     font=ctk.CTkFont("Segoe UI", fs["label"]),
                     text_color=MUTED, anchor="w").pack(fill="x")
        self._editor = ctk.CTkTextbox(self._body,
                                      fg_color=SURFACE2, border_color=SURFACE,
                                      text_color=WHITE,
                                      font=ctk.CTkFont("Segoe UI", fs["editor"]),
                                      height=160, corner_radius=8,
                                      wrap="word", border_width=1)
        self._editor.pack(fill="x", pady=(4, 8))

        # Knoppen
        btn_row = ctk.CTkFrame(self._body, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 8))

        for txt, cmd, danger in [
            ("+ Toevoegen",   self._add_item,  False),
            ("✎ Opslaan",     self._save_item, False),
            ("✕ Verwijderen", self._del_item,  True),
        ]:
            ctk.CTkButton(btn_row, text=txt, command=cmd, width=96, height=28,
                          fg_color=SURFACE,
                          hover_color=ACCENT_DIM if not danger else "#7a1a1a",
                          text_color=ACCENT if not danger else "#ff6b6b",
                          font=ctk.CTkFont("Segoe UI", fs["btn"]),
                          corner_radius=8).pack(side="left", padx=(0, 5))

        ctk.CTkButton(btn_row, text="↑", command=lambda: self._move(-1),
                      width=30, height=28, fg_color=SURFACE, hover_color=ACCENT_DIM,
                      text_color=WHITE, font=ctk.CTkFont("Segoe UI", fs["ui"]),
                      corner_radius=8).pack(side="left", padx=(0, 4))
        ctk.CTkButton(btn_row, text="↓", command=lambda: self._move(1),
                      width=30, height=28, fg_color=SURFACE, hover_color=ACCENT_DIM,
                      text_color=WHITE, font=ctk.CTkFont("Segoe UI", fs["ui"]),
                      corner_radius=8).pack(side="left")

        # Statusbalk
        ctk.CTkFrame(self._body, fg_color=SURFACE, height=1,
                     corner_radius=0).pack(fill="x", pady=(2, 8))
        status_row = ctk.CTkFrame(self._body, fg_color="transparent")
        status_row.pack(fill="x")

        self._status_lbl = ctk.CTkLabel(status_row, text="⏹  Gestopt",
                                         font=ctk.CTkFont("Segoe UI", fs["ui"]),
                                         text_color=MUTED)
        self._status_lbl.pack(side="left")

        self._progress_lbl = ctk.CTkLabel(status_row, text="",
                                           font=ctk.CTkFont("Segoe UI", fs["ui"], "bold"),
                                           text_color=ACCENT)
        self._progress_lbl.pack(side="left", padx=(10, 0))

        self._start_btn = ctk.CTkButton(status_row, text="▶  START",
                                         command=self._toggle_run,
                                         width=100, height=32,
                                         fg_color=ACCENT, hover_color=ACCENT_DIM,
                                         text_color=WHITE,
                                         font=ctk.CTkFont("Segoe UI", fs["ui"], "bold"),
                                         corner_radius=8)
        self._start_btn.pack(side="right")

        if self._running:
            self._start_btn.configure(text="⏹  STOP",
                                       fg_color="#7a1a1a", hover_color="#5a1010")
            self._status_lbl.configure(text="▶  Actief", text_color=GREEN)

        self._refresh_list()

        if self._sel_idx is not None and self._entries:
            self._editor.delete("1.0", "end")
            self._editor.insert("1.0", self._entries[self._sel_idx].text)

    def _rebuild_ui(self):
        if hasattr(self, "_editor") and self._sel_idx is not None and self._entries:
            self._entries[self._sel_idx].text = self._editor.get("1.0", "end-1c")
        self._body.destroy()
        self._build_ui()

    def _open_settings(self):
        if self._settings_win is None or not self._settings_win.winfo_exists():
            self._settings_win = SettingsWindow(self)
        else:
            self._settings_win.focus()

    # ── Lijst tekenen ─────────────────────────────────────────────────────────
    def _refresh_list(self):
        for w in self._list_inner.winfo_children():
            w.destroy()

        fs    = self._fs()
        row_h = fs["list"] + 14

        for i, entry in enumerate(self._entries):
            is_active = self._running and (i == self._current)
            is_sel    = (i == self._sel_idx)

            row_bg = ACCENT if is_active else (SURFACE if is_sel else SURFACE2)

            row = tk.Frame(self._list_inner, bg=row_bg, height=row_h)
            row.pack(fill="x", pady=(0, 1))
            row.pack_propagate(False)

            # Checkbox
            cb_char  = "☑" if entry.enabled else "☐"
            cb_color = GREEN if (entry.enabled and not is_active) else (WHITE if is_active else MUTED)
            cb = tk.Label(row, text=cb_char, bg=row_bg, fg=cb_color,
                          font=("Segoe UI", fs["btn"]), cursor="hand2", padx=6)
            cb.pack(side="left")
            cb.bind("<Button-1>", lambda e, idx=i: self._toggle_enabled(idx))

            # Nummer
            num_fg = WHITE if (is_active or is_sel) else MUTED
            tk.Label(row, text=f"{i+1}.", bg=row_bg, fg=num_fg,
                     font=("Segoe UI", fs["btn"]), width=3,
                     anchor="e").pack(side="left")

            # Preview
            prev_fg = WHITE if (is_active or is_sel) else (DIM_TEXT if not entry.enabled else WHITE)
            preview = entry.text.replace("\n", "↵ ")[:64]
            lbl = tk.Label(row, text=preview, bg=row_bg, fg=prev_fg,
                           font=("Segoe UI", fs["btn"]), anchor="w")
            lbl.pack(side="left", fill="x", expand=True, padx=(4, 6))

            for widget in (row, lbl):
                widget.bind("<Button-1>", lambda e, idx=i: self._select_row(idx))
            # Muiswiel ook op rijen
            for widget in (row, cb, lbl):
                widget.bind("<MouseWheel>", lambda e: self._list_canvas.yview_scroll(
                    -1 * (e.delta // 120), "units"))

    # ── Selectie & toggle ─────────────────────────────────────────────────────
    def _select_row(self, idx):
        self._sel_idx = idx
        self._editor.delete("1.0", "end")
        self._editor.insert("1.0", self._entries[idx].text)
        self._refresh_list()

    def _toggle_enabled(self, idx):
        self._entries[idx].enabled = not self._entries[idx].enabled
        self._refresh_list()

    # ── Itembeheer ────────────────────────────────────────────────────────────
    def _add_item(self):
        basis = self._editor.get("1.0", "end-1c").strip() or "Nieuwe tekst"
        self._entries.append(Entry(basis))
        self._sel_idx = len(self._entries) - 1
        self._editor.delete("1.0", "end")
        self._editor.insert("1.0", self._entries[self._sel_idx].text)
        self._refresh_list()
        self._save_config()

    def _save_item(self):
        if self._sel_idx is None or self._sel_idx >= len(self._entries):
            messagebox.showinfo("Geen item geselecteerd",
                                "Klik eerst op een item in de lijst.")
            return
        self._entries[self._sel_idx].text = self._editor.get("1.0", "end-1c")
        self._refresh_list()
        self._save_config()

    def _del_item(self):
        if self._sel_idx is None or not self._entries:
            return
        self._entries.pop(self._sel_idx)
        if self._entries:
            self._sel_idx = min(self._sel_idx, len(self._entries) - 1)
            self._editor.delete("1.0", "end")
            self._editor.insert("1.0", self._entries[self._sel_idx].text)
        else:
            self._sel_idx = None
            self._editor.delete("1.0", "end")
        self._refresh_list()
        self._save_config()

    def _move(self, direction):
        if self._sel_idx is None:
            return
        new = self._sel_idx + direction
        if 0 <= new < len(self._entries):
            self._entries[self._sel_idx], self._entries[new] = \
                self._entries[new], self._entries[self._sel_idx]
            self._sel_idx = new
            self._refresh_list()
            self._save_config()

    # ── Config ────────────────────────────────────────────────────────────────
    def _save_config(self):
        data = {
            "output":    self._output.get(),
            "interval":  self._interval.get(),
            "font_size": self._font_size,
            "width":     self.winfo_width(),
            "entries":   [e.to_dict() for e in self._entries],
            "sel_idx":   self._sel_idx,
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return

        self._output.set(data.get("output", self._output.get()))
        self._interval.set(str(data.get("interval", "3.0")))

        font = data.get("font_size", "Normaal")
        self._font_size = font if font in FONT_SIZES else "Normaal"

        try:
            self._restore_width = max(400, int(data.get("width", 480)))
        except (TypeError, ValueError):
            self._restore_width = 480

        try:
            self._entries = [Entry.from_dict(e) for e in data.get("entries", [])]
        except Exception:
            self._entries = []

        try:
            sel = data.get("sel_idx")
            if sel is not None and self._entries:
                self._sel_idx = min(int(sel), len(self._entries) - 1)
        except (TypeError, ValueError):
            self._sel_idx = None

    # ── Start / stop ──────────────────────────────────────────────────────────
    def _toggle_run(self):
        self._stop() if self._running else self._start()

    def _start(self):
        if not any(e.enabled for e in self._entries):
            messagebox.showwarning("Geen teksten", "Schakel minimaal één tekst in.")
            return
        self._save_config()
        self._running = True
        self._current = -1
        self._start_btn.configure(text="⏹  STOP",
                                   fg_color="#7a1a1a", hover_color="#5a1010")
        self._status_lbl.configure(text="▶  Actief", text_color=GREEN)
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _stop(self):
        self._running = False
        self._current = -1
        self._start_btn.configure(text="▶  START",
                                   fg_color=ACCENT, hover_color=ACCENT_DIM)
        self._status_lbl.configure(text="⏹  Gestopt", text_color=MUTED)
        self._progress_lbl.configure(text="")
        self.after(0, self._refresh_list)

    def _run_loop(self):
        loop_idx = 0
        while self._running:
            try:
                interval = float(self._interval.get())
            except ValueError:
                interval = 3.0

            enabled_indices = [i for i, e in enumerate(self._entries) if e.enabled]
            if not enabled_indices:
                time.sleep(0.2)
                continue

            loop_idx = loop_idx % len(enabled_indices)
            real_idx = enabled_indices[loop_idx]
            tekst    = self._entries[real_idx].text
            path     = self._output.get()

            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(tekst)
            except Exception as ex:
                self.after(0, lambda ex=ex: messagebox.showerror(
                    "Schrijffout", f"Kan bestand niet schrijven:\n{ex}"))
                self.after(0, self._stop)
                return

            self._current = real_idx
            pos   = loop_idx + 1
            total = len(enabled_indices)
            self.after(0, self._refresh_list)
            self.after(0, lambda p=pos, t=total:
                       self._progress_lbl.configure(text=f"[{p}/{t}]"))

            loop_idx += 1
            if loop_idx >= len(enabled_indices):
                loop_idx = 0

            deadline = time.time() + interval
            while self._running and time.time() < deadline:
                time.sleep(0.05)

    def destroy(self):
        try:
            self._save_config()
        except Exception:
            pass
        super().destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
