"""
ganim release helper
--------------------
by mark <mark@joshwel.co>

see DEVELOPING.md for more information about this script.

This file is part of ganim, which is free and unencumbered software released into the
public domain. See <https://unlicense.org> for more information or the UNLICENSE file
included with the ganim source code.
"""

from pathlib import Path
from sys import argv, stderr

import tomlkit
from pygit2 import Repository  # type: ignore
from semver import Version

import ganim

REPLACE_LINES: tuple[str, str, str] = (
    "BUILD_BRANCH: Final[str] = ",
    "BUILD_HASH: Final[str] = ",
    "VERSION: Final[str] = ",
)

PATH_ROOT = Path(__file__).parent.parent
PATH_REPO = PATH_ROOT.joinpath(".git")
PATH_INIT = PATH_ROOT.joinpath("src/ganim/__init__.py")
PATH_PYPROJ = PATH_ROOT.joinpath("pyproject.toml")

assert (
    PATH_REPO.exists() and PATH_REPO.is_dir()
), f"{PATH_REPO} is not a git repository, are you running in repo root?"
assert (
    PATH_INIT.exists() and PATH_INIT.is_file()
), f"{PATH_INIT} does not exist, are you running in repo root?"
assert (
    PATH_PYPROJ.exists() and PATH_PYPROJ.is_file()
), f"{PATH_PYPROJ} does not exist, are you running in repo root?"


def main(argv: list[str] = argv) -> int:
    # stderr.write(f"{argv[1:]=}\n")

    current_branch = "unknown"
    latest_commit_hash = "unknown"
    tag: str | None = None

    repo = Repository(PATH_REPO)
    current_branch = repo.head.shorthand
    latest_commit_hash = repo[repo.head.target].hex

    match argv[1:]:
        case ["info"]:
            stderr.write(
                f"{PATH_ROOT=}\n"
                f"{PATH_REPO=}\n"
                f"{PATH_INIT=}\n"
                f"{PATH_PYPROJ=}\n"
                "\n"
                f"{ganim.NAME=}\n"
                f"{ganim.DESCRIPTION=}\n"
                f"{ganim.VERSION=}\n"
                f"{ganim.BUILD_BRANCH=}\n"
                f"{ganim.BUILD_HASH=}\n"
                "\n"
                f"{current_branch=}\n"
                f"{latest_commit_hash=}\n"
            )

        case ["version"]:
            print(f"{ganim.VERSION}")

        case ["__init__.py", "tagged", tag]:
            try:
                version = Version.parse(tag.removeprefix("v"))

            except ValueError as exc:
                stderr.write(f"error: semver parser error '{exc}'\n")
                return -2

            # shared code
            with open(PATH_INIT, "r") as initfd:
                init = initfd.readlines()

                for find, replace in zip(
                    REPLACE_LINES,
                    (
                        f'BUILD_BRANCH: Final[str] = "{current_branch}"\n',
                        f'BUILD_HASH: Final[str] = "{latest_commit_hash}"\n',
                        f'VERSION: Final[str] = "{version}"\n',
                    ),
                ):
                    for idx, line in enumerate(init):
                        if line.startswith(find):
                            init[idx] = replace

                print("".join(init))

        case ["__init__.py", "nightly"]:
            # shared code (minus use of VERSION)
            with open(PATH_INIT, "r") as initfd:
                init = initfd.readlines()

                for find, replace in zip(
                    REPLACE_LINES,
                    (
                        f'BUILD_BRANCH: Final[str] = "{current_branch}"\n',
                        f'BUILD_HASH: Final[str] = "{latest_commit_hash}"\n',
                    ),
                ):
                    for idx, line in enumerate(init):
                        if line.startswith(find):
                            init[idx] = replace

                print("".join(init))

        case ["pyproject.toml"]:
            with open(PATH_PYPROJ, "r", encoding="utf-8") as pyprofd:
                pyproject = tomlkit.parse(pyprofd.read())

                try:
                    pyproject["tool"]["poetry"]["name"] = ganim.NAME  # type: ignore
                    pyproject["tool"]["poetry"]["description"] = ganim.DESCRIPTION  # type: ignore
                    pyproject["tool"]["poetry"]["version"] = ganim.VERSION  # type: ignore

                except Exception as exc:
                    stderr.write(
                        f"error when updating pyproject: {exc}"
                        f" ({exc.__class__.__name__})\n"
                    )
                    return -2

                print(tomlkit.dumps(pyproject))

        case (["__init__.py"] | ["__init__.py", _] | ["__init__.py", "tagged"]):
            stderr.write(f"error: incorrect command usage (see DEVELOPING.md#usage)\n")
            return -1

        case []:
            stderr.write(f"error: no command (see DEVELOPING.md#usage)\n")
            return -1

    return 0


if __name__ == "__main__":
    exit(main())
