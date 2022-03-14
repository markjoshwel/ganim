"""
ganim: Animating the history of a file using Git.

-------------------------------------------------

This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or distribute this software,
either in source code form or as a compiled binary, for any purpose, commercial or
non-commercial, and by any means.

In jurisdictions that recognize copyright laws, the author or authors of this software
dedicate any and all copyright interest in the software to the public domain. We make
this dedication for the benefit of the public at large and to the detriment of our heirs
and successors. We intend this dedication to be an overt act of relinquishment in
perpetuity of all present and future rights to this software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

For more information, please refer to <http://unlicense.org/>
"""

from typing import Dict, List, NamedTuple

from dataclasses import dataclass, field
from argparse import ArgumentParser
from asyncio.futures import Future
from asyncio import ensure_future
from datetime import datetime
from asyncio import sleep
from pathlib import Path

from pydriller import Repository, ModificationType  # type: ignore
from pygments.styles import get_all_styles  # type: ignore
from rich.text import Text

from textual.views._window_view import WindowView
from textual.layouts.grid import GridLayout
from textual.reactive import Reactive
from textual._easing import EASING
from textual.widget import Widget
from textual.view import View
from textual.app import App
from textual import events


class Behaviour(NamedTuple):
    """ganim behaviour namedtuple, set from clargs"""

    # ganim args
    targets: List[Path] = []
    repo_root: Path = Path("")
    easing_style: str = "in_out_cubic"
    easing_duration: float = 0.75
    wpm: int = 150
    quit_once_done: int = -1

    # rich.Syntax args
    theme: str = "default"
    line_numbers: bool = False
    indent_guides: bool = False
    word_wrap: bool = False

    # pydriller.Repository args
    from_commit: str | None = None
    to_commit: str | None = None
    from_tag: str | None = None
    to_tag: str | None = None
    only_in_branch: str | None = None
    only_no_merge: bool = False
    only_authors: List[str] | None = None
    only_commits: List[str] | None = None
    only_releases: bool = False
    filepath: str | None = None
    only_file_types: List[str] | None = None


class Modification(NamedTuple):
    """namedtuple representing a file modification

    old_path: Path | None
        None if file was created, else same as new_path
    new_path: Path | None
        None if file was deleted, else same as old_path
    type: pydriller.ModificationType
        see pydriller docs
    added: Dict[int, str]
        added/modified lines in the form of (line number, content), sorted
    deleted: Dict[int, str]
        deleted lines in the form of (line number, content), sorted
    """

    old_path: Path | None
    new_path: Path | None
    type: ModificationType
    added: Dict[int, str]
    deleted: Dict[int, str]


class Commit(NamedTuple):
    """
    namedtuple representing a git commit

    author: str
        author username
    message: str
        commit message
    modifications: List[Modification]
        list of ganim.Modification representing modifications pushed in commit
    """

    author: str
    message: str
    modifications: List[Modification]


