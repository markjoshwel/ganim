# ganim.app: Textual application
#
# This file is part of ganim, which is dedicated to the public domain.
# See <https://unlicense.org/> for more information or the UNLICENSE file included with
# the ganim source code.

from typing import List

from asyncio.futures import Future
from asyncio import ensure_future
from asyncio import sleep

from textual.app import App
from textual import events

from .widgets import ContentView, CommitInfo, FileManager
from .structures import Behaviour, Commit


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
        self.contentview = ContentView(name="ContentView")
        self.commitinfo = CommitInfo(name="CommitInfo")
        self.filemgr = FileManager(name="FileManager")

        await self.view.dock(self.filemgr, edge="top", size=1, name="fileview")
        await self.view.dock(self.commitinfo, edge="bottom", size=1, name="commitview")
        await self.view.dock(self.contentview)

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

        else:
            cps = (self.behaviour.wpm * 4.7) / 60

            for commit in self.commits:
                await self.filemgr.advance()

                self.commitinfo.text = (
                    f"[bold cyan]<{commit.author}>[/]: {commit.message}"
                )
                self.commitinfo.refresh()

                for mod in commit.modifications:
                    await self.contentview.animate_modification(
                        file=await self.filemgr.update(
                            mod_type=mod.type,
                            old_path=mod.old_path,
                            new_path=mod.new_path,
                        ),
                        modification=mod,
                        iter_method=self.behaviour.iter_method,
                        cps=cps,
                        fps=self.behaviour.fps,
                    )

        await self.filemgr.advance()
        self.commitinfo.text = f"[dim]{self.commitinfo.text}"
        self.commitinfo.refresh()

        if self.behaviour.quit_once_done != -1:
            await sleep(self.behaviour.quit_once_done)
            await self.action_quit()
