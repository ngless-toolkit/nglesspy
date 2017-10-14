#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from ngless import NGLess

try:
    import argparse
except ImportError:
    print("argparse not found. Please install argparse with 'pip install argparse'")
    sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--force", action="store_true",
                        help="Install NGLess even if it is already found")

    parser.add_argument("-t", "--target",
                        help="Output file/path for results")

    parser.add_argument("-m", "--mode", choices=["user", "global"],
                        help="Global or user install")

    parser.add_argument("--verbose", action="store_true",
                        help="Verbose mode")

    return parser.parse_args()


def main():
    from ngless import install
    args = parse_args()
    if not args.mode and not args.target:
        from sys import stderr, exit
        stderr.write("Either --mode or --target are required arguments (use -h to see full help)")
        exit(1)
    i = install.install_ngless(mode=args.mode, target=args.target, force=args.force, verbose=args.verbose)
    if not i and args.verbose:
        print("NGLess already installed. Use --force to re-install.")

if __name__ == "__main__":
    main()

# vim: ai sts=4 et sw=4
