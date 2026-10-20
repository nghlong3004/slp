"""Translate role/provider data into Paseo settings; preserve unrelated IDs."""

import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from .adapters import get_adapter
from .common import SlpError, atomic_write, provider_id, state_home

EFFORT_LABELS = {"low": "Low", "medium": "Medium", "high": "High", "xhigh": "Extra High", "max": "Max"}


def home():
    return Path(os.environ.get("PASEO_HOME", Path.home() / ".paseo")).expanduser().resolve()


def build(installation, existing, previous=None):
    previous = previous or {"providers": [], "profiles": []}
    result = copy.deepcopy(existing)
    result.setdefault("version", 1)
    daemon = result.setdefault("daemon", {})
    daemon.setdefault("mcp", {}).update(enabled=True, injectIntoAgents=True)
    providers = result.setdefault("agents", {}).setdefault("providers", {})
    old_profiles = daemon.get("agentProfiles", [])
    owned_providers = set(previous["providers"])
    owned_profiles = set(previous["profiles"])
    # Adopt only the IDs from the previous three-role installation.
    owned_providers.update(f"slp-{role}" for role in installation.settings["roles"])
    owned_profiles.update(f"slp-{role}" for role in installation.settings["roles"])
    generated, profiles, reports = {}, [], []
    for provider in installation.providers():
        adapter = get_adapter(provider)
        report = adapter.catalog(installation, provider)
        reports.append(report)
        command = installation.binary(provider)
        for role in installation.settings["roles"]:
            role_config = installation.role(role)
            pid = provider_id(provider, role)
            env = {**provider.get("env", {}), **adapter.launch_env(installation, provider, role),
                   "SLP_ROOT": str(installation.root), "SLP_CONFIG_HOME": str(installation.config),
                   "SLP_RUNTIME_ROOT": str(installation.runtime)}
            if provider.get("binary_env"):
                env[provider["binary_env"]] = command[0]
            definition = {
                "extends": provider["extends"], "label": role.title(),
                "command": [str(installation.launcher(provider)), role],
                "env": env,
                "models": [{"id": model["id"], "label": model["label"],
                            "thinkingOptions": [{"id": effort["id"], "label": EFFORT_LABELS.get(effort["id"], effort["label"]),
                                                 "isDefault": effort["id"] == model.get("default_effort")}
                                                for effort in model.get("efforts", [])]}
                           for model in report["models"]],
            }
            if role_config.get("disabled_tools"):
                definition["paseoTools"] = {"disabledTools": role_config["disabled_tools"]}
            generated[pid] = definition
            default_model, default_effort = installation.defaults(provider, role, report["models"])
            for item in definition["models"]:
                item["isDefault"] = item["id"] == default_model
                if item["isDefault"] and default_effort:
                    for option in item["thinkingOptions"]:
                        option["isDefault"] = option["id"] == default_effort
            pairs = [(default_model, default_effort)]
            pair_notes = {}
            if role_config.get("provider") == provider["id"]:
                for preset in role_config.get("profiles", []):
                    model_id = preset.get("model")
                    model = next((m for m in report["models"] if m["id"] == model_id), None)
                    if model is None:
                        raise SlpError(f"Profile model is absent from {provider['id']} catalog: {model_id}")
                    effort = preset.get("effort", model.get("default_effort"))
                    if effort and effort not in [e["id"] for e in model.get("efforts", [])]:
                        raise SlpError(f"Unsupported profile effort {effort} for {model_id}")
                    pair = (model_id, effort)
                    if pair in pairs:
                        raise SlpError(f"Duplicate profile for {provider['id']}/{role}: {model_id}/{effort}")
                    pairs.append(pair)
                    pair_notes[pair] = preset.get("notes", role_config["notes"])
            for model in report["models"]:
                supported = {effort["id"] for effort in model.get("efforts", [])}
                for effort in installation.settings.get("profiles", {}).get("efforts", []):
                    if effort in supported and (model["id"], effort) not in pairs:
                        pairs.append((model["id"], effort))
            for index, (model_id, effort) in enumerate(pairs):
                model = next(model for model in report["models"] if model["id"] == model_id)
                profile_id = (f"slp-{role}" if role_config.get("provider") == provider["id"] else f"{pid}-default") if index == 0 else f"{pid}-{model_id}-{effort}"
                profile = {"id": profile_id,
                           "name": f"{role.title()} · {model['label']} · {EFFORT_LABELS.get(effort, effort or 'Default')}",
                           "provider": pid, "model": model_id,
                           "notes": pair_notes.get((model_id, effort), role_config["notes"])}
                if effort:
                    profile["thinkingOptionId"] = effort
                profiles.append(profile)
    for pid, definition in generated.items():
        if pid in providers and pid not in owned_providers and providers[pid] != definition:
            raise SlpError(f"Unmanaged Paseo provider would be overwritten: {pid}")
    for profile in profiles:
        old = next((p for p in old_profiles if p["id"] == profile["id"]), None)
        if old and old["id"] not in owned_profiles and old != profile:
            raise SlpError(f"Unmanaged Paseo profile would be overwritten: {old['id']}")
    for pid in owned_providers:
        providers.pop(pid, None)
    providers.update(generated)
    new_ids = {p["id"] for p in profiles}
    daemon["agentProfiles"] = [p for p in old_profiles if p["id"] not in owned_profiles and p["id"] not in new_ids] + profiles
    return result, {"providers": list(generated), "profiles": [p["id"] for p in profiles]}, reports


