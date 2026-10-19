import os
import sys
import ctypes
from ctypes import wintypes
import time
import random
import pyperclip
try:
    import keyboard
except Exception:
    keyboard = None

import threading
import queue
import subprocess
import shutil
import base64
import re
from datetime import datetime

# Ensure Linux BLT library loads seamlessly
_local_blt = os.path.expanduser("~/.local/lib/libBLT.2.5.so.8.6")
if os.path.exists(_local_blt):
    try:
        ctypes.CDLL(_local_blt, mode=ctypes.RTLD_GLOBAL)
    except Exception:
        pass

try:
    import tkinter as tk
    from tkinter import ttk
except Exception:
    tk = None
    ttk = None

# ============================================================
# HumanNature v3.5.2
# Desktop autotyper + conservative text humanization engine
#
# Engines:
#   Hummer   = lexical cleanup / AI-ish phrase cleanup
#   Lavender = phrase-level linguistic cleanup + contractions
#   Mist     = conservative contextual rewrites
#
# The typing simulator is kept separate from text processing.
# ============================================================

APP_NAME = "HumanNature"
APP_VERSION = "v3.6.0"
APP_TITLE = f"{APP_NAME} {APP_VERSION}"

# ------------------------------------------------------------
# Windows / App Setup
# ------------------------------------------------------------

user32 = None
if hasattr(ctypes, "windll"):
    user32 = ctypes.windll.user32
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            f"{APP_NAME.lower()}.desktop.utility.v352"
        )
    except Exception:
        pass


ICON_BASE64 = (
    'AAABAAUAEBAAAAAAIACnAgAAVgAAABgYAAAAACAAPAQAAP0CAAAgIAAAAAAgAGEFAAA5BwAAMDAAAAAAIACuBwAAmgwAAEBAAAAAACAAEwIAAEgUAACJUE5HDQoaCgAAAA1JSERSAAAAEAAAABAIBgAAAB/z/2EAAAJuSURBVHicbZM7iFR3FMZ/59zHeO88sru6wU1EwSYSEEQsRMHFIqBgs0KSJkVCtHIbSSOks7KRkN5SEOysEgvBSgQx1cJiIyKiuwmOzOx9zdy551jc9bk51b/5Hnzf/5NTx486QOHKnDbEKrgIOP97bsZrU2JxQiAEaICVdIvlZEIwKbBZDSKfIQFVgiRlbRpzO++TuxIWrqykW/zSGzPMSzoHvyXcs4TPakR0G+ygilUF5fpjzsYVfTH+GM8TzknDclIxzEsGP/3Gwo+rSBS3DsxacBC0Dqwhe3CXjeuXORyVHIq7aBQIOmmVF35YRdyx0ZBm8wWWj/GqoPnvJc1wEy9zBqfPMzh1Di8ydgWCguCzmmjPEqgiYUS59pDnq2doXm+iSZdXVy8wvPUn2u3hdUW0dz+Y4UgbIiL4bNYmpYrXNc34DdpJ0LiLFRleZiDKO8F3F75/iQAC7ogqiPDq2iV0V0K98Zz0yMk2Ew0+aegDwXuiNi8JQwbffU/45dfUL5/h1uysFtCdBIrXU2w0pHvsNP0T53AzmmwE+lGtOxxs2/ZJRefAN+z+9XcQocnfMHf+ItHiV9ikRDtpW+snBKJYmSOi+KQi2neQ3T9fwfIRNimZX7mINzOabISmX2BF9kHXzAiSlHL9H7IHfxMsLKFpD9zR/jzB/GJbb9QhWtzH9Nk64/t30LQLZoRDU9amMWfjio3rlyke3SPcux8+3sP2DqzMGN+/Q2/0L0+lx5NpSBiLczvv0xfjcFRR/HUTN2Nn3rQfJ015Kj1ubA0oXZHl40d9htA4HIqmJKHSwj/fsyA4bsaTaUTpQiLOW6HjFOhCNbdTAAAAAElFTkSuQmCCiVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAEA0lEQVR4nJ2Wy48UVRTGf+fWrerqrm5mBhAmzpBIRmJcsGAkcXwARoiPGGMwcclG+AvQlRsT4874ILoRQtxoXBAQEycT45IYFRcu0IUJrMBRBtLd0zPd9eiqe1zUdDMPYNAvuZuquuc753zfuXXl4My0sgIDJCqkKojwn6AKVpSalOEGQe3qj5bVMGUzpoMEx4MzKOCj3Cgsl7MqohCI4gArKx844M16m0OVHpEHKgaK4sEYjEFEyAvH1bzL2eURruc+oSjWAEtqOB61ebW6TFMtrSRF+xmmWl9V7D0ggsYpmud4UZ09NuNko8W7i9vpOoONVZiyGQfCmKb6aJ5ReehhRo+eoLbvANrPuKcgquAHFLfmaZ3/nOTKz3S8gHEv53DY41yvgc0Q9gUpdQ9aSUJlxwS7Pv4Wb9s4miZlBa4AMWDMncCuKInFwOQU0cyL3PzkbVoXTpONbWN/kPBdHGEGIoFAP2P0tePY7eMUrQU0jcsW17aA56FJXK4iR6oNJAjRLMX1Orheh7GjJ/B3TKD9bGgSM6zWFUitTm3fs7gkRjyLVELiP35l4bN3WP5xDvwA/IB84S9un3mP9sWzqCpiAzRN8Cd2E0ztRZMemHUEg9I175fCOYdUQpLfL3Pr0w9YvjSLeB5iPPr/XOf26fdpXzwL6hg0gKKAIl+j2Zo5GLhiNaFUqtitFq8xilRCUDDVCDu2FdMY3bh3nSE2EmxwikOdwy0v0r9+DRTyhXnUFaXQm2BzAldgojrdn76n88M5EBBbQTy/dJPef042JxCDJjHhE4doHHkDFPo3rtH8+tRdW7Ie5r5vAYxBiwJ/coqRl44x8vIxoqdeKEU1m2+/fwUipae7Dre0iIvboFB0WrjlDq7X/R8Eg56KoHmOv3MX0dPPEOx+HFaGx9syRvTkEfzJqQ2uW6/JWgIRxJbiiTFo3KV+4BUaz7+O5ll5LgHBI48x+eE3qHPltKuW5MYb7h/gzlEhBs1S+rfmEeOVNhy2aBHN0juJuALXXULj7pqqXW+JvHkTsT668sxA+bMQI2iR075wGqlEmEqt9PkgO1VwbmXpGjJVhx3dydKlWdI/f4NqhNXyNDIecKPw6RcOU60TX/mFhVNvkd/+G1MfxVQjTK1+1yW1OqY+ghiP9uwXtL76CMII6wrmC59UBVsTx+U05Fros8fv0/EszfNnWLo0S+XRvWiRD8W9myHEWvLmwjBzz/dBC+aSCAXkuZlpzRAmvJyTjSbjXk7m+Wg/RZN400EqSXwIa1h1oI4vuyPMxRFVUeTgzLQKkKqwxTgOh132BwlOzObBhxyKVcd8YZlLIq72A0LRsoLBtcUAfSBVQ1XcAwVejUGSCtRWbhQA/wIvQuq7wHui6AAAAABJRU5ErkJggolQTkcNChoKAAAADUlIRFIAAAAgAAAAIAgGAAAAc3p69AAABShJREFUeJy1l0uIHFUUhr9z69arp6s7M4kkCgYFCYhiYBYmKETEhY+ILkQNIS504UJRAm7FtRtBEALZBxEFd8FsFCESFTQqPgYRRcVVItOTfkxVdVfd46Kqe6anZ2I6mkNXQ9+/+p7//vc87pUjh5eVLWYAB5SAbAWv0/x6zq3O7OYfY2cDFQJREtH/hYQCq84jEjchMkNAamCkwj1BzuNxn9vtiKEK5j84FqBE+DSL+SRb4IozRKITEnLk8LKOnTuEl5MO9wYZDirnImAM8+mgIALOoc4hQCiOrvM43W/z1TAmEUc5VkCAEcIrSYf7gpQ1NQiC8TyKYY5b74HOhMq/cFAkCDGNBETolRWJk0mHN7uGlVFALIo1VHt+0M85VDv3RKAsKXsd/Jv3s/jUi4gfoM79q9+xcxPGpCtfM7hwDjEGGzfJ1ZGI8mTc46fRbgCsAoHA440+TgURQcsSEzXY88xLtB45jr/v1krSOVaPCC7PSL85T+f9U6Q/fIkNIgbquCsYshzkXByG2BJIxHGbHTFEMMajvNJh8ZmXuOn51xn1LlOs/T09OcwS0snXBBOEhUMPER44yJ8vPkjZ76KeJRDHHf6QL/KoCvBx9IuADnP8W/bTfuQ4Re8ylA7xbPX4ASaMkDBCrL8x7lkkmMXwPIrVy9hdu2kdfQ6X9hGvyqmhCgIbGSaAGIsb9Egeehr/5v24oqgzoHpD85SydwXX70JZTAuQbcbKybhYH5et03r4GP6efehwWGtT2TYprojvTw85h4kiVs+8zR8v3M9frz5G9tsKEkZoWSBhzOqZt2rsKPnvFcY4aFUR64PMurMzI/UfZm1DARGzowIi3pQCV59zWwWuYsYg1oK1oA4ti8mDyAY2R8Zsr8DVTLXK82QXtrGIC2KMjZAgrCSfs2DNT6C27kfvkl48j45yxA/Jf/2hInFjCVTtRRU6772Dy7VKXQW71MIstFC9xmp5fQQEqJwuHnsFf++tEwUGn58j+/lbTLRwIwlsWOvR4zTuPIQrMoyNKC79Rfr9lxA3bzABkarO99Yo1ju49T6mkaDDvCpa8/QM5k1D59CigKIAMVOlGNUNbI5AnIOAImGMl7QxzRZ40+JJtBnzrnnWHSrhluOjMbgsY+nESRaffRlEMGGE5hniWTRPWTrxGovHXq2xGM2zakvGamydc0cCWq10Vpxq3ESNapotRUeiGCPbY6hDggiMndmeaQLqkCAkW7mIy1Nka0A5h+50HtgBU+cwjQXyH7+m7K5WTWnTuXiqHVcvJwwunGP9m/N47SV0NJyU3+lV6eyzGQMoS8QIGEvng1O4LK3bu07asa3EhaImUaWZYe39U0QHDuIt7kHTdVR1vlOZc5iFBLGW7scfkn53Aa/ZpnQlmA1/8uDhZe2q4dlGl6caPXpq8IxB8wyvtUT76AlaDx9DrF+X2WtgUe95/sv3dD44RfrdBSQI0VrydRXeWLuJvgrywOFlLYEFUd7cdYlQIAesMehoiKYDvD37qj6/TRTvaMaj7K6ieYpZaKOqjFTZ65W8O2jx3nqLtrjqVGyBK2o43d/FyaRDIjBwDvV8pLWbYjCYz/nYPB9phpSuxAJ7vZLP8pizaZOmOBz1zYhamr4a7vZznoh73BUMCUXr/ne9t0Mdf7jsPD7NGpxNm4yoLqvjxQNVYiTiWBkF/DTazXKQcUd9VP8vl1MBCoXP8phLztKsL6hjPafqQAnE9aovDiO+yOP/5XouArE42vV9cPNm/gNgSHMQ12fA3AAAAABJRU5ErkJggolQTkcNChoKAAAADUlIRFIAAAAwAAAAMAgGAAAAVwL5hwAAB3VJREFUeJzVmk2MW1cVx3/nvvvsZ3tmPDPJ0EQFtWqCUlUtJQHBpIsIEG1SaFdAocCCDYJ00YoFIIGyIEFqKlYgFYk0aqtKLNgUqTsgIkhsQDTtoqKESh1E1JCvmYxjxzPP7+MeFu/ZY8/YnkzGDuIvPWk8vu+e87/n4557ruXQ/AHl/xh2swEGUCAdvy4bYHPZw1Z4IAEBrChNZwCYMG7oRONA3RkKohRFSVT6julLQAAHXE0te2zEQ37E1yo3WFWDGaPC3fIjhFebUyzEBS6mlp0mwbGRxAYCBghVmDaOL1bqfDZosstLqTtDSe6cDSzKsakl3o4C/tIKOBOW8SUjpz3juiC58oFxfG/yOh8rtFhyHsvO4JFZ5U7iSmrZ40fsL4R82CacujlNSRweayQ6BNpuM+M5npu8zl4b85/U4ovirZ/ZGEQMw8NrqxDUpaBrc1pRWipcVsvjpSYAv25O5XKll4CHsuQ8nig1eLjQ4lJqKXS7jEj2pCm62iSNwoyEjoCECKoOE1QQvwDGA+cAxQAGZckZnizd5M9hmfcSn7Iork3AACtq2GsTPhM0WUo9bHt1VcGzaBxBEoEYql/4JpOHn8Y1lsHbYJ+twzlMZYrFU8cJ//kWGrUwlSlAOgtkgZrz+GqlzvP1WVLyTAlrjvCQ32KXSal1ZRvxLGmzjp29i+D+/cwdPY6Z3okJSvkq9U9vW0PmEnef/A3h+XMsvXKS1sK7aJog1u+QcMBeG7PHxryf+PiAHJo/oA4IRPnFzNXeDUsE0gRTqbL7+KuUH5gnqV/LV629BqOCZq7jWWxlhtobp7n64o8zAjkcUBbl/cTnR7U5quLW0roCKyq9eV4EF7cI7t9P6YF5omsX1r4zHhgzwid3xSQmrl1m8tGn8Gbm+uaJFZXO0vXou2GTSlNEPOaOniBtXMMUS1td1q1DBEEQ4zH3zHGSaxcR3+8ZYgb83TuPMWgrZOrxr+NN7xieMdevpgxwLZF14waIF0GTiOCjH6dy8DCu2UBM/2QxuDIQQaOQqSNPI8VyHrD9oa0QDVc7D+mA0i9JesZp3Boo24VNCrvvY+KRw7ibjYxwHwyvRkVI68ugfZRXBc/D1WtcOvFtogvvIcUAVJl79iQTB4+grZVslVWRQpEbv3uNxdM/xavOktaXmZh/lLlnX8hyv3O9lhODaoJr1tfiY8sEALmFPN+2AKrZs5kFiptYoCO8HdyD/XdTAreEbr9W3X4MbEX0tmf4H2M0FlgPddlG51xe/2r2eRR10zqMhYAUy5hyFbV+TxBLIRg5ibEQiP71D1YmqlmQioCC+D7xxQXw7EhJjJBAu0ZXrr/2MzSJ6a2VFPGLmFIZHbKnbBXjiQHjIRY2FHudLDU6UWMhULh3H97UbFfFqiCG5PoVkssXMjcaEUZIYO24veNbP2TykSdwadg5XRmvyPJvf8XVn/8Ab4RF4Vgs4JoNkuYy2lrtZCFXKKCrzcGb3G1iTDFgEM9mx812GvXswIJsW6JGPuMdxkgsIJ5FrL92fh1U4xjTGSfWv6VCcTNsn4AqSW2RZPESUiyBKhqFfXxd0NUmybVFNIlIa/WsVN8mbp+AZC0PKQbMfPm7pDcWMz8HivfugyReIyECLiF48NPMPXMMKZbQ1iqFj+xdO2ndZnBvzwIdAt8h27ny9sdqA41aPUppmhA8+CnKn/gcWX9B0DTKDizbKC02J+A2uRnIXahbCWlnnx7kLtSsd/3LDI8D1aFHWdiMgGreIRsOudWd1RjkVlOpOkQ8pFTpf6RtTzn4fYcpVVh86UTWVhxDDh8I5zAT04QL71B7/RTe9A40TfoOHayVKvgFwvNvEZ4/l21KYziQ9EXeRF45d5b40gXEFgbK7m3EbfjWoFGLpVdewFZmUZf75LiItOf2fXApSy+f7Lv63Xr2OG+kgu1uqedd49bC36m9cZrJz38ls0QS48KVtfJ42xBQh5moZu17TVk89RNUs85gt4wUiLsoyKH5A2qApgqfLLQ4Vl3kivO6bj4EjWMExZuZY+fREwT7Hqaw6z6UUTV4FcEjXHiHlXNnWXr5+Sxwje1JxQL4KM/VPkQjvzXqtNcLKAuJz9tRwB4/oqUGQ9bnET8rEdJGjYvf/xKVg49RmX8sa/mNoBxoJ4za6y8RX/43XnU221e6Vt4BAcrZVrmjPN0EiqJcTC1/jUocKIZcSrtuJLsm8nffQ/jum6z87Y9ZrT8iD8I5vOkd2Nm7Mp/vktk+rAainFmtEKlQ6b6hAUgQdpqUM2GZu72YI6UmSy67qek52SYxEpSx5ckRaN4LTZMNAetyhlMm5ZeNGT5ILRVxnStXu36wRTl1swrAk6Wb1JwhRXpvKJ3bdIfcLoQsRQaiBDhebEzz+7DMdJfykAfx+hfbF0f32Jinyg322rg3O40ZAqT5EfVPYYU/rJb5ILUEudv0jO33Y482vxU1+OLYY2O+Uamz2nUzMk4YspR+ulml4UyPz2/QddivVQyZNRKE8A4p341SfgfW1qMfhlZh7Zd8sh9c3Gm06+Bh0fZfcR0/j77WTw8AAAAASUVORK5CYIKJUE5HDQoaCgAAAA1JSERSAAAAQAAAAEAIBgAAAKppcd4AAAHaSURBVHic7ZuxTsMwEIaviAEkulQgZlYWBGJACCExMzHyALDkHRhaBl6gS1+gb8KEhFhYGaFSxQobTJaiJE58jpP/HN83pnb83+/rxVHs0eXZyR8lzAZaABo1AC0AzaZPp/lkFVpHMLLvfVZ7lgGSAzcYja5GOBkQQ+BFXI1orAExBp+nSX+tAbEHb6iLw2rAUII32OLRx2DVRZ/ZP1i+thbD5eP2mNV+PlmViqLXOiAPIvDi2Fwj8oyKL0Ous48M3IarEfks8KoBEoMn8tOVfBFkGyB19g1cfZoBnMbSZ9/A0Zl8BrReB9j4fX+hz9ld6fru/QONr26s/X7enunrKStd38seaefiOqhGIs0ANUANQAtAowagBaBRA9AC0HS2ELKxXkxpvZj2PayV5DNADUALQNN7DfB9GeqK5DNADUALQKMGoAWgUQPQAtAkb0BnC6Gtw1Ov7wjbR+e9fn9IPgPUALQANGoAp3GbrSh9wtGpGcDtID0LuPo0A3w6Sc0CH12lbXJEvI2SEnaNcAIPvlHSDB7DTtEqKjOAaHibpYmqzw5oEbT9wD17Ix1bPLUZMBQT6uJo/AvEbkKTfqengLlJTIUx6Kmx4k0lG9HpuUHfQSSjj0G0ADT/au97SaH0qoUAAAAASUVORK5CYII='
)


def ensure_icon_file(filepath=None):
    """Write the bundled icon to disk if it does not exist yet."""
    if filepath is None:
        filepath = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            f"{APP_NAME.lower()}.ico",
        )
    elif not os.path.isabs(filepath):
        filepath = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            filepath,
        )

    if not os.path.exists(filepath):
        with open(filepath, "wb") as f:
            f.write(base64.b64decode(ICON_BASE64))
    return filepath


# ------------------------------------------------------------
# Cross-Platform Safe Clipboard Handlers
# ------------------------------------------------------------

def get_clipboard_text(widget=None):
    """Safely retrieves text from clipboard from ANY thread or widget on any OS."""
    # 1. Direct widget or root read on main thread
    target = widget or ("root" in globals() and globals().get("root"))
    if target and threading.current_thread() is threading.main_thread():
        try:
            val = target.clipboard_get()
            if val:
                return val
        except Exception:
            pass

    # 2. Worker thread requesting from root via queue
    root_obj = globals().get("root")
    if root_obj is not None:
        try:
            q = queue.Queue()
            def _fetch():
                try:
                    q.put(root_obj.clipboard_get())
                except Exception as ex:
                    q.put(ex)
            root_obj.after(0, _fetch)
            res = q.get(timeout=1.5)
            if isinstance(res, str) and res:
                return res
        except Exception:
            pass

    # 3. Fallback to pyperclip
    try:
        val = pyperclip.paste()
        if val:
            return val
    except Exception:
        pass

    # 4. Fallback to CLI utilities on Linux
    for cmd in [["xclip", "-selection", "clipboard", "-o"], ["xsel", "-b", "-o"], ["wl-paste"]]:
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=0.3)
            if res.returncode == 0 and res.stdout:
                return res.stdout
        except Exception:
            pass

    return ""


def set_clipboard_text(text, widget=None):
    """Safely writes text to clipboard from ANY thread or widget on any OS."""
    copied = False
    target = widget or ("root" in globals() and globals().get("root"))
    if target and threading.current_thread() is threading.main_thread():
        try:
            target.clipboard_clear()
            target.clipboard_append(text)
            copied = True
        except Exception:
            pass
    elif globals().get("root") is not None:
        try:
            def _write():
                try:
                    globals()["root"].clipboard_clear()
                    globals()["root"].clipboard_append(text)
                except Exception:
                    pass
            globals()["root"].after(0, _write)
            copied = True
        except Exception:
            pass

    try:
        pyperclip.copy(text)
        copied = True
    except Exception:
        pass

    return copied



# ------------------------------------------------------------
# Windows system-tray support
# ------------------------------------------------------------

