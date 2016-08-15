#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os

from pis.config import (
    config_user_path,
    read_config,
    write_config,
)
from pis import __version__
from pis import lib


def main():
    #TODO:: these lines are module cli, and here is's imported only
    parser = argparse.ArgumentParser(
        prog='pis',
        description=(
            'Install python package as cloned repo from guessed VCS'
            ' (git, hg, etc.) repository.'
        ),
    )
    #TODO::
    #parser.add_argument(
    #    '-d', '--destiny-dir', action='store', default=os.getcwd(),
    #)
    parser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s {}'.format(__version__),
    )
    parser.add_argument(
        'pkg_names', nargs='+',
    )
    args = parser.parse_args()
    if args.pkg_names:
        config = read_config(config_user_path)
        #founds = lib.source_install(args.pkg_names, args.destiny_dir, config)
        founds = lib.source_install(args.pkg_names, os.getcwd(), config)
        if founds:
            for pkg_name, repo_url in founds.items():
                config['pkg_name2repo_url'][pkg_name] = repo_url
                write_config(config_user_path, config)


if __name__ == "__main__":
    main()
