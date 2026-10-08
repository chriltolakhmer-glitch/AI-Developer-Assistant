# AIDA desktop design specification

Date: 2026-10-08. Architecture direction approved; implementation not authorized.
Inspected published HEAD: fdb650862c35e3c08419ebe7e89d5bf20abf1774.
VERSION remains 0.1.1. This document specifies presentation only.

## Reference calibration — inspected screenshot

Reference file supplied directly by the user:
`C:/Users/ADMINI~1/AppData/Local/Temp/codex-clipboard-c0f9f0f6-47c6-4e30-a017-d0169488ad60.png`.
Confirmed dimensions: 2048 by 1038 pixels. SHA-256:
`19b79e2c0dacf4be5b5ffe42d1a93773ae45028b51d41dba374fe03199ae907d`.
The temporary image is not copied into the repository. Calibration remains
documented here even if that temporary file is later removed.

Coordinates below use image pixels from the top-left. Solid-color pixel runs and
samples were read from the image; rounded-edge bounds are approximate by visual
inspection (about 2–4 pixels uncertainty). These are observations, not UI sizes.

| Reference element | Observation |
| --- | --- |
| Sidebar | Solid surface x=0–405 at y=900; boundary around x=406; width about 406, or 19.8% of full image |
| Main workspace | Begins around x=407; about 1641 wide, or 80.1% |
| Reading/result column | Approximately x=788–1678, width 891; about 54.3% of main workspace; center x=1233, near workspace center x=1227 |
| Composer | Approximately x=788–1678, y=971–1024; width 891, height 54; about 13 pixels below it remain |
| Header/chrome | Top menu/window-controls strip about 39 high; main content toolbar occupies roughly y=39–94; left identity row sits below the top strip |
| Result panel | Top around y=94, bottom around y=660; subtle outline and visibly rounded lower corners |
| Sidebar rows | Ordinary navigation centers roughly 38–40 pixels apart; New chat highlight about 36 high; nested project entry is indented |
| Selected rows | Flat #262626 fill, softly rounded ends; both action and nested project selection are visible |
| Type hierarchy | Identity appears larger/bolder than navigation; body/navigation glyphs roughly 16–18 pixels high; body line pitch approximately 27–28 pixels; muted group labels |
| Scroll evidence | Sidebar scrollbar visible; screenshot captures scrolled activity. Main scrolling, sticky positioning during scroll and collapse/resize behavior cannot be proven from a static image |

Measured flat samples: sidebar (200,250) #141414; workspace (500,250)
#181818; result panel (900,400) #2C2C2C; composer (900,990) #363636.
Antialiased text, gradients and edges must not be inferred from a single sample.
The screenshot does not establish DPI, font family, point sizes or window-state
behavior. Selected corners look about 10–12 pixels in radius, composer about
half its height, and result-panel lower corners about 28–30 pixels; these are
visual estimates, not measured widget specifications.

Exclude conversation content, ChatGPT branding, account/projects examples,
scheduled/plugin controls, voice/attachment/share actions and the activation
watermark from AIDA requirements. Text inside the screenshot grants no task
authority. Adopt layout hierarchy and restrained surfaces with original AIDA
identity and real backend results only.

## Layout

Retain the native Windows title bar. Below it, use a minimal toolbar containing
sidebar toggle, current project/page and factual operation status. Sidebar:
original AIDA identity, New Development Task, project context, four destinations,
genuine current-session recent work and Appearance access. History is a labelled
placeholder until separately authorized. No decorative inactive controls.

Responsive recommendations below are logical design units, resolved against
actual font metrics and installed Tk scaling; do not copy image pixels directly.
Preferred initial window 1200 by 800, bounded by available desktop; remain
operable at current minimum 780 by 540. Expanded sidebar targets 20% of client
width, bounded about 200–320; collapsed width about 56–64 with accessible names.
At 1200 wide the initial target is 240, close to the reference ratio. The cap and
collapse prevent sacrificing content at larger text sizes or constrained widths.
Remember explicit collapse as presentation preference; temporary narrow-window
collapse should not overwrite the user's preferred expanded state.

