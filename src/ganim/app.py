"""
ganim.app: textual-related classes and functions
------------------------------------------------
by mark <mark@joshwel.co>

This file is part of ganim, which is free and unencumbered software released into the
public domain. See <https://unlicense.org> for more information or the UNLICENSE file
included with the ganim source code.
"""

from typing import Final

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header

from .utils import Behaviour
from .widgets import CommitManager, ContentView, FileManager

ACTION_WPM_CHANGE: Final[int] = 50


class GAnim(App):
    """the ganim textual application"""

    BINDINGS = [
        ("f", "toggle_fileview", "Toggle File View"),
        ("c", "toggle_commitview", "Toggle Commit View"),
        ("p", "action_playpause", "Play/Pause"),
        ("[", "action_wpm_decrease", f"Decrease WPM by {ACTION_WPM_CHANGE}"),
        ("]", "action_wpm_increase", f"Increase WPM by {ACTION_WPM_CHANGE}"),
        ("q", "action_quit", "Exit ganim"),
    ]

    bev: Behaviour
    filemgr: FileManager
    commitmgr: CommitManager
    contentview: ContentView

    def __init__(self, behaviour: Behaviour) -> None:
        self.bev = behaviour
        self.filemgr = FileManager()
        self.commitmgr = CommitManager()
        self.contentview = ContentView()

        super().__init__()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
