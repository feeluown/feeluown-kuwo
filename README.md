# Kuwo music provider for FeelUOwn player

## Installation

### Arch Linux
`pacman -S feeluown-kuwo`

### Install from pypi
`pip install --user feeluown-kuwo`

### Install with pip
`pip install --user .`

## Development with poetry
`poetry install` to create venv and start development.
`poetry run pre-commit install` to setup git pre-commit hooks.
`poetry run poetry2setup > setup.py` before commit.

## Run tests
`pytest -v`

test_kuwo_api.py -- Kuwo API tests

## Changelog

### v0.2.2 (2024-01-04)
* 适配 FeelUOwn 最新代码（兼容 v3.8.15 及以上）
* API 仍然不可用

### v0.2.1 (2023-07-15)
* 修复 API 不可用的问题

### v0.2.0 (2023-07-13)
* 修复 API 不可用的问题
* 适配 feeluown v2 model，废弃 v1 models

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
