"""Four-tab shell with explicit repository inventory/index and goal planning."""

import tkinter as tk
from tkinter import ttk

from .state import ViewState


class ShellView:
    FIELD_LABELS = (
        ("repository_id", "Repository ID"), ("branch", "Branch"), ("head", "HEAD"),
        ("clean", "Working tree"), ("changes", "Change presence"),
        ("languages", "Supported languages"), ("index", "Index freshness (last Refresh)"),
        ("aida_version", "AIDA version"), ("source_authority", "AIDA source authority"),
    )

    def __init__(self, root, open_repository, browse_repository, browse_workspace, start_operation, inputs_changed):
        self.rendering = False
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=12)
        self.project = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.project, text="Project")
        self.plan = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.plan, text="Plan & Review")
        for title in ("Run & Result", "History"):
            placeholder = ttk.Frame(self.notebook, padding=20)
            ttk.Label(placeholder, text="Available in a later UI slice.").pack(anchor="w")
            self.notebook.add(placeholder, text=title)
        self.project.columnconfigure(1, weight=1)
        self.repository = tk.StringVar(root)
        self.workspace = tk.StringVar(root)
        ttk.Label(self.project, text="Repository root").grid(row=0, column=0, sticky="w", pady=5)
        self.repository_entry = ttk.Entry(self.project, textvariable=self.repository)
        self.repository_entry.grid(row=0, column=1, sticky="ew", padx=8)
        self.browse_repo_button = ttk.Button(self.project, text="Browse…", command=browse_repository)
        self.browse_repo_button.grid(row=0, column=2)
        self.open_button = ttk.Button(self.project, text="Open", command=open_repository)
        self.open_button.grid(row=0, column=3, padx=8)
        ttk.Label(self.project, text="External workspace").grid(row=1, column=0, sticky="w", pady=5)
        self.workspace_entry = ttk.Entry(self.project, textvariable=self.workspace)
        self.workspace_entry.grid(row=1, column=1, sticky="ew", padx=8)
        self.browse_workspace_button = ttk.Button(self.project, text="Browse…", command=browse_workspace)
        self.browse_workspace_button.grid(row=1, column=2)
        self.refresh_button = ttk.Button(self.project, text="Refresh status", command=open_repository)
        self.refresh_button.grid(row=1, column=3, padx=8)
        actions = ttk.Frame(self.project)
        actions.grid(row=2, column=0, columnspan=4, sticky="w")
        self.scan_button = ttk.Button(actions, text="Scan repository", command=lambda: start_operation("scan"))
        self.scan_button.pack(side="left", padx=4)
        self.index_button = ttk.Button(actions, text="Index / Reindex", command=lambda: start_operation("index"))
        self.index_button.pack(side="left", padx=4)
        ttk.Label(actions, text="Refresh is read-only. Scan and Index write external AIDA artifacts.").pack(side="left", padx=8)
        self.fields = {}
        for row, (key, label) in enumerate(self.FIELD_LABELS, start=3):
            ttk.Label(self.project, text=label).grid(row=row, column=0, sticky="nw", pady=4)
            value = tk.StringVar(root, value="—")
            ttk.Label(self.project, textvariable=value, wraplength=680).grid(row=row, column=1, columnspan=3, sticky="w", padx=8)
            self.fields[key] = value
        self.status = tk.StringVar(root)
        ttk.Label(self.project, textvariable=self.status, wraplength=800).grid(row=13, column=0, columnspan=4, sticky="w", pady=12)
        self.details = tk.Text(self.project, height=7, wrap="none", state="disabled")
        self.details.grid(row=14, column=0, columnspan=4, sticky="nsew")
        self.project.rowconfigure(14, weight=1)
        ttk.Label(self.plan, text="Development goal").pack(anchor="w")
        self.goal = tk.Text(self.plan, height=4, wrap="word")
        self.goal.pack(fill="x", pady=6)
        ttk.Label(self.plan, text="Existing regression tests — no selection uses Phase 65 automatic binding.").pack(anchor="w")
        self.catalog_button = ttk.Button(self.plan, text="Load existing regression tests",
                                         command=lambda: start_operation("catalog_tests"))
        self.catalog_button.pack(anchor="w", pady=4)
        self.tests = tk.Listbox(self.plan, selectmode="extended", exportselection=False, height=5)
        self.tests.pack(fill="x")
        self.catalog_ids = ()
        self.plan_button = ttk.Button(self.plan, text="Plan change", command=lambda: start_operation("plan"))
        self.plan_button.pack(anchor="w", pady=6)
        self.plan_status = tk.StringVar(root)
        ttk.Label(self.plan, textvariable=self.plan_status, wraplength=880).pack(anchor="w")
        self.plan_summary = tk.Text(self.plan, height=10, wrap="word", state="disabled")
        self.plan_summary.pack(fill="both", expand=True)
        ttk.Label(self.plan, text="Candidate validation and detailed evidence are available in later UI slices.").pack(anchor="w", pady=5)
        self.controls = (self.repository_entry, self.workspace_entry, self.browse_repo_button,
                         self.open_button, self.browse_workspace_button, self.refresh_button,
                         self.scan_button, self.index_button, self.goal, self.catalog_button, self.tests, self.plan_button)
        self.repository.trace_add("write", lambda *_: inputs_changed())
        self.workspace.trace_add("write", lambda *_: inputs_changed())
        self.goal.bind("<<Modified>>", lambda *_: self._goal_changed(inputs_changed))
        self.tests.bind("<<ListboxSelect>>", lambda *_: inputs_changed())

    def _goal_changed(self, callback):
        if self.goal.edit_modified():
            self.goal.edit_modified(False)
            callback()

    def selected_test_ids(self):
        return tuple(self.catalog_ids[int(index)] for index in self.tests.curselection())

    def render(self, state: ViewState):
        self.rendering = True
        try:
            self._render(state)
        finally:
            self.rendering = False

    def _render(self, state: ViewState):
        for control in self.controls:
            control.configure(state="disabled" if state.loading or state.close_pending else "normal")
        if not state.loading:
            self.repository.set(state.repository)
            self.workspace.set(state.workspace)
        for value in self.fields.values():
            value.set("—")
        details = ""
        if state.facts:
            facts = state.facts
            for key in ("repository_id", "head", "aida_version", "source_authority"):
                self.fields[key].set(facts[key])
            self.fields["branch"].set("Detached HEAD" if facts["detached_head"] else facts["branch"])
            self.fields["clean"].set("Clean" if facts["clean"] else "Dirty")
            self.fields["changes"].set("; ".join(f"{name}: {'yes' if facts[key] else 'no'}" for name, key in (
                ("Staged", "staged_changes"), ("Unstaged", "unstaged_changes"), ("Untracked", "untracked_files"))))
            self.fields["languages"].set(", ".join(facts["supported_languages"]))
            freshness = facts["index_freshness"]
            self.fields["index"].set(freshness["status"] + (": " + freshness["reason"] if freshness.get("reason") else ""))
            details = "\n".join(f"{row['status']} {row['path']!r}" for row in facts["working_tree_status"])
            if facts.get("parser_failures"):
                details += "\nParser diagnostics: " + repr(facts["parser_failures"])
        if state.close_pending:
            message = "Close pending — waiting for the current operation to finish."
            if state.error:
                message += " " + state.error
        elif state.loading:
            message = f"Running {state.operation}…"
        else:
            message = "Repository loaded. Choose an explicit operation." if state.facts else "Choose a repository. Opening/refreshing creates no AIDA evidence."
            if state.operation == "read_repository" and state.facts:
                message = state.facts["notice"]
            result = {"scan": state.scan_result, "index": state.index_result, "plan": state.plan_result}.get(state.operation)
            if result is not None:
                message = f"{state.operation}: {result['status']}"
            if state.operation == "catalog_tests" and state.test_catalog is not None:
                message = "Existing regression catalog loaded; no target tests executed."
            message = state.error or message
        self.status.set(message)
        operation_details = []
        for kind, result in (("Scan", state.scan_result), ("Index", state.index_result)):
            if result is not None:
                repo = result["scan"] if kind == "Scan" else result["repository"]
                operation_details.append(
                    f"{kind}: {result['status']} | run: {result['run_id']}\n"
                    f"Repository: {repo['repository_id']}\nHEAD: {repo['commit_sha']}\n"
                    f"Source snapshot: {repo['working_tree_sha256']}\n"
                    f"Files: {repo['tracked_file_count']}; eligible Python: {repo['eligible_python_file_count']}")
                if kind == "Index":
                    operation_details.append(f"Index result: {result['index_status']}\nIndex path: {result['index_path']}\nIndexed chunks: {result['indexed_chunk_count']}\nRefresh status explicitly to read current freshness.")
        details = "\n\n".join([details, *operation_details]).strip()
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        self.details.insert("1.0", details)
        self.details.configure(state="disabled")
        ids = tuple(identity for rows in (state.test_catalog or {}).values() for identity in rows)
        if ids != self.catalog_ids:
            self.catalog_ids = ids
            self.tests.configure(state="normal")
            self.tests.delete(0, "end")
            for identity in ids:
                self.tests.insert("end", identity)
            self.tests.configure(state="disabled" if state.loading or state.close_pending else "normal")
        self.tests.selection_clear(0, "end")
        for index, identity in enumerate(ids):
            if identity in state.selected_tests:
                self.tests.selection_set(index)
        self.plan_status.set(message)
        summary = "No plan selected. Enter a goal and explicitly choose Plan change."
        if state.plan_result is not None:
            plan = state.plan_result
            tests = plan["tests"]["selected_tests"]
            summary = (f"Status: {plan['status']}\nRun: {plan['run_id']}\n"
                       f"Proposal/action: {plan.get('proposed_action', {}).get('action_id', 'unavailable')}\n"
                       f"Goal: {plan['goal']}\nPrimary targets: {sum(row['role'] in {'primary_target', 'configuration_target'} for row in plan['implementation_targets'])}\n"
                       f"Affected/bound existing tests: {len(tests)}\n" + "\n".join(tests) +
                       f"\nUnresolved items (backend): {len(plan['unresolved_evidence'])}\n" +
                       ", ".join(row['type'] for row in plan['unresolved_evidence']) +
                       f"\nWarnings: {len(plan.get('warnings', []))}\n" +
                       ", ".join(row['type'] for row in plan.get('warnings', [])) +
                       f"\nIndex freshness: {plan['change_impact']['index_freshness']['status']}")
            if plan["status"] == "completed":
                summary += "\nReady for candidate validation in a later UI slice."
        self.plan_summary.configure(state="normal")
        self.plan_summary.delete("1.0", "end")
        self.plan_summary.insert("1.0", summary)
        self.plan_summary.configure(state="disabled")
