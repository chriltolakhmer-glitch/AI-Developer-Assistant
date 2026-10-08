"""Display state only; no persisted evidence or execution authority."""

from dataclasses import dataclass, field
from typing import Any
from copy import deepcopy


@dataclass(frozen=True)
class ReadRequest:
    generation: int
    token: int
    repository: str
    workspace: str
    operation: str = "read_repository"
    goal: str = ""
    expected_tests: tuple[str, ...] = ()
    top_k: int = 10
    plan_run_id: str = ""
    proposal: dict[str, Any] | None = None
    patch_path: str = ""
    patch_run_id: str = ""
    approved_by: str = "local-developer"
    note: str | None = None
    expected_branch: str | None = None


@dataclass(frozen=True)
class ApprovalContext:
    generation: int
    repository: str
    workspace: str
    patch_run_id: str
    patch_id: str
    patch_sha256: str
    current_commit: str
    working_tree_sha256: str
    branch_reference: str
    approved_by: str
    note: str | None


@dataclass
class ViewState:
    repository: str = ""
    workspace: str = ""
    loading: bool = False
    facts: dict[str, Any] | None = None
    error: str | None = None
    generation: int = 0
    token: int = 0
    close_pending: bool = False
    goal: str = ""
    selected_tests: tuple[str, ...] = ()
    scan_result: dict[str, Any] | None = None
    index_result: dict[str, Any] | None = None
    test_catalog: dict[str, list[str]] | None = None
    plan_result: dict[str, Any] | None = None
    candidate_path: str = ""
    selected_plan_run_id: str = ""
    candidate_result: dict[str, Any] | None = None
    selected_patch_run_id: str = ""
    review_result: dict[str, Any] | None = None
    review_error: str | None = None
    decision_result: dict[str, Any] | None = None
    decision_error: str | None = None
    pending_approval: ApprovalContext | None = None
    approved_by: str = "local-developer"
    note: str | None = None
    operation: str | None = None
    _active: ReadRequest | None = field(default=None, repr=False)

    def clear_candidate(self):
        self.candidate_result = None
        self.selected_patch_run_id = ""
        self.clear_review()

    def clear_review(self):
        self.review_result = self.decision_result = None
        self.review_error = self.decision_error = None
        self.pending_approval = None

    def patch_inputs(self, patch_run_id: str):
        if patch_run_id != (self.candidate_result or {}).get('run_id'):
            patch_run_id = ''
        if patch_run_id != self.selected_patch_run_id:
            self.generation += 1
            self.selected_patch_run_id = patch_run_id
            self.clear_review()

    def decision_inputs(self, approved_by: str, note: str | None):
        if (approved_by, note) != (self.approved_by, self.note):
            self.approved_by, self.note = approved_by, note
            self.pending_approval = None

    @staticmethod
    def branch_reference(facts):
        return 'HEAD' if facts.get('detached_head') else 'refs/heads/' + str(facts.get('branch'))

    def approval_matches(self):
        pending = self.pending_approval
        review = self.review_result or {}
        draft = review.get('draft', {})
        return pending is not None and pending == ApprovalContext(
            self.generation, self.repository, self.workspace, self.selected_patch_run_id,
            draft.get('patch_id'), review.get('patch_sha256'), draft.get('current_commit'),
            draft.get('working_tree_sha256'), self.branch_reference(review.get('facts', {})),
            self.approved_by, self.note)

    def open_approval(self, request):
        review = self.review_result
        if (not review or self.close_pending or request.generation != self.generation
                or request.patch_run_id != self.selected_patch_run_id
                or (request.approved_by, request.note) != (self.approved_by, self.note)):
            return False
        draft = review['draft']
        if draft['status'] != 'draft':
            self.review_error = 'Blocked PatchDraft cannot be approved; replan and redraft.'
            return False
        if not review['state_matches']:
            self.review_error = 'Repository state differs from the PatchDraft; replan and redraft.'
            return False
        if request.expected_branch != self.branch_reference(review['facts']):
            self.clear_review()
            self.review_error = 'Repository branch context changed; reload the session and review explicitly.'
            return False
        self.pending_approval = ApprovalContext(
            self.generation, self.repository, self.workspace, request.patch_run_id,
            draft['patch_id'], review['patch_sha256'], draft['current_commit'],
            draft['working_tree_sha256'], request.expected_branch, request.approved_by, request.note)
        return True

    def candidate_inputs(self, path: str, plan_run_id: str):
        if not self.plan_result or plan_run_id != self.plan_result.get('run_id'):
            plan_run_id = ''
        if (path, plan_run_id) != (self.candidate_path, self.selected_plan_run_id):
            self.generation += 1
            self.candidate_path, self.selected_plan_run_id = path, plan_run_id
            self.clear_candidate()
            self.error = None

    def select(self, repository: str, workspace: str) -> None:
        if (repository, workspace) != (self.repository, self.workspace):
            self.generation += 1
            self.repository, self.workspace = repository, workspace
            self.facts, self.error = None, None
            self.scan_result = self.index_result = self.test_catalog = self.plan_result = None
            self.selected_tests = ()
            self.selected_plan_run_id = ""
            self.clear_candidate()

    def planning_inputs(self, goal: str, tests: tuple[str, ...]) -> None:
        if (goal, tests) != (self.goal, self.selected_tests):
            self.generation += 1
            self.goal, self.selected_tests = goal, tests
            self.plan_result = None
            self.selected_plan_run_id = ""
            self.clear_candidate()

    def begin(self, repository: str, workspace: str) -> ReadRequest | None:
        if self.loading or self.close_pending or self.pending_approval:
            return None
        self.select(repository, workspace)
        self.facts, self.error = None, None
        self.plan_result = None
        self.selected_plan_run_id = ""
        self.clear_candidate()
        if not repository.strip() or not workspace.strip():
            self.error = "Choose or enter both a repository root and an external workspace."
            return None
        self.token += 1
        self.loading = True
        self.operation = "read_repository"
        self._active = ReadRequest(self.generation, self.token, repository, workspace)
        return self._active

    def begin_operation(self, operation: str, repository: str, workspace: str) -> ReadRequest | None:
        if operation == "read_repository":
            return self.begin(repository, workspace)
        if self.loading or self.close_pending or (self.pending_approval and operation != 'decide_approve'):
            return None
        if operation not in {"scan", "index", "catalog_tests", "plan", "import_candidate",
                             "review_patch", "review_approval", "decide_approve", "decide_reject"}:
            raise ValueError("Unsupported UI operation")
        self.select(repository, workspace)
        self.error = None
        if self.facts is None:
            self.error = "Open the selected repository before requesting an operation."
            return None
        if operation in {'review_patch', 'review_approval', 'decide_approve', 'decide_reject'}:
            if not self.selected_patch_run_id or self.selected_patch_run_id != (self.candidate_result or {}).get('run_id'):
                self.clear_review()
                self.review_error = 'Select the exact Phase 67 patch run before review or decision.'
                return None
            if operation == 'decide_approve' and not self.approval_matches():
                self.pending_approval = None
                self.decision_error = 'Approval confirmation context changed; review explicitly again.'
                return None
            if operation.startswith('review_'):
                self.clear_review()
            elif self.decision_result is not None or self.decision_error is not None:
                self.error = 'A decision was already submitted. Review canonical patch explicitly before another deliberate decision.'
                return None
            self.review_error = self.decision_error = None
        if operation == "plan" and not self.goal.strip():
            self.error = "Development goal must be nonempty text."
            return None
        if operation in {"scan", "index", "plan"}:
            self.plan_result = None
            self.selected_plan_run_id = ""
            self.clear_candidate()
        if operation == "import_candidate":
            self.clear_candidate()
            plan = self.plan_result or {}
            proposal = plan.get("proposed_action")
            if (plan.get("status") != "completed" or not self.selected_plan_run_id
                    or self.selected_plan_run_id != plan.get("run_id")
                    or not isinstance(proposal, dict) or not proposal.get("action_id")
                    or not self.candidate_path):
                self.error = "Select a completed Phase 65 plan and an external candidate file. Backend validation remains required."
                return None
        if operation == "scan":
            self.scan_result = None
        if operation == "index":
            self.index_result = None
        self.token += 1
        self.loading, self.operation = True, operation
        self._active = ReadRequest(self.generation, self.token, repository, workspace,
                                   operation, self.goal, self.selected_tests,
                                   plan_run_id=self.selected_plan_run_id,
                                   proposal=deepcopy(self.plan_result.get("proposed_action")) if operation == "import_candidate" else None,
                                   patch_path=self.candidate_path,
                                   patch_run_id=self.selected_patch_run_id, approved_by=self.approved_by, note=self.note,
                                   expected_branch=(self.pending_approval.branch_reference if self.pending_approval
                                                    else self.branch_reference(self.facts)))
        if operation == 'decide_approve':
            self.pending_approval = None
        return self._active

    def complete(self, request: ReadRequest, facts: dict[str, Any] | None, error: str | None) -> bool:
        if request != self._active:
            return False
        self.loading, self._active = False, None
        if request.generation != self.generation:
            return False
        self.error = error
        if request.operation in {'review_patch', 'review_approval'}:
            self.review_result = facts
            self.review_error = error
            return True
        if request.operation in {'decide_approve', 'decide_reject'}:
            self.decision_result = facts
            self.decision_error = error
            if error:
                self.review_result = None
                self.review_error = error
            return True
        if request.operation != "read_repository":
            if facts is not None:
                field_name = {"scan": "scan_result", "index": "index_result",
                              "catalog_tests": "test_catalog", "plan": "plan_result",
                              "import_candidate": "candidate_result"}[request.operation]
                if request.operation == "plan":
                    self.selected_plan_run_id = ""
                    self.clear_candidate()
                setattr(self, field_name, facts)
            return True
        self.facts = facts
        if facts is not None:
            self.repository = facts["repository_path"]
            self.workspace = facts["workspace_path"]
        return True
