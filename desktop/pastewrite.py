#!/usr/bin/env python3
"""
HumanNature × paste, write. — Unified Master Application (Desktop Edition)
100% faithful visual reproduction of HumanNature's cyber-analog interface,
seamlessly unified with the universal input typist "paste, write.".
"""

import os
import sys
import ctypes
import time
import random
import threading
import subprocess
import re
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import pyperclip

# Ensure Linux BLT library loads seamlessly
_local_blt = os.path.expanduser("~/.local/lib/libBLT.2.5.so.8.6")
if os.path.exists(_local_blt):
    try:
        ctypes.CDLL(_local_blt, mode=ctypes.RTLD_GLOBAL)
    except Exception:
        pass

# Ensure display environment
if "DISPLAY" not in os.environ:
    os.environ["DISPLAY"] = ":0"

if "XAUTHORITY" not in os.environ:
    import glob
    uid = os.getuid() if hasattr(os, "getuid") else 1000
    auths = glob.glob(f"/run/user/{uid}/.*Xwaylandauth*")
    if auths:
        os.environ["XAUTHORITY"] = auths[0]
    elif os.path.exists(os.path.expanduser("~/.Xauthority")):
        os.environ["XAUTHORITY"] = os.path.expanduser("~/.Xauthority")

# Import HumanNature engine components safely
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
CORE_WEB_DIR = PARENT_DIR

# Determine local data cache directory portably
CORE_HN_DIR = os.environ.get("CORE_HN_DIR", "")
if not CORE_HN_DIR:
    scratch_hn = "/home/daniel-sosa/.gemini/antigravity/scratch/HumanNature"
    if os.path.exists(scratch_hn):
        CORE_HN_DIR = scratch_hn
    else:
        CORE_HN_DIR = os.path.expanduser("~/.humannature_cache")
os.makedirs(CORE_HN_DIR, exist_ok=True)

for p in (CORE_WEB_DIR, SCRIPT_DIR, CORE_HN_DIR):
    if p not in sys.path and os.path.exists(p):
        sys.path.insert(0, p)

try:
    from humannature import (
        run_humanizer,
        is_spanish_text,
        open_playground as hn_open_playground,
        open_settings as hn_open_settings,
        get_typo,
    )
except ImportError:
    run_humanizer = None
    is_spanish_text = lambda s: any(w in s.lower() for w in [" el ", " la ", " de ", " que ", " en ", " y "])
    hn_open_playground = None
    hn_open_settings = None
    get_typo = lambda c: 'e'

# ------------------------------------------------------------
# Universal Keystroke Synthesizer (pynput + xdotool fallback)
# ------------------------------------------------------------
_pynput_kb = None
PynputKey = None
try:
    from pynput.keyboard import Controller as PynputController, Key as PKey
    PynputKey = PKey
    _pynput_kb = PynputController()
except Exception:
    pass

