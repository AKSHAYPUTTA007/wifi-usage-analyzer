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
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_TEXT_SUCCESS, COLOR_TEXT_WARNING, COLOR_TEXT_DANGER,
    COLOR_ACCENT_BLUE, COLOR_ACCENT_GREEN, COLOR_ACCENT_ORANGE,
    FONT_FAMILY, FONT_HEADING, FONT_SUBHEAD, FONT_BODY,
    FONT_CARD_VAL, FONT_CARD_LBL,
    CHART_FIG_WIDE, CHART_DPI,
    APP_TITLE, APP_VERSION, APP_AUTHOR,
    ALERT_HIGH_UPLOAD_MB, ALERT_MAX_DEVICES_PER_USER,
    ALERT_BLOCKED_ATTEMPTS, ALERT_AP_MAX_USERS,
    COL_ACCESS_POINT, COL_WEBSITE, COL_WEBSITE_CATEGORY, COL_STATUS,
)


# =============================================================
# Global ttk Style
# =============================================================

def _apply_styles():
    """Configure Treeview and Scrollbar styles once at startup."""

    style = ttk.Style()
    style.theme_use("clam")

    style.configure(
        "Treeview",
        background=COLOR_CARD_BG,
        foreground=COLOR_TEXT_PRIMARY,
        rowheight=28,
        fieldbackground=COLOR_CARD_BG,
        font=(FONT_FAMILY, 10),
    )
    style.configure(
        "Treeview.Heading",
        background=COLOR_SIDEBAR_BG,
        foreground="white",
        font=(FONT_FAMILY, 10, "bold"),
        relief="flat",
    )
    style.map(
        "Treeview",
        background=[("selected", COLOR_ACCENT_BLUE)],
        foreground=[("selected", "white")],
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
            fg="#7B9EC0",
            font=(FONT_FAMILY, 8),
            wraplength=210,
            justify="center",
        ).pack(pady=(0, 12))

        # ── Divider ────────────────────────────────────────────
        tk.Frame(self.sidebar, bg="#2C4C72", height=1).pack(
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
                font=(FONT_FAMILY, 11),
                bg=COLOR_SIDEBAR_BTN,
                fg="white",
                bd=0,
                anchor="w",
                padx=18,
                activebackground=COLOR_SIDEBAR_HOVER,
                activeforeground="white",
                cursor="hand2",
                command=lambda pn=page_name, m=method: self._navigate(pn, m),
            )
            btn.pack(fill="x", padx=12, pady=3, ipady=9)
            self.nav_buttons[page_name] = btn

        # ── Divider ────────────────────────────────────────────
        tk.Frame(self.sidebar, bg="#2C4C72", height=1).pack(
            fill="x", padx=15, pady=12
        )

        # ── Load Dataset button ────────────────────────────────
        tk.Button(
            self.sidebar,
            text="📂  Load Dataset",
            font=(FONT_FAMILY, 11, "bold"),
            bg="#22C55E",
            fg="white",
            bd=0,
            padx=18,
            activebackground="#16A34A",
            activeforeground="white",
            cursor="hand2",
            command=self.upload_file,
        ).pack(fill="x", padx=12, pady=3, ipady=9)

        # ── Dataset status label ───────────────────────────────
        self.sidebar_status = tk.Label(
            self.sidebar,
            text="No dataset loaded",
            bg=COLOR_SIDEBAR_BG,
            fg="#7B9EC0",
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
                  col_widths: dict = None, height: int = 12) -> tk.Frame:
        """
        Styled Treeview table with alternating row colors.

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
            tag = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end", values=row, tags=(tag,))

        tree.tag_configure("even", background="#F8FAFC")
        tree.tag_configure("odd",  background="#FFFFFF")

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
            bg="#22C55E", fg="white", bd=0,
            padx=22, pady=10,
            activebackground="#16A34A", activeforeground="white",
            cursor="hand2", command=self.upload_file,
        ).pack()

    def _unavailable_notice(self, missing_col: str):
        """Yellow notice when an optional column is absent."""

        f = tk.Frame(
            self.content, bg="#FEF9C3",
            highlightbackground="#FDE68A", highlightthickness=1,
        )
        f.pack(fill="x", padx=30, pady=10)
        tk.Label(
            f,
            text=f"⚠️  Feature Unavailable — column '{missing_col}' "
                 "not found in this dataset.",
            bg="#FEF9C3", fg="#92400E",
            font=(FONT_FAMILY, 10),
            padx=14, pady=10,
        ).pack(anchor="w")

    def _alert_section(self, title: str, severity: str,
                       description: str, df_alert):
        """
        Render one alert block (title + badge + description + table).

        severity: "high" | "medium" | "low"
        """

        palette = {
            "high":   (COLOR_TEXT_DANGER,  "#FEF2F2", "#FECACA"),
            "medium": (COLOR_TEXT_WARNING, "#FFFBEB", "#FDE68A"),
            "low":    (COLOR_ACCENT_BLUE,  "#EFF6FF", "#BFDBFE"),
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
            ax.set_facecolor("#F8FAFC")

            hours    = hourly_df["Hour"].tolist()
            sessions = hourly_df["Sessions"].tolist()
            peak_idx = sessions.index(max(sessions)) if sessions else 0

            bar_colors = [
                COLOR_TEXT_DANGER if i == peak_idx else COLOR_ACCENT_BLUE
                for i in range(24)
            ]

            ax.bar(hours, sessions, color=bar_colors, alpha=0.85,
                   width=0.75, edgecolor="white")
            ax.set_xlabel("Hour of Day", fontsize=10, color=COLOR_TEXT_SECONDARY)
            ax.set_ylabel("Sessions",    fontsize=10, color=COLOR_TEXT_SECONDARY)
            ax.set_title("Network Sessions by Hour  (red = peak)",
                         fontsize=12, fontweight="bold",
                         color=COLOR_TEXT_PRIMARY, pad=10)
            ax.set_xticks(range(24))
            ax.tick_params(colors=COLOR_TEXT_SECONDARY, labelsize=8)
            ax.spines[["top", "right"]].set_visible(False)
            ax.grid(axis="y", linestyle="--", alpha=0.4)
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
            ax2.set_facecolor("#F8FAFC")

            cats   = cat_df["Website_Category"].tolist()
            dl_mb  = cat_df["Download_MB"].tolist()
            palette = ["#3B82F6", "#22C55E", "#F97316",
                       "#8B5CF6", "#EC4899", "#EF4444"]

            bars = ax2.bar(
                cats, dl_mb,
                color=[palette[i % len(palette)] for i in range(len(cats))],
                alpha=0.85, edgecolor="white",
            )
            ax2.set_ylabel("Download (MB)", fontsize=10, color=COLOR_TEXT_SECONDARY)
            ax2.set_title("Total Download per Website Category",
                          fontsize=12, fontweight="bold",
                          color=COLOR_TEXT_PRIMARY, pad=8)
            ax2.tick_params(colors=COLOR_TEXT_SECONDARY, labelsize=9)
            ax2.spines[["top", "right"]].set_visible(False)
            ax2.grid(axis="y", linestyle="--", alpha=0.4)
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
            - Per-user upload / download / total / sessions table
            - Sessions by device type (pie chart)
            - Devices per user table
        """

        self._page_header(
            "Users",
            "Per-user bandwidth consumption and device usage statistics"
        )

        if self.data is None:
            self._no_data_banner()
            return

        df = self.data

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

            labels  = dev_type_df["Device_Type"].tolist()
            sizes   = dev_type_df["Sessions"].tolist()
            colors  = ["#3B82F6", "#22C55E", "#F97316"]

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
            - Most overloaded / least utilized summary cards
            - AP summary table (users, sessions, bandwidth)
            - Horizontal bar chart of sessions per AP
            - Peak simultaneous users per AP table
        """

        self._page_header(
            "Access Points",
            "Utilization, load analysis and peak concurrent users per AP"
        )

        if self.data is None:
            self._no_data_banner()
            return

        df = self.data

        # Check the required column exists in this dataset
        if not has_column(df, COL_ACCESS_POINT):
            self._unavailable_notice("Access_Point")
            return

        # ── Summary Cards ──────────────────────────────────────
        most_loaded = an.get_most_overloaded_ap(df)
        least_used  = an.get_least_utilized_ap(df)

        self._card_row([
            {"label": "Most Overloaded AP", "value": most_loaded, "color": COLOR_TEXT_DANGER},
            {"label": "Least Utilized AP",  "value": least_used,  "color": COLOR_ACCENT_GREEN},
        ])

        # ── AP Summary Table ───────────────────────────────────
        self._section_label("Access Point Summary")
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
                height=12,
            )
            tbl.pack(fill="x", padx=30, pady=5)

        # ── Sessions Bar Chart (horizontal) ───────────────────
        if not ap_df.empty:
            self._section_label("Sessions per Access Point")
            cf = self._chart_frame()

            fig, ax = plt.subplots(figsize=(9, 4.2), dpi=CHART_DPI)
            fig.patch.set_facecolor(COLOR_CARD_BG)
            ax.set_facecolor("#F8FAFC")

            aps      = ap_df["Access_Point"].tolist()
            sessions = ap_df["Sessions"].tolist()
            bar_colors = [
                COLOR_TEXT_DANGER if a == most_loaded else COLOR_ACCENT_BLUE
                for a in aps
            ]

            # Reverse for top-to-bottom display in horizontal bar
            ax.barh(aps[::-1], sessions[::-1],
                    color=bar_colors[::-1], alpha=0.85, edgecolor="white")
            ax.set_xlabel("Sessions", fontsize=10, color=COLOR_TEXT_SECONDARY)
            ax.set_title("Total Sessions per AP  (red = most overloaded)",
                         fontsize=12, fontweight="bold",
                         color=COLOR_TEXT_PRIMARY, pad=8)
            ax.tick_params(colors=COLOR_TEXT_SECONDARY, labelsize=9)
            ax.spines[["top", "right"]].set_visible(False)
            ax.grid(axis="x", linestyle="--", alpha=0.4)
            fig.tight_layout(pad=1.5)
            self._embed_chart(cf, fig)

        # ── Peak Simultaneous Users Table ──────────────────────
        self._section_label("Peak Simultaneous Users per AP")
        peak_df = an.get_ap_peak_users(df)

        if not peak_df.empty:
            cols = ["Access_Point", "Peak_Users", "Peak_Timestamp"]
            rows = [tuple(r) for _, r in peak_df[cols].iterrows()]
            tbl2 = self._treeview(
                self.content, cols, rows,
                col_widths={"Access_Point": 200, "Peak_Users": 130,
                            "Peak_Timestamp": 220},
                height=12,
            )
            tbl2.pack(fill="x", padx=30, pady=5)

        tk.Frame(self.content, bg=COLOR_PAGE_BG, height=30).pack()

    # ==========================================================
    # PAGE 4 — WEBSITES
    # ==========================================================

    def show_websites(self):
        """
        Websites page.

        Displays:
            - Category breakdown pie chart
            - Top 15 most visited websites table
            - All blocked-access sessions table
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
                wedgeprops={"edgecolor": "white", "linewidth": 2},
                pctdistance=0.80,
            )
            for t in texts:
                t.set_fontsize(9)
            for at in autotexts:
                at.set_fontsize(8)

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

        Runs all four rule-based alert checks and displays results:
            1. High Upload Activity (per session)
            2. Multiple Devices per User
            3. Repeated Blocked Website Access
            4. Overloaded Access Point

        Each section shows: title, count badge, description, table.
        """

        if self.data is None:
            self._page_header("Alerts", "")
            self._no_data_banner()
            return

        df     = self.data
        alerts = an.get_all_alerts(df)
        total  = alerts["total_alerts"]

        self._page_header(
            f"Alerts  —  {total} flagged entries",
            "Rule-based behavioral anomaly detection for administrator investigation"
        )

        # ── Disclaimer ─────────────────────────────────────────
        disc = tk.Frame(
            self.content, bg="#EFF6FF",
            highlightbackground="#BFDBFE", highlightthickness=1,
        )
        disc.pack(fill="x", padx=30, pady=(5, 14))

        tk.Label(
            disc,
            text=(
                "ℹ️  This system identifies unusual network usage patterns. "
                "It does NOT detect malware or confirm any policy violation. "
                "All flagged entries must be reviewed by a network administrator "
                "before any action is taken."
            ),
            bg="#EFF6FF", fg="#1D4ED8",
            font=(FONT_FAMILY, 10),
            wraplength=880, justify="left",
            padx=14, pady=10,
        ).pack(anchor="w")

        # ── Alert 1: High Upload ───────────────────────────────
        self._alert_section(
            title="🔴  High Upload Activity",
            severity="high",
            description=(
                f"Individual sessions where Upload_MB > {ALERT_HIGH_UPLOAD_MB} MB. "
                "Possible causes: cloud backup, large project upload, "
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
                f"Users connected from {ALERT_MAX_DEVICES_PER_USER} or more "
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
                f"{ALERT_BLOCKED_ATTEMPTS} times. May indicate intentional "
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
                f"Access points where peak simultaneous users reached "
                f"{ALERT_AP_MAX_USERS} or more. Consider load balancing, "
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
        and dataset disclaimer.
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
        alerts  = an.get_all_alerts(df)
        top5    = an.get_top_bandwidth_users(df, n=5)
        ap_df   = an.get_ap_summary(df)
        fname   = get_filename(self.file_path) if self.file_path else "Unknown"

        # ── Build report text ──────────────────────────────────
        W = 65
        sep = "─" * W

        lines = [
            "=" * W,
            "    Wi-Fi Usage Analyzer — Network Summary Report",
            "=" * W,
            f"  Dataset       : {fname}",
            f"  Total Records : {df.shape[0]}",
            f"  Columns       : {df.shape[1]}",
            "",
            sep,
            "  NETWORK OVERVIEW",
            sep,
            f"  Total Unique Users   : {summary['total_users']}",
            f"  Total Unique Devices : {summary['total_devices']}",
            f"  Total Upload         : {format_bytes(summary['total_upload_mb'])}",
            f"  Total Download       : {format_bytes(summary['total_download_mb'])}",
            f"  Peak Usage Hour      : {summary['peak_hour']}",
            "",
            sep,
            "  TOP 5 BANDWIDTH USERS",
            sep,
        ]

        for _, row in top5.iterrows():
            lines.append(
                f"  {row['Username']:<14} "
                f"↑ {row['Upload_MB']:>9.1f} MB   "
                f"↓ {row['Download_MB']:>9.1f} MB   "
                f"Total: {row['Total_MB']:>9.1f} MB"
            )

        if not ap_df.empty:
            lines += ["", sep, "  ACCESS POINT SUMMARY", sep]
            for _, row in ap_df.iterrows():
                lines.append(
                    f"  {row['Access_Point']:<18} "
                    f"Users: {int(row['Unique_Users']):<4} "
                    f"Sessions: {int(row['Sessions']):<4} "
                    f"Total: {format_bytes(row['Total_MB'])}"
                )

        lines += [
            "", sep, "  ALERTS SUMMARY", sep,
            f"  High Upload Alerts        : {len(alerts['high_upload'])} sessions",
            f"  Multi-Device Alerts       : {len(alerts['multi_device'])} users",
            f"  Blocked Site Alerts       : {len(alerts['blocked_repeat'])} users",
            f"  Overloaded AP Alerts      : {len(alerts['overloaded_ap'])} APs",
            f"  Total Flagged Entries     : {alerts['total_alerts']}",
            "",
            sep, "  DISCLAIMER", sep,
            "  Synthetic dataset created for educational purposes,",
            "  inspired by publicly documented enterprise Wi-Fi client",
            "  log structures. No real user data was used.",
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
            bg="#1E293B", fg="#E2E8F0",
            wrap="none", height=42, bd=0,
            padx=18, pady=14,
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
            - Loaded dataset info (file, size, rows, column status)
            - Alert threshold values (from config.py)
            - Application info (version, team, purpose)
        """

        self._page_header(
            "Settings",
            "Dataset information, alert thresholds, and application details"
        )

        # ── Dataset Info ───────────────────────────────────────
        self._section_label("Loaded Dataset")

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

        # ── Alert Thresholds ───────────────────────────────────
        self._section_label("Alert Thresholds  (edit in config.py)")

        th_frame = tk.Frame(
            self.content, bg=COLOR_CARD_BG,
            highlightbackground=COLOR_CARD_BORDER,
            highlightthickness=1,
        )
        th_frame.pack(fill="x", padx=30, pady=5)

        thresholds = [
            ("High Upload (per session)",    f"> {ALERT_HIGH_UPLOAD_MB} MB"),
            ("Max Devices per User",         f">= {ALERT_MAX_DEVICES_PER_USER} devices"),
            ("Blocked Site Attempts",        f"> {ALERT_BLOCKED_ATTEMPTS} attempts"),
            ("Max Simultaneous Users / AP",  f">= {ALERT_AP_MAX_USERS} users"),
        ]

        for label, value in thresholds:
            r = tk.Frame(th_frame, bg=COLOR_CARD_BG)
            r.pack(fill="x", padx=20, pady=5)
            tk.Label(r, text=f"{label}:", bg=COLOR_CARD_BG,
                     fg=COLOR_TEXT_SECONDARY,
                     font=(FONT_FAMILY, 10, "bold"),
                     width=32, anchor="w").pack(side="left")
            tk.Label(r, text=value, bg=COLOR_CARD_BG,
                     fg=COLOR_TEXT_WARNING,
                     font=(FONT_FAMILY, 10, "bold"), anchor="w").pack(side="left")

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
