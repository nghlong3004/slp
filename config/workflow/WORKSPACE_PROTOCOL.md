# Workspace Protocol

This is the small shared contract for a SLP workspace. Human
instructions and owner decisions remain authoritative. A repository may add
project-local detail, but cannot change role authority or safety boundaries.

All roles read this shared contract from the configured SLP config directory
(normally `~/.config/slp/workflow/WORKSPACE_PROTOCOL.md`) before project work, then
read `docs/WORKSPACE_PROTOCOL.md` relative to the actual target project when
present. The local document supplements this contract. Report a missing or
unreadable shared contract rather than silently assuming it was loaded.

## Authority

- Human owns product goals, priority, material cost, external effects, and
  irreversible risk decisions.
- Supervisor observes, faithfully routes Human intent, and performs bounded
  room recovery. It is not another project Lead.
- Lead owns project framing, technical decisions, integration, verification,
  and explicit candidate acceptance.
- Peer owns one bounded outcome delegated by Lead.

## Ownership and dispatch

Coordinate sessions through Paseo tools. Role prompts are shared across agent
CLIs; each configured provider adapter is responsible for loading its role.
Before delegation, inspect saved profiles and their notes, select a Peer
profile appropriate to the task, and apply its provider/model and settings.
Use list_models when the profile has no model. Never infer the role from a
model name or route project work through a plain provider without SLP role
instructions. Native subagent delegation is disabled for SLP Codex homes;
use Paseo for project delegation. Peer returns its handoff through its normal
response channel and does not create or coordinate agents.

Tool availability is not authority. Peer must not manage workspaces, other
agents, or schedules, including heartbeats; do not bypass catalog restrictions
through a CLI, terminal, SDK, or another tool. Project terminals and scripts
are usable only for the assigned work within its granted scope. Supervisor
uses read-only observation and bounded agent recovery, not project execution,
permission approval for other agents, or workspace-wide lifecycle actions.
Tool policies reduce mistakes; they do not replace host permissions or enforce
ownership mechanically.

Project instructions carry outcomes, constraints, and existing authority, not
private conversation transcripts or attribution about who spoke to whom.
Keep briefs self-contained. Preserve the meaning of an authorized decision;
an evidence-based question does not grant new authority or revoke existing
permission. Resolve a coordination question against current ownership and
evidence, then continue ready work without creating another approval gate.

- Give every moving write scope one owner. Run writable Peers in parallel
  only with verified, accepted inputs and separate write scopes.
- Agree on shared contracts before dispatch. Sequence changes to shared files
  or interfaces; use separate branches or worktrees when needed. Do not start
  blocked work merely to increase parallel activity. Continue each ready
  branch without waiting for unrelated assignments.
- A Peer must notify Lead before changing a shared contract or writing outside
  its owned scope; it must not expand ownership or coordinate other Peers.
- A Lead brief states the observable outcome, dependencies, write scope,
  relevant contract or invariants, acceptance evidence, and when to reopen the
  decision. Implementation file lists remain provisional.
- A writable Peer returns an immutable candidate or deterministic snapshot,
  original base, complete changed paths, verification, and residual risk.
- Preserve unrelated work and existing private notebooks, runtime/session
  state. The setup must not silently take
  ownership of them.

### Write handoff

A dispatch grants the named Peer the stated write scope; Lead keeps technical
and coordination responsibility but does not concurrently write that scope.
Intermediate progress or a request for a decision does not release ownership.
A blocked Peer states whether it has paused writes; Lead must reconcile a
paused or unresponsive owner before reassigning. Silence, an elapsed timeout,
or a lifecycle status alone does not release a scope.

Submitting a candidate for review ends that Peer's write assignment for the
submitted scope, even if its response omits an explicit release statement.
Peer stops all writers it started for that scope before handoff, identifies
the stable candidate, and reports the released scope. It must not modify the
candidate or resume those writes on a delayed callback or heartbeat. It may
continue separately assigned, independent work without changing the candidate.

Lead verifies the actual handoff, candidate, and that the prior writer and its
background writers are stopped before taking over or reassigning writes.
Record the scope under Lead's control in the work-status source; a delayed
acknowledgment does not authorize Peer to resume. For repairs, name the owner,
scope, candidate/base, and requested outcome explicitly. Any subsequent change
produces a new identified candidate; acceptance applies only to the candidate
actually reviewed. Read-only review does not acquire write ownership. These
are short coordination decisions, not new Human approval gates or a required
ceremony for each edit.

## Ready inputs and continuity

At session resumption, Lead inspects project instructions, actual state, the
latest handoff, and current ownership before assigning work. Verify required
inputs exist, are accepted, and are available in the working context; a closed
task or completion message alone does not establish readiness. Give each
assignment enough context to start without the preceding conversation.

After acceptance, Lead updates the existing work-status source, records
remaining limits and usable downstream inputs, and reconciles affected
assumptions and dependencies before choosing next work. When a decision changes
the plan, update the existing issue or project document, including outdated
task descriptions and completion criteria. Record the decision and its reason
there; do not leave it only in chat or create a duplicate tracker.

### Project work-status source

Lead designates one existing issue, tracker view, or project document as the
project's current work-status source and includes its location in briefs and
handoffs. Reuse a source already designated by project instructions. If none
exists, first use a suitable existing project document; otherwise create
`docs/WORK_STATUS.md` within the authorized project. Do not copy an established
tracker into a second competing tracker. If the designated source is
unavailable or not writable within existing authority, report that limitation,
keep the latest handoff explicit, and resolve access or a deliberate source
change instead of silently initializing the fallback. Continue unaffected work.

