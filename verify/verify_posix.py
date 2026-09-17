"""Assert the config files zhengmi-setup.sh writes on Linux/macOS."""

import json
import os
import pathlib
import sys

HOME = pathlib.Path(os.environ["HOME"])
TOOL = os.environ["TOOL"]
BASE_URL = os.environ.get("ZHENGMI_BASE_URL", "https://ci.example.com")
API_KEY = os.environ.get("ZHENGMI_API_KEY", "sk-ci-test-key-000000000000")

failures = []


def check(cond, msg):
    print(("  OK   " if cond else "  FAIL ") + msg)
    if not cond:
        failures.append(msg)


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        check(False, f"{path} 不是合法 JSON: {exc}")
        return {}


def dig(data, *keys):
    cur = data
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur


print(f"== {TOOL} on {sys.platform} ==")

if TOOL == "claude":
    f = HOME / ".claude" / "settings.json"
    check(f.exists(), f"{f} 存在")
    if f.exists():
        env = load_json(f).get("env", {})
        check(env.get("ANTHROPIC_BASE_URL") == BASE_URL, "ANTHROPIC_BASE_URL 正确")
        check(env.get("ANTHROPIC_AUTH_TOKEN") == API_KEY, "ANTHROPIC_AUTH_TOKEN 正确")

elif TOOL == "codex":
    d = HOME / ".codex"
    cfg, auth = d / "config.toml", d / "auth.json"
    check(cfg.exists(), f"{cfg} 存在")
    check(auth.exists(), f"{auth} 存在")
    if auth.exists():
        check(load_json(auth).get("OPENAI_API_KEY") == API_KEY, "auth.json 密钥正确")
    if cfg.exists():
        text = cfg.read_text(encoding="utf-8")
        check(BASE_URL in text, "config.toml 含网关地址")

elif TOOL == "gemini":
    d = HOME / ".gemini"
    envf, st = d / ".env", d / "settings.json"
    check(envf.exists(), f"{envf} 存在")
    check(st.exists(), f"{st} 存在")
    if envf.exists():
        text = envf.read_text(encoding="utf-8")
        check(BASE_URL in text, ".env 含网关地址")
        check(API_KEY in text, ".env 含密钥")
    if st.exists():
        check(dig(load_json(st), "security", "auth", "selectedType") == "gemini-api-key",
              "security.auth.selectedType = gemini-api-key")

elif TOOL == "opencode":
    f = HOME / ".config" / "opencode" / "opencode.json"
    check(f.exists(), f"{f} 存在")
    if f.exists():
        text = json.dumps(load_json(f))
        check(BASE_URL in text, "opencode.json 含网关地址")
        check(API_KEY in text, "opencode.json 含密钥")

elif TOOL == "hermes":
    for base in (HOME / ".hermes", HOME / "Library" / "Application Support" / "hermes"):
        if base.exists():
            check(True, f"{base} 存在")
            blob = " ".join(
                p.read_text(encoding="utf-8", errors="ignore")
                for p in base.rglob("*") if p.is_file() and p.stat().st_size < 1_000_000
            )
            check(BASE_URL in blob, f"{base} 下配置含网关地址")
            break
    else:
        check(False, "hermes 配置目录未创建")

elif TOOL == "pi":
    f = HOME / ".pi" / "agent" / "models.json"
    check(f.exists(), f"{f} 存在")
    if f.exists():
        check(BASE_URL in json.dumps(load_json(f)), "models.json 含网关地址")

elif TOOL == "openclaw":
    candidates = [HOME / ".openclaw" / "openclaw.json",
                  HOME / ".openclaw" / "agents" / "main" / "agent" / "models.json"]
    found = [c for c in candidates if c.exists()]
    check(bool(found), "openclaw 配置文件已写入")
    for c in found:
        check(BASE_URL in c.read_text(encoding="utf-8", errors="ignore"), f"{c.name} 含网关地址")

elif TOOL == "kilo":
    f = HOME / ".config" / "kilo" / "kilo.jsonc"
    check(f.exists(), f"{f} 存在")
    if f.exists():
        text = f.read_text(encoding="utf-8", errors="ignore")
        check(BASE_URL in text, "kilo.jsonc 含网关地址")
        check(API_KEY in text, "kilo.jsonc 含密钥")

elif TOOL == "claude-desktop":
    # Claude Desktop 是 GUI 应用；Linux 上没有官方版本，脚本只给出下载指引。
    if sys.platform == "darwin":
        roots = [HOME / "Library" / "Application Support" / "Claude-3p", HOME / ".config" / "Claude-3p"]
        hits = [p for r in roots if r.exists() for p in r.rglob("*.json") if BASE_URL in p.read_text(encoding="utf-8", errors="ignore")]
        check(bool(hits), "Claude Desktop 配置含网关地址（macOS）")
        for h in hits[:3]:
            print("       写入:", h)
    else:
        check(True, "Claude Desktop 在 Linux 无官方版本，跳过配置校验")

elif TOOL in ("codebuddy", "cline"):
    hits = []
    for base in (HOME / ".codebuddy", HOME / ".kilo", HOME / ".cline",
                 HOME / ".config", HOME / "Library" / "Application Support"):
        if base.exists():
            for p in base.rglob("*"):
                if p.is_file() and p.suffix in {".json", ".toml", ".env"} and p.stat().st_size < 1_000_000:
                    try:
                        if BASE_URL in p.read_text(encoding="utf-8", errors="ignore"):
                            hits.append(p)
                    except OSError:
                        pass
    check(bool(hits), f"{TOOL} 配置含网关地址")
    for h in hits[:3]:
        print("       写入:", h)

else:
    check(False, f"未实现的校验: {TOOL}")

print()
if failures:
    print(f"共 {len(failures)} 项失败")
    sys.exit(1)
print("全部通过")
