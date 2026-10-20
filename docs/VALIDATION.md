# Validation — 2026-10-19

Validated against installed **Codex 0.163.0** and **Paseo 0.12.0**.

- 20 offline tests pass: role/home routing, preservation of existing sessions
  and private files, TOML semantics, invalid-input behavior, native-delegation
  exclusions, supported model/effort combinations, preservation of unrelated
  Paseo settings, ownership cleanup, data-only addition of a second fake CLI,
  provider-aware version probing, and repeatable layout migration.
- Candidate Paseo JSON passes the installed daemon configuration schema before
  saving. There are three role providers and 42 saved model/effort profiles.
- All three roles start through the **actual installed Paseo Codex adapter**
  over stdio. `config/read` confirms the role prompt, namespaced home,
  GPT-6.1-Sol / High defaults, and disabled native multi-agent flags.
- `model/list` through those processes returns seven visible models. Each
  offers the configured High and Extra High shortcuts. Native multi-agent
  hints and Ultra are absent from the generated role catalog.
- Repeating sync on the installed configuration leaves its content unchanged.
- Old runtime directories were moved into the Codex namespace with compatible
  symlinks; source configuration and launchers are backed up under
  `~/.local/state/slp/backups/`.

No paid model inference, project delegation, or heartbeat was started during
validation. Claude Code is not installed here; its template is disabled and
only the generic adapter has been exercised with a fake CLI.

The restricted execution environment cannot connect to the host's localhost
daemon. The host setup subsequently reloaded the daemon successfully; visual
confirmation in Paseo remains a host-side check. For future reloads and
provider checks, use a normal terminal:

```sh
paseo reload
paseo provider ls
paseo provider diagnostic slp-lead --json
```

New sessions receive the refreshed prompt and tool catalog.

## ZeroSub integration follow-up

All 20 tests pass. The Codex adapter now supports ZeroSub-owned account homes and separate role
overrides. Additional tests cover account-home preservation, unchanged auth,
legacy SQLite preservation, provider eligibility, install preparation, and
revision-aware preference writes. The actual Paseo adapter was exercised with
two credential-free home fixtures: selected-home settings and role overrides
were both honored.

ZeroSub **1.3.0 is installed and enabled**. The host ran
`./scripts/setup-zerosub` from its checkout successfully on 2026-10-19; Paseo reported
`status: running` and saved preferences through the live schema. Shared-file
checks confirmed the installed package version, success marker, preferences,
and account-routing eligibility of Lead, Supervisor, and Peer. Live switching
between two signed-in accounts has not been tested. See [ZeroSub status](ZEROSUB.md).

## Role contract and tool-policy follow-up

Implemented the agreed four improvements: role-aligned Paseo tool policies,
explicit candidate/write handoff, one designated project work-status source,
and a session-recovery procedure for same-ID resume and changed-ID continuation.
The contract defines default ownership release on candidate submission and
explicit repair/reassignment, preserves independently owned ready work, and
does not require another approval for unchanged same-ID ownership. Project
status keeps public work/ownership evidence; supervision metadata stays private.

The 20 existing offline integration tests pass after the update. Installed
Paseo 0.12 policy evaluation confirms Peer agent/workspace/schedule/heartbeat
restrictions and Supervisor project-execution restrictions while preserving
read tools, Supervisor recovery/own-heartbeat tools, and Lead capabilities.
Generated JSON passes the installed schema; all three generated prompts and
Codex launch overrides match source. Compared with the pre-change config,
only Peer/Supervisor tool policies changed: 42 profiles, models, ZeroSub,
web UI, and unrelated daemon/provider settings were preserved.

The handoff/recovery paths were reviewed against the written contract, not
tested with live multi-agent work or two signed-in Codex accounts. Ownership
is coordinated by prompts and evidence; no lock service or automatic callback
or heartbeat migration was added. No project was dispatched, session killed,
heartbeat created, or model inference started for this validation.

Local configuration and runtimes are saved. The live reload attempt returned
`DAEMON_NOT_RUNNING` from the restricted environment; TCP socket creation here
also fails with `EPERM`. Host-side activation remains unverified for this
update. Run `paseo daemon reload --home "$HOME/.paseo"` from the daemon host's
normal terminal. Already-running sessions need the refreshed role instructions
and tool catalog loaded at a safe session reopen; config reload alone does
not prove that an active turn received new instructions.

