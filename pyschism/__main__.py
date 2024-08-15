#! /usr/bin/env python
import argparse
import inspect
import sys

from pyschism.cmd import *


def main():

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="clitype")

    clitypes = [
        clitype
        for cliname, clitype in inspect.getmembers(
            sys.modules[__name__], inspect.isclass
        )
        if "Cli" in cliname
    ]

    for clitype in clitypes:
        clitype.add_subparser_action(subparsers)

    args = parser.parse_args()

    for clitype in clitypes:
        if args.clitype.replace("_", "") == f"{clitype.__name__.lower()[:-3]}":
            clitype(args)
            break


if __name__ == "__main__":
    main()
