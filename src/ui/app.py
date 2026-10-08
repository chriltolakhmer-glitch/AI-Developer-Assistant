"""Tk main-loop controller and one worker for explicit backend operations."""

from pathlib import Path
from queue import Empty, Queue
from threading import Thread
from tkinter import filedialog

from .service import RepositoryService
from .state import ReadRequest, ViewState
from .views import ShellView


class Application:
    def __init__(self, root, service: RepositoryService, workspace: Path):
        self.root, self.service = root, service
        self.state = ViewState(workspace=str(workspace.expanduser().resolve()))
        self.results = Queue()
        self.worker: Thread | None = None
        self.closed = False
        root.title("AIDA — Repository status")
        root.geometry("980x620")
        root.minsize(780, 540)
        self.view = ShellView(root, self.open_repository, self.browse_repository, self.browse_workspace,
                              self.start_operation, self.inputs_changed,
                              self.confirm_approval, self.cancel_approval,
                              self.confirm_apply, self.cancel_apply, self.show_log)
        self.view.render(self.state)
        root.protocol("WM_DELETE_WINDOW", self.request_close)
        self.poll_id = root.after(40, self._poll)

    def open_repository(self):
        self.start_operation("read_repository")

    def inputs_changed(self):
        if self.view.rendering:
            return
        repository, workspace = self.view.repository.get(), self.view.workspace.get()
        same_session = (repository, workspace) == (self.state.repository, self.state.workspace)
        self.state.select(repository, workspace)
        self.state.planning_inputs(self.view.goal.get("1.0", "end-1c"),
                                   self.view.selected_test_ids() if same_session else ())
        self.state.candidate_inputs(self.view.candidate_path.get(), self.view.selected_plan.get())
        self.state.patch_inputs(self.view.selected_patch.get())
        self.state.decision_inputs(self.view.audit_label.get(), self.view.review_note.get() or None)
        self._execution_inputs()
        self.view.render(self.state)

    def _execution_inputs(self):
        for kind, selector in (('authorization', self.view.selected_authorization),
                               ('execution', self.view.selected_execution),
                               ('observation', self.view.selected_observation),
                               ('verification', self.view.selected_verification)):
            self.state.select_execution_input(kind, selector.get())

    def show_log(self, stream: str, offset: int = 0):
        self.start_operation('read_log', log_stream=stream, log_offset=offset)

    def start_operation(self, operation: str, *, log_stream: str = '', log_offset: int = 0):
        if self.closed or (self.worker is not None and self.worker.is_alive()):
            return
        self.state.planning_inputs(self.view.goal.get("1.0", "end-1c"), self.view.selected_test_ids())
        self.state.candidate_inputs(self.view.candidate_path.get(), self.view.selected_plan.get())
        self.state.patch_inputs(self.view.selected_patch.get())
        self.state.decision_inputs(self.view.audit_label.get(), self.view.review_note.get() or None)
        self._execution_inputs()
        if operation == 'apply' and self.state.pending_apply is None:
            decision = self.state.decision_result or {}
            run_id = self.state.selected_authorization_run_id
            if (run_id and decision.get('run_id') == run_id and decision.get('decision') == 'approve'
                    and decision.get('execution_authorized') is True
                    and decision.get('allowed_operation') == 'apply_exact_patch'
                    and decision.get('executed') is False and not self.state.application_result
                    and not self.state.apply_outcome_uncertain
                    and self.state.applied_authorization_run_id != run_id):
                self.state.pending_apply = (self.state.generation, self.state.repository, self.state.workspace, run_id)
                self.view.open_apply_confirmation(self.state.pending_apply, decision,
                                                  self.state.review_result, self.state.facts)
            self.view.render(self.state)
            return
        request = self.state.begin_operation(operation, self.view.repository.get(), self.view.workspace.get(),
                                             log_stream=log_stream, log_offset=log_offset)
        self.view.render(self.state)
        if request is not None:
            self.worker = Thread(target=self._read, args=(request,), name="aida-ui-operation", daemon=False)
            self.worker.start()

    def _read(self, request: ReadRequest):
        try:
            if request.operation == "plan":
                facts = self.service.plan(request.repository, request.workspace, goal=request.goal,
                                          top_k=request.top_k, expected_tests=request.expected_tests)
            elif request.operation == "import_candidate":
                facts = self.service.import_candidate(request.repository, request.workspace,
                    plan_run_id=request.plan_run_id, proposal=request.proposal, patch_path=request.patch_path)
            elif request.operation in {'review_patch', 'review_approval'}:
                facts = self.service.review_patch(request.repository, request.workspace, patch_run_id=request.patch_run_id)
            elif request.operation in {'decide_approve', 'decide_reject'}:
                facts = self.service.decide(request.repository, request.workspace,
                    patch_run_id=request.patch_run_id,
                    decision='approve' if request.operation == 'decide_approve' else 'reject',
                    approved_by=request.approved_by, note=request.note,
                    expected_branch=request.expected_branch if request.operation == 'decide_approve' else None)
            elif request.operation == 'apply':
                facts = self.service.apply(request.repository, request.workspace, request.authorization_run_id)
            elif request.operation == 'test':
                facts = self.service.test(request.repository, request.workspace, request.execution_run_id)
            elif request.operation == 'verify':
                facts = self.service.verify(request.repository, request.workspace,
                                            request.execution_run_id, request.observation_run_id)
            elif request.operation == 'evaluate':
                facts = self.service.evaluate(request.repository, request.workspace, request.verification_run_id)
            elif request.operation == 'read_log':
                facts = self.service.read_log(request.repository, request.workspace,
                                              request.observation_run_id, request.log_stream, request.log_offset)
            else:
                operation = {"read_repository": self.service.read_repository, "scan": self.service.scan,
                             "index": self.service.index, "catalog_tests": self.service.catalog_tests}[request.operation]
                facts = operation(request.repository, request.workspace)
            result = (request, facts, None)
        except BaseException as error:
            # Deliver unexpected worker termination too, so pending close can finish.
            result = (request, None, f"{type(error).__name__}: {error}")
        self.results.put(result)

    def _poll(self):
        while True:
            try:
                request, facts, error = self.results.get_nowait()
            except Empty:
                break
            try:
                completed = self.state.complete(request, facts, error)
                if completed and request.operation == 'review_approval' and error is None:
                    self.state.open_approval(request)
                self.view.render(self.state)
                if self.state.pending_approval and self.state.approval_matches():
                    self.view.open_confirmation(self.state.pending_approval, self.state.review_result)
            except (KeyError, TypeError, ValueError) as failure:
                self.state.facts = None
                self.state.plan_result = self.state.scan_result = self.state.index_result = self.state.test_catalog = None
                self.state.error = f"Cannot display repository result: {failure}"
                self.state.clear_candidate()
                self.view.render(self.state)
        if self.state.close_pending and not self.state.loading and not (self.worker and self.worker.is_alive()):
            self._destroy()
        elif not self.closed:
            self.poll_id = self.root.after(40, self._poll)

    def browse_repository(self):
        if self.state.loading or self.state.close_pending or self.state.pending_approval:
            return
        chosen = filedialog.askdirectory(parent=self.root, title="Choose an existing Git repository root", mustexist=True)
        if chosen:
            self.view.repository.set(chosen)
            self.open_repository()

    def browse_workspace(self):
        if self.state.loading or self.state.close_pending or self.state.pending_approval:
            return
        chosen = filedialog.askdirectory(parent=self.root, title="Choose external AIDA workspace", mustexist=True)
        if chosen:
            self.state.select(self.view.repository.get(), chosen)
            self.view.render(self.state)

    def request_close(self):
        self.cancel_approval()
        self.cancel_apply()
        if self.state.loading or (self.worker is not None and self.worker.is_alive()):
            self.state.close_pending = True
            self.view.render(self.state)
        else:
            self._destroy()

    def _destroy(self):
        self.closed = True
        self.root.after_cancel(self.poll_id)
        self.root.destroy()

    def cancel_approval(self):
        self.state.pending_approval = None
        self.view.dismiss_confirmation()
        if not self.closed:
            self.view.render(self.state)

    def confirm_approval(self, context):
        if context != self.state.pending_approval:
            return
        self.inputs_changed()
        if not self.state.approval_matches():
            self.state.pending_approval = None
            self.state.decision_error = 'Approval confirmation context changed; review explicitly again.'
            self.view.dismiss_confirmation()
            self.view.render(self.state)
            return
        self.start_operation('decide_approve')

    def cancel_apply(self):
        self.state.pending_apply = None
        self.view.dismiss_apply_confirmation()
        if not self.closed:
            self.view.render(self.state)

    def confirm_apply(self, context):
        if context != self.state.pending_apply:
            return
        self.view.dismiss_apply_confirmation()
        self.start_operation('apply')
