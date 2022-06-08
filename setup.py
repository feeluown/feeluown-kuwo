from setuptools import setup


setup(
    name='fuo_kuwo',
    version='0.1.6',
    packages=['fuo_kuwo', 'fuo_kuwo.enc'],
    package_data={
        '': ['assets/*.svg']
    },
    url='https://github.com/feeluown/feeluown-kuwo',
    license='GPL',
    author='BruceZhang1993',
    author_email='zttt183525594@gmail.com',
    description='Kuwo music provider for FeelUOwn music player',
    keywords=['feeluown', 'plugin', 'kuwo'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3 :: Only',
    ],
    install_requires=[
        'feeluown>=3.7.7',
        'requests',
        'marshmallow'
    ],
    entry_points={
        'fuo.plugins_v1': [
            'kuwo = fuo_kuwo',
        ]
    },
)