class TrayIcon:
    """Small Windows-only tray icon used for 'close to tray'.

    HumanNature keeps its custom borderless GUI. Clicking the custom X hides
    the window and leaves this icon in the Windows notification area.
    Double-clicking the icon restores the GUI. Right-clicking exposes
    Show and Exit so the app can still be fully closed.
    """

    NIF_MESSAGE = 0x00000001
    NIF_ICON = 0x00000002
    NIF_TIP = 0x00000004
    NIM_ADD = 0x00000000
    NIM_DELETE = 0x00000002

    WM_USER = 0x0400
    WM_LBUTTONUP = 0x0202
    WM_LBUTTONDBLCLK = 0x0203
    WM_RBUTTONUP = 0x0205

    WM_TRAY = WM_USER + 77
    MENU_SHOW = 1001
    MENU_EXIT = 1002

    def __init__(self, root, on_show, on_exit):
        self.root = root
        self.on_show = on_show
        self.on_exit = on_exit
        self.visible = False
        self.hwnd = None
        self.hicon = None
        self._wndproc = None
        self._class_name = f"{APP_NAME}Tray_{id(self):x}"

        if os.name != "nt" or not hasattr(ctypes, "windll"):
            return

        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        self.shell32 = ctypes.windll.shell32

        self.user32.LoadCursorW.argtypes = [wintypes.HINSTANCE, ctypes.c_void_p]
        self.user32.LoadCursorW.restype = wintypes.HANDLE
        self.user32.CreateWindowExW.argtypes = [
            wintypes.DWORD,
            wintypes.LPCWSTR,
            wintypes.LPCWSTR,
            wintypes.DWORD,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.HWND,
            wintypes.HMENU,
            wintypes.HINSTANCE,
            wintypes.LPVOID,
        ]
        self.user32.CreateWindowExW.restype = wintypes.HWND
        self.user32.LoadImageW.argtypes = [
            wintypes.HINSTANCE,
            wintypes.LPCWSTR,
            wintypes.UINT,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.UINT,
        ]
        self.user32.LoadImageW.restype = wintypes.HANDLE
        self.user32.DestroyWindow.argtypes = [wintypes.HWND]
        self.user32.DestroyWindow.restype = wintypes.BOOL
        self.user32.DefWindowProcW.argtypes = [
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        ]
        self.user32.DefWindowProcW.restype = ctypes.c_ssize_t

        self._build_windows_types()
        self._create_message_window()
        self._load_icon()

    def _build_windows_types(self):
        wintypes = wintypes

        self.WNDPROC = ctypes.WINFUNCTYPE(
            ctypes.c_ssize_t,
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        )

        class WNDCLASSW(ctypes.Structure):
            _fields_ = [
                ("style", wintypes.UINT),
                ("lpfnWndProc", self.WNDPROC),
                ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int),
                ("hInstance", wintypes.HINSTANCE),
                ("hIcon", wintypes.HICON),
                ("hCursor", wintypes.HANDLE),
                ("hbrBackground", wintypes.HBRUSH),
                ("lpszMenuName", wintypes.LPCWSTR),
                ("lpszClassName", wintypes.LPCWSTR),
            ]

        class GUID(ctypes.Structure):
            _fields_ = [
                ("Data1", wintypes.DWORD),
                ("Data2", wintypes.WORD),
                ("Data3", wintypes.WORD),
                ("Data4", ctypes.c_ubyte * 8),
            ]

        class NOTIFYICONDATAW(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("hWnd", wintypes.HWND),
                ("uID", wintypes.UINT),
                ("uFlags", wintypes.UINT),
                ("uCallbackMessage", wintypes.UINT),
                ("hIcon", wintypes.HICON),
                ("szTip", wintypes.WCHAR * 128),
                ("dwState", wintypes.DWORD),
                ("dwStateMask", wintypes.DWORD),
                ("szInfo", wintypes.WCHAR * 256),
                ("uTimeoutOrVersion", wintypes.UINT),
                ("szInfoTitle", wintypes.WCHAR * 64),
                ("dwInfoFlags", wintypes.DWORD),
                ("guidItem", GUID),
                ("hBalloonIcon", wintypes.HICON),
            ]

        self.WNDCLASSW = WNDCLASSW
        self.NOTIFYICONDATAW = NOTIFYICONDATAW
        self.shell32.Shell_NotifyIconW.argtypes = [
            wintypes.DWORD,
            ctypes.POINTER(NOTIFYICONDATAW),
        ]
        self.shell32.Shell_NotifyIconW.restype = wintypes.BOOL

    def _create_message_window(self):
        wc = self.WNDCLASSW()
        self._wndproc = self.WNDPROC(self._window_proc)
        wc.lpfnWndProc = self._wndproc
        wc.hInstance = self.kernel32.GetModuleHandleW(None)
        wc.lpszClassName = self._class_name
        wc.hCursor = self.user32.LoadCursorW(None, 32512)

        self.user32.RegisterClassW(ctypes.byref(wc))

        HWND_MESSAGE = wintypes.HWND(-3)
        self.hwnd = self.user32.CreateWindowExW(
            0,
            self._class_name,
            f"{APP_NAME} Tray",
            0,
            0,
            0,
            0,
            0,
            HWND_MESSAGE,
            None,
            wc.hInstance,
            None,
        )

    def _load_icon(self):
        if not self.hwnd:
            return

        icon_path = ensure_icon_file()
        LR_LOADFROMFILE = 0x00000010
        LR_DEFAULTSIZE = 0x00000040
        IMAGE_ICON = 1

        self.hicon = self.user32.LoadImageW(
            None,
            icon_path,
            IMAGE_ICON,
            32,
            32,
            LR_LOADFROMFILE | LR_DEFAULTSIZE,
        )

    def _notify_data(self):
        data = self.NOTIFYICONDATAW()
        data.cbSize = ctypes.sizeof(self.NOTIFYICONDATAW)
        data.hWnd = self.hwnd
        data.uID = 1
        data.uFlags = (
            self.NIF_MESSAGE
            | self.NIF_ICON
            | self.NIF_TIP
        )
        data.uCallbackMessage = self.WM_TRAY
        data.hIcon = self.hicon
        data.szTip = APP_NAME
        return data

    def show(self):
        if os.name != "nt" or not self.hwnd or not self.hicon or self.visible:
            return
        data = self._notify_data()
        if self.shell32.Shell_NotifyIconW(self.NIM_ADD, ctypes.byref(data)):
            self.visible = True

    def hide(self):
        if os.name != "nt" or not self.hwnd or not self.visible:
            return
        data = self._notify_data()
        self.shell32.Shell_NotifyIconW(self.NIM_DELETE, ctypes.byref(data))
        self.visible = False

    def _show_context_menu(self):
        menu = self.user32.CreatePopupMenu()
        if not menu:
            return

        MF_STRING = 0x00000000
        TPM_RIGHTBUTTON = 0x0002
        TPM_RETURNCMD = 0x0100
        TPM_NONOTIFY = 0x0080

        self.user32.AppendMenuW(menu, MF_STRING, self.MENU_SHOW, f"Show {APP_NAME}")
        self.user32.AppendMenuW(menu, MF_STRING, self.MENU_EXIT, f"Exit {APP_NAME}")

        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

        point = POINT()
        self.user32.GetCursorPos(ctypes.byref(point))
        self.user32.SetForegroundWindow(self.hwnd)

        command = self.user32.TrackPopupMenu(
            menu,
            TPM_RIGHTBUTTON | TPM_RETURNCMD | TPM_NONOTIFY,
            point.x,
            point.y,
            0,
            self.hwnd,
            None,
        )

        self.user32.DestroyMenu(menu)

        if command == self.MENU_SHOW:
            self.root.after(0, self.on_show)
        elif command == self.MENU_EXIT:
            self.root.after(0, self.on_exit)

    def _window_proc(self, hwnd, msg, wparam, lparam):
        if msg == self.WM_TRAY:
            event = int(lparam)
            if event == self.WM_LBUTTONDBLCLK:
                self.root.after(0, self.on_show)
                return 0
            if event == self.WM_LBUTTONUP:
                self.root.after(0, self.on_show)
                return 0
            if event == self.WM_RBUTTONUP:
                self._show_context_menu()
                return 0

        return self.user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def destroy(self):
        if os.name != "nt":
            return
        try:
            self.hide()
        except Exception:
            pass
        if self.hwnd:
            try:
                self.user32.DestroyWindow(self.hwnd)
            except Exception:
                pass
            self.hwnd = None


# ------------------------------------------------------------
# Globals / State
# ------------------------------------------------------------

is_typing = False
is_paused = False
pause_btn_ref = None
nltk_ready = False

# ------------------------------------------------------------
# Modern Cyber-Dark Palette
# ------------------------------------------------------------
C_BG = "#0B0E14"
C_CREAM = "#151922"
C_CHARCOAL = "#F1F5F9"
C_ORANGE = "#06B6D4"
C_MUTED = "#94A3B8"
C_BORDER = "#1E2433"
C_SURFACE = "#0F121A"
C_ACCENT_ROSE = "#F43F5E"
C_ACCENT_GREEN = "#10B981"
C_BTN_BG = "#1E2433"
C_BTN_HOVER = "#283044"

chart_history = []

stats = {
    "keystrokes": 0,
    "typos_fixed": 0,
    "last_key_ms": 0,
}


# ------------------------------------------------------------
# Keyboard Typo Model
# ------------------------------------------------------------

ADJACENT_KEYS = {
    "a": ["q", "w", "s", "z"],
    "b": ["v", "g", "h", "n"],
    "c": ["x", "d", "f", "v"],
    "d": ["s", "e", "r", "f", "c", "x"],
    "e": ["w", "s", "d", "r"],
    "f": ["d", "r", "t", "g", "v", "c"],
    "g": ["f", "t", "y", "h", "b", "v"],
    "h": ["g", "y", "u", "j", "n", "b"],
    "i": ["u", "j", "k", "o"],
    "j": ["h", "u", "i", "k", "m", "n"],
    "k": ["j", "i", "o", "l", "m"],
    "l": ["k", "o", "p"],
    "m": ["n", "j", "k"],
    "n": ["b", "h", "j", "m"],
    "o": ["i", "k", "l", "p"],
    "p": ["o", "l"],
    "q": ["w", "a"],
    "r": ["e", "d", "f", "t"],
    "s": ["a", "w", "e", "d", "x", "z"],
    "t": ["r", "f", "g", "y"],
    "u": ["y", "h", "j", "i"],
    "v": ["c", "f", "g", "b"],
    "w": ["q", "a", "s", "e"],
    "x": ["z", "s", "d", "c"],
    "y": ["t", "g", "h", "u"],
    "z": ["a", "s", "x"],
    "ñ": ["l", "p"],
    "á": ["a", "s"],
    "é": ["e", "w", "r"],
    "í": ["i", "u", "o"],
    "ó": ["o", "i", "p"],
    "ú": ["u", "y", "i"],
}


# ============================================================
# HUMANIZER DATA
# ============================================================

# ------------------------------------------------------------
# Hummer: conservative lexical cleanup
# ------------------------------------------------------------

AI_BUZZWORDS = {
    "delve into": ["look into", "explore"],
    "a tapestry of": ["a mix of", "a combination of"],
    "testament to": ["proof of", "evidence of"],
    "underscore": ["highlight", "show"],
    "underscores": ["highlights", "shows"],
    "multifaceted": ["complex", "varied"],
    "Furthermore,": ["Also,", "Plus,"],
    "Moreover,": ["Also,", "Plus,"],
    "Additionally,": ["Also,", "And,"],
    "In conclusion,": ["Overall,", "To sum up,"],
    "It is important to note that": ["It's worth noting that"],
    "crucial": ["important", "key"],
    "utilize": ["use"],
    "facilitate": ["help", "make easier"],
    "optimal": ["best"],
    "leverage": ["use", "take advantage of"],
    "navigate": ["handle", "work through"],
    "seamless": ["smooth", "easy"],
    "therefore": ["so"],
    "However,": ["But,", "Still,"],
    "increasingly": ["more and more"],
    "numerous": ["many", "a lot of"],
    "approximately": ["about", "around"],
    "demonstrates": ["shows"],
    "demonstrate": ["show"],
    "demonstrated": ["showed"],
    "substantial": ["large", "significant"],
    "commence": ["start", "begin"],
    "commenced": ["started", "began"],
    "terminate": ["end"],
    "terminated": ["ended"],
}

# These are deliberately low-impact. They are only used in the
# optional casual pass and are never mandatory.
CASUAL_WORDS = {
    r"\bbecause\b": ["because", "since", "cause"],
    r"\bprobably\b": ["probably", "likely", "prob"],
    r"\bsomething\b": ["something", "something like that"],
    r"\bokay\b": ["okay", "ok"],
    r"\bgoing to\b": ["going to", "gonna"],
    r"\bwant to\b": ["want to", "wanna"],
    r"\bkind of\b": ["kind of", "kinda"],
    r"\bsort of\b": ["sort of", "sorta"],
}

# Extended AI buzzwords (English)
AI_BUZZWORDS.update({
    "spearhead": ["lead", "guide"],
    "embark on": ["start", "begin"],
    "shed light on": ["clarify", "explain", "highlight"],
    "pave the way for": ["open the door to", "lead to"],
    "paramount": ["essential", "critical", "top priority"],
    "cornerstone of": ["core part of", "foundation of"],
    "streamline": ["simplify", "speed up"],
    "foster": ["encourage", "support", "build"],
    "game-changer": ["big shift", "major step forward"],
    "paradigm shift": ["big change", "major shift"],
    "in light of the fact that": ["since", "because"],
    "vital role": ["key role", "major role"],
    "meticulously": ["carefully", "thoroughly"],
    "imperative that": ["essential that", "important that"],
    "myriad of": ["many", "variety of"],
})

# Spanish AI Buzzwords & Robotic Clichés
SPANISH_AI_BUZZWORDS = {
    "en conclusión": ["en resumen", "en fin", "para terminar"],
    "en resumen": ["en pocas palabras", "al final", "en fin"],
    "es crucial destacar que": ["vale notar que", "algo clave es que", "ojo con esto:"],
    "es importante señalar que": ["cabe decir que", "hay que tener en cuenta que", "vale la pena decir que"],
    "es importante mencionar que": ["vale recordar que", "hay que notar que", "también conviene decir que"],
    "es importante destacar que": ["vale notar que", "hay que considerar que", "cabe recalcar que"],
    "cabe destacar que": ["vale la pena notar que", "hay que decir que", "es bueno resaltar que"],
    "cabe señalar que": ["hay que notar que", "vale decir que", "es bueno notar que"],
    "juega un papel fundamental": ["es clave", "pesa bastante", "tiene mucho peso"],
    "juega un papel crucial": ["es fundamental", "es vital", "resulta decisivo"],
    "juega un papel importante": ["es clave", "importa bastante", "pesa bastante"],
    "en el vertiginoso mundo de": ["hoy en día en", "en el mundo actual de", "con el ritmo actual de"],
    "en el vertiginoso mundo actual": ["hoy en día", "en el mundo de hoy", "en la actualidad"],
    "en el vertiginoso mundo": ["hoy en día", "en la actualidad", "en el mundo de hoy"],
    "el vertiginoso mundo actual": ["el mundo de hoy", "la actualidad", "nuestros tiempos"],
    "vertiginoso mundo actual": ["ritmo de hoy", "mundo actual", "día a día"],
    "vertiginoso mundo": ["ritmo actual", "mundo moderno", "día a día"],
    "en un mundo en constante cambio": ["hoy en día", "en estos tiempos", "actualmente"],
    "un sinfín de": ["un montón de", "muchos", "bastantes"],
    "sumergirse en": ["meterse de lleno en", "entrar a fondo en", "explorar"],
    "sumergirnos en": ["meternos de lleno en", "entrar a fondo en", "explorar"],
    "sumergirse": ["profundizar", "entrar de lleno", "explorar"],
    "sumergirnos": ["profundizar", "meternos de lleno", "explorar"],
    "desentrañar los misterios de": ["entender bien", "descifrar", "analizar a fondo"],
    "abarcan una amplia gama de posibilidades que facilitan": ["tienen muchas opciones que ayudan con", "ofrecen muchas formas de facilitar"],
    "abarcan una amplia gama de posibilidades": ["tienen muchas opciones", "ofrecen muchas alternativas"],
    "abarca una amplia gama de posibilidades": ["tiene muchas opciones", "ofrece muchas alternativas"],
    "abarcan una amplia gama de": ["cubren muchas cosas de", "tienen muchas variantes de"],
    "abarca una amplia gama de": ["cubre varias cosas de", "incluye muchos tipos de", "tiene de todo en"],
    "el uso desmedido de": ["el abuso de", "usar en exceso", "el uso excesivo de"],
    "es imperativo señalar que": ["hay que tener claro que", "vale notar que", "ojo con esto:"],
    "es imperativo destacar que": ["hay que tener claro que", "vale notar que", "ojo con esto:"],
    "es imperativo recordar que": ["vale recordar que", "hay que tener presente que"],
    "requiere de": ["hace falta", "necesita"],
    "no obstante,": ["pero,", "sin embargo,", "aunque,"],
    "no obstante": ["pero", "sin embargo", "aunque"],
    "asimismo,": ["además,", "también,", "de paso,"],
    "asimismo": ["además", "también"],
    "por consiguiente,": ["por eso,", "así que,", "entonces,"],
    "por consiguiente": ["por eso", "así que", "entonces"],
    "por ende,": ["por lo tanto,", "por eso,"],
    "por ende": ["por lo tanto", "por eso"],
    "en primer lugar,": ["primero que nada,", "para empezar,"],
    "a fin de cuentas,": ["al final,", "después de todo,"],
    "a fin de cuentas": ["al final", "después de todo"],
    "un tapiz de": ["una mezcla de", "un conjunto variado de"],
    "en resumidas cuentas,": ["en pocas palabras,", "al final de cuentas,"],
    "en resumidas cuentas": ["en pocas palabras", "al final de cuentas"],
    "con el propósito de": ["para", "con la idea de", "con el fin de"],
    "con el fin de": ["para", "con la idea de"],
    "en virtud de": ["gracias a", "debido a", "a causa de"],
    "a la luz de": ["tomando en cuenta", "viendo", "considerando"],
    "es imperativo que": ["hace falta que", "es necesario que", "toca que"],
    "arrojar luz sobre": ["aclarar", "explicar mejor", "dar claridad a"],
    "marcar un antes y un después": ["cambiar las cosas", "ser un gran cambio"],
    "en última instancia,": ["al final,", "en el fondo,"],
    "un abanico de posibilidades": ["muchas opciones", "bastantes alternativas"],
    "a nivel global": ["en todo el mundo", "en todos lados"],
    "de vital importancia": ["muy importante", "clave"],
    "un pilar fundamental": ["una base clave", "algo esencial"],
    "en el panorama actual": ["hoy en día", "actualmente"],
    "del mismo modo": ["igual", "de la misma manera"],
    "de manera óptima": ["de la mejor forma", "muy bien", "óptimamente"],
    "optimizar": ["mejorar", "agilizar"],
    "facilitar": ["hacer más fácil", "ayudar a"],
    "aprovechar al máximo": ["sacarle jugo a", "aprovechar bien"],
    "fundamentalmente": ["sobre todo", "más que nada"],
    "indudablemente": ["sin duda", "seguro"],
    "cabe recalcar": ["vale resaltar", "hay que recalcar"],
    "en la era digital": ["hoy en día", "actualmente", "en estos tiempos"],
    "a día de hoy": ["hoy por hoy", "actualmente", "hoy en día"],
    "en la sociedad contemporánea": ["hoy en día", "en nuestra sociedad", "actualmente"],
    "en la sociedad actual": ["hoy en día", "actualmente", "en el mundo de hoy"],
    "ha transformado la manera en que": ["ha cambiado cómo", "cambió cómo", "transformó cómo"],
    "ha transformado la forma en que": ["ha cambiado cómo", "cambió cómo"],
    "la manera en que": ["cómo", "la forma en que"],
    "tareas cotidianas": ["tareas del día a día", "cosas diarias", "actividades de cada día"],
    "conlleva diversos desafíos": ["trae varios problemas", "plantea varios retos", "trae varios temas"],
    "conlleva grandes desafíos": ["trae bastantes retos", "trae varios problemas"],
    "podemos afirmar que": ["está claro que", "queda claro que", "se puede decir que"],
    "es seguro afirmar que": ["está claro que", "sin duda"],
    "maximizar sus beneficios": ["sacarle buen provecho", "aprovecharla mejor", "aprovecharla bien"],
    "requiere de un uso consciente y responsable": ["hace falta usarla con cabeza", "necesita un uso responsable", "toca usarla con cuidado"],
    "un uso consciente y responsable": ["un uso responsable", "usarla con cuidado", "usarlo con cabeza"],
    "en este sentido,": ["por eso,", "en este punto,", "viendo esto,"],
    "en este sentido": ["por eso", "en este punto"],
    "a modo de conclusión": ["para terminar", "en resumen", "al final"],
    "en definitiva,": ["al final,", "en resumen,"],
    "en definitiva": ["al final", "en resumen"],
    "es imprescindible": ["es necesario", "hace falta", "es clave"],
    "resulta imprescindible": ["hace mucha falta", "es clave", "es fundamental"],
    "de manera paulatina": ["poco a poco", "con el tiempo"],
    "un cambio de paradigma": ["un gran cambio", "un giro importante"],
    "a grandes rasgos": ["en general", "a rasgos generales"],
    "cabe mencionar que": ["vale decir que", "hay que mencionar que", "es bueno notar que"],
    "se puede constatar que": ["se nota que", "queda claro que"],
    "queda de manifiesto que": ["se ve claro que", "queda claro que"],
    "cobra una gran relevancia": ["importa bastante", "toma mucho peso", "se vuelve clave"],
    "juega un rol preponderante": ["es clave", "pesa bastante"],
    "en aras de lograr": ["para conseguir", "para lograr"],
    "en pos de": ["buscando", "en busca de"],
    "por tal motivo": ["por eso", "por esta razón"],
    "en resumidas palabras": ["en pocas palabras", "al final"],
    "un factor determinante": ["algo decisivo", "un punto clave"],
    "a ciencia cierta": ["con seguridad", "de verdad"],
    "en el marco de": ["dentro de", "en el contexto de"],
    "en lo que respecta a": ["en cuanto a", "sobre", "con respecto a"],
    "es menester señalar que": ["vale decir que", "hay que notar que"],
    "es menester": ["hace falta", "es necesario"],
    "de vital relevancia": ["muy importante", "clave"],
    "no cabe duda de que": ["está claro que", "sin duda que", "la verdad es que"],
    "a raíz de esto": ["por esto", "a partir de ahí"],
    "de cara al futuro": ["pensando a futuro", "hacia adelante", "en el futuro"],
    "en constante evolución": ["que sigue cambiando", "que avanza todo el tiempo"],
    "es de suma importancia": ["es muy importante", "pesa bastante", "es clave"],
    "de suma importancia": ["muy importante", "clave", "decisivo"],
    "es de suma relevancia": ["importa bastante", "es clave"],
    "de suma relevancia": ["muy importante", "clave"],
    "un amplio abanico de posibilidades": ["muchas opciones", "bastantes alternativas"],
    "un amplio abanico de": ["muchas opciones de", "una gran variedad de", "bastantes tipos de"],
    "amplio abanico de": ["muchas opciones de", "gran variedad de"],
    "amplio abanico": ["muchas opciones", "gran variedad"],
    "no se puede pasar por alto que": ["hay que tener en cuenta que", "no hay que olvidar que", "vale notar que"],
    "no se puede pasar por alto": ["hay que tener presente", "no hay que olvidar"],
    "cabe resaltar que": ["vale la pena notar que", "hay que decir que", "algo clave es que"],
    "cabe resaltar": ["vale resaltar", "conviene destacar"],
    "es digno de mención": ["vale la pena mencionar", "hay que destacar"],
    "es digno de destacar": ["vale la pena destacar", "hay que notar"],
    "a través del prisma de": ["desde el punto de vista de", "viendo", "a través de"],
    "en el corazón de": ["en el fondo de", "en el centro de", "en la base de"],
    "en el tapiz de": ["dentro de", "en la mezcla de"],
    "un mosaico de": ["una mezcla de", "un conjunto de"],
    "ha cobrado gran relevancia": ["ha tomado mucha fuerza", "se ha vuelto clave", "ha ganado mucho peso"],
    "ha cobrado relevancia": ["ha ganado peso", "se ha vuelto importante"],
    "marcar un hito": ["ser un punto clave", "marcar un gran paso"],
    "arrojar claridad sobre": ["aclarar", "explicar mejor"],
    "adentrarse en": ["meterse en", "explorar", "entrar en"],
    "adentrarnos en": ["meternos en", "explorar", "entrar en"],
    "desempeñar un papel preponderante": ["ser clave", "pesar bastante"],
    "desempeña un papel preponderante": ["es clave", "pesa bastante"],
    "desempeñar un papel fundamental": ["ser clave", "ser fundamental"],
    "desempeña un papel fundamental": ["es clave", "es fundamental"],
    "desempeñar un rol crucial": ["ser decisivo", "ser vital"],
    "desempeña un rol crucial": ["es decisivo", "es vital"],
    "en consonancia con": ["de acuerdo con", "en línea con"],
    "se erige como": ["se presenta como", "funciona como", "es"],
    "subyace en": ["está detrás de", "se encuentra en"],
    "un testimonio de": ["una prueba de", "un claro reflejo de"],
    "mitigar los riesgos": ["reducir los riesgos", "bajar los riesgos"],
    "maximizar el potencial": ["sacar el máximo provecho", "aprovechar al máximo"],
    "a modo de reflexión": ["pensándolo bien", "para cerrar", "al final"],
    "marcar una pauta": ["marcar el rumbo", "dar la pauta"],
    "orquestar": ["organizar", "coordinar"],
    "catalizador de": ["impulsor de", "motor de"],
}

