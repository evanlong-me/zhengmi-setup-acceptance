"""Assert the config files zhengmi-setup.ps1 writes on Windows."""

from __future__ import annotations

import io
import json
import os
import pathlib
import sys

HOME = pathlib.Path(os.environ["USERPROFILE"])
APPDATA = pathlib.Path(os.environ.get("APPDATA") or HOME / "AppData" / "Roaming")
LOCALAPPDATA = pathlib.Path(os.environ.get("LOCALAPPDATA") or HOME / "AppData" / "Local")
TOOL = os.environ["TOOL"]
BASE_URL = os.environ.get("ZHENGMI_BASE_URL", "https://ci.example.com")
API_KEY = os.environ.get("ZHENGMI_API_KEY", "sk-ci-test-key-000000000000")

# The Windows console defaults to cp1252; printing CJK raises UnicodeEncodeError
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

failures = []


def check(cond, msg):
    print(("  OK   " if cond else "  FAIL ") + msg)
    if not cond:
        failures.append(msg)


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        check(False, f"{path} is not valid JSON: {exc}")
        return {}


def dig(data, *keys):
    cur = data
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur


def scan_for_url(bases):
    hits = []
    for base in bases:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or p.stat().st_size > 1_000_000:
                continue
            if p.suffix.lower() not in {".json", ".jsonc", ".toml", ".env", ".yaml", ".yml", ""}:
                continue
            try:
                if BASE_URL in p.read_text(encoding="utf-8", errors="ignore"):
                    hits.append(p)
            except OSError:
                pass
    return hits


print(f"== {TOOL} on Windows ==")
print(f"   HOME={HOME}")
print(f"   APPDATA={APPDATA}")

if TOOL == "claude":
    f = HOME / ".claude" / "settings.json"
    check(f.exists(), f"{f} exists")
    if f.exists():
        env = load_json(f).get("env", {})
        check(env.get("ANTHROPIC_BASE_URL") == BASE_URL, "ANTHROPIC_BASE_URL correct")
        check(env.get("ANTHROPIC_AUTH_TOKEN") == API_KEY, "ANTHROPIC_AUTH_TOKEN correct")

elif TOOL == "claude-desktop":
    # Setup-ClaudeDesktop writes under LOCALAPPDATA on Windows and ~/.config elsewhere
    roots = [LOCALAPPDATA / "Claude-3p", HOME / ".config" / "Claude-3p"]
    hits = scan_for_url(roots)
    check(bool(hits), "Claude Desktop config contains gateway URL")
    for h in hits[:3]:
        print("       wrote:", h)

elif TOOL == "codex":
    d = HOME / ".codex"
    check((d / "config.toml").exists(), f"{d}/config.toml exists")
    check((d / "auth.json").exists(), f"{d}/auth.json exists")
    if (d / "auth.json").exists():
        check(load_json(d / "auth.json").get("OPENAI_API_KEY") == API_KEY, "auth.json key correct")
    if (d / "config.toml").exists():
        check(BASE_URL in (d / "config.toml").read_text(encoding="utf-8"), "config.toml contains gateway URL")

elif TOOL == "gemini":
    d = HOME / ".gemini"
    check((d / ".env").exists(), f"{d}/.env exists")
    check((d / "settings.json").exists(), f"{d}/settings.json exists")
    if (d / ".env").exists():
        text = (d / ".env").read_text(encoding="utf-8")
        check(BASE_URL in text, ".env contains gateway URL")
        check(API_KEY in text, ".env contains key")
    if (d / "settings.json").exists():
        check(dig(load_json(d / "settings.json"), "security", "auth", "selectedType") == "gemini-api-key",
              "security.auth.selectedType = gemini-api-key")

elif TOOL == "opencode":
    f = HOME / ".config" / "opencode" / "opencode.json"
    check(f.exists(), f"{f} exists")
    if f.exists():
        check(BASE_URL in json.dumps(load_json(f)), "opencode.json contains gateway URL")

elif TOOL == "hermes":
    base = LOCALAPPDATA / "hermes"
    check(base.exists(), f"{base} exists")
    if base.exists():
        hits = scan_for_url([base])
        check(bool(hits), "hermes config contains gateway URL")

elif TOOL == "pi":
    f = HOME / ".pi" / "agent" / "models.json"
    check(f.exists(), f"{f} exists")
    if f.exists():
        check(BASE_URL in json.dumps(load_json(f)), "models.json contains gateway URL")

elif TOOL == "openclaw":
    hits = scan_for_url([HOME / ".openclaw"])
    check(bool(hits), "openclaw config contains gateway URL")
    for h in hits[:3]:
        print("       wrote:", h)

elif TOOL == "codebuddy":
    hits = scan_for_url([HOME / ".codebuddy", APPDATA / "CodeBuddy"])
    check(bool(hits), "CodeBuddy config contains gateway URL")
    for h in hits[:3]:
        print("       wrote:", h)

elif TOOL == "kilo":
    f = HOME / ".config" / "kilo" / "kilo.jsonc"
    check(f.exists(), f"{f} exists")
    if f.exists():
        check(BASE_URL in f.read_text(encoding="utf-8", errors="ignore"), "kilo.jsonc contains gateway URL")
    else:
        hits = scan_for_url([HOME / ".config" / "kilo"])
        check(bool(hits), "kilo config contains gateway URL")

elif TOOL == "cline":
    bases = [APPDATA / "Code" / "User", APPDATA / "Cursor" / "User", HOME / ".cline"]
    hits = scan_for_url(bases)
    check(bool(hits), "Cline config contains gateway URL")
    for h in hits[:3]:
        print("       wrote:", h)

else:
    check(False, f"no verifier implemented for {TOOL}")

print()
if failures:
    print(f"{len(failures)} failures")
    sys.exit(1)
print("ALL PASS")
