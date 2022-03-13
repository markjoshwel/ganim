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

from typing import Dict, List, NamedTuple, Optional, Tuple

from dataclasses import dataclass, field
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path

from pydriller import Repository, ModificationType  # type: ignore
from pygments.styles import get_all_styles  # type: ignore
from rich.text import Text

from textual.views._window_view import WindowView
from textual.layouts.grid import GridLayout
from textual.reactive import Reactive
from textual.widget import Widget
from textual.view import View
from textual.app import App
from textual import events


class Behaviour(NamedTuple):
    """ganim behaviour namedtuple, set from clargs"""

    # ganim args
    targets: List[Path]
    repo_root: Path

    # rich.Syntax args
    theme: str = "default"
    line_numbers: bool = False
    indent_guides: bool = False
    word_wrap: bool = False

    # pydriller.Repository args
    from_commit: Optional[str] = None
    to_commit: Optional[str] = None
    from_tag: Optional[str] = None
    to_tag: Optional[str] = None
    only_in_branch: Optional[str] = None
    only_no_merge: bool = False
    only_authors: Optional[List[str]] = None
    only_commits: Optional[List[str]] = None
    only_releases: bool = False
    filepath: Optional[str] = None
    only_file_types: Optional[List[str]] = None


class Modification(NamedTuple):
    """namedtuple representing a file modification

    old_path: Optional[Path]
    new_path: Optional[Path]
    type: ModificationType
    added: Dict[int, str]
    deleted: Dict[int, str]
    """

    old_path: Optional[Path]
    new_path: Optional[Path]
    type: ModificationType
    added: Dict[int, str]
    deleted: Dict[int, str]


class Commit(NamedTuple):
    """namedtuple representing a git commit"""

    author: str
    date: datetime
    modifications: List[Modification]


