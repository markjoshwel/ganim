# ganim.structures: Data structures used in ganim
#
# This file is part of ganim, which is dedicated to the public domain.
# See <https://unlicense.org/> for more information or the UNLICENSE file included with
# the ganim source code.

from typing import Dict, List, NamedTuple

from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

from pydriller import ModificationType  # type: ignore


class Modification(NamedTuple):
    """
    namedtuple representing a file modification

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
    modifications: List[ganim.structures.Modification]
        list of Modification representing modifications pushed in commit
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
    position: int = 0
        used to keep track of which line ContentView should resume animation of file from
    content: List[str] = []
        file contents as a List[str], so line contents can be easily changed using
        indexing
    current: bool = False
        used by FileManager to keep track of whether this file was modified during the
        current commit
    deleted: bool = False
        same as `current` argument however for deletion; file will be removed from
        FileManager.files after update
    """

    path: Path
    position: int = 0
    content: List[str] = field(default_factory=list)
    current: bool = False
    deleted: bool = False


class ModificationIterationMethod(Enum):
    """iteration method enum"""

    TOP_BOTTOM = "top_bottom"
    NEAREST = "nearest"


class Behaviour(NamedTuple):
    """ganim behaviour namedtuple, set from clargs"""

    # ganim args
    targets: List[Path] = []
    repo_root: Path = Path("")
    easing_style: str = "in_out_cubic"
    easing_duration: float = 0.5
    wpm: int = 500
    fps: int = 60
    quit_once_done: int = -1
    iter_method: ModificationIterationMethod = ModificationIterationMethod.NEAREST

    # syntax highlighting args
    highlight_syntax: bool = False
    # highlight_theme: str = "default"
    line_numbers: bool = True
    # indent_guides: bool = True
    word_wrap: bool = False

    # pydriller.Repository args
    from_commit: str | None = None
    to_commit: str | None = None
    from_tag: str | None = None
    to_tag: str | None = None
    only_file_types: List[str] | None = None


default = Behaviour()