@dataclass
class File:
    """
    dataclass representing a file

    path: Path
        path to file
    current_line: int = 0
        used to keep track of which line ContentView should resume animation of file from
    content: List[str] = []
        file contents as a List[str], so line contents can be easily changed using
        indexing
    new: bool = False
        used to keep track of whether this file was modified during the current commit
    """

    path: Path
    current_line: int = 0
    content: List[str] = field(default_factory=list)
    current: bool = False


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

            file_text.append(Text.from_markup(f"[{style}]{file.path.name}[/]"))
            file_text.append(self.spacing)

        return file_text

    async def update(self, mod_type: ModificationType, old_path: Path | None, new_path: Path | None) -> File:
        """
        updates internal file list if needed and returns file object for modification by
        ContentView.ganimate()
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

        elif new_path is None and old_path is not None:  # file is deleted
            return self.files.pop(old_path)

        elif old_path is not None and new_path is not None:  # no change in file path
            _file = self.files.pop(old_path)
            _file.current = True
            self.files.update({old_path: _file})
            return self.files[old_path]
        
        else:
            print("unreachable")
            raise Exception("unreachable (no suitable new_path old_path criteria)")

    async def advance(self) -> None:
        """
        called before an animation of a new commit to False the new property of any file
        """
        for f in self.files.values():
            if f.current == True:
                f.current = False


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

        # self.fluid = True
        self.window = WindowView("", auto_width=False, gutter=(0, 0))
        layout = GridLayout()
        layout.add_column("main")
        layout.add_row("main")
        layout.add_areas(
            content="main,main", vscroll="vscroll,main", hscroll="main,hscroll"
        )
        super().__init__(name=name, layout=layout)

    x: Reactive[float] = Reactive(0.0, repaint=False)
    y: Reactive[float] = Reactive(0.0, repaint=False)

    target_x: Reactive[float] = Reactive(0.0, repaint=False)
    target_y: Reactive[float] = Reactive(0.0, repaint=False)

    async def on_mount(self, event: events.Mount) -> None:
        assert isinstance(self.layout, GridLayout)
        self.layout.place(
            content=self.window,
        )
        await self.layout.mount_all(self)


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

    async def start_ganimate(self):
        """
        bootstraps GAnim.ganimate() call using asyncio.ensure_future()

        stores returned future in self.ganimate_future
        """
        self.ganimate_future = ensure_future(self.ganimate())

    async def ganimate(self) -> None:
        """where the magic happens"""
        spc: float = 60 / (self.behaviour.wpm * 4.7)  # seconds per character

        for commit in self.commits:
            await self.filemgr.advance()

            # update CommitInfo widget
            self.commitinfo.text = f"[bold cyan]<{commit.author}>[/]: {commit.message}"
            self.commitinfo.refresh()

            # process modified files
            for mod in commit.modifications:
                file = await self.filemgr.update(mod_type=mod.type, old_path=mod.old_path, new_path=mod.new_path)
                self.filemgr.refresh()

                # TODO: animate modified files

        if self.behaviour.quit_once_done != -1:
            await sleep(self.behaviour.quit_once_done)
            await self.action_quit()


def main() -> None:
    """ganim entry point, returns Behaviour"""

    behaviour: Behaviour = handle_args()
    commits: List[Commit] = process(behaviour)

    if len(commits) == 0:
        from rich import print
        print("[bold red]error[/]: no commits to be animated")
        exit(1)

    # try to install uvloop
    try:
        import uvloop

    except ImportError:
        pass

    else:
        uvloop.install

    GAnim.run(behaviour=behaviour, commits=commits)


def handle_args() -> Behaviour:
    """handles clargs and sets a global Behaviour variable as bev"""
    default = Behaviour()

    parser = ArgumentParser(
        prog="ganim", description="animating the history of a file using git"
    )
    # ganim arguments
    parser.add_argument(
        "targets",
        help="target file paths, defaults to all files",
        type=Path,
        nargs="*",
        default=default.targets,
    )
    parser.add_argument(
        "--repo_root",
        help="path to repo, defaults to cwd",
        type=Path,
        default=default.repo_root,
    )
    parser.add_argument(
        "--easing_style",
        help="specify textual easing style",
        choices=[ek for ek in sorted(EASING.keys())],
        type=str,
        default=default.easing_style,
    )
    parser.add_argument(
        "--easing_duration",
        help=f"specify easing duration, defaults to {default.easing_duration}",
        type=float,
        default=default.easing_duration,
    )
    parser.add_argument(
        "--wpm",
        help="specify words per minute, defaults to {default.wpm}",
        type=int,
        default=default.wpm,
    )
    parser.add_argument(
        "--quit_once_done",
        help=(
            "quits n seconds after animation finishes, "
            f"defaults to {default.quit_once_done} (dont quit)"
        ),
        type=int,
        default=-1,
    )

    # syntax arguments
    syntax_args = parser.add_argument_group(
        "code syntax args",
        description="see https://rich.readthedocs.io/en/stable/syntax.html",
    )
    syntax_args.add_argument(
        "--theme",
        help="specifies a pygments theme to display file contents in",
        choices=[theme for theme in get_all_styles()],
        type=str,
        default=default.theme,
    )
    syntax_args.add_argument(
        "--line_numbers",
        help=f"enable indent guides, defaults to {default.line_numbers}",
        choices=[True, False],
        type=bool,
        default=default.line_numbers,
    )
    syntax_args.add_argument(
        "--indent_guides",
        help=f"enable indent guides, defaults to {default.indent_guides}",
        choices=[True, False],
        type=bool,
        default=default.indent_guides,
    )
    syntax_args.add_argument(
        "--word_wrap",
        help=f"enable word wrapping, defaults to {default.word_wrap}",
        choices=[True, False],
        type=bool,
        default=default.word_wrap,
    )

    # commit range arguments
    commit_range_args = parser.add_argument_group(
        "commit range arguments",
        description=(
            "see https://"
            "pydriller.readthedocs.io/en/latest/repository.html"
            "#selecting-the-commit-range"
        ),
    )
    commit_range_args.add_argument(
        "--from_commit", help="starting commit", type=str, default=default.from_commit
    )
    commit_range_args.add_argument(
        "--to_commit", help="ending commit", type=str, default=default.to_commit
    )
    commit_range_args.add_argument(
        "--from_tag",
        help="starting the analysis from specified tag",
        type=str,
        default=default.from_tag,
    )
    commit_range_args.add_argument(
        "--to_tag",
        help="ending the analysis from specified tag",
        type=str,
        default=default.to_tag,
    )

    # commit filter arguments
    commit_filter_args = parser.add_argument_group(
        "commit_filter_args",
        description=(
            "see https://"
            "pydriller.readthedocs.io/en/latest/repository.html#filtering-commits"
        ),
    )
    commit_filter_args.add_argument(
        "--only_in_branch",
        help="only analyses commits that belong to this branch",
        type=str,
        default=default.only_in_branch,
    )
    commit_filter_args.add_argument(
        "--only_no_merge",
        help=(
            "only analyses commits that are not merge commits, "
            f"defaults to {default.only_no_merge}"
        ),
        choices=[True, False],
        type=bool,
        default=default.only_no_merge,
    )
    commit_filter_args.add_argument(
        "--only_authors",
        help="only analyses commits that are made by these authors' usernames",
        nargs="+",
        type=str,
        default=default.only_authors,
    )
    commit_filter_args.add_argument(
        "--only_commits",
        help="only these commits will be analyzed",
        nargs="+",
        type=str,
        default=default.only_authors,
    )
    commit_filter_args.add_argument(
        "--only_releases",
        help=(
            "only commits that are tagged will be analyzed, "
            f"defaults to {default.only_releases}"
        ),
        choices=[True, False],
        type=bool,
        default=default.only_releases,
    )
    commit_filter_args.add_argument(
        "--filepath",
        help="only commits that modified this file will be analyzed",
        type=str,
        default=default.filepath,
    )
    commit_filter_args.add_argument(
        "--only_file_types",
        help="only show histories of certain file types, e.g. '.py'",
        nargs="+",
        type=str,
        default=default.only_file_types,
    )

    args = parser.parse_args()

    # target file validation
    for i, target in enumerate(args.targets, start=1):
        if not (target.exists() and target.is_file()):
            print(f"ganim: error: target #{i} '{target}' is an invalid path")
            exit(1)

    # file type standardisation
    only_file_types: List[str] | None = None
    if args.only_file_types is not None:
        only_file_types = []
        for file_type in args.only_file_types:
            if file_type.startswith("."):
                only_file_types.append(file_type)
            else:
                only_file_types.append(f".{file_type}")

    return Behaviour(
        targets=args.targets,
        repo_root=args.repo_root,
        easing_style=args.easing_style,
        easing_duration=args.easing_duration,
        wpm=args.wpm,
        quit_once_done=args.quit_once_done,
        theme=args.theme,
        line_numbers=args.line_numbers,
        indent_guides=args.indent_guides,
        word_wrap=args.word_wrap,
        from_commit=args.from_commit,
        to_commit=args.to_commit,
        from_tag=args.from_tag,
        to_tag=args.to_tag,
        only_in_branch=args.only_in_branch,
        only_no_merge=args.only_no_merge,
        only_authors=args.only_authors,
        only_commits=args.only_commits,
        only_releases=args.only_releases,
        filepath=args.filepath,
        only_file_types=only_file_types,
    )


def process(behaviour: Behaviour) -> List[Commit]:
    """processes the repository for files to animate, returns List[Commit]"""

    commits: List[Commit] = []

    for commit in Repository(
        path_to_repo=str(behaviour.repo_root),
        from_commit=behaviour.from_commit,
        to_commit=behaviour.to_commit,
        from_tag=behaviour.from_tag,
        to_tag=behaviour.to_tag,
        only_in_branch=behaviour.only_in_branch,
        only_no_merge=behaviour.only_no_merge,
        only_authors=behaviour.only_authors,
        only_commits=behaviour.only_commits,
        only_releases=behaviour.only_releases,
        filepath=behaviour.filepath,
        only_modifications_with_file_types=behaviour.only_file_types,
    ).traverse_commits():
        modifications: List[Modification] = []

        for file in commit.modified_files:
            # skip file if targets were specified and file is not a target
            if len(behaviour.targets) > 0 and file.filename not in [
                str(p) for p in behaviour.targets
            ]:
                continue

            # skip file if file types were specified and file type was not specified
            elif (
                behaviour.only_file_types is not None
                and Path(file.filename).suffix not in behaviour.only_file_types
            ):
                continue

            diff = file.diff_parsed
            old_path = Path(file.old_path) if file.old_path is not None else None
            new_path = Path(file.new_path) if file.new_path is not None else None
            added: Dict[int, str] = {}
            deleted: Dict[int, str] = {}

            for line, content in diff["added"]:
                added.update({line: content})

            for line, content in diff["deleted"]:
                added.update({line: content})

            modifications.append(
                Modification(
                    old_path=old_path,
                    new_path=new_path,
                    type=file.change_type,
                    added=added,
                    deleted=deleted,
                )
            )

        commits.append(
            Commit(
                author=commit.author.name,
                message=commit.msg,
                modifications=modifications,
            )
        )

    return commits


if __name__ == "__main__":
    main()
