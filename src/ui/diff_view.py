"""Read-only stored diff presentation; line parsing confers no validity."""
import re
import tkinter as tk
from tkinter import ttk

from .theme import LIGHT


def line_labels(text):
    old = new = None
    labels = []
    for line in text.splitlines():
        match = re.match(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
        if line.startswith(('--- ', '+++ ')):
            old = new = None
            labels.append('File')
        elif match:
            old, new = map(int, match.groups())
            labels.append('Hunk')
        elif old is not None and line.startswith('+'):
            labels.append(f'{"":>5} {new:>5}'); new += 1
        elif old is not None and line.startswith('-'):
            labels.append(f'{old:>5} {"":>5}'); old += 1
        elif old is not None and line.startswith(' '):
            labels.append(f'{old:>5} {new:>5}'); old += 1; new += 1
        else:
            labels.append('')
    return labels


class DiffView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        self.notice = tk.StringVar(parent, value='Stored unified diff (complete raw text) | gutter: original / new line')
        ttk.Label(self, textvariable=self.notice).grid(row=0, column=0, columnspan=3, sticky='w')
        self.gutter = tk.Text(self, width=13, height=12, wrap='none', font=('Consolas', 10), state='disabled', takefocus=False)
        self.text = tk.Text(self, height=12, wrap='none', font=('Consolas', 10), state='disabled')
        self.gutter.grid(row=1, column=0, sticky='ns')
        self.text.grid(row=1, column=1, sticky='nsew')
        self.vertical = ttk.Scrollbar(self, command=self._scroll)
        self.vertical.grid(row=1, column=2, sticky='ns')
        horizontal = ttk.Scrollbar(self, orient='horizontal', command=self.text.xview)
        horizontal.grid(row=2, column=1, sticky='ew')
        self.text.configure(xscrollcommand=horizontal.set, yscrollcommand=self._position)
        self.text.tag_configure('addition', foreground=LIGHT['addition'], background=LIGHT['addition_bg'])
        self.text.tag_configure('deletion', foreground=LIGHT['deletion'], background=LIGHT['deletion_bg'])
        self.text.tag_configure('heading', foreground=LIGHT['focus'])
        self.text.tag_configure('hunk', foreground=LIGHT['muted'])
        self.stored_text = ''

    def _scroll(self, *args):
        self.text.yview(*args)
        self.gutter.yview(*args)

    def _position(self, first, last):
        self.vertical.set(first, last)
        self.gutter.yview_moveto(first)

    def show(self, text):
        self.stored_text = text
        try:
            labels = line_labels(text)
            self.notice.set('Stored unified diff (complete raw text) | gutter: original / new line')
        except (ValueError, TypeError):
            labels = []
            self.notice.set('Line numbers unavailable; complete stored diff remains visible.')
        for widget, body in ((self.text, text), (self.gutter, '\n'.join(labels))):
            widget.configure(state='normal')
            widget.delete('1.0', 'end')
            widget.insert('1.0', body)
            widget.configure(state='disabled')
        for index, line in enumerate(text.splitlines(), 1):
            tag = ('heading' if line.startswith(('--- ', '+++ ')) else 'hunk' if line.startswith('@@')
                   else 'addition' if line.startswith('+') else 'deletion' if line.startswith('-') else None)
            if tag:
                self.text.tag_add(tag, f'{index}.0', f'{index}.end')