def validate(config):
    binary = os.environ.get("SLP_PASEO_BIN") or shutil.which("paseo")
    if not binary:
        raise SlpError("paseo is required to validate its configuration before writing")
    with tempfile.TemporaryDirectory(prefix="slp-paseo-validate-") as directory:
        atomic_write(Path(directory) / "config.json", json.dumps(config))
        result = subprocess.run([binary, "daemon", "config", "get", "--home", directory, "--json"],
                                capture_output=True, text=True, timeout=20)
        if result.returncode:
            raise SlpError("Paseo rejected the generated configuration: " + (result.stderr or result.stdout)[:1000])


def sync(installation, reload=False):
    path = home() / "config.json"
    existing = json.loads(path.read_text()) if path.exists() else {"version": 1}
    manifest_path = installation.runtime / "paseo-managed.json"
    previous = json.loads(manifest_path.read_text()) if manifest_path.exists() else None
    config, manifest, reports = build(installation, existing, previous)
    validate(config)
    for provider in installation.providers():
        for role in installation.settings["roles"]:
            get_adapter(provider).prepare(installation, provider, role)
        installation.write_launcher(provider)
    if config != existing:
        if path.exists():
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            atomic_write(state_home() / "backups" / f"paseo-{stamp}.json", path.read_text())
        atomic_write(path, json.dumps(config, indent=2, ensure_ascii=False) + "\n")
    atomic_write(manifest_path, json.dumps(manifest, indent=2) + "\n")
    for report in reports:
        atomic_write(installation.runtime / "catalogs" / f"{report['provider']}.json", json.dumps(report, indent=2) + "\n")
    print(f"Paseo config saved and validated: {len(manifest['providers'])} role providers, {len(manifest['profiles'])} model/effort profiles")
    if reload:
        result = subprocess.run([shutil.which("paseo"), "daemon", "reload", "--home", str(home()), "--json"],
                                capture_output=True, text=True, timeout=20)
        if result.returncode:
            raise SlpError("Configuration saved; daemon reload failed. Run paseo reload in a normal host terminal. " + (result.stderr or result.stdout)[:700])
        print("Paseo daemon reloaded")


def snapshots(installation):
    for provider in installation.providers():
        report = get_adapter(provider).catalog(installation, provider)
        target = installation.runtime.parent / "snapshots" / provider["id"]
        atomic_write(target / "models.json", json.dumps(report, indent=2) + "\n")
        for role in installation.settings["roles"]:
            runtime = installation.role_runtime(provider, role)
            model, effort = installation.defaults(provider, role, report["models"])
            atomic_write(target / f"{role}.json", json.dumps({"role": role, "provider": provider["id"],
                         "model": model, "effort": effort,
                         "links": {p.name: str(p.readlink()).replace(str(Path.home()), "~") for p in runtime.iterdir() if p.is_symlink()}}, indent=2) + "\n")
    print(installation.runtime.parent / "snapshots")