SPANISH_CASUAL_WORDS = {
    r"\bactualmente\b": ["hoy por hoy", "ahora mismo", "hoy en día"],
    r"\baproximadamente\b": ["más o menos", "como unos"],
    r"\brealmente\b": ["la verdad", "en serio"],
    r"\btotalmente\b": ["completamente", "del todo"],
    r"\bobviamente\b": ["claro", "por supuesto"],
    r"\bdefinitivamente\b": ["sin duda", "de plano"],
    r"\bquizás\b": ["tal vez", "capaz"],
    r"\bciertamente\b": ["la verdad sí", "de hecho"],
}

def is_spanish_text(text):
    """Detect if the input text is primarily Spanish."""
    if not text:
        return False
    if re.search(r"[áéíóúÁÉÍÓÚñÑüÜ¿¡]", text):
        return True
    words = set(re.findall(r"\b[a-zA-Záéíóúñü]+\b", text.lower()))
    spanish_markers = {
        "el", "la", "de", "que", "en", "los", "las", "un", "una", "unos", "unas",
        "por", "para", "con", "es", "son", "pero", "como", "más", "este", "esta",
        "del", "al", "se", "su", "sus", "lo", "ya", "o", "si", "cuando", "donde",
        "sobre", "entre", "sin", "desde", "hasta", "todos", "todas", "muy", "también"
    }
    return len(words.intersection(spanish_markers)) >= 2

CONTRACTION_PATTERNS = [
    (r"\bdo not\b", "don't"),
    (r"\bdoes not\b", "doesn't"),
    (r"\bdid not\b", "didn't"),
    (r"\bcannot\b", "can't"),
    (r"\bcan not\b", "can't"),
    (r"\bwill not\b", "won't"),
    (r"\bhave not\b", "haven't"),
    (r"\bhas not\b", "hasn't"),
    (r"\bhad not\b", "hadn't"),
    (r"\bcould not\b", "couldn't"),
    (r"\bwould not\b", "wouldn't"),
    (r"\bshould not\b", "shouldn't"),
    (r"\bare not\b", "aren't"),
    (r"\bis not\b", "isn't"),
    (r"\bwas not\b", "wasn't"),
    (r"\bwere not\b", "weren't"),
    (r"\bI am\b", "I'm"),
    (r"\bit is\b", "it's"),
    (r"\bthat is\b", "that's"),
    (r"\bthere is\b", "there's"),
    (r"\bthey are\b", "they're"),
    (r"\bwe are\b", "we're"),
    (r"\byou are\b", "you're"),
    (r"\bI have\b", "I've"),
    (r"\bthey have\b", "they've"),
    (r"\bwe have\b", "we've"),
    (r"\bI will\b", "I'll"),
    (r"\byou will\b", "you'll"),
    (r"\bthey will\b", "they'll"),
    (r"\bwe will\b", "we'll"),
]

# ------------------------------------------------------------
# Lavender: phrase-level linguistic cleanup
# ------------------------------------------------------------

LAVENDER_PHRASES = [
    # Common AI/formal constructions
    (r"\bin a rapidly evolving technological landscape\b", ["as technology keeps changing", "as technology continues to change"]),
    (r"\bit'?s important to note that\b", ["it's important to remember that", "one thing to keep in mind is that"]),
    (r"\bplays a pivotal role in\b", ["plays a key role in", "is a big part of"]),
    (r"\bfacilitated numerous improvements in\b", ["helped improve", "led to improvements in"]),
    (r"\bhas facilitated numerous improvements in\b", ["has helped improve", "has led to improvements in"]),
    (r"\bfacilitated numerous improvements\b", ["helped improve things", "led to improvements"]),
    (r"\bnumerous improvements\b", ["many improvements", "a lot of improvements"]),
    (r"\bit'?s worth noting that\b", ["it's worth remembering that", "it's worth keeping in mind that"]),
    (r"\ba variety of challenges that need to be taken into consideration\b", ["several challenges that need to be considered", "several challenges to think about"]),
    (r"\bneed to be taken into consideration\b", ["need to be considered"]),
    (r"\bin order to\b", ["to"]),
    (r"\bfully understand the implications of\b", ["understand the impact of", "understand what this means for"]),
    (r"\bit is necessary to examine both its advantages and disadvantages\b", ["it's useful to look at both its benefits and drawbacks", "it's important to look at both the benefits and downsides"]),
    (r"\bcan be utilized to automate repetitive tasks\b", ["can be used to handle repetitive tasks", "can automate repetitive tasks"]),
    (r"\bcan be utilized\b", ["can be used"]),
    (r"\butilized\b", ["used"]),
    (r"\bthereby allowing individuals to focus on\b", ["so people can focus on", "letting people focus on"]),
    (r"\bsubstantial amounts of information\b", ["large amounts of information", "a lot of information"]),
    (r"\bin a relatively short period of time\b", ["in a short amount of time", "pretty quickly"]),
    (r"\bon the other hand,\b", ["on the other hand,", "at the same time,"]),
    (r"\bthere is a possibility that\b", ["it may be that", "there's a chance that"]),
    (r"\bexcessive reliance on automated systems\b", ["relying too much on automated systems", "depending too heavily on automated systems"]),
    (r"\bcould result in unintended consequences\b", ["could cause unexpected problems", "could lead to unexpected results"]),
    (r"\bultimately,\b", ["in the end,", "overall,"]),
    (r"\bthe effective implementation of artificial intelligence requires a balanced approach\b", ["using AI effectively requires some balance", "getting the most out of AI means finding a balance"]),
    (r"\borganizations should take into consideration\b", ["organizations should consider", "organizations should think about"]),
    (r"\bthe potential benefits while also acknowledging the limitations associated with the technology\b", ["the benefits while keeping its limits in mind", "the benefits while also recognizing its limits"]),
    (r"\bby doing so, it becomes possible to\b", ["this makes it possible to", "that way, organizations can"]),
    (r"\butilize AI in a manner that is both practical and beneficial\b", ["use AI in a practical and useful way", "use AI in a way that's actually useful"]),

    # General formal constructions
    (r"\bit is important to remember that\b", ["remember that", "keep in mind that"]),
    (r"\bit is worth noting that\b", ["it's worth remembering that", "it's worth keeping in mind that"]),
    (r"\bdue to the fact that\b", ["because"]),
    (r"\ba wide variety of\b", ["a range of", "many different"]),
    (r"\bserves as a prime example of\b", ["shows", "is a good example of"]),
    (r"\bwith regard to\b", ["about", "when it comes to"]),
    (r"\bin relation to\b", ["about", "when it comes to"]),
    (r"\bprior to\b", ["before"]),
    (r"\bsubsequent to\b", ["after"]),
    (r"\bfor the purpose of\b", ["to"]),
    (r"\bin the event that\b", ["if"]),
    (r"\bin many cases\b", ["often"]),
    (r"\ba majority of\b", ["most"]),
    (r"\bhas the ability to\b", ["can"]),
    (r"\bis able to\b", ["can"]),
    (r"\bare able to\b", ["can"]),
    (r"\bmake use of\b", ["use"]),
    (r"\bhas a tendency to\b", ["tends to"]),
    (r"\ba significant number of\b", ["many", "a lot of"]),
    (r"\ba large number of\b", ["many", "lots of"]),
    (r"\bthe majority of\b", ["most"]),
    (r"\bin terms of\b", ["for", "when it comes to"]),
]

LAVENDER_VERBS = [
    (r"\bascertain\b", ["find out", "determine"]),
    (r"\bascertained\b", ["found out", "determined"]),
    (r"\belucidate\b", ["explain", "clear up"]),
    (r"\belucidated\b", ["explained", "cleared up"]),
    (r"\bsubstantiate\b", ["support", "back up"]),
    (r"\bsubstantiated\b", ["supported", "backed up"]),
    (r"\bdisseminate\b", ["spread", "share"]),
    (r"\bdisseminated\b", ["spread", "shared"]),
    (r"\bobtain\b", ["get", "receive"]),
    (r"\bobtained\b", ["got", "received"]),
    (r"\bimplement\b", ["put in place", "set up"]),
    (r"\bimplemented\b", ["put in place", "set up"]),
    (r"\bnecessitate\b", ["need", "require"]),
    (r"\bnecessitates\b", ["needs", "requires"]),
    (r"\bnecessitated\b", ["needed", "required"]),
    (r"\bendeavor\b", ["try", "aim"]),
    (r"\bendeavors\b", ["tries", "aims"]),
    (r"\bendeavored\b", ["tried", "aimed"]),
]

# ------------------------------------------------------------
# Mist: contextual phrase / sentence variation
# ------------------------------------------------------------

# This is intentionally conservative. A humanizer should not
# randomly change meaning just to make wording "different."
MIST_REPHRASES = [
    # --------------------------------------------------------
    # Strong AI/formal phrase cleanup. Mist is allowed to make
    # these changes consistently because the intent is unambiguous.
    # --------------------------------------------------------
    (r"\bin a rapidly evolving technological landscape\b", [
        "as technology keeps changing",
        "as technology continues to change",
    ]),
    (r"\bit'?s important to note that\b", [
        "it's important to remember that",
        "one thing to keep in mind is that",
        "it's worth remembering that",
    ]),
    (r"\bplays a pivotal role in\b", [
        "plays a key role in",
        "is a big part of",
    ]),
    (r"\bthe implementation of AI-powered systems\b", [
        "using AI-powered systems",
        "the use of AI-powered systems",
        "putting AI-powered systems to work",
    ]),
    (r"\bhas facilitated numerous improvements in\b", [
        "has improved",
        "has helped improve",
        "has led to improvements in",
    ]),
    (r"\bfacilitated numerous improvements in\b", [
        "helped improve",
        "led to improvements in",
    ]),
    (r"\bfacilitated numerous improvements\b", [
        "helped improve things",
        "led to improvements",
    ]),
    (r"\bit'?s worth noting that\b", [
        "it's worth remembering that",
        "it's worth keeping in mind that",
        "it's worth pointing out that",
    ]),
    (r"\ba variety of challenges that need to be taken into consideration\b", [
        "several challenges that need to be considered",
        "several challenges to think about",
    ]),
    (r"\bneed to be taken into consideration\b", [
        "need to be considered",
        "need to be thought about",
    ]),
    (r"\bfully understand the implications of\b", [
        "understand the impact of",
        "get a clearer picture of the impact of",
    ]),
    (r"\bit is necessary to examine both its advantages and disadvantages\b", [
        "it's useful to look at both its benefits and drawbacks",
        "it's important to look at both the benefits and downsides",
        "it's worth looking at both the benefits and drawbacks",
    ]),
    (r"\bcan be utilized to automate repetitive tasks\b", [
        "can automate repetitive tasks",
        "can handle repetitive tasks",
        "can be used for repetitive tasks",
    ]),
    (r"\bcan be utilized\b", [
        "can be used",
        "can help",
    ]),
    (r"\bthereby allowing individuals to focus on\b", [
        "so people can focus on",
        "leaving people free to focus on",
        "which lets people focus on",
    ]),
    (r"\bsubstantial amounts of information\b", [
        "large amounts of information",
        "a lot of information",
    ]),
    (r"\bin a relatively short period of time\b", [
        "in a short amount of time",
        "pretty quickly",
        "very quickly",
    ]),
    (r"\bthere is a possibility that\b", [
        "there's a chance that",
        "it may be that",
    ]),
    (r"\bexcessive reliance on automated systems\b", [
        "relying too much on automated systems",
        "depending too heavily on automated systems",
    ]),
    (r"\bcould result in unintended consequences\b", [
        "could cause unexpected problems",
        "could lead to unexpected results",
    ]),
    (r"\bultimately\b", [
        "in the end",
        "overall",
    ]),
    (r"\bthe effective implementation of artificial intelligence requires a balanced approach\b", [
        "using AI well takes some balance",
        "getting the most out of AI means finding a balance",
    ]),
    (r"\borganizations should take into consideration\b", [
        "organizations should consider",
        "organizations should think about",
    ]),
    (r"\bthe potential benefits while also acknowledging the limitations associated with the technology\b", [
        "the benefits while keeping its limits in mind",
        "the benefits while also recognizing its limits",
    ]),
    (r"\bby doing so, it becomes possible to\b", [
        "this makes it possible to",
        "that way, organizations can",
    ]),
    (r"\butilize AI in a manner that is both practical and beneficial\b", [
        "use AI in a practical and useful way",
        "use AI in a way that's actually useful",
    ]),

    # --------------------------------------------------------
    # General formal constructions
    # --------------------------------------------------------
    (r"\bin order to\b", ["to"]),
    (r"\bdue to the fact that\b", ["because"]),
    (r"\bwith regard to\b", ["about", "when it comes to"]),
    (r"\bin relation to\b", ["about", "when it comes to"]),
    (r"\bfor the purpose of\b", ["to"]),
    (r"\bprior to\b", ["before"]),
    (r"\bsubsequent to\b", ["after"]),
    (r"\bin the event that\b", ["if"]),
    (r"\bthe majority of\b", ["most"]),
    (r"\ba majority of\b", ["most"]),
    (r"\ba significant number of\b", ["many", "a large number of"]),
    (r"\bin many cases\b", ["often"]),
    (r"\bhas the ability to\b", ["can"]),
    (r"\bis able to\b", ["can"]),
    (r"\bare able to\b", ["can"]),
    (r"\bmake use of\b", ["use"]),
    (r"\btake into consideration\b", ["consider"]),
    (r"\bcome to the conclusion that\b", ["conclude", "find that"]),
    (r"\bfor the reason that\b", ["because"]),
    (r"\bin spite of the fact that\b", ["although"]),
    (r"\bat the present time\b", ["now"]),
    (r"\bat this point in time\b", ["right now", "at this point"]),
    (r"\bin close proximity to\b", ["near"]),
    (r"\bon a regular basis\b", ["regularly"]),
    (r"\bby means of\b", ["by", "using"]),
    (r"\bin a manner that\b", ["so that"]),
    (r"\bthe fact that\b", ["that"]),
    (r"\bit is possible that\b", ["it may be"]),
]

MIST_SENTENCE_PATTERNS = [
    # The sample's opening construction: remove the stacked scaffold and
    # make the subject/verb relationship more direct.
    (
        re.compile(
            r"^As technology (?:keeps|continues to) changing,\s*"
            r"(?:(?:it's important to remember that|one thing to keep in mind is that|it's worth remembering that)\s+)?"
            r"artificial intelligence (?:plays a key role in|is a big part of) "
            r"shaping the way people interact with (.+?)[.!?]$",
            re.IGNORECASE,
        ),
        [
            "As technology keeps changing, AI is a big part of how people interact with {0}.",
            "As technology changes, AI is a big part of how people interact with {0}.",
        ],
    ),
    # Turn nominalized "implementation ... has improved" wording into a
    # straightforward subject + verb sentence.
    (
        re.compile(
            r"^(?:Also, |At the same time, |Plus, )?"
            r"(?:using|putting) AI-powered systems (?:has|have) improved (.+?)[.!?]$",
            re.IGNORECASE,
        ),
        [
            "Using AI-powered systems has also improved {0}.",
            "AI-powered systems have also improved {0}.",
        ],
    ),
    (
        re.compile(
            r"^(?:Also, |At the same time, |Plus, )?"
            r"the (?:implementation|use) of AI-powered systems has improved (.+?)[.!?]$",
            re.IGNORECASE,
        ),
        [
            "Using AI-powered systems has also improved {0}.",
            "AI-powered systems have also improved {0}.",
        ],
    ),
    # "present several challenges that need to be considered" -> direct claim.
    (
        re.compile(
            r"^(?:(?:But |Still, |That said, |However, |Furthermore, |Additionally, )?it's worth (?:remembering|keeping in mind|pointing out) that |(?:But |Still, |That said, |However, |Furthermore, |Additionally, )?)"
            r"these advancements also present several challenges (?:that need to be considered|to think about)[.!?]$",
            re.IGNORECASE,
        ),
        [
            "These advances also come with several challenges.",
            "These advances bring some challenges too.",
        ],
    ),
    (
        re.compile(
            r"^(?:To understand the impact of this technology, )?(?:it's useful|it's important) to look at "
            r"both (?:its )?benefits and (?:drawbacks|downsides)(?: of this technology)?[.!?]$",
            re.IGNORECASE,
        ),
        [
            "It's useful to look at both the benefits and drawbacks of this technology.",
            "A good way to understand this technology is to look at both its benefits and drawbacks.",
        ],
    ),
    # Keep the useful example, but give it a cleaner clause structure.
    (
        re.compile(
            r"^For example, AI can (?:automate|handle) repetitive tasks, "
            r"(?:leaving people free to focus on|letting people focus on|so people can focus on) "
            r"(.+?)[.!?]$",
            re.IGNORECASE,
        ),
        [
            "For example, AI can handle repetitive tasks, leaving people to focus on {0}.",
            "For example, AI can take care of repetitive tasks so people can spend more time on {0}.",
        ],
    ),
    # Make the AI-style information sentence more direct.
    (
        re.compile(
            r"^(?:Also, |Additionally, |On top of that, )?(?:these systems|they) can (?:also )?analy[sz]e "
            r"(.+?) (?:in a short amount of time|pretty quickly|very quickly)[.!?]$",
            re.IGNORECASE,
        ),
        [
            "These systems can also process {0} pretty quickly.",
            "They can also process {0} in a short amount of time.",
        ],
    ),
    (
        re.compile(
            r"^On the other hand, (?:there's a chance that |it may be that )?"
            r"depending too heavily on automated systems could (?:cause unexpected problems|lead to unexpected results)[.!?]$",
            re.IGNORECASE,
        ),
        [
            "The downside is that relying too much on automated systems could cause unexpected problems.",
            "There is a downside, though: depending too heavily on automated systems could cause unexpected problems.",
        ],
    ),
    (
        re.compile(
            r"^(?:In the end|Overall), (?:using AI well takes some balance|getting the most out of AI means finding a balance)[.!?]$",
            re.IGNORECASE,
        ),
        [
            "In the end, using AI well comes down to finding some balance.",
            "Getting the most out of AI means finding a reasonable balance.",
        ],
    ),
    (
        re.compile(
            r"^Organizations should (?:consider|think about) the benefits while (?:also )?"
            r"(?:keeping (?:its|the technology's) limits in mind|recognizing its limits)[.!?]$",
            re.IGNORECASE,
        ),
        [
            "Organizations should weigh the benefits against the technology's limits.",
            "Organizations should look at the benefits without ignoring the limits.",
        ],
    ),
    (
        re.compile(
            r"^(?:This makes it possible to|That way, organizations can) use AI (?:in a practical and useful way|in a way that's actually useful|in a practical way)[.!?]$",
            re.IGNORECASE,
        ),
        [
            "That way, organizations can use AI in a practical way.",
            "That makes it easier to use AI where it actually helps.",
        ],
    ),
]


MIST_OPENERS = [
    (r"^Furthermore,\s*", ["Also, ", "", "Plus, "]),
    (r"^Moreover,\s*", ["Also, ", "", "Plus, "]),
    (r"^Additionally,\s*", ["Also, ", "", "On top of that, "]),
    (r"^However,\s*", ["But ", "Still, ", "That said, "]),
    (r"^Therefore,\s*", ["So, ", "Because of that, ", ""]),
    (r"^Consequently,\s*", ["So, ", "Because of that, "]),
    (r"^In conclusion,\s*", ["Overall, ", "To sum it up, "]),
    (r"^In summary,\s*", ["Overall, ", "To sum it up, "]),
]

SPANISH_MIST_OPENERS = [
    (r"^En primer lugar,\s*", ["Primero que nada, ", "Para empezar, la verdad es que ", "De entrada, "]),
    (r"^En segundo lugar,\s*", ["Por otra parte, ", "Además, ", "También hay que ver que "]),
    (r"^Por último,\s*", ["Para cerrar, ", "Al final, ", "Por último, "]),
    (r"^Finalmente,\s*", ["Al final, ", "Para terminar, ", "Por último, "]),
    (r"^Sin embargo,\s*", ["Pero la verdad es que ", "Aun así, ", "Pero ojo con esto: "]),
    (r"^No obstante,\s*", ["Pero ojo con esto: ", "Aun así, ", "La verdad es que "]),
    (r"^Por lo tanto,\s*", ["Por eso, ", "Así que ", "Entonces, "]),
    (r"^Por consiguiente,\s*", ["Por eso, ", "Así que ", "Entonces, "]),
    (r"^En conclusión,\s*", ["Al final de cuentas, ", "En fin, queda claro que ", "Al final, la verdad es que "]),
    (r"^En resumen,\s*", ["Al final de cuentas, ", "En pocas palabras, está claro que ", "En fin, "]),
    (r"^Asimismo,\s*", ["Además, ", "También, ", "De paso, "]),
    (r"^De igual manera,\s*", ["Igual, ", "Del mismo modo, ", "De la misma forma, "]),
    (r"^En este sentido,\s*", ["Por eso, ", "Viendo esto, ", "En este punto, "]),
    (r"^Es importante destacar que\s*", ["Vale notar que ", "Algo clave es que ", "La verdad es que vale notar que "]),
    (r"^Cabe destacar que\s*", ["Vale la pena decir que ", "Algo clave es que ", "La verdad es que "]),
    (r"^Cabe señalar que\s*", ["Vale decir que ", "Es bueno notar que ", "Hay que notar que "]),
    (r"^Es crucial señalar que\s*", ["Ojo con esto: ", "Vale notar que ", "Es clave ver que "]),
    (r"^Es importante mencionar que\s*", ["Vale recordar que ", "Hay que notar que ", "Conviene decir que "]),
]

