"""
ganim: animating a repositories' history using git and textual
--------------------------------------------------------------
by mark <mark@joshwel.co>

This file is part of ganim, which is free and unencumbered software released into the
public domain. See <https://unlicense.org> for more information or the UNLICENSE file
included with the ganim source code.
"""

from . import app, utils


def run() -> None:
    """ganim command-line entry point"""
    behaviour = utils.process_args()

    try:
        import uvloop

    except ImportError:
        pass

    else:
        uvloop.install()

    ganim = app.GAnim(behaviour=behaviour)
    ganim.run()
