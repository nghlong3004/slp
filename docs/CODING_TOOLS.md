# RTK and Ponytail in SLP

Lead and implementation/refactoring Peers use Ponytail `full` and selective
RTK shell calls. Read-only reviews keep their original criteria. Supervisor
retains its observation and recovery responsibilities. Neither tool expands
scope, permissions, delegation, or acceptance authority.

## Installation and activation

The repository includes an unmodified Ponytail skill, its MIT license, and
[pinned upstream provenance](../config/skills/ponytail/UPSTREAM.md). Run
`./scripts/install` to expose it at `~/.agents/skills/ponytail`. The installer
preserves an existing matching link, and refuses an unrelated skill directory
or link before changing the installation. There are no Ponytail lifecycle
hooks or additional audit/review skills.

RTK is installed on each daemon host. The tested Linux x86_64 release is
[RTK OSS 1.0.1](https://github.com/rtk-ai/rtk/releases/tag/v1.0.1), asset
`rtk-oss-x86_64-unknown-linux-musl.tar.gz`. Its SHA-256 from the release's
`checksums.txt` is:

```text
a44e8ffc43981100b4ddf1710399a1649a6c874591aa6d0c0727fe6cbd983c41
```

For this platform, download that archive, verify it against the checksum,
extract it, and install its `rtk` executable into `~/.local/bin/rtk`. Other
platforms need their own release asset and checksum. Keep `~/.local/bin` on
the daemon's PATH; the role guidance also provides the explicit fallback path.
`rtk --version` and `rtk --help` verify the binary is executable.

After installing, run:

```sh
./scripts/install
slp paseo sync --reload
paseo provider ls
slp doctor
```

Start new Lead/Peer sessions to load the updated role prompt. In an already
running session, explicitly ask it to read the current coding-tool guidance;
daemon reload alone does not replace instructions in an active turn. Codex's
skill discovery can refresh on the next turn, independently of role-prompt
loading. There is no new MCP server, provider, API proxy, or model router.

## How agents use them

The role prompt points to
[`config/workflow/CODING_TOOLS.md`](../config/workflow/CODING_TOOLS.md). That
document asks the agent to read Ponytail's full skill for relevant tasks and
choose explicit RTK calls for repetitive output. RTK's native command-rewrite
hooks are not installed. Calling `rtk` is a model decision, not a guarantee
that every eligible command is compressed.

Use `rtk git status`, `rtk pytest`, or another supported wrapper when useful.
Use original commands to inspect exact files, full diffs, logs, tracebacks,
or structured data consumed by another command. For example, a full patch
review can still use `git diff` even if a quick progress check uses RTK.

Ponytail is discovered from the shared user skill directory, and role
instructions reference SLP's source config. Both paths stay independent of
ZeroSub's selected account home. Existing auth, SQLite state, model defaults,
profiles, and role tool restrictions remain in their existing configuration.

## Verification on 2026-10-20

- 25 offline integration tests pass, including a private-skill collision and
  installation from a checkout with spaces in its path.
- RTK OSS 1.0.1 passed release-checksum verification. Smoke checks covered
  compact Git status, a successful test command, and a failing command whose
  exit code 7 was preserved. Telemetry was checked and is disabled.
- The installed Paseo Codex transport was used to start all three role
  launchers against two credential-free account-home fixtures. `config/read`
  confirmed selected-home settings and role-specific guidance; `skills/list`
  found the same Ponytail skill in both accounts.
- The live Paseo daemon reloaded successfully. All three SLP providers report
  available, with 42 profiles retained at that point. `slp doctor` passes.
  The later reduction to five model profiles is recorded in
  [validation](VALIDATION.md#five-model-profiles--2026-10-20).

No model inference or live account failover was run for these checks. They
verify installation, discovery, configuration, launch compatibility and RTK's
tested exit behavior; they do not measure savings or prove model adherence.