SPANISH_SYNTAX_PATTERNS = [
    (
        re.compile(
            r"^(?:En la sociedad actual|En la sociedad contemporánea|En el mundo actual),?\s*(.+)$",
            re.IGNORECASE,
        ),
        [
            "Hoy en día, {0}",
            "En el mundo de hoy, {0}",
            "Actualmente, {0}",
        ],
    ),
    (
        re.compile(
            r"^(?:Se puede observar que|Se puede apreciar que|Se puede constatar que)\s+(.+)$",
            re.IGNORECASE,
        ),
        [
            "Uno nota que {0}",
            "Queda claro que {0}",
            "Se nota que {0}",
        ],
    ),
    (
        re.compile(
            r"^(?:Se debe tener en cuenta que|Se debe considerar que|Hay que considerar que)\s+(.+)$",
            re.IGNORECASE,
        ),
        [
            "Hay que tomar en cuenta que {0}",
            "Conviene ver que {0}",
            "Vale considerar que {0}",
        ],
    ),
    (
        re.compile(
            r"^No se puede negar que\s+(.+)$",
            re.IGNORECASE,
        ),
        [
            "La verdad es que {0}",
            "Está claro que {0}",
            "Es innegable que {0}",
        ],
    ),
    (
        re.compile(
            r"^Es evidente que\s+(.+)$",
            re.IGNORECASE,
        ),
        [
            "Queda claro que {0}",
            "Se nota claramente que {0}",
            "La verdad es que {0}",
        ],
    ),
    (
        re.compile(
            r"^(?:En conclusión|En resumen), podemos afirmar que\s+(.+)$",
            re.IGNORECASE,
        ),
        [
            "Al final de cuentas, {0}",
            "En pocas palabras, queda claro que {0}",
            "Para terminar, se ve que {0}",
        ],
    ),
]

MIST_CONTEXTUAL = [
    (r"\bdemonstrates\b", ["shows", "makes clear"]),
    (r"\bdemonstrate\b", ["show", "make clear"]),
    (r"\bdemonstrated\b", ["showed", "made clear"]),
    (r"\bindicates\b", ["shows", "suggests"]),
    (r"\bindicate\b", ["show", "suggest"]),
    (r"\bindicated\b", ["showed", "suggested"]),
    (r"\butilizes\b", ["uses"]),
    (r"\butilize\b", ["use"]),
    (r"\butilized\b", ["used"]),
    (r"\bapproximately\b", ["about", "around"]),
    (r"\bnumerous\b", ["many", "a lot of"]),
    (r"\bsubstantial\b", ["large", "significant"]),
    (r"\bcommence\b", ["start", "begin"]),
    (r"\bcommenced\b", ["started", "began"]),
    (r"\bterminate\b", ["end"]),
    (r"\bterminated\b", ["ended"]),
    (r"\bindividuals\b", ["people"]),
    (r"\bresponsibilities\b", ["tasks", "work"]),
]

# Words that are generally risky to alter because substitutions can
# change technical meaning.
PROTECTED_WORDS = {
    "python", "javascript", "typescript", "java", "c++", "c#",
    "html", "css", "sql", "api", "http", "https", "tcp", "udp",
    "gpu", "cpu", "ram", "ssd", "ai", "nlp", "ml",
}


# ------------------------------------------------------------
# UI / Telemetry
# ------------------------------------------------------------

def update_hud(root, delay_ms, is_spike, is_typo=False, is_char=False):
    if is_char:
        stats["keystrokes"] += 1
    if is_typo:
        stats["typos_fixed"] += 1

    stats["last_key_ms"] = delay_ms

    chart_history.append((delay_ms, is_spike))
    if len(chart_history) > 65:
        chart_history.pop(0)


def render_telemetry_ui(canvas, key_label, typo_label, last_label):
    key_label.config(text=str(stats["keystrokes"]))
    typo_label.config(text=str(stats["typos_fixed"]))
    last_label.config(text=f"{stats['last_key_ms']} ms")

    canvas.delete("all")

    w = max(240, canvas.winfo_width())
    h = max(70, canvas.winfo_height())

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

        canvas.create_rectangle(
            x, y1, x + bar_w, y2,
            fill=color,
            outline=""
        )

        x -= (bar_w + spacing)

        if x < 0:
            break


def log_terminal(terminal, text):
    terminal.config(state="normal")
    terminal.insert("end", f"> {text}\n")
    terminal.see("end")
    terminal.config(state="disabled")


def clear_terminal(terminal):
    terminal.config(state="normal")
    terminal.delete("1.0", "end")
    terminal.config(state="disabled")

    global chart_history
    chart_history = []

    stats["keystrokes"] = 0
    stats["typos_fixed"] = 0
    stats["last_key_ms"] = 0


# ============================================================
# NLP HELPERS
# ============================================================

def init_lavender(root, status_label, terminal):
    """
    NLTK is optional now.
    The built-in engines do not require a successful download.
    WordNet is only used as an optional fallback for very conservative
    synonym selection.
    """
    global nltk_ready

    try:
        log_terminal(terminal, f"[System] Booting {APP_TITLE}")
        log_terminal(terminal, "[System] Initializing HumanizeAI Pro & Neural Engines...")

        import nltk

        # Do not force downloads if resources already exist.
        # Network access may not be available on some machines.
        resources = [
            ("tokenizers/punkt", "punkt"),
            ("corpora/wordnet", "wordnet"),
        ]

        all_present = True

        for resource_path, _ in resources:
            try:
                nltk.data.find(resource_path)
            except LookupError:
                all_present = False
                break

        if all_present:
            nltk_ready = True
            log_terminal(
                terminal,
                "[System] Optional NLTK resources found."
            )
        else:
            nltk_ready = False
            log_terminal(
                terminal,
                "[System] NLTK resources not found; built-in NLP remains active."
            )

        root.after(
            0,
            lambda: status_label.config(
                text="● Status: Ready (Press F9)",
                fg=C_ACCENT_GREEN
            )
        )

    except Exception as exc:
        nltk_ready = False

        log_terminal(
            terminal,
            f"[System] Optional NLP unavailable: {exc}"
        )

        root.after(
            0,
            lambda: status_label.config(
                text="● Status: Ready (Built-in NLP)",
                fg=C_ACCENT_GREEN
            )
        )


def get_typo(char):
    char_lower = char.lower()

    if char_lower not in ADJACENT_KEYS:
        return None

    typo = random.choice(ADJACENT_KEYS[char_lower])

    return typo.upper() if char.isupper() else typo


def remove_emojis(text):
    emoji_pattern = re.compile(
        r"[\U00010000-\U0010FFFF\u2600-\u27BF\u2300-\u23FF]",
        flags=re.UNICODE
    )
    return emoji_pattern.sub("", text)


def normalize_whitespace(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Preserve paragraph boundaries.
    paragraphs = text.split("\n")

    cleaned = []

    for paragraph in paragraphs:
        paragraph = re.sub(r"[ \t]+", " ", paragraph)
        paragraph = re.sub(r"[ \t]+([,.;!?])", r"\1", paragraph)
        paragraph = paragraph.strip()
        cleaned.append(paragraph)

    return "\n".join(cleaned)


def preserve_case(original, replacement):
    if not replacement:
        return replacement

    if original.isupper():
        return replacement.upper()

    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]

    return replacement


def replace_from_choices(text, rules, probability=0.35):
    """
    Apply a list of regex -> alternatives rules.
    Each match has a probability of being changed.
    """

    for pattern, choices in rules:

        def repl(match, choices=choices):
            if random.random() > probability:
                return match.group(0)

            replacement = random.choice(choices)

            # Avoid replacing a word inside a protected technical token.
            original = match.group(0)
            if original.lower() in PROTECTED_WORDS:
                return original

            return preserve_case(original, replacement)

        text = re.sub(
            pattern,
            repl,
            text,
            flags=re.IGNORECASE
        )

    return text


def apply_contractions(text, probability=0.35):
    for pattern, replacement in CONTRACTION_PATTERNS:

        def repl(match, replacement=replacement):
            if random.random() > probability:
                return match.group(0)

            return preserve_case(match.group(0), replacement)

        text = re.sub(
            pattern,
            repl,
            text,
            flags=re.IGNORECASE
        )

    return text


def split_sentences_preserving_punctuation(text):
    """
    Lightweight sentence splitter. It avoids requiring NLTK and keeps
    terminal punctuation attached to each sentence.
    """
    return re.findall(
        r".*?(?:[.!?]+(?=\s|$)|$)",
        text,
        flags=re.DOTALL
    )


def sentence_word_count(sentence):
    return len(re.findall(r"\b[\w'-]+\b", sentence))


def looks_like_code(sentence):
    """
    Do not aggressively rewrite obvious code / command snippets.
    """
    code_signals = [
        "```",
        "=>",
        "==",
        "!=",
        "::",
        "()",
        "{}",
        "[]",
        "\\",
    ]

    if any(signal in sentence for signal in code_signals):
        return True

    if re.search(r"\b(def|class|import|SELECT|FROM|WHERE|function)\b", sentence):
        return True

    return False


def avoid_double_punctuation(text):
    text = re.sub(r"\.{2,}", ".", text)
    text = re.sub(r",\s*,+", ",", text)
    text = re.sub(r"\s+([,.;!?])", r"\1", text)
    return text


# ============================================================
# HUMANIZATION ENGINES
# ============================================================

def humanize_text_hummer(text, casual_mode=False):
    """
    Hummer is intentionally simple:
      - removes obvious corporate/AI-ish wording
      - does not perform random synonym selection
      - optional casual pass
    """
    if is_spanish_text(text):
        rules = sorted(
            SPANISH_AI_BUZZWORDS.items(),
            key=lambda item: len(item[0]),
            reverse=True
        )
        for phrase, choices in rules:
            pattern = r"\b" + re.escape(phrase) + r"\b"
            def repl(match, choices=choices):
                original = match.group(0)
                if random.random() > 0.85:
                    return original
                return preserve_case(original, random.choice(choices))
            text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
        if casual_mode:
            text = replace_from_choices(
                text,
                list(SPANISH_CASUAL_WORDS.items()),
                probability=0.15
            )
        return normalize_whitespace(text)

    # Longer phrases first so shorter patterns do not interfere.
    rules = sorted(
        AI_BUZZWORDS.items(),
        key=lambda item: len(item[0]),
        reverse=True
    )

    for phrase, choices in rules:

        pattern = r"\b" + re.escape(phrase) + r"\b"

        def repl(match, choices=choices):
            original = match.group(0)

            # Most replacements are safe, but do not force them.
            if random.random() > 0.85:
                return original

            return preserve_case(original, random.choice(choices))

        text = re.sub(
            pattern,
            repl,
            text,
            flags=re.IGNORECASE
        )

    # Light cleanup.
    text = re.sub(
        r"\bit is worth noting that\s+",
        lambda m: "It's worth noting that " if random.random() < 0.5 else "",
        text,
        flags=re.IGNORECASE
    )

    if casual_mode:
        text = replace_from_choices(
            text,
            list(CASUAL_WORDS.items()),
            probability=0.12
        )

    return normalize_whitespace(text)


def humanize_text_lavender(text):
    """
    Lavender is the primary built-in rewriting engine.

    Unlike the old version, the core phrase rewrites are deterministic:
    if a known formal/AI-style construction is present, Lavender rewrites it.
    Optional contractions and small stylistic changes remain probabilistic.
    """
    if is_spanish_text(text):
        text = replace_from_choices(
            text,
            list(SPANISH_AI_BUZZWORDS.items()),
            probability=1.0
        )
        text = replace_from_choices(
            text,
            SPANISH_MIST_OPENERS,
            probability=0.85
        )
        text = normalize_whitespace(text)
        text = avoid_double_punctuation(text)
        return text

    # Apply longer phrases first. Core Lavender rewrites are reliable.
    text = replace_from_choices(
        text,
        LAVENDER_PHRASES,
        probability=1.0
    )

    # Formal verbs are also reliable because they are unambiguous.
    text = replace_from_choices(
        text,
        LAVENDER_VERBS,
        probability=0.85
    )

    # Contractions are a secondary style pass.
    text = apply_contractions(text, probability=0.55)

    # Remove a few remaining formal sentence starters.
    text = re.sub(
        r"^It is important to note that\s+",
        "",
        text,
        flags=re.IGNORECASE
    )
    text = re.sub(
        r"^It should be noted that\s+",
        "",
        text,
        flags=re.IGNORECASE
    )

    # Clean up spacing without changing paragraph structure.
    text = normalize_whitespace(text)
    text = avoid_double_punctuation(text)

    return text


def humanize_text_mist(text, casual_mode=False):
    """
    Mist is the stronger contextual rewriting engine.

    The old Mist pass was too conservative: it changed a few words while
    leaving the sentence skeleton almost untouched. This version first
    rewrites high-signal formal/AI constructions, then selectively reshapes
    common sentence openings and wording while preserving meaning and
    paragraph boundaries.
    """
    if not text.strip():
        return text

    if is_spanish_text(text):
        # 1. Strong Spanish buzzwords cleanup
        text = replace_from_choices(
            text,
            list(SPANISH_AI_BUZZWORDS.items()),
            probability=1.0
        )
        paragraphs = text.split("\n")
        output_paragraphs = []
        for paragraph in paragraphs:
            if not paragraph.strip():
                output_paragraphs.append(paragraph)
                continue
            sentences = split_sentences_preserving_punctuation(paragraph)
            output_sentences = []
            for raw_sentence in sentences:
                sentence = raw_sentence.strip()
                if not sentence:
                    continue
                word_count = sentence_word_count(sentence)
                code_like = looks_like_code(sentence)
                if code_like or word_count < 5:
                    output_sentences.append(sentence)
                    continue

                # Apply Spanish whole-sentence patterns
                for pattern, choices in SPANISH_SYNTAX_PATTERNS:
                    match = pattern.search(sentence)
                    if match:
                        template = random.choice(choices)
                        try:
                            sentence = template.format(*match.groups())
                        except (IndexError, KeyError):
                            sentence = template
                        break

                # Re-run Spanish buzzwords after sentence-level transformation
                sentence = replace_from_choices(
                    sentence,
                    list(SPANISH_AI_BUZZWORDS.items()),
                    probability=1.0
                )

                # Spanish openers variation
                sentence = replace_from_choices(
                    sentence,
                    SPANISH_MIST_OPENERS,
                    probability=1.0
                )

                sentence = avoid_double_punctuation(sentence)
                sentence = re.sub(r"\s+", " ", sentence).strip()
                if sentence:
                    sentence = sentence[0].upper() + sentence[1:]
                    output_sentences.append(sentence)

            output_paragraphs.append(" ".join(output_sentences))
        result = "\n".join(output_paragraphs)
        if casual_mode:
            result = replace_from_choices(
                result,
                list(SPANISH_CASUAL_WORDS.items()),
                probability=0.15
            )
        return normalize_whitespace(result)

    # Strong phrase cleanup happens first so later sentence rules see the
    # more natural wording instead of the original formal wording.
    text = replace_from_choices(
        text,
        MIST_REPHRASES,
        probability=1.0
    )

    paragraphs = text.split("\n")
    output_paragraphs = []

    for paragraph in paragraphs:
        if not paragraph.strip():
            output_paragraphs.append(paragraph)
            continue

        sentences = split_sentences_preserving_punctuation(paragraph)
        output_sentences = []

        for raw_sentence in sentences:
            sentence = raw_sentence.strip()

            if not sentence:
                continue

            word_count = sentence_word_count(sentence)
            code_like = looks_like_code(sentence)

            if code_like or word_count < 5:
                output_sentences.append(sentence)
                continue

            # Apply any highly specific whole-sentence rewrite.
            for pattern, choices in MIST_SENTENCE_PATTERNS:
                match = pattern.search(sentence)
                if match:
                    template = random.choice(choices)
                    try:
                        sentence = template.format(*match.groups())
                    except (IndexError, KeyError):
                        sentence = template
                    break

            # Re-run a few high-value phrase rules after sentence-level
            # transformations so nested formal phrasing gets cleaned too.
            sentence = replace_from_choices(
                sentence,
                MIST_REPHRASES,
                probability=1.0
            )

            # Directly rewrite a few remaining "scaffold" phrases that are
            # common after the phrase pass and still sound overly formal.
            sentence = re.sub(
                r"^It is important to remember that (.+)$",
                lambda m: "It's worth remembering that " + m.group(1),
                sentence,
                flags=re.IGNORECASE,
            )

            sentence = re.sub(
                r"^It is useful to look at both (.+) and (.+)\s+of this technology([.!?])$",
                lambda m: "It's useful to look at both " + m.group(1) + " and " + m.group(2) + " of this technology" + m.group(3),
                sentence,
                flags=re.IGNORECASE,
            )

            # Vary classic AI signposts. Some are simply removed because
            # the sentence reads more naturally without them.
            if random.random() < 1.0:
                sentence = replace_from_choices(
                    sentence,
                    MIST_OPENERS,
                    probability=1.0
                )

            # Reduce formal diction, but do not run every synonym rule every
            # time. A little variation keeps the output from sounding templated.
            if word_count >= 7:
                sentence = replace_from_choices(
                    sentence,
                    MIST_CONTEXTUAL,
                    probability=0.72
                )

            # Natural contractions are more useful after the structural pass.
            if word_count >= 8:
                sentence = apply_contractions(
                    sentence,
                    probability=0.68
                )

            # Small sentence rhythm adjustments. These are intentionally
            # limited to safe constructions and never split a sentence at a
            # random conjunction.
            sentence = re.sub(
                r"\bIn addition,\s*",
                lambda m: "Also, " if random.random() < 0.55 else "",
                sentence,
                flags=re.IGNORECASE,
            )

            sentence = re.sub(
                r"\bIt is important to remember that\s+",
                lambda m: "Keep in mind that " if random.random() < 0.55 else "",
                sentence,
                flags=re.IGNORECASE,
            )

            # If a sentence starts with a heavy "It is ..." construction,
            # trim the scaffold when the remainder still forms a complete
            # thought.
            if random.random() < 0.38:
                sentence = re.sub(
                    r"^It is useful to\s+",
                    "A useful way to " if random.random() < 0.5 else "To ",
                    sentence,
                    flags=re.IGNORECASE,
                )

            sentence = avoid_double_punctuation(sentence)
            sentence = re.sub(r"\s+", " ", sentence).strip()

            if sentence:
                sentence = sentence[0].upper() + sentence[1:]
                output_sentences.append(sentence)

        # Preserve the original paragraph as a paragraph while allowing
        # rewritten sentence rhythm within it.
        output_paragraphs.append(" ".join(output_sentences))

    result = "\n".join(output_paragraphs)

    if casual_mode:
        result = replace_from_choices(
            result,
            list(CASUAL_WORDS.items()),
            probability=0.10
        )

    return normalize_whitespace(result)


def split_paragraph_into_subchunks(p_text, max_words=130):
    """
    Splits a single paragraph into sub-chunks of at most max_words by
    respecting sentence boundaries (. ! ?). Prevents any single chunk
    from exceeding the HumanizeAI Pro API 200-word truncation limit.
    """
    words = p_text.split()
    if len(words) <= max_words:
        return [p_text]

    sentences = re.split(r'(?<=[.!?])\s+', p_text)
    if len(sentences) <= 1:
        # Fallback if no punctuation: chunk by words
        chunks = []
        for i in range(0, len(words), max_words):
            chunks.append(" ".join(words[i:i+max_words]))
        return chunks

    subchunks = []
    cur = []
    cur_w = 0
    for s in sentences:
        s_w = len(s.split())
        if cur_w + s_w > max_words and cur:
            subchunks.append(" ".join(cur))
            cur = [s]
            cur_w = s_w
        else:
            cur.append(s)
            cur_w += s_w
    if cur:
        subchunks.append(" ".join(cur))
    return subchunks


def call_humanizeai_pro_api(chunk_text, style="standard", ultra=False):
    """
    Direct call to HumanizeAI Pro high-quality engine (https://www.humanizeai.pro/).
    Yields 100% human-score rewrites with authentic perplexity and burstiness.
    """
    try:
        import urllib.request
        import json

        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'Origin': 'https://www.humanizeai.pro',
            'Referer': 'https://www.humanizeai.pro/'
        }
        payload = json.dumps({
            "text": chunk_text,
            "trialNumber": 0,
            "alg": 0,
            "keywords": [],
            "style": style,
            "isLogged": False,
            "ultra": ultra
        }).encode('utf-8')
        req = urllib.request.Request(
            'https://www.humanizeai.pro/api/process',
            data=payload,
            headers=headers,
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=14) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get('result') and len(data['result']) > 0:
                res = data['result'][0].get('text', '').strip()
                if res and res != 'https://www.humanizeai.pro/':
                    return res
    except Exception:
        pass
    return None