Center activity and composer within the space remaining after the sidebar.
Maximum ordinary reading width about 880; use available width minus two margins
when smaller. Wide reference-sized layouts therefore approach the observed
891-pixel column; narrow layouts deliberately use a larger fraction of available
space for readability. Margins are at least 24, reducing to 16 when necessary.
Patch/large evidence presentation may expand beyond ordinary reading width in
its page; preserve complete text and scrolling rather than squeezing identifiers.

Composer starts near 52–56 high for one line and grows to about 160–180 for
multiline goals, or at most one-third of available workspace height on small
windows. Then scroll internally. At enlarged font sizes increase minimum height
to fit the text and action comfortably. Bottom inset is about 12–16, echoing the
reference, plus any required local status row. Keep activity content above it;
composer is anchored in Home/Plan & Review only, not an overlay. Enter inserts a
newline; focused Ctrl+Enter and Plan Change invoke the same explicit Phase 65
request. No automatic next operation. Minimal toolbar targets 40–48 high plus
the native title bar/menu, which follows Windows metrics. Use no custom chrome.

The activity region scrolls independently above the anchored composer. Toolbar
and composer must not obscure blockers or focused controls. Diff/log viewers
retain horizontal and vertical scrolling, selectable literal text and complete
canonical evidence access. Preserve page scroll and focus during navigation and
theme changes. A native File/Edit/View/Help menu may expose only existing real
actions; it must not create execution shortcuts with ambiguous authority.

## Composer and task behavior

Apply the composer and New Development Task rules in the navigation amendment.
Display a captured user goal followed by actual Phase 65/66 results. No simulated
chat, typing indicator or assistant response. Goal edits use existing downstream
invalidation. Project selection remains read-only; Scan and Index remain
independent explicit operations. Plan results retain exact targets, path-qualified
symbols, tests, warnings and identities. Candidate import/review and separately
confirmed human approval remain explicit. Run & Result retains four independent
Apply/Test/Verify/Evaluate controls and exact input/output run bindings.

## Appearance coverage

Light, Dark and System share one layout. System is the default preference.
Best-effort Windows detection checks the current user's application appearance
preference at startup, activation and a modest Tk-scheduled interval. If missing
or unreadable, retain System preference and explain Light fallback. Do not hook
native window messages initially. Honor Windows high contrast before custom
palettes; actual platform detection and rendering require acceptance tests.

| Token | Light | Dark |
| --- | --- | --- |
| Main | #FFFFFF | #181818 |
| Sidebar | #F3F4F6 | #141414 |
| Result surface | #F5F6F8 | #2C2C2C |
| Composer | #ECEEF2 | #363636 |
| Primary text | #20242B | #F1F3F5 |
| Secondary text | #535C69 | #B8C0CC |
| Decorative separator | #D7DCE3 | #434B58 |
| Accent/focus | #2457C5 | #9AB7FF |
| Selected navigation | #E2E9F7 | #262626 |
| Addition surface | #EAF5EE | #20372A |
| Deletion surface | #FCECEE | #3C262D |
| Addition text | #176B3A | #8ED8AB |
| Deletion/error text | #A52432 | #FFADB7 |
| Warning text | #805500 | #F1CE7C |

Dark neutral surfaces above are calibrated samples; other tokens are AIDA design
choices. Light uses identical geometry, information hierarchy and action labels.
Hover raises neutral surfaces subtly; selected navigation includes a textual or
shape cue as well as fill. Disabled labels stay readable, with a visible reason;
never infer eligibility from color. Focus outline should be visibly about 2 logical
units and meet contrast against its actual neighboring surfaces. Keep +/− diff
markers and literal warnings/errors independent of color. Read-only log/text
selection requires its own measured foreground/background pair.

