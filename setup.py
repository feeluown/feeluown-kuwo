# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['fuo_kuwo', 'fuo_kuwo.enc', 'fuo_kuwo.pages']

package_data = \
{'': ['*'], 'fuo_kuwo': ['assets/*']}

install_requires = \
['feeluown>=3.8.12', 'marshmallow', 'requests']

entry_points = \
{'fuo.plugins_v1': ['kuwo = fuo_kuwo']}

setup_kwargs = {
    'name': 'fuo-kuwo',
    'version': '0.2.0',
    'description': 'Kuwo music provider for FeelUOwn music player',
    'long_description': "# Kuwo music provider for FeelUOwn player\n\n## Installation\n\n### Arch Linux\n`pacman -S feeluown-kuwo`\n\n### Install from pypi\n`pip install --user feeluown-kuwo`\n\n### Install with pip\n`pip install --user .`\n\n## Development with poetry\n`poetry install` to create venv and start development.\n`poetry run pre-commit install` to setup git pre-commit hooks.\n`poetry run poetry2setup > setup.py` before commit.\n\n## Run tests\n`pytest -v`\n\ntest_kuwo_api.py -- Kuwo API tests\n\n## Changelog\n\n### v0.2.0 (2023-07-13)\n* 修复 API 不可用的问题\n* 适配 feeluown v2 model，废弃 v1 models\n\n### v0.1.6 (2022-06-08)\n* 修复获取歌曲/mv播放链接有一定概率会失败的问题\n\n### v0.1.5 (2021-11-06)\n* 处理 html 字符实体\n\n### v0.1.4 (2021-05-27)\n* 处理 html 字符实体\n\n### v0.1.3 (2021-04-23)\n* 加了个图标\n* 支持网页登录\n* 支持加载个人收藏的播放列表\n\n### v0.1.2 (2020-10-18)\n* 使用 SequentialReader\n\n### v0.1.1 (2020-06-05)\n* fix the issue that fuo-kuwo can't be installed without install_requries\n\n### v0.1 (2020-06-05)\n* support fetching song/artist/album/playlist detail\n* support searching\n",
    'author': 'feeluown team',
    'url': 'https://github.com/feeluown/feeluown-kuwo',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)

