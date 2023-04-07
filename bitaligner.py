#! /usr/bin/env python3
import argparse
import seqparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile")
    parser.add_argument("outputfile")

    args = parser.parse_args()
    with open(args.inputfile) as f:
        data = f.read()
        with open(args.outputfile, "w") as of:
            of.write(seqparse.splitBits(data))