@dataclass
class File:
    """dataclass representing a file

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

            # dim old files
            else:
                style = "dim"

            # bold first file
            if ind == 0:
                style + " bold"

            file_text.append(Text.from_markup(f"[{style}]{file.path.name}[/]"))
            file_text.append(self.spacing)

        return file_text

    async def update(self, old_path: Path, new_path: Path) -> File:
        """
        updates internal file list if needed and returns file object for modification by
        ContentView.ganimate()
        """

        if old_path is None:  # file is added
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

        elif new_path is None:  # file is deleted
            return self.files.pop(old_path)

        else:  # no change in file path
            file = self.files[old_path]
            file.current = True
            return file

    async def advance(self) -> None:
        """called before an animation of a new commit to False the new property of any file"""
        for f in self.files.values():
            if f.current == True:
                f.current = False


class CommitInfo(Widget):
    """custom widget that shows the current commit"""

    text: str = ""

    def render(self) -> Text:
        return Text.from_markup(f"[bold]{self.text}")


class ContentView(View):
    """
    custom textual view object based on textual.widgets.ScrollView

    animates new changes to file objects returned by FileWidget.update() based on file
    modifications (ganim.Modification)
    """

    def __init__(
        self,
        name: Optional[str] = None,
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
        super().__init__(*args, **kwargs)

    async def on_load(self) -> None:
        """key bindings"""
        await self.bind("f", "view.toggle('fileview')")
        await self.bind("c", "view.toggle('commitview')")
        await self.bind("q", "quit")

    async def on_mount(self) -> None:
        """mount widgets"""
        # create
        self.content = ContentView(name="ContentView")
        self.commit = CommitInfo(name="CommitInfo")
        self.files = FileManager(name="FileManager")

        # dock
        await self.view.dock(self.files, edge="top", size=1, name="fileview")
        await self.view.dock(self.commit, edge="bottom", size=1, name="commitview")
        await self.view.dock(self.content)

        # get ready
        await self.call_later(self.ganimate)

    async def ganimate(self) -> None:
        """where the magic happens"""
        pass


def main() -> None:
    """ganim entry point, returns Behaviour"""

    behaviour: Behaviour = handle_args()
    commits: List[Commit] = process(behaviour)

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
    parser = ArgumentParser(
        prog="ganim", description="animating the history of a file using git"
    )

    # ganim arguments
    parser.add_argument(
        "target",
        help="target file paths, defaults to all files",
        type=Path,
        nargs="*",
        default=[],
    )
    parser.add_argument(
        "-r",
        "--repo_root",
        help="path to repo, defaults to cwd",
        type=Path,
        default=Path(""),
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
        default="default",
    )
    syntax_args.add_argument(
        "--line_numbers",
        help="enable indent guides, defaults to False",
        choices=[True, False],
        type=bool,
        default=False,
    )
    syntax_args.add_argument(
        "--indent_guides",
        help="enable indent guides, defaults to False",
        choices=[True, False],
        type=bool,
        default=False,
    )
    syntax_args.add_argument(
        "--word_wrap",
        help="enable word wrapping, defaults to False",
        choices=[True, False],
        type=bool,
        default=False,
    )

    # commit range arguments
    commit_range_args = parser.add_argument_group(
        "commit range arguments",
        description="see https://pydriller.readthedocs.io/en/latest/repository.html#selecting-the-commit-range",
    )
    commit_range_args.add_argument(
        "--from_commit", help="starting commit", type=str, default=None
    )
    commit_range_args.add_argument(
        "--to_commit", help="ending commit", type=str, default=None
    )
    commit_range_args.add_argument(
        "--from_tag",
        help="starting the analysis from specified tag",
        type=str,
        default=None,
    )
    commit_range_args.add_argument(
        "--to_tag", help="ending the analysis from specified tag", type=str, default=None
    )

    # commit filter arguments
    commit_filter_args = parser.add_argument_group(
        "commit_filter_args",
        description="see https://pydriller.readthedocs.io/en/latest/repository.html#selecting-the-commit-range",
    )
    commit_filter_args.add_argument(
        "--only_in_branch",
        help="only analyses commits that belong to this branch",
        type=str,
        default=None,
    )
    commit_filter_args.add_argument(
        "--only_no_merge",
        help="only analyses commits that are not merge commits, defaults to False",
        choices=[True, False],
        type=bool,
        default=False,
    )
    commit_filter_args.add_argument(
        "--only_authors",
        help="only analyses commits that are made by these authors' usernames",
        nargs="+",
        type=str,
        default=None,
    )
    commit_filter_args.add_argument(
        "--only_commits",
        help="only these commits will be analyzed",
        nargs="+",
        type=str,
        default=None,
    )
    commit_filter_args.add_argument(
        "--only_releases",
        help="only commits that are tagged will be analyzed, defaults to False",
        choices=[True, False],
        type=bool,
        default=False,
    )
    commit_filter_args.add_argument(
        "--filepath",
        help="only commits that modified this file will be analyzed",
        type=str,
        default=None,
    )
    commit_filter_args.add_argument(
        "--only_file_types",
        help="only show histories of certain file types, e.g. '.py'",
        nargs="+",
        type=str,
        default=None,
    )

    args = parser.parse_args()

    # target file validation
    for i, target in enumerate(args.target, start=1):
        if not (target.exists() and target.is_file()):
            print(f"ganim: error: target #{i} '{target}' is an invalid path")
            exit(1)

    # file type standardisation
    only_file_types: Optional[List[str]] = None
    if args.only_file_types is not None:
        only_file_types = []
        for file_type in args.only_file_types:
            if file_type.startswith("."):
                only_file_types.append(file_type)
            else:
                only_file_types.append(f".{file_type}")

    return Behaviour(
        targets=args.target,
        repo_root=args.repo_root,
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
            old_path = Path(file.old_path) if file.old_path is not None else file.old_path
            new_path = Path(file.new_path) if file.new_path is not None else file.new_path
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
                date=commit.author_date,
                modifications=modifications,
            )
        )

    return commits


if __name__ == "__main__":
    main()