## External state and fresh-runtime validation

The checkout location is chosen by each installer; no parent path or folder
name is required. The tested installation's old SLP `.runtime` and generated
`runtime/snapshots` directories were reset and rebuilt fresh. No checkout-local
runtime link was retained. Codex and Paseo/ZeroSub account
directories were not deleted or moved.

Persistent runtime now defaults to `~/.local/state/slp/runtime`, with snapshots
beside it and backups under the same SLP state home. State/config bases honor
absolute XDG overrides; `SLP_RUNTIME_ROOT` still provides an explicit runtime
override. Config/command symlinks, role settings, provider launcher and Paseo
source/config/runtime paths were regenerated for the new layout.

All 23 offline tests pass, including external state defaults, inode-preserving
legacy migration and refusal of conflicting destinations. The installed Paseo
schema accepts three role providers and 42 profiles. A config comparison
confirmed only expected path changes; ZeroSub, web settings, models and tool
policies remained unchanged. A temporary Git index simulated `git add .`:
31 source files, no runtime/snapshots/caches or detected tokens/private keys,
personal absolute paths or emails. No repository was initialized or published.
Live daemon reload remains unverified because the restricted environment
cannot connect; activation must be run from the normal daemon-host terminal.

## Checkout-location independence

All 24 offline tests pass. An additional test copies the real scripts and
configuration into an arbitrarily named checkout under a parent containing
spaces, removes SLP root/config/runtime overrides, and invokes installation
and sync from outside the checkout. It verifies custom XDG config/state
locations, generated local launcher/provider paths, and a launch through that
provider command using the selected account home. Provider inference and
schema CLI are fixture-based for this test; no live model inference is used.
Public setup commands are relative to the checkout and do not prescribe a
machine-specific source location or imply the reader already installed ZeroSub.

## RTK and Ponytail integration — 2026-10-20

Installed RTK OSS 1.0.1 after checking its release SHA-256 and bundled the
unmodified Ponytail skill from a pinned upstream commit with its MIT license.
The installer exposes the skill in the account-independent user skills path,
and refuses an unrelated local skill before any installation changes.
Lead/Peer prompts load the coding-tool guidance; Supervisor's role source
and role permissions are unchanged. RTK calls are selected by the agent;
no global rewrite hook, Ponytail lifecycle hook, or API proxy was installed.

All 25 offline tests pass. RTK smoke checks preserve success and failure exit
codes. The installed Paseo Codex transport confirms role configuration and
Ponytail discovery across all three roles and two credential-free account
homes. Live sync/reload succeeded, repairing stale launcher paths in the
previous daemon configuration. All three SLP providers now report available,
42 profiles remain, and `slp doctor` passes.

No model inference, savings benchmark, or signed-in account failover was run.
See [coding-tool setup and verification](CODING_TOOLS.md).

## Five model profiles — 2026-10-20

The saved SLP profiles were reduced from 42 to five: Lead GPT-6.1-Sol/High,
Supervisor GPT-6.1-Sol/Medium, Peer GPT-6.1-Sol/Medium, light Peer
GPT-6-Luna/Medium, and difficult Peer GPT-6-Sol/High. Explicit per-role
presets are checked against the selected provider's catalog before writes.
The full seven-model catalog and manual thinking choices remain available.

All 28 offline tests pass, covering profile migration, personal-profile
preservation, defaults reaching role launches, invalid presets without writes,
and isolation from another CLI provider. Live sync and daemon reload succeeded;
Paseo's profile API returns the five SLP profiles plus the existing personal
profile. A before/after comparison confirms unrelated Paseo settings were
preserved, and generation from the resulting configuration is stable.

All three SLP providers report available. The installed Paseo Codex transport
reads GPT-6.1-Sol and the intended thinking default for each role from the
actual app-server, with role instructions loaded in credential-free account
homes. `slp doctor` passes. No model inference or account failover was run.
Existing agent sessions were not forcibly switched to new defaults.
