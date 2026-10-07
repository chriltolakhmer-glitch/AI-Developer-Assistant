"""Four-tab desktop shell; only repository browsing is functional."""

import tkinter as tk
from tkinter import ttk

from .state import ViewState


class ShellView:
    FIELD_LABELS = (
        ("repository_id", "Repository ID"), ("branch", "Branch"), ("head", "HEAD"),
        ("clean", "Working tree"), ("changes", "Change presence"),
        ("languages", "Supported languages"), ("index", "Index freshness"),
        ("aida_version", "AIDA version"), ("source_authority", "AIDA source authority"),
    )

    def __init__(self, root, open_repository, browse_repository, browse_workspace):
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=12)
        self.project = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.project, text="Project")
        for title in ("Plan & Review", "Run & Result", "History"):
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
        self.refresh_button = ttk.Button(self.project, text="Refresh", command=open_repository)
        self.refresh_button.grid(row=1, column=3, padx=8)
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
        self.controls = (self.repository_entry, self.workspace_entry, self.browse_repo_button,
                         self.open_button, self.browse_workspace_button, self.refresh_button)

    def render(self, state: ViewState):
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
            message = "Close pending — waiting for the current read to finish."
            if state.error:
                message += " " + state.error
        elif state.loading:
            message = "Reading repository status…"
        else:
            message = state.error or (state.facts["notice"] if state.facts else "Choose a repository. Opening/refreshing creates no AIDA evidence.")
        self.status.set(message)
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        self.details.insert("1.0", details)
        self.details.configure(state="disabled")
