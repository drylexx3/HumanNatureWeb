#!/usr/bin/env python3
"""
HumanNature Public Tunnel Runner
Keeps a persistent, free public HTTPS domain active via Cloudflare
"""
import os
import re
import sys
import time
import signal
import subprocess

DIR = os.path.dirname(os.path.abspath(__file__))
URL_FILE = os.path.join(DIR, "PUBLIC_URL.txt")
LOG_FILE = os.path.expanduser("~/.cache/humannature-tunnel.log")

proc = None

def cleanup(sig=None, frame=None):
    global proc
    if proc:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def log(msg):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n"
    sys.stdout.write(line)
    sys.stdout.flush()
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass

def main():
    global proc
    log("🚀 Starting HumanNature Cloudflare Tunnel...")

    while True:
        try:
            proc = subprocess.Popen(
                ["cloudflared", "tunnel", "--url", "http://127.0.0.1:5050"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            current_url = None
            for line in iter(proc.stderr.readline, ''):
                if not line:
                    break
                # Look for trycloudflare.com URL
                m = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
                if m:
                    current_url = m.group(0)
                    log(f"✅ Live Public HTTPS Domain: {current_url}")
                    with open(URL_FILE, "w", encoding="utf-8") as f:
                        f.write(current_url.strip() + "\n")
            
            proc.wait()
            log("⚠️ Cloudflared process exited, restarting in 3 seconds...")
            time.sleep(3)
        except Exception as e:
            log(f"Tunnel error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
