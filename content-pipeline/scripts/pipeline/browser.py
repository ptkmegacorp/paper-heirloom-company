"""Deterministic Firefox control helpers for review pages."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path


def _session_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = f"/home/bot/.local/bin:{env.get('PATH', '/usr/bin:/bin')}"
    env.setdefault("DISPLAY", ":0")
    env.setdefault("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    xauth = Path.home() / ".Xauthority"
    if "XAUTHORITY" not in env and xauth.is_file():
        env["XAUTHORITY"] = str(xauth)
    return env


def _firefox_bin() -> str:
    for name in ("firefox-esr", "firefox"):
        found = shutil.which(name)
        if found:
            return found
    raise RuntimeError("firefox not installed")


def _wm_available() -> bool:
    return shutil.which("i3-msg") is not None or shutil.which("swaymsg") is not None


def _wm_msg(args: list[str]) -> subprocess.CompletedProcess[str]:
    helper = Path("/home/bot/.config/i3/bin/wm-msg.sh")
    if helper.is_file():
        return subprocess.run([str(helper), *args], env=_session_env(), capture_output=True, text=True, check=False)
    cmd = "i3-msg" if shutil.which("i3-msg") else "swaymsg"
    return subprocess.run([cmd, *args], env=_session_env(), capture_output=True, text=True, check=False)


def firefox_status() -> dict[str, object]:
    windows: list[str] = []
    if shutil.which("xdotool"):
        proc = subprocess.run(["xdotool", "search", "--class", "firefox"], env=_session_env(), capture_output=True, text=True, check=False)
        windows = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    return {
        "ok": True,
        "firefox_bin": shutil.which("firefox-esr") or shutil.which("firefox"),
        "wm_available": _wm_available(),
        "window_count": len(windows),
        "window_ids": windows,
    }


def open_url(url: str) -> dict[str, object]:
    browser = _firefox_bin()
    if _wm_available():
        _wm_msg(["exec", f"{browser} --new-window {url}"])
    else:
        subprocess.Popen([browser, "--new-window", url], env=_session_env(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    result = firefox_status()
    result.update({"action": "open", "url": url, "browser": browser})
    return result


def open_file(path: Path | str) -> dict[str, object]:
    resolved = Path(path).resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"file not found: {resolved}")
    return open_url(resolved.as_uri())


def refresh() -> dict[str, object]:
    if not shutil.which("xdotool"):
        raise RuntimeError("xdotool not installed")
    env = _session_env()
    proc = subprocess.run(["xdotool", "search", "--class", "firefox"], env=env, capture_output=True, text=True, check=False)
    wid = next((line.strip() for line in proc.stdout.splitlines() if line.strip()), "")
    if not wid:
        raise RuntimeError("no firefox window found")
    subprocess.run(["xdotool", "windowactivate", "--sync", wid], env=env, check=False)
    subprocess.run(["xdotool", "key", "--window", wid, "--delay", "40", "F5"], env=env, check=False)
    result = firefox_status()
    result.update({"action": "refresh", "window_id": wid})
    return result


def close() -> dict[str, object]:
    if _wm_available():
        _wm_msg(['[app_id="firefox"] kill'])
        _wm_msg(['[class="firefox"] kill'])
        _wm_msg(['[instance="firefox"] kill'])
    subprocess.run(["pkill", "-x", "firefox-esr"], check=False)
    subprocess.run(["pkill", "-x", "firefox"], check=False)
    return {"ok": True, "action": "close", **firefox_status()}
