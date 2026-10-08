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
                              self.start_operation, self.inputs_changed)
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
        self.view.render(self.state)

    def start_operation(self, operation: str):
        if self.closed or (self.worker is not None and self.worker.is_alive()):
            return
        self.state.planning_inputs(self.view.goal.get("1.0", "end-1c"), self.view.selected_test_ids())
        self.state.candidate_inputs(self.view.candidate_path.get(), self.view.selected_plan.get())
        request = self.state.begin_operation(operation, self.view.repository.get(), self.view.workspace.get())
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
                self.state.complete(request, facts, error)
                self.view.render(self.state)
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
        if self.state.loading or self.state.close_pending:
            return
        chosen = filedialog.askdirectory(parent=self.root, title="Choose an existing Git repository root", mustexist=True)
        if chosen:
            self.view.repository.set(chosen)
            self.open_repository()

    def browse_workspace(self):
        if self.state.loading or self.state.close_pending:
            return
        chosen = filedialog.askdirectory(parent=self.root, title="Choose external AIDA workspace", mustexist=True)
        if chosen:
            self.state.select(self.view.repository.get(), chosen)
            self.view.render(self.state)

    def request_close(self):
        if self.state.loading or (self.worker is not None and self.worker.is_alive()):
            self.state.close_pending = True
            self.view.render(self.state)
        else:
            self._destroy()

    def _destroy(self):
        self.closed = True
        self.root.after_cancel(self.poll_id)
        self.root.destroy()
