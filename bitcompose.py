#! /usr/bin/env python3
import argparse
from bitparse import encodeByte

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile")
    parser.add_argument("outputfile")

    args = parser.parse_args()

    firstHeader = True
    with open(args.inputfile) as f, open(args.outputfile, "w") as of:
        for w in f.read().split():
            w = w.strip()
            if len(w) == 2:
                w = encodeByte(int(w, 16))
            if w == "H":
                if firstHeader:
                    firstHeader = False
                else:
                    of.write(" "*1200)
                of.write("1"*3600)
            else:
                of.write(w)