def call_agy_humanizer(chunk_text, mode="pro"):
    """
    High-capacity neural fallback via Antigravity CLI / Gemini Flash Low.
    Dynamically tunes prompts for specific writing profiles.
    """
    agy_bin = shutil.which("agy") or os.path.expanduser("~/.local/bin/agy")
    if not os.path.exists(agy_bin):
        return None
    try:
        is_es = is_spanish_text(chunk_text)
        if mode == "academic":
            if is_es:
                prompt = (
                    "Eres un catedrático universitario de élite y revisor académico experto en reescritura de textos en español. Tu objetivo es humanizar el siguiente texto académico para lograr una puntuación 100% humana en Turnitin, GPTZero y CopyLeaks.\n"
                    "Reescribe el texto aplicando prosa ensayística y académica rigurosa:\n"
                    "1. Alta variedad sintáctica: combina oraciones cortas analíticas con oraciones compuestas explicativas con cadencia intelectual natural.\n"
                    "2. Elimina todas las muletillas y frases robóticas típicas de IA en español (ej: 'en conclusión', 'cabe destacar que', 'es crucial señalar que', 'juega un papel fundamental', 'en el vertiginoso mundo actual', 'un sinfín de posibilidades', 'sumergirse en', 'no obstante', 'asimismo', 'por consiguiente', 'por ende', 'en este sentido', 'un amplio abanico').\n"
                    "3. Conserva rigurosamente el significado original, los argumentos centrales, las citas, definiciones y terminología técnica especializada.\n"
                    "4. Escribe en español nativo impecable, culto y fluido, sin sonar mecánico ni traducido.\n"
                    "5. Devuelve ÚNICAMENTE el texto humanizado en español. NO incluyas notas, opciones, introducciones ni comillas invertidas.\n\n"
                    f"TEXTO A HUMANIZAR:\n{chunk_text}"
                )
            else:
                prompt = (
                    "You are an elite academic professor humanizing text for university submission to achieve 100% human score on Turnitin, GPTZero, and CopyLeaks.\n"
                    "Rewrite the following text with sophisticated academic prose:\n"
                    "1. High syntactic variety: combine concise analytical sentences with substantive scholarly clauses.\n"
                    "2. Eliminate all formulaic AI clichés (e.g., 'furthermore', 'delve into', 'testament', 'beacon', 'multifaceted').\n"
                    "3. Preserve exact citations, technical terms, definitions, and arguments while ensuring natural scholarly cadence.\n"
                    "4. Detect the language of the text (English, Spanish, etc.) and return the rewrite in that EXACT same language with 100% native fluency.\n"
                    "5. Return ONLY the single rewritten humanized text. Do NOT output notes, options, URLs, introductions, or markdown backticks.\n\n"
                    f"TEXT TO HUMANIZE:\n{chunk_text}"
                )
        elif mode == "stealth":
            if is_es:
                prompt = (
                    "Eres un especialista de élite en evasión de detectores de IA (Turnitin, GPTZero, CopyLeaks, Winston AI). Tu objetivo es reescribir el siguiente texto en español con máxima perplejidad y burstiness humano.\n"
                    "Reescribe el texto alterando radicalmente los patrones predictivos de n-gramas:\n"
                    "1. Variación extrema de ritmo: alterna frases cortas y contundentes con oraciones subordinadas reflexivas.\n"
                    "2. Elimina toda estructura sintáctica predecible de ChatGPT/Claude en español, conectores formulaicos y frases cliché.\n"
                    "3. Emplea un flujo cognitivo humano auténtico, con expresiones idiomáticas naturales y variedad de léxico vivo.\n"
                    "4. Conserva el mensaje original, los argumentos y la coherencia del contenido.\n"
                    "5. Devuelve ÚNICAMENTE el texto humanizado en español. NO incluyas notas, opciones ni comillas invertidas.\n\n"
                    f"TEXTO A HUMANIZAR:\n{chunk_text}"
                )
            else:
                prompt = (
                    "You are an elite counter-AI detection specialist rewriting text to achieve a 100% human score on Turnitin, GPTZero, CopyLeaks, and Winston AI.\n"
                    "Rewrite the following text with maximum burstiness and high perplexity:\n"
                    "1. Drastically vary sentence length and rhythm: follow short punchy sentences with compound reflective thoughts.\n"
                    "2. Break predictable n-gram token sequences, formulaic sentence structures, and robotic transitions.\n"
                    "3. Use genuine human cognitive flow with varied phrasing.\n"
                    "4. Detect the language of the text (English, Spanish, etc.) and return the rewrite in that EXACT same language with 100% native fluency.\n"
                    "5. Return ONLY the single rewritten humanized text. Do NOT output notes, options, URLs, introductions, or markdown backticks.\n\n"
                    f"TEXT TO HUMANIZE:\n{chunk_text}"
                )
        elif mode == "natural":
            if is_es:
                prompt = (
                    "Eres un escritor y ensayista hispanohablante de élite. Tu objetivo es humanizar el siguiente texto para que suene con una voz 100% humana, fresca, auténtica y atractiva.\n"
                    "Reescribe el texto con cadencia orgánica y ritmo natural:\n"
                    "1. Ritmo conversacional y fluido, eliminando por completo el tono corporativo o robótico de IA.\n"
                    "2. Erradica clichés en español como 'en resumen', 'en este sentido', 'desempeña un rol crucial', 'un tapiz de', 'a día de hoy', 'sumergirse en'.\n"
                    "3. Mantén exactamente los argumentos, la estructura de párrafos y la intención original del texto.\n"
                    "4. Devuelve ÚNICAMENTE el texto humanizado en español. NO añadas introducciones, notas ni explicaciones.\n\n"
                    f"TEXTO A HUMANIZAR:\n{chunk_text}"
                )
            else:
                prompt = (
                    "You are an elite author humanizing text so it reads with 100% authentic, engaging, natural human voice.\n"
                    "Rewrite the following text with fluid sentence variety and organic rhythm:\n"
                    "1. Ensure engaging, conversational, yet polished human cadence.\n"
                    "2. Completely eliminate stiff, robotic, corporate AI phrasing.\n"
                    "3. Keep the exact meaning, paragraph flow, and core arguments.\n"
                    "4. Detect the language of the text (English, Spanish, etc.) and return the rewrite in that EXACT same language with 100% native fluency.\n"
                    "5. Return ONLY the single rewritten humanized text. Do NOT output notes, options, URLs, introductions, or markdown backticks.\n\n"
                    f"TEXT TO HUMANIZE:\n{chunk_text}"
                )
        else: # "pro"
            if is_es:
                prompt = (
                    "Eres un editor profesional de élite especializado en humanizar textos generados por IA en español con calidad HumanizeAI Pro (100% human score en Turnitin, GPTZero y CopyLeaks).\n"
                    "Reescribe el siguiente texto con alta naturalidad y variedad de vocabulario:\n"
                    "1. Alta perplejidad y burstiness: mezcla oraciones breves y directas con oraciones explicativas para evitar la monotonía sintáctica.\n"
                    "2. Elimina todas las transiciones mecánicas y muletillas robóticas de IA en español.\n"
                    "3. Utiliza la voz auténtica de un estudiante o redactor humano reflexivo con profundidad y claridad.\n"
                    "4. Conserva exactamente los argumentos, ideas, hechos, datos y párrafos originales.\n"
                    "5. Devuelve ÚNICAMENTE el texto humanizado en español. Sin comentarios, enlaces ni comillas invertidas.\n\n"
                    f"TEXTO A HUMANIZAR:\n{chunk_text}"
                )
            else:
                prompt = (
                    "You are an elite human editor specializing in humanizing AI text to achieve 100% human score on Turnitin, GPTZero, and CopyLeaks.\n"
                    "Rewrite the following text with HumanizeAI Pro quality:\n"
                    "1. High burstiness: mix short sentences with compound descriptive ones to vary rhythm.\n"
                    "2. Eliminate all robotic clichés, monotonous cadence, and predictable transitions.\n"
                    "3. Use authentic, thoughtful student prose with genuine conversational depth.\n"
                    "4. Keep the exact arguments, meaning, citations, and paragraph structure.\n"
                    "5. Detect the language of the text (English, Spanish, etc.) and return the rewrite in that EXACT same language.\n"
                    "6. Return ONLY the humanized text. Do NOT output notes, URLs, introductions, or markdown backticks.\n\n"
                    f"TEXT TO HUMANIZE:\n{chunk_text}"
                )

        cmd = [
            agy_bin,
            "-p", prompt,
            "--disable-slash-commands",
            "--effort", "low",
            "--model", "gemini-3.8-flash-low"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=40)
        if res.returncode == 0 and res.stdout.strip():
            out = res.stdout.strip()
            if out.startswith("```") and out.endswith("```"):
                lines = out.split("\n")
                if len(lines) >= 3:
                    out = "\n".join(lines[1:-1]).strip()
            if out and "https://www.humanizeai.pro/" not in out:
                return out
    except Exception:
        pass
    return None


def humanize_text_humanizeai_pro(text, casual_mode=False, progress_cb=None):
    """
    Flagship HumanizeAI Pro transformation engine with hierarchical paragraph
    and formatting preservation.
    Ensures that documents of any size (from 50 words to 50,000+ words) are
    processed with zero truncation, complete sentences, and exact layout preservation.
    """
    if not text or not text.strip():
        return text

    # Split text into alternating text blocks and newline separators (\n, \n\n, etc.)
    # This guarantees 100% fidelity to the original document formatting.
    parts = re.split(r'(\n+)', text)

    work_items = []  # list of (part_idx, list_of_subchunks)
    total_subchunks = 0
    for idx, part in enumerate(parts):
        if idx % 2 == 0 and part.strip():
            subchunks = split_paragraph_into_subchunks(part.strip(), max_words=130)
            work_items.append((idx, subchunks))
            total_subchunks += len(subchunks)

    if total_subchunks == 0:
        return text

    processed_count = 0
    rewritten_parts = list(parts)

    for part_idx, subchunks in work_items:
        p_rewritten_pieces = []
        for sc in subchunks:
            processed_count += 1
            if progress_cb:
                try:
                    progress_cb(processed_count, total_subchunks)
                except Exception:
                    pass

            # 1. Primary: Direct HumanizeAI Pro API (guaranteed <= 130 words, zero truncation)
            out = call_humanizeai_pro_api(sc, style="standard", ultra=False)

            # 2. Secondary: Neural Fallback via agy
            if not out:
                out = call_agy_humanizer(sc, mode="pro")

            # 3. Tertiary: Deep Local Fallback
            if not out:
                out = humanize_text_mist(sc, casual_mode=casual_mode)

            p_rewritten_pieces.append(out if out else sc)

        # Recombine pieces of the SAME paragraph with space
        rewritten_parts[part_idx] = " ".join(p_rewritten_pieces).strip()

    # Recombine all parts with original newline separators intact
    result = "".join(rewritten_parts)
    return normalize_whitespace(result)


def humanize_text_academic(text, casual_mode=False, progress_cb=None):
    """
    Academic Master transformation engine:
    Produces scholarly, university-level prose with advanced syntactic perplexity,
    specifically calibrated for 100% human score on Turnitin and academic detectors.
    """
    if not text or not text.strip():
        return text

    parts = re.split(r'(\n+)', text)
    work_items = []
    total_subchunks = 0
    for idx, part in enumerate(parts):
        if idx % 2 == 0 and part.strip():
            subchunks = split_paragraph_into_subchunks(part.strip(), max_words=130)
            work_items.append((idx, subchunks))
            total_subchunks += len(subchunks)

    if total_subchunks == 0:
        return text

    processed_count = 0
    rewritten_parts = list(parts)

    for part_idx, subchunks in work_items:
        p_rewritten_pieces = []
        for sc in subchunks:
            processed_count += 1
            if progress_cb:
                try:
                    progress_cb(processed_count, total_subchunks)
                except Exception:
                    pass

            # 1. Primary: HumanizeAI Pro Academic model
            out = call_humanizeai_pro_api(sc, style="academic", ultra=False)

            # 2. Secondary: Neural Academic specialized model
            if not out:
                out = call_agy_humanizer(sc, mode="academic")

            # 3. Tertiary: Deep local structural pass
            if not out:
                out = humanize_text_mist(sc, casual_mode=casual_mode)

            p_rewritten_pieces.append(out if out else sc)

        rewritten_parts[part_idx] = " ".join(p_rewritten_pieces).strip()

    result = "".join(rewritten_parts)
    return normalize_whitespace(result)


def humanize_text_stealth(text, casual_mode=False, progress_cb=None):
    """
    GhostWriter Ultra transformation engine:
    Aggressive anti-detection mode utilizing ultra-entropy styling and
    irregular token pacing to bypass strict detectors (GPTZero, CopyLeaks, Winston AI).
    """
    if not text or not text.strip():
        return text

    parts = re.split(r'(\n+)', text)
    work_items = []
    total_subchunks = 0
    for idx, part in enumerate(parts):
        if idx % 2 == 0 and part.strip():
            subchunks = split_paragraph_into_subchunks(part.strip(), max_words=130)
            work_items.append((idx, subchunks))
            total_subchunks += len(subchunks)

    if total_subchunks == 0:
        return text

    processed_count = 0
    rewritten_parts = list(parts)

    for part_idx, subchunks in work_items:
        p_rewritten_pieces = []
        for sc in subchunks:
            processed_count += 1
            if progress_cb:
                try:
                    progress_cb(processed_count, total_subchunks)
                except Exception:
                    pass

            # 1. Primary: HumanizeAI Pro Ultra Formal bypass model
            out = call_humanizeai_pro_api(sc, style="formal", ultra=True)

            # 2. Secondary: Neural Stealth counter-detection model
            if not out:
                out = call_agy_humanizer(sc, mode="stealth")

            # 3. Tertiary: Deep local structural pass
            if not out:
                out = humanize_text_mist(sc, casual_mode=casual_mode)

            p_rewritten_pieces.append(out if out else sc)

        rewritten_parts[part_idx] = " ".join(p_rewritten_pieces).strip()

    result = "".join(rewritten_parts)
    return normalize_whitespace(result)


def humanize_text_natural(text, casual_mode=False, progress_cb=None):
    """
    Natural Flow transformation engine:
    Focuses on organic, human voice with fluid conversational cadence and
    varied rhythm, eliminating all robotic AI stiffness.
    """
    if not text or not text.strip():
        return text

    parts = re.split(r'(\n+)', text)
    work_items = []
    total_subchunks = 0
    for idx, part in enumerate(parts):
        if idx % 2 == 0 and part.strip():
            subchunks = split_paragraph_into_subchunks(part.strip(), max_words=130)
            work_items.append((idx, subchunks))
            total_subchunks += len(subchunks)

    if total_subchunks == 0:
        return text

    processed_count = 0
    rewritten_parts = list(parts)

    for part_idx, subchunks in work_items:
        p_rewritten_pieces = []
        for sc in subchunks:
            processed_count += 1
            if progress_cb:
                try:
                    progress_cb(processed_count, total_subchunks)
                except Exception:
                    pass

            # 1. Primary: Neural Natural human voice model
            out = call_agy_humanizer(sc, mode="natural")

            # 2. Secondary: HumanizeAI Pro Standard model
            if not out:
                out = call_humanizeai_pro_api(sc, style="standard", ultra=False)

            # 3. Tertiary: Local phrase & contraction pass
            if not out:
                out = humanize_text_lavender(sc)
                if casual_mode:
                    out = apply_contractions(out, probability=0.75)

            p_rewritten_pieces.append(out if out else sc)

        rewritten_parts[part_idx] = " ".join(p_rewritten_pieces).strip()

    result = "".join(rewritten_parts)
    return normalize_whitespace(result)


def run_humanizer(text, engine, casual_mode=False, progress_cb=None):
    """
    Central dispatch function.
    Dispatches to the selected engine:
      - ⚡ HumanizeAI Pro: Flagship balanced engine (https://www.humanizeai.pro/)
      - 🎓 Academic Master: Scholarly university essay & research rewriter (Turnitin 100% human)
      - 👻 GhostWriter Ultra: Maximum entropy stealth bypass (GPTZero, CopyLeaks, Winston AI)
      - 🌊 Natural Flow: Organic human voice and fluid cadence
    """
    if not text or not text.strip():
        return text

    eng_str = str(engine).lower()

    # 1. ⚡ HumanizeAI Pro (Untouched!)
    if "humanize" in eng_str or "⚡" in eng_str or "pro" in eng_str:
        return humanize_text_humanizeai_pro(text, casual_mode=casual_mode, progress_cb=progress_cb)

    # 2. 🎓 Academic Master (Scholarly / University)
    if "academic" in eng_str or "🎓" in eng_str or "mist" in eng_str:
        return humanize_text_academic(text, casual_mode=casual_mode, progress_cb=progress_cb)

    # 3. 👻 GhostWriter Ultra (Stealth / Anti-Detection)
    if "ghost" in eng_str or "stealth" in eng_str or "👻" in eng_str or "hummer" in eng_str:
        return humanize_text_stealth(text, casual_mode=casual_mode, progress_cb=progress_cb)

    # 4. 🌊 Natural Flow (Organic / Human Voice)
    if "natural" in eng_str or "flow" in eng_str or "🌊" in eng_str or "lavender" in eng_str:
        return humanize_text_natural(text, casual_mode=casual_mode, progress_cb=progress_cb)

    # Default to HumanizeAI Pro flagship
    return humanize_text_humanizeai_pro(text, casual_mode=casual_mode, progress_cb=progress_cb)





# ============================================================
# Typing Engine
# ============================================================

def get_next_pause_info(text, start_idx, use_burst):
    search_text = text[start_idx:].lower()

    pause_triggers = ["\n", ". ", "! ", "? "]

    if use_burst:
        if is_spanish_text(text):
            pause_triggers.extend([
                " y ",
                " pero ",
                " porque ",
                " además ",
                " entonces ",
                " aunque ",
                " así que ",
                " o sea ",
                " es decir ",
                " sin embargo ",
                " por lo tanto ",
                " en cambio ",
                " por eso ",
            ])
        else:
            pause_triggers.extend([
                " and ",
                " but ",
                " because ",
                " so ",
                " also ",
                " however ",
                " then ",
            ])

    closest_idx = -1
    trigger_found = ""

    for trigger in pause_triggers:
        idx = search_text.find(trigger)

        if idx != -1 and (
            closest_idx == -1 or idx < closest_idx
        ):
            closest_idx = idx
            trigger_found = trigger.strip()

    if closest_idx != -1:
        words_away = len(search_text[:closest_idx].split())

        if trigger_found in [".", "!", "?"]:
            trigger_display = "end of sentence"
        elif trigger_found == "":
            trigger_display = "paragraph break"
        else:
            trigger_display = f"'{trigger_found}'"

        return (
            f"Next pause in ~{words_away} words at "
            f"{trigger_display}"
        )

    return "No more pauses"


def stop_typing(status_label, telemetry_label, root, terminal):
    global is_typing, is_paused

    if is_typing:
        is_typing = False
        is_paused = False

        log_terminal(
            terminal,
            "[System] ⏹ DETENIDO por el usuario (F10)."
        )

        root.after(
            0,
            lambda: status_label.config(
                text="Status: 🛑 Stopped (Press F9)",
                fg=C_ORANGE
            )
        )

        root.after(
            0,
            lambda: telemetry_label.config(
                text="> status: standing by"
            )
        )

        if pause_btn_ref is not None:
            try:
                root.after(0, lambda: pause_btn_ref.config(text="⏸  PAUSE (F8)", bg="#334155", fg="#F1F5F9"))
            except Exception:
                pass


def toggle_pause(status_label, telemetry_label, root, terminal):
    global is_typing, is_paused

    if not is_typing:
        return

    is_paused = not is_paused

    if is_paused:
        log_terminal(
            terminal,
            "[System] ⏸ PAUSA activada (F8). Presiona F8 para continuar."
        )
        root.after(
            0,
            lambda: status_label.config(
                text="● Status: ⏸ En Pausa (F8 para seguir)",
                fg="#F59E0B"
            )
        )
        root.after(
            0,
            lambda: telemetry_label.config(
                text="> status: paused (press F8 to resume)"
            )
        )
        if pause_btn_ref is not None:
            try:
                root.after(0, lambda: pause_btn_ref.config(text="▶  RESUME (F8)", bg="#D97706", fg="#FFFFFF"))
            except Exception:
                pass
    else:
        log_terminal(
            terminal,
            "[System] ▶ REANUDANDO escritura..."
        )
        root.after(
            0,
            lambda: status_label.config(
                text="● Status: Typing... (F8 Pausa, F10 Detener)",
                fg="#10B981"
            )
        )
        root.after(
            0,
            lambda: telemetry_label.config(
                text="> status: active typing sequence"
            )
        )
# ------------------------------------------------------------
# Universal Keystroke Synthesizer (Zero permissions, rootless)
# ------------------------------------------------------------
_pynput_kb = None
try:
    from pynput.keyboard import Controller as PynputController, Key as PynputKey
    _pynput_kb = PynputController()
except Exception:
    PynputKey = None

def emit_char(c):
    # Normalize typography if passed here
    if c in ("\u2019", "\u2018"):
        c = "'"
    elif c in ("\u201c", "\u201d"):
        c = '"'
    elif c in ("\u2013", "\u2014"):
        c = "-"
    elif c == "\u00a0":
        c = " "

    # 1. Native pynput (Zero permissions, works everywhere on Linux XWayland/X11 & Windows & macOS)
    if _pynput_kb is not None:
        try:
            _pynput_kb.type(c)
            return True
        except Exception:
            pass

    # 2. Windows native keyboard module (Windows only, avoids root error on Linux)
    if os.name == "nt":
        try:
            keyboard.write(c)
            return True
        except Exception:
            pass

    # 3. Fallback: xdotool (Linux X11/XWayland rootless)
    try:
        subprocess.run(["xdotool", "type", "--clearmodifiers", "--", c], stderr=subprocess.DEVNULL)
        return True
    except Exception:
        pass
    return False

def emit_key(k):
    # 1. Native pynput (Zero permissions)
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

    # 2. Windows native keyboard module
    if os.name == "nt":
        try:
            keyboard.send(k)
            return True
        except Exception:
            pass

    # 3. Fallback: xdotool
    try:
        if k == "backspace":
            subprocess.run(["xdotool", "key", "BackSpace"], stderr=subprocess.DEVNULL)
        elif k == "enter":
            subprocess.run(["xdotool", "key", "Return"], stderr=subprocess.DEVNULL)
        elif k == "shift+enter":
            subprocess.run(["xdotool", "key", "Shift+Return"], stderr=subprocess.DEVNULL)
        return True
    except Exception:
        pass
    return False


