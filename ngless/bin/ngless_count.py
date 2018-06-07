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
                        help="SAM/BAM/CRAM file to count reads on")
    parser.add_argument("-o", "--output", required=True,
                        help="Output file/path for results")
    parser.add_argument("-f", "--features",
                        help="Feature to count")
    parser.add_argument("-m", "--multiple",
                        choices=["dist1", "all1", "1overN", "unique_only"],
                        help="How to handle multiple mappers")
    parser.add_argument("--auto-install", action="store_true",
                        help="Install NGLess if not found in PATH")
    parser.add_argument("--debug", action="store_true",
                        help="Prints the payload before submitting to ngless")

    return parser.parse_args()


def ngless_count(args):
    sc = NGLess.NGLess('0.8')
    e = sc.env
    e.samfile = sc.samfile_(args.input)


    feature = 'seqname'
    if args.features:
        feature = args.features
    count_opts = {}
    if args.multiple:
        count_opts['multiple'] = '{'+args.multiple+'}'
    e.counts = sc.count_(e.samfile,
                            features=[feature],
                            **count_opts)
    sc.write_(e.counts,
                ofile=args.output)

    sc.run(verbose=args.debug, auto_install=args.auto_install)

def main():
    args = parse_args()
    ngless_count(args)


if __name__ == "__main__":
    main()

# vim: ai sts=4 et sw=4
