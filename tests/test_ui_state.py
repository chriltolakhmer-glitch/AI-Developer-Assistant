from dataclasses import fields
import unittest

from src.ui.state import ReadRequest, ViewState


class UIStateTests(unittest.TestCase):
    def test_initial_and_loading_state_prevent_duplicate_work(self):
        state = ViewState(workspace="workspace")
        self.assertEqual("", state.repository)
        self.assertFalse(state.loading)
        self.assertIsNone(state.facts)
        request = state.begin("repository", "workspace")
        self.assertTrue(state.loading)
        self.assertIsNotNone(request)
        self.assertIsNone(state.begin("another", "workspace"))

    def test_ready_error_and_changed_selection_clear_old_facts(self):
        state = ViewState()
        request = state.begin("repo", "workspace")
        facts = {"repository_path": "resolved-repo", "workspace_path": "resolved-workspace"}
        self.assertTrue(state.complete(request, facts, None))
        self.assertEqual(facts, state.facts)
        self.assertFalse(state.loading)
        state.select("other", "workspace")
        self.assertIsNone(state.facts)
        request = state.begin("other", "workspace")
        state.complete(request, None, "invalid Git root")
        self.assertEqual("invalid Git root", state.error)
        self.assertFalse(state.loading)

    def test_stale_session_and_request_tokens_cannot_replace_facts(self):
        state = ViewState()
        first = state.begin("first", "workspace")
        state.select("second", "workspace")
        self.assertFalse(state.complete(first, {"repository_path": "first", "workspace_path": "workspace"}, None))
        self.assertIsNone(state.facts)
        self.assertEqual("second", state.repository)
        second = state.begin("second", "workspace")
        self.assertFalse(state.complete(first, None, "stale error"))
        self.assertTrue(state.loading)
        facts = {"repository_path": "second", "workspace_path": "workspace"}
        self.assertTrue(state.complete(second, facts, None))
        self.assertEqual(facts, state.facts)

    def test_pending_close_prevents_requests_but_accepts_completion(self):
        state = ViewState()
        request = state.begin("repo", "workspace")
        state.close_pending = True
        self.assertIsNone(state.begin("repo", "workspace"))
        self.assertTrue(state.complete(request, None, "read failed"))
        self.assertTrue(state.close_pending)
        self.assertEqual("read failed", state.error)

    def test_empty_inputs_and_no_lifecycle_authority_fields(self):
        state = ViewState()
        self.assertIsNone(state.begin("", "workspace"))
        self.assertTrue(state.error)
        self.assertFalse(state.loading)
        self.assertFalse({"approved", "authorized", "applied", "tests_passed", "verified"} & {f.name for f in fields(state)})
