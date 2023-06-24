<div align="center">

<!-- [![logo](https://raw.githubusercontent.com/)](https://github.com/markjoshwel/ganim) -->

# ganim

animating a repositories' history using git and textual.

![project hits](https://img.shields.io/endpoint?url=https://hits.dwyl.com/markjoshwel/ganim.json&style=flat-square&label=hits&color=6244bb)
![lines of code](https://img.shields.io/tokei/lines/github/markjoshwel/ganim?style=flat-square&label=loc&color=6244bb)
[![licence](https://img.shields.io/github/license/markjoshwel/ganim?style=flat-square&label=licence&color=6244bb)](/UNLICENSE)

</div>

---

inspired by [mitxela/git-animate](https://github.com/mitxela/git-animate), as shown in his
[swotGB video](https://www.youtube.com/watch?v=i08S5qolgvc&t=29s).

> **Note**  
> this project was archived on the 31st March 2022.
> see the old code in the [`old`](https://github.com/markjoshwel/ganim/tree/old) branch.

- [installation](#installation)
- [usage](#usage)
- [developing and contributing](/DEVELOPING.md)
- [licence](#licence)

## installation

prerequisites:

- python 3.10 or newer

```text
pip install git+https://github.com/markjoshwel/ganim@main
```

any `libz.so.1: cannot open shared object file` issues should be easily solved by
installing zlib. check your package manager!

> **Note**  
> alpine linux/musl users should install gcompat as a compatibilty layer if you
> fall into any zlib `symbol not found` issues.

## usage

TODO

### actions

during the animation, you can execute the following actions using these key bindings:

view toggles

- `f`: toggle current file view
- `c`: toggle commit history log view

playback co ntrols

- `p`: play/pause
- `[`: decrement wpm by 50
- `]`: increment wpm by 50

meta

- `q`: quit

## licence

surplus is free and unencumbered software released into the public domain.
for more information, please refer to the [UNLICENCE](/UNLICENCE) file,
<http://unlicense.org/> or the python module docstring.
