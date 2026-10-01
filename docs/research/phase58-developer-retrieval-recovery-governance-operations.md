# Phase 58 - Developer Mode Retrieval Recovery Strategic Governance Operations

## Baseline and developer-only scope

Phase 57 provides strategic objectives, owned roadmap records, dependencies and
strategic reviews. Earlier phases retain maturity, evolution and assurance
operations history. Operational gaps remain in decision attribution, action
lifecycles, follow-up ownership, exception acceptance and inspectable closure.
This phase adds independent operational governance records for those gaps.

The starting checkout contained uncommitted Phase 46-57 work. Its 294 tracked and
nonignored untracked files were inventoried by SHA-256 in the external directory
`C:/Apps/Temp/Phase58/baseline.json`. Git status and tracked diff paths were retained
alongside it. Protected research paths were unchanged; the existing tracked changes
were confined to the CLI, developer tests and CLI guide. All nine Phase 57 tests
passed in 83.438 seconds with no skips, failures or errors (`baseline-tests.log`).
The starting `v0.1.1` tag object was
`05688504f74ad51230ee1566fad8cda0f1b1ad97`.

The new layer does not change research evaluation, research retrieval methodology,
benchmark datasets, Humanize, frozen releases, research snapshots or v0.1.1 behavior.
It creates no scores, rankings, productivity metrics or automated prioritization.
Execution means recording human-directed work performed outside this layer; no
command executes recovery, changes retrieval behavior or activates deployment.

## Storage and decision model

`src/developer/governance_operations.py` maintains a separate append-only journal
under `<external developer workspace>/optimization/governance-operations`. Existing
workspace/source/research guards apply before reads and writes. Events retain mode,
schema version, sequence, previous-event digest, UTC timestamp, actor and reason.
Replay validates lifecycle and closure invariants. Exclusive atomic publication
prevents overwriting a competing append. Read-only commands create no workspace,
journal or repair records.

Decisions contain `decision_id` (`decision-001`), `governance_id`, decision text,
owner, status, created/updated times, history, reviews, actions and exceptions.
Creation requires an existing strategic objective and retains its snapshot.
Decision reviews preserve the objective, roadmap, dependency and evolution review
state along with the operator's note and closure evidence.

| Current decision state | Allowed next states |
| --- | --- |
| open | reviewing, deferred |
| reviewing | open, decided, deferred |
| decided | reviewing, deferred, closed |
| deferred | open, reviewing |
| closed | None |

Every transition is explicit and requires a note, actor and reason. Becoming decided
requires a current recorded review. Closure additionally requires the closure checks
below. Ownership reassignment invalidates the earlier owner's review. Deferring a
decision never changes its actions or exceptions.

## Action lifecycle and deferral

Actions contain an action ID, decision and governance links, owner, description,
status, ISO `due_date` (`YYYY-MM-DD`), completion evidence, optional deferral,
timestamps and history. Owners and dates are required. Overdue means an unfinished,
nondeferred action whose due date precedes the current UTC date. A due date includes
that entire UTC day. Merely reaching it changes no stored state.

| Current action state | Allowed next states |
| --- | --- |
| open | in_progress, blocked, cancelled |
| in_progress | blocked, completed, cancelled |
| blocked | open, in_progress, cancelled |
| completed | None |
| cancelled | None |

Completing or cancelling requires evidence or a separate explicit manual closure
reason. A transition note alone does not satisfy this requirement. Terminal actions
are immutable. Ownership/due-date revisions append history and clear a prior deferral.

The requested states have no deferred state, so `governance-action-defer` records a
blocked action with an attributed reason and future UTC `--until` date. This explicit
deferral remains current through that date. It suppresses overdue reporting and
permits decision closure with a visible warning. Once the window elapses, follow-up
and closure checks flag the action again without changing stored status. Ordinary
blocked actions are not implicitly deferred. Resuming work clears the deferral.

## Exceptions

Exceptions contain an exception ID, governance/decision links, related decision or
action ID, description, owner, original reason, status, expiration timestamp,
closure evidence, review history and complete event history. Action links must
belong to the same decision. Creation requires a future timezone-aware expiration.

