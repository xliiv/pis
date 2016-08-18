import setuptools
import sys

from pis import __version__


if int(sys.version[0]) < 3:
    print("Only Python 3.x supported")
    sys.exit(1)


setuptools.setup(
    name="pis",
    version=__version__,
    url="http://github.com/xliiv/pis",

    author="xliiv",
    author_email="tymoteusz.jankowski@gmail.com",

    description=(
        'Install python package as cloned repo from guessed VCS'
        ' (git, hg, etc.) repository.'
    ),
    long_description=open('README.md').read(),
    license='MIT',

    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=[],

    entry_points={
        'console_scripts': [
            'pis = pis.main:main',
        ],
    },

    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
)
