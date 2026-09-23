# =============================================================
# ui.py — Graphical User Interface
# Wi-Fi Usage Analyzer
# =============================================================
# Builds the full Tkinter application window.
#
# Rules:
#   - No Pandas analysis logic here (all in analysis.py).
#   - All analysis functions are called via analysis.py.
#   - UI reads results and displays them only.
#
# Architecture:
#   main.py → ui.py → analysis.py → utils.py / config.py
# =============================================================

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
import subprocess
import platform
import os
import sys

# Ensure the src/ directory is on the path
sys.path.insert(0, os.path.dirname(__file__))

import analysis as an
from utils import (
    check_columns, has_column,
    format_bytes, format_number,
    get_filename, get_file_size_kb,
)
from config import (
    COLOR_SIDEBAR_BG, COLOR_SIDEBAR_BTN,
    COLOR_SIDEBAR_HOVER, COLOR_SIDEBAR_ACTIVE,
    COLOR_PAGE_BG, COLOR_CARD_BG, COLOR_CARD_BORDER,
    COLOR_CARD_INNER, COLOR_INPUT_BG, COLOR_INPUT_BORDER,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED,
    COLOR_TEXT_SUCCESS, COLOR_TEXT_WARNING, COLOR_TEXT_DANGER,
    COLOR_STATUS_NORMAL, COLOR_STATUS_WARNING, COLOR_STATUS_OVERLOAD,
    COLOR_ACCENT_PRIMARY, COLOR_ACCENT_HOVER, COLOR_ACCENT_BLUE, COLOR_ACCENT_GREEN,
    COLOR_ACCENT_ORANGE, COLOR_ACCENT_PURPLE,
    FONT_FAMILY, FONT_HEADING, FONT_SUBHEAD, FONT_BODY, FONT_SMALL,
    FONT_CARD_VAL, FONT_CARD_LBL,
    CHART_FIG_WIDE, CHART_DPI,
    APP_TITLE, APP_VERSION, APP_AUTHOR,
    USER_SETTINGS_FILE,
    DEFAULT_ALERT_HIGH_UPLOAD_MB, DEFAULT_ALERT_MAX_DEVICES_PER_USER,
    DEFAULT_ALERT_BLOCKED_ATTEMPTS, DEFAULT_ALERT_AP_MAX_USERS,
    ALERT_HIGH_UPLOAD_MB, ALERT_MAX_DEVICES_PER_USER,
    ALERT_BLOCKED_ATTEMPTS, ALERT_AP_MAX_USERS,
    COL_USERNAME, COL_ACCESS_POINT, COL_WEBSITE, COL_WEBSITE_CATEGORY, COL_STATUS,
)


# =============================================================
# Global ttk Style
# =============================================================

def _apply_styles():
    """Configure modern dark Treeview and Scrollbar styles once at startup."""

    style = ttk.Style()
    style.theme_use("clam")

    style.configure(
        "Treeview",
        background=COLOR_CARD_BG,
        foreground=COLOR_TEXT_PRIMARY,
        rowheight=30,
        fieldbackground=COLOR_CARD_BG,
        font=(FONT_FAMILY, 10),
        borderwidth=0,
    )
    style.configure(
        "Treeview.Heading",
        background=COLOR_SIDEBAR_BG,
        foreground=COLOR_ACCENT_BLUE,
        font=(FONT_FAMILY, 10, "bold"),
        relief="flat",
        borderwidth=0,
        padding=4,
    )
    style.map(
        "Treeview",
        background=[("selected", COLOR_ACCENT_PRIMARY)],
        foreground=[("selected", "#FFFFFF")],
    )
    style.map(
        "Treeview.Heading",
        background=[("active", COLOR_SIDEBAR_HOVER)],
        foreground=[("active", "#FFFFFF")],
    )


# =============================================================
# Main Application Class
# =============================================================

