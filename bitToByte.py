#! /usr/bin/env python3
import argparse


def toByte(s):
    if len(s) != 11 or s[0] != '0' or s[-2:] != "11":
        print(f"invalid [{s}]")
        return
    n = 0
    for i, ch in enumerate(s[1:-2]):
        if ch == "1":
            n += 1 << i
        elif ch != "0":
            raise Exception("Unknown chunck", s)
    return f"{n:02X}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile")
    parser.add_argument("outputfile")
    parser.add_argument("--newline_on", default="0D count")

    args = parser.parse_args()
    count = 0
    with open(args.inputfile) as f, open(args.outputfile, "w") as g:
        for chunk in f.read().split():
            ab = toByte(chunk)
            if ab:
                g.write(ab)
                if ab == "0D" and "0D" in args.newline_on:
                    g.write("\n")
                    count = 0
            else:
                if "error" in args.newline_on:
                    g.write("\n"+chunk+"\n")
                else:
                    g.write(chunk)
                    if chunk == "0D" and "0D" in args.newline_on:
                        g.write("\n")
                        count = 0
            if count == 15 and "count" in args.newline_on:
                g.write("\n")
                count = 0
            else:
                g.write(" ")
            count += 1
