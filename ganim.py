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

from typing import List, NamedTuple, Optional, Tuple

from tempfile import TemporaryDirectory
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path

from pydriller import Repository, ModificationType  # type: ignore
from textual.app import App


class Behaviour(NamedTuple):
    """ganim behaviour namedtuple, set from clargs"""

    targets: List[Path]
    repo_root: Path

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
    """namedtuple representing a file modification"""

    old_path: Optional[Path]
    new_path: Optional[Path]
    type: ModificationType
    added: List[Tuple[int, str]]  # line no, new content
    deleted: List[Tuple[int, str]]


class Commit(NamedTuple):
    """namedtuple representing a git commit"""

    author: str
    date: datetime
    modifications: List[Modification]


class GAnim(App):
    """ganim textual app"""

    pass


def ganim(bev: Behaviour):
    """start ganim

    bev: Behaviour
        ganim behaviour namedtuple
    """

    commits: List[Commit] = []

    for commit in Repository(
        path_to_repo=str(bev.repo_root),
        from_commit=bev.from_commit,
        to_commit=bev.to_commit,
        from_tag=bev.from_tag,
        to_tag=bev.to_tag,
        only_in_branch=bev.only_in_branch,
        only_no_merge=bev.only_no_merge,
        only_authors=bev.only_authors,
        only_commits=bev.only_commits,
        only_releases=bev.only_releases,
        filepath=bev.filepath,
        only_modifications_with_file_types=bev.only_file_types,
    ).traverse_commits():
        modifications: List[Modification] = []

        for file in commit.modified_files:
            # skip file if targets were specified and file is not a target
            if len(bev.targets) > 0 and file.filename not in [str(p) for p in bev.targets]:
                continue

            # skip file if file types were specified and file type was not specified
            elif (
                bev.only_file_types is not None
                and Path(file.filename).suffix not in bev.only_file_types
            ):
                continue

            diff = file.diff_parsed
            old_path = Path(file.old_path) if file.old_path is not None else file.old_path
            new_path = Path(file.new_path) if file.new_path is not None else file.new_path

            modifications.append(
                Modification(
                    old_path=old_path,
                    new_path=new_path,
                    type=file.change_type,
                    added=diff["added"],
                    deleted=diff["deleted"],
                )
            )
        
        commits.append(Commit(
            author=commit.author.name,
            date=commit.author_date,
            modifications=modifications
        ))

    # with TemporaryDirectory() as _tmpdir:
    #     tmpdir = Path(_tmpdir)
    #     textual_log = tmpdir.joinpath("textual.log")
    #     GAnim.run(title="GAnim App", log=textual_log)


def main():
    """ganim entry point, returns Behaviour"""
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
        help="only analyses commits that are not merge commits",
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
        help="only commits that are tagged will be analyzed",
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

    bev = Behaviour(
        targets=args.target,
        repo_root=args.repo_root,
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
    ganim(bev)


if __name__ == "__main__":
    main()
