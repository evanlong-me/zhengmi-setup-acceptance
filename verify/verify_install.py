#!/usr/bin/env python3
"""Report whether the installed CLI is reachable after the setup script ran.

Prints one machine-readable line per tool so the CI summary is greppable.
Exit code is 0 when the expected outcome for that tool happened, 1 when the
install should have worked but the command is missing.
"""
import os
import pathlib
import shutil
import subprocess
import sys

TOOL = os.environ["TOOL"]
HOME = pathlib.Path(os.environ.get("USERPROFILE") or os.environ["HOME"])
LOCALAPPDATA = pathlib.Path(os.environ.get("LOCALAPPDATA") or HOME / "AppData" / "Local")

# 工具的安装脚本会往这些目录放可执行文件，会话 PATH 里未必立刻可见
EXTRA_DIRS = [
    HOME / ".local" / "bin",
    HOME / ".opencode" / "bin",
    HOME / ".hermes" / "bin",
    HOME / ".pi" / "bin",
    HOME / ".bun" / "bin",
    HOME / ".npm-global" / "bin",
    LOCALAPPDATA / "Programs" / "claude",
]


def on_path(name: str) -> str | None:
    for d in EXTRA_DIRS:
        cand = d / name
        if cand.exists():
            return str(cand)
    found = shutil.which(name)
    if found:
        return found
    if os.name == "nt":
        # npm 全局 bin 在 %APPDATA%\npm
        appdata = pathlib.Path(os.environ.get("APPDATA", ""))
        for suffix in (".cmd", ".exe", ".ps1", ""):
            cand = appdata / "npm" / f"{name}{suffix}"
            if cand.exists():
                return str(cand)
    return None


def editor_extension_present() -> bool:
    for cli in ("code", "cursor", "code-insiders", "codium", "windsurf"):
        exe = shutil.which(cli)
        if not exe:
            continue
        try:
            out = subprocess.run([exe, "--list-extensions"], capture_output=True, text=True, timeout=120)
        except (OSError, subprocess.SubprocessError):
            continue
        if "saoudrizwan.claude-dev" in (out.stdout or "").lower():
            return True
    return False


if TOOL == "cline":
    ok = editor_extension_present()
    print(f"INSTALL cline {'ok' if ok else 'missing'} (saoudrizwan.claude-dev)")
elif TOOL == "claude-desktop":
    candidates = [
        LOCALAPPDATA / "AnthropicClaude" / "claude.exe",
        LOCALAPPDATA / "Programs" / "Claude" / "Claude.exe",
        pathlib.Path("/Applications/Claude.app"),
        HOME / "Applications" / "Claude.app",
    ]
    hit = next((p for p in candidates if p.exists()), None)
    print(f"INSTALL claude-desktop {'ok' if hit else 'missing'} ({hit or 'no app bundle'})")
    ok = hit is not None
else:
    found = on_path(TOOL)
    print(f"INSTALL {TOOL} {'ok' if found else 'missing'} ({found or 'not on PATH'})")
    ok = found is not None

if not ok:
    print(f"INSTALL FAILED: {TOOL} is not installed")
    sys.exit(1)
print(f"INSTALL OK: {TOOL}")
