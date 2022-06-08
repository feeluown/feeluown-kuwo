# Kuwo music provider for FeelUOwn player

## Installation

### Arch Linux
`pacman -S feeluown-kuwo`

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

### v0.1.6 (2022-06-08)
* 修复获取歌曲/mv播放链接有一定概率会失败的问题

### v0.1.5 (2021-11-06)
* 处理 html 字符实体

### v0.1.4 (2021-05-27)
* 处理 html 字符实体

### v0.1.3 (2021-04-23)
* 加了个图标
* 支持网页登录
* 支持加载个人收藏的播放列表

### v0.1.2 (2020-10-18)
* 使用 SequentialReader

### v0.1.1 (2020-06-05)
* fix the issue that fuo-kuwo can't be installed without install_requries

### v0.1 (2020-06-05)
* support fetching song/artist/album/playlist detail
* support searching
