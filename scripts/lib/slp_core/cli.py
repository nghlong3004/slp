"""CLI dispatch; provider-specific behavior belongs in adapters."""

import json
import os
from pathlib import Path
import subprocess
import sys
from .adapters import get_adapter
from .common import Installation, SlpError, read_toml, provider_id
from . import paseo


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    provider_name = None
    if args[:1] == ["--provider"]:
        if len(args) < 3:
            raise SlpError("Expected --provider <name> <role|command>")
        provider_name, args = args[1], args[2:]
    installation = Installation.load()
    if not args or args[0] in ("--help", "-h"):
        print("slp [--provider NAME] <lead|supervisor|peer> [agent args...]\n"
              "slp [--provider NAME] models [--refresh] [--json]\n"
              "slp [--provider NAME] sync [ROLE|all]\n"
              "slp providers | doctor | snapshots\n"
              "slp paseo sync [--reload]")
        return
    action, rest = args[0], args[1:]
    if action == "providers":
        for path in sorted((installation.config / "providers").glob("*.toml")):
            provider = read_toml(path)
            print(f"{provider['id']}: {provider['adapter']} ({'enabled' if provider.get('enabled') else 'disabled'})")
        return
    if action == "paseo":
        if not rest or rest[0] != "sync" or any(a != "--reload" for a in rest[1:]):
            raise SlpError("usage: slp paseo sync [--reload]")
        paseo.sync(installation, reload="--reload" in rest)
        return
    if action == "snapshots":
        paseo.snapshots(installation)
        return
    if action == "doctor":
        config = json.loads((paseo.home() / "config.json").read_text())
        paseo.validate(config)
        for provider in installation.providers():
            adapter = get_adapter(provider)
            installation.binary(provider)
            report = adapter.catalog(installation, provider)
            for role in installation.settings["roles"]:
                installation.role_prompt(role)
                installation.defaults(provider, role, report["models"])
                runtime = installation.role_runtime(provider, role)
                if not (runtime / "role.md").is_file():
                    raise SlpError(f"Missing generated runtime: {runtime}")
                if provider_id(provider, role) not in config.get("agents", {}).get("providers", {}):
                    raise SlpError(f"Paseo role provider is not installed: {role}")
            print(f"{provider['id']}: binary, prompts, defaults, runtimes, Paseo schema OK; {len(report['models'])} visible models")
        zerosub_config = installation.config / "zerosub.toml"
        if zerosub_config.is_file():
            requested = read_toml(zerosub_config)["version"]
            plugin = config.get("plugins", {}).get("zerosub")
            if plugin:
                package = Path(plugin["path"]).expanduser() / "package.json"
                actual = json.loads(package.read_text()).get("version")
                if actual != requested:
                    raise SlpError(f"ZeroSub version mismatch: requested {requested}, installed {actual}")
                print(f"ZeroSub {actual}: package present; use paseo plugin ls zerosub to check live status")
            else:
                print(f"ZeroSub {requested}: installation pending; run {installation.root / 'scripts/setup-zerosub'} on the daemon host")
        print("Daemon connectivity and model inference were not probed.")
        return
    role_default = installation.settings["roles"].get(action, {}).get("provider")
    provider = installation.provider(provider_name or role_default)
    adapter = get_adapter(provider)
    if action in ("--version", "-V"):
        command = installation.binary(provider) + ["--version"]
        os.execvpe(command[0], command, os.environ)
    if action == "models":
        if any(arg not in ("--refresh", "--json") for arg in rest):
            raise SlpError("usage: slp [--provider NAME] models [--refresh] [--json]")
        report = adapter.catalog(installation, provider, refresh="--refresh" in rest)
        if "--json" in rest:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print(f"Source: {report['source']}")
            for model in report["models"]:
                print(f"{model['id']}: {', '.join(e['id'] for e in model.get('efforts', []))}")
        return
    if action == "sync":
        roles = list(installation.settings["roles"]) if not rest or rest == ["all"] else rest
        for role in roles:
            print(adapter.prepare(installation, provider, role), file=sys.stderr)
        return
    installation.role(action)
    runtime = adapter.prepare(installation, provider, action)
    env = {**os.environ, **provider.get("env", {}), **adapter.launch_env(installation, provider, action)}
    command = adapter.launch_args(installation, provider, action) + rest
    print(runtime, file=sys.stderr)
    os.execvpe(command[0], command, env)


def run(argv=None):
    try:
        main(argv)
    except (SlpError, OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"slp: {error}", file=sys.stderr)
        raise SystemExit(1) from None
