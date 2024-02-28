#! /usr/bin/env python3
import argparse
import sc3000decoder as sc
from pathlib import Path


def convertFileContent(inputfile, binary, keepPastEnd):
    errors = 0
    of = bytearray()
    if binary:
        toks = [f"{v:02X}" for v in open(inputfile, "rb").read()]
    else:
        toks = open(inputfile).read().split()
    idx_list = [idx + 1 for idx, val in
                enumerate(toks) if val == "0D"]
    if len(idx_list) == 0:
        lines = toks
    else:
        lines = [toks[i: j] for i, j in
                 zip([0] + idx_list, idx_list +
                 ([len(toks)] if idx_list[-1] != len(toks) else []))]

    head = []
    for ci, line in enumerate(lines):
        if not keepPastEnd and line[:1] == ["00"]:
            # print("END MARKER")
            break
        if ci == len(lines)-1:
            line = line[:int(line[0], 16)]

        if len(line) <= 3:
            head = line
            continue
        else:
            line = head+line
            head = []
        while "H" in line:
            s = line.index("H")+1
            if line[s] == "16":
                print("found header")
                h = line[s+1:s+1+16]
                print(" ".join([c for c in h]))
                print(" ".join([f" {chr(int(c,16))}" for c in h]))
            print("cut", line)
            line = line[line.index("H")+2:]
            print("to", line)

        # of.write(f"\n {line} \n")
        try:
            joined = "".join(line)
            di, lineNo, res = sc.decode_one_line(
                joined, suppress_error=False)
            if len(joined) != di:
                of.extend(
                    bytearray(
                        f"#len mismatch {di} {len(joined)}:{lineNo} {res}", "utf-8"))
                errors += 1
            else:
                of.extend(bytearray(f"{lineNo} {res}", "utf-8"))
        except Exception as e:
            print(line, str(e))
            of.extend(bytearray("#"+str(e), "utf-8"))
            errors += 1
        of.extend(bytearray("\r", "utf-8"))
    return of, errors


def outname(outputPath, errors, version):
    if version == 0:
        vs = ""
    else:
        vs = f".v{version}"
    if errors == 0:
        es = ""
    else:
        es = f"[{errors}]"
    return str(outputPath)+es+vs+".basic"


def convertVersionedFile(inputfile, outputPath, binary, keepPastEnd):
    data, errors = convertFileContent(inputfile, binary, keepPastEnd)
    version = 0

    while Path((ofile := outname(outputPath, errors, version))).exists():
        existing = open(ofile, "rb").read()
        if data == existing:
            print(f"Identical to file {ofile}")
            return
        else:
            version += 1
    Path(ofile).parent.mkdir(exist_ok=True, parents=True)
    open(ofile, "wb").write(data)


def convertFile(inputfile, outputPath, binary, keepPastEnd):
    data, errors = convertFileContent(inputfile, binary, keepPastEnd)
    open(ofile, "wb").write(data)


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("inputfile")
    parser.add_argument("outputfile")
    parser.add_argument("--binary", action="store_true")
    parser.add_argument("--keepPastEnd", action="store_true")

    args=parser.parse_args()
    inp=Path(args.inputfile)
    if inp.is_file():
        convertFile(args.inputfile, args.outputfile,
                    args.binary, args.keepPastEnd)
    else:
        files=inp.glob("*")
        for f in files:
            convertVersionedFile(f, Path(args.outputfile) /
                                 f.relative_to(inp), args.binary,args.keepPastEnd)
