#! /usr/bin/env python3
import argparse
import sc3000decoder as sc

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("inputfile")
    parser.add_argument("outputfile")

    args = parser.parse_args()

    with open(args.inputfile) as f, open(args.outputfile, "w") as of:
        toks = f.read().split()
        idx_list = [idx + 1 for idx, val in
                    enumerate(toks) if val == "0D"]

        res = [toks[i: j] for i, j in
               zip([0] + idx_list, idx_list +
                   ([len(toks)] if idx_list[-1] != len(toks) else []))]

        head = []
        for line in res:
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
            of.write("\r")
            try:
                joined = "".join(line)
                di, lineNo, res = sc.decode_one_line(
                    joined, suppress_error=False)
                if len(joined) != di:
                    of.write(f"len mismatch {di} {len(joined)}\n")
                of.write(f"{lineNo} {res}")
            except Exception as e:
                print(line, str(e))
                of.write("!!!"+str(e))
