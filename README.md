# Supervisor, Lead, Peer

SLP is a role system for agents coordinated through Paseo. Role and provider
are independent: the same Peer contract can be loaded by Codex or another CLI.
The implementation follows [Ports and Adapters](docs/ARCHITECTURE.md), using
small provider modules and configuration files rather than an inheritance tree.

| Role | Responsibility | Source prompt |
| --- | --- | --- |
| Supervisor | Observe named workspaces, preserve user intent, intervene through Lead, maintain an authorized monitoring wake-up | `config/roles/supervisor.md` |
| Lead | Own technical decisions, delegate bounded work, integrate, verify, and accept candidates | `config/roles/lead.md` |
| Peer | Own one delegated outcome or read-only review, return evidence, and leave acceptance to Lead | `config/roles/peer.md` |

Each prompt explicitly declares `Role: Supervisor.`, `Role: Lead.`, or
`Role: Peer.`. Paseo displays providers as **Supervisor**, **Lead**, **Peer**.
Saved model choices use names such as **Lead · GPT-6.1-Sol · High**.
Display labels do not define authority; the loaded role prompt does.

## Ownership, project status, and recovery

The [shared contract](config/workflow/WORKSPACE_PROTOCOL.md) defines the
coordination rules. Peer tool policies hide agent/workspace management and
schedule/heartbeat mutations. Supervisor retains observation, bounded agent
recovery and its own heartbeat, while project execution and workspace-wide
actions stay with Lead. Tool filtering is an accident-reduction measure, not
a filesystem security boundary; the same actions must not be routed through
a CLI or terminal to bypass the role policy.

When Peer submits a candidate, it stops writers for that scope and releases it
to Lead's control. Lead verifies the actual handoff/stopped writers before
editing or reassigning, and names the scope/base for any repair. Progress,
blockers, timeouts and lifecycle status do not themselves release ownership.
Acceptance identifies an exact candidate; a changed candidate needs a new
decision. Independent, separately owned work can continue.

Lead names one existing tracker or project document as the work-status source
in briefs. If none exists, reuse a suitable document or create
`docs/WORK_STATUS.md` in the target project. Keep outcomes/acceptance, active
Lead/Peer IDs and scope owners, candidates/dispositions, and open decisions
with their return checkpoint. This is a small current record, not another
tracker beside an established one. Private supervision stays outside it.

Resume and ZeroSub continuation reconcile actual files, activity, current
owners and predecessor work before affected writes or dispatch. A new agent
ID does not inherit ownership, parentage, callbacks or heartbeats. Lead
reassigns a changed-ID Peer explicitly; same-ID resume with confirmed ownership
does not need another approval. Supervisor retires predecessor wake-ups through
their owning session or an authorized host operator before starting another
intervention loop. Report unresolved ownership or notification gaps while
continuing read-only investigation and unaffected, independently owned work.
These are prompt-level coordination rules; SLP does not implement a lock
service, a new tracker or automatic callback/heartbeat migration.

## Source layout

Clone or unpack the repository wherever you prefer, with any directory name. Commands
below assume your current directory is the repository root. The installer
and CLI discover that root from their own files; `SLP_ROOT` is an optional
override, not a required setting.

```text
slp/
├── config/
│   ├── slp.toml                   # Role defaults, notes, tool policy, shortcuts
│   ├── shared.md                  # Provider-independent working instructions
│   ├── roles/                     # Supervisor, Lead, Peer
│   ├── workflow/                  # Shared handoff and authority contract
│   └── providers/                 # Provider registry and provider-specific files
├── scripts/
│   ├── slp, slp-sync, install
│   └── lib/slp_core/               # Core plus adapters
├── tests/
└── docs/

~/.config/slp -> <checkout>/config
~/.local/bin/slp -> <checkout>/scripts/slp
~/.local/bin/slp-sync -> <checkout>/scripts/slp-sync

~/.local/state/slp/
├── runtime/
│   ├── codex/{lead,supervisor,peer} # Persistent role state + generated settings
│   ├── codex/launch                # Provider-aware launcher for Paseo probes
│   ├── catalogs/                   # Generated discovery reports
│   └── paseo-managed.json          # IDs owned by the configuration generator
├── snapshots/                      # Generated local summaries
└── backups/                        # Local config/layout backups
```

