#! /usr/bin/env python3
import sys
import argparse


def extractBas(bin, start):
    a = start
    print(f"Extracting from {a:04x}")
    while (size := bin[a]) != 0:
        ret = a+4+size+1
        if bin[ret] != 0x0D:
            raise Exception("Line end not found")
        a = ret+1
    print(f"final addr {a:04x}")
    return bin[start:a+1]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile")
    parser.add_argument("outputfile")
    parser.add_argument("--start_addr", default="9800",
                        type=lambda s: int(s, 16))
    args = parser.parse_args()

    with open(args.inputfile, "rb") as f, open(args.outputfile, "wb") as out:
        out.write(extractBas(f.read(), args.start_addr))