| Current exception state | Allowed next states |
| --- | --- |
| open | accepted, mitigated, expired, closed |
| accepted | mitigated, expired, closed |
| mitigated | open, closed |
| expired | mitigated, closed |
| closed | None |

Acceptance requires an explicit human note and a still-future expiration. Acceptance
is never inferred from a clean report. An open or accepted exception becomes visibly
expired when its timestamp is reached, without writing an expired event. Operators
may also explicitly expire an exception early with a reason. Expired exceptions
cannot be accepted; mitigation or a new exception is required.

Mitigation and closure require evidence or a separate manual closure reason.
Mitigated and closed exceptions are resolved, so their former acceptance expiration
no longer applies. Closed exceptions are immutable. Reassigning an accepted exception
returns it to open for the new owner's explicit acceptance. Prior acceptance and
ownership remain in history. No command performs remediation.

## Evidence and closure verification

Evidence references use paths relative to the external developer workspace. At
recording time, each referenced file must exist within that workspace; its path,
SHA-256 digest and size are retained. Absolute, escaping and missing paths are
rejected. Reports compare current content against the captured digest and expose
changed or missing evidence. The journal retains references and hashes, not file
contents; operators must preserve those external files.

`--closure-reason TEXT` is the explicit alternative when file evidence is unavailable
or inappropriate. It is separate from the general mutation reason and transition
note. If references are supplied, all must remain valid even when a manual reason
is also present. A fresh explicit decision review may choose a manual rationale
instead; prior evidence remains in history. Terminal action/exception evidence
cannot be rewritten, so lost evidence remains a visible historical gap.

`governance-close-check` returns `passed`, `warnings`, `blocked`, `manual_actions`
and never closes a decision. A decision passes when:

- It is decided (or already closed during historical rechecking), with an owner.
- Its latest human review belongs to that owner and exactly matches current related
  governance state. Missing source history or changed strategic/evolution/maturity
  evidence blocks closure until the operator inspects and records a fresh review.
- The decision has valid evidence or an explicit manual closure rationale.
- Every action is completed, explicitly cancelled with proof/reason, or currently
  deferred with an owner and time-bound review note.
- Every exception is mitigated/closed with proof/reason, or explicitly accepted and
  unexpired. Open and expired exceptions block closure.

Cancellations, current deferrals and accepted exceptions appear as warnings.
Known strategic readiness gaps, risks and dependencies also appear as warnings:
closing an operational decision does not assert that the entire strategic objective
is complete or ready. The operator must review the exact current source state; this
layer cannot approve, waive or change Phase 57 readiness gates. A passed result can
therefore still have warnings and requires an explicit human closure transition.

The closure event retains its check result. Later evidence loss, source drift,
exception expiry or elapsed deferrals is visible without reopening the decision.
Existing nonterminal actions and exceptions can still be explicitly followed up
after decision closure, preserving the original closure record. New actions,
exceptions, decision reviews or ownership changes require a new decision.

## Read-only operational reports

All commands accept `--workspace PATH` and `--json`. Default output is the developer
notice followed by JSON; `--json` returns one JSON object containing the notice.

| Command | Output |
| --- | --- |
| `prototype local governance-decisions` | Open/reviewing/decided, deferred, closed, recent decisions and owners |
| `prototype local governance-actions` | Open, blocked, overdue, deferred, completed/cancelled actions and owners |
| `prototype local governance-exceptions` | Active, expired, mitigated and unresolved exceptions |
| `prototype local governance-decision DECISION_ID` | Full decision history, source objective/roadmap/dependencies, actions, exceptions, reviews and closure analysis |
| `prototype local governance-followup` | decisions, blocked_actions, overdue_actions, exceptions, missing_evidence, ownership_gaps and manual_actions |
| `prototype local governance-close-check` | passed, warnings, blocked and manual_actions |

Recent decisions means the ten most recently changed decision records, not a
priority ranking. Follow-up includes deferred actions and outstanding exceptions
belonging to already-closed decisions. Reports retain insertion order elsewhere.
Valid records require explicit ownership; malformed journals fail closed rather
than silently repairing missing fields. Reports exit zero even when blockers exist;
inspect result fields. Unknown IDs and invalid journal data use existing CLI errors.
Empty report lists create no directories or records.

## Explicit operator workflow

Mutations require `--reason` and accept `--actor` (default `developer`).