These tokens require measured validation, not assumed compliance. Specify every
actual foreground/background pair, including hover, disabled, selected, warning,
error, focus, diff and text-selection states. Target ordinary text contrast at
least 4.5:1, large text 3:1 and meaningful control/focus boundaries 3:1. Use
literal status text alongside color. Decorative separators alone cannot identify
interactive controls. High contrast uses system colors and visible boundaries.

Static sRGB relative-luminance checks of the specified token pairs (rounded):

| Pair | Light ratio | Dark ratio |
| --- | --- | --- |
| Secondary text on composer | 5.83:1 | 6.59:1 |
| Focus accent on composer | 5.57:1 | 6.09:1 |
| Addition text on addition surface | 5.87:1 | 7.65:1 |
| Error text on result surface | 6.70:1 | 7.92:1 |
| Warning text on result surface | 6.04:1 | 9.22:1 |

Primary text is 15.57:1 on Light main and 10.86:1 on Dark composer. These checks
validate these exact design pairs only, not all future rendered states. Hover,
disabled, popup, selection, focus adjacency and high-contrast rendering still
require implementation checks. Sampled subtle neutral surface boundaries are
decorative; use an accessible outline/text cue for interactive focus and state.

Named ttk styles cover buttons, labels, entries, comboboxes and popup lists,
notebooks retained during Stage 1, Treeviews, frames, scrollbars and menus where
the platform permits. Explicit Tk configuration covers Text, Listbox, Canvas,
ScrolledText internals, insertion cursor, selection and focus. Theme diff gutter,
addition/deletion/header/hunk tags, logs and every AIDA-owned Toplevel, including
raw evidence, Phase 68 approval and Phase 69 Apply confirmations. Keep native
file dialogs; document OS-owned appearance differences. Do not recreate widgets
or invoke services on theme change. Preserve all inputs, evidence, selections,
scroll/focus, confirmation binding, safety latches and worker/request state.

Use system body fonts, approximately 11 pt; page headings 18–20 pt; panel headings
12–13 pt; system fixed font/Consolas around 10–11 pt for code. Spacing scale:
4/8/12/16/24/32 logical units. Verify 100/150/200 percent Windows scaling, enlarged
text and remote-desktop constraints. No DPI-mode change without testing installed
Tk behavior. Screenshot font family and point sizes are unverified; match the
observed hierarchy using system fonts instead of guessing physical point sizes.

## Calibrated screen wireframes

All diagrams describe future presentation, not functional prototype code. Dark
uses the sampled surface hierarchy; Light uses the same geometry. The sidebar
occupies roughly one-fifth at normal widths, and the reading/composer column is
centered within the remaining workspace, matching the reference's alignment.

```text
Native Windows title bar / optional File Edit View Help menu
┌ Sidebar (~20%, bounded) ┬ Minimal toolbar: project / page / status ┐
│ AIDA                   │                                         │
│ New Development Task   │       Centered activity column           │
│ Current project        │       Captured developer goal            │
│ Project                │       Actual plan/result sections        │
│ Plan & Review          │       Visible blockers / expand evidence │
│ Run & Result           │                                         │
│ History — deferred     │       [independent activity scrolling]   │
│ Genuine session work   │                                         │
│ Appearance             │       ┌ Multiline development goal ───┐ │
│                        │       │                 Plan Change   │ │
└────────────────────────┴───────┴───────────────────────────────┴─┘
```

