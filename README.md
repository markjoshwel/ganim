# ganim

Animating the history of a file using Git.

- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Installation

Prerequisites:

- Python 3.8 or newer
- Git 1.7.0 or newer

### From pip

```text
pip install ganim
```

For (small) speed gains, you can install `ganim[uvloop]` instead.

### From main

```text
git clone https://github.com/markjoshwel/ganim.git
```

You can then either use pip to install the dependencies from requirements.txt, or use
Poetry instead.

## Usage

```text
usage: ganim [-h] [--repo_root REPO_ROOT] [--easing_style {...}] [--easing_duration EASING_DURATION]
             [--theme {...}] [--line_numbers {True,False}] [--indent_guides {True,False}]
             [--word_wrap {True,False}] [--from_commit FROM_COMMIT] [--to_commit TO_COMMIT]
             [--from_tag FROM_TAG] [--to_tag TO_TAG] [--only_in_branch ONLY_IN_BRANCH]
             [--only_no_merge {True,False}] [--only_authors ONLY_AUTHORS [ONLY_AUTHORS ...]] 
             [--only_commits ONLY_COMMITS [ONLY_COMMITS ...]]
             [--only_releases {True,False}] [--filepath FILEPATH]
             [--only_file_types ONLY_FILE_TYPES [ONLY_FILE_TYPES ...]]
             [target ...]

animating the history of a file using git

positional arguments:
  target                target file paths, defaults to all files

options:
  -h, --help            show this help message and exit
  --repo_root REPO_ROOT
                        path to repo, defaults to cwd
  --easing_style {...}  specify textual easing style
  --easing_duration EASING_DURATION
                        specify easing duration, defaults to 0.75
  --wpm WPM             specify words per minute

code syntax args:
  see https://rich.readthedocs.io/en/stable/syntax.html

  --theme {...}
                        specifies a pygments theme to display file contents in
  --line_numbers {True,False}
                        enable indent guides, defaults to False
  --indent_guides {True,False}
                        enable indent guides, defaults to False
  --word_wrap {True,False}
                        enable word wrapping, defaults to False

commit range arguments:
  see https://pydriller.readthedocs.io/en/latest/repository.html#selecting-the-commit-range

  --from_commit FROM_COMMIT
                        starting commit
  --to_commit TO_COMMIT
                        ending commit
  --from_tag FROM_TAG   starting the analysis from specified tag
  --to_tag TO_TAG       ending the analysis from specified tag

commit_filter_args:
  see https://pydriller.readthedocs.io/en/latest/repository.html#filtering-commits

  --only_in_branch ONLY_IN_BRANCH
                        only analyses commits that belong to this branch
  --only_no_merge {True,False}
                        only analyses commits that are not merge commits, defaults to False
  --only_authors ONLY_AUTHORS [ONLY_AUTHORS ...]
                        only analyses commits that are made by these authors' usernames
  --only_commits ONLY_COMMITS [ONLY_COMMITS ...]
                        only these commits will be analyzed
  --only_releases {True,False}
                        only commits that are tagged will be analyzed, defaults to False
  --filepath FILEPATH   only commits that modified this file will be analyzed
  --only_file_types ONLY_FILE_TYPES [ONLY_FILE_TYPES ...]
                        only show histories of certain file types, e.g. '.py'
```

### Examples

```text
ganim ganim.py
```

```text
ganim ganim.py --only_authors "markjoshwel" --only_no_merge True
```

```text
ganim --only_file_types ".py"
```

### Actions

During the animation, you can execute the following actions using these key bindings:

- `f`: Toggle file tree
- `c`: Toggle commit history log
- `q`: Quit

## Contributing

When contributing your first changes, please include an empty commit for copyright waiver
using the following message (replace 'John Doe' with your name or nickname):

```text
John Doe Copyright Waiver

I dedicate any and all copyright interest in this software to the
public domain.  I make this dedication for the benefit of the public at
large and to the detriment of my heirs and successors.  I intend this
dedication to be an overt act of relinquishment in perpetuity of all
present and future rights to this software under copyright law.
```

The command to create an empty commit from the command-line is:

```shell
git commit --allow-empty
```

## License

ganim is unlicensed with The Unlicense. In short, do whatever. You can find copies of
the license in the [UNLICENSE](UNLICENSE) file or in the
[ganim module docstring](ganim.py).
