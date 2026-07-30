#!/usr/bin/env python3
"""
JARVIS launcher.

    python run.py            start Jarvis and open the HUD
    python run.py devices    list microphones, so you can pin one in config.yaml
    python run.py doctor     check that everything is installed and configured
"""
from __future__ import annotations

import sys
import threading
import time
import webbrowser

BANNER = r"""
     ____   _____   ______  _    _  _____  _____
    |  _ \ / ____| |  ____|| |  | ||_   _|/ ____|
    | |_) | |  __  | |__   | |  | |  | | | (___
    |  _ <| | |_ | |  __|  | |  | |  | |  \___ \
    | |_) | |__| | | |     | |__| | _| |_ ____) |
    |____/ \_____| |_|      \____/ |_____|_____/

        J . A . R . V . I . S .      online
"""


def doctor() -> int:
    ok = True
    print("\n  Checking your setup\n  " + "-" * 46)

    if sys.version_info < (3, 9):
        print(f"  FAIL  Python {sys.version_info.major}.{sys.version_info.minor} — need 3.9+")
        ok = False
    else:
        print(f"  ok    Python {sys.version_info.major}.{sys.version_info.minor}")

    required = [
        ("anthropic", "Claude API"),
        ("fastapi", "web server"),
        ("uvicorn", "web server"),
        ("numpy", "audio maths"),
        ("sounddevice", "microphone"),
        ("faster_whisper", "speech to text"),
        ("edge_tts", "speech out"),
        ("psutil", "system telemetry"),
        ("mss", "screen capture"),
        ("PIL", "image handling"),
        ("yaml", "config"),
    ]
    for mod, why in required:
        try:
            __import__(mod)
            print(f"  ok    {mod:<18}{why}")
        except ImportError:
            print(f"  FAIL  {mod:<18}{why} — pip install -r requirements.txt")
            ok = False

    try:
        __import__("openwakeword")
        print(f"  ok    {'openwakeword':<18}wake word")
    except ImportError:
        print("  warn  openwakeword     missing — push-to-talk will still work")

    from core.config import ANTHROPIC_API_KEY

    if ANTHROPIC_API_KEY.startswith("sk-ant-"):
        print("  ok    ANTHROPIC_API_KEY found")
    else:
        print("  FAIL  ANTHROPIC_API_KEY missing — copy .env.example to .env")
        ok = False

    try:
        import sounddevice as sd

        default_in = sd.query_devices(kind="input")
        print(f"  ok    microphone        {default_in['name']}")
    except Exception as exc:
        print(f"  FAIL  microphone        {exc}")
        ok = False

    print("  " + "-" * 46)
    print("  All clear. Run: python run.py\n" if ok else "  Fix the failures above, then re-run.\n")
    return 0 if ok else 1


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"

    if cmd == "devices":
        from core.audio import list_devices

        print(list_devices())
        return 0

    if cmd == "doctor":
        return doctor()

    import uvicorn

    from core.config import ANTHROPIC_API_KEY, cfg

    if not ANTHROPIC_API_KEY:
        print("\n  No ANTHROPIC_API_KEY. Copy .env.example to .env and add your key.\n")
        return 1

    host = cfg.get("server.host", "127.0.0.1")
    port = int(cfg.get("server.port", 8123))
    url = f"http://{host}:{port}"

    print(BANNER)
    print(f"  HUD          {url}")
    print(f"  Model        {cfg.get('brain.model')}")
    print(f"  Wake word    {'Hey Jarvis' if cfg.get('voice.wake_word') else 'disabled'}")
    print(f"  Voice        {cfg.get('tts.voice')} via {cfg.get('tts.engine')}")
    print("\n  First run downloads the speech models. Give it a minute.\n")

    if cfg.get("server.open_browser", True):
        threading.Thread(
            target=lambda: (time.sleep(2.0), webbrowser.open(url)), daemon=True
        ).start()

    uvicorn.run("core.server:app", host=host, port=port, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