Keep a small current record, using the existing format: outcome and acceptance
criteria; active assignment references, scopes, Lead/Peer operational agent
IDs and write owners; candidates and their disposition; open decisions or
blockers with an owner and return event/checkpoint. Include usable results and
remaining limits. No new mandatory status vocabulary or separate log per edit
is needed. Update on dispatch, write handoff/reassignment, material decisions,
acceptance, and recovery. Lead maintains this record; Peer reports changes
through its response and does not acquire a shared status-file write scope.
Reconcile stale records against actual handoffs, files, and activity before
acting; the document is an index of evidence, not proof of exclusive ownership.
Private Supervisor IDs, conversations, monitoring registrations and private
notes stay in private coordination state, outside project artifacts.

### Session recovery

A restored session or continuation must recover its assignment before taking
affected write ownership or dispatching dependent work:

1. Resolve the current role, project/workspace, directory and task/assignment,
   the current operational agent ID and predecessor when known. Read project
   instructions, the designated work-status source, latest handoffs, actual
   files/Git status and relevant agent activity. A transcript is context, not
   a new assignment or evidence that old work has stopped.
2. Identify active owners, candidate state, predecessor turns/background
   writers, and any known queued work or recurring wake-ups. Do not redispatch
   an existing assignment or infer a released scope from a closed session.
   Same-ID resume still requires checking current ownership; a different ID
   does not inherit the predecessor's rights automatically.
3. Lead reconciles project ownership. A Peer whose ID changed or whose ownership
   is unresolved reports its current ID and assignment to Lead through its
   response channel and waits for an explicit resumed assignment before
   affected writes. A same-ID resume with confirmed, unchanged ownership may
   continue its existing assignment without a new permission request. If Lead
   itself is replaced, use already-authorized lifecycle recovery to quiesce the old Lead and
   confirm its affected work cannot continue before transferring coordination.
   Supervisor may perform bounded recovery under its existing authority but
   never becomes technical owner. Unreachable owners or unavailable lifecycle
   evidence leave affected writes/dispatch pending; read-only investigation
   and independently owned, unaffected work can proceed. Report the exact
   missing evidence or capability, without asking again for settled permission.
4. The recovered Lead records confirmed project-facing owner changes in the
   status source and checks completion/attention delivery for existing Peers.
   Parentage and callbacks are not assumed to follow a continuation. Read
   existing outputs and restore available event coverage; do not send a fresh
   task merely to attach notifications. If reattachment is unsupported, report
   the gap and arrange an available, already-authorized wake-up mechanism.
   Do not claim an intact notification path without evidence.
5. A recovered Supervisor reconciles predecessor wake-ups in private state
   before sending autonomous interventions. Same-name heartbeat replacement
   only deduplicates for the same target agent, not a new ZeroSub agent ID.
   Retire an old heartbeat through its owning session or an authorized host
   operator; the current session's delete_heartbeat cannot delete another
   agent's heartbeat. If retirement cannot be confirmed, keep observation
   read-only, report the unresolved registration, and do not run a second
   autonomous intervention loop. Establish and save current-session wake-up
   coverage after reconciliation before claiming monitoring is active.

An old callback or heartbeat does not revive a released or reassigned write
scope. Its recipient rechecks current ownership; if superseded, it does not
write or dispatch and retires its own obsolete wake-up when possible. Keep
completed work and granted authority; recovery is not a reason to start over.

## Evidence and handoff

Identify the exact candidate, verification environment, reproduction steps,
actual results, and durable evidence locations. Separate verified behavior,
untested scope, failed checks, and unknowns. Match proof to the promised
outcome: passing tests or valid data alone do not establish usable UI, playback
quality, or save/reopen behavior.

A handoff states what is usable, how to try it, remaining limits, and usable
downstream inputs. Permission to proceed with a limitation does not turn an
unmet criterion into a pass.

## Independent judgment

Peer may return `REOPEN_REQUEST` for a failed premise,
`DEPENDENCY_REQUEST` for an unowned prerequisite, or `BLOCKED` when no safe
in-scope progress remains. Each signal includes evidence, consequence, and the
decision or dependency needed.

When architecture or an exact candidate carries material uncertainty, Lead may
request a fresh read-only Peer review of the stable candidate or snapshot. The
review uses the flexible Peer profile and a bounded question; no dedicated
review role, mandatory form, or reviewer count is
required.

## Acceptance and waiting

Every actionable Peer response closes a loop with its original Lead brief.
Peer addresses the assigned outcome and requested evidence, distinguishes
complete/missing/failed/unverified claims, and states write ownership. A
read-only review supplies findings and limits for the bounded question; a
blocker supplies evidence, consequence, and the decision needed.

Lead must answer the question, resolve dependencies or ownership, request
specific missing evidence, or explicitly accept/reject the identified
candidate with a reason. Communicate decisions that affect the Peer and
record them in the existing project status source. A deferral identifies an
owner and return event/checkpoint. Silence, DONE, or test results do not close
the loop. Keep dependent work waiting for resolution while unrelated ready
work continues.

Supervisor checks briefs, actual Peer responses, and Lead dispositions,
intervenes through Lead on a concrete gap, and follows it until repaired
responses and decisions provide closure. An acknowledgment alone is not
closure. Allow normal response handling within an active turn; escalate at
the affected decision or missed checkpoint. Private supervision records and
conversation sources do not belong in project-facing instructions.

Writer proof, passing tests, completion messages, and lifecycle status are
evidence. Lead inspects the exact artifact and explicitly accepts or rejects
the candidate with a technical reason. Human alone decides product scope,
material cost, external effects, and irreversible risk.

Use finish, error, attention, and decision events to advance work. Wait for an
event instead of repeatedly polling unchanged state. Keep handoffs concise and
decision-ready; add detail only when it changes the route or acceptance.
