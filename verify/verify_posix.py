"""Assert the config files zhengmi-setup.sh writes on Linux/macOS."""

from __future__ import annotations

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

# 脚本退出码由运行步骤写到 ~/zs.exit（没有该文件时视为 0，兼容旧的直接执行方式）
EXIT_FILE = HOME / "zs.exit"
EXIT_CODE = int(EXIT_FILE.read_text().strip() or "0") if EXIT_FILE.exists() else 0
HTTPS_OR_LOOPBACK = BASE_URL.startswith("https://") or BASE_URL.startswith(("http://127.0.0.1", "http://localhost"))

if TOOL == "claude-desktop":
    # Claude Desktop 只接受 https（http 仅限回环），脚本对不合格地址必须在写任何文件前退出 1。
    roots = [HOME / "Library" / "Application Support" / "Claude-3p", HOME / ".config" / "Claude-3p",
             HOME / "Library" / "Application Support" / "Claude", HOME / ".config" / "Claude"]
    written = [p for r in roots if r.exists() for p in r.rglob("*.json")]
    if not HTTPS_OR_LOOPBACK:
        check(EXIT_CODE == 1, f"http 网关地址被明确拒绝（退出码 {EXIT_CODE}）")
        check(not written, "拒绝时不写任何 Claude Desktop 文件")
    else:
        check(EXIT_CODE == 0, f"脚本成功（退出码 {EXIT_CODE}）")
        hits = [p for p in written if p.parent.name == "configLibrary" and BASE_URL in p.read_text(encoding="utf-8", errors="ignore")]
        check(bool(hits), "configLibrary 里的配置含网关地址")
        dev = [p for p in written if p.name == "developer_settings.json" and load_json(p).get("allowDevTools") is True]
        check(len(dev) == 2, "Claude 与 Claude-3p 两个目录都开启了开发者模式")
elif TOOL == "cline":
    check(EXIT_CODE == 0, f"脚本成功（退出码 {EXIT_CODE}）")
    state = HOME / ".cline" / "data" / "globalState.json"
    secrets = HOME / ".cline" / "data" / "secrets.json"
    if state.exists():
        data = load_json(state)
        check(data.get("openAiBaseUrl") == BASE_URL + "/v1", "Cline CLI globalState.openAiBaseUrl 指向网关 /v1")
        check(data.get("apiProvider") == "openai", "Cline CLI apiProvider = openai")
        check(secrets.exists() and load_json(secrets).get("openAiApiKey") == API_KEY, "Cline CLI secrets.openAiApiKey 正确")
    else:
        check(True, "未预置 Cline CLI 状态，脚本只打印扩展的手动步骤")
    # 扩展没有 settings.json 配置项：任何 cline.* 键都不得再写进编辑器设置
    polluted = []
    for base in (HOME / ".config", HOME / "Library" / "Application Support"):
        if base.exists():
            polluted += [p for p in base.rglob("settings.json") if '"cline.' in p.read_text(encoding="utf-8", errors="ignore")]
    check(not polluted, "没有把已失效的 cline.* 键写进编辑器 settings.json")
else:
    check(EXIT_CODE == 0, f"脚本成功（退出码 {EXIT_CODE}）")

if TOOL == "claude":
    f = HOME / ".claude" / "settings.json"
    check(f.exists(), f"{f} 存在")
    if f.exists():
        env = load_json(f).get("env", {})
        check(env.get("ANTHROPIC_BASE_URL") == BASE_URL, "ANTHROPIC_BASE_URL 正确")
        check(env.get("ANTHROPIC_AUTH_TOKEN") == API_KEY, "ANTHROPIC_AUTH_TOKEN 正确")
    onboarding = HOME / ".claude.json"
    check(onboarding.exists(), f"{onboarding} 存在")
    if onboarding.exists():
        check(load_json(onboarding).get("hasCompletedOnboarding") is True, "hasCompletedOnboarding 已置 true（跳过登录选择）")

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
    main_cfg = HOME / ".openclaw" / "openclaw.json"
    found = [main_cfg] if main_cfg.exists() else []
    check(bool(found), "openclaw.json 已写入")
    # agents/main/agent/models.json 由网关生成，脚本不再直接写它
    check(not (HOME / ".openclaw" / "agents" / "main" / "agent" / "models.json").exists(), "没有直接写 agents/main/agent/models.json")
    if main_cfg.exists():
        primary = dig(load_json(main_cfg), "agents", "defaults", "model", "primary")
        check(isinstance(primary, str) and primary.startswith("zhengmi-"), "agents.defaults.model.primary 指向 zhengmi")
    for c in found:
        check(BASE_URL in c.read_text(encoding="utf-8", errors="ignore"), f"{c.name} 含网关地址")

elif TOOL == "kilo":
    f = HOME / ".config" / "kilo" / "kilo.jsonc"
    check(f.exists(), f"{f} 存在")
    if f.exists():
        text = f.read_text(encoding="utf-8", errors="ignore")
        check(BASE_URL in text, "kilo.jsonc 含网关地址")
        check(API_KEY in text, "kilo.jsonc 含密钥")

elif TOOL in ("claude-desktop", "cline"):
    pass  # 上面已按退出码校验

elif TOOL == "codebuddy":
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
