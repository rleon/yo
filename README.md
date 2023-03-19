# Collection of routine tasks in one package

This is a set of common scripts designed to help perform daily routines
efficiently.

# Documentation

**yo** is like **git**. It incorporates multiple internal commands under the
**yo** multiplexer. Each command has man-page style documentation that can be
viewed with **yo cmd --help**, or online as linked below:

* **[yo upload](docs/yo_upload.1.md)**
* **[yo setup](docs/yo_setup.1.md)**
* **[yo push](docs/yo_push.1.md)**
* **[yo verify](docs/yo_verify.1.md)**
* **[yo web](docs/yo_web.1.md)**

# Installation

The tools are currently designed to run from a source tree and **not** as root.
Clone the repository, and link the main tool into your path:

```sh
$ cd /swgwork/`whoami`
$ git clone https://github.com/rleon/yo.git
$ ln -s /swgwork/`whoami`/yo/yo ~/bin/
```

This assumes your shell profile has configured ~/bin/ to be in your local
search path, with something like this in the .bash_profile:

```sh
PATH=$PATH:$HOME/bin
```

From time to time, **git pull** to get the latest version.

## Command line argument completion

**yo** support command line argument completion, however it relies on python
argcomplete to be enabled in the shell. Follow the directions
https://pypi.org/project/argcomplete/#global-completion to enable this for
your shell of choice.

Several other commonly used tools make use of this, so it is recommended to
enable it globally.