`<checkout>` is the actual absolute path selected on the installing machine.
Symlinks, launchers and Paseo definitions record it only in local installed
files. Generated files are not part of the source repository.

Runtime and snapshots live outside the checkout. Legacy state paths, Python
caches, local environment files, auth files and databases are also excluded
by `.gitignore`. Credentials
stay in the selected account's home; they are not copied into source config.
In the current ZeroSub mode, role prompts/defaults/native-agent restrictions
are passed as CLI overrides. SLP preserves the `CODEX_HOME` supplied by Paseo
and ZeroSub. Role directories retain their existing SQLite state and notebooks;
explicit `sqlite_home` points there so existing thread indexes remain readable.
The previous `account_routing="isolated"` mode remains available as a fallback.

`XDG_STATE_HOME` and `XDG_CONFIG_HOME` override the default state/config base
directories. `SLP_RUNTIME_ROOT` can explicitly select an isolated runtime.
State is persistent and must not be treated as disposable cache. The installer
can move a legacy checkout-local runtime on the same filesystem and retain
its compatibility links; it refuses conflicting destinations or implicit
cross-filesystem copies. Fresh installs need no checkout-local runtime links.
`config/model-instructions.md` links to the Codex-specific source file.

## Models and reasoning

Five saved profiles are configured in `config/slp.toml`:

| Role / use | Model | Thinking |
| --- | --- | --- |
| Lead default | GPT-6.1-Sol | High |
| Supervisor default | GPT-6.1-Sol | Medium |
| Peer default | GPT-6.1-Sol | Medium |
| Peer light work | GPT-6-Luna | Medium |
| Peer difficult work | GPT-6-Sol | High |

Role defaults and `[[roles.peer.profiles]]` select these shortcuts. Models
and efforts are checked against the local catalog; an unavailable selection
fails explicitly. The full discovered catalog remains available through the
model/thinking picker, subject to account access. `[profiles].efforts = []`
disables automatic shortcuts for every model/role combination; a nonempty
list can still enable them. Sync removes previously managed shortcuts while
preserving personal profiles.

Discovery uses the signed-in canonical Codex home model cache, falling back
to the installed bundled catalog only when there is no cache. Bundled fallback
is identified as account-unverified. The report records its source; model
inference and account quota are not probed by setup checks.

Hidden internal models are excluded from choices. Ultra is excluded because
the catalog describes it as automatic native delegation, while SLP project
delegation uses Paseo. Codex native multi-agent flags and catalog hints are
disabled only in generated role homes. `~/.codex/config.toml` is unchanged.

```sh
slp models
slp models --json
slp models --refresh              # Explicit online refresh; errors are surfaced
```

After refreshing, sync Paseo to update its shortcuts and model choices.

## Use and maintain

```sh
./scripts/install                # Run from your chosen checkout
slp paseo sync --reload           # Validate, regenerate, save, then reload Paseo
slp doctor                       # Local source/runtime/schema checks
slp providers                    # Active and inactive provider adapters
slp sync all                     # Regenerate Codex role homes
slp-sync peer                    # Compatibility command
slp snapshots                    # Sanitized local summaries
python3 -m unittest discover -s tests -v
```

Python 3.11+, Codex, and Paseo are required. The generator validates the
candidate with the **installed Paseo schema before saving**. It preserves
unrelated providers, profiles, authentication, relay settings, and features.
Its ownership manifest removes stale generated entries on later syncs.

In Paseo's profile picker select the role/model/effort choice. Lead reads
`list_profiles` and the notes before selecting a Peer. It applies the saved
provider/model and settings to `create_agent`. There is no hard-coded single
Peer provider in the role prompt.

For a new checkout, install Python 3.11+, Node.js, Paseo and the desired agent
CLI, sign into that CLI, then run `./scripts/install` from the repository.
Ensure `~/.local/bin` is on `PATH`. Use `slp models` to inspect the local model
catalog and adjust `config/slp.toml` if its defaults are unavailable for your
account. Run `slp paseo sync --reload` against the existing daemon. Plugin
download and account login are separate: run `./scripts/setup-zerosub` on the
daemon host when ZeroSub installation is needed. The source repository does
not include your Paseo or Codex account data.