```powershell
prototype local governance-decision-create governance-001 --decision "Continue recovery assurance improvement" --owner maintainer --reason "Record review proposal" --workspace C:\DeveloperWorkspace
prototype local governance-decision-transition decision-001 reviewing --note "Begin review" --reason "Review proposal" --workspace C:\DeveloperWorkspace
prototype local governance-decision-review decision-001 --note "Objective and roadmap reviewed" --closure-reason "Manual review outcome recorded here" --reason "Record review" --workspace C:\DeveloperWorkspace
prototype local governance-decision-transition decision-001 decided --note "Proceed with follow-up" --reason "Human decision" --workspace C:\DeveloperWorkspace
prototype local governance-action-add decision-001 --description "Review renewal procedure" --owner maintainer --due-date 2027-01-31 --reason "Track follow-up" --workspace C:\DeveloperWorkspace
prototype local governance-action-transition decision-001 action-001 in_progress --note "Review started" --reason "Record progress" --workspace C:\DeveloperWorkspace
prototype local governance-action-transition decision-001 action-001 completed --note "Procedure checked" --closure-reason "Maintainer confirmed the procedure manually" --reason "Record completion" --workspace C:\DeveloperWorkspace
prototype local governance-close-check --workspace C:\DeveloperWorkspace
prototype local governance-decision-transition decision-001 closed --note "Closure result and warnings reviewed" --reason "Explicit closure" --workspace C:\DeveloperWorkspace
```

Replace example dates with the intended schedule. Use repeated `--evidence PATH`
on decision review, action transitions or exception transitions for external
workspace file references. Use `governance-decision-assign DECISION_ID --owner OWNER`
for handoff, then record a new review. `governance-action-assign DECISION_ID ACTION_ID
--owner OWNER --due-date YYYY-MM-DD` retains earlier owner/date history.

```powershell
prototype local governance-action-defer decision-001 action-001 --until 2027-02-15 --note "Owner agreed to the follow-up window" --reason "Explicit deferral" --workspace C:\DeveloperWorkspace
prototype local governance-exception-add decision-001 --action-id action-001 --description "Temporary procedure exception" --owner maintainer --expires-at 2027-02-15T00:00:00+00:00 --reason "Pending replacement review" --workspace C:\DeveloperWorkspace
prototype local governance-exception-transition decision-001 exception-001 accepted --note "Human acceptance until expiry" --reason "Review exception" --workspace C:\DeveloperWorkspace
prototype local governance-followup --workspace C:\DeveloperWorkspace
```

Deferral and exception examples apply to unfinished items before closure; completed
actions cannot be deferred. Omit `--action-id` to link an exception to the decision
itself. `governance-exception-assign DECISION_ID EXCEPTION_ID --owner OWNER` records
handoff. Exception mitigation/closure and action cancellation require `--evidence`
or `--closure-reason`. Future exception expiry and deferral windows are mandatory.

## Limitations and validation

This layer records local operational accountability, not proof of successful recovery.
Actors/owners are attribution, not authenticated identities. Hash chains detect
broken history but cannot prevent rewriting an entire chain. Serialize related
mutations for consistent source snapshots. Evidence availability is checked at report
and decision time; no background watcher, scheduler or automatic repair is added.
Developer repositories are not added to research snapshots. Existing runtime
retrieval authority remains unchanged.

Tests use temporary external workspaces. Baseline inventories, logs and preservation
evidence are retained in `C:/Apps/Temp/Phase58`.

Nine new regression tests cover decision/action/exception lifecycles, invalid
transitions and attribution, due dates and expiry, explicit deferrals, post-closure
follow-up, closure proof and replay invariants, changed/missing evidence files,
workspace containment, ownership handoffs, source drift, strategic/evolution/maturity/
assurance compatibility, all CLI reports and mutation routes, read-only behavior,
atomic publication failure and journal corruption. The final targeted run passed
all nine tests in 125.695 seconds with zero skips, failures or errors
(`operations-final.log`, exit 0). The initial eight-test run also passed before the
final time-validation and closure replay coverage was added.

Required suites run sequentially under Python 3.14.7. `EMBEDDING_MODEL_CACHE` is
unset; no dependency or environment changes were made.