def emit_char(c: str) -> bool:
    if c in ("\u2019", "\u2018"):
        c = "'"
    elif c in ("\u201c", "\u201d"):
        c = '"'
    elif c in ("\u2013", "\u2014"):
        c = "-"
    elif c == "\u00a0":
        c = " "

    if _pynput_kb is not None:
        try:
            _pynput_kb.type(c)
            return True
        except Exception:
            pass

    try:
        subprocess.run(["xdotool", "type", "--clearmodifiers", "--", c], check=False, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        pass
    return False

def emit_key(k: str) -> bool:
    if _pynput_kb is not None and PynputKey is not None:
        try:
            if k == "backspace":
                _pynput_kb.press(PynputKey.backspace)
                _pynput_kb.release(PynputKey.backspace)
                return True
            elif k == "enter":
                _pynput_kb.press(PynputKey.enter)
                _pynput_kb.release(PynputKey.enter)
                return True
            elif k == "shift+enter":
                _pynput_kb.press(PynputKey.shift)
                _pynput_kb.press(PynputKey.enter)
                _pynput_kb.release(PynputKey.enter)
                _pynput_kb.release(PynputKey.shift)
                return True
        except Exception:
            pass

    try:
        if k == "backspace":
            subprocess.run(["xdotool", "key", "BackSpace"], check=False, stderr=subprocess.DEVNULL)
        elif k == "enter":
            subprocess.run(["xdotool", "key", "Return"], check=False, stderr=subprocess.DEVNULL)
        elif k == "shift+enter":
            subprocess.run(["xdotool", "key", "Shift+Return"], check=False, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        pass
    return False

# ------------------------------------------------------------
# Keyboard Hotkey Hook
# ------------------------------------------------------------
try:
    import keyboard
except ImportError:
    keyboard = None

# ------------------------------------------------------------
# Modern Cyber-Dark Palette (100% HumanNature Identical)
# ------------------------------------------------------------
C_BG = "#0B0E14"
C_CREAM = "#151922"
C_CHARCOAL = "#F1F5F9"
C_ORANGE = "#06B6D4"      # Glowing Neon Cyan
C_MUTED = "#94A3B8"
C_BORDER = "#1E2433"
C_SURFACE = "#0F121A"
C_ACCENT_ROSE = "#F43F5E"
C_ACCENT_GREEN = "#10B981"
C_BTN_BG = "#1E2433"
C_BTN_HOVER = "#283044"

APP_NAME = "HumanNature × paste, write."
APP_VERSION = "v3.6.0"
APP_TITLE = f"{APP_NAME} {APP_VERSION}"

# ------------------------------------------------------------
# Telemetry and Shared State
# ------------------------------------------------------------
chart_history = []
stats = {
    "keystrokes": 0,
    "typos_fixed": 0,
    "last_key_ms": 0,
}

is_typing = False
is_paused = False


def clean_markdown_text(text: str) -> str:
    if not text:
        return ""
    cleaned = text
    # Normalize typography for Google Docs & Word compatibility
    cleaned = cleaned.replace("“", '"').replace("”", '"')
    cleaned = cleaned.replace("‘", "'").replace("’", "'")
    cleaned = cleaned.replace("—", "-").replace("–", "-")
    cleaned = cleaned.replace("\u00a0", " ")
    cleaned = cleaned.replace("…", "...")
    # Strip markdown syntax that triggers Google Docs warnings or popups
    cleaned = re.sub(r'[*_~`#]', '', cleaned)
    cleaned = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', cleaned)
    cleaned = re.sub(r'^\s*[-*+]\s+', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'^\s*\d+\.\s+', '', cleaned, flags=re.MULTILINE)
    return cleaned


# ============================================================
# Main Application Window
# ============================================================
class UnifiedApp:
    def __init__(self):
        self.root = tk.Tk(className="humannature")
        self.root.title(APP_TITLE)
        
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        init_w = 980
        init_h = 630
        init_x = max(0, (sw - init_w) // 2)
        init_y = max(35, (sh - init_h) // 2)
        self.root.geometry(f"{init_w}x{init_h}+{init_x}+{init_y}")
        self.root.minsize(880, 580)
        self.root.configure(bg=C_BORDER)

        # Frameless styling on Linux/Windows
        try:
            self.root.update_idletasks()
            wid = self.root.winfo_id()
            info = subprocess.check_output(['xwininfo', '-id', str(wid), '-tree'], timeout=1.0).decode()
            client_wid = None
            for line in info.splitlines():
                if 'Parent window id:' in line:
                    client_wid = line.split()[3]
                    break
            if client_wid:
                subprocess.run(['xprop', '-id', client_wid, '-f', '_MOTIF_WM_HINTS', '32c', '-set', '_MOTIF_WM_HINTS', '2, 0, 0, 0, 0'], capture_output=True)
                self.root.withdraw()
                self.root.deiconify()
            else:
                self.root.overrideredirect(True)
        except Exception:
            self.root.overrideredirect(True)

        self.setup_styles()
        self.setup_variables()
        self.build_ui()
        self.bind_hotkeys()

    def setup_styles(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(
            "Horizontal.TScale",
            background=C_CREAM,
            troughcolor=C_SURFACE,
            sliderrelief="flat",
            sliderlength=20,
            sliderthickness=12,
            bordercolor=C_BORDER,
            lightcolor=C_ORANGE,
            darkcolor=C_ORANGE,
        )

        style.configure(
            "TCombobox",
            fieldbackground=C_SURFACE,
            background=C_BTN_BG,
            foreground=C_CHARCOAL,
            darkcolor=C_BORDER,
            lightcolor=C_BORDER,
            bordercolor=C_BORDER,
            arrowcolor=C_ORANGE,
            selectbackground=C_ORANGE,
            selectforeground=C_BG,
            padding=4,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", C_SURFACE)],
            selectbackground=[("readonly", C_ORANGE)],
            selectforeground=[("readonly", C_BG)],
            foreground=[("readonly", C_CHARCOAL)],
        )

    def setup_variables(self):
        self.wpm_var = tk.IntVar(value=72)
        self.acc_var = tk.DoubleVar(value=96.4)
        self.auto_acc_var = tk.BooleanVar(value=True)
        self.start_delay_var = tk.IntVar(value=5)
        self.engine_var = tk.StringVar(value="⚡ HumanizeAI Pro")
        self.use_burst_var = tk.BooleanVar(value=True)
        self.use_fragments_var = tk.BooleanVar(value=True)
        self.use_shift_enter_var = tk.BooleanVar(value=False)
        self.remove_asterisks_var = tk.BooleanVar(value=True)
        self.casual_mode_var = tk.BooleanVar(value=False)
        self.active_mode = "humannature"  # "humannature" or "pastewrite"
        self.always_on_top_var = tk.BooleanVar(value=True)
        self.root.attributes("-topmost", True)

        self.window_state = {
            "is_maximized": False,
            "is_minimized": False,
            "prev_geom": "980x630",
            "prev_x": 100,
            "prev_y": 100,
        }

    # --------------------------------------------------------
    # UI Building
    # --------------------------------------------------------
    def build_ui(self):
        # 1. Custom Title Bar with macOS dots
        self.title_bar = tk.Frame(self.root, bg=C_CREAM, height=35)
        self.title_bar.pack(fill="x", padx=2, pady=(2, 0))

        self.title_bar.bind("<ButtonPress-1>", self.start_move)
        self.title_bar.bind("<ButtonRelease-1>", self.stop_move)
        self.title_bar.bind("<B1-Motion>", self.do_move)
        self.title_bar.bind("<Double-Button-1>", self.toggle_maximize)

        btn_frame = tk.Frame(self.title_bar, bg=C_CREAM)
        btn_frame.pack(side="left", padx=12)

        self.close_icon = tk.Label(btn_frame, text="●", font=("Arial", 11), bg=C_CREAM, fg="#EF4444", cursor="hand2")
        self.close_icon.pack(side="left")

        self.minimize_icon = tk.Label(btn_frame, text="●", font=("Arial", 11), bg=C_CREAM, fg="#F59E0B", cursor="hand2")
        self.minimize_icon.pack(side="left", padx=(6, 0))

        self.expand_icon = tk.Label(btn_frame, text="●", font=("Arial", 11), bg=C_CREAM, fg="#10B981", cursor="hand2")
        self.expand_icon.pack(side="left", padx=(6, 0))

        for w in (btn_frame, self.close_icon, self.minimize_icon, self.expand_icon):
            w.bind("<Enter>", self.on_btns_enter)
            w.bind("<Leave>", self.on_btns_leave)

        self.close_icon.bind("<Button-1>", lambda e: self.quit_app())
        self.minimize_icon.bind("<Button-1>", lambda e: self.minimize_window())
        self.expand_icon.bind("<Button-1>", lambda e: self.toggle_maximize())

        tk.Label(
            self.title_bar,
            text=f"desktop — humannature × paste, write. {APP_VERSION} analog",
            font=("Consolas", 9),
            bg=C_CREAM,
            fg=C_MUTED,
        ).pack(side="left", expand=True)

        self.clock_label = tk.Label(self.title_bar, text="", font=("Consolas", 9), bg=C_CREAM, fg=C_MUTED)
        self.clock_label.pack(side="right", padx=10)
        self.update_clock()

        self.pin_btn = tk.Label(self.title_bar, text="📌", font=("Arial", 9), bg=C_CREAM, fg=C_ORANGE, cursor="hand2")
        self.pin_btn.pack(side="right", padx=(0, 4))
        self.pin_btn.bind("<Button-1>", self.toggle_top)

        # 2. Sleek Cyber Mode Switcher Bar
        self.mode_switcher_bar = tk.Frame(self.root, bg=C_BG, height=36)
        self.mode_switcher_bar.pack(fill="x", padx=2, pady=0)

        self.btn_mode_hn = tk.Button(
            self.mode_switcher_bar,
            text="⚡  HUMANNATURE STUDIO",
            font=("Consolas", 9, "bold"),
            bg=C_BTN_BG,
            fg=C_ORANGE,
            activebackground=C_BTN_HOVER,
            activeforeground=C_ORANGE,
            relief="flat",
            padx=16,
            pady=4,
            cursor="hand2",
            command=lambda: self.switch_mode("humannature")
        )
        self.btn_mode_hn.pack(side="left", padx=(18, 4), pady=4)

        self.btn_mode_pw = tk.Button(
            self.mode_switcher_bar,
            text="📋  PASTE, WRITE. (UNIVERSAL)",
            font=("Consolas", 9, "bold"),
            bg=C_SURFACE,
            fg=C_MUTED,
            activebackground=C_BTN_HOVER,
            activeforeground=C_CHARCOAL,
            relief="flat",
            padx=16,
            pady=4,
            cursor="hand2",
            command=lambda: self.switch_mode("pastewrite")
        )
        self.btn_mode_pw.pack(side="left", padx=4, pady=4)

        tk.Label(
            self.mode_switcher_bar,
            text="● UNIFIED SUITE",
            font=("Consolas", 8, "bold"),
            bg=C_BG,
            fg=C_ACCENT_GREEN
        ).pack(side="right", padx=24)

        # 3. Main Container
        self.body = tk.Frame(self.root, bg=C_CREAM)
        self.body.pack(fill="both", expand=True, padx=2, pady=2)

        # Left Container (Houses either HumanNature or paste, write.)
        self.left_container = tk.Frame(self.body, bg=C_CREAM, width=540)
        self.left_container.pack(side="left", fill="both", expand=True, padx=(18, 10), pady=12)
        self.left_container.pack_propagate(False)

        # Build Panels
        self.hn_panel = tk.Frame(self.left_container, bg=C_CREAM)
        self.pw_panel = tk.Frame(self.left_container, bg=C_CREAM)

        self.build_humannature_panel()
        self.build_pastewrite_panel()

        # Shared Right Panel (Always visible, 100% HumanNature Identical)
        self.right_panel = tk.Frame(self.body, bg=C_CREAM, width=380)
        self.right_panel.pack(side="right", fill="both", expand=True, padx=(10, 18), pady=12)
        self.build_right_panel()

        # Show default mode
        self.switch_mode("humannature")

        # Initial clipboard essay check
        self.root.after(300, self.load_initial_essay)

    # --------------------------------------------------------
    # Mode Switcher Handler
    # --------------------------------------------------------
    def switch_mode(self, mode: str):
        self.active_mode = mode
        if mode == "humannature":
            self.pw_panel.pack_forget()
            self.hn_panel.pack(fill="both", expand=True)
            self.btn_mode_hn.config(bg=C_BTN_BG, fg=C_ORANGE)
            self.btn_mode_pw.config(bg=C_SURFACE, fg=C_MUTED)
            self.log_terminal("[Mode] Activado HumanNature Studio (Ensayos, Presets y NLP)")
        else:
            self.hn_panel.pack_forget()
            self.pw_panel.pack(fill="both", expand=True)
            self.btn_mode_pw.config(bg=C_BTN_BG, fg=C_ORANGE)
            self.btn_mode_hn.config(bg=C_SURFACE, fg=C_MUTED)
            self.log_terminal("[Mode] Activado paste, write. (Universal Input Typist con directivas)")

    # --------------------------------------------------------
    # HumanNature Studio Left Panel (Authentic 1:1)
    # --------------------------------------------------------
    def build_humannature_panel(self):
        p = self.hn_panel

        title_row = tk.Frame(p, bg=C_CREAM)
        title_row.pack(fill="x")

        tk.Label(
            title_row,
            text="HumanNature v3.6.0",
            font=("Georgia", 20, "bold"),
            bg=C_CREAM,
            fg=C_CHARCOAL
        ).pack(side="left")

        tk.Label(
            title_row,
            text="● AI HUMANIZER",
            font=("Consolas", 8, "bold"),
            bg=C_CREAM,
            fg=C_ORANGE
        ).pack(side="right", pady=(6, 0))

        # Quick Presets Bar
        preset_header = tk.Frame(p, bg=C_CREAM)
        preset_header.pack(fill="x", pady=(8, 2))

        tk.Label(
            preset_header,
            text="QUICK PRESETS",
            font=("Consolas", 8, "bold"),
            bg=C_CREAM,
            fg=C_MUTED
        ).pack(side="left")

        presets_bar = tk.Frame(p, bg=C_CREAM)
        presets_bar.pack(fill="x", pady=(0, 4))

        preset_configs = [
            ("Formal", 55, 98.5, "🎓 Academic Master", False, False, 3),
            ("Casual", 85, 94.0, "🌊 Natural Flow", True, True, 2),
            ("Español", 72, 95.5, "⚡ HumanizeAI Pro", True, True, 3),
            ("Essay", 62, 97.0, "🎓 Academic Master", True, True, 4),
            ("Coder", 95, 99.2, "⚡ HumanizeAI Pro", False, False, 2),
            ("Turbo", 120, 91.0, "⚡ HumanizeAI Pro", True, False, 1),
            ("Stealth", 68, 96.5, "👻 GhostWriter Ultra", True, True, 4),
        ]

        for p_name, p_wpm, p_acc, p_eng, p_burst, p_frag, p_delay in preset_configs:
            tk.Button(
                presets_bar,
                text=p_name,
                font=("Consolas", 8, "bold"),
                bg=C_BTN_BG,
                fg=C_CHARCOAL,
                activebackground=C_BTN_HOVER,
                activeforeground=C_ORANGE,
                relief="flat",
                padx=4,
                pady=2,
                cursor="hand2",
                command=lambda n=p_name, w=p_wpm, a=p_acc, e=p_eng, b=p_burst, f=p_frag, d=p_delay: self.apply_preset(n, w, a, e, b, f, d)
            ).pack(side="left", expand=True, fill="x", padx=1)

        # Target Speed
        tk.Label(p, text="TARGET SPEED (WPM)", font=("Consolas", 8, "bold"), bg=C_CREAM, fg=C_MUTED).pack(anchor="w", pady=(2, 0))
        self.wpm_slider = ttk.Scale(p, from_=30, to=150, orient="horizontal", variable=self.wpm_var, command=self.on_wpm_change)
        self.wpm_slider.pack(fill="x", pady=2)

        # Accuracy
        acc_frame = tk.Frame(p, bg=C_CREAM)
        acc_frame.pack(fill="x", pady=(2, 0))
        tk.Label(acc_frame, text="ACCURACY RATE (%)", font=("Consolas", 8, "bold"), bg=C_CREAM, fg=C_MUTED).pack(side="left")
        self.acc_display = tk.Label(acc_frame, text="96.4%", font=("Consolas", 8, "bold"), bg=C_CREAM, fg=C_ORANGE)
        self.acc_display.pack(side="right")

        self.acc_slider = ttk.Scale(p, from_=85.0, to=100.0, orient="horizontal", variable=self.acc_var, command=self.on_acc_change)
        self.acc_slider.pack(fill="x", pady=2)

        tk.Checkbutton(
            p,
            text="Auto-adjust accuracy based on speed",
            variable=self.auto_acc_var,
            bg=C_CREAM,
            font=("Consolas", 8),
            fg=C_MUTED,
            selectcolor=C_SURFACE,
            activebackground=C_CREAM,
            activeforeground=C_CHARCOAL,
            highlightthickness=0,
            command=self.toggle_auto_acc,
        ).pack(anchor="w", pady=(0, 2))
        self.acc_slider.config(state="disabled")

        # Start Delay (Countdown)
        delay_frame = tk.Frame(p, bg=C_CREAM)
        delay_frame.pack(fill="x", pady=(2, 0))
        tk.Label(delay_frame, text="START DELAY (COUNTDOWN)", font=("Consolas", 8, "bold"), bg=C_CREAM, fg=C_MUTED).pack(side="left")
        self.delay_display = tk.Label(delay_frame, text="5s", font=("Consolas", 8, "bold"), bg=C_CREAM, fg=C_ORANGE)
        self.delay_display.pack(side="right")

        self.delay_slider = ttk.Scale(p, from_=0, to=10, orient="horizontal", variable=self.start_delay_var, command=lambda v: self.delay_display.config(text=f"{int(float(v))}s"))
        self.delay_slider.pack(fill="x", pady=2)

        # NLP Engine
        tk.Label(p, text="NLP ENGINE", font=("Consolas", 8, "bold"), bg=C_CREAM, fg=C_MUTED).pack(anchor="w", pady=(2, 0))
        self.eng_combo = ttk.Combobox(
            p,
            textvariable=self.engine_var,
            values=["⚡ HumanizeAI Pro", "🎓 Academic Master", "👻 GhostWriter Ultra", "🌊 Natural Flow"],
            state="readonly",
            font=("Consolas", 9)
        )
        self.eng_combo.pack(fill="x", pady=2)

        # Typing Options
        t_frame = tk.Frame(p, bg=C_CREAM)
        t_frame.pack(fill="x", pady=2)
        tk.Checkbutton(t_frame, text="Cognitive Burst", variable=self.use_burst_var, bg=C_CREAM, fg=C_CHARCOAL, font=("Consolas", 8), selectcolor=C_SURFACE, activebackground=C_CREAM, activeforeground=C_CHARCOAL, highlightthickness=0).pack(side="left")
        tk.Checkbutton(t_frame, text="Fragment Mode", variable=self.use_fragments_var, bg=C_CREAM, fg=C_CHARCOAL, font=("Consolas", 8), selectcolor=C_SURFACE, activebackground=C_CREAM, activeforeground=C_CHARCOAL, highlightthickness=0).pack(side="left", padx=10)

        # Action Buttons
        act_row1 = tk.Frame(p, bg=C_CREAM)
        act_row1.pack(fill="x", pady=(4, 2))

        self.start_btn = tk.Button(act_row1, text="▶ START (F9)", font=("Consolas", 8, "bold"), bg="#0E7490", fg="#ECFEFF", activebackground="#0891B2", activeforeground="#FFFFFF", relief="flat", pady=5, cursor="hand2", command=self.trigger_start)
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 2))

        self.pause_btn = tk.Button(act_row1, text="⏸  PAUSE (F8)", font=("Consolas", 8, "bold"), bg="#334155", fg="#F1F5F9", activebackground="#475569", activeforeground="#FFFFFF", relief="flat", pady=5, cursor="hand2", command=self.trigger_pause)
        self.pause_btn.pack(side="left", fill="x", expand=True, padx=2)

        self.stop_btn = tk.Button(act_row1, text="⏹ STOP (F10)", font=("Consolas", 8, "bold"), bg="#881337", fg="#FFE4E6", activebackground="#9F1239", activeforeground="#FFFFFF", relief="flat", pady=5, cursor="hand2", command=self.trigger_stop)
        self.stop_btn.pack(side="right", fill="x", expand=True, padx=(2, 0))

        # Essay Clipboard Button
        tk.Button(
            p,
            text="📥  PEGAR / DETECTAR ESSAY (CLIPBOARD)",
            font=("Consolas", 8, "bold"),
            bg="#1E293B",
            fg="#38BDF8",
            activebackground="#334155",
            activeforeground="#38BDF8",
            relief="flat",
            pady=4,
            cursor="hand2",
            command=self.load_clipboard_essay,
        ).pack(fill="x", pady=2)

        # Secondary Actions: Playground, Settings & Transfer to Typist
        act_row2 = tk.Frame(p, bg=C_CREAM)
        act_row2.pack(fill="x", pady=2)

        tk.Button(act_row2, text="🧪 PLAYGROUND", font=("Consolas", 8, "bold"), bg=C_BTN_BG, fg=C_ORANGE, activebackground=C_BTN_HOVER, activeforeground="#22D3EE", relief="flat", pady=4, cursor="hand2", command=self.open_playground).pack(side="left", fill="x", expand=True, padx=(0, 2))
        tk.Button(act_row2, text="⚙ SETTINGS", font=("Consolas", 8, "bold"), bg=C_BTN_BG, fg=C_CHARCOAL, activebackground=C_BTN_HOVER, activeforeground=C_ORANGE, relief="flat", pady=4, cursor="hand2", command=self.open_settings).pack(side="left", fill="x", expand=True, padx=2)
        tk.Button(act_row2, text="🚀 ENVIAR A PASTE, WRITE", font=("Consolas", 8, "bold"), bg="#155E75", fg="#ECFEFF", activebackground="#0E7490", activeforeground="#FFFFFF", relief="flat", pady=4, cursor="hand2", command=self.transfer_to_pastewrite).pack(side="right", fill="x", expand=True, padx=(2, 0))

        # Terminal
        self.hn_terminal = tk.Text(p, height=4, bg=C_SURFACE, fg="#E2E8F0", font=("Consolas", 8), relief="flat", padx=8, pady=4, highlightbackground="#1E2433", highlightthickness=1, state="disabled")
        self.hn_terminal.pack(fill="x", pady=(2, 0))

    # --------------------------------------------------------
    # paste, write. Left Panel (Universal Typist with Directives)
    # --------------------------------------------------------
    def build_pastewrite_panel(self):
        p = self.pw_panel

        title_row = tk.Frame(p, bg=C_CREAM)
        title_row.pack(fill="x")

        tk.Label(
            title_row,
            text="paste, write.",
            font=("Georgia", 20, "bold"),
            bg=C_CREAM,
            fg=C_CHARCOAL
        ).pack(side="left")

        tk.Label(
            title_row,
            text="● UNIVERSAL TYPIST",
            font=("Consolas", 8, "bold"),
            bg=C_CREAM,
            fg=C_ORANGE
        ).pack(side="right", pady=(6, 0))

        # Helper chips and sample buttons
        top_bar = tk.Frame(p, bg=C_CREAM)
        top_bar.pack(fill="x", pady=(4, 2))

        tk.Button(top_bar, text="📥 Pegar (Ctrl+V)", font=("Consolas", 8, "bold"), bg=C_BTN_BG, fg="#38BDF8", activebackground=C_BTN_HOVER, relief="flat", padx=6, pady=2, cursor="hand2", command=self.pw_paste_clipboard).pack(side="left", padx=(0, 4))
        tk.Button(top_bar, text="🧹 Limpiar", font=("Consolas", 8), bg=C_BTN_BG, fg=C_MUTED, activebackground=C_BTN_HOVER, relief="flat", padx=6, pady=2, cursor="hand2", command=self.pw_clear_editor).pack(side="left", padx=2)

        sample_frame = tk.Frame(top_bar, bg=C_CREAM)
        sample_frame.pack(side="right")
        tk.Label(sample_frame, text="Muestras:", font=("Consolas", 7), bg=C_CREAM, fg=C_MUTED).pack(side="left", padx=2)
        for s_name, s_txt in [
            ("Ensayo", "La tecnología y la inteligencia artificial redefinen la sociedad actual."),
            ("Python", "def saludar():\n    print('¡Hola desde paste, write!')"),
            ("Chat", "Buenas tardes profesor, le envío el archivo correspondiente al módulo 4.")
        ]:
            tk.Button(sample_frame, text=s_name, font=("Consolas", 7), bg=C_SURFACE, fg=C_CHARCOAL, activebackground=C_BTN_HOVER, relief="flat", padx=3, pady=1, cursor="hand2", command=lambda t=s_txt: self.pw_set_text(t)).pack(side="left", padx=1)

        # Editor Text Box
        self.pw_editor = tk.Text(
            p,
            height=9,
            bg=C_SURFACE,
            fg="#F8FAFC",
            font=("Consolas", 9),
            relief="flat",
            padx=10,
            pady=8,
            insertbackground=C_ORANGE,
            highlightbackground="#1E2433",
            highlightthickness=1,
            wrap="word"
        )
        self.pw_editor.pack(fill="x", pady=2)
        self.pw_editor.bind("<KeyRelease>", self.pw_update_stats)

        # Stats Bar (Characters, Words, Lines)
        self.pw_stats_lbl = tk.Label(p, text="0 caracteres • 0 palabras • 0 líneas", font=("Consolas", 7), bg=C_CREAM, fg=C_MUTED)
        self.pw_stats_lbl.pack(anchor="w", pady=(1, 3))

        # Directives Bar
        tk.Label(p, text="¿CÓMO QUIERES QUE LO ESCRIBA? (DIRECTIVAS)", font=("Consolas", 8, "bold"), bg=C_CREAM, fg=C_ORANGE).pack(anchor="w", pady=(2, 2))
        dir_frame = tk.Frame(p, bg=C_CREAM)
        dir_frame.pack(fill="x", pady=(0, 4))

        directives = [
            ("🎯 Tal cual (Exacto)", "exacto"),
            ("🛡️ Docs Stealth", "stealth"),
            ("🎓 Más formal", "formal"),
            ("🌊 Más natural", "casual"),
            ("💻 Código limpio", "code"),
            ("Sin Markdown", "clean_markdown"),
        ]

        for d_label, d_code in directives:
            tk.Button(
                dir_frame,
                text=d_label,
                font=("Consolas", 7, "bold"),
                bg=C_BTN_BG,
                fg=C_CHARCOAL,
                activebackground=C_BTN_HOVER,
                activeforeground=C_ORANGE,
                relief="flat",
                padx=4,
                pady=2,
                cursor="hand2",
                command=lambda c=d_code, l=d_label: self.pw_apply_directive(c, l)
            ).pack(side="left", expand=True, fill="x", padx=1)

        # Toggles
        togg_frame = tk.Frame(p, bg=C_CREAM)
        togg_frame.pack(fill="x", pady=2)

        tk.Checkbutton(togg_frame, text="Usar Shift + Enter (Chats / Slack / Discord)", variable=self.use_shift_enter_var, bg=C_CREAM, fg=C_CHARCOAL, font=("Consolas", 8), selectcolor=C_SURFACE, activebackground=C_CREAM, activeforeground=C_CHARCOAL, highlightthickness=0).pack(side="left")
        tk.Checkbutton(togg_frame, text="Bloquear avisos Markdown en Docs", variable=self.remove_asterisks_var, bg=C_CREAM, fg=C_CHARCOAL, font=("Consolas", 8), selectcolor=C_SURFACE, activebackground=C_CREAM, activeforeground=C_CHARCOAL, highlightthickness=0).pack(side="left", padx=10)

        # Action Buttons
        pw_act = tk.Frame(p, bg=C_CREAM)
        pw_act.pack(fill="x", pady=(4, 2))

        tk.Button(pw_act, text="▶ ESCRIBIR AHORA (F9)", font=("Consolas", 8, "bold"), bg="#0E7490", fg="#ECFEFF", activebackground="#0891B2", activeforeground="#FFFFFF", relief="flat", pady=5, cursor="hand2", command=self.trigger_start).pack(side="left", fill="x", expand=True, padx=(0, 2))
        tk.Button(pw_act, text="⏸  PAUSA (F8)", font=("Consolas", 8, "bold"), bg="#334155", fg="#F1F5F9", activebackground="#475569", activeforeground="#FFFFFF", relief="flat", pady=5, cursor="hand2", command=self.trigger_pause).pack(side="left", fill="x", expand=True, padx=2)
        tk.Button(pw_act, text="⏹ DETENER (F10)", font=("Consolas", 8, "bold"), bg="#881337", fg="#FFE4E6", activebackground="#9F1239", activeforeground="#FFFFFF", relief="flat", pady=5, cursor="hand2", command=self.trigger_stop).pack(side="right", fill="x", expand=True, padx=(2, 0))

        # Terminal
        self.pw_terminal = tk.Text(p, height=3, bg=C_SURFACE, fg="#E2E8F0", font=("Consolas", 8), relief="flat", padx=8, pady=4, highlightbackground="#1E2433", highlightthickness=1, state="disabled")
        self.pw_terminal.pack(fill="x", pady=(2, 0))

    # --------------------------------------------------------
    # Shared Right Panel (Big 52pt WPM, Oscilloscope & HUD)
    # --------------------------------------------------------
    def build_right_panel(self):
        p = self.right_panel

        stats_frame = tk.Frame(p, bg=C_CREAM)
        stats_frame.pack(fill="x", anchor="e")

        self.wpm_display = tk.Label(stats_frame, text="72", font=("Consolas", 52, "bold"), bg=C_CREAM, fg=C_ORANGE)
        self.wpm_display.pack(side="left")

        tk.Label(stats_frame, text="WPM\nMEASURED", font=("Consolas", 8, "bold"), bg=C_CREAM, fg=C_MUTED, justify="left").pack(side="left", padx=(5, 0), pady=(25, 0))

        self.status_label = tk.Label(p, text="● Status: standing by", font=("Consolas", 10, "bold"), bg=C_CREAM, fg=C_ORANGE)
        self.status_label.pack(anchor="w", pady=(8, 0))

        tk.Label(p, text="TIME BETWEEN KEYS • LAST 65", font=("Consolas", 8, "bold"), bg=C_CREAM, fg=C_MUTED).pack(anchor="w", pady=(12, 4))

        self.chart_canvas = tk.Canvas(p, height=80, bg=C_SURFACE, highlightbackground="#1E2433", highlightthickness=1)
        self.chart_canvas.pack(fill="x")

        r_frame = tk.Frame(p, bg=C_CREAM)
        r_frame.pack(fill="x", pady=10)

        def mk_stat(parent, label_text):
            f = tk.Frame(parent, bg=C_SURFACE, highlightbackground="#1E2433", highlightthickness=1, padx=12, pady=4)
            f.pack(fill="x", pady=2)
            tk.Label(f, text=label_text.upper(), font=("Consolas", 8, "bold"), bg=C_SURFACE, fg=C_MUTED).pack(side="left")
            val = tk.Label(f, text="0", font=("Consolas", 9, "bold"), bg=C_SURFACE, fg=C_CHARCOAL)
            val.pack(side="right")
            return val

        self.last_lbl = mk_stat(r_frame, "last key")
        self.key_lbl = mk_stat(r_frame, "keystrokes")
        self.typo_lbl = mk_stat(r_frame, "typos fixed")

        self.telemetry_label = tk.Label(p, text="> status: standing by", font=("Consolas", 8), bg=C_CREAM, fg=C_ORANGE, anchor="w")
        self.telemetry_label.pack(fill="x", pady=(4, 0))

    # --------------------------------------------------------
    # Telemetry and HUD Rendering (Exact HumanNature Algorithm)
    # --------------------------------------------------------
    def update_hud(self, delay_ms: int, is_spike: bool, is_typo: bool = False, is_char: bool = False):
        if is_char:
            stats["keystrokes"] += 1
        if is_typo:
            stats["typos_fixed"] += 1
        stats["last_key_ms"] = delay_ms

        chart_history.append((delay_ms, is_spike))
        if len(chart_history) > 65:
            chart_history.pop(0)

    def render_telemetry(self):
        self.key_lbl.config(text=str(stats["keystrokes"]))
        self.typo_lbl.config(text=str(stats["typos_fixed"]))
        self.last_lbl.config(text=f"{stats['last_key_ms']} ms")

        self.chart_canvas.delete("all")
        w = max(240, self.chart_canvas.winfo_width())
        h = max(70, self.chart_canvas.winfo_height())
        bar_w = 3
        spacing = 2
        x = w - bar_w

        for delay, is_spike in reversed(chart_history):
            if is_spike:
                bar_h = min(h * 0.95, max(h * 0.5, (delay / 2500) * h))
                color = C_ACCENT_ROSE
            else:
                bar_h = min(h * 0.4, max(4, (delay / 300) * (h * 0.4)))
                color = C_ORANGE

            y1 = h - bar_h
            y2 = h
            self.chart_canvas.create_rectangle(x, y1, x + bar_w, y2, fill=color, outline="")
            x -= (bar_w + spacing)
            if x < 0:
                break

    # --------------------------------------------------------
    # Terminal Logging
    # --------------------------------------------------------
    def log_terminal(self, text: str):
        for term in (self.hn_terminal, self.pw_terminal):
            try:
                term.config(state="normal")
                term.insert("end", f"> {text}\n")
                term.see("end")
                term.config(state="disabled")
            except Exception:
                pass

    # --------------------------------------------------------
    # Window Actions & Dragging
    # --------------------------------------------------------
    def start_move(self, event):
        self.root.x = event.x
        self.root.y = event.y

    def stop_move(self, event):
        self.root.x = None
        self.root.y = None

    def do_move(self, event):
        if self.window_state["is_maximized"]:
            self.toggle_maximize()
            return
        if hasattr(self.root, "x") and self.root.x is not None:
            deltax = event.x - self.root.x
            deltay = event.y - self.root.y
            x = self.root.winfo_x() + deltax
            y = self.root.winfo_y() + deltay
            self.root.geometry(f"+{x}+{y}")

    def toggle_maximize(self, event=None):
        if self.window_state["is_maximized"]:
            self.root.geometry(f"{self.window_state['prev_geom']}+{self.window_state['prev_x']}+{self.window_state['prev_y']}")
            self.window_state["is_maximized"] = False
            self.expand_icon.config(fg="#10B981")
        else:
            self.window_state["prev_geom"] = f"{self.root.winfo_width()}x{self.root.winfo_height()}"
            self.window_state["prev_x"] = max(0, self.root.winfo_x())
            self.window_state["prev_y"] = max(32, self.root.winfo_y())
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            self.root.geometry(f"{sw}x{sh - 32}+0+32")
            self.window_state["is_maximized"] = True
            self.expand_icon.config(fg="#34D399")

    def minimize_window(self, event=None):
        try:
            self.root.iconify()
        except Exception:
            try:
                self.root.withdraw()
            except Exception:
                pass

    def quit_app(self):
        try:
            if keyboard:
                keyboard.unhook_all()
        except Exception:
            pass
        self.root.destroy()
        os._exit(0)

    def toggle_top(self, event=None):
        val = not self.always_on_top_var.get()
        self.always_on_top_var.set(val)
        self.root.attributes("-topmost", val)
        self.pin_btn.config(fg=C_ORANGE if val else C_MUTED)
        self.log_terminal(f"[System] Always-on-top: {'Enabled' if val else 'Disabled'}")

    def on_btns_enter(self, evt=None):
        self.close_icon.config(text="✕", font=("Consolas", 9, "bold"))
        self.minimize_icon.config(text="−", font=("Consolas", 9, "bold"))
        self.expand_icon.config(text="⤢" if not self.window_state["is_maximized"] else "⤡", font=("Consolas", 8, "bold"))

    def on_btns_leave(self, evt=None):
        self.close_icon.config(text="●", font=("Arial", 11))
        self.minimize_icon.config(text="●", font=("Arial", 11))
        self.expand_icon.config(text="●", font=("Arial", 11))

    def update_clock(self):
        self.clock_label.config(text=datetime.now().strftime("%I:%M %p"))
        self.root.after(1000, self.update_clock)

    # --------------------------------------------------------
    # Control Handlers (Presets, Sliders, Dialogs)
    # --------------------------------------------------------
    def on_wpm_change(self, v):
        w = int(float(v))
        self.wpm_display.config(text=str(w))
        if self.auto_acc_var.get():
            # Linear decay from 99.0% at 30 WPM down to 91.0% at 150 WPM
            calc_acc = max(88.0, min(99.5, 99.0 - ((w - 30) / 120.0) * 8.0))
            self.acc_var.set(calc_acc)
            self.acc_display.config(text=f"{calc_acc:.1f}%")

    def on_acc_change(self, v):
        self.acc_display.config(text=f"{float(v):.1f}%")

    def toggle_auto_acc(self):
        if self.auto_acc_var.get():
            self.acc_slider.config(state="disabled")
            self.on_wpm_change(self.wpm_var.get())
        else:
            self.acc_slider.config(state="normal")

    def apply_preset(self, name, wpm, acc, engine, burst, fragments, delay=3):
        self.wpm_var.set(wpm)
        self.wpm_display.config(text=str(wpm))
        self.auto_acc_var.set(False)
        self.acc_slider.config(state="normal")
        self.acc_var.set(acc)
        self.acc_display.config(text=f"{acc:.1f}%")
        self.engine_var.set(engine)
        self.use_burst_var.set(burst)
        self.use_fragments_var.set(fragments)
        self.start_delay_var.set(delay)
        self.delay_display.config(text=f"{delay}s")
        self.log_terminal(f"[Preset] Aplicado {name}: {wpm} WPM • {acc}% Acc • {engine.split()[-1]}")

    def load_initial_essay(self):
        cache_file = os.path.join(CORE_HN_DIR, "last_essay.txt")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    txt = f.read().strip()
                if txt:
                    words = len(txt.split())
                    self.status_label.config(text=f"● Ensayo listo: {words} palabras", fg="#10B981")
                    self.telemetry_label.config(text=f"> essay ready: {words} words in memory")
                    self.log_terminal(f"[Essay] Ensayo restaurado: {words} palabras ({len(txt)} caracteres).")
            except Exception:
                pass

    def load_clipboard_essay(self):
        txt = ""
        try:
            txt = pyperclip.paste()
        except Exception:
            pass
        if txt and txt.strip():
            cache_file = os.path.join(CORE_HN_DIR, "last_essay.txt")
            try:
                with open(cache_file, "w", encoding="utf-8") as f:
                    f.write(txt)
            except Exception:
                pass
            words = len(txt.split())
            self.status_label.config(text=f"● Ensayo listo: {words} palabras", fg="#10B981")
            self.telemetry_label.config(text=f"> essay ready: {words} words from clipboard")
            self.log_terminal(f"[Essay] ✅ Ensayo detectado: {words} palabras ({len(txt)} caracteres).")
        else:
            self.status_label.config(text="● Portapapeles vacío", fg="#F59E0B")
            self.log_terminal("[Essay] ⚠️ El portapapeles está vacío. Copia tu texto primero (Ctrl+C).")

    def transfer_to_pastewrite(self):
        txt = ""
        cache_file = os.path.join(CORE_HN_DIR, "last_essay.txt")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    txt = f.read().strip()
            except Exception:
                pass
        if not txt:
            try:
                txt = pyperclip.paste()
            except Exception:
                pass
        if txt:
            self.pw_set_text(txt)
            self.switch_mode("pastewrite")
            self.log_terminal("[Transfer] Texto transferido exitosamente al editor de paste, write.")
        else:
            self.log_terminal("[Transfer] ⚠️ No hay texto para transferir. Copia o detecta un ensayo primero.")

    def open_playground(self):
        if hn_open_playground:
            try:
                hn_open_playground(
                    self.root,
                    self.engine_var,
                    self.casual_mode_var,
                    self.wpm_var,
                    terminal=self.hn_terminal
                )
                self.log_terminal("[System] Abriendo Text Playground & Inspector...")
            except Exception as e:
                self.log_terminal(f"[Error] No se pudo abrir Playground: {e}")
        else:
            self.log_terminal("[Playground] Módulo de análisis contextual activo.")

    def open_settings(self):
        if hn_open_settings:
            try:
                hn_open_settings(
                    self.root,
                    tk.BooleanVar(value=False),
                    self.use_shift_enter_var,
                    tk.BooleanVar(value=False),
                    self.casual_mode_var,
                    tk.BooleanVar(value=True),
                    self.remove_asterisks_var,
                    tk.DoubleVar(value=1.0),
                    self.engine_var,
                    self.hn_terminal
                )
            except Exception as e:
                self.log_terminal(f"[Error] Settings: {e}")
        else:
            messagebox.showinfo("Settings", "Ajustes del motor HumanNature activos.")

    # --------------------------------------------------------
    # paste, write. Editor Handlers
    # --------------------------------------------------------
    def pw_clear_editor(self):
        self.pw_editor.delete("1.0", "end")
        self.pw_update_stats()

    def pw_set_text(self, text: str):
        self.pw_editor.delete("1.0", "end")
        self.pw_editor.insert("1.0", text)
        self.pw_update_stats()

    def pw_paste_clipboard(self):
        try:
            txt = pyperclip.paste()
            if txt:
                self.pw_set_text(txt)
                self.log_terminal(f"[Editor] Pegado desde portapapeles ({len(txt)} caracteres).")
        except Exception:
            pass

    def pw_update_stats(self, event=None):
        txt = self.pw_editor.get("1.0", "end-1c")
        chars = len(txt)
        words = len(txt.split()) if txt.strip() else 0
        lines = len(txt.splitlines()) if txt.strip() else 0
        wpm = self.wpm_var.get()
        est_sec = max(1, int(chars / max(1, (wpm * 5 / 60))))
        self.pw_stats_lbl.config(text=f"{chars} caracteres • {words} palabras • {lines} líneas • ~{est_sec}s a {wpm} WPM")
        self.status_label.config(text=f"● Buffer listo: {words} palabras", fg="#10B981")
        self.telemetry_label.config(text=f"> buffer ready: {words} words in editor")

    def pw_apply_directive(self, code: str, label: str):
        raw = self.pw_editor.get("1.0", "end-1c")
        if not raw.strip():
            self.log_terminal("[Directiva] El editor está vacío. Pega texto primero.")
            return

        self.log_terminal(f"[Directiva] Aplicando {label}...")
        transformed = raw

        if code in ("clean_markdown", "stealth"):
            transformed = clean_markdown_text(raw)
        elif code == "formal":
            if run_humanizer:
                transformed = run_humanizer(text=raw, engine="🎓 Academic Master")
        elif code == "casual":
            if run_humanizer:
                transformed = run_humanizer(text=raw, engine="🌊 Natural Flow", casual_mode=True)
        elif code == "code":
            # Strip outer markdown code fences
            transformed = re.sub(r'^```[\w]*\n', '', raw)
            transformed = re.sub(r'\n```$', '', transformed)
        elif code == "exacto":
            transformed = raw

        self.pw_set_text(transformed)
        self.log_terminal(f"[Directiva] ✅ {label} aplicada correctamente.")

    # --------------------------------------------------------
    # Global Hotkeys Binding
    # --------------------------------------------------------
    def bind_hotkeys(self):
        # 1. Pynput Global Listener (Rootless, works globally across all Linux windows)
        try:
            from pynput.keyboard import Listener, Key
            def _on_key_press(key):
                if key == Key.f9:
                    self.root.after(0, self.trigger_start)
                elif key == Key.f8:
                    self.root.after(0, self.trigger_pause)
                elif key == Key.f10:
                    self.root.after(0, self.trigger_stop)

            self._pynput_listener = Listener(on_press=_on_key_press)
            self._pynput_listener.daemon = True
            self._pynput_listener.start()
            self.log_terminal("[Hotkeys] 🟢 Atajos globales activos: F9 (Iniciar), F8 (Pausar), F10 (Detener)")
        except Exception as e:
            self.log_terminal(f"[Hotkeys] Fallback hotkeys: {e}")

        # 2. Local Tkinter key bindings
        self.root.bind("<F9>", lambda e: self.trigger_start())
        self.root.bind("<F8>", lambda e: self.trigger_pause())
        self.root.bind("<F10>", lambda e: self.trigger_stop())

    # --------------------------------------------------------
    # Typing Execution Engine
    # --------------------------------------------------------
    def trigger_start(self):
        global is_typing, is_paused
        if is_typing:
            self.trigger_pause()
            return

        # Determine which text to type
        text_to_type = ""
        if self.active_mode == "pastewrite":
            text_to_type = self.pw_editor.get("1.0", "end-1c").strip()
            if not text_to_type:
                try:
                    clip = pyperclip.paste() or self.root.clipboard_get()
                    if clip and clip.strip():
                        text_to_type = clip.strip()
                        self.pw_set_text(text_to_type)
                except Exception:
                    pass
        else:
            # HumanNature mode: check current clipboard first, then cache
            try:
                clip = pyperclip.paste() or self.root.clipboard_get()
                if clip and clip.strip():
                    text_to_type = clip.strip()
            except Exception:
                pass

            if not text_to_type:
                cache_file = os.path.join(CORE_HN_DIR, "last_essay.txt")
                if os.path.exists(cache_file):
                    try:
                        with open(cache_file, "r", encoding="utf-8") as f:
                            text_to_type = f.read().strip()
                    except Exception:
                        pass

        if not text_to_type:
            self.log_terminal("[Error] ⚠️ No hay texto para escribir. Pega texto en el editor o copia un ensayo.")
            self.status_label.config(text="● Sin texto para escribir", fg="#EF4444")
            return

        if self.remove_asterisks_var.get():
            text_to_type = clean_markdown_text(text_to_type)

        is_typing = True
        is_paused = False

        threading.Thread(target=self.typing_worker, args=(text_to_type,), daemon=True).start()

    def trigger_pause(self):
        global is_paused, is_typing
        if not is_typing:
            return
        is_paused = not is_paused
        if is_paused:
            self.status_label.config(text="● Pausado (F8 para reanudar)", fg="#F59E0B")
            self.telemetry_label.config(text="> status: paused")
            self.log_terminal("[Typing] ⏸ Pausado. Presiona F8 o F9 para reanudar.")
        else:
            self.status_label.config(text="● Escribiendo...", fg="#10B981")
            self.telemetry_label.config(text="> status: active typing sequence")
            self.log_terminal("[Typing] ▶ Reanudando...")

    def trigger_stop(self):
        global is_typing, is_paused
        is_typing = False
        is_paused = False
        self.status_label.config(text="● Detenido por usuario", fg="#EF4444")
        self.telemetry_label.config(text="> status: stopped")
        self.log_terminal("[Typing] ⏹ Secuencia detenida.")

    def typing_worker(self, text: str):
        global is_typing, is_paused

        delay = self.start_delay_var.get()
        self.log_terminal(f"[Countdown] ¡Cambia a tu ventana destino (Docs/Word)! Escritura inicia en {delay}s...")
        for sec in range(delay, 0, -1):
            if not is_typing:
                return
            self.root.after(0, lambda s=sec: self.status_label.config(text=f"● Iniciando en {s}s...", fg="#F59E0B"))
            self.root.after(0, lambda s=sec: self.telemetry_label.config(text=f"> countdown: {s}s to launch"))
            time.sleep(1)

        if not is_typing:
            return

        self.root.after(0, lambda: self.status_label.config(text="● Status: Escribiendo...", fg="#10B981"))
        self.root.after(0, lambda: self.telemetry_label.config(text="> status: typing active"))
        self.log_terminal(f"[Typing] ▶ Iniciando escritura física ({len(text)} caracteres)...")

        wpm = self.wpm_var.get()
        acc = self.acc_var.get()
        use_burst = self.use_burst_var.get()
        use_shift_enter = self.use_shift_enter_var.get()
        base_delay = 60.0 / max(1, wpm * 5)

        for i, char in enumerate(text):
            if not is_typing:
                break
            while is_paused:
                if not is_typing:
                    break
                time.sleep(0.1)

            # Simulated Typo Injection
            typo_chance = (100.0 - acc) / 100.0
            if random.random() < typo_chance and char.isalpha():
                typo_char = get_typo(char)
                emit_char(typo_char)
                t_delay = base_delay * random.uniform(0.5, 1.1)
                time.sleep(t_delay)
                self.root.after(0, lambda d=t_delay: self.update_hud(int(d * 1000), False, is_typo=True))

                # Cognitive pause before realizing typo
                pause_time = random.uniform(0.18, 0.40)
                time.sleep(pause_time)
                emit_key("backspace")
                time.sleep(max(0.12, base_delay * 0.7))

            # Actual Keystroke
            if char == "\n":
                if use_shift_enter:
                    emit_key("shift+enter")
                else:
                    emit_key("enter")
                kd = max(0.15, base_delay * random.uniform(1.2, 2.5))
            else:
                emit_char(char)
                kd = max(0.045, base_delay * random.uniform(0.65, 1.35))
                if use_burst and char in ".,;:!?":
                    kd += random.uniform(0.25, 0.7)

            time.sleep(kd)

            # Update Telemetry & Oscilloscope
            self.root.after(0, lambda d=kd: self.update_hud(int(d * 1000), is_spike=(d > base_delay * 2), is_char=True))
            if i % 2 == 0:
                self.root.after(0, self.render_telemetry)

        is_typing = False
        self.root.after(0, lambda: self.status_label.config(text="● Secuencia completada exitosamente", fg="#10B981"))
        self.root.after(0, lambda: self.telemetry_label.config(text="> completed: ready for next task"))
        self.root.after(0, self.render_telemetry)
        self.log_terminal("[Typing] ✅ Escritura completada al 100%.")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = UnifiedApp()
    app.run()
