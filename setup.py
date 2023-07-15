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
    'version': '0.2.1',
    'description': 'Kuwo music provider for FeelUOwn music player',
    'author': 'feeluown team',
    'url': 'https://github.com/feeluown/feeluown-kuwo',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)

