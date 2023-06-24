"""
ganim.utils: internal helper utility functions and data structures
------------------------------------------------------------------
by mark <mark@joshwel.co>

This file is part of ganim, which is free and unencumbered software released into the
public domain. See <https://unlicense.org> for more information or the UNLICENSE file
included with the ganim source code.
"""

from argparse import ArgumentParser
from typing import Final, NamedTuple

from . import BUILD_BRANCH, BUILD_HASH, NAME, VERSION


class Behaviour(NamedTuple):  # TODO
    ...


def process_args() -> Behaviour:  # TODO
    parser = ArgumentParser(prog="ganim", description="")

    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        default=False,
        help="prints version information to stdout and exits",
    )

    args = parser.parse_args()

    if args.version:
        print(
            f"ganim {VERSION} on {BUILD_BRANCH}@{BUILD_HASH[:10]}"
            if "+" not in VERSION
            else f"ganim {VERSION} on {BUILD_BRANCH}"
        )
        exit()

    return Behaviour()
