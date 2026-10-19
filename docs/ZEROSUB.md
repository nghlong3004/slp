# ZeroSub with Codex roles

## Installation status and activation

ZeroSub **1.3.0** is pinned in `config/zerosub.toml`. All three SLP role
providers are configured for account routing. Plugin installation, activation,
and sign-in happen on each daemon host; cloning SLP does not perform them.
See [validation](VALIDATION.md) for the tested host's results.

Run from your chosen repository root in a normal terminal on the daemon host:

```sh
./scripts/setup-zerosub
```

The script checks npm for exactly 1.3.0, reloads the existing daemon rather
than launching a competing instance, installs that version using Paseo's own
installer, checks the installed package version, then writes preferences
through Paseo's plugin settings RPC. A missing setting, rejected schema,
revision conflict, download failure, or version mismatch is surfaced as an
error. It never silently installs 1.2.1.

Successful activation writes `zerosub-installation.json` under SLP's runtime
(default `~/.local/state/slp/runtime/`). If setup
fails, that success marker is not written. `--prepare` is available for local
preparation only and explicitly reports that installation is still pending.

## Routing and role configuration

ZeroSub owns account choice and credentials via `CODEX_HOME`. SLP role provider
entries do not contain `CODEX_HOME`, API keys, or custom endpoints, so they
are eligible for the plugin's subscription-family routing. The launcher also
preserves the incoming account home instead of replacing it.

SLP generates role settings under `~/.local/state/slp/runtime/codex/<role>/`
(or `SLP_RUNTIME_ROOT`), then passes only
the role-specific settings with Codex `-c key=value` overrides. This includes
the role prompt, model/effort defaults, shared model-instruction path, filtered
model catalog, and disabled native multi-agent settings. Account config,
authentication, plugins, skills, and other user settings remain inherited.

The explicit `sqlite_home` setting points to the existing role directory,
retaining its thread indexes. Codex gives this setting precedence over
`CODEX_SQLITE_HOME`. Session files and old databases are not moved or deleted
by this integration. Old `auth.json` links, if present, are retained for
rollback but are not used as the active account home in ZeroSub mode.

The current model catalog is discovered from the canonical account. Accounts
with different plan/model access may not support every saved model choice.
Adding an account does not grant access to models its plan does not supply.

## Accounts and preferences

After activation, open **Accounts (ZeroSub)**, add a ChatGPT account, and
finish sign-in in the provider's own login flow. Set a default account or
choose one from the agent composer's account control. Existing CLI login is
the initial account. Adding multiple accounts requires signing into each;
the installer does not copy or fabricate credentials.

Configured preferences:

| Setting | Value |
| --- | --- |
| Automatic switching | On |
| Continue after switching | On |
| Balance every new agent across accounts | Off; starts with the chosen default |
| Show account control | On |
| Automatically spend banked reset credits | Off |
| Fork to Claude when Codex accounts are exhausted | Off |

When all usable accounts are exhausted, this configuration leaves the agent
stopped instead of buying/using resets or switching to Claude automatically.

## Continuation identities

A Codex account change can require a new continuation agent because threads
contain account-bound reasoning. Treat this as a new Paseo identity with a
handoff, not as proof that callbacks, parentage, or schedules transferred.
Shared role instructions require the [session-recovery procedure](../config/workflow/WORKSPACE_PROTOCOL.md#session-recovery):
check current files, the designated project status source, actual activity,
and existing owners before affected writes or dispatch. A changed-ID Peer
returns its assignment/current ID to Lead and waits for explicit reassignment.
Same-ID resume with confirmed unchanged ownership can continue the original
assignment. Lead reconciles predecessor work and existing Peer callbacks;
no duplicate dispatch is used merely to obtain a notification.

Supervisor reconciles old heartbeat registrations in private state before
starting another intervention loop. Matching names do not deduplicate across
agent IDs. Retirement uses the old owning session or an authorized host
operator; if that cannot be confirmed, the new session remains an observer
and reports the registration gap. Current-session wake-up coverage must be
verified separately. SLP does not automatically migrate these registrations.

This setup does not modify third-party continuation code or claim seamless
transfer of the entire SLP coordination graph. A real multi-account failover
must be checked after sign-in: confirm the account control, continuation role,
model/effort, and current Lead/Peer/monitoring relationships.

## Verification completed locally

The test suite covers inherited account A/B homes across all three roles,
role overrides, unchanged account credentials, preservation of legacy auth and
SQLite files, routing eligibility, preparation without a false installation
claim, and settings RPC revision/schema behavior.

The actual installed Paseo Codex adapter was also run with two temporary
account-home fixtures. Codex loaded the selected fixture settings while
retaining the Lead prompt, role defaults, disabled native agents, and legacy
role SQLite location. No credentials were created in those fixtures and no
model inference was started. These fixtures verify launch/config compatibility.
The host installer separately confirmed the running ZeroSub 1.3.0 plugin and
saved preferences. Live switching between two signed-in accounts has not been
tested.

Useful host checks:

```sh
paseo plugin ls zerosub --json
paseo plugin logs zerosub
paseo provider diagnostic slp-lead --json
```

To restore isolated role homes, set `account_routing="isolated"` in
`config/providers/codex.toml`, then run `slp paseo sync --reload`. This restores
the previous role-home launch behavior without deleting any account data.

References: [ZeroSub](https://github.com/kapybara-org/zerosub),
[provider-family routing](https://github.com/kapybara-org/zerosub/blob/main/server/families.ts),
[Codex environment variables](https://learn.chatgpt.com/docs/config-file/environment-variables),
[Codex CLI overrides](https://learn.chatgpt.com/docs/cli/reference).
