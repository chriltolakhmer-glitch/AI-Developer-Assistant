import unittest
import tkinter as tk
from unittest.mock import patch
from src.ui.diff_view import DiffView, line_labels


class DiffViewTests(unittest.TestCase):
    def test_multi_file_line_numbers_context_markers_and_no_newline(self):
        text = '--- a/a.py\n+++ b/a.py\n@@ -2,2 +2,2 @@\n context\n-old\n+new\n\\ No newline at end of file\n--- a/b.py\n+++ b/b.py\n@@ -4 +4 @@\n-x\n+<script>alert(1)</script>'
        labels = line_labels(text)
        self.assertEqual(['File', 'File', 'Hunk', '    2     2', '    3      ', '          3', '', 'File', 'File', 'Hunk', '    4      ', '          4'], labels)

    def test_readonly_raw_fidelity_tags_scroll_and_literal_content(self):
        root = tk.Tk(); self.addCleanup(root.destroy); root.withdraw()
        view = DiffView(root)
        text = '--- a/a.py\r\n+++ b/a.py\r\n@@ -1 +1 @@\r\n-old\r\n+<script>' + 'x' * 2000 + '</script>\r\n\\ No newline at end of file'
        text += '\n--- a/b.py\n+++ b/b.py\n@@ -2 +2 @@\n-second\n+complete second hunk\n'
        view.show(text)
        self.assertEqual(text, view.text.get('1.0', 'end-1c'))
        self.assertEqual(text, view.stored_text)
        self.assertEqual('disabled', view.text.cget('state'))
        self.assertTrue(view.text.tag_ranges('addition'))
        self.assertTrue(view.text.tag_ranges('deletion'))
        self.assertTrue(view.text.tag_ranges('heading'))
        self.assertTrue(view.text.tag_ranges('hunk'))
        self.assertEqual(8, len(view.text.tag_ranges('heading')))
        self.assertEqual(4, len(view.text.tag_ranges('hunk')))
        self.assertTrue(view.text.cget('xscrollcommand'))
        with patch('src.ui.diff_view.line_labels', side_effect=ValueError('presentation failure')):
            view.show(text)
        self.assertEqual(text, view.text.get('1.0', 'end-1c'))
        self.assertIn('unavailable', view.notice.get())
        view.show('')
        self.assertEqual('', view.text.get('1.0', 'end-1c'))
