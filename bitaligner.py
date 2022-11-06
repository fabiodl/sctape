import sys


def isByte(x):
    if len(x) < 11:
        return
    if x[0] == "0" and x[9] == "1" and x[10] == "1":
        n = 0
        for d in range(8):
            c = x[1+d]
            if c == "1":
                n += (1 << d)
            elif c == "0":
                pass
            else:
                return None
        return n


def writeSplit(data, outfname):
    with open(outfname, "w") as of:
        splits = [i for i in range(2, len(data)) if data[i-2:i+1] == "110"]
        # print(splits)
        of.write(data[0:splits[1]])
        ll = splits[1]
        w = 0
        r = 0
        for i, j in zip(splits, splits[1:]):
            l = j-i
            if w >= 11:
                r += 1
                if r == 8:
                    r = 0
                    of.write("\n")
                of.write(" ")

                w = 0
            of.write(data[i:j])
            w += l


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage {argv[0]} inputfile outputfile")
    else:
        with open(sys.argv[1]) as f:
            data = f.read()
            writeSplit(data, sys.argv[2])
