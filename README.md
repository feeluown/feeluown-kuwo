# Kuwo music provider for FeelUOwn player

## Installation

### Arch Linux
`yay -S feeluown-kuwo` (Replace yay with your favorite AUR manager)

Included in [Arch Linux CN Repository](https://www.archlinuxcn.org/archlinux-cn-repo-and-mirror/).

### Install from pypi
`pip install --user feeluown-kuwo`

### Install with pip
`pip install --user .`

## Development with pipenv
`pipenv install` to create venv and start development.

## Run tests
`pytest -v`

test_kuwo_api.py -- Kuwo API tests

## Changelog

### v0.1.1 (2020-06-05)
* fix the issue that fuo-kuwo can't be installed without install_requries

### v0.1 (2020-06-05)
* support fetching song/artist/album/playlist detail
* support searching