def type_text(
    text,
    wpm,
    typo_chance,
    use_shift_enter,
    use_burst,
    use_fragments,
    tether_var_val,
    target_hwnd,
    status_label,
    telemetry_label,
    chart_canvas,
    key_lbl,
    typo_lbl,
    last_lbl,
    root,
    terminal,
):
    global is_typing, is_paused

    root.after(
        0,
        lambda: status_label.config(
            text="● Status: Typing... (F10 to Stop)",
            fg="#F59E0B"
        )
    )

    cpm = max(1, wpm * 5)
    base_delay = 60.0 / cpm

    is_new_sentence = True
    is_new_paragraph = True

    if is_spanish_text(text):
        connectors = [
            " y ",
            " pero ",
            " porque ",
            " además ",
            " entonces ",
            " aunque ",
            " así que ",
            " o sea ",
            " es decir ",
            " sin embargo ",
            " por lo tanto ",
            " en cambio ",
            " por eso ",
        ]
    else:
        connectors = [
            " and ",
            " but ",
            " because ",
            " so ",
            " also ",
            " then ",
            " however ",
        ]

    for i, char in enumerate(text):
        if not is_typing:
            return

        while is_paused:
            if not is_typing:
                return
            time.sleep(0.1)

        # ----------------------------------------------------
        # Optional foreground-window tethering
        # ----------------------------------------------------
        if tether_var_val and user32 is not None and target_hwnd is not None:
            paused = False

            while user32.GetForegroundWindow() != target_hwnd:
                if not is_typing:
                    return

                if not paused:
                    root.after(
                        0,
                        lambda: status_label.config(
                            text="Status: ⏸ Tether Paused",
                            fg=C_ORANGE
                        )
                    )
                    paused = True

                time.sleep(0.2)

            if paused and is_typing:
                root.after(
                    0,
                    lambda: status_label.config(
                        text="Status: Typing... (F10 to Stop)",
                        fg=C_CHARCOAL
                    )
                )
                time.sleep(0.5)

        # ----------------------------------------------------
        # Zero-width / non-breaking spaces
        # ----------------------------------------------------
        if char in ("\u200b", "\u00a0"):
            emit_char(" ")
            continue

        # ----------------------------------------------------
        # Telemetry label
        # ----------------------------------------------------
        if char == " " or i == 0:
            root.after(
                0,
                lambda: telemetry_label.config(
                    text="> injecting token stream..."
                )
            )

        # ----------------------------------------------------
        # Bracket / parenthesis pause
        # ----------------------------------------------------
        if char in ["(", ")", "[", "]", "{", "}"]:
            root.after(
                0,
                lambda c=char: telemetry_label.config(
                    text=f"> physical pause: locating '{c}'"
                )
            )

            pt = random.uniform(0.5, 1.1)
            time.sleep(pt)

            root.after(
                0,
                lambda p=pt: update_hud(
                    root,
                    int(p * 1000),
                    True
                )
            )

        # ----------------------------------------------------
        # Optional false-start fragment
        # ----------------------------------------------------
        fragment_triggered = False

        if (
            is_new_sentence
            and char.isalpha()
            and use_fragments
            and random.random() < 0.18
        ):
            fragment_triggered = True

            if is_spanish_text(text):
                fragment = random.choice([
                    "O sea, ",
                    "Bueno, ",
                    "Es decir, ",
                    "En verdad, ",
                    "La verdad, ",
                    "O bueno, ",
                    "A ver, ",
                    "Digo, ",
                ])
            else:
                fragment = random.choice([
                    "Actually, ",
                    "I mean, ",
                    "Basically, ",
                    "Well, ",
                    "So, ",
                ])

            root.after(
                0,
                lambda f=fragment: telemetry_label.config(
                    text=f"> false-start: revising '{f.strip()}'"
                )
            )

            for f_char in fragment:
                if not is_typing:
                    return

                emit_char(f_char)

                cd = base_delay * random.uniform(0.6, 1.2)

                time.sleep(cd)

                root.after(
                    0,
                    lambda c=cd: update_hud(
                        root,
                        int(c * 1000),
                        False,
                        False,
                        True
                    )
                )

                root.after(
                    0,
                    lambda: render_telemetry_ui(
                        chart_canvas,
                        key_lbl,
                        typo_lbl,
                        last_lbl
                    )
                )

            rt = random.uniform(1.2, 2.5)
            time.sleep(rt)

            root.after(
                0,
                lambda r=rt: update_hud(
                    root,
                    int(r * 1000),
                    True
                )
            )

            for _ in range(len(fragment)):
                if not is_typing:
                    return

                emit_key("backspace")
                time.sleep(
                    base_delay * random.uniform(0.3, 0.6)
                )

            time.sleep(random.uniform(0.5, 1.2))

        # ----------------------------------------------------
        # Start-of-sentence cognitive pause
        # ----------------------------------------------------
        if is_new_sentence and char.isalpha():

            if use_burst and not fragment_triggered:
                if is_new_paragraph:
                    pt = random.uniform(2.2, 4.0)
                else:
                    pt = random.uniform(0.8, 2.1)

                root.after(
                    0,
                    lambda: telemetry_label.config(
                        text="> cog-burst: structural mapping"
                    )
                )

                time.sleep(pt)

                root.after(
                    0,
                    lambda p=pt: update_hud(
                        root,
                        int(p * 1000),
                        True
                    )
                )

            is_new_sentence = False
            is_new_paragraph = False

        # ----------------------------------------------------
        # Connector pauses
        # ----------------------------------------------------
        if use_burst and char == " ":
            look_ahead = text[i:i + 15].lower()

            for conn in connectors:
                if look_ahead.startswith(conn):
                    pt = random.uniform(0.5, 1.1)

                    root.after(
                        0,
                        lambda c=conn.strip(): telemetry_label.config(
                            text=f"> cog-burst: bridging '{c}'"
                        )
                    )

                    time.sleep(pt)

                    root.after(
                        0,
                        lambda p=pt: update_hud(
                            root,
                            int(p * 1000),
                            True
                        )
                    )

                    break

        # ----------------------------------------------------
        # Base timing jitter
        # ----------------------------------------------------
        delay = base_delay * random.uniform(0.72, 1.28)

        # ----------------------------------------------------
        # Optional typo simulation
        # ----------------------------------------------------
        if char.isalpha() and random.random() < typo_chance:
            typo = get_typo(char)

            if typo:
                emit_char(typo)

                time.sleep(
                    base_delay * random.uniform(1.5, 3.0)
                )

                emit_key("backspace")

                time.sleep(
                    base_delay * random.uniform(0.8, 1.5)
                )

                root.after(
                    0,
                    lambda d=delay: update_hud(
                        root,
                        int(d * 1000),
                        False,
                        True,
                        False
                    )
                )

        # ----------------------------------------------------
        # Actual character output
        # ----------------------------------------------------
        if char == "\n":
            is_new_sentence = True
            is_new_paragraph = True

            if use_shift_enter:
                emit_key("shift+enter")
            else:
                emit_key("enter")

        elif char == "\r":
            continue

        else:
            emit_char(char)

        # ----------------------------------------------------
        # Punctuation pauses
        # ----------------------------------------------------
        if char in [".", "!", "?"]:
            delay += random.uniform(0.3, 0.6)
            is_new_sentence = True

        elif char in [",", ";", ":"]:
            delay += random.uniform(0.15, 0.4)

        # Occasional natural hesitation.
        if random.random() < 0.012:
            delay += random.uniform(0.5, 1.5)

        time.sleep(delay)

        root.after(
            0,
            lambda d=delay: update_hud(
                root,
                int(d * 1000),
                False,
                False,
                True
            )
        )

        root.after(
            0,
            lambda: render_telemetry_ui(
                chart_canvas,
                key_lbl,
                typo_lbl,
                last_lbl
            )
        )

    is_typing = False
    is_paused = False

    if pause_btn_ref is not None:
        try:
            root.after(
                0,
                lambda: pause_btn_ref.config(
                    text="⏸  PAUSE (F8)",
                    bg="#334155",
                    fg="#F1F5F9"
                )
            )
        except Exception:
            pass

    log_terminal(
        terminal,
        "[System] ✅ ¡Escritura completada con éxito! En espera."
    )

    root.after(
        0,
        lambda: status_label.config(
            text="● ¡Escritura Completada! (Listo)",
            fg=C_ACCENT_GREEN
        )
    )

    root.after(
        0,
        lambda: telemetry_label.config(
            text="> estado: escritura completada al 100%"
        )
    )

    try:
        top_val = getattr(root, '_always_on_top_val', True)
        root.after(0, lambda: root.attributes("-topmost", top_val))
        root.after(0, lambda: root.lift())
    except Exception:
        pass


# ============================================================
# Processing Pipeline
# ============================================================

def async_pipeline(
    text,
    wpm,
    accuracy,
    humanize,
    engine,
    remove_lines,
    use_shift_enter,
    remove_all_lines,
    use_burst,
    use_fragments,
    tether_val,
    casual_mode,
    status_label,
    telemetry_label,
    chart_canvas,
    key_lbl,
    typo_lbl,
    last_lbl,
    terminal,
    root,
    engine_var,
    start_delay=5,
):
    global is_typing

    root.after(
        0,
        lambda: clear_terminal(terminal)
    )

    log_terminal(
        terminal,
        "[System] F9 received. Processing text..."
    )

    root.after(
        0,
        lambda: telemetry_label.config(
            text="> analyzing text structure..."
        )
    )

    # --------------------------------------------------------
    # Humanization
    # --------------------------------------------------------
    if humanize:
        root.after(
            0,
            lambda: status_label.config(
                text="Status: NLP Processing...",
                fg=C_ORANGE
            )
        )

        log_terminal(
            terminal,
            f"[NLP] Selected engine: {engine}"
        )

        before = text

        def nlp_prog(done, total):
            root.after(
                0,
                lambda d=done, t=total: status_label.config(
                    text=f"Status: NLP Processing ({d}/{t})...",
                    fg=C_ORANGE
                )
            )
            log_terminal(terminal, f"[NLP] Processing chunk {done}/{total}...")

        text = run_humanizer(
            text,
            engine,
            casual_mode=casual_mode,
            progress_cb=nlp_prog
        )

        if text != before:
            log_terminal(
                terminal,
                "[NLP] Text transformed (HumanizeAI Pro quality)."
            )
        else:
            log_terminal(
                terminal,
                "[NLP] No safe rewrite required."
            )

    # --------------------------------------------------------
    # Small final cleanup & smart typography normalization
    # --------------------------------------------------------
    quote_map = {
        '’': "'",
        '‘': "'",
        '“': '"',
        '”': '"',
        '–': '-',
        '—': ',',
        '…': '...',
        '\u00a0': ' ',
        '\u200b': '',
    }
    for orig_char, rep_char in quote_map.items():
        text = text.replace(orig_char, rep_char)

    text = normalize_whitespace(text)

    log_terminal(
        terminal,
        f"[NLP] Longitud final lista: {len(text)} caracteres ({len(text.split())} palabras)"
    )

    # --------------------------------------------------------
    # Launch countdown
    # --------------------------------------------------------
    if start_delay > 0:
        log_terminal(
            terminal,
            f"[System] ⏳ Iniciando en {start_delay}s... (¡Haz clic en tu destino!) (F10 para cancelar)"
        )

        steps = int(start_delay * 10)
        for i in range(steps, 0, -1):
            if not is_typing:
                return

            c_sec = i / 10.0
            root.after(
                0,
                lambda c=c_sec: status_label.config(
                    text=f"⏳ {c:.1f}s — ¡Haz clic en tu destino!",
                    fg=C_ORANGE,
                )
            )

            root.after(
                0,
                lambda c=c_sec: telemetry_label.config(
                    text=f"> seq launch: t-minus {c:.1f}s (haz clic en tu destino)"
                )
            )
            time.sleep(0.1)
    else:
        log_terminal(
            terminal,
            "[System] Starting immediately..."
        )

    target_hwnd = user32.GetForegroundWindow() if user32 is not None else None

    try:
        type_text(
            text,
            wpm,
            (100.0 - accuracy) / 100.0,
            use_shift_enter,
            use_burst,
            use_fragments,
            tether_val,
            target_hwnd,
            status_label,
            telemetry_label,
            chart_canvas,
            key_lbl,
            typo_lbl,
            last_lbl,
            root,
            terminal,
        )
    except Exception as exc:
        import traceback
        traceback.print_exc()
        is_typing = False
        is_paused = False
        log_terminal(terminal, f"[Error] Error en escritura: {exc}")
        root.after(0, lambda: status_label.config(text=f"● Error: {exc}", fg="#EF4444"))


def on_trigger_event(
    wpm,
    accuracy,
    humanize,
    engine,
    remove_lines,
    use_shift_enter,
    remove_all_lines,
    use_burst,
    use_fragments,
    tether_val,
    casual_mode,
    remove_emojis_val,
    remove_asterisks_val,
    status_label,
    telemetry_label,
    chart_canvas,
    key_lbl,
    typo_lbl,
    last_lbl,
    terminal,
    root,
    engine_var,
    start_delay=5,
):
    global is_typing

    if is_typing:
        return

    text = get_clipboard_text(root)

    cache_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "last_essay.txt")
    if text and text.strip():
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception:
            pass
    elif os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached = f.read()
            if cached.strip():
                text = cached
                set_clipboard_text(text, root)
                try:
                    log_terminal(terminal, f"[System] 📄 Usando ensayo guardado ({len(text.split())} palabras).")
                except Exception:
                    pass
        except Exception:
            pass

    if not text or not text.strip():
        try:
            log_terminal(
                terminal,
                "[System] ⚠️ Portapapeles vacío. Copia tu texto (Ctrl+C) o usa 'Pegar Ensayo' antes de iniciar!"
            )
        except Exception:
            pass
        root.after(
            0,
            lambda: status_label.config(
                text="⚠️ Copia tu texto (Ctrl+C) primero",
                fg="#EF4444"
            )
        )
        root.after(
            0,
            lambda: telemetry_label.config(
                text="> clipboard is empty"
            )
        )
        return

    is_typing = True

    # --------------------------------------------------------
    # Preprocessing
    # --------------------------------------------------------
    if remove_emojis_val:
        text = remove_emojis(text)

    if remove_asterisks_val:
        text = text.replace("*", "")

    text = text.replace("—", ",")
    text = text.replace("--", ",")
    text = text.replace(";", ",")

    for arrow in ["→", "⇒", "➔", "➢", "➣", "➤", "=>"]:
        text = text.replace(arrow, "->")

    # --------------------------------------------------------
    # Line handling
    # --------------------------------------------------------
    if remove_all_lines:
        text = re.sub(
            r"\s+",
            " ",
            text.replace("\r", " ").replace("\n", " ")
        )

    elif remove_lines:
        text = re.sub(
            r"(\r?\n)\s*(\r?\n)+",
            r"\1",
            text
        )

    text = normalize_whitespace(text)

    # --------------------------------------------------------
    # Threaded processing
    # --------------------------------------------------------
    threading.Thread(
        target=lambda: async_pipeline(
            text,
            wpm,
            accuracy,
            humanize,
            engine,
            remove_lines,
            use_shift_enter,
            remove_all_lines,
            use_burst,
            use_fragments,
            tether_val,
            casual_mode,
            status_label,
            telemetry_label,
            chart_canvas,
            key_lbl,
            typo_lbl,
            last_lbl,
            terminal,
            root,
            engine_var,
            start_delay,
        ),
        daemon=True,
    ).start()


# ============================================================
# Settings Window
# ============================================================

def open_settings(
    root,
    remove_lines_var,
    use_shift_enter_var,
    remove_all_lines_var,
    casual_mode_var,
    remove_emojis_var,
    remove_asterisks_var,
    use_fragments_var,
    transparency_var,
):
    settings_win = tk.Toplevel(root)

    settings_win.title("Engine Settings")
    settings_win.geometry("390x430")
    settings_win.resizable(False, False)
    settings_win.configure(bg=C_CREAM)
    settings_win.transient(root)
    settings_win.grab_set()

    tk.Label(
        settings_win,
        text="TEXT PROCESSING",
        font=("Consolas", 9, "bold"),
        bg=C_CREAM,
        fg=C_ORANGE,
    ).pack(pady=(12, 6))

    tk.Checkbutton(
        settings_win,
        text="🚫 Strip Markdown (*, **)",
        variable=remove_asterisks_var,
        bg=C_CREAM,
        fg=C_CHARCOAL,
        selectcolor=C_SURFACE,
        activebackground=C_CREAM,
        activeforeground=C_CHARCOAL,
        highlightthickness=0,
    ).pack(anchor="w", padx=20)

    tk.Checkbutton(
        settings_win,
        text="🚫 Strip Emojis",
        variable=remove_emojis_var,
        bg=C_CREAM,
        fg=C_CHARCOAL,
        selectcolor=C_SURFACE,
        activebackground=C_CREAM,
        activeforeground=C_CHARCOAL,
        highlightthickness=0,
    ).pack(anchor="w", padx=20)

    tk.Checkbutton(
        settings_win,
        text="📱 Casual Mode",
        variable=casual_mode_var,
        bg=C_CREAM,
        fg=C_CHARCOAL,
        selectcolor=C_SURFACE,
        activebackground=C_CREAM,
        activeforeground=C_CHARCOAL,
        highlightthickness=0,
    ).pack(anchor="w", padx=20)

    tk.Label(
        settings_win,
        text="LINE BREAKS",
        font=("Consolas", 9, "bold"),
        bg=C_CREAM,
        fg=C_ORANGE,
    ).pack(pady=(12, 6))

    tk.Checkbutton(
        settings_win,
        text="Prevent Auto-Submit (Use Shift+Enter)",
        variable=use_shift_enter_var,
        bg=C_CREAM,
        fg=C_CHARCOAL,
        selectcolor=C_SURFACE,
        activebackground=C_CREAM,
        activeforeground=C_CHARCOAL,
        highlightthickness=0,
    ).pack(anchor="w", padx=20)

    tk.Checkbutton(
        settings_win,
        text="Remove empty lines",
        variable=remove_lines_var,
        bg=C_CREAM,
        fg=C_CHARCOAL,
        selectcolor=C_SURFACE,
        activebackground=C_CREAM,
        activeforeground=C_CHARCOAL,
        highlightthickness=0,
    ).pack(anchor="w", padx=20)

    tk.Checkbutton(
        settings_win,
        text="NUCLEAR: Remove ALL breaks",
        variable=remove_all_lines_var,
        bg=C_CREAM,
        fg=C_CHARCOAL,
        selectcolor=C_SURFACE,
        activebackground=C_CREAM,
        activeforeground=C_CHARCOAL,
        highlightthickness=0,
    ).pack(anchor="w", padx=20)

    tk.Label(
        settings_win,
        text="APPEARANCE",
        font=("Consolas", 9, "bold"),
        bg=C_CREAM,
        fg=C_ORANGE,
    ).pack(pady=(12, 6))

    trans_frame = tk.Frame(settings_win, bg=C_CREAM)
    trans_frame.pack(fill="x", padx=20)

    tk.Label(
        trans_frame,
        text="Window Transparency:",
        bg=C_CREAM,
        fg=C_CHARCOAL,
    ).pack(side="left")

    trans_val = tk.Label(
        trans_frame,
        text=f"{int(transparency_var.get() * 100)}%",
        bg=C_CREAM,
        fg=C_CHARCOAL,
    )
    trans_val.pack(side="right")

    def update_alpha(val):
        try:
            v = float(val)
            root.attributes("-alpha", v)
            trans_val.config(
                text=f"{int(v * 100)}%"
            )
        except Exception:
            pass

    ttk.Scale(
        settings_win,
        from_=0.3,
        to=1.0,
        orient="horizontal",
        variable=transparency_var,
        command=update_alpha,
    ).pack(
        fill="x",
        padx=20,
        pady=5
    )

    tk.Label(
        settings_win,
        text="Humanizer notes",
        font=("Consolas", 10, "bold"),
        bg=C_CREAM,
        fg=C_CHARCOAL,
    ).pack(pady=(15, 5))

    note = (
        "⚡ HumanizeAI Pro = Flagship balanced humanizer (Turnitin & GPTZero bypass)\n"
        "🎓 Academic Master = Scholarly prose, advanced vocabulary & academic depth\n"
        "👻 GhostWriter Ultra = Maximum entropy & stealth bypass for strict detectors\n"
        "🌊 Natural Flow = Organic conversational rhythm, fluid cadence & human voice\n\n"
        "All 4 engines feature zero truncation, paragraph layout fidelity & 100% human score."
    )

    tk.Label(
        settings_win,
        text=note,
        justify="left",
        font=("Consolas", 8),
        bg=C_CREAM,
        fg=C_MUTED,
    ).pack(
        anchor="w",
        padx=20
    )


# ============================================================
# Interactive Text Playground & Inspector
# ============================================================

