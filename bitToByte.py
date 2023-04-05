#! /usr/bin/env python3
import argparse
import seqparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile")
    parser.add_argument("outputfile")
    parser.add_argument("--newline_on", default="0D count")
    parser.add_argument('--onlybits', default=False, action='store_true')

    args = parser.parse_args()
    count = 0
    with open(args.inputfile) as f, open(args.outputfile, "w") as g:
        g.write(
            seqparse.alignBytes(
                seqparse.packBytes(
                    f.read(), hexPassthrough=not args.onlybits),
                args.newline_on)
        )
