# the developers' guide to ganim

an attempt to document what i do to develop and release ganim.

- [environment setup](#environment-setup)
  - [using devbox](#using-devbox)
  - [using poetry and python](#using-python-and-poetry)

- [contributing](#contributing)
  - [general workflow](#general-workflow)
  - [copyright waiver](#copyright-waiver)

- [releasing](#releasing)
  - [overview](#overview)
  - [metadata](#metadata)
  - [the src/releaser.py file](#the-srcreleaserpy-file)
    - [usage](#usage)
    - [error messages](#error-messages)
  - [tagged releases](#tagged-releases)
  - [nightly releases](#nightly-releases)

## environment setup

> **note**  
> alpine linux/musl users should install gcompat as a compatibilty layer if you
> fall into any `symbol not found` or zlib issues.  
> (pygit2/libgi2, a dependency of ganim uses zlib.)

### using devbox

i recommend you use [devbox](https://www.jetpack.io/devbox/)
(which uses [nix](https://nixos.org/)) to setup a hermetic environment.

```shell
devbox shell
```

### using python and poetry

prerequisites:

- [python 3.10+](https://python-poetry.org/)
- [poetry](https://www.python.org/)
- zlib (check your package manager!)

```shell
poetry install
poetry shell
```

## contributing

### general workflow

if you're new to contributing, your workflow should seem similar to this:

1. fork the respository or branch off the main branches (`main` or `future`)

2. make your changes

3. pull in any changes from the upstream `future` branch and resolve any conflicts, if any

4. commit your [copyright waiver](#copyright-waiver)

4. submit a pull request  

   (or mail in a diff if that's more your style)

### copyright waiver

as ganim [is dedicated to the public domain](/UNLICENCE), any contributors must waive
their copyrights before merging any contributions upstream.

when contributing your first changes, please include an empty commit for copyright waiver
using the following message:

```text
<Your Name/Username/Psuedonym> Copyright Waiver

I dedicate any and all copyright interest in this software to the
public domain.  I make this dedication for the benefit of the public at
large and to the detriment of my heirs and successors.  I intend this
dedication to be an overt act of relinquishment in perpetuity of all
present and future rights to this software under copyright law.
```

the command to create an empty commit from the command-line is:

```shell
git commit --allow-empty -m "..."
```

## releasing

### overview

there are two types of ganim releases:

- [`tagged` releases](#tagged-releases),
    where their workflows are ran when a new tag is pushed to a repository.
    a github release is created.

- [`nightly` releases](#nightly-releases),
    where their workflows are ran once a day if there are new commits.
    a build artifact is created, and is made accessible using <https://nightly.link>.

all releases are
[slsa v3 compliant](https://github.blog/2022-04-07-slsa-3-compliance-with-github-actions/).

### metadata

also: version bumping

files to track for metadata:

- [`src/ganim/__init__.py`](/src/ganim/__init__.py)  

    used as metadata source and for access via api

    **tl,dr:** update the `X.Y.Z` part of the string in the `VERSION` variable,
    and let [releaser.py](#the-srcreleaserpy-file) help you update other files.

    ```python
    NAME: Final[str] = (_about := __doc__.splitlines()[1]).split(":")[0].strip()
    DESCRIPTION: Final[str] = _about.split(":")[1].strip()
    BUILD_BRANCH: Final[str] = "local"
    BUILD_HASH: Final[str] = "latest"
    VERSION: Final[str] = f"0.1.0-edge+{BUILD_HASH[:10]}"
    ```

    the values of `NAME` and `DESCRIPTION` variables are taken from the second line of the
    module docstring (below the `"""`), so update that instead.

    the values of `BUILD_BRANCH` and `BUILD_HASH` are determined on build by
    [src/releaser.py](#the-srcreleaserpy-file). they default to `local` and `latest`
    respectively.

    the `VERSION` variable is a string that follows
    [semantic versioning](https://semver.org/). and should follow the following format:

    ```text
    <MAJOR>.<MINOR>.<PATCH>-edge+{BUILD_HASH}
    ```

    where `<MAJOR>`, `<MINOR>`, `<PATCH>` are updated accordingly.
    the `-edge+{BUILD_HASH}` portion is kept untouched for use in
    [nightly releases](#nightly-releases).

    **but what about alpha and beta releases?**  
    the appropriate variables will be determined from the semver portion of the tag.
    see [tagged releases](#tagged-releases) for more information.  
    any other release is a nightly release, so using `-edge+{BUILD_HASH}`
    works for this project.

    **important:** `BUILD_BRANCH`, `BUILD_HASH` and `VERSION` are updated using a lazy
    line replace. this means that for whatever reason, the expressions for these variable
    values should _not exceed a single line_.  
    however i see very little reason for these any by-hand changes to these variables to
    exceed one line. or any reason to change them other than the `x.y.z` portion of
    `VERSION`.

- [`pyproject.toml`](/poetry.toml)  

    used for wheel metadata

    wheel name, description and version are to be updated accordingly to be accurate with
    `src/ganim/__init__.py`, if updated manually.

    else, update `src/ganim/__init__.py` and use
    [the src/releaser.py file](#the-srcreleaserpy-file) to update `pyproject.toml`.

### the [src/releaser.py](/src/releaser.py) file

a helper script for release workflows.

#### usage

```text
commands
--------
info              prints ganim info to stderr
version           prints ganim long semver (<x>.<y>.<z>-edge+<hash>)
__init__.py       updates BUILD_BRANCH and BUILD_HASH and prints new file to stdout
  tagged <tag>      also updates VERSION based on semver portion of <tag>
  nightly           
pyproject.toml    updates name, description and version keys and prints new file to stdout
```

the script will **not** overwrite any files, so redirect stdout to overwrite the contents
of the targeted file.

```shell
$ # nightly example

$ grep BUILD src/ganim/__init__.py
BUILD_BRANCH: Final[str] = "local"
BUILD_HASH: Final[str] = "latest"
VERSION: Final[str] = f"0.0.2-edge+{BUILD_HASH[:10]}"

$ grep version pyproject.toml
version = "0.0.2"

$ python src/releaser.py __init__.py nightly > src/ganim/__init__.py
$ python src/releaser.py pyproject.toml > pyproject.toml

$ grep BUILD src/ganim/__init__.py
BUILD_BRANCH: Final[str] = "main"
BUILD_HASH: Final[str] = "10eeba443efb397322296e1ca374bdcec06e10b3"
VERSION: Final[str] = f"0.0.2-edge+{BUILD_HASH[:10]}"

$ grep version pyproject.toml
version = "0.0.2-edge+10eeba443e"
```

```shell
$ # tagged example

$ grep BUILD src/ganim/__init__.py
BUILD_BRANCH: Final[str] = "local"
BUILD_HASH: Final[str] = "latest"
VERSION: Final[str] = f"0.9.0-edge+{BUILD_HASH[:10]}"

$ grep version pyproject.toml
version = "0.9.0"

$ python src/releaser.py __init__.py tagged v1.0.0-rc.1 > src/ganim/__init__.py
$ python src/releaser.py pyproject.toml > pyproject.toml

$ grep BUILD src/ganim/__init__.py
BUILD_BRANCH: Final[str] = "main"
BUILD_HASH: Final[str] = "120d7bed6074a176894db4152019436a2987415b"
VERSION: Final[str] = f"1.0.0-rc.1"

$ grep version pyproject.toml
version = "1.0.0-rc.1"
```

#### error messages

here are some error messages you may encounter:

- `error: incorrect command usage (see DEVELOPING.md#usage)`  
    `error: no command (see DEVELOPING.md#usage)`

    self-descriptive, see [usage](#usage).

- `error: semver parser error '...'`  

    ValueError exception handling from `semver.Version.parse()`.
    see exception message in single quotes for further direction.

### tagged releases

TODO

### nightly releases

TODO