class WiFiUsageAnalyzer(tk.Tk):
    """
    Root Tkinter window for the Wi-Fi Usage Analyzer.

    Responsibilities:
        - Build and manage the sidebar + scrollable content area.
        - Handle CSV/Excel file upload and column validation.
        - Render each page by calling analysis.py functions and
          displaying the results in tables and charts.
    """

    def __init__(self):
        super().__init__()

        # ── Application State ──────────────────────────────────
        self.data       = None    # Loaded pandas DataFrame
        self.file_path  = None    # Path to the loaded file
        self.compat     = {}      # Column compatibility report

        # Sidebar button references for active-state highlighting
        self.nav_buttons  = {}
        self.active_page  = "Dashboard"

        # Open Matplotlib figures (closed when navigating away)
        self.open_figures = []

        # ── Window Setup ───────────────────────────────────────
        self.title(APP_TITLE)
        self.geometry("1280x800")
        self.minsize(1050, 650)
        self.configure(bg=COLOR_PAGE_BG)

        _apply_styles()

        # ── Build UI ───────────────────────────────────────────
        self._create_sidebar()
        self._create_scrollable_content()

        # ── Threshold State & Customization ────────────────────
        self.thresholds = {
            "high_upload_mb": DEFAULT_ALERT_HIGH_UPLOAD_MB,
            "max_devices_user": DEFAULT_ALERT_MAX_DEVICES_PER_USER,
            "blocked_attempts": DEFAULT_ALERT_BLOCKED_ATTEMPTS,
            "default_ap_capacity": DEFAULT_ALERT_AP_MAX_USERS,
            "ap_capacities": {},
        }
        self._load_user_settings()

        # Map page names → show methods (used after file upload)
        self.page_methods = {
            "Dashboard":     self.show_dashboard,
            "Users":         self.show_users,
            "Access Points": self.show_access_points,
            "Websites":      self.show_websites,
            "Alerts":        self.show_alerts,
            "Reports":       self.show_reports,
            "Settings":      self.show_settings,
        }

        # Start on Dashboard
        self._navigate("Dashboard", self.show_dashboard)

    # ==========================================================
    # SETTINGS & THRESHOLD PERSISTENCE
    # ==========================================================

    def _get_settings_file_path(self) -> str:
        """Return the absolute path to user_settings.json in the project root."""
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            USER_SETTINGS_FILE
        )

    def _load_user_settings(self):
        """Load user threshold preferences from json file if available."""
        path = self._get_settings_file_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.thresholds["high_upload_mb"] = float(
                            data.get("high_upload_mb", DEFAULT_ALERT_HIGH_UPLOAD_MB)
                        )
                        self.thresholds["max_devices_user"] = int(
                            data.get("max_devices_user", DEFAULT_ALERT_MAX_DEVICES_PER_USER)
                        )
                        self.thresholds["blocked_attempts"] = int(
                            data.get("blocked_attempts", DEFAULT_ALERT_BLOCKED_ATTEMPTS)
                        )
                        self.thresholds["default_ap_capacity"] = int(
                            data.get("default_ap_capacity", DEFAULT_ALERT_AP_MAX_USERS)
                        )
                        caps = data.get("ap_capacities", {})
                        if isinstance(caps, dict):
                            self.thresholds["ap_capacities"] = {
                                str(k): int(v) for k, v in caps.items() if str(v).isdigit() or isinstance(v, (int, float))
                            }
            except Exception as e:
                print(f"Warning: Failed to load user settings: {e}")

    def _save_user_settings(self):
        """Persist current threshold preferences to json file."""
        path = self._get_settings_file_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.thresholds, f, indent=4)
        except Exception as e:
            print(f"Warning: Failed to save user settings: {e}")

    def _reset_user_settings(self):
        """Reset threshold preferences back to baseline defaults."""
        self.thresholds = {
            "high_upload_mb": DEFAULT_ALERT_HIGH_UPLOAD_MB,
            "max_devices_user": DEFAULT_ALERT_MAX_DEVICES_PER_USER,
            "blocked_attempts": DEFAULT_ALERT_BLOCKED_ATTEMPTS,
            "default_ap_capacity": DEFAULT_ALERT_AP_MAX_USERS,
            "ap_capacities": {},
        }
        self._save_user_settings()

    def _open_per_ap_modal(self):
        """Open a modal dialog allowing users to set custom capacities per Access Point."""
        if self.data is None or not has_column(self.data, COL_ACCESS_POINT):
            messagebox.showinfo(
                "No Access Point Data",
                "Please load a dataset containing the 'Access_Point' column first."
            )
            return

        aps = sorted(self.data[COL_ACCESS_POINT].dropna().unique().tolist())
        if not aps:
            messagebox.showinfo("No APs Found", "No access points found in the loaded dataset.")
            return

        modal = tk.Toplevel(self)
        modal.title("Configure Per-Access Point Device Capacities")
        modal.geometry("560x540")
        modal.minsize(500, 420)
        modal.configure(bg=COLOR_PAGE_BG)
        modal.transient(self)
        modal.grab_set()

        # Center relative to parent
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - 280
        y = self.winfo_y() + (self.winfo_height() // 2) - 270
        modal.geometry(f"+{max(0, x)}+{max(0, y)}")

        # Header
        hdr = tk.Frame(modal, bg=COLOR_SIDEBAR_BG, padx=20, pady=16)
        hdr.pack(fill="x")
        tk.Label(
            hdr, text="⚙️  Access Point Capacity Configuration",
            bg=COLOR_SIDEBAR_BG, fg=COLOR_TEXT_PRIMARY, font=FONT_SUBHEAD
        ).pack(anchor="w")
        def_cap = int(self.thresholds.get("default_ap_capacity", DEFAULT_ALERT_AP_MAX_USERS))
        tk.Label(
            hdr,
            text=f"Set maximum simultaneous devices for each AP. Default global capacity: {def_cap} devices.",
            bg=COLOR_SIDEBAR_BG, fg=COLOR_TEXT_SECONDARY, font=FONT_SMALL
        ).pack(anchor="w", pady=(3, 0))

        # Scrollable container for AP list
        container = tk.Frame(modal, bg=COLOR_PAGE_BG)
        container.pack(fill="both", expand=True, padx=20, pady=12)

        canvas = tk.Canvas(
            container, bg=COLOR_CARD_BG, highlightthickness=1,
            highlightbackground=COLOR_CARD_BORDER
        )
        vsb = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=COLOR_CARD_BG)

        canvas_win = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

        def _on_canvas_configure(e):
            canvas.itemconfig(canvas_win, width=e.width)

        canvas.bind("<Configure>", _on_canvas_configure)
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.configure(yscrollcommand=vsb.set)

        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Column headers
        th_row = tk.Frame(scroll_frame, bg=COLOR_SIDEBAR_BTN, padx=14, pady=8)
        th_row.pack(fill="x")
        tk.Label(th_row, text="Access Point", bg=COLOR_SIDEBAR_BTN, fg=COLOR_ACCENT_BLUE, font=(FONT_FAMILY, 9, "bold"), width=22, anchor="w").pack(side="left")
        tk.Label(th_row, text="Max Devices", bg=COLOR_SIDEBAR_BTN, fg=COLOR_ACCENT_BLUE, font=(FONT_FAMILY, 9, "bold"), width=14, anchor="w").pack(side="left")
        tk.Label(th_row, text="Status", bg=COLOR_SIDEBAR_BTN, fg=COLOR_ACCENT_BLUE, font=(FONT_FAMILY, 9, "bold"), anchor="w").pack(side="left")

        entries = {}
        current_caps = self.thresholds.get("ap_capacities", {})

        for i, ap in enumerate(aps):
            row_bg = COLOR_CARD_BG if i % 2 == 0 else COLOR_CARD_INNER
            row = tk.Frame(scroll_frame, bg=row_bg, padx=14, pady=7)
            row.pack(fill="x")
            tk.Label(row, text=ap, bg=row_bg, fg=COLOR_TEXT_PRIMARY, font=(FONT_FAMILY, 10, "bold"), width=22, anchor="w").pack(side="left")

            spin = tk.Spinbox(
                row, from_=1, to=1000, width=8,
                font=(FONT_FAMILY, 10),
                bg=COLOR_INPUT_BG, fg=COLOR_TEXT_PRIMARY,
                buttonbackground=COLOR_SIDEBAR_BTN,
                insertbackground="white",
                relief="flat", highlightthickness=1,
                highlightbackground=COLOR_INPUT_BORDER
            )
            active_val = current_caps.get(ap, def_cap)
            spin.delete(0, "end")
            spin.insert(0, str(active_val))
            spin.pack(side="left", padx=5)

            is_custom = ap in current_caps
            lbl_type = tk.Label(
                row,
                text="[Custom Limit]" if is_custom else "[Global Default]",
                bg=row_bg,
                fg=COLOR_TEXT_WARNING if is_custom else COLOR_TEXT_MUTED,
                font=(FONT_FAMILY, 9, "bold" if is_custom else "normal")
            )
            lbl_type.pack(side="left", padx=8)
            entries[ap] = spin

        # Action Buttons
        action_bar = tk.Frame(modal, bg=COLOR_PAGE_BG, padx=20, pady=14)
        action_bar.pack(fill="x")

        def save_and_close():
            new_caps = {}
            for ap_name, sp in entries.items():
                try:
                    val = int(sp.get().strip())
                    if val > 0 and val != def_cap:
                        new_caps[ap_name] = val
                except ValueError:
                    pass
            self.thresholds["ap_capacities"] = new_caps
            self._save_user_settings()
            modal.destroy()
            if self.active_page in self.page_methods:
                self.page_methods[self.active_page]()

        def clear_custom():
            self.thresholds["ap_capacities"] = {}
            self._save_user_settings()
            modal.destroy()
            if self.active_page in self.page_methods:
                self.page_methods[self.active_page]()

        def set_all_default():
            for sp in entries.values():
                sp.delete(0, "end")
                sp.insert(0, str(def_cap))

        btn_save = tk.Button(
            action_bar, text="💾 Save Limits", bg=COLOR_ACCENT_PRIMARY, fg="white",
            activebackground="#1D4ED8", activeforeground="white",
            font=(FONT_FAMILY, 10, "bold"), relief="flat", padx=14, pady=6,
            command=save_and_close, cursor="hand2"
        )
        btn_save.pack(side="right", padx=(8, 0))

        btn_cancel = tk.Button(
            action_bar, text="Cancel", bg=COLOR_SIDEBAR_BTN, fg=COLOR_TEXT_SECONDARY,
            activebackground=COLOR_SIDEBAR_HOVER, activeforeground="white",
            font=(FONT_FAMILY, 10), relief="flat", padx=14, pady=6,
            command=modal.destroy, cursor="hand2"
        )
        btn_cancel.pack(side="right")

        btn_clear = tk.Button(
            action_bar, text="Reset to Global Default", bg="#450A0A", fg=COLOR_TEXT_DANGER,
            activebackground="#7F1D1D", activeforeground="white",
            font=(FONT_FAMILY, 9), relief="flat", padx=10, pady=6,
            command=clear_custom, cursor="hand2"
        )
        btn_clear.pack(side="left")

        btn_fill = tk.Button(
            action_bar, text=f"Fill with {def_cap}", bg=COLOR_SIDEBAR_BTN, fg=COLOR_TEXT_PRIMARY,
            activebackground=COLOR_SIDEBAR_HOVER, activeforeground="white",
            font=(FONT_FAMILY, 9), relief="flat", padx=10, pady=6,
            command=set_all_default, cursor="hand2"
        )
        btn_fill.pack(side="left", padx=6)

    # ==========================================================
    # LAYOUT CREATION
    # ==========================================================

    def _create_sidebar(self):
        """Build the fixed left-side navigation sidebar."""

        self.sidebar = tk.Frame(self, bg=COLOR_SIDEBAR_BG, width=240)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # ── App identity ───────────────────────────────────────
        tk.Label(
            self.sidebar,
            text="📡",
            bg=COLOR_SIDEBAR_BG,
            fg="white",
            font=(FONT_FAMILY, 32),
        ).pack(pady=(25, 2))

        tk.Label(
            self.sidebar,
            text=APP_TITLE,
            bg=COLOR_SIDEBAR_BG,
            fg="white",
            font=(FONT_FAMILY, 13, "bold"),
            justify="center",
            wraplength=210,
        ).pack(pady=(0, 3))

        tk.Label(
            self.sidebar,
            text=f"v{APP_VERSION}  ·  {APP_AUTHOR}",
            bg=COLOR_SIDEBAR_BG,
            fg=COLOR_TEXT_MUTED,
            font=(FONT_FAMILY, 8),
            wraplength=210,
            justify="center",
        ).pack(pady=(0, 12))

        # ── Divider ────────────────────────────────────────────
        tk.Frame(self.sidebar, bg=COLOR_CARD_BORDER, height=1).pack(
            fill="x", padx=15, pady=(0, 8)
        )

        # ── Navigation buttons ─────────────────────────────────
        nav_items = [
            ("🏠  Dashboard",      "Dashboard"),
            ("👤  Users",          "Users"),
            ("📡  Access Points",  "Access Points"),
            ("🌐  Websites",       "Websites"),
            ("🔔  Alerts",         "Alerts"),
            ("📄  Reports",        "Reports"),
            ("⚙️  Settings",       "Settings"),
        ]

        show_methods = [
            self.show_dashboard,
            self.show_users,
            self.show_access_points,
            self.show_websites,
            self.show_alerts,
            self.show_reports,
            self.show_settings,
        ]

        for (label, page_name), method in zip(nav_items, show_methods):
            btn = tk.Button(
                self.sidebar,
                text=label,
                font=(FONT_FAMILY, 10, "bold"),
                bg=COLOR_SIDEBAR_BTN,
                fg=COLOR_TEXT_PRIMARY,
                bd=0,
                anchor="w",
                padx=18,
                activebackground=COLOR_SIDEBAR_HOVER,
                activeforeground="white",
                cursor="hand2",
                command=lambda pn=page_name, m=method: self._navigate(pn, m),
            )
            btn.pack(fill="x", padx=12, pady=3, ipady=8)
            self.nav_buttons[page_name] = btn

        # ── Divider ────────────────────────────────────────────
        tk.Frame(self.sidebar, bg=COLOR_CARD_BORDER, height=1).pack(
            fill="x", padx=15, pady=12
        )

        # ── Load Dataset button ────────────────────────────────
        tk.Button(
            self.sidebar,
            text="📂  Load Dataset",
            font=(FONT_FAMILY, 10, "bold"),
            bg=COLOR_ACCENT_PRIMARY,
            fg="white",
            bd=0,
            padx=18,
            activebackground="#1D4ED8",
            activeforeground="white",
            cursor="hand2",
            command=self.upload_file,
        ).pack(fill="x", padx=12, pady=3, ipady=9)

        # ── Dataset status label ───────────────────────
        self.sidebar_status = tk.Label(
            self.sidebar,
            text="No dataset loaded",
            bg=COLOR_SIDEBAR_BG,
            fg=COLOR_TEXT_SECONDARY,
            font=(FONT_FAMILY, 9),
            wraplength=210,
            justify="left",
        )
        self.sidebar_status.pack(padx=15, pady=(8, 5), anchor="w")

    def _create_scrollable_content(self):
        """Create the scrollable main content area (Canvas + inner Frame)."""

        container = tk.Frame(self, bg=COLOR_PAGE_BG)
        container.pack(side="right", expand=True, fill="both")

        # Vertical scrollbar
        vsb = tk.Scrollbar(container, orient="vertical")
        vsb.pack(side="right", fill="y")

        # Canvas
        self.canvas = tk.Canvas(
            container,
            bg=COLOR_PAGE_BG,
            yscrollcommand=vsb.set,
            highlightthickness=0,
        )
        self.canvas.pack(side="left", expand=True, fill="both")
        vsb.config(command=self.canvas.yview)

        # Inner frame (populated by each page method)
        self.content = tk.Frame(self.canvas, bg=COLOR_PAGE_BG)
        self._content_win = self.canvas.create_window(
            (0, 0), window=self.content, anchor="nw"
        )

        # Bindings
        self.content.bind("<Configure>", self._on_content_resize)
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>",   self._on_mousewheel)
        self.canvas.bind_all("<Button-5>",   self._on_mousewheel)

    def _on_content_resize(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_resize(self, event):
        self.canvas.itemconfig(self._content_win, width=event.width)

    def _on_mousewheel(self, event):
        if   event.num == 4: self.canvas.yview_scroll(-1, "units")
        elif event.num == 5: self.canvas.yview_scroll(1, "units")
        else: self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ==========================================================
    # NAVIGATION
    # ==========================================================

    def _navigate(self, page_name: str, show_func):
        """Switch to a page, highlight its sidebar button, scroll to top."""

        self._clear_content()

        # Reset all button colors
        for name, btn in self.nav_buttons.items():
            btn.config(bg=COLOR_SIDEBAR_BTN)

        # Highlight active button
        if page_name in self.nav_buttons:
            self.nav_buttons[page_name].config(bg=COLOR_SIDEBAR_ACTIVE)

        self.active_page = page_name
        self.canvas.yview_moveto(0)
        show_func()

    def _clear_content(self):
        """Close all open Matplotlib figures and destroy content widgets."""

        for fig in self.open_figures:
            plt.close(fig)
        self.open_figures.clear()

        for widget in self.content.winfo_children():
            widget.destroy()

    # ==========================================================
    # REUSABLE UI COMPONENTS
    # ==========================================================

    def _page_header(self, title: str, subtitle: str = ""):
        """Standard page title + optional subtitle."""

        frame = tk.Frame(self.content, bg=COLOR_PAGE_BG)
        frame.pack(fill="x", padx=30, pady=(25, 5))

        tk.Label(
            frame, text=title,
            bg=COLOR_PAGE_BG, fg=COLOR_TEXT_PRIMARY,
            font=FONT_HEADING,
        ).pack(anchor="w")

        if subtitle:
            tk.Label(
                frame, text=subtitle,
                bg=COLOR_PAGE_BG, fg=COLOR_TEXT_SECONDARY,
                font=FONT_BODY,
            ).pack(anchor="w", pady=(3, 0))

    def _section_label(self, text: str):
        """Bold section heading inside the content area."""

        tk.Label(
            self.content, text=text,
            bg=COLOR_PAGE_BG, fg=COLOR_TEXT_PRIMARY,
            font=FONT_SUBHEAD,
        ).pack(anchor="w", padx=30, pady=(18, 6))

    def _card_row(self, cards: list):
        """
        Horizontal row of KPI stat cards.

        Each card:  { "label": str, "value": str, "color": str }
        """

        row = tk.Frame(self.content, bg=COLOR_PAGE_BG)
        row.pack(fill="x", padx=24, pady=(4, 8))

        for card in cards:
            f = tk.Frame(
                row, bg=COLOR_CARD_BG,
                highlightbackground=COLOR_CARD_BORDER,
                highlightthickness=1,
            )
            f.pack(side="left", padx=6, pady=4,
                   ipadx=16, ipady=14, expand=True, fill="x")

            tk.Label(
                f, text=card["value"],
                bg=COLOR_CARD_BG,
                fg=card.get("color", COLOR_TEXT_PRIMARY),
                font=FONT_CARD_VAL,
            ).pack()

            tk.Label(
                f, text=card["label"],
                bg=COLOR_CARD_BG, fg=COLOR_TEXT_SECONDARY,
                font=FONT_CARD_LBL,
            ).pack()

    def _treeview(self, parent, columns: list, rows: list,
                  col_widths: dict = None, height: int = 12,
                  row_tags: list = None) -> tk.Frame:
        """
        Styled Treeview table with alternating row colors and optional status row_tags.

        Returns the containing Frame (caller must pack/grid it).
        """

        frame = tk.Frame(parent, bg=COLOR_CARD_BG)

        tree = ttk.Treeview(frame, columns=columns,
                            show="headings", height=height)

        for col in columns:
            tree.heading(col, text=col.replace("_", " "))
            w = (col_widths or {}).get(col, 130)
            tree.column(col, width=w, anchor="center", stretch=True)

        for i, row in enumerate(rows):
            if row_tags and i < len(row_tags) and row_tags[i]:
                tag = row_tags[i]
            else:
                tag = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end", values=row, tags=(tag,))

        tree.tag_configure("even", background="#0E1626", foreground=COLOR_TEXT_PRIMARY)
        tree.tag_configure("odd",  background="#111B2E", foreground=COLOR_TEXT_PRIMARY)
        tree.tag_configure("overload", background="#450A0A", foreground="#FECACA")
        tree.tag_configure("warning",  background="#451A03", foreground="#FDE68A")
        tree.tag_configure("normal",   background="#064E3B", foreground="#A7F3D0")

        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)

        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        return frame

    def _embed_chart(self, parent, fig):
        """Embed a Matplotlib figure into a Tkinter parent widget."""

        self.open_figures.append(fig)
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _chart_frame(self) -> tk.Frame:
        """Return a blank card frame for placing a chart inside."""

        f = tk.Frame(
            self.content, bg=COLOR_CARD_BG,
            highlightbackground=COLOR_CARD_BORDER,
            highlightthickness=1,
        )
        f.pack(fill="x", padx=30, pady=5)
        return f

    def _no_data_banner(self, msg: str = "Load a dataset to view this page."):
        """Centered 'no data' prompt with a Load Dataset button."""

        frame = tk.Frame(self.content, bg=COLOR_PAGE_BG)
        frame.pack(expand=True, pady=70)

        tk.Label(frame, text="📂", bg=COLOR_PAGE_BG,
                 font=(FONT_FAMILY, 44)).pack()
        tk.Label(frame, text=msg, bg=COLOR_PAGE_BG,
                 fg=COLOR_TEXT_SECONDARY, font=(FONT_FAMILY, 13)).pack(pady=10)
        tk.Button(
            frame, text="Load Dataset",
            font=(FONT_FAMILY, 11, "bold"),
            bg=COLOR_ACCENT_PRIMARY, fg="white", bd=0,
            padx=22, pady=10,
            activebackground="#1D4ED8", activeforeground="white",
            cursor="hand2", command=self.upload_file,
        ).pack()

    def _unavailable_notice(self, missing_col: str):
        """Dark amber notice when an optional column is absent."""

        f = tk.Frame(
            self.content, bg="#261A08",
            highlightbackground="#78350F", highlightthickness=1,
        )
        f.pack(fill="x", padx=30, pady=10)
        tk.Label(
            f,
            text=f"⚠️  Feature Unavailable — column '{missing_col}' "
                 "not found in this dataset.",
            bg="#261A08", fg=COLOR_TEXT_WARNING,
            font=(FONT_FAMILY, 10, "bold"),
            padx=14, pady=10,
        ).pack(anchor="w")

    def _alert_section(self, title: str, severity: str,
                       description: str, df_alert):
        """
        Render one alert block (title + badge + description + table).

        severity: "high" | "medium" | "low"
        """

        palette = {
            "high":   (COLOR_TEXT_DANGER,  "#1A0E13", "#7F1D1D"),
            "medium": (COLOR_TEXT_WARNING, "#1C1408", "#78350F"),
            "low":    (COLOR_ACCENT_BLUE,  "#0C1626", "#1E3A8A"),
        }
        text_c, bg_c, border_c = palette.get(severity, palette["medium"])

        outer = tk.Frame(
            self.content, bg=bg_c,
            highlightbackground=border_c, highlightthickness=1,
        )
        outer.pack(fill="x", padx=30, pady=8)

        # ── Header row ─────────────────────────────────────────
        hrow = tk.Frame(outer, bg=bg_c)
        hrow.pack(fill="x", padx=16, pady=(12, 4))

        tk.Label(
            hrow, text=title, bg=bg_c, fg=text_c,
            font=(FONT_FAMILY, 13, "bold"),
        ).pack(side="left")

        tk.Label(
            hrow, text=f"  {len(df_alert)} flagged  ",
            bg=text_c, fg="white",
            font=(FONT_FAMILY, 9, "bold"),
        ).pack(side="left", padx=10)

        # ── Description ────────────────────────────────────────
        tk.Label(
            outer, text=description, bg=bg_c,
            fg=COLOR_TEXT_SECONDARY, font=(FONT_FAMILY, 10),
            wraplength=870, justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 8))

        # ── Table or ✅ notice ─────────────────────────────────
        if df_alert.empty:
            tk.Label(
                outer, text="✅  No violations found.",
                bg=bg_c, fg=COLOR_TEXT_SUCCESS,
                font=(FONT_FAMILY, 10),
            ).pack(anchor="w", padx=16, pady=(0, 12))
        else:
            cols = list(df_alert.columns)
            rows = [tuple(r) for _, r in df_alert.iterrows()]
            tbl  = self._treeview(outer, cols, rows, height=min(len(rows), 6))
            tbl.pack(fill="x", padx=16, pady=(0, 12))

    # ==========================================================
    # FILE OPERATIONS
    # ==========================================================

    def choose_file(self) -> str:
        """
        Open a native file-chooser dialog.

        On Linux: tries kdialog first, falls back to Tkinter.
        On other OS: uses Tkinter's filedialog.
        """

        if platform.system() == "Linux":
            try:
                result = subprocess.run(
                    ["kdialog", "--getopenfilename", "",
                     "*.csv *.xlsx *.xls",
                     "--title", "Select Wi-Fi Usage Dataset"],
                    capture_output=True, text=True,
                )
                path = result.stdout.strip()
                if path:
                    return path
            except Exception:
                pass  # kdialog not installed — fall through

        return filedialog.askopenfilename(
            title="Select Wi-Fi Usage Dataset",
            filetypes=[
                ("CSV files",           "*.csv"),
                ("Excel files",         "*.xlsx *.xls"),
                ("All supported files", "*.csv *.xlsx *.xls"),
            ],
        )

    def upload_file(self):
        """
        Load and validate a CSV or Excel dataset.

        Validates that all mandatory columns exist before accepting
        the file. Updates the sidebar status label on success.
        After loading, reloads whichever page is currently active.
        """

        path = self.choose_file()
        if not path:
            return

        try:
            if path.lower().endswith(".csv"):
                df = pd.read_csv(path)
            elif path.lower().endswith((".xlsx", ".xls")):
                df = pd.read_excel(path)
            else:
                messagebox.showerror("Unsupported File",
                    "Please select a .csv or .xlsx file.")
                return

            # ── Validate mandatory columns ──────────────────
            compat = check_columns(df)

            if not compat["is_valid"]:
                missing = ", ".join(compat["missing_mandatory"])
                messagebox.showerror(
                    "Incompatible Dataset",
                    f"Missing required columns:\n\n{missing}\n\n"
                    "Please check the dataset and try again."
                )
                return

            # ── Store state ─────────────────────────────────
            self.data      = df
            self.file_path = path
            self.compat    = compat

            # ── Update sidebar label ─────────────────────────
            fname = get_filename(path)
            fsize = get_file_size_kb(path)
            self.sidebar_status.config(
                text=f"✅ {fname}\n{df.shape[0]} rows  ·  {fsize}",
                fg="#86EFAC",
            )

            # ── Build success message ────────────────────────
            present  = len(compat["present_optional"])
            total_op = present + len(compat["missing_optional"])
            missing_names = compat["missing_optional"]

            info = (
                f"Dataset loaded successfully!\n\n"
                f"File     : {fname}\n"
                f"Rows     : {df.shape[0]}\n"
                f"Columns  : {df.shape[1]}\n\n"
                f"Optional columns available: {present}/{total_op}"
            )
            if missing_names:
                info += f"\nFeatures disabled: {', '.join(missing_names)}"

            messagebox.showinfo("Upload Successful", info)

            # ── Reload current page with new data ────────────
            reload_fn = self.page_methods.get(
                self.active_page, self.show_dashboard
            )
            self._navigate(self.active_page, reload_fn)

        except Exception as e:
            messagebox.showerror("Error Loading Dataset",
                                 f"Could not load the file.\n\n{e}")

    # ==========================================================
    # PAGE 1 — DASHBOARD
    # ==========================================================

    def show_dashboard(self):
        """
        Dashboard page.

        Displays:
            - 5 KPI summary cards
            - Hourly activity bar chart
            - Top 10 bandwidth users table
            - Website category usage bar chart
        """

        self._page_header(
            "Dashboard",
            "Real-time overview of network usage across all users and access points"
        )

        if self.data is None:
            self._no_data_banner("Load a dataset to see the dashboard.")
            return

        df = self.data

        # ── KPI Cards ──────────────────────────────────────────
        self._section_label("Network Summary")
        summary = an.get_dashboard_summary(df)

        self._card_row([
            {"label": "Total Users",    "value": format_number(summary["total_users"]),       "color": COLOR_ACCENT_BLUE},
            {"label": "Total Devices",  "value": format_number(summary["total_devices"]),     "color": COLOR_ACCENT_BLUE},
            {"label": "Total Upload",   "value": format_bytes(summary["total_upload_mb"]),    "color": COLOR_ACCENT_ORANGE},
            {"label": "Total Download", "value": format_bytes(summary["total_download_mb"]),  "color": COLOR_ACCENT_GREEN},
            {"label": "Peak Hour",      "value": summary["peak_hour"],                         "color": COLOR_TEXT_PRIMARY},
        ])

        # ── Hourly Activity Chart ──────────────────────────────
        hourly_df = an.get_hourly_activity(df)

        if not hourly_df.empty:
            self._section_label("Hourly Activity")
            cf = self._chart_frame()

            fig, ax = plt.subplots(figsize=CHART_FIG_WIDE, dpi=CHART_DPI)
            fig.patch.set_facecolor(COLOR_CARD_BG)
            ax.set_facecolor(COLOR_CARD_INNER)

            hours    = hourly_df["Hour"].tolist()
            sessions = hourly_df["Sessions"].tolist()
            peak_idx = sessions.index(max(sessions)) if sessions else 0

            bar_colors = [
                COLOR_STATUS_OVERLOAD if i == peak_idx else COLOR_ACCENT_BLUE
                for i in range(24)
            ]

            ax.bar(hours, sessions, color=bar_colors, alpha=0.88,
                   width=0.75, edgecolor=COLOR_CARD_BG)
            ax.set_xlabel("Hour of Day", fontsize=10, color=COLOR_TEXT_SECONDARY)
            ax.set_ylabel("Sessions",    fontsize=10, color=COLOR_TEXT_SECONDARY)
            ax.set_title("Network Sessions by Hour  (red = peak activity)",
                         fontsize=12, fontweight="bold",
                         color=COLOR_TEXT_PRIMARY, pad=10)
            ax.set_xticks(range(24))
            ax.tick_params(colors=COLOR_TEXT_SECONDARY, labelsize=8)
            ax.spines[["top", "right"]].set_visible(False)
            ax.spines["left"].set_color(COLOR_CARD_BORDER)
            ax.spines["bottom"].set_color(COLOR_CARD_BORDER)
            ax.grid(axis="y", linestyle="--", alpha=0.25, color="#334155")
            fig.tight_layout(pad=1.5)
            self._embed_chart(cf, fig)

        # ── Top Bandwidth Users Table ──────────────────────────
        self._section_label("Top 10 Bandwidth Users")
        top_users = an.get_top_bandwidth_users(df, n=10)

        if not top_users.empty:
            cols = ["Username", "Upload_MB", "Download_MB", "Total_MB"]
            rows = [tuple(r) for _, r in top_users[cols].iterrows()]
            tbl  = self._treeview(
                self.content, cols, rows,
                col_widths={"Username": 160, "Upload_MB": 120,
                            "Download_MB": 130, "Total_MB": 120},
                height=10,
            )
            tbl.pack(fill="x", padx=30, pady=5)

        # ── Website Category Bar Chart ─────────────────────────
        cat_df = an.get_top_website_categories(df)

        if not cat_df.empty:
            self._section_label("Download by Website Category")
            cf2 = self._chart_frame()

            fig2, ax2 = plt.subplots(figsize=(9, 3.2), dpi=CHART_DPI)
            fig2.patch.set_facecolor(COLOR_CARD_BG)
            ax2.set_facecolor(COLOR_CARD_INNER)

            cats   = cat_df["Website_Category"].tolist()
            dl_mb  = cat_df["Download_MB"].tolist()
            palette = [COLOR_ACCENT_BLUE, COLOR_ACCENT_GREEN, COLOR_ACCENT_ORANGE,
                       COLOR_ACCENT_PURPLE, "#EC4899", COLOR_STATUS_OVERLOAD]

            bars = ax2.bar(
                cats, dl_mb,
                color=[palette[i % len(palette)] for i in range(len(cats))],
                alpha=0.88, edgecolor=COLOR_CARD_BG,
            )
            ax2.set_ylabel("Download (MB)", fontsize=10, color=COLOR_TEXT_SECONDARY)
            ax2.set_title("Total Download per Website Category",
                          fontsize=12, fontweight="bold",
                          color=COLOR_TEXT_PRIMARY, pad=8)
            ax2.tick_params(colors=COLOR_TEXT_SECONDARY, labelsize=9)
            ax2.spines[["top", "right"]].set_visible(False)
            ax2.spines["left"].set_color(COLOR_CARD_BORDER)
            ax2.spines["bottom"].set_color(COLOR_CARD_BORDER)
            ax2.grid(axis="y", linestyle="--", alpha=0.25, color="#334155")
            fig2.tight_layout(pad=1.5)
            self._embed_chart(cf2, fig2)

        tk.Frame(self.content, bg=COLOR_PAGE_BG, height=30).pack()

    # ==========================================================
    # PAGE 2 — USERS
    # ==========================================================

    def show_users(self):
        """
        Users page.

        Displays:
            - User KPI summary cards
            - Full user bandwidth table (searchable/sortable in future)
            - Device type distribution pie chart
            - Unique devices per user table
        """

        self._page_header(
            "User Analysis",
            "Bandwidth consumption, device counts and session activity per user"
        )

        if self.data is None:
            self._no_data_banner()
            return

        df = self.data

        # ── KPI Cards ──────────────────────────────────────────
        user_table = an.get_user_bandwidth_table(df)
        top_user   = user_table.iloc[0][COL_USERNAME] if not user_table.empty else "N/A"
        avg_mb     = round(user_table["Total_MB"].mean(), 2) if not user_table.empty else 0

        self._card_row([
            {"label": "Top Bandwidth Consumer", "value": top_user,                "color": COLOR_TEXT_DANGER},
            {"label": "Average Usage / User",   "value": format_bytes(avg_mb),    "color": COLOR_ACCENT_BLUE},
            {"label": "Active Users",           "value": str(len(user_table)),     "color": COLOR_ACCENT_GREEN},
        ])

        # ── User Bandwidth Table ───────────────────────────────
        self._section_label("User Bandwidth Summary")
        user_df = an.get_user_bandwidth_table(df)

        if not user_df.empty:
            cols = ["Username", "Upload_MB", "Download_MB", "Total_MB", "Sessions"]
            rows = [tuple(r) for _, r in user_df[cols].iterrows()]
            tbl  = self._treeview(
                self.content, cols, rows,
                col_widths={"Username": 150, "Upload_MB": 120,
                            "Download_MB": 130, "Total_MB": 120, "Sessions": 90},
                height=15,
            )
            tbl.pack(fill="x", padx=30, pady=5)

        # ── Device Type Pie Chart ──────────────────────────────
        dev_type_df = an.get_user_device_types(df)

        if not dev_type_df.empty:
            self._section_label("Sessions by Device Type")

            cf = tk.Frame(
                self.content, bg=COLOR_CARD_BG,
                highlightbackground=COLOR_CARD_BORDER,
                highlightthickness=1,
            )
            cf.pack(padx=30, pady=5, anchor="w")

            fig, ax = plt.subplots(figsize=(5.5, 3.8), dpi=CHART_DPI)
            fig.patch.set_facecolor(COLOR_CARD_BG)
            ax.set_facecolor(COLOR_CARD_INNER)

            labels  = dev_type_df["Device_Type"].tolist()
            sizes   = dev_type_df["Sessions"].tolist()
            colors  = [COLOR_ACCENT_BLUE, COLOR_ACCENT_GREEN, COLOR_ACCENT_ORANGE, COLOR_ACCENT_PURPLE]

            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels,
                colors=colors[:len(labels)],
                autopct="%1.1f%%", startangle=140,
                wedgeprops={"edgecolor": "white", "linewidth": 2},
                pctdistance=0.80,
            )
            for t in texts:
                t.set_fontsize(10)
                t.set_color(COLOR_TEXT_PRIMARY)
            for at in autotexts:
                at.set_fontsize(9)

            ax.set_title("Sessions by Device Type", fontsize=12,
                         fontweight="bold", color=COLOR_TEXT_PRIMARY, pad=8)
            fig.tight_layout(pad=1.5)
            self._embed_chart(cf, fig)

        # ── Devices Per User Table ─────────────────────────────
        dev_count_df = an.get_user_device_count(df)

        if not dev_count_df.empty:
            self._section_label("Unique Devices Per User")
            cols = ["Username", "Device_Count"]
            rows = [tuple(r) for _, r in dev_count_df[cols].iterrows()]
            tbl2 = self._treeview(
                self.content, cols, rows,
                col_widths={"Username": 200, "Device_Count": 180},
                height=12,
            )
            tbl2.pack(fill="x", padx=30, pady=5)

        tk.Frame(self.content, bg=COLOR_PAGE_BG, height=30).pack()

    # ==========================================================
    # PAGE 3 — ACCESS POINTS
    # ==========================================================

    def show_access_points(self):
        """
        Access Points page.

        Displays:
            - Interactive capacity and overload threshold tuning bar
            - Overload summary status cards
            - Comprehensive AP capacity & overload status table (with visual tags)
            - Peak concurrent users vs capacity chart
            - Overall traffic and sessions AP summary table
        """

        self._page_header(
            "Access Points",
            "Dynamic overload detection, customizable device capacity limits, and traffic analysis"
        )

        if self.data is None:
            self._no_data_banner()
            return

        df = self.data

        # Check the required column exists in this dataset
        if not has_column(df, COL_ACCESS_POINT):
            self._unavailable_notice("Access_Point")
            return

        # ── Interactive Capacity Tuning Bar ───────────────────
        tune_frame = tk.Frame(
            self.content, bg=COLOR_CARD_BG,
            highlightbackground=COLOR_CARD_BORDER,
            highlightthickness=1, padx=20, pady=12,
        )
        tune_frame.pack(fill="x", padx=30, pady=(5, 15))

        # Title & Help
        t_top = tk.Frame(tune_frame, bg=COLOR_CARD_BG)
        t_top.pack(fill="x", pady=(0, 8))

        tk.Label(
            t_top, text="⚙️  Capacity & Overload Threshold Controls",
            bg=COLOR_CARD_BG, fg=COLOR_TEXT_PRIMARY,
            font=(FONT_FAMILY, 12, "bold"), anchor="w"
        ).pack(side="left")

        custom_count = len(self.thresholds.get("ap_capacities", {}))
        custom_tag_text = f"({custom_count} custom limit{'s' if custom_count != 1 else ''} active)" if custom_count > 0 else "(Global default applied)"
        tk.Label(
            t_top, text=custom_tag_text,
            bg=COLOR_CARD_BG,
            fg=COLOR_TEXT_WARNING if custom_count > 0 else COLOR_TEXT_SECONDARY,
            font=(FONT_FAMILY, 10, "italic"), anchor="w"
        ).pack(side="left", padx=10)

        # Controls Row
        ctrl_row = tk.Frame(tune_frame, bg=COLOR_CARD_BG)
        ctrl_row.pack(fill="x")

        tk.Label(
            ctrl_row, text="Global Max Devices / AP:",
            bg=COLOR_CARD_BG, fg=COLOR_TEXT_SECONDARY,
            font=(FONT_FAMILY, 10, "bold"), anchor="w"
        ).pack(side="left")

        def_cap = int(self.thresholds.get("default_ap_capacity", DEFAULT_ALERT_AP_MAX_USERS))
        spin_ap_cap = tk.Spinbox(
            ctrl_row, from_=1, to=1000, width=6,
            font=(FONT_FAMILY, 10),
            bg=COLOR_INPUT_BG, fg=COLOR_TEXT_PRIMARY,
            buttonbackground=COLOR_SIDEBAR_BTN,
            insertbackground="white",
            relief="flat", highlightthickness=1,
            highlightbackground=COLOR_INPUT_BORDER
        )
        spin_ap_cap.delete(0, "end")
        spin_ap_cap.insert(0, str(def_cap))
        spin_ap_cap.pack(side="left", padx=(8, 18))

        def apply_ap_threshold():
            try:
                val = int(spin_ap_cap.get().strip())
                if val > 0:
                    self.thresholds["default_ap_capacity"] = val
                    self._save_user_settings()
                    self.show_access_points()
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a valid positive integer for AP capacity.")

        def reset_ap_thresholds():
            self.thresholds["default_ap_capacity"] = DEFAULT_ALERT_AP_MAX_USERS
            self.thresholds["ap_capacities"] = {}
            self._save_user_settings()
            self.show_access_points()

        btn_apply = tk.Button(
            ctrl_row, text="⚡ Apply & Recalculate",
            bg=COLOR_ACCENT_PRIMARY, fg="white",
            activebackground="#1D4ED8", activeforeground="white",
            font=(FONT_FAMILY, 9, "bold"), relief="flat",
            padx=12, pady=4, cursor="hand2",
            command=apply_ap_threshold
        )
        btn_apply.pack(side="left", padx=(0, 10))

        btn_custom = tk.Button(
            ctrl_row, text="🔧 Custom Per-AP Limits...",
            bg=COLOR_SIDEBAR_BTN, fg=COLOR_TEXT_PRIMARY,
            activebackground=COLOR_SIDEBAR_HOVER, activeforeground="white",
            font=(FONT_FAMILY, 9, "bold"), relief="flat",
            padx=12, pady=4, cursor="hand2",
            command=self._open_per_ap_modal
        )
        btn_custom.pack(side="left", padx=(0, 10))

        btn_reset = tk.Button(
            ctrl_row, text="🔄 Reset Defaults",
            bg=COLOR_SIDEBAR_BTN, fg=COLOR_TEXT_SECONDARY,
            activebackground=COLOR_SIDEBAR_HOVER, activeforeground="white",
            font=(FONT_FAMILY, 9), relief="flat",
            padx=10, pady=4, cursor="hand2",
            command=reset_ap_thresholds
        )
        btn_reset.pack(side="left")

        # ── Analysis Calculations ──────────────────────────────
        current_caps = self.thresholds.get("ap_capacities", {})
        active_def_cap = self.thresholds.get("default_ap_capacity", DEFAULT_ALERT_AP_MAX_USERS)

        status_df   = an.get_ap_overload_status(df, ap_capacities=current_caps, default_capacity=active_def_cap)
        most_loaded = an.get_most_overloaded_ap(df, ap_capacities=current_caps, default_capacity=active_def_cap)
        least_used  = an.get_least_utilized_ap(df)

        overloaded_aps = status_df[status_df["Status"] == "Overloaded"] if not status_df.empty else pd.DataFrame()
        warning_aps    = status_df[status_df["Status"] == "Warning"] if not status_df.empty else pd.DataFrame()
        overloaded_cnt = len(overloaded_aps)

        # ── Summary Cards ──────────────────────────────────────
        if overloaded_cnt > 0:
            status_val   = f"⚠️ {overloaded_cnt} AP{'s' if overloaded_cnt > 1 else ''} Overloaded"
            status_color = COLOR_TEXT_DANGER
        else:
            status_val   = "✅ All APs Normal"
            status_color = COLOR_TEXT_SUCCESS

        if not status_df.empty:
            top_ap = status_df.iloc[0]
            most_val = f"{top_ap['Access_Point']} ({top_ap['Peak_Users']}/{top_ap['Max_Capacity']} dev — {top_ap['Utilization_Pct']}%)"
            most_col = COLOR_TEXT_DANGER if top_ap["Status"] == "Overloaded" else (COLOR_TEXT_WARNING if top_ap["Status"] == "Warning" else COLOR_TEXT_PRIMARY)
        else:
            most_val = "N/A"
            most_col = COLOR_TEXT_PRIMARY

        self._card_row([
            {"label": "Network AP Health", "value": status_val, "color": status_color},
            {"label": "Highest Loaded AP",  "value": most_val,   "color": most_col},
            {"label": "Least Utilized AP",  "value": least_used,  "color": COLOR_ACCENT_GREEN},
            {"label": "Default AP Capacity", "value": f"{active_def_cap} Devices", "color": COLOR_ACCENT_BLUE},
        ])

        # ── Capacity & Overload Status Table ───────────────────
        self._section_label("Access Point Capacity & Overload Evaluation")

        if not status_df.empty:
            cols = ["Access_Point", "Peak_Users", "Max_Capacity",
                    "Utilization_%", "Excess_Users", "Status", "Peak_Timestamp"]
            rows = []
            tags = []

            for _, r in status_df.iterrows():
                st = r["Status"]
                if st == "Overloaded":
                    st_str = "🔴 Overloaded"
                    tag = "overload"
                elif st == "Warning":
                    st_str = "🟡 Warning"
                    tag = "warning"
                else:
                    st_str = "🟢 Normal"
                    tag = "normal"

                tags.append(tag)
                rows.append((
                    r["Access_Point"],
                    int(r["Peak_Users"]),
                    int(r["Max_Capacity"]),
                    f"{r['Utilization_Pct']:.1f}%",
                    int(r["Excess_Users"]),
                    st_str,
                    r["Peak_Timestamp"],
                ))

            tbl_status = self._treeview(
                self.content, cols, rows,
                col_widths={"Access_Point": 160, "Peak_Users": 100,
                            "Max_Capacity": 110, "Utilization_%": 110,
                            "Excess_Users": 100, "Status": 130,
                            "Peak_Timestamp": 180},
                height=min(12, max(5, len(rows))),
                row_tags=tags,
            )
            tbl_status.pack(fill="x", padx=30, pady=5)

        # ── Peak Concurrent Users vs Capacity Chart ────────────
        if not status_df.empty:
            self._section_label("Peak Simultaneous Users vs Configured Capacity")
            cf = self._chart_frame()

            fig, ax = plt.subplots(figsize=(9, 4.5), dpi=CHART_DPI)
            fig.patch.set_facecolor(COLOR_CARD_BG)
            ax.set_facecolor(COLOR_CARD_INNER)

            plot_df = status_df.sort_values("Peak_Users", ascending=True)
            aps        = plot_df["Access_Point"].tolist()
            peak_users = plot_df["Peak_Users"].tolist()
            capacities = plot_df["Max_Capacity"].tolist()
            statuses   = plot_df["Status"].tolist()

            bar_colors = [
                COLOR_STATUS_OVERLOAD if s == "Overloaded"
                else (COLOR_STATUS_WARNING if s == "Warning" else COLOR_ACCENT_BLUE)
                for s in statuses
            ]

            y_pos = range(len(aps))
            bars = ax.barh(y_pos, peak_users, color=bar_colors, alpha=0.88, edgecolor=COLOR_CARD_BG, height=0.65)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(aps, fontsize=9, color=COLOR_TEXT_PRIMARY, fontweight="bold")

            # Draw threshold markers for each bar or line
            ax.axvline(
                active_def_cap, color=COLOR_STATUS_OVERLOAD, linestyle="--",
                linewidth=1.5, alpha=0.85,
                label=f"Default Capacity ({active_def_cap} dev)"
            )

            # Value labels on bars
            for bar, p_u, cap in zip(bars, peak_users, capacities):
                lbl = f"{p_u} (cap: {cap})"
                ax.text(
                    bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                    lbl, va="center", ha="left",
                    fontsize=8, color=COLOR_TEXT_SECONDARY, fontweight="bold"
                )

            ax.set_xlabel("Peak Simultaneous Users", fontsize=10, color=COLOR_TEXT_SECONDARY)
            ax.set_title("Peak Users per AP (Red = Overloaded, Amber = Warning, Blue = Normal)",
                         fontsize=11, fontweight="bold", color=COLOR_TEXT_PRIMARY, pad=10)
            ax.tick_params(colors=COLOR_TEXT_SECONDARY, labelsize=9)
            ax.spines[["top", "right"]].set_visible(False)
            ax.spines["left"].set_color(COLOR_CARD_BORDER)
            ax.spines["bottom"].set_color(COLOR_CARD_BORDER)
            ax.grid(axis="x", linestyle="--", alpha=0.25, color="#334155")
            ax.legend(loc="lower right", frameon=True, facecolor=COLOR_CARD_BG, edgecolor=COLOR_CARD_BORDER, labelcolor=COLOR_TEXT_PRIMARY, fontsize=8)
            fig.tight_layout(pad=1.5)
            self._embed_chart(cf, fig)

        # ── Overall AP Traffic Summary Table ───────────────────
        self._section_label("Access Point Traffic & Session Summary")
        ap_df = an.get_ap_summary(df)

        if not ap_df.empty:
            cols = ["Access_Point", "Unique_Users", "Sessions",
                    "Upload_MB", "Download_MB", "Total_MB"]
            rows = [tuple(r) for _, r in ap_df[cols].iterrows()]
            tbl  = self._treeview(
                self.content, cols, rows,
                col_widths={"Access_Point": 170, "Unique_Users": 110,
                            "Sessions": 90, "Upload_MB": 110,
                            "Download_MB": 120, "Total_MB": 110},
                height=10,
            )
            tbl.pack(fill="x", padx=30, pady=5)

        tk.Frame(self.content, bg=COLOR_PAGE_BG, height=30).pack()

    # ==========================================================
    # PAGE 4 — WEBSITES
    # ==========================================================

    def show_websites(self):
        """
        Websites page.

        Displays:
            - Browsing category distribution (pie chart)
            - Top visited websites table
            - Blocked access attempts table (if Status column present)
        """

        self._page_header(
            "Websites",
            "Browsing category analysis, top domains, and blocked access attempts"
        )

        if self.data is None:
            self._no_data_banner()
            return

        df = self.data

        # ── Category Pie Chart ─────────────────────────────────
        cat_df = an.get_category_breakdown(df)

        if cat_df.empty:
            self._unavailable_notice("Website_Category")
        else:
            self._section_label("Browsing Category Breakdown")

            cf = tk.Frame(
                self.content, bg=COLOR_CARD_BG,
                highlightbackground=COLOR_CARD_BORDER,
                highlightthickness=1,
            )
            cf.pack(padx=30, pady=5, anchor="w")

            fig, ax = plt.subplots(figsize=(6.5, 4.5), dpi=CHART_DPI)
            fig.patch.set_facecolor(COLOR_CARD_BG)

            labels  = cat_df["Website_Category"].tolist()
            sizes   = cat_df["Sessions"].tolist()
            palette = ["#3B82F6", "#22C55E", "#F97316",
                       "#8B5CF6", "#EC4899", "#EF4444"]

            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels,
                colors=palette[:len(labels)],
                autopct="%1.1f%%", startangle=130,
                wedgeprops={"edgecolor": COLOR_CARD_BG, "linewidth": 2},
                pctdistance=0.80,
            )
            for t in texts:
                t.set_fontsize(9)
                t.set_color(COLOR_TEXT_PRIMARY)
            for at in autotexts:
                at.set_fontsize(8)
                at.set_color("white")

            ax.set_title("Sessions by Website Category",
                         fontsize=12, fontweight="bold",
                         color=COLOR_TEXT_PRIMARY, pad=8)
            fig.tight_layout(pad=1.5)
            self._embed_chart(cf, fig)

        # ── Top Websites Table ─────────────────────────────────
        top_web = an.get_top_websites(df, n=15)

        if top_web.empty:
            self._unavailable_notice("Website")
        else:
            self._section_label("Top 15 Most Visited Websites")
            cols = ["Website", "Sessions", "Download_MB"]
            rows = [tuple(r) for _, r in top_web[cols].iterrows()]
            tbl  = self._treeview(
                self.content, cols, rows,
                col_widths={"Website": 240, "Sessions": 130, "Download_MB": 150},
                height=15,
            )
            tbl.pack(fill="x", padx=30, pady=5)

        # ── Blocked Access Table ───────────────────────────────
        blocked_df = an.get_blocked_sites(df)

        if not blocked_df.empty:
            self._section_label(
                f"Blocked Access Attempts  ({len(blocked_df)} total)"
            )
            want = ["Username", "Website", "Website_Category", "Timestamp"]
            avail = [c for c in want if c in blocked_df.columns]
            rows  = [tuple(r) for _, r in blocked_df[avail].iterrows()]
            tbl2  = self._treeview(
                self.content, avail, rows,
                col_widths={"Username": 150, "Website": 220,
                            "Website_Category": 160, "Timestamp": 190},
                height=8,
            )
            tbl2.pack(fill="x", padx=30, pady=5)

        tk.Frame(self.content, bg=COLOR_PAGE_BG, height=30).pack()

    # ==========================================================
    # PAGE 5 — ALERTS
    # ==========================================================

    def show_alerts(self):
        """
        Alerts page.

        Runs all four rule-based alert checks using user-configured thresholds:
            1. High Upload Activity (per session) — user-tunable threat limit
            2. Multiple Devices per User — user-tunable device limit
            3. Repeated Blocked Website Access — user-tunable attempt limit
            4. Overloaded Access Point — user-tunable AP capacity limits

        Each section shows: title, count badge, description, table.
        """

        if self.data is None:
            self._page_header("Alerts", "Rule-based behavioral anomaly detection for administrator investigation")
            self._no_data_banner()
            return

        df = self.data

        # ── Interactive Threat Threshold Tuning Bar ───────────
        tune_frame = tk.Frame(
            self.content, bg=COLOR_CARD_BG,
            highlightbackground=COLOR_CARD_BORDER,
            highlightthickness=1, padx=20, pady=12,
        )
        tune_frame.pack(fill="x", padx=30, pady=(5, 14))

        # Title
        t_top = tk.Frame(tune_frame, bg=COLOR_CARD_BG)
        t_top.pack(fill="x", pady=(0, 10))

        tk.Label(
            t_top, text="🛡️  Security Threat & Anomaly Detection Controls",
            bg=COLOR_CARD_BG, fg=COLOR_TEXT_PRIMARY,
            font=(FONT_FAMILY, 12, "bold"), anchor="w"
        ).pack(side="left")

        tk.Label(
            t_top, text="(Tune parameters in real-time to analyze network risks)",
            bg=COLOR_CARD_BG, fg=COLOR_TEXT_SECONDARY,
            font=(FONT_FAMILY, 10, "italic"), anchor="w"
        ).pack(side="left", padx=10)

        # Row 1: Upload threat threshold + presets
        row1 = tk.Frame(tune_frame, bg=COLOR_CARD_BG)
        row1.pack(fill="x", pady=(0, 8))

        tk.Label(
            row1, text="Upload Threat Limit (MB):",
            bg=COLOR_CARD_BG, fg=COLOR_TEXT_SECONDARY,
            font=(FONT_FAMILY, 10, "bold"), width=22, anchor="w"
        ).pack(side="left")

        current_up = float(self.thresholds.get("high_upload_mb", DEFAULT_ALERT_HIGH_UPLOAD_MB))
        spin_upload = tk.Spinbox(
            row1, from_=1, to=100000, increment=50, width=8,
            font=(FONT_FAMILY, 10),
            bg=COLOR_INPUT_BG, fg=COLOR_TEXT_PRIMARY,
            buttonbackground=COLOR_SIDEBAR_BTN,
            insertbackground="white",
            relief="flat", highlightthickness=1,
            highlightbackground=COLOR_INPUT_BORDER
        )
        spin_upload.delete(0, "end")
        spin_upload.insert(0, str(int(current_up) if current_up.is_integer() else current_up))
        spin_upload.pack(side="left", padx=(0, 15))

        tk.Label(
            row1, text="Presets:", bg=COLOR_CARD_BG,
            fg=COLOR_TEXT_SECONDARY, font=(FONT_FAMILY, 9)
        ).pack(side="left", padx=(0, 5))

        def set_preset_upload(val):
            spin_upload.delete(0, "end")
            spin_upload.insert(0, str(val))
            self.thresholds["high_upload_mb"] = float(val)
            self._save_user_settings()
            self.show_alerts()

        for preset_val in [100, 250, 500, 1000]:
            btn_pre = tk.Button(
                row1, text=f"{preset_val} MB",
                bg=COLOR_ACCENT_PRIMARY if int(current_up) == preset_val else COLOR_SIDEBAR_BTN,
                fg="white" if int(current_up) == preset_val else COLOR_TEXT_PRIMARY,
                activebackground=COLOR_ACCENT_HOVER if int(current_up) == preset_val else COLOR_SIDEBAR_HOVER,
                activeforeground="white",
                font=(FONT_FAMILY, 8, "bold" if int(current_up) == preset_val else "normal"),
                relief="flat", padx=8, pady=2, cursor="hand2",
                command=lambda v=preset_val: set_preset_upload(v)
            )
            btn_pre.pack(side="left", padx=2)

        # Row 2: Secondary thresholds + Apply/Reset
        row2 = tk.Frame(tune_frame, bg=COLOR_CARD_BG)
        row2.pack(fill="x", pady=(2, 0))

        tk.Label(
            row2, text="Max Devices / User:",
            bg=COLOR_CARD_BG, fg=COLOR_TEXT_SECONDARY,
            font=(FONT_FAMILY, 9, "bold"), anchor="w"
        ).pack(side="left")

        spin_dev = tk.Spinbox(
            row2, from_=1, to=50, width=4, font=(FONT_FAMILY, 10),
            bg=COLOR_INPUT_BG, fg=COLOR_TEXT_PRIMARY,
            buttonbackground=COLOR_SIDEBAR_BTN,
            insertbackground="white",
            relief="flat", highlightthickness=1,
            highlightbackground=COLOR_INPUT_BORDER
        )
        spin_dev.delete(0, "end")
        spin_dev.insert(0, str(self.thresholds.get("max_devices_user", DEFAULT_ALERT_MAX_DEVICES_PER_USER)))
        spin_dev.pack(side="left", padx=(5, 15))

        tk.Label(
            row2, text="Blocked Attempts:",
            bg=COLOR_CARD_BG, fg=COLOR_TEXT_SECONDARY,
            font=(FONT_FAMILY, 9, "bold"), anchor="w"
        ).pack(side="left")

        spin_blk = tk.Spinbox(
            row2, from_=1, to=100, width=4, font=(FONT_FAMILY, 10),
            bg=COLOR_INPUT_BG, fg=COLOR_TEXT_PRIMARY,
            buttonbackground=COLOR_SIDEBAR_BTN,
            insertbackground="white",
            relief="flat", highlightthickness=1,
            highlightbackground=COLOR_INPUT_BORDER
        )
        spin_blk.delete(0, "end")
        spin_blk.insert(0, str(self.thresholds.get("blocked_attempts", DEFAULT_ALERT_BLOCKED_ATTEMPTS)))
        spin_blk.pack(side="left", padx=(5, 15))

        tk.Label(
            row2, text="AP Capacity:",
            bg=COLOR_CARD_BG, fg=COLOR_TEXT_SECONDARY,
            font=(FONT_FAMILY, 9, "bold"), anchor="w"
        ).pack(side="left")

        spin_ap = tk.Spinbox(
            row2, from_=1, to=1000, width=5, font=(FONT_FAMILY, 10),
            bg=COLOR_INPUT_BG, fg=COLOR_TEXT_PRIMARY,
            buttonbackground=COLOR_SIDEBAR_BTN,
            insertbackground="white",
            relief="flat", highlightthickness=1,
            highlightbackground=COLOR_INPUT_BORDER
        )
        spin_ap.delete(0, "end")
        spin_ap.insert(0, str(self.thresholds.get("default_ap_capacity", DEFAULT_ALERT_AP_MAX_USERS)))
        spin_ap.pack(side="left", padx=(5, 15))

        def apply_all_thresholds():
            try:
                up_val = float(spin_upload.get().strip())
                dev_val = int(spin_dev.get().strip())
                blk_val = int(spin_blk.get().strip())
                ap_val = int(spin_ap.get().strip())

                if up_val > 0 and dev_val > 0 and blk_val > 0 and ap_val > 0:
                    self.thresholds["high_upload_mb"] = up_val
                    self.thresholds["max_devices_user"] = dev_val
                    self.thresholds["blocked_attempts"] = blk_val
                    self.thresholds["default_ap_capacity"] = ap_val
                    self._save_user_settings()
                    self.show_alerts()
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid numeric values for all threshold fields.")

        def reset_all_alert_thresholds():
            self._reset_user_settings()
            self.show_alerts()

        btn_apply = tk.Button(
            row2, text="⚡ Apply & Recalculate",
            bg=COLOR_ACCENT_PRIMARY, fg="white",
            activebackground=COLOR_ACCENT_HOVER, activeforeground="white",
            font=(FONT_FAMILY, 9, "bold"), relief="flat",
            padx=12, pady=4, cursor="hand2",
            command=apply_all_thresholds
        )
        btn_apply.pack(side="left", padx=(5, 10))

        btn_reset = tk.Button(
            row2, text="🔄 Reset",
            bg=COLOR_SIDEBAR_BTN, fg=COLOR_TEXT_SECONDARY,
            activebackground=COLOR_SIDEBAR_HOVER, activeforeground="white",
            font=(FONT_FAMILY, 9), relief="flat",
            padx=10, pady=4, cursor="hand2",
            command=reset_all_alert_thresholds
        )
        btn_reset.pack(side="left")

        # ── Compute Alerts dynamically ─────────────────────────
        alerts = an.get_all_alerts(df, self.thresholds)
        total  = alerts["total_alerts"]

        up_limit = self.thresholds.get("high_upload_mb", DEFAULT_ALERT_HIGH_UPLOAD_MB)
        dev_limit = self.thresholds.get("max_devices_user", DEFAULT_ALERT_MAX_DEVICES_PER_USER)
        blk_limit = self.thresholds.get("blocked_attempts", DEFAULT_ALERT_BLOCKED_ATTEMPTS)
        ap_limit = self.thresholds.get("default_ap_capacity", DEFAULT_ALERT_AP_MAX_USERS)

        self._page_header(
            f"Alerts  —  {total} flagged entries",
            f"Active Limits: Upload > {up_limit} MB | Devices ≥ {dev_limit} | Blocked > {blk_limit} | AP Cap ≥ {ap_limit}"
        )

        # ── Disclaimer ─────────────────────────────────────────
        disc = tk.Frame(
            self.content, bg=COLOR_CARD_INNER,
            highlightbackground="#1E3A8A", highlightthickness=1,
        )
        disc.pack(fill="x", padx=30, pady=(5, 14))

        tk.Label(
            disc,
            text=(
                "ℹ️  This system identifies unusual network usage patterns using user-configurable thresholds. "
                "It does NOT detect malware or confirm any policy violation. "
                "All flagged entries must be reviewed by a network administrator before taking action."
            ),
            bg=COLOR_CARD_INNER, fg="#93C5FD",
            font=(FONT_FAMILY, 10),
            wraplength=880, justify="left",
            padx=14, pady=10,
        ).pack(anchor="w")

        # ── Alert 1: High Upload ───────────────────────────────
        self._alert_section(
            title="🔴  High Upload Activity (Possible Threat / Exfiltration)",
            severity="high",
            description=(
                f"Individual sessions where Upload_MB > {up_limit} MB. "
                "Possible causes: unauthorized cloud backup, large archive transmission, "
                "file sharing, or potential data exfiltration. "
                "Requires administrator investigation."
            ),
            df_alert=alerts["high_upload"],
        )

        # ── Alert 2: Multiple Devices ──────────────────────────
        self._alert_section(
            title="🟠  Multiple Devices Per User",
            severity="medium",
            description=(
                f"Users connected from {dev_limit} or more "
                "unique devices simultaneously. Possible causes: legitimate "
                "multi-device use or credential sharing. Verify with the user."
            ),
            df_alert=alerts["multi_device"],
        )

        # ── Alert 3: Blocked Site Repeats ──────────────────────
        self._alert_section(
            title="🔴  Repeated Blocked Site Access",
            severity="high",
            description=(
                f"Users who attempted to access blocked websites more than "
                f"{blk_limit} times. May indicate intentional "
                "policy bypass attempts. Consider issuing a policy reminder "
                "or escalating for review."
            ),
            df_alert=alerts["blocked_repeat"],
        )

        # ── Alert 4: Overloaded AP ─────────────────────────────
        self._alert_section(
            title="🟠  Overloaded Access Point",
            severity="medium",
            description=(
                f"Access points where peak simultaneous users reached or exceeded capacity "
                f"(Default: {ap_limit} devices, plus custom AP overrides). Consider load balancing, "
                "adding more APs, or setting connection limits per AP."
            ),
            df_alert=alerts["overloaded_ap"],
        )

        tk.Frame(self.content, bg=COLOR_PAGE_BG, height=30).pack()

    # ==========================================================
    # PAGE 6 — REPORTS
    # ==========================================================

    def show_reports(self):
        """
        Reports page.

        Generates and displays a text-based network summary report
        covering: overview KPIs, top users, AP stats, alert summary,
        configured thresholds, and dataset disclaimer.
        """

        self._page_header(
            "Reports",
            "Auto-generated network summary report from the loaded dataset"
        )

        if self.data is None:
            self._no_data_banner()
            return

        df      = self.data
        summary = an.get_dashboard_summary(df)
        alerts  = an.get_all_alerts(df, self.thresholds)
        top5    = an.get_top_bandwidth_users(df, n=5)
        ap_df   = an.get_ap_summary(df)
        over_df = an.get_ap_overload_status(
            df,
            ap_capacities=self.thresholds.get("ap_capacities"),
            default_capacity=self.thresholds.get("default_ap_capacity")
        )
        fname   = get_filename(self.file_path) if self.file_path else "Unknown"

        up_lim  = self.thresholds.get("high_upload_mb", DEFAULT_ALERT_HIGH_UPLOAD_MB)
        dev_lim = self.thresholds.get("max_devices_user", DEFAULT_ALERT_MAX_DEVICES_PER_USER)
        blk_lim = self.thresholds.get("blocked_attempts", DEFAULT_ALERT_BLOCKED_ATTEMPTS)
        ap_lim  = self.thresholds.get("default_ap_capacity", DEFAULT_ALERT_AP_MAX_USERS)

        # ── Build report text ──────────────────────────────────
        W = 68
        sep = "─" * W

        lines = [
            "=" * W,
            "     Wi-Fi Usage Analyzer — Comprehensive Network Report",
            "=" * W,
            f"  Dataset Source        : {fname}",
            f"  Total Session Records : {df.shape[0]}",
            f"  Total Features/Cols   : {df.shape[1]}",
            "",
            sep,
            "  NETWORK OVERVIEW",
            sep,
            f"  Total Unique Users    : {summary['total_users']}",
            f"  Total Unique Devices  : {summary['total_devices']}",
            f"  Total Upload Bandwidth: {format_bytes(summary['total_upload_mb'])}",
            f"  Total Download Data   : {format_bytes(summary['total_download_mb'])}",
            f"  Peak Activity Hour    : {summary['peak_hour']}",
            "",
            sep,
            "  ACTIVE SECURITY & CAPACITY THRESHOLDS",
            sep,
            f"  Upload Threat Limit   : > {up_lim} MB",
            f"  Max Devices Per User  : >= {dev_lim} devices",
            f"  Blocked Site Tolerance: > {blk_lim} attempts",
            f"  Default AP Max Devices: >= {ap_lim} concurrent devices",
            f"  Custom AP Capacities  : {len(self.thresholds.get('ap_capacities', {}))} AP(s) customized",
            "",
            sep,
            "  TOP 5 BANDWIDTH USERS",
            sep,
        ]

        for _, row in top5.iterrows():
            lines.append(
                f"  {row['Username']:<15} "
                f"↑ {row['Upload_MB']:>9.1f} MB   "
                f"↓ {row['Download_MB']:>9.1f} MB   "
                f"Total: {row['Total_MB']:>9.1f} MB"
            )

        if not ap_df.empty:
            lines += ["", sep, "  ACCESS POINT OVERLOAD & TRAFFIC SUMMARY", sep]
            for _, row in over_df.iterrows():
                flag_mark = "[OVERLOADED]" if row["Status"] == "Overloaded" else ("[WARNING]" if row["Status"] == "Warning" else "[OK]")
                lines.append(
                    f"  {row['Access_Point']:<15} "
                    f"Peak: {int(row['Peak_Users']):>2}/{int(row['Max_Capacity']):<2} dev "
                    f"({row['Utilization_Pct']:>5.1f}%) "
                    f"{flag_mark:<12}"
                )

        lines += [
            "", sep, "  ALERTS & THREAT SUMMARY", sep,
            f"  High Upload Alerts        : {len(alerts['high_upload'])} session(s)",
            f"  Multi-Device Alerts       : {len(alerts['multi_device'])} user(s)",
            f"  Blocked Site Alerts       : {len(alerts['blocked_repeat'])} user(s)",
            f"  Overloaded AP Alerts      : {len(alerts['overloaded_ap'])} AP(s)",
            f"  Total Flagged Anomalies   : {alerts['total_alerts']}",
            "",
            sep, "  DISCLAIMER", sep,
            "  Synthetic dataset created for educational purposes,",
            "  inspired by enterprise Wi-Fi client log structures.",
            "  No real user data was compromised or used.",
            "=" * W,
        ]

        report_text = "\n".join(lines)

        # ── Render in dark terminal-style Text widget ──────────
        rf = tk.Frame(
            self.content, bg=COLOR_CARD_BG,
            highlightbackground=COLOR_CARD_BORDER,
            highlightthickness=1,
        )
        rf.pack(fill="x", padx=30, pady=15)

        txt = tk.Text(
            rf,
            font=("Courier New", 10),
            bg=COLOR_INPUT_BG, fg="#E2E8F0",
            wrap="none", height=44, bd=0,
            padx=18, pady=14,
            insertbackground="white",
        )
        hsb = tk.Scrollbar(rf, orient="horizontal", command=txt.xview)
        txt.configure(xscrollcommand=hsb.set)
        txt.pack(fill="both", expand=True)
        hsb.pack(fill="x")

        txt.insert("1.0", report_text)
        txt.config(state="disabled")

        tk.Frame(self.content, bg=COLOR_PAGE_BG, height=30).pack()

    # ==========================================================
    # PAGE 7 — SETTINGS
    # ==========================================================

    def show_settings(self):
        """
        Settings page.

        Displays:
            - Interactive alert threshold editor with instant save & reset
            - Per-AP capacity management button
            - Loaded dataset information
            - Application details
        """

        self._page_header(
            "Settings",
            "Tune threat alert thresholds, configure AP device capacities, and view application info"
        )

        # ── Interactive Alert Thresholds Form ──────────────────
        self._section_label("Configurable Alert & Capacity Thresholds")

        th_frame = tk.Frame(
            self.content, bg=COLOR_CARD_BG,
            highlightbackground=COLOR_CARD_BORDER,
            highlightthickness=1, padx=20, pady=15,
        )
        th_frame.pack(fill="x", padx=30, pady=5)

        # High Upload Limit
        r1 = tk.Frame(th_frame, bg=COLOR_CARD_BG)
        r1.pack(fill="x", pady=6)
        tk.Label(
            r1, text="High Upload Threat Limit (MB):",
            bg=COLOR_CARD_BG, fg=COLOR_TEXT_PRIMARY,
            font=(FONT_FAMILY, 10, "bold"), width=32, anchor="w"
        ).pack(side="left")
        spin_up = tk.Spinbox(
            r1, from_=1, to=100000, increment=50, width=10, font=(FONT_FAMILY, 10),
            bg=COLOR_INPUT_BG, fg=COLOR_TEXT_PRIMARY,
            buttonbackground=COLOR_SIDEBAR_BTN,
            insertbackground="white",
            relief="flat", highlightthickness=1,
            highlightbackground=COLOR_INPUT_BORDER
        )
        cur_up = float(self.thresholds.get("high_upload_mb", DEFAULT_ALERT_HIGH_UPLOAD_MB))
        spin_up.delete(0, "end")
        spin_up.insert(0, str(int(cur_up) if cur_up.is_integer() else cur_up))
        spin_up.pack(side="left", padx=5)
        tk.Label(
            r1, text="Flag sessions exceeding this upload volume (possible threat/exfiltration)",
            bg=COLOR_CARD_BG, fg=COLOR_TEXT_SECONDARY, font=(FONT_FAMILY, 9)
        ).pack(side="left", padx=10)

        # Default AP Max Capacity
        r2 = tk.Frame(th_frame, bg=COLOR_CARD_BG)
        r2.pack(fill="x", pady=6)
        tk.Label(
            r2, text="Default AP Max Capacity (devices):",
            bg=COLOR_CARD_BG, fg=COLOR_TEXT_PRIMARY,
            font=(FONT_FAMILY, 10, "bold"), width=32, anchor="w"
        ).pack(side="left")
        spin_ap = tk.Spinbox(
            r2, from_=1, to=1000, width=10, font=(FONT_FAMILY, 10),
            bg=COLOR_INPUT_BG, fg=COLOR_TEXT_PRIMARY,
            buttonbackground=COLOR_SIDEBAR_BTN,
            insertbackground="white",
            relief="flat", highlightthickness=1,
            highlightbackground=COLOR_INPUT_BORDER
        )
        spin_ap.delete(0, "end")
        spin_ap.insert(0, str(self.thresholds.get("default_ap_capacity", DEFAULT_ALERT_AP_MAX_USERS)))
        spin_ap.pack(side="left", padx=5)
        tk.Label(
            r2, text="Flag access points exceeding this concurrent device count",
            bg=COLOR_CARD_BG, fg=COLOR_TEXT_SECONDARY, font=(FONT_FAMILY, 9)
        ).pack(side="left", padx=10)

        # Max Devices per User
        r3 = tk.Frame(th_frame, bg=COLOR_CARD_BG)
        r3.pack(fill="x", pady=6)
        tk.Label(
            r3, text="Max Devices per User:",
            bg=COLOR_CARD_BG, fg=COLOR_TEXT_PRIMARY,
            font=(FONT_FAMILY, 10, "bold"), width=32, anchor="w"
        ).pack(side="left")
        spin_dev = tk.Spinbox(
            r3, from_=1, to=50, width=10, font=(FONT_FAMILY, 10),
            bg=COLOR_INPUT_BG, fg=COLOR_TEXT_PRIMARY,
            buttonbackground=COLOR_SIDEBAR_BTN,
            insertbackground="white",
            relief="flat", highlightthickness=1,
            highlightbackground=COLOR_INPUT_BORDER
        )
        spin_dev.delete(0, "end")
        spin_dev.insert(0, str(self.thresholds.get("max_devices_user", DEFAULT_ALERT_MAX_DEVICES_PER_USER)))
        spin_dev.pack(side="left", padx=5)
        tk.Label(
            r3, text="Flag users connected with this many or more devices simultaneously",
            bg=COLOR_CARD_BG, fg=COLOR_TEXT_SECONDARY, font=(FONT_FAMILY, 9)
        ).pack(side="left", padx=10)

        # Blocked Site Attempts
        r4 = tk.Frame(th_frame, bg=COLOR_CARD_BG)
        r4.pack(fill="x", pady=6)
        tk.Label(
            r4, text="Blocked Website Attempts:",
            bg=COLOR_CARD_BG, fg=COLOR_TEXT_PRIMARY,
            font=(FONT_FAMILY, 10, "bold"), width=32, anchor="w"
        ).pack(side="left")
        spin_blk = tk.Spinbox(
            r4, from_=1, to=100, width=10, font=(FONT_FAMILY, 10),
            bg=COLOR_INPUT_BG, fg=COLOR_TEXT_PRIMARY,
            buttonbackground=COLOR_SIDEBAR_BTN,
            insertbackground="white",
            relief="flat", highlightthickness=1,
            highlightbackground=COLOR_INPUT_BORDER
        )
        spin_blk.delete(0, "end")
        spin_blk.insert(0, str(self.thresholds.get("blocked_attempts", DEFAULT_ALERT_BLOCKED_ATTEMPTS)))
        spin_blk.pack(side="left", padx=5)
        tk.Label(
            r4, text="Flag users with repeated blocked URL access attempts",
            bg=COLOR_CARD_BG, fg=COLOR_TEXT_SECONDARY, font=(FONT_FAMILY, 9)
        ).pack(side="left", padx=10)

        # Custom AP Limits Section
        r5 = tk.Frame(th_frame, bg=COLOR_CARD_BG)
        r5.pack(fill="x", pady=10)
        custom_caps = self.thresholds.get("ap_capacities", {})
        tk.Label(
            r5, text="Per-Access Point Custom Limits:",
            bg=COLOR_CARD_BG, fg=COLOR_TEXT_PRIMARY,
            font=(FONT_FAMILY, 10, "bold"), width=32, anchor="w"
        ).pack(side="left")

        caps_info = f"{len(custom_caps)} custom AP limit(s) configured" if custom_caps else "None (all APs use default)"
        tk.Label(
            r5, text=caps_info,
            bg=COLOR_CARD_BG,
            fg=COLOR_TEXT_WARNING if custom_caps else COLOR_TEXT_SECONDARY,
            font=(FONT_FAMILY, 10)
        ).pack(side="left", padx=(5, 15))

        btn_per_ap = tk.Button(
            r5, text="🔧 Manage Per-AP Capacities...",
            bg=COLOR_SIDEBAR_BTN, fg=COLOR_TEXT_PRIMARY,
            activebackground=COLOR_SIDEBAR_HOVER, activeforeground="white",
            font=(FONT_FAMILY, 9, "bold"), relief="flat",
            padx=12, pady=4, cursor="hand2",
            command=self._open_per_ap_modal
        )
        btn_per_ap.pack(side="left")

        # Status feedback label for settings actions
        lbl_feedback = tk.Label(
            th_frame, text="", bg=COLOR_CARD_BG,
            font=(FONT_FAMILY, 9, "bold")
        )
        lbl_feedback.pack(pady=(4, 0))

        # Buttons Row
        btn_row = tk.Frame(th_frame, bg=COLOR_CARD_BG)
        btn_row.pack(fill="x", pady=(10, 0))

        def save_settings_action():
            try:
                up_v  = float(spin_up.get().strip())
                ap_v  = int(spin_ap.get().strip())
                dev_v = int(spin_dev.get().strip())
                blk_v = int(spin_blk.get().strip())

                if up_v <= 0 or ap_v <= 0 or dev_v <= 0 or blk_v <= 0:
                    raise ValueError()

                self.thresholds["high_upload_mb"] = up_v
                self.thresholds["default_ap_capacity"] = ap_v
                self.thresholds["max_devices_user"] = dev_v
                self.thresholds["blocked_attempts"] = blk_v
                self._save_user_settings()

                lbl_feedback.config(
                    text="✅ Settings saved successfully! Changes are applied across all views.",
                    fg=COLOR_TEXT_SUCCESS
                )
            except ValueError:
                lbl_feedback.config(
                    text="❌ Please enter valid positive numbers for all fields.",
                    fg=COLOR_TEXT_DANGER
                )

        def reset_settings_action():
            self._reset_user_settings()
            self.show_settings()

        btn_save = tk.Button(
            btn_row, text="💾 Save Settings",
            bg=COLOR_ACCENT_PRIMARY, fg="white",
            activebackground=COLOR_ACCENT_HOVER, activeforeground="white",
            font=(FONT_FAMILY, 10, "bold"), relief="flat",
            padx=14, pady=6, cursor="hand2",
            command=save_settings_action
        )
        btn_save.pack(side="left", padx=(0, 10))

        btn_reset = tk.Button(
            btn_row, text="🔄 Reset to Defaults",
            bg=COLOR_SIDEBAR_BTN, fg=COLOR_TEXT_SECONDARY,
            activebackground=COLOR_SIDEBAR_HOVER, activeforeground="white",
            font=(FONT_FAMILY, 10), relief="flat",
            padx=14, pady=6, cursor="hand2",
            command=reset_settings_action
        )
        btn_reset.pack(side="left")

        # ── Dataset Info ───────────────────────────────────────
        self._section_label("Loaded Dataset Information")

        ds_frame = tk.Frame(
            self.content, bg=COLOR_CARD_BG,
            highlightbackground=COLOR_CARD_BORDER,
            highlightthickness=1,
        )
        ds_frame.pack(fill="x", padx=30, pady=5)

        if self.data is not None:
            present_opt = ", ".join(self.compat.get("present_optional", []))
            disabled    = ", ".join(self.compat.get("missing_optional", [])) or "None"
            info_rows = [
                ("File",                 get_filename(self.file_path)),
                ("File Size",            get_file_size_kb(self.file_path)),
                ("Rows",                 str(self.data.shape[0])),
                ("Columns",              str(self.data.shape[1])),
                ("Optional cols active", present_opt or "None"),
                ("Disabled features",    disabled),
            ]
        else:
            info_rows = [("Status", "No dataset loaded — use 'Load Dataset' in the sidebar.")]

        for label, value in info_rows:
            r = tk.Frame(ds_frame, bg=COLOR_CARD_BG)
            r.pack(fill="x", padx=20, pady=5)
            tk.Label(r, text=f"{label}:", bg=COLOR_CARD_BG,
                     fg=COLOR_TEXT_SECONDARY,
                     font=(FONT_FAMILY, 10, "bold"),
                     width=25, anchor="w").pack(side="left")
            tk.Label(r, text=value, bg=COLOR_CARD_BG,
                     fg=COLOR_TEXT_PRIMARY,
                     font=(FONT_FAMILY, 10), anchor="w",
                     wraplength=600, justify="left").pack(side="left")

        # ── About ──────────────────────────────────────────────
        self._section_label("About")

        ab_frame = tk.Frame(
            self.content, bg=COLOR_CARD_BG,
            highlightbackground=COLOR_CARD_BORDER,
            highlightthickness=1,
        )
        ab_frame.pack(fill="x", padx=30, pady=5)

        about_rows = [
            ("Application",  APP_TITLE),
            ("Version",      APP_VERSION),
            ("Team",         APP_AUTHOR),
            ("Subject",      "Data Analysis & Engineering — B.Tech Sem 3"),
            ("Dataset Note", "Synthetic dataset. No real user data used."),
        ]

        for label, value in about_rows:
            r = tk.Frame(ab_frame, bg=COLOR_CARD_BG)
            r.pack(fill="x", padx=20, pady=5)
            tk.Label(r, text=f"{label}:", bg=COLOR_CARD_BG,
                     fg=COLOR_TEXT_SECONDARY,
                     font=(FONT_FAMILY, 10, "bold"),
                     width=18, anchor="w").pack(side="left")
            tk.Label(r, text=value, bg=COLOR_CARD_BG,
                     fg=COLOR_TEXT_PRIMARY,
                     font=(FONT_FAMILY, 10), anchor="w").pack(side="left")

        tk.Frame(self.content, bg=COLOR_PAGE_BG, height=30).pack()


# =============================================================
# Run Application Directly
# =============================================================

if __name__ == "__main__":
    app = WiFiUsageAnalyzer()
    app.mainloop()
