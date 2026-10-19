# Adding a provider

Role Markdown and the workspace contract stay unchanged when adding an agent
CLI. Select an adapter that can load those instructions into the actual CLI.

## CLI with a prompt-file argument

The disabled `config/providers/claude.toml` uses `prompt-argument`. Its command
prefix appends a generated `role.md` with Claude's documented
`--append-system-prompt-file` flag. It retains Claude's normal configuration,
authentication, and session home; Codex TOML/auth are never reused for Claude.

After installing/authenticating the CLI, discover the actual models and
thinking IDs from Paseo:

```sh
paseo provider diagnostic claude --json
paseo provider models claude --json
```

Replace `models = []` in the provider file with verified metadata, for example
using this structure (the model and effort strings below are placeholders):

```toml
[[models]]
id = "verified-model-id"
label = "Model display name"
default_effort = "verified-effort-id"

[[models.efforts]]
id = "verified-effort-id"
label = "Effort display name"
```

Set `enabled = true`, then run `slp paseo sync --reload`. Optional top-level
`default_model`/`default_effort` choose defaults for this provider; otherwise
the first configured model and its default effort are used. Saved role
defaults in `slp.toml` apply to their selected provider only.

The generic launcher supports `prompt_args`, `model_args`, and `effort_args`
with `{prompt_file}`, `{model}`, and `{effort}` placeholders. Final arguments
from Paseo or a user follow these defaults. Each provider gets its own
executable launcher, so even an argv[0]-only version probe reaches the correct
CLI. Its model list and supported modes must be tested against the installed
CLI/Paseo adapter before relying on it for project work.

Namespaced internal IDs default to `slp-<provider>-<role>`. They can be
overridden by `[provider_ids]`. Visible provider labels remain Supervisor,
Lead, and Peer; profile names include the actual model and effort.

## Other agent protocols

An ACP executable must actually speak ACP; pointing a Codex command at it
does not translate the protocol. If it accepts a prompt-file argument, the
generic adapter can supply that argument with `extends = "acp"`. If it loads
instructions through settings, an SDK, or a different transport, implement a
small adapter exposing `catalog`, `prepare`, `launch_env`, and `launch_args`,
then add it to `adapters/__init__.py`.

Do not enable a provider whose role prompt cannot be loaded. Do not copy
credentials or permission settings between unrelated CLIs. Add a fixture test
showing the actual launch arguments and prompt path, then test the installed
provider through Paseo. The current offline tests include a second fake CLI
provider to verify that the core is independent of Codex.

Reference: [Claude CLI flags](https://code.claude.com/docs/en/cli-reference),
[Paseo custom providers](https://paseo.sh/docs/custom-providers).
