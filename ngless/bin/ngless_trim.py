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
                        help="FastQ file with reads to trim")
    parser.add_argument("-o", "--output", required=True,
                        help="Output file/path for results")
    parser.add_argument("-m", "--method", required=True,
                        choices=["substrim", "endstrim"],
                        help="Which trimming method to use")
    parser.add_argument("-q", "--min-quality", type=int, required=True,
                        help="Minimum quality value")
    parser.add_argument("-d", "--discard", type=int, default=50,
                        help="Discard if shorted than")
    parser.add_argument("--auto-install", action="store_true",
                        help="Install NGLess if not found in PATH")
    parser.add_argument("--debug", action="store_true",
                        help="Prints the payload before submitting to ngless")

    return parser.parse_args()


def ngless_trim(args):
    sc = NGLess.NGLess('0.8')
    e = sc.env
    e.input = sc.fastq_(args.input)

    @sc.preprocess_(e.input, using='r')
    def proc(bk):
        bk.r = sc.function(args.method)(bk.r, min_quality=args.min_quality)
        sc.if_(sc.len_(bk.r) < args.discard,
                sc.discard_)

    sc.write_(e.input,
                ofile=args.output)

    sc.run(verbose=args.debug, auto_install=args.auto_install)

def main():
    args = parse_args()
    ngless_trim(args)


if __name__ == "__main__":
    main()

# vim: ai sts=4 et sw=4
