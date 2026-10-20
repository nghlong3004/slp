# Architecture

SLP uses Ports and Adapters with configuration as data. The core owns roles,
profile generation, paths, and CLI dispatch. Adapters translate these into
each agent CLI's settings and launch flags.

The adapter port has four functions: `catalog`, `prepare`, `launch_env`, and
`launch_args`. Adapters are small modules selected by an explicit registry;
there is no inheritance hierarchy or plugin discovery framework. CLIs with a
prompt-file flag use the existing `prompt-argument` adapter through provider
TOML. A new protocol or configuration mechanism needs its own adapter.

Role authority and workflow live in Markdown. Provider identity, CLI paths,
model settings, and role tool policies live in TOML. Paseo JSON is generated
from these sources while preserving settings and profiles outside SLP-owned
IDs. Model names and effort IDs come from the installed CLI's catalog.

Source can be checked out anywhere, with any checkout directory name. The
installer and CLI discover the source root from their own files; local
generated paths refer to that chosen checkout. Config links use `XDG_CONFIG_HOME`, while persistent runtime,
snapshots and backups default to `XDG_STATE_HOME/slp` or `~/.local/state/slp`.
`SLP_RUNTIME_ROOT` overrides the runtime location. State is not placed in the
repository or a temporary/cache directory. Source paths in launchers and
Paseo definitions are generated from the actual installation root.

The Codex adapter supports isolated role homes and externally routed account
homes. In ZeroSub mode account environment is preserved; role settings travel
as CLI overrides. Existing SQLite state remains located by an explicit Codex
configuration setting. Plugin install/preferences orchestration is separate
from the four-function provider adapter port.

Generated Codex TOML is serialized from parsed data; multiline strings,
quoted paths, arrays, and nested tables are preserved semantically. Runtime
config files are disposable; auth, sessions, databases, and notebooks are not.
Migration renames existing homes and keeps compatibility links.

Native subagent hints and Ultra effort are excluded from SLP Codex homes.
The catalog describes Ultra as automatic delegation; SLP project delegation
uses Paseo. Saved profiles include each role's default and explicit per-role
model/effort presets, validated against that provider's catalog. Optional
global effort shortcuts remain supported; the full model picker is retained.

Tool policies limit the catalog presented to a session. Role prompts define
coordination authority. Filesystem permissions remain with the agent's own
permission mode and host policy.