Local commands such as `slp lead` load the same role and defaults. Direct CLI
sessions receive Paseo tools only if those tools are separately configured;
use Paseo-launched sessions for the built-in orchestration workflow.

Environment overrides: `SLP_ROOT`, `SLP_CONFIG_HOME`, `SLP_RUNTIME_ROOT`,
`PASEO_HOME`, `SLP_CANONICAL_HOME`, and `CODEX_BIN`. `SLP_MODEL_CATALOG` is an
offline fixture override. Runtime paths always include provider then role.

## RTK and Ponytail

Lead and implementation Peers load the [coding-tool guidance](config/workflow/CODING_TOOLS.md)
through their role prompt. Ponytail uses `full` within the existing assignment;
RTK is called selectively for verbose shell output. Exact evidence and full
instruction reads use normal commands. Supervisor keeps its observation role.

The pinned Ponytail skill and its MIT license are included under
`config/skills/ponytail/`. `./scripts/install` links it into
`~/.agents/skills/ponytail`, so Codex discovers it even when ZeroSub changes
`CODEX_HOME`. Installation refuses to overwrite an unrelated local skill.
Install RTK separately on each daemon host; the tested binary is RTK OSS
1.0.1 under `~/.local/bin/rtk`. No API proxy or global rewrite hook is enabled.

After role-source changes, run `slp paseo sync --reload` and start a new role
session to load the updated prompt. Paseo needs no additional MCP server or
provider for these tools. Agents choose explicit RTK commands; this is not
automatic interception of every shell call. See [setup and verification](docs/CODING_TOOLS.md).

## Add another provider

Codex is enabled by default. A disabled Claude Code configuration is included;
see the validation report for the providers actually tested.
See [adding a provider](docs/ADDING_PROVIDER.md). A CLI supporting a prompt-file
argument needs a provider TOML file and verified model metadata. A different
protocol/configuration mechanism needs a new small adapter module.

## ZeroSub for Codex

ZeroSub **1.3.0** is the configured installation target, with Codex account
routing enabled for Lead, Supervisor, and Peer. The release is pinned in
`config/zerosub.toml`; setup verifies
that exact npm version and installed package version, with no older fallback.

To install or reinstall, run from the repository root in a normal terminal
on the daemon host:

```sh
./scripts/setup-zerosub
```

This validates/regenerates the three role providers, enables Paseo plugins,
reloads the daemon, installs ZeroSub, and saves preferences using its live
settings schema and revision checks. Automatic switching/continuation are on;
automatic reset-credit spending and cross-provider continuation are off.
Claude stays disabled. Open **Accounts (ZeroSub)** in Paseo to add accounts.

`--prepare` only writes local configuration and desired preferences; it does
not download or activate the plugin. Cloning the repository does not install
the plugin or sign into an account. The validation report records results
from the tested host; installation status is local to each host.

See [ZeroSub integration and verification](docs/ZEROSUB.md), including the
continuation-agent identity behavior that matters to Lead and Supervisor.

## Migration and activation

When an installation migrates existing files, it saves backups and a migration
map under `~/.local/state/slp/backups/` by default. Legacy migration preserves existing state and
compatibility links; normal fresh installs put persistent runtime outside
the checkout from the start.
The installer is covered by an idempotence and session-preservation test.

After changing source configuration, regenerate and reload from a terminal
that can reach the selected daemon:

```sh
slp paseo sync --reload
paseo provider ls
```

If the daemon is actually stopped, start it with `paseo daemon start`.
Provider IDs are preserved, so existing Paseo session identities stay valid.
Start a new session to receive the updated prompt and tool catalog.

References: [Paseo providers](https://paseo.sh/docs/custom-providers),
[profiles](https://paseo.sh/docs/agent-profiles),
[tools](https://paseo.sh/docs/mcp),
[OpenAI configuration](https://learn.chatgpt.com/docs/config-file/config-reference).
