# ganim.app: Textual application
#
# This file is part of ganim, which is dedicated to the public domain.
# See <https://unlicense.org/> for more information or the UNLICENSE file included with
# the ganim source code.

from typing import Dict, List, NamedTuple

from asyncio.futures import Future
from asyncio import ensure_future
from asyncio import sleep

from pydriller import ModificationType
from rich.syntax import Syntax

from textual.app import App
from textual import events

from .widgets import ContentView, CommitInfo, FileManager
from .structures import Behaviour, Commit
from .utils import moditer


class GAnim(App):
    """ganim textual app"""

    def __init__(
        self, *args, behaviour: Behaviour, commits: List[Commit], **kwargs
    ) -> None:
        self.behaviour: Behaviour = behaviour
        self.commits: List[Commit] = commits
        self.ganimate_future: Future | None = None

        super().__init__(*args, **kwargs)

    async def on_load(self) -> None:
        """key bindings"""
        await self.bind("f", "view.toggle('fileview')")
        await self.bind("c", "view.toggle('commitview')")
        await self.bind("q", "quit")

    async def on_mount(self) -> None:
        """mount widgets"""
        # create
        self.contentview = ContentView(name="ContentView")
        self.commitinfo = CommitInfo(name="CommitInfo")
        self.filemgr = FileManager(name="FileManager")

        # dock
        await self.view.dock(self.filemgr, edge="top", size=1, name="fileview")
        await self.view.dock(self.commitinfo, edge="bottom", size=1, name="commitview")
        await self.view.dock(self.contentview)

        # get ready
        await self.call_later(self.start_ganimate)

    async def action_quit(self) -> None:
        if self.ganimate_future is not None:
            self.ganimate_future.cancel()
        return await super().action_quit()

    async def on_shutdown_request(self, event: events.ShutdownRequest) -> None:
        if self.ganimate_future is not None:
            self.ganimate_future.cancel()
        return await super().on_shutdown_request(event)

    async def start_ganimate(self):
        """
        bootstraps GAnim.ganimate() call using asyncio.ensure_future()

        stores returned future in self.ganimate_future
        """
        self.ganimate_future = ensure_future(self.ganimate())

    async def ganimate(self) -> None:
        """where the magic happens"""
        if len(self.commits) == 0:
            self.commitinfo.text = f"[bold red]no commits to analyse, nothing to do"
            self.commitinfo.refresh()

            if self.behaviour.quit_once_done != -1:
                await sleep(self.behaviour.quit_once_done)
                await self.action_quit()

        spc: float = 60 / (self.behaviour.wpm * 4.7)  # seconds per character

        # FIXME: is there a better way to do this?
        async def _refresh():
            """
            nested function to refresh filemanager, contentview and contentinfo all at
            once, used only during animation
            """
            self.commitinfo.refresh()
            self.filemgr.refresh()
            await self.contentview.update()

        for commit in self.commits:
            await self.filemgr.advance()

            # update CommitInfo widget
            self.commitinfo.text = f"[bold cyan]<{commit.author}>[/]: {commit.message}"
            self.commitinfo.refresh()

            # process modified files
            for mod in commit.modifications:
                # 0.2.0
                # await self.commitview.animod(mod)

                # update filemgr
                file = await self.filemgr.update(
                    mod_type=mod.type, old_path=mod.old_path, new_path=mod.new_path
                )
                self.filemgr.refresh()

                # create syntax
                syntax = Syntax(
                    code="",
                    lexer=Syntax.guess_lexer(str(file.path)),
                    theme=self.behaviour.theme,
                    line_numbers=self.behaviour.line_numbers,
                    indent_guides=self.behaviour.indent_guides,
                    word_wrap=self.behaviour.word_wrap,
                )

                # register file with contentview
                await self.contentview.register_file(file, syntax)

                # skip animation if whole file was deleted
                if mod.type == ModificationType.DELETE and len(mod.deleted) == len(
                    self.contentview.file.content
                ):
                    continue

                # FIXME: is there a better way to do this?
                last_line: int = file.current_line
                for ln, added, deleted in moditer(
                    mod, method=self.behaviour.iter_method, position=file.current_line
                ):
                    clen = len(self.contentview.file.content)

                    # move to position
                    await self.contentview.scroll_to(
                        line=ln,
                        easing=self.behaviour.easing_style,
                        duration=self.behaviour.easing_duration,
                    )

                    if deleted != "":
                        for _ in deleted:
                            self.contentview.file.content[
                                ln - 1
                            ] = self.contentview.file.content[ln - 1][:-1]

                            # refresh and wait
                            await _refresh()
                            await sleep(spc)

                    if added != "":
                        # create any needed lines
                        if clen == 0 and ln == 1:
                            self.contentview.file.content = [""]
                        elif ln > clen:
                            for _ln in range(clen - 1, ln - 1):
                                self.contentview.file.content.append("")

                        for c in added:
                            self.contentview.file.content[ln - 1] += c

                            # refresh and wait
                            await _refresh()
                            await sleep(spc)

                    last_line = ln

                file.current_line = last_line

        # finish up; dim text to signal completion of animation
        await self.filemgr.advance()
        self.commitinfo.text = f"[dim]{self.commitinfo.text}"
        await _refresh()

        if self.behaviour.quit_once_done != -1:
            await sleep(self.behaviour.quit_once_done)
            await self.action_quit()
