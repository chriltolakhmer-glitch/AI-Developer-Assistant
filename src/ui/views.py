"""Four-tab shell with explicit repository inventory/index and goal planning."""

import tkinter as tk
from tkinter import ttk, filedialog
from tkinter.scrolledtext import ScrolledText
import json
import hashlib

from .formatters import TARGET_ROLES, format_plan, role_label
from .state import ViewState
from .diff_view import DiffView


class ShellView:
    FIELD_LABELS = (
        ("repository_id", "Repository ID"), ("branch", "Branch"), ("head", "HEAD"),
        ("clean", "Working tree"), ("changes", "Change presence"),
        ("languages", "Supported languages"), ("index", "Index freshness (last Refresh)"),
        ("aida_version", "AIDA version"), ("source_authority", "AIDA source authority"),
    )

    def __init__(self, root, open_repository, browse_repository, browse_workspace, start_operation, inputs_changed,
                 confirm_approval, cancel_approval):
        self.rendering = False
        self.root = root
        self.confirm_approval, self.cancel_approval = confirm_approval, cancel_approval
        self.confirmation = None
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
        review_tabs = ttk.Notebook(self.plan)
        self.review_tabs = review_tabs
        review_tabs.pack(fill='both', expand=True)
        evidence_tab = ttk.Frame(review_tabs)
        evidence_canvas = tk.Canvas(evidence_tab, highlightthickness=0, takefocus=True)
        canvas_scroll = ttk.Scrollbar(evidence_tab, orient='vertical', command=evidence_canvas.yview)
        canvas_scroll.pack(side='right', fill='y')
        evidence_canvas.pack(side='left', fill='both', expand=True)
        evidence_canvas.configure(yscrollcommand=canvas_scroll.set)
        self.plan_evidence = ttk.Frame(evidence_canvas)
        evidence_window = evidence_canvas.create_window((0, 0), window=self.plan_evidence, anchor='nw')
        self.plan_evidence.bind('<Configure>', lambda _event: evidence_canvas.configure(scrollregion=evidence_canvas.bbox('all')))
        evidence_canvas.bind('<Configure>', lambda event: evidence_canvas.itemconfigure(evidence_window, width=event.width))
        evidence_canvas.bind('<Next>', lambda _event: evidence_canvas.yview_scroll(1, 'pages'))
        evidence_canvas.bind('<Prior>', lambda _event: evidence_canvas.yview_scroll(-1, 'pages'))
        self.candidate_frame = ttk.Frame(review_tabs, padding=6)
        review_tabs.add(evidence_tab, text='Planning evidence')
        review_tabs.add(self.candidate_frame, text='Candidate patch')
        self.selected_plan = tk.StringVar(root)
        self.candidate_path = tk.StringVar(root)
        candidate_inputs = ttk.Frame(self.candidate_frame)
        candidate_inputs.pack(fill='x')
        candidate_inputs.columnconfigure(1, weight=1)
        ttk.Label(candidate_inputs, text='Selected Phase 65 plan').grid(row=0, column=0, sticky='w')
        self.plan_selector = ttk.Combobox(candidate_inputs, textvariable=self.selected_plan, state='readonly')
        self.plan_selector.grid(row=0, column=1, columnspan=3, sticky='ew')
        ttk.Label(candidate_inputs, text='External UTF-8 patch file').grid(row=1, column=0, sticky='w')
        self.candidate_entry = ttk.Entry(candidate_inputs, textvariable=self.candidate_path)
        self.candidate_entry.grid(row=1, column=1, sticky='ew')
        self.candidate_browse = ttk.Button(candidate_inputs, text='Browse…', command=self._browse_candidate)
        self.candidate_browse.grid(row=1, column=2, padx=4)
        self.candidate_validate = ttk.Button(candidate_inputs, text='Validate imported patch', command=lambda: start_operation('import_candidate'))
        self.candidate_validate.grid(row=1, column=3)
        ttk.Label(self.candidate_frame, text='Explicit Phase 67 records external workspace evidence. Target source remains unchanged.').pack(anchor='w')
        self.candidate_status = tk.StringVar(root)
        ttk.Label(self.candidate_frame, textvariable=self.candidate_status, wraplength=900, justify='left').pack(anchor='w')
        candidate_panes = ttk.Panedwindow(self.candidate_frame, orient='vertical')
        candidate_panes.pack(fill='both', expand=True)
        scope_frame = ttk.Frame(candidate_panes)
        self.candidate_details = ScrolledText(scope_frame, height=4, wrap='word', state='disabled')
        self.candidate_details.pack(fill='both', expand=True)
        candidate_panes.add(scope_frame, weight=1)
        self.diff_view = DiffView(candidate_panes)
        candidate_panes.add(self.diff_view, weight=2)
        self.human_frame = ttk.Frame(review_tabs, padding=6)
        review_tabs.add(self.human_frame, text='Human decision')
        self.selected_patch = tk.StringVar(root)
        self.audit_label = tk.StringVar(root, value='local-developer')
        self.review_note = tk.StringVar(root)
        self.human_frame.columnconfigure(1, weight=1)
        self.human_frame.rowconfigure(6, weight=1)
        ttk.Label(self.human_frame, text='Selected Phase 67 patch run').grid(row=0, column=0, sticky='w')
        self.patch_selector = ttk.Combobox(self.human_frame, textvariable=self.selected_patch, state='readonly')
        self.patch_selector.grid(row=0, column=1, sticky='ew')
        ttk.Label(self.human_frame, text='Audit label (local label, not authentication)').grid(row=1, column=0, sticky='w')
        self.audit_entry = ttk.Entry(self.human_frame, textvariable=self.audit_label)
        self.audit_entry.grid(row=1, column=1, sticky='ew')
        ttk.Label(self.human_frame, text='Optional review note').grid(row=2, column=0, sticky='w')
        self.note_entry = ttk.Entry(self.human_frame, textvariable=self.review_note)
        self.note_entry.grid(row=2, column=1, sticky='ew')
        decision_buttons = ttk.Frame(self.human_frame)
        decision_buttons.grid(row=3, column=0, columnspan=2, sticky='w', pady=4)
        self.review_button = ttk.Button(decision_buttons, text='Review canonical patch', command=lambda: start_operation('review_patch'))
        self.review_button.pack(side='left')
        self.approve_button = ttk.Button(decision_buttons, text='APPROVE', command=lambda: start_operation('review_approval'))
        self.approve_button.pack(side='left', padx=16)
        self.reject_button = ttk.Button(decision_buttons, text='REJECT', command=lambda: start_operation('decide_reject'))
        self.reject_button.pack(side='left')
        ttk.Label(self.human_frame, text='REJECT records an external Phase 68 decision. Review records nothing. Neither action applies a patch or runs tests.\nDistinct historical decisions remain immutable; a later rejection does not revoke an earlier approval.', wraplength=890).grid(row=4, column=0, columnspan=2, sticky='w')
        self.decision_status = tk.StringVar(root)
        ttk.Label(self.human_frame, textvariable=self.decision_status, wraplength=890).grid(row=5, column=0, columnspan=2, sticky='w', pady=4)
        self.decision_details = ScrolledText(self.human_frame, height=10, wrap='word', state='disabled')
        self.decision_details.grid(row=6, column=0, columnspan=2, sticky='nsew')
        self.plan_header = tk.StringVar(root, value="No plan selected.")
        ttk.Label(self.plan_evidence, textvariable=self.plan_header, justify="left", wraplength=1000).pack(anchor="w", fill="x", pady=4)
        self.raw_detail_button = ttk.Button(self.plan_evidence, text="View raw plan details", command=self.open_raw_plan)
        self.raw_detail_button.pack(anchor="w", pady=2)
        self._current_plan = None
        self.raw_detail_window = None
        target_frame = ttk.LabelFrame(self.plan_evidence, text="Implementation targets", padding=5)
        target_frame.pack(fill="x", pady=4)
        target_frame.columnconfigure(0, weight=1)
        target_frame.columnconfigure(1, weight=2)
        target_frame.rowconfigure(0, weight=1)
        self.target_tree = ttk.Treeview(target_frame, columns=("role", "target"), show="headings", height=5)
        self.target_tree.heading("role", text="Role")
        self.target_tree.heading("target", text="File / qualified symbol")
        self.target_tree.column("role", width=240, stretch=False)
        self.target_tree.column("target", width=440, stretch=True)
        self.target_tree.grid(row=0, column=0, sticky="nsew")
        target_scroll = ttk.Scrollbar(target_frame, orient="vertical", command=self.target_tree.yview)
        target_scroll.grid(row=0, column=0, sticky="nse")
        self.target_tree.configure(yscrollcommand=target_scroll.set)
        self.target_detail = tk.Text(target_frame, height=7, wrap="word", state="disabled")
        self.target_detail.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self.target_tree.bind("<<TreeviewSelect>>", self._target_selected)
        evidence_frame = ttk.LabelFrame(self.plan_evidence, text="Plan evidence", padding=5)
        evidence_frame.pack(fill="both", expand=True, pady=4)
        evidence_frame.rowconfigure(0, weight=1)
        evidence_frame.columnconfigure(0, weight=1)
        self.plan_summary = tk.Text(evidence_frame, height=12, wrap="word", state="disabled")
        self.plan_summary.grid(row=0, column=0, sticky="nsew")
        evidence_scroll = ttk.Scrollbar(evidence_frame, orient="vertical", command=self.plan_summary.yview)
        evidence_scroll.grid(row=0, column=1, sticky="ns")
        self.plan_summary.configure(yscrollcommand=evidence_scroll.set)
        self.controls = (self.repository_entry, self.workspace_entry, self.browse_repo_button,
                         self.open_button, self.browse_workspace_button, self.refresh_button,
                         self.scan_button, self.index_button, self.goal, self.catalog_button, self.tests, self.plan_button)
        self.controls += (self.raw_detail_button, self.candidate_entry, self.candidate_browse, self.candidate_validate)
        self.controls += (self.audit_entry, self.note_entry, self.review_button, self.approve_button, self.reject_button)
        self.selected_patch.trace_add('write', lambda *_: inputs_changed())
        self.audit_label.trace_add('write', lambda *_: inputs_changed())
        self.review_note.trace_add('write', lambda *_: inputs_changed())
        self.selected_plan.trace_add('write', lambda *_: inputs_changed())
        self.candidate_path.trace_add('write', lambda *_: inputs_changed())
        self.repository.trace_add("write", lambda *_: inputs_changed())
        self.workspace.trace_add("write", lambda *_: inputs_changed())
        self.goal.bind("<<Modified>>", lambda *_: self._goal_changed(inputs_changed))
        self.tests.bind("<<ListboxSelect>>", lambda *_: inputs_changed())

    def _goal_changed(self, callback):
        if self.goal.edit_modified():
            self.goal.edit_modified(False)
            callback()

    def _browse_candidate(self):
        chosen = filedialog.askopenfilename(parent=self.plan, title='Select external unified diff', filetypes=[('Patch files', '*.diff *.patch'), ('All files', '*')])
        if chosen:
            self.candidate_path.set(chosen)

    def _render_candidate(self, state):
        plan = state.plan_result or {}
        self.plan_selector.configure(values=(plan['run_id'],) if plan.get('run_id') else (),
            state='disabled' if state.loading or state.close_pending or state.pending_approval else 'readonly')
        self.selected_plan.set(state.selected_plan_run_id)
        self.candidate_path.set(state.candidate_path)
        result = state.review_result['draft'] if state.review_result else state.candidate_result
        if state.review_error or (state.loading and state.operation in {'review_patch', 'review_approval'}):
            result = None
        status = 'Select a completed plan, choose an external candidate, then explicitly validate.'
        status += f"\nSelected Phase 65 run: {state.selected_plan_run_id or 'unavailable'} | Phase 66 action: {plan.get('proposed_action', {}).get('action_id', 'unavailable')}"
        if state.operation == 'import_candidate' and state.loading:
            status = 'Running Phase 67 validation…'
        elif state.error:
            status = state.error
            if state.operation == 'import_candidate':
                status += '\nPhase 67 expects direct --- / +++ unified-diff file headers; unsupported metadata is not removed.'
        elif result:
            status = f"Phase 67: {result.get('status', 'unavailable')}"
            status += (' | Human review pending' if result.get('status') == 'draft' else ' | No accepted patch body')
        self.candidate_status.set(status)
        body = ''
        detail = ''
        if result:
            detail = self._row_text({key: value for key, value in result.items()
                if key not in {'patch_text', 'target_paths', 'candidate_paths', 'allowed_symbol_scope', 'candidate_symbol_scope'}})
            detail += '\n\nAllowed by Phase 66 / Phase 67 evidence\n' + self._row_text({key: result[key] for key in ('target_paths', 'allowed_symbol_scope') if key in result})
            detail += '\n\nActually present in validated candidate\n' + self._row_text({key: result[key] for key in ('candidate_paths', 'candidate_symbol_scope') if key in result})
            if result.get('status') == 'draft':
                body = result.get('patch_text', '')
                if state.review_result:
                    detail += '\nCanonical patch review digest: ' + state.review_result['patch_sha256']
                else:
                    detail += '\nDisplay-only patch SHA-256: ' + hashlib.sha256(body.encode('utf-8')).hexdigest()
        self._replace_text(self.candidate_details, detail)
        self.diff_view.show(body)

    def _render_decision(self, state):
        locked = state.loading or state.close_pending or state.pending_approval is not None
        candidate = state.candidate_result or {}
        self.patch_selector.configure(values=(candidate['run_id'],) if candidate.get('run_id') else (),
                                      state='disabled' if locked else 'readonly')
        self.selected_patch.set(state.selected_patch_run_id)
        submitted = state.decision_result is not None or state.decision_error is not None
        selected = bool(state.selected_patch_run_id)
        self.review_button.configure(state='disabled' if locked or not selected else 'normal')
        self.approve_button.configure(state='disabled' if locked or not selected or submitted or candidate.get('status') != 'draft' else 'normal')
        self.reject_button.configure(state='disabled' if locked or not selected or submitted else 'normal')
        message = 'Select the exact Phase 67 run. Approval reloads canonical evidence before confirmation.'
        details = ''
        if state.review_result:
            review = state.review_result
            details = 'Canonical PatchDraft\n' + self._row_text({key: value for key, value in review['draft'].items() if key != 'patch_text'})
            details += '\n\nCanonical patch review digest: ' + review['patch_sha256']
            details += '\nCurrent repository facts\n' + self._row_text(review['facts'])
            details += '\nBound existing tests: ' + json.dumps(review['bound_tests'] if review['bound_tests'] is not None else 'Unavailable', ensure_ascii=False)
            details += '\nLinked plan evidence: ' + (review['linked_plan_error'] or
                ('Available' if review['bound_tests'] is not None else 'Unavailable'))
            details += '\nPlan warnings\n' + json.dumps(review['plan_warnings'], ensure_ascii=False)
            message = 'Canonical review loaded. Exact stored diff is in Candidate patch. Review created no run.'
        if state.pending_approval:
            message = 'Approval confirmation pending. No decision has been recorded by this review.'
        if state.decision_result is not None:
            result = state.decision_result
            message = ('APPROVED FOR FUTURE EXACT PATCH APPLICATION — NOT APPLIED' if result.get('decision') == 'approve'
                       else 'PATCH REJECTED — NO EXECUTION AUTHORITY' if result.get('decision') == 'reject' else 'Phase 68 result returned')
            details += '\n\nPhase 68 AuthorizationRecord (literal backend values)\n' + self._row_text(result)
            details += '\nApproval authorizes only a later explicit Phase 69 operation with the exact same binding. No arbitrary edits, automatic application or target test execution.'
        if state.review_error:
            message = state.review_error
        if state.decision_error:
            message = state.decision_error + '\nDecision returned no record; final persistence outcome is unconfirmed. Review explicitly before another deliberate submission.'
        if state.loading and state.operation in {'review_patch', 'review_approval', 'decide_approve', 'decide_reject'}:
            message = 'Running ' + state.operation + '…'
        self.decision_status.set(message)
        self._replace_text(self.decision_details, details)
        if self.confirmation and (not state.pending_approval or not state.approval_matches()):
            self.dismiss_confirmation()

    def open_confirmation(self, context, review):
        if self.confirmation is not None:
            return
        dialog = tk.Toplevel(self.root)
        self.confirmation = dialog
        dialog.title('Confirm exact patch approval')
        dialog.geometry('780x620')
        dialog.transient(self.root)
        ttk.Label(dialog, text='You are approving this exact stored patch for possible future application. No files will be changed and no tests will run now.', wraplength=740, padding=10).pack(fill='x')
        self.confirmation_details = ScrolledText(dialog, wrap='word', height=20)
        self.confirmation_details.pack(fill='both', expand=True, padx=10)
        draft = review['draft']
        text = self._row_text({key: value for key, value in draft.items() if key != 'patch_text'})
        text += '\nRecorded HEAD: ' + str(draft['current_commit']) + '\nCurrent HEAD: ' + str(review['facts']['head'])
        text += '\nCanonical patch review digest: ' + review['patch_sha256']
        text += '\nBound existing tests: ' + json.dumps(review['bound_tests'] if review['bound_tests'] is not None else 'Unavailable', ensure_ascii=False)
        text += '\nPlan warnings: ' + json.dumps(review['plan_warnings'], ensure_ascii=False)
        text += '\nAudit label: ' + context.approved_by + '\nOptional note: ' + (context.note or '')
        self._replace_text(self.confirmation_details, text)
        buttons = ttk.Frame(dialog, padding=10)
        buttons.pack(fill='x')
        self.confirm_button = ttk.Button(buttons, text='Confirm approval', command=lambda: self.confirm_approval(context))
        self.confirm_button.pack(side='left')
        self.cancel_button = ttk.Button(buttons, text='Cancel', command=self.cancel_approval)
        self.cancel_button.pack(side='right')
        dialog.protocol('WM_DELETE_WINDOW', self.cancel_approval)
        dialog.grab_set()
        self.cancel_button.focus_set()

    def dismiss_confirmation(self):
        if self.confirmation is not None:
            self.confirmation.grab_release()
            self.confirmation.destroy()
            self.confirmation = None

    @staticmethod
    def _replace_text(widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def _target_selected(self, _event=None):
        selection = self.target_tree.selection()
        target = self._target_rows.get(selection[0]) if selection else None
        self._replace_text(self.target_detail, self._row_text(target) if target else "Select a target to inspect its Phase 65 evidence.")

    def open_raw_plan(self):
        if self._current_plan is None:
            return
        if self.raw_detail_window is not None and self.raw_detail_window.winfo_exists():
            self.raw_detail_window.lift()
            return
        window = tk.Toplevel(self.plan)
        window.title("Read-only Phase 65 plan detail")
        window.geometry("760x560")
        window.rowconfigure(0, weight=1)
        window.columnconfigure(0, weight=1)
        detail = tk.Text(window, wrap="none", state="normal")
        detail.grid(row=0, column=0, sticky="nsew")
        vertical = ttk.Scrollbar(window, orient="vertical", command=detail.yview)
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal = ttk.Scrollbar(window, orient="horizontal", command=detail.xview)
        horizontal.grid(row=1, column=0, sticky="ew")
        detail.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        detail.insert("1.0", json.dumps(self._current_plan, ensure_ascii=False, indent=2, sort_keys=True))
        detail.configure(state="disabled")
        window.protocol("WM_DELETE_WINDOW", lambda: self._close_raw_plan(window))
        self.raw_detail_window = window

    def _close_raw_plan(self, window):
        if window.winfo_exists():
            window.destroy()
        if self.raw_detail_window is window:
            self.raw_detail_window = None

    @staticmethod
    def _row_text(row):
        if not isinstance(row, dict):
            return ""
        return "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False, sort_keys=True)}"
                         for key, value in row.items())

    @staticmethod
    def _section(title, rows):
        lines = [title]
        if not rows:
            lines.append("  None recorded.")
        for row in rows:
            if isinstance(row, dict):
                lines.append("  " + ShellView._row_text(row).replace("\n", "\n  "))
            else:
                lines.append("  " + json.dumps(row, ensure_ascii=False))
            lines.append("")
        return "\n".join(lines)

    def _render_plan(self, plan):
        if plan is not self._current_plan and self.raw_detail_window is not None:
            self._close_raw_plan(self.raw_detail_window)
        self._current_plan = plan
        self.target_tree.delete(*self.target_tree.get_children())
        self._target_rows = {}
        if plan is None:
            self.plan_header.set("No plan selected. Enter a goal and explicitly choose Plan change.")
            self._replace_text(self.plan_summary, "Plan evidence appears here after an explicit Plan operation.")
            self._replace_text(self.target_detail, "No target selected.")
            return

        evidence = format_plan(plan)
        action = evidence["proposed_action"]
        repository = evidence["repository"]
        repository = repository if isinstance(repository, dict) else {}
        impact = evidence["change_impact"]
        repo_impact = impact.get("repository") if isinstance(impact.get("repository"), dict) else {}
        freshness = evidence["index_freshness"]
        tests = evidence["selected_tests"]
        status = evidence["status"]
        status_description = {
            "completed": "Completed planning result",
            "limited": "Planning result with insufficient evidence",
            "manual_review_required": "Planning requires manual review",
        }.get(status)
        header_fields = [
            f"Plan status: {status if status is not None else 'unavailable'}" +
            (f" ({status_description})" if status_description else ""),
            f"Goal: {evidence['goal'] if evidence['goal'] is not None else 'unavailable'}",
            f"Phase 65 run ID: {evidence['run_id'] if evidence['run_id'] is not None else 'unavailable'}",
            f"Phase 66 action ID: {action.get('action_id', 'unavailable')}",
            f"Repository identity: {repo_impact.get('repository_id', repository.get('repository_id', 'unavailable'))}",
            f"Recorded commit: {repo_impact.get('current_commit', 'unavailable')}",
            f"Source snapshot: {repo_impact.get('working_tree_sha256', 'unavailable')}",
            f"Index freshness: {freshness.get('status', 'unavailable')}",
            f"Selected/bound existing tests: {len(tests)}",
        ]
        self.plan_header.set("\n".join(header_fields))

        ordered_roles = [role for role in TARGET_ROLES if role in evidence["targets_by_role"]]
        ordered_roles.extend(role for role in evidence["targets_by_role"] if role not in ordered_roles)
        target_lines = ["Implementation targets - exact backend roles; counts are role-specific."]
        for role in ordered_roles:
            rows = evidence["targets_by_role"][role]
            target_lines.append(f"{role_label(role)}: {len(rows)}")
            for index, row in enumerate(rows):
                target_id = f"{role}:{index}"
                path = row.get("file_path", "unavailable")
                symbol = row.get("qualified_symbol", "unavailable")
                self._target_rows[target_id] = row
                self.target_tree.insert("", "end", iid=target_id, values=(role_label(role), f"{path} :: {symbol}"))
        sections = ["\n".join(target_lines)]

        selection = evidence["test_selection"]
        selection_rows = []
        if isinstance(selection, dict):
            selection_rows.append({key: selection[key] for key in selection if key != "evidence"})
            selection_rows.extend(evidence["test_evidence"])
            selection_rows.extend({"uncertainty": item} for item in evidence["test_uncertainty"])
        sections.append(self._section("Existing test evidence", evidence["selected_tests"]))
        sections.append("Selection status and binding evidence\n" + (self._section("Selection details", selection_rows) if selection_rows else "  No expected-test selection details recorded.\n"))
        sections.append("  Existing regression evidence does not necessarily prove the new requested behavior.")

        preserved = evidence["preserved_behavior"]
        sections.append(self._section("Preserved behavior", preserved) if preserved else
                        "Preserved behavior\n  No preserved behavior was established by current evidence.")
        sections.append(self._section("Blocking / unresolved evidence", evidence["unresolved_evidence"]))
        sections.append(self._section("Warnings / informational evidence", evidence["warnings"]))
        if evidence["retained_leaf_proofs"]:
            proof_intro = "Retained-leaf backend evidence\n  The parent container exceeded the context limit, but the exact affected leaf was retained and bound by backend evidence.\n"
            sections.append(proof_intro + self._section("Retained-leaf proof details", evidence["retained_leaf_proofs"]))
        else:
            sections.append("Retained-leaf backend evidence\n  No recognized retained-leaf proof is present; warnings and unresolved evidence above show the backend records.")

        steps = evidence["implementation_steps"]
        sections.append("Proposed implementation steps - no source changes have been made.\n" +
                        self._section("Ordered advisory steps", steps))
        sections.append("Proposed Action\n" + self._row_text(action) +
                        "\n\nThis is a review-only proposal contract. It is not approval or execution authority.")
        proposed_scope = {key: action[key] for key in ("target_paths", "target_symbols") if key in action}
        if proposed_scope:
            sections.append("Proposed scope (from Phase 66)\n" + self._row_text(proposed_scope))
        sections.append(self._section("Recommended validation (advisory; not executed)", evidence["recommended_validation"]))
        sections.append(self._section("Limitations", evidence["limitations"]))
        self._replace_text(self.plan_summary, "\n\n".join(sections))
        children = self.target_tree.get_children()
        if children:
            self.target_tree.selection_set(children[0])
            self.target_tree.focus(children[0])
            self._target_selected()
        else:
            self._replace_text(self.target_detail, "No implementation targets were recorded.")

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
            control.configure(state="disabled" if state.loading or state.close_pending or state.pending_approval else "normal")
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
            self.tests.configure(state="disabled" if state.loading or state.close_pending or state.pending_approval else "normal")
        self.tests.selection_clear(0, "end")
        for index, identity in enumerate(ids):
            if identity in state.selected_tests:
                self.tests.selection_set(index)
        self.plan_status.set(message)
        self._render_plan(state.plan_result)
        try:
            self._render_candidate(state)
        except (KeyError, TypeError, ValueError, tk.TclError) as failure:
            result = (state.review_result or {}).get('draft', state.candidate_result or {}) if not state.review_error else {}
            self.candidate_status.set(f"Phase 67: {result.get('status', 'unavailable')} | Presentation error: {failure}")
            self._replace_text(self.candidate_details, json.dumps({key: value for key, value in result.items() if key != 'patch_text'}, ensure_ascii=False, indent=2))
            body = result.get('patch_text', '') if result.get('status') == 'draft' else ''
            self.diff_view.show(body if isinstance(body, str) else '')
        try:
            self._render_decision(state)
        except (KeyError, TypeError, ValueError, tk.TclError) as failure:
            # Presentation failures cannot erase an actual backend decision.
            state.pending_approval = None
            self.dismiss_confirmation()
            self.decision_status.set(f'Phase 68 presentation error: {failure}')
            self._replace_text(self.decision_details, json.dumps(state.decision_result or state.review_result,
                                                               ensure_ascii=False, indent=2))
