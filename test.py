from typing import List

from asyncio.futures import Future
from asyncio import ensure_future

from rich.syntax import Syntax

from textual.widgets import ScrollView
from textual.app import App

from src.ganim.structures import *
from src.ganim.widgets import *
from src.ganim.utils import *


class TestContentView(View):
    """
    custom textual view object based on textual.widgets.ScrollView

    animates new changes to file objects returned by FileWidget.update() based on file
    modifications (ganim.structures.Modification)
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
        return max(0, self.window.virtual_size.height - self.window.size.height)

    @property
    def max_scroll_x(self) -> float:
        return max(0, self.window.virtual_size.width - self.window.size.width)

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

    async def scroll_to(
        self,
        line: int,
        easing: str,
        duration: float,
    ) -> None:
        """
        custom function, scrolls to a specific line

        line: int
            line to scroll to
        easing: str
            easing method
        duration: float
            duration in seconds
        """
        self.target_y = line - self.size.height // 2

        if abs(self.target_y - self.y) > 1:
            self.animate("y", self.target_y, easing=easing, duration=duration)
        else:
            self.y = self.target_y

    async def animate_modification(
        self,
        file: File,
        modification: Modification,
        iter_method: ModificationIterationMethod,
        cps: float,
        fps: int = 60,
    ) -> None:
        """
        custom function, animates a Modification object

        file: ganim.structures.File
            File object returned from ganim.widgets.FileManager.update()
        modification: ganim.widgets.Modification
            Modification object
        iter_method: ganim.structures.ModificationIterationMethod
            iteration method
        cps: float
            characters per second
        fps: int = 60
            frames per second
        """
        stime = (1 / fps) if (fps > 0) else (60 / (cps * 60))
        await self.window.update(f"{cps=} {fps=} {stime=}")

        for line, added, deleted in moditer(
            modification, method=iter_method, position=file.position
        ):
            pass


class TestGAnim(App):
    """ganim textual app"""

    def __init__(
        self, *args, **kwargs
    ) -> None:
        self.ganimate_future: Future | None = None

        super().__init__(*args, **kwargs)

    async def on_load(self) -> None:
        """key bindings"""
        await self.bind("f", "view.toggle('fileview')")
        await self.bind("c", "view.toggle('commitview')")
        await self.bind("q", "quit")

    async def on_mount(self) -> None:
        """mount widgets"""
        self.contentview = TestContentView(name="ContentView")
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
        await self.contentview.window.update("TestGAnim")

        tgt = "TestGAnim "

        for _ in iter(int, 1):
            for i in range(len(tgt)):
                self.commitinfo.text = "[bold red]" + tgt[i:-1] + (" TestGAnim" * 20)
                self.commitinfo.refresh()
                await sleep(1 / 29.98)  # CD / Frame Rate


TestGAnim.run()
