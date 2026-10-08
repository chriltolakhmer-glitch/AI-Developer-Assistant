# Desktop Stage 1: Theme Foundation

The existing four-tab interface offers Light, Dark and System in its appearance
selector. System is the default preference. This stage adds no sidebar, composer
or functional History. The default window height reserves space for the selector
without reducing the existing review panel.

`src/ui/theme.py` owns semantic palettes, named Tk fonts, ttk styles and existing
Tk widget colors. Standard ttk controls use the controllable `clam` theme.
Evidence panels retain Text behavior and use ttk scrollbars. Theme changes update
presentation in place: they do not rebuild the session, alter evidence, change
selections or dispatch backend work. Existing approval and Apply dialogs retain
their exact confirmation context.

## System appearance and accessibility

On Windows, detection reads AppsUseLightTheme and native high-contrast settings.
High contrast takes priority over all three modes and uses system text, surface
and selection colors. Detection runs on activation and every two seconds through
the Tk event loop. When detection is unavailable, System resolves to Light while
retaining the System preference and showing a factual fallback message.

Light and Dark text, selection, hover, disabled, warning, error and diff color
pairs are tested against rendered widget/style values at 4.5:1 or better. Focus
indicators are tested at 3:1 or better. Keyboard traversal uses native controls.
Tk scaling tests exercise approximately 100%, 150% and 200% scaling values; these
do not substitute for moving a window between physical Windows monitors.

Native title bars and operating-system file dialogs remain controlled by Windows.
Tk/ttk cannot guarantee their dark appearance or identical rendering across Tk
versions. Screen-reader behavior and physical per-monitor DPI transitions require
separate manual acceptance. High-contrast priority is tested with controlled
system-color fixtures; tests do not change the user's Windows accessibility mode.

## Appearance-only preferences

The default file is `%LOCALAPPDATA%/AIDA/ui-v1/preferences.json`, with
`~/.prototype/ui-v1/preferences.json` as the fallback when LOCALAPPDATA is absent.
Only an explicit appearance selection writes it. Startup and shutdown do not
create preferences. The payload contains only `appearance`.

Reads are bounded to 4096 bytes. Invalid, inaccessible or unsafe files fall back
to System with a visible warning. Saves replace an external temporary file
atomically; save failures do not interrupt developer operations. Paths are checked
against the AIDA checkout, configured protected roots and the current target
repository before writes. Symlinks and junctions are rejected. These checks are
local path protection, not a security boundary against concurrent hostile changes
to the filesystem.

No lifecycle authority, authorization, execution state or evidence is persisted
in appearance preferences. All Phase 65–72 contracts, explicit actions, single
worker, stale-result rejection and safety latches remain unchanged.
