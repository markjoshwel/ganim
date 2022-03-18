# ganim

Animating the history of a file using Git. Inspired by
[mitxela/git-animate](https://github.com/mitxela/git-animate), shown in his
[swotGB video](https://www.youtube.com/watch?v=i08S5qolgvc&t=29s).

- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Roadmap

- [x] 0.0.1: **Proof of Concept**  
  _This version of ganim can be seen in the [main](https://github.com/markjoshwel/ganim/tree/main) branch._

- [ ] 0.1.0: **Practical Concept**

- [ ] 0.2.0: **Syntax Highlighting**

## Installation

Prerequisites:

- Python 3.7 or newer
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

To process and animate one file, you can run the following:

```text
ganim ganim.py
```

To process and animate multiple files, you can run the following:

```text
ganim ganim.py README.md
```

To process and animate files only by the author "Mark Joshwel" (thats me!), you can run
the following:

```text
ganim ganim.py --only_authors "Mark Joshwel"
```

To process and animate only files ending with ".py", you can run the following:

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
