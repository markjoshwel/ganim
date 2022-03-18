# ganim.widgets: Textual widgets used by ganim.GAnim
#
# This file is part of ganim, which is dedicated to the public domain.
# See <https://unlicense.org/> for more information or the UNLICENSE file included with
# the ganim source code.


from typing import Dict

from asyncio import sleep
from pathlib import Path

from pydriller import ModificationType
from rich.syntax import Syntax
from rich.text import Text

from textual.views._window_view import WindowView
from textual.layouts.grid import GridLayout
from textual.scrollbar import ScrollBar
from textual.reactive import Reactive
from textual.geometry import clamp
from textual.widget import Widget
from textual.view import View
from textual import events

from .structures import File


class FileManager(Widget):
    """custom widget that shows and manages open files"""

    spacing: str = "  "
    files: Dict[Path, File] = {}

    def render(self) -> Text:
        file_text = Text(justify="left", overflow="crop")

        # unique everseen
        ue_files = []
        seen = set()

        for p, f in self.files.items():
            if str(p) in seen:
                continue
            seen.add(str(p))
            ue_files.append(f)

        for ind, file in enumerate(ue_files[:-15:-1]):  # get last 15 files
            style: str = ""

            # underline current files
            if file.current:
                style = "underline"

                if ind == 0:  # bold first file
                    style += " bold"

            # dim old files
            else:
                style = "dim"

            if file.deleted:
                style += " strike italic"

            file_text.append(Text.from_markup(f"[{style}]{file.path.name}[/]"))
            file_text.append(self.spacing)

        return file_text

    async def update(
        self, mod_type: ModificationType, old_path: Path | None, new_path: Path | None
    ) -> File:
        """
        updates internal file list if needed and returns ganim.File object for
        modification by ContentView.ganimate()
        """

        if mod_type == ModificationType.ADD and new_path is not None:  # file is added
            self.files.update(
                {
                    new_path: File(
                        path=new_path,
                        current_line=0,
                        current=True,
                    )
                }
            )
            return self.files[new_path]

        # file was deleted
        elif mod_type == ModificationType.DELETE and old_path is not None:
            # self.files[old_path].deleted = True
            # return self.files[old_path]
            self.files[old_path].deleted = True
            return self.files[old_path]

        elif old_path is not None and new_path is not None:
            _file = self.files.pop(old_path)
            _file.current = True
            _file.path = new_path
            self.files.update({new_path: _file})
            return self.files[old_path]

        else:
            print("unreachable")
            raise Exception("unreachable (no suitable new_path old_path criteria)")

    async def advance(self) -> None:
        """
        called before an animation of a new commit to False the current property of any
        file modifed previous commit, and to remove them from self.files if it was
        deleted previous commit
        """
        for p, f in list(self.files.items()):
            if f.current:
                f.current = False
            if f.deleted:
                self.files.pop(p)


class CommitInfo(Widget):
    """custom widget that shows the current commit"""

    text: str = ""

    def render(self) -> Text:
        return Text.from_markup(self.text)


class ContentView(View):
    """
    custom textual view object based on textual.widgets.ScrollView

    animates new changes to file objects returned by FileWidget.update() based on file
    modifications (ganim.Modification)
    """

    def __init__(
        self,
        name: str | None = None,
    ) -> None:
        self.fluid = True
        self.vscroll = ScrollBar(vertical=True)
        self.hscroll = ScrollBar(vertical=False)
        self.window = WindowView("", auto_width=False, gutter=(0, 0))
        layout = GridLayout()
        layout.add_column("main")
        layout.add_row("main")
        layout.add_areas(content="main,main")
        super().__init__(name=name, layout=layout)

    x: Reactive[float] = Reactive(0.0, repaint=False)
    y: Reactive[float] = Reactive(0.0, repaint=False)

    target_x: Reactive[float] = Reactive(0.0, repaint=False)
    target_y: Reactive[float] = Reactive(0.0, repaint=False)

    def validate_x(self, value: float) -> float:
        return clamp(value, 0, self.max_scroll_x)

    def validate_target_x(self, value: float) -> float:
        return clamp(value, 0, self.max_scroll_x)

    def validate_y(self, value: float) -> float:
        return clamp(value, 0, self.max_scroll_y)

    def validate_target_y(self, value: float) -> float:
        return clamp(value, 0, self.max_scroll_y)

    @property
    def max_scroll_y(self) -> float:
        return max(0, self.window.virtual_size.height)

    @property
    def max_scroll_x(self) -> float:
        return max(0, self.window.virtual_size.width)

    async def watch_x(self, new_value: float) -> None:
        self.window.scroll_x = round(new_value)
        self.hscroll.position = round(new_value)

    async def watch_y(self, new_value: float) -> None:
        self.window.scroll_y = round(new_value)
        self.vscroll.position = round(new_value)

    async def on_mount(self, event: events.Mount) -> None:
        assert isinstance(self.layout, GridLayout)
        self.layout.place(
            content=self.window,
        )
        await self.layout.mount_all(self)

    # FIXME: is there a better way to do this?
    async def update(self) -> None:
        """rebuilds file contents and updates contentview window"""
        if self.file is not None and self.syntax is not None:

            self.syntax.code = "\n".join(self.file.content).rstrip()
            await self.window.update(self.syntax)

    async def register_file(self, file: File, syntax: Syntax):
        """sets self.file, self.syntax and updates contentview window"""
        self.file = file
        self.syntax = syntax
        await self.window.update(syntax)

    async def scroll_to(
        self,
        line: int,
        easing: str,
        duration: float,
    ) -> None:
        """scrolls to a specific line

        line: int
            line to scroll to
        easing: str
            easing method
        duration: float
            duration in seconds
        """
        from math import ceil

        res = line - self.size.height // 2
        self.target_y = line - self.size.height // 2

        # animate if l, else
        if abs(self.target_y - self.y) > 1:
            self.animate("y", res, easing=easing, duration=duration)
        else:
            self.y = self.target_y
