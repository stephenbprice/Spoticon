from setuptools import setup

setup(
    name = 'spoticon',
    version = '0.1.0',
    description = 'Spotify in the console',
    url = 'https://github.com/stephenbprice/spoticon',
    keywords = ['spotify', 'console', 'curses', 'audio', 'music'],

    author = 'Stephen Price',
    author_email = 'stephen.b.price@gmail.com',
    license = 'MIT',

    packages = ['spoticon'],
    include_package_data = True,
    install_requires = ['spotipy', 'PIL', 'numpy'],
    entry_points = {'console_scripts': ['spoticon=spoticon.main:run']},
    classifiers = [],
)

