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
                        help="FastQ file with reads to map (forward)")
    parser.add_argument("-i2", "--input-reverse",
                        help="FastQ file with reads to map (reverse) - if paired end")
    parser.add_argument("-s", "--input-singles",
                        help="FastQ file with reads to map (singles) - if paired end and unpaired reads exist")
    parser.add_argument("-o", "--output", required=True,
                        help="Output file/path for results")
    parser.add_argument("--auto-install", action="store_true",
                        help="Install NGLess if not found in PATH")
    parser.add_argument("--debug", action="store_true",
                        help="Prints the payload before submitting to ngless")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-r", "--reference",
                       choices=["sacCer3", "ce10", "dm3", "gg4", "canFam2",
                                "rn4", "bosTau4", "mm10", "hg19"],
                       help="Map against a builtin reference")
    group.add_argument("-f", "--fasta",
                       help="Map against a given fasta file (will be indexed if index is not available)")

    args = parser.parse_args()

    if args.input_singles and not args.input_reverse:
        parser.error("--input-singles cannot be used without --input-reverse, use --input instead")

    if args.input_reverse:
        args.target = "paired"
    else:
        args.target = "fastq"

    return args


def ngless_map(args):
    sc = NGLess.NGLess('0.8')
    e = sc.env
    if args.input_reverse:
        paired_args = {}
        if args.input_singles:
            paired_args['singles'] = args.input_singles
        e.input = sc.paired_(args.input, args.input_reverse, **paired_args)
    else:
        e.input = sc.fastq_(args.input)
    if args.reference:
        map_opts = {'reference': args.reference}
    elif args.fasta:
        map_opts = {'fafile': args.fasta}
    else:
        raise ValueError("Missing argument. Either --reference or --fasta must be used")
    e.mapped = sc.map_(e.input, **map_opts)
    sc.write_(e.mapped,
                ofile=args.output)

    sc.run(verbose=args.debug, auto_install=args.auto_install)

def main():
    ngless_map(parse_args())


if __name__ == "__main__":
    main()

# vim: ai sts=4 et sw=4
