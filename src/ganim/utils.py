# ganim.utils: Unexported utilities used in ganim
#
# This file is part of ganim, which is dedicated to the public domain.
# See <https://unlicense.org/> for more information or the UNLICENSE file included with
# the ganim source code.

from typing import Dict, List

from argparse import ArgumentParser
from bisect import bisect_left
from pathlib import Path

from pygments.styles import get_all_styles  # type: ignore
from textual._easing import EASING
from pydriller import Repository  # type: ignore

from .structures import Behaviour, Modification, ModificationIterationMethod, Commit


def process_args() -> Behaviour:
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
        help=f"specify words per minute, defaults to {default.wpm}",
        type=int,
        default=default.wpm,
    )
    parser.add_argument(
        "--fps",
        help=f"specify words per minute, defaults to {default.fps}",
        type=int,
        default=default.fps,
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
    parser.add_argument(
        "--iter_method",
        help=f"specify line iteration method, defaults to {default.iter_method.value}",
        choices=[im.value for im in ModificationIterationMethod],
        type=str,
        default=default.iter_method.value,
    )

    # syntax arguments
    syntax_args = parser.add_argument_group(
        "syntax highlighting args",
    )
    syntax_args.add_argument(
        "--highlight_syntax",
        help=f"enables syntax highlighting, defaults to {default.highlight_syntax}",
        choices=[True, False],
        type=bool,
        default=default.highlight_syntax,
    )
    syntax_args.add_argument(
        "--highlight_theme",
        help=(
            "specifies a pygments theme to highlight file contents in, "
            "see https://pygments.org/styles/"
        ),
        choices=[theme for theme in get_all_styles()],
        type=str,
        default=default.highlight_theme,
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
        fps=args.fps,
        quit_once_done=args.quit_once_done,
        iter_method=ModificationIterationMethod(args.iter_method),
        highlight_syntax=args.highlight_syntax,
        highlight_theme=args.highlight_theme,
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


def process_repo(behaviour: Behaviour) -> List[Commit]:
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
                deleted.update({line: content})

            modifications.append(
                Modification(
                    old_path=old_path,
                    new_path=new_path,
                    type=file.change_type,
                    added=added,
                    deleted=deleted,
                )
            )
        if len(modifications) > 0:
            commits.append(
                Commit(
                    author=commit.author.name,
                    message=commit.msg,
                    modifications=modifications,
                )
            )

    return commits


def moditer(
    mod: Modification,
    method: ModificationIterationMethod = ModificationIterationMethod.TOP_BOTTOM,
    position: int = 0,
):
    """
    custom iterator for file modifications

    mod: Modification,
        ganim.Modification object
    method: ModificationIterationMethod = ModificationIterationMethod.TOP_BOTTOM
        ganim.ModificationIterationMethod object
    position: int = 0
        used if iter method is nearest_*, if so change value from 0 to the cursor
        position before last modification animation
    """
    last = max(max(mod.added.keys(), default=-1), max(mod.deleted.keys(), default=-1))

    if last == -1:
        yield 0, "", ""

    elif method == ModificationIterationMethod.TOP_BOTTOM:
        for ln in range(1, last):
            deleted = mod.deleted.get(ln, "")
            added = mod.added.get(ln, "")
            yield ln, added, deleted

    else:
        # get nearest modifed line
        nearest = _get_nearest(
            sorted(list(mod.added.keys()) + list(mod.deleted.keys())),
            position,
        )

        for ln in range(nearest, last + 1):
            yield ln, mod.added.get(ln, ""), mod.deleted.get(ln, "")

        for ln in range(nearest):
            yield ln, mod.added.get(ln, ""), mod.deleted.get(ln, "")


def _get_nearest(l: List[int], n: int) -> int:
    pos = bisect_left(l, n)
    if pos == 0:
        return l[0]
    elif pos == len(l):
        return l[-1]
    else:
        pos_left, pos_right = l[pos - 1], l[pos]
        return pos_left if (pos_left - n) < (n - pos_right) else pos_right
