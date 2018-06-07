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
    parser.add_argument("-i", "--input", required=True,
                        help="SAM/BAM/CRAM file filter")
    parser.add_argument("-o", "--output", required=True,
                        help="Output file/path for results")
    parser.add_argument("-a", "--action", required=True,
                        choices=["keep_if", "drop_if"],
                        help="Whether to keep or drop when condition are met")
    parser.add_argument("-c", "--conditions", required=True, nargs="+",
                        choices=["mapped", "unmapped", "unique"],
                        help="One or more conditions to filter on")
    parser.add_argument("--auto-install", action="store_true",
                        help="Install NGLess if not found in PATH")
    parser.add_argument("--debug", action="store_true",
                        help="Prints the payload before submitting to ngless")

    return parser.parse_args()


def ngless_select(args):
    print(args)
    select_opts = {
            args.action : ['{'+c+'}' for c in args.conditions]
            }
    sc = NGLess.NGLess('0.8')
    e = sc.env
    e.samfile = sc.samfile_(args.input)
    e.selected = sc.select_(e.samfile, **select_opts)
    sc.write_(e.selected,
                ofile=args.output)
    sc.run(verbose=args.debug, auto_install=args.auto_install)

def main():
    args = parse_args()
    ngless_select(args)


if __name__ == "__main__":
    main()

# vim: ai sts=4 et sw=4
