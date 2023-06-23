"""
ganim: animating a repositories' history using git and textual
--------------------------------------------------------------
by mark <mark@joshwel.co>

This file is part of ganim, which is free and unencumbered software released into the
public domain. See <https://unlicense.org> for more information or the UNLICENSE file
included with the ganim source code.
"""

from typing import Final

# note: be wary when changing these!, or src/releaser.py may raise errors.
#       see DEVELOPING.md#metadata on the whys, whats and hows.

NAME: Final[str] = (_about := __doc__.splitlines()[1]).split(":")[0].strip()
DESCRIPTION: Final[str] = _about.split(":")[1].strip()
BUILD_BRANCH: Final[str] = "local"
BUILD_HASH: Final[str] = "latest"
VERSION: Final[str] = f"0.1.0-edge+{BUILD_HASH[:10]}"

from .app import GAnim
from .cli import run
from .utils import Behaviour, process_args
from .widgets import CommitManager, ContentView, FileManager
