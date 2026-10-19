"""Agent CLIs that accept a role prompt file as a command-line argument."""

from ..common import SlpError, atomic_write


def catalog(installation, provider, refresh=False):
    models = provider.get("models", [])
    if not models:
        raise SlpError(f"Configure verified models/efforts in providers/{provider['id']}.toml before enabling it")
    return {"provider": provider["id"], "source": "configured provider catalog", "models": models}


def prepare(installation, provider, role):
    # Validate the catalog/defaults and launcher contract before writing.
    installation.defaults(provider, role, catalog(installation, provider)["models"])
    if not provider.get("prompt_args") or not any("{prompt_file}" in arg for arg in provider["prompt_args"]):
        raise SlpError("prompt-argument adapter requires prompt_args containing {prompt_file}")
    runtime = installation.role_runtime(provider, role)
    prompt = installation.role_prompt(role)
    runtime.mkdir(parents=True, exist_ok=True)
    runtime.chmod(0o700)
    atomic_write(runtime / "role.md", prompt)
    return runtime


def launch_env(installation, provider, role):
    return dict(provider.get("env", {}))


def launch_args(installation, provider, role):
    prompt_file = installation.role_runtime(provider, role) / "role.md"
    model, effort = installation.defaults(provider, role, catalog(installation, provider)["models"])
    args = provider["prompt_args"] + provider.get("model_args", [])
    if effort:
        args += provider.get("effort_args", [])
    return installation.binary(provider) + [arg.replace("{prompt_file}", str(prompt_file)).replace("{model}", model).replace("{effort}", effort or "") for arg in args]
