"""Codex TOML/home/catalog translation. Role policy stays in config/roles."""

import copy
import json
import os
from pathlib import Path
import subprocess
from ..common import SlpError, atomic_write, check_link, dump_toml, read_toml, shared_link, toml_value


def account_routing(provider):
    mode = provider.get("account_routing", "isolated")
    if mode not in ("isolated", "zerosub"):
        raise SlpError(f"Unsupported Codex account_routing: {mode}")
    return mode


def canonical_home(provider):
    return Path(os.environ.get(provider.get("canonical_home_env", ""), provider["canonical_home"])).expanduser().resolve()


def raw_catalog(installation, provider, refresh=False):
    fixture = os.environ.get("SLP_MODEL_CATALOG")
    if fixture:
        return json.loads(Path(fixture).expanduser().read_text()), "fixture"
    home = canonical_home(provider)
    if refresh:
        result = subprocess.run(installation.binary(provider) + ["debug", "models"],
                                env={**os.environ, "CODEX_HOME": str(home)},
                                capture_output=True, text=True, check=True, timeout=30)
        return json.loads(result.stdout), "codex debug models"
    cache = home / "models_cache.json"
    if cache.is_file():
        data = json.loads(cache.read_text())
        if isinstance(data.get("models"), list) and data["models"]:
            return data, f"{cache} (fetched {data.get('fetched_at', 'unknown')})"
    result = subprocess.run(installation.binary(provider) + ["debug", "models", "--bundled"],
                            env={**os.environ, "CODEX_HOME": str(home)},
                            capture_output=True, text=True, check=True, timeout=30)
    return json.loads(result.stdout), "bundled CLI catalog; account availability unverified"


def catalog(installation, provider, refresh=False):
    raw, source = raw_catalog(installation, provider, refresh)
    excluded = set(provider.get("excluded_efforts", []))
    models = []
    for model in raw.get("models", []):
        if model.get("visibility") != "list":
            continue
        efforts = [{"id": item["effort"], "label": item["effort"], "description": item.get("description", "")}
                   for item in model.get("supported_reasoning_levels", []) if item["effort"] not in excluded]
        default = model.get("default_reasoning_level")
        models.append({"id": model["slug"], "label": model.get("display_name", model["slug"]),
                       "description": model.get("description", ""), "efforts": efforts,
                       "default_effort": default if default not in excluded else efforts[0]["id"]})
    if not models:
        raise SlpError("Codex catalog has no visible models")
    return {"provider": provider["id"], "source": source, "excluded_efforts": sorted(excluded), "models": models}


def prepare(installation, provider, role):
    routing = account_routing(provider)
    home = canonical_home(provider)
    base = read_toml(home / "config.toml") if (home / "config.toml").exists() else {}
    available = catalog(installation, provider)
    model_id, effort = installation.defaults(provider, role, available["models"])
    prompt = installation.role_prompt(role)
    runtime = installation.role_runtime(provider, role)
    links = []
    # In ZeroSub mode, role directories store settings and existing SQLite
    # state, never the active account's credentials. Leave old auth links alone.
    for name in (("auth.json", "AGENTS.md", "skills", "plugins", "hooks.json") if routing == "isolated" else ()):
        target = home / name
        if target.is_symlink() and not target.exists():
            raise SlpError(f"Dangling canonical link: {target}")
        if target.exists():
            check_link(runtime / name, target)
            links.append((runtime / name, target))
    instructions = (installation.config / provider["model_instructions"]).resolve()
    check_link(runtime / "model-instructions.md", instructions)
    links.append((runtime / "model-instructions.md", instructions))
    raw, _ = raw_catalog(installation, provider)
    raw = {"models": copy.deepcopy(raw["models"])}
    excluded = set(provider.get("excluded_efforts", []))
    for model in raw["models"]:
        model["multi_agent_version"] = None
        model["supported_reasoning_levels"] = [e for e in model.get("supported_reasoning_levels", []) if e["effort"] not in excluded]
    merged = copy.deepcopy(base)
    merged.update(model=model_id, model_reasoning_effort=effort,
                  developer_instructions="\n\n".join(filter(None, [base.get("developer_instructions"), prompt])),
                  model_instructions_file=str(runtime / "model-instructions.md"),
                  model_catalog_json=str(runtime / "model-catalog.no-native-agents.json"))
    merged.setdefault("agents", {})["enabled"] = False
    features = merged.setdefault("features", {})
    features["multi_agent"] = False
    if isinstance(features.get("multi_agent_v2"), dict):
        features["multi_agent_v2"]["enabled"] = False
    else:
        features["multi_agent_v2"] = False
    overrides = {key: merged[key] for key in (
        "model", "model_reasoning_effort", "developer_instructions",
        "model_instructions_file", "model_catalog_json",
    )}
    overrides.update({"agents.enabled": False, "features.multi_agent": False})
    v2_key = "features.multi_agent_v2.enabled" if isinstance(features["multi_agent_v2"], dict) else "features.multi_agent_v2"
    overrides[v2_key] = False
    if routing == "zerosub":
        # Keep legacy thread indexes readable without overriding account auth.
        # sqlite_home takes precedence over CODEX_SQLITE_HOME by Codex design.
        overrides["sqlite_home"] = str(runtime)
        overrides["log_dir"] = str(runtime / "log")
    rendered = dump_toml(merged)
    runtime.mkdir(parents=True, exist_ok=True)
    installation.runtime.chmod(0o700)
    runtime.parent.chmod(0o700)
    runtime.chmod(0o700)
    atomic_write(runtime / "model-catalog.no-native-agents.json", json.dumps(raw) + "\n")
    atomic_write(runtime / "config.toml", rendered)
    atomic_write(runtime / "launch-overrides.json", json.dumps(overrides, ensure_ascii=False) + "\n")
    atomic_write(runtime / "role.md", prompt)
    for path, target in links:
        shared_link(path, target)
    return runtime


def launch_env(installation, provider, role):
    env = {}
    if account_routing(provider) == "isolated":
        env["CODEX_HOME"] = str(installation.role_runtime(provider, role))
    if provider.get("canonical_home_env"):
        env[provider["canonical_home_env"]] = str(canonical_home(provider))
    return env


def launch_args(installation, provider, role):
    command = installation.binary(provider)
    if account_routing(provider) == "zerosub":
        path = installation.role_runtime(provider, role) / "launch-overrides.json"
        for key, value in json.loads(path.read_text()).items():
            command.extend(["-c", f"{key}={toml_value(value)}"])
    return command