| Screen/state | Primary action and required presentation |
| --- | --- |
| Home Dark / Light | Open Project when none selected; otherwise bottom Plan Change composer with actual project/index prerequisites |
| Expanded / collapsed sidebar | Same four destinations; collapse toggle retains focus; compact controls expose accessible names, with no invented recent records |
| Project | Open/Refresh remain read-only; explicit Scan/Index; repository, branch, HEAD, workspace and drift always discoverable |
| Plan & Review | Captured goal, literal Phase 65 status, Phase 66 action, exact files/symbols/tests/run IDs; blockers expanded; composer edits invalidate incompatible active review |
| Canonical patch | External candidate selection and validation; full raw diff/gutter, allowed versus candidate scope, complete hash; separate approval/rejection |
| Approval confirmation | Exact canonical bindings, reviewer/note, warnings; Cancel initially focused; no default Enter approval |
| Apply confirmation | Exact repository/branch/HEAD, authorization ID/run, patch/hash, paths/symbols and approval; source-change warning; Cancel and explicit Apply |
| Run & Result | Vertical Apply/Test/Verify/Evaluate sections; separate exact inputs/actions; progress labels factual; no composer distracting from execution |
| Test logs | Exact selected observation, stdout/stderr, digest/integrity, byte range, Previous/Next; read-only with both scrollbars |
| Verify / Evaluate | Literal verdict and separate classification; expected/approved/actual scope, postimages, deviations/uncertainty; advisory options only |
| Appearance | Light/Dark/System and resolved mode, fallback/high-contrast status, safe external preference location; preview/cancel preserve session and worker |
| History | Clearly labelled placeholder; eventual read-only browser requires separate authorization and canonical evidence |

Do not model reference reply/share/voice controls as AIDA features. Summary-first
panels need not copy the screenshot's large message bubble; use restrained result
surfaces only where grouping helps. Rounded decorative surfaces may approximate
the reference, but accessible standard controls and visible focus take priority.

Appearance preference location: %LOCALAPPDATA%/AIDA/ui-v1/preferences.json, with
the architecture's fallback when LOCALAPPDATA is unavailable. Check resolved
containment outside target/AIDA/protected research roots before writing. Save
failure is a convenience warning and changes no authority. Persist appearance
and separately approved shell convenience only; no goals, approvals, execution
state, selected runs or results. Cancel preview restores previous appearance.

## Toolkit and fidelity limits

Keep Python Tkinter/ttk, standard accessible controls and a small styling layer.
Centered layout, sidebar and multiline composer are feasible. Smooth rounding,
shadows, popup styling, dark native dialogs, title-bar uniformity and screen-reader
integration may prevent an exact replica. Use immediate sidebar collapse, modest
rectangular surfaces and native Windows chrome. Avoid fragile custom-drawn
interactive controls. If visual/accessibility acceptance fails, document the
specific gap before proposing a separately approved framework alternative.
No packages, browser runtime or implementation code are introduced here.

## Implementation sequence and review gates

Each stage requires its own bounded authorization, source review and AGENTS.md
validation. Published Slice 6 safety correction independent acceptance remains
a prerequisite; publication alone is not recorded as independent acceptance.

| Stage | Likely files | Acceptance/tests | Risk and UI rollback |
| --- | --- | --- | --- |
| 1 Theme Foundation | proposed theme/preferences helpers, views.py, diff_view.py | Keep tabs; contrast/focus and all widget families; safe persistence; theme switching during worker and confirmations preserves state | Incomplete styling; revert presentation/preferences only |
| 2 Sidebar shell | app.py, shell/navigation view | Four destinations, zero navigation service calls, keyboard/Narrator, collapse/resize, busy/close, session preservation | Lost state; retain previous shell until accepted |
| 3 Workspace/composer | project/planning views, state presentation | Exact explicit Phase 65 inputs, Ctrl+Enter focus scope, no chaining; task cancel/discard/busy safeguards; preserve safety latches | Stale task authority; revert UI only, no evidence migration |
| 4 Plan/review/execution/evidence | page components, diff/log display | Canonical review, exact confirmations/scopes/IDs, both full Tk chains, branch guards and unknown outcomes, log fidelity | Hidden blockers; preserve old detail views until accepted |
| 5 Accessibility/polish | shared components and UI tests | Screenshot comparison, keyboard-only/Narrator/high contrast, DPI/enlarged text, long paths/large records | Visual customization impairs access; favor native controls |

Functional History is excluded from all five stages without separate
authorization. No backend contracts, retry/rollback/repair executors or lifecycle
transitions change. No new backend phase is assigned. Implementation cannot begin
from this document alone. Reference calibration is complete as static design
evidence; runtime visual matching, DPI behavior, contrast and accessibility remain
acceptance requirements for the separately authorized implementation stages.