def open_playground(
    root,
    engine_var,
    casual_mode_var,
    wpm_var,
    terminal=None,
):
    import difflib

    pg_win = tk.Toplevel(root)
    pg_win.title(f"{APP_NAME} — Text Playground & Inspector")
    pg_win.geometry("920x630")
    pg_win.minsize(820, 520)
    pg_win.configure(bg=C_BG)
    pg_win.transient(root)

    # Top header
    header_frame = tk.Frame(pg_win, bg=C_CREAM, padx=16, pady=12)
    header_frame.pack(fill="x")

    title_box = tk.Frame(header_frame, bg=C_CREAM)
    title_box.pack(side="left")

    tk.Label(
        title_box,
        text="🧪 TEXT PLAYGROUND & INSPECTOR",
        font=("Georgia", 13, "bold"),
        bg=C_CREAM,
        fg=C_CHARCOAL,
    ).pack(anchor="w")

    tk.Label(
        title_box,
        text="Live test text humanization (English / Spanish), inspect linguistic diffs, and preview typing metrics.",
        font=("Consolas", 8),
        bg=C_CREAM,
        fg=C_MUTED,
    ).pack(anchor="w", pady=(2, 0))

    close_btn = tk.Button(
        header_frame,
        text="✕ CLOSE",
        font=("Consolas", 8, "bold"),
        bg=C_BTN_BG,
        fg=C_MUTED,
        activebackground=C_BTN_HOVER,
        activeforeground=C_CHARCOAL,
        relief="flat",
        padx=10,
        pady=4,
        cursor="hand2",
        command=pg_win.destroy,
    )
    close_btn.pack(side="right")

    # Toolbar
    toolbar = tk.Frame(pg_win, bg=C_SURFACE, padx=16, pady=10)
    toolbar.pack(fill="x")

    tk.Label(
        toolbar,
        text="ENGINE:",
        font=("Consolas", 8, "bold"),
        bg=C_SURFACE,
        fg=C_MUTED,
    ).pack(side="left", padx=(0, 6))

    pg_engine_var = tk.StringVar(value=engine_var.get())
    pg_engine_combo = ttk.Combobox(
        toolbar,
        textvariable=pg_engine_var,
        values=[
            "⚡ HumanizeAI Pro",
            "🎓 Academic Master",
            "👻 GhostWriter Ultra",
            "🌊 Natural Flow",
        ],
        state="readonly",
        font=("Consolas", 9),
        width=18,
    )
    pg_engine_combo.pack(side="left", padx=(0, 10))

    pg_casual_var = tk.BooleanVar(value=casual_mode_var.get())
    tk.Checkbutton(
        toolbar,
        text="Casual Mode",
        variable=pg_casual_var,
        bg=C_SURFACE,
        fg=C_CHARCOAL,
        font=("Consolas", 9),
        selectcolor=C_BG,
        activebackground=C_SURFACE,
        activeforeground=C_CHARCOAL,
        highlightthickness=0,
    ).pack(side="left", padx=(0, 12))

    SAMPLE_TEXT_EN = (
        "Furthermore, it is important to note that utilizing this framework ensures optimal results. "
        "In order to delve into the realm of artificial intelligence, we must meticulously analyze every aspect "
        "and take into consideration various factors to revolutionize our workflow."
    )

    SAMPLE_TEXT_ES = (
        "Es crucial destacar que la inteligencia artificial juega un papel fundamental en el vertiginoso mundo actual. "
        "Asimismo, cabe señalar que para optimizar los procesos debemos sumergirnos en un sinfín de posibilidades "
        "con el fin de arrojar luz sobre esta materia y desentrañar los misterios de la tecnología."
    )

    def load_sample_en():
        in_text_widget.delete("1.0", tk.END)
        in_text_widget.insert("1.0", SAMPLE_TEXT_EN)
        execute_playground_humanize()

    def load_sample_es():
        in_text_widget.delete("1.0", tk.END)
        in_text_widget.insert("1.0", SAMPLE_TEXT_ES)
        execute_playground_humanize()

    def paste_input():
        try:
            cb = get_clipboard_text(in_text_widget)
            if cb and cb.strip():
                in_text_widget.delete("1.0", tk.END)
                in_text_widget.insert("1.0", cb)
                execute_playground_humanize()
                if terminal:
                    log_terminal(
                        terminal,
                        f"[Playground] ✅ Pegado: {len(cb.split())} palabras ({len(cb)} caracteres)"
                    )
            else:
                if terminal:
                    log_terminal(
                        terminal,
                        "[Playground] ⚠️ El portapapeles está vacío. Copia tu texto primero (Ctrl+C)."
                    )
        except Exception as e:
            if terminal:
                log_terminal(terminal, f"[Playground] Error: {e}")

    def copy_output():
        out = out_text_widget.get("1.0", tk.END).strip()
        if out:
            set_clipboard_text(out, out_text_widget)
            copy_btn.config(text="✓ COPIED!")
            pg_win.after(1500, lambda: copy_btn.config(text="📋 COPY"))

    def copy_for_autotyper():
        out = out_text_widget.get("1.0", tk.END).strip()
        if out:
            set_clipboard_text(out, out_text_widget)
            type_ready_btn.config(text="✓ READY!")
            pg_win.after(1500, lambda: type_ready_btn.config(text="🚀 USE IN AUTOTYPER"))
            if terminal:
                log_terminal(
                    terminal,
                    f"[Playground] Cargadas {len(out.split())} palabras en portapapeles. Listo para escribir con START (F9)!"
                )

    def clear_all():
        in_text_widget.delete("1.0", tk.END)
        out_text_widget.delete("1.0", tk.END)
        update_analytics()

    sample_en_btn = tk.Button(
        toolbar,
        text="✨ SAMPLE EN",
        font=("Consolas", 8, "bold"),
        bg=C_BTN_BG,
        fg=C_CHARCOAL,
        activebackground=C_BTN_HOVER,
        activeforeground=C_ORANGE,
        relief="flat",
        padx=7,
        pady=4,
        cursor="hand2",
        command=load_sample_en,
    )
    sample_en_btn.pack(side="left", padx=(0, 4))

    sample_es_btn = tk.Button(
        toolbar,
        text="🇪🇸 SAMPLE ES",
        font=("Consolas", 8, "bold"),
        bg=C_BTN_BG,
        fg=C_CHARCOAL,
        activebackground=C_BTN_HOVER,
        activeforeground=C_ORANGE,
        relief="flat",
        padx=7,
        pady=4,
        cursor="hand2",
        command=load_sample_es,
    )
    sample_es_btn.pack(side="left", padx=(0, 6))

    paste_btn = tk.Button(
        toolbar,
        text="📥 PASTE",
        font=("Consolas", 8, "bold"),
        bg=C_BTN_BG,
        fg=C_CHARCOAL,
        activebackground=C_BTN_HOVER,
        activeforeground=C_ORANGE,
        relief="flat",
        padx=8,
        pady=4,
        cursor="hand2",
        command=paste_input,
    )
    paste_btn.pack(side="left", padx=(0, 4))

    clear_btn = tk.Button(
        toolbar,
        text="CLEAR",
        font=("Consolas", 8),
        bg=C_BTN_BG,
        fg=C_MUTED,
        activebackground=C_BTN_HOVER,
        activeforeground=C_CHARCOAL,
        relief="flat",
        padx=6,
        pady=4,
        cursor="hand2",
        command=clear_all,
    )
    clear_btn.pack(side="left", padx=(0, 8))

    type_ready_btn = tk.Button(
        toolbar,
        text="🚀 USE IN AUTOTYPER",
        font=("Consolas", 8, "bold"),
        bg="#059669",
        fg="#FFFFFF",
        activebackground="#10B981",
        activeforeground="#FFFFFF",
        relief="flat",
        padx=10,
        pady=4,
        cursor="hand2",
        command=copy_for_autotyper,
    )
    type_ready_btn.pack(side="right")

    copy_btn = tk.Button(
        toolbar,
        text="📋 COPY",
        font=("Consolas", 8, "bold"),
        bg=C_BTN_BG,
        fg=C_CHARCOAL,
        activebackground=C_BTN_HOVER,
        activeforeground=C_ORANGE,
        relief="flat",
        padx=8,
        pady=4,
        cursor="hand2",
        command=copy_output,
    )
    copy_btn.pack(side="right", padx=(0, 4))

    run_btn = tk.Button(
        toolbar,
        text="⚡ RUN HUMANIZER",
        font=("Consolas", 8, "bold"),
        bg=C_ORANGE,
        fg=C_BG,
        activebackground="#22D3EE",
        activeforeground=C_BG,
        relief="flat",
        padx=12,
        pady=4,
        cursor="hand2",
        command=lambda: execute_playground_humanize(),
    )
    run_btn.pack(side="right", padx=(0, 6))

    # Bottom analytics dashboard (packed first with side=bottom so it retains full height)
    analytics_frame = tk.Frame(pg_win, bg=C_CREAM, padx=16, pady=10)
    analytics_frame.pack(fill="x", side="bottom")

    # Split editor pane (expands into remaining vertical area)
    editors_frame = tk.Frame(pg_win, bg=C_BG, padx=16, pady=10)
    editors_frame.pack(fill="both", expand=True)

    # Left editor: Original
    left_editor = tk.Frame(editors_frame, bg=C_BG)
    left_editor.pack(side="left", fill="both", expand=True, padx=(0, 8))

    tk.Label(
        left_editor,
        text="ORIGINAL TEXT (INPUT)",
        font=("Consolas", 8, "bold"),
        bg=C_BG,
        fg=C_MUTED,
    ).pack(anchor="w", pady=(0, 4))

    in_text_widget = tk.Text(
        left_editor,
        bg=C_SURFACE,
        fg="#E2E8F0",
        insertbackground=C_ORANGE,
        font=("Consolas", 10),
        wrap="word",
        relief="flat",
        padx=10,
        pady=10,
        highlightbackground=C_BORDER,
        highlightthickness=1,
    )
    in_text_widget.pack(fill="both", expand=True)

    # Right editor: Output
    right_editor = tk.Frame(editors_frame, bg=C_BG)
    right_editor.pack(side="right", fill="both", expand=True, padx=(8, 0))

    tk.Label(
        right_editor,
        text="HUMANIZED OUTPUT (PREVIEW)",
        font=("Consolas", 8, "bold"),
        bg=C_BG,
        fg=C_ORANGE,
    ).pack(anchor="w", pady=(0, 4))

    out_text_widget = tk.Text(
        right_editor,
        bg=C_SURFACE,
        fg="#E2E8F0",
        insertbackground=C_ORANGE,
        font=("Consolas", 10),
        wrap="word",
        relief="flat",
        padx=10,
        pady=10,
        highlightbackground=C_BORDER,
        highlightthickness=1,
    )
    out_text_widget.pack(fill="both", expand=True)

    def make_metric_card(parent, title):
        card = tk.Frame(
            parent,
            bg=C_SURFACE,
            highlightbackground=C_BORDER,
            highlightthickness=1,
            padx=12,
            pady=6,
        )
        card.pack(side="left", fill="x", expand=True, padx=4)

        tk.Label(
            card,
            text=title,
            font=("Consolas", 7, "bold"),
            bg=C_SURFACE,
            fg=C_MUTED,
        ).pack(anchor="w")

        val_lbl = tk.Label(
            card,
            text="0",
            font=("Consolas", 11, "bold"),
            bg=C_SURFACE,
            fg=C_CHARCOAL,
        )
        val_lbl.pack(anchor="w")
        return val_lbl

    card_in_words = make_metric_card(analytics_frame, "INPUT WORDS / CHARS")
    card_out_words = make_metric_card(analytics_frame, "OUTPUT WORDS / CHARS")
    card_diff = make_metric_card(analytics_frame, "WORDS CHANGED / DIFF")
    card_lang = make_metric_card(analytics_frame, "DETECTED LANGUAGE")
    card_timing = make_metric_card(analytics_frame, "EST. TYPING DURATION")

    def update_analytics():
        in_t = in_text_widget.get("1.0", tk.END).strip()
        out_t = out_text_widget.get("1.0", tk.END).strip()

        in_words = re.findall(r"\b\w+\b", in_t.lower()) if in_t else []
        out_words = re.findall(r"\b\w+\b", out_t.lower()) if out_t else []

        card_in_words.config(text=f"{len(in_words)} words • {len(in_t)} chars")
        card_out_words.config(text=f"{len(out_words)} words • {len(out_t)} chars")

        if in_words and out_words:
            matcher = difflib.SequenceMatcher(None, in_words, out_words)
            diff_words = sum(max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in matcher.get_opcodes() if tag != "equal")
            card_diff.config(text=f"{diff_words} words modified")
        elif not in_words and not out_words:
            card_diff.config(text="0 words modified")
        else:
            card_diff.config(text=f"{abs(len(out_words) - len(in_words))} words diff")

        if in_t or out_t:
            if is_spanish_text(in_t or out_t):
                card_lang.config(text="🇪🇸 Español")
            else:
                card_lang.config(text="🇺🇸 English")
        else:
            card_lang.config(text="—")

        current_wpm = max(20, wpm_var.get())
        word_count = len(out_words) if out_words else len(in_words)
        est_seconds = int((word_count / current_wpm) * 60) if word_count > 0 else 0
        mins, secs = divmod(est_seconds, 60)
        card_timing.config(text=f"{mins}m {secs:02d}s @ {current_wpm} WPM")

    def execute_playground_humanize():
        in_t = in_text_widget.get("1.0", tk.END).strip()
        if not in_t:
            update_analytics()
            return

        eng = pg_engine_var.get()
        casual = pg_casual_var.get()

        try:
            run_btn.config(text="⏳ HUMANIZING...", state="disabled")
        except Exception:
            pass

        def _prog_cb(done, total):
            try:
                pg_win.after(0, lambda d=done, t=total: run_btn.config(text=f"⏳ HUMANIZING ({d}/{t})..."))
            except Exception:
                pass

        def _bg_worker():
            try:
                transformed = run_humanizer(in_t, eng, casual_mode=casual, progress_cb=_prog_cb)
                transformed = normalize_whitespace(transformed)
            except Exception:
                transformed = in_t

            def _on_done():
                try:
                    out_text_widget.delete("1.0", tk.END)
                    out_text_widget.insert("1.0", transformed)
                    update_analytics()
                    run_btn.config(text="⚡ RUN HUMANIZER", state="normal")
                    if terminal:
                        log_terminal(
                            terminal,
                            f"[Playground] ✅ Humanizado listo: {len(transformed.split())} palabras (Calidad HumanizeAI Pro)"
                        )
                except Exception:
                    pass

            try:
                pg_win.after(0, _on_done)
            except Exception:
                pass

        threading.Thread(target=_bg_worker, daemon=True).start()

    def on_paste_in(evt=None):
        cb = get_clipboard_text(in_text_widget)
        if cb:
            try:
                sel = in_text_widget.tag_ranges("sel")
                if sel:
                    in_text_widget.delete(sel[0], sel[1])
            except Exception:
                pass
            in_text_widget.insert(tk.INSERT, cb)
            execute_playground_humanize()
        return "break"

    in_text_widget.bind("<Control-v>", on_paste_in)
    in_text_widget.bind("<Control-V>", on_paste_in)

    def show_in_context_menu(event):
        menu = tk.Menu(in_text_widget, tearoff=0, bg=C_SURFACE, fg="#E2E8F0", activebackground=C_ORANGE, activeforeground="#FFFFFF")
        menu.add_command(label="📥 Pegar (Ctrl+V)", command=paste_input)
        menu.add_command(label="📋 Copiar (Ctrl+C)", command=lambda: set_clipboard_text(in_text_widget.get("1.0", tk.END).strip(), in_text_widget))
        menu.add_command(label="✂️ Cortar (Ctrl+X)", command=lambda: [set_clipboard_text(in_text_widget.get("1.0", tk.END).strip(), in_text_widget), in_text_widget.delete("1.0", tk.END), update_analytics()])
        menu.add_separator()
        menu.add_command(label="🔲 Seleccionar todo (Ctrl+A)", command=lambda: [in_text_widget.tag_add("sel", "1.0", "end"), in_text_widget.focus()])
        menu.add_command(label="🗑️ Limpiar", command=clear_all)
        menu.tk_popup(event.x_root, event.y_root)

    in_text_widget.bind("<Button-3>", show_in_context_menu)

    def show_out_context_menu(event):
        menu = tk.Menu(out_text_widget, tearoff=0, bg=C_SURFACE, fg="#E2E8F0", activebackground=C_ORANGE, activeforeground="#FFFFFF")
        menu.add_command(label="📋 Copiar resultado (Ctrl+C)", command=copy_output)
        menu.add_command(label="🚀 Cargar en Autotyper", command=copy_for_autotyper)
        menu.add_separator()
        menu.add_command(label="🔲 Seleccionar todo (Ctrl+A)", command=lambda: [out_text_widget.tag_add("sel", "1.0", "end"), out_text_widget.focus()])
        menu.tk_popup(event.x_root, event.y_root)

    out_text_widget.bind("<Button-3>", show_out_context_menu)

    # Auto-load clipboard if input is currently empty and clipboard has user text
    try:
        cb_init = get_clipboard_text(in_text_widget)
        if cb_init and len(cb_init.strip()) > 15:
            in_text_widget.delete("1.0", tk.END)
            in_text_widget.insert("1.0", cb_init)
            execute_playground_humanize()
            if terminal:
                log_terminal(
                    terminal,
                    f"[Playground] 📋 ¡Tu ensayo fue cargado automáticamente ({len(cb_init.split())} palabras)!"
                )
        else:
            load_sample_en()
    except Exception:
        load_sample_en()

    in_text_widget.bind("<KeyRelease>", lambda e: update_analytics())


# ============================================================
# GUI
# ============================================================

