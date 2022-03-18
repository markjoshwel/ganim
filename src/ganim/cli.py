# ganim.cli: Command line entry point and argument parsing
#
# This file is part of ganim, which is dedicated to the public domain.
# See <https://unlicense.org/> for more information or the UNLICENSE file included with
# the ganim source code.

from . import utils, app


def run() -> None:
    """ganim entry point"""
    behaviour = utils.process_args()
    commits = utils.process_repo(behaviour)

    try:
        import uvloop

    except ImportError:
        pass

    else:
        uvloop.install

    app.GAnim.run(behaviour=behaviour, commits=commits)