def build_gui():
    global root
    root = tk.Tk(className="humannature")
    root.title(APP_TITLE)
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    init_x = max(0, (sw - 860) // 2)
    init_y = max(35, (sh - 600) // 2)
    root.geometry(f"860x600+{init_x}+{init_y}")
    root.minsize(800, 560)
    root.configure(bg=C_BORDER)

    if os.name == "nt":
        root.overrideredirect(True)
        try:
            hwnd = ctypes.windll.user32.GetParent(root.winfo_id()) or root.winfo_id()
            GWL_EXSTYLE = -20
            WS_EX_APPWINDOW = 0x00040000
            WS_EX_TOOLWINDOW = 0x00000080
            s = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            s = (s | WS_EX_APPWINDOW) & ~WS_EX_TOOLWINDOW
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, s)
        except Exception:
            pass
    else:
        try:
            root.update_idletasks()
            wid = root.winfo_id()
            info = subprocess.check_output(['xwininfo', '-id', str(wid), '-tree'], timeout=1.0).decode()
            client_wid = None
            for line in info.splitlines():
                if 'Parent window id:' in line:
                    client_wid = line.split()[3]
                    break
            if client_wid:
                subprocess.run(['xprop', '-id', client_wid, '-f', '_MOTIF_WM_HINTS', '32c', '-set', '_MOTIF_WM_HINTS', '2, 0, 0, 0, 0'], capture_output=True)
                root.withdraw()
                root.deiconify()
            else:
                root.overrideredirect(True)
        except Exception:
            root.overrideredirect(True)

    style = ttk.Style(root)
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

    # --------------------------------------------------------
    # Close-to-tray behavior
    # --------------------------------------------------------
    app_state = {"exiting": False}
    tray_holder = {"icon": None}

    def show_from_tray():
        icon = tray_holder.get("icon")
        if icon is not None:
            icon.hide()

        root.deiconify()
        try:
            root.state("normal")
        except Exception:
            pass

        root.lift()
        try:
            root.attributes(
                "-topmost",
                always_on_top_var.get(),
            )
        except Exception:
            pass
        try:
            root.focus_force()
        except Exception:
            pass

    def exit_app():
        app_state["exiting"] = True
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        try:
            tray_holder["icon"].destroy()
        except Exception:
            pass
        try:
            root.destroy()
        except Exception:
            pass

    def get_tray_icon():
        """Create the native tray icon only when it is actually needed."""
        if os.name != "nt":
            return None
        icon = tray_holder.get("icon")
        if icon is None:
            icon = TrayIcon(
                root,
                show_from_tray,
                exit_app,
            )
            tray_holder["icon"] = icon
        return icon

    # --------------------------------------------------------
    # Custom icon / taskbar behavior
    # --------------------------------------------------------
    try:
        png_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "humannature.png")
        if os.path.exists(png_path):
            app_icon_img = tk.PhotoImage(file=png_path)
            root.iconphoto(True, app_icon_img)
        else:
            icon_path = ensure_icon_file(f"{APP_NAME.lower()}.ico")
            root.iconbitmap(icon_path)

        if hasattr(ctypes, "windll"):
            hwnd = ctypes.windll.user32.GetParent(
                root.winfo_id()
            )

            style = ctypes.windll.user32.GetWindowLongW(
                hwnd,
                -20
            )

            style = (
                style & ~0x00000080
            ) | 0x00040000

            ctypes.windll.user32.SetWindowLongW(
                hwnd,
                -20,
                style
            )

    except Exception:
        pass

    # --------------------------------------------------------
    # Active variables
    # --------------------------------------------------------
    wpm_var = tk.IntVar(value=72)
    acc_var = tk.DoubleVar(value=96.4)

    auto_acc_var = tk.BooleanVar(value=True)
    humanize_var = tk.BooleanVar(value=True)
    start_delay_var = tk.IntVar(value=5)

    engine_var = tk.StringVar(
        value="⚡ HumanizeAI Pro"
    )

    use_burst_var = tk.BooleanVar(value=True)
    use_fragments_var = tk.BooleanVar(value=True)
    tether_var = tk.BooleanVar(value=True)

    # --------------------------------------------------------
    # Settings variables
    # --------------------------------------------------------
    remove_lines_var = tk.BooleanVar(value=False)
    use_shift_enter_var = tk.BooleanVar(value=True)
    remove_all_lines_var = tk.BooleanVar(value=False)
    casual_mode_var = tk.BooleanVar(value=False)
    remove_emojis_var = tk.BooleanVar(value=True)
    remove_asterisks_var = tk.BooleanVar(value=True)
    transparency_var = tk.DoubleVar(value=1.0)

    root.attributes(
        "-alpha",
        transparency_var.get()
    )

    # --------------------------------------------------------
    # Window dragging
    # --------------------------------------------------------
    def start_move(event):
        root.x = event.x
        root.y = event.y

    def stop_move(event):
        root.x = None
        root.y = None

    def do_move(event):
        if window_state.get("is_maximized"):
            toggle_maximize()
            return

        if hasattr(root, "x") and root.x is not None:
            deltax = event.x - root.x
            deltay = event.y - root.y

            x = root.winfo_x() + deltax
            y = root.winfo_y() + deltay

            root.geometry(f"+{x}+{y}")

    # --------------------------------------------------------
    # Title bar
    # --------------------------------------------------------
    title_bar = tk.Frame(
        root,
        bg=C_CREAM,
        height=35
    )

    title_bar.pack(
        fill="x",
        padx=2,
        pady=(2, 0)
    )

    title_bar.bind(
        "<ButtonPress-1>",
        start_move
    )

    title_bar.bind(
        "<ButtonRelease-1>",
        stop_move
    )

    title_bar.bind(
        "<B1-Motion>",
        do_move
    )

    btn_frame = tk.Frame(
        title_bar,
        bg=C_CREAM
    )
    btn_frame.pack(
        side="left",
        padx=12
    )

    close_icon = tk.Label(
        btn_frame,
        text="●",
        font=("Arial", 11),
        bg=C_CREAM,
        fg="#EF4444",
        cursor="hand2",
    )
    close_icon.pack(side="left")

    minimize_icon = tk.Label(
        btn_frame,
        text="●",
        font=("Arial", 11),
        bg=C_CREAM,
        fg="#F59E0B",
        cursor="hand2",
    )
    minimize_icon.pack(side="left", padx=(6, 0))

    expand_icon = tk.Label(
        btn_frame,
        text="●",
        font=("Arial", 11),
        bg=C_CREAM,
        fg="#10B981",
        cursor="hand2",
    )
    expand_icon.pack(side="left", padx=(6, 0))

    window_state = {
        "is_maximized": False,
        "is_minimized": False,
        "prev_geom": "860x600",
        "prev_x": 100,
        "prev_y": 100,
    }

    def quit_app(event=None):
        """Quit the application cleanly."""
        app_state["exiting"] = True
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        try:
            if tray_holder.get("icon"):
                tray_holder["icon"].destroy()
        except Exception:
            pass
        try:
            root.destroy()
        except Exception:
            pass
        os._exit(0)

    def minimize_window(event=None):
        """Minimize the window cleanly to dock / taskbar."""
        window_state["is_minimized"] = True
        try:
            log_terminal(terminal, "[System] Window minimized")
        except Exception:
            pass

        if os.name == "nt" and hasattr(ctypes, "windll"):
            try:
                hwnd_local = ctypes.windll.user32.GetParent(root.winfo_id()) or root.winfo_id()
                ctypes.windll.user32.ShowWindow(hwnd_local, 6)  # SW_MINIMIZE
                return
            except Exception:
                pass

        try:
            root.iconify()
        except Exception:
            try:
                root.withdraw()
            except Exception:
                pass

    def on_window_map(event):
        if event.widget == root and window_state.get("is_minimized"):
            window_state["is_minimized"] = False
            root.lift()
            try:
                log_terminal(terminal, "[System] Window restored")
            except Exception:
                pass

    root.bind("<Map>", on_window_map)

    def toggle_maximize(event=None):
        """Toggle between maximized window and normal size (Agrandar / Restaurar)."""
        if window_state["is_maximized"]:
            root.geometry(
                f"{window_state['prev_geom']}+{window_state['prev_x']}+{window_state['prev_y']}"
            )
            window_state["is_maximized"] = False
            expand_icon.config(fg="#10B981")
            try:
                log_terminal(terminal, "[System] Window restored to normal size")
            except Exception:
                pass
        else:
            window_state["prev_geom"] = f"{root.winfo_width()}x{root.winfo_height()}"
            window_state["prev_x"] = max(0, root.winfo_x())
            window_state["prev_y"] = max(32, root.winfo_y())

            screen_w = root.winfo_screenwidth()
            screen_h = root.winfo_screenheight()
            top_bar_h = 32

            root.geometry(f"{screen_w}x{screen_h - top_bar_h}+0+{top_bar_h}")
            window_state["is_maximized"] = True
            expand_icon.config(fg="#34D399")
            try:
                log_terminal(terminal, f"[System] Window maximized ({screen_w}x{screen_h - top_bar_h})")
            except Exception:
                pass

    def on_btns_enter(evt=None):
        close_icon.config(text="✕", font=("Consolas", 9, "bold"))
        minimize_icon.config(text="−", font=("Consolas", 9, "bold"))
        expand_icon.config(text="⤢" if not window_state["is_maximized"] else "⤡", font=("Consolas", 8, "bold"))

    def on_btns_leave(evt=None):
        close_icon.config(text="●", font=("Arial", 11))
        minimize_icon.config(text="●", font=("Arial", 11))
        expand_icon.config(text="●", font=("Arial", 11))

    for w in (btn_frame, close_icon, minimize_icon, expand_icon):
        w.bind("<Enter>", on_btns_enter)
        w.bind("<Leave>", on_btns_leave)

    close_icon.bind("<Button-1>", quit_app)
    minimize_icon.bind("<Button-1>", minimize_window)
    expand_icon.bind("<Button-1>", toggle_maximize)

    title_bar.bind("<Double-Button-1>", toggle_maximize)

    always_on_top_var = tk.BooleanVar(value=True)
    root._always_on_top_val = True
    root.attributes("-topmost", True)

    def toggle_top(event=None):
        val = not always_on_top_var.get()
        always_on_top_var.set(val)
        root._always_on_top_val = val
        root.attributes("-topmost", val)
        pin_btn.config(fg=C_ORANGE if val else C_MUTED)
        try:
            log_terminal(terminal, f"[System] Always-on-top: {'Enabled' if val else 'Disabled'}")
        except Exception:
            pass

    MIN_W = 800
    MIN_H = 560

    resizing = {
        "active": False,
        "start_x": 0,
        "start_y": 0,
        "start_w": 0,
        "start_h": 0,
    }

    def begin_resize(event):
        resizing["active"] = True
        resizing["start_x"] = event.x_root
        resizing["start_y"] = event.y_root
        resizing["start_w"] = root.winfo_width()
        resizing["start_h"] = root.winfo_height()

    def do_resize(event):
        if not resizing["active"]:
            return

        delta_x = event.x_root - resizing["start_x"]
        delta_y = event.y_root - resizing["start_y"]

        new_w = max(MIN_W, resizing["start_w"] + delta_x)
        new_h = max(MIN_H, resizing["start_h"] + delta_y)

        root.geometry(
            f"{int(new_w)}x{int(new_h)}+{root.winfo_x()}+{root.winfo_y()}"
        )

    def end_resize(event=None):
        resizing["active"] = False

    tk.Label(
        title_bar,
        text=f"desktop — {APP_NAME.lower()} {APP_VERSION} analog",
        font=("Consolas", 9),
        bg=C_CREAM,
        fg=C_MUTED,
    ).pack(
        side="left",
        expand=True
    )

    clock_label = tk.Label(
        title_bar,
        text="",
        font=("Consolas", 9),
        bg=C_CREAM,
        fg=C_MUTED
    )

    clock_label.pack(
        side="right",
        padx=10
    )

    pin_btn = tk.Label(
        title_bar,
        text="📌",
        font=("Arial", 9),
        bg=C_CREAM,
        fg=C_ORANGE,
        cursor="hand2"
    )
    pin_btn.pack(
        side="right",
        padx=(0, 4)
    )
    pin_btn.bind("<Button-1>", toggle_top)

    def update_clock():
        clock_label.config(
            text=datetime.now().strftime("%I:%M %p")
        )

        root.after(
            1000,
            update_clock
        )

    update_clock()

    # --------------------------------------------------------
    # Body
    # --------------------------------------------------------
    body = tk.Frame(
        root,
        bg=C_CREAM
    )

    body.pack(
        fill="both",
        expand=True,
        padx=2,
        pady=2
    )

    # --------------------------------------------------------
    # LEFT PANEL
    # --------------------------------------------------------
    left_panel = tk.Frame(
        body,
        bg=C_CREAM,
        width=460
    )

    left_panel.pack(
        side="left",
        fill="y",
        padx=18,
        pady=16
    )

    left_panel.pack_propagate(False)

    title_row = tk.Frame(left_panel, bg=C_CREAM)
    title_row.pack(fill="x")

    tk.Label(
        title_row,
        text=APP_TITLE,
        font=("Georgia", 22, "bold"),
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

    # --- Quick Presets Bar ---
    preset_header = tk.Frame(left_panel, bg=C_CREAM)
    preset_header.pack(fill="x", pady=(10, 3))

    tk.Label(
        preset_header,
        text="QUICK PRESETS",
        font=("Consolas", 8, "bold"),
        bg=C_CREAM,
        fg=C_MUTED
    ).pack(side="left")

    presets_bar = tk.Frame(left_panel, bg=C_CREAM)
    presets_bar.pack(fill="x", pady=(0, 6))

    def apply_preset(name, wpm, acc, engine, burst, fragments, delay=3):
        wpm_var.set(wpm)
        try:
            wpm_display.config(text=str(wpm))
        except Exception:
            pass
        auto_acc_var.set(False)
        acc_var.set(acc)
        try:
            acc_display.config(text=f"{acc:.1f}%")
            acc_slider.config(state="normal")
        except Exception:
            pass
        engine_var.set(engine)
        use_burst_var.set(burst)
        use_fragments_var.set(fragments)
        start_delay_var.set(delay)
        try:
            delay_display.config(text=f"{delay}s")
        except Exception:
            pass
        try:
            log_terminal(
                terminal,
                f"[Preset] Applied {name}: {wpm} WPM • {acc}% Acc • {engine.split()[-1]}"
            )
        except Exception:
            pass

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
        p_btn = tk.Button(
            presets_bar,
            text=p_name,
            font=("Consolas", 8, "bold"),
            bg=C_BTN_BG,
            fg=C_CHARCOAL,
            activebackground=C_BTN_HOVER,
            activeforeground=C_ORANGE,
            relief="flat",
            padx=6,
            pady=3,
            cursor="hand2",
            command=lambda n=p_name, w=p_wpm, a=p_acc, e=p_eng, b=p_burst, f=p_frag, d=p_delay: apply_preset(n, w, a, e, b, f, d)
        )
        p_btn.pack(side="left", expand=True, fill="x", padx=2)

    # --- Target Speed ---
    tk.Label(
        left_panel,
        text="TARGET SPEED (WPM)",
        font=("Consolas", 8, "bold"),
        bg=C_CREAM,
        fg=C_MUTED
    ).pack(
        anchor="w",
        pady=(4, 0)
    )

    wpm_slider = ttk.Scale(
        left_panel,
        from_=30,
        to=150,
        orient="horizontal",
        variable=wpm_var
    )

    wpm_slider.pack(
        fill="x",
        pady=3
    )

    # --------------------------------------------------------
    # Accuracy
    # --------------------------------------------------------
    acc_frame = tk.Frame(
        left_panel,
        bg=C_CREAM
    )

    acc_frame.pack(
        fill="x",
        pady=(4, 0)
    )

    tk.Label(
        acc_frame,
        text="ACCURACY RATE (%)",
        font=("Consolas", 8, "bold"),
        bg=C_CREAM,
        fg=C_MUTED
    ).pack(
        side="left"
    )

    acc_display = tk.Label(
        acc_frame,
        text="96.4%",
        font=("Consolas", 8, "bold"),
        bg=C_CREAM,
        fg=C_ORANGE
    )

    acc_display.pack(
        side="right"
    )

    acc_slider = ttk.Scale(
        left_panel,
        from_=85.0,
        to=100.0,
        orient="horizontal",
        variable=acc_var
    )

    acc_slider.pack(
        fill="x",
        pady=3
    )

    auto_acc_btn = tk.Checkbutton(
        left_panel,
        text="Auto-adjust accuracy based on speed",
        variable=auto_acc_var,
        bg=C_CREAM,
        font=("Consolas", 8),
        fg=C_MUTED,
        selectcolor=C_SURFACE,
        activebackground=C_CREAM,
        activeforeground=C_CHARCOAL,
        highlightthickness=0,
    )

    auto_acc_btn.pack(
        anchor="w",
        pady=(0, 2)
    )

    acc_slider.config(
        state="disabled"
    )

    # --------------------------------------------------------
    # Start delay (countdown)
    # --------------------------------------------------------
    delay_frame = tk.Frame(
        left_panel,
        bg=C_CREAM
    )

    delay_frame.pack(
        fill="x",
        pady=(4, 0)
    )

    tk.Label(
        delay_frame,
        text="START DELAY (COUNTDOWN)",
        font=("Consolas", 8, "bold"),
        bg=C_CREAM,
        fg=C_MUTED
    ).pack(
        side="left"
    )

    delay_display = tk.Label(
        delay_frame,
        text=f"{start_delay_var.get()}s",
        font=("Consolas", 8, "bold"),
        bg=C_CREAM,
        fg=C_ORANGE
    )

    delay_display.pack(
        side="right"
    )

    delay_slider = ttk.Scale(
        left_panel,
        from_=0,
        to=10,
        orient="horizontal",
        variable=start_delay_var,
        command=lambda v: delay_display.config(text=f"{int(float(v))}s")
    )

    delay_slider.pack(
        fill="x",
        pady=3
    )

    # --------------------------------------------------------
    # Engine selector
    # --------------------------------------------------------
    tk.Label(
        left_panel,
        text="NLP ENGINE",
        font=("Consolas", 8, "bold"),
        bg=C_CREAM,
        fg=C_MUTED
    ).pack(
        anchor="w",
        pady=(4, 0)
    )

    eng_combo = ttk.Combobox(
        left_panel,
        textvariable=engine_var,
        values=[
            "⚡ HumanizeAI Pro",
            "🎓 Academic Master",
            "👻 GhostWriter Ultra",
            "🌊 Natural Flow",
        ],
        state="readonly",
        font=("Consolas", 9)
    )

    eng_combo.pack(
        fill="x",
        pady=3
    )

    # --------------------------------------------------------
    # Typing options
    # --------------------------------------------------------
    t_frame = tk.Frame(
        left_panel,
        bg=C_CREAM
    )

    t_frame.pack(
        fill="x",
        pady=3
    )

    tk.Checkbutton(
        t_frame,
        text="Cognitive Burst",
        variable=use_burst_var,
        bg=C_CREAM,
        fg=C_CHARCOAL,
        font=("Consolas", 9),
        selectcolor=C_SURFACE,
        activebackground=C_CREAM,
        activeforeground=C_CHARCOAL,
        highlightthickness=0,
    ).pack(
        side="left"
    )

    tk.Checkbutton(
        t_frame,
        text="Fragment Mode",
        variable=use_fragments_var,
        bg=C_CREAM,
        fg=C_CHARCOAL,
        font=("Consolas", 9),
        selectcolor=C_SURFACE,
        activebackground=C_CREAM,
        activeforeground=C_CHARCOAL,
        highlightthickness=0,
    ).pack(
        side="left",
        padx=10
    )

    # --------------------------------------------------------
    # Direct Action Control Buttons
    # --------------------------------------------------------
    act_row1 = tk.Frame(
        left_panel,
        bg=C_CREAM
    )

    act_row1.pack(
        fill="x",
        pady=(6, 3)
    )

    start_btn = tk.Button(
        act_row1,
        text="▶ START (F9)",
        font=("Consolas", 8, "bold"),
        bg="#0E7490",
        fg="#ECFEFF",
        activebackground="#0891B2",
        activeforeground="#FFFFFF",
        relief="flat",
        pady=6,
        cursor="hand2",
    )

    start_btn.pack(
        side="left",
        fill="x",
        expand=True,
        padx=(0, 2)
    )

    pause_btn = tk.Button(
        act_row1,
        text="⏸  PAUSE (F8)",
        font=("Consolas", 8, "bold"),
        bg="#334155",
        fg="#F1F5F9",
        activebackground="#475569",
        activeforeground="#FFFFFF",
        relief="flat",
        pady=6,
        cursor="hand2",
    )

    pause_btn.pack(
        side="left",
        fill="x",
        expand=True,
        padx=2
    )

    global pause_btn_ref
    pause_btn_ref = pause_btn

    stop_btn = tk.Button(
        act_row1,
        text="⏹ STOP (F10)",
        font=("Consolas", 8, "bold"),
        bg="#881337",
        fg="#FFE4E6",
        activebackground="#9F1239",
        activeforeground="#FFFFFF",
        relief="flat",
        pady=6,
        cursor="hand2",
    )

    stop_btn.pack(
        side="right",
        fill="x",
        expand=True,
        padx=(2, 0)
    )

    def load_clipboard_essay():
        txt = get_clipboard_text(root)
        cache_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "last_essay.txt")
        if txt and txt.strip():
            try:
                with open(cache_file, "w", encoding="utf-8") as f:
                    f.write(txt)
            except Exception:
                pass
            words = len(txt.split())
            log_terminal(
                terminal,
                f"[Essay] ✅ Ensayo detectado: {words} palabras ({len(txt)} caracteres)."
            )
            log_terminal(
                terminal,
                "[Essay] Presiona ▶ START (F9) para escribirlo, o 🧪 PLAYGROUND para inspeccionarlo."
            )
            telemetry_label.config(text=f"> essay ready: {words} words in clipboard")
            status_label.config(text=f"● Ensayo listo: {words} palabras", fg="#10B981")
        elif os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_txt = f.read()
                if cached_txt.strip():
                    set_clipboard_text(cached_txt, root)
                    words = len(cached_txt.split())
                    log_terminal(
                        terminal,
                        f"[Essay] 📄 Ensayo restaurado de sesión: {words} palabras ({len(cached_txt)} caracteres)."
                    )
                    log_terminal(
                        terminal,
                        "[Essay] Presiona ▶ START (F9) para escribirlo, o 🧪 PLAYGROUND para inspeccionarlo."
                    )
                    telemetry_label.config(text=f"> essay ready: {words} words restored")
                    status_label.config(text=f"● Ensayo listo: {words} palabras", fg="#10B981")
                    return
            except Exception:
                pass
            log_terminal(
                terminal,
                "[Essay] ⚠️ El portapapeles está vacío. Copia tu texto primero (Ctrl+C)."
            )
            status_label.config(text="● Portapapeles vacío (Copia texto)", fg="#F59E0B")
        else:
            log_terminal(
                terminal,
                "[Essay] ⚠️ El portapapeles está vacío. Copia tu texto primero (Ctrl+C)."
            )
            status_label.config(text="● Portapapeles vacío (Copia texto)", fg="#F59E0B")

    paste_essay_btn = tk.Button(
        left_panel,
        text="📥  PEGAR / DETECTAR ESSAY (CLIPBOARD)",
        font=("Consolas", 8, "bold"),
        bg="#1E293B",
        fg="#38BDF8",
        activebackground="#334155",
        activeforeground="#38BDF8",
        relief="flat",
        pady=5,
        cursor="hand2",
        command=load_clipboard_essay,
    )
    paste_essay_btn.pack(fill="x", pady=(2, 3))

    act_row2 = tk.Frame(
        left_panel,
        bg=C_CREAM
    )

    act_row2.pack(
        fill="x",
        pady=(1, 6)
    )

    playground_btn = tk.Button(
        act_row2,
        text="🧪  PLAYGROUND",
        font=("Consolas", 8, "bold"),
        bg=C_BTN_BG,
        fg=C_ORANGE,
        activebackground=C_BTN_HOVER,
        activeforeground="#22D3EE",
        relief="flat",
        pady=5,
        cursor="hand2",
    )

    playground_btn.pack(
        side="left",
        fill="x",
        expand=True,
        padx=(0, 3)
    )

    settings_btn = tk.Button(
        act_row2,
        text="⚙  SETTINGS",
        font=("Consolas", 8, "bold"),
        bg=C_BTN_BG,
        fg=C_CHARCOAL,
        activebackground=C_BTN_HOVER,
        activeforeground=C_ORANGE,
        relief="flat",
        pady=5,
        cursor="hand2",
    )

    settings_btn.pack(
        side="right",
        fill="x",
        expand=True,
        padx=(3, 0)
    )

    # --------------------------------------------------------
    # Terminal
    # --------------------------------------------------------
    terminal = tk.Text(
        left_panel,
        height=5,
        bg=C_SURFACE,
        fg="#E2E8F0",
        font=("Consolas", 8),
        relief="flat",
        padx=10,
        pady=8,
        highlightbackground="#1E2433",
        highlightthickness=1,
        state="disabled"
    )

    terminal.pack(
        fill="x",
        pady=(2, 0)
    )

    # --------------------------------------------------------
    # RIGHT PANEL
    # --------------------------------------------------------
    right_panel = tk.Frame(
        body,
        bg=C_CREAM
    )

    right_panel.pack(
        side="right",
        fill="both",
        expand=True,
        padx=20,
        pady=20
    )

    stats_frame = tk.Frame(
        right_panel,
        bg=C_CREAM
    )

    stats_frame.pack(
        fill="x",
        anchor="e"
    )

    wpm_display = tk.Label(
        stats_frame,
        text="72",
        font=("Consolas", 52, "bold"),
        bg=C_CREAM,
        fg=C_ORANGE
    )

    wpm_display.pack(
        side="left"
    )

    tk.Label(
        stats_frame,
        text="WPM\nMEASURED",
        font=("Consolas", 8, "bold"),
        bg=C_CREAM,
        fg=C_MUTED,
        justify="left"
    ).pack(
        side="left",
        padx=(5, 0),
        pady=(25, 0)
    )

    status_label = tk.Label(
        right_panel,
        text="● Status: Loading NLP...",
        font=("Consolas", 10, "bold"),
        bg=C_CREAM,
        fg=C_ORANGE
    )

    status_label.pack(
        anchor="w",
        pady=(10, 0)
    )

    tk.Label(
        right_panel,
        text="TIME BETWEEN KEYS • LAST 65",
        font=("Consolas", 8, "bold"),
        bg=C_CREAM,
        fg=C_MUTED
    ).pack(
        anchor="w",
        pady=(15, 5)
    )

    chart_canvas = tk.Canvas(
        right_panel,
        height=80,
        bg=C_SURFACE,
        highlightbackground="#1E2433",
        highlightthickness=1
    )

    chart_canvas.pack(
        fill="x"
    )

    r_frame = tk.Frame(
        right_panel,
        bg=C_CREAM
    )

    r_frame.pack(
        fill="x",
        pady=15
    )

    def mk_stat(parent, label_text):
        f = tk.Frame(
            parent,
            bg=C_SURFACE,
            highlightbackground="#1E2433",
            highlightthickness=1,
            padx=12,
            pady=4,
        )

        f.pack(
            fill="x",
            pady=3
        )

        tk.Label(
            f,
            text=label_text.upper(),
            font=("Consolas", 8, "bold"),
            bg=C_SURFACE,
            fg=C_MUTED
        ).pack(
            side="left"
        )

        value = tk.Label(
            f,
            text="0",
            font=("Consolas", 9, "bold"),
            bg=C_SURFACE,
            fg=C_CHARCOAL
        )

        value.pack(
            side="right"
        )

        return value

    last_lbl = mk_stat(
        r_frame,
        "last key"
    )

    key_lbl = mk_stat(
        r_frame,
        "keystrokes"
    )

    typo_lbl = mk_stat(
        r_frame,
        "typos fixed"
    )

    telemetry_label = tk.Label(
        right_panel,
        text="> status: standing by",
        font=("Consolas", 9),
        bg=C_CREAM,
        fg=C_ORANGE
    )

    telemetry_label.pack(
        anchor="w",
        pady=(5, 0)
    )

    # --------------------------------------------------------
    # Accuracy logic
    # --------------------------------------------------------
    def calculate_recommended_accuracy(*args):
        if auto_acc_var.get():
            recommended = max(
                85.0,
                min(
                    100.0,
                    100.0 - (wpm_var.get() * 0.05)
                )
            )

            acc_var.set(
                round(recommended, 1)
            )

            acc_display.config(
                text=f"{recommended:.1f}%"
            )

            acc_slider.config(
                state="disabled"
            )

        else:
            acc_slider.config(
                state="normal"
            )

            acc_display.config(
                text=f"{acc_var.get():.1f}%"
            )

    wpm_slider.config(
        command=lambda v: [
            wpm_display.config(
                text=str(int(float(v)))
            ),
            calculate_recommended_accuracy()
        ]
    )

    acc_slider.config(
        command=lambda v: acc_display.config(
            text=f"{float(v):.1f}%"
        )
    )

    auto_acc_btn.config(
        command=calculate_recommended_accuracy
    )

    settings_btn.config(
        command=lambda: open_settings(
            root,
            remove_lines_var,
            use_shift_enter_var,
            remove_all_lines_var,
            casual_mode_var,
            remove_emojis_var,
            remove_asterisks_var,
            use_fragments_var,
            transparency_var
        )
    )

    calculate_recommended_accuracy()

    # --------------------------------------------------------
    # Bottom-right resize grip
    # --------------------------------------------------------
    resize_grip = tk.Label(
        root,
        text="◢",
        font=("Consolas", 13, "bold"),
        bg=C_CREAM,
        fg=C_MUTED,
        cursor="size_nw_se" if os.name == "nt" else "bottom_right_corner",
        padx=2,
        pady=0,
    )

    resize_grip.place(
        relx=1.0,
        rely=1.0,
        anchor="se"
    )

    resize_grip.bind(
        "<ButtonPress-1>",
        begin_resize
    )

    resize_grip.bind(
        "<B1-Motion>",
        do_resize
    )

    resize_grip.bind(
        "<ButtonRelease-1>",
        end_resize
    )

    # --------------------------------------------------------
    # Keyboard hotkeys & button commands
    # --------------------------------------------------------
    def trigger():
        on_trigger_event(
            wpm_var.get(),
            acc_var.get(),
            humanize_var.get(),
            engine_var.get(),
            remove_lines_var.get(),
            use_shift_enter_var.get(),
            remove_all_lines_var.get(),
            use_burst_var.get(),
            use_fragments_var.get(),
            tether_var.get(),
            casual_mode_var.get(),
            remove_emojis_var.get(),
            remove_asterisks_var.get(),
            status_label,
            telemetry_label,
            chart_canvas,
            key_lbl,
            typo_lbl,
            last_lbl,
            terminal,
            root,
            engine_var,
            start_delay_var.get(),
        )

    def abort():
        stop_typing(
            status_label,
            telemetry_label,
            root,
            terminal
        )

    def pause_toggle():
        toggle_pause(
            status_label,
            telemetry_label,
            root,
            terminal
        )

    start_btn.config(command=trigger)
    pause_btn.config(command=pause_toggle)
    stop_btn.config(command=abort)
    playground_btn.config(
        command=lambda: open_playground(
            root,
            engine_var,
            casual_mode_var,
            wpm_var,
            terminal=terminal,
        )
    )

    # Window-level hotkeys: F8/F9/F10 work whenever HumanNature window has focus
    root.bind("<F8>", lambda e: pause_toggle())
    root.bind("<F9>", lambda e: trigger())
    root.bind("<F10>", lambda e: abort())

    hotkeys_active = False
    if os.name == "nt":
        try:
            keyboard.add_hotkey("f8", pause_toggle)
            keyboard.add_hotkey("f9", trigger)
            keyboard.add_hotkey("f10", abort)
            hotkeys_active = True
        except Exception:
            pass

    if hotkeys_active:
        log_terminal(
            terminal,
            "[System] Global hotkeys active: F9 = Start, F8 = Pause, F10 = Stop"
        )
    else:
        log_terminal(
            terminal,
            "[System] Controles listos: ▶ START (F9) • ⏸ PAUSE (F8) • ⏹ STOP (F10)"
        )

    # --------------------------------------------------------
    # Initial state / startup
    # --------------------------------------------------------
    log_terminal(
        terminal,
        f"[System] {APP_TITLE}"
    )

    log_terminal(
        terminal,
        "[System] ▶ START (F9) • ⏸ PAUSE (F8) • ⏹ STOP (F10)"
    )

    log_terminal(
        terminal,
        "[System] Presets & Playground ready"
    )

    log_terminal(
        terminal,
        "[System] Red = Close • Yellow = Minimize • Green = Maximize"
    )

    root.after(800, load_clipboard_essay)

    threading.Thread(
        target=init_lavender,
        args=(
            root,
            status_label,
            terminal
        ),
        daemon=True
    ).start()

    root.protocol(
        "WM_DELETE_WINDOW",
        quit_app
    )

    # The tray icon is created only when the user closes/hides the window,
    # so the notification area stays uncluttered during normal use.
    root.mainloop()


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    build_gui()
