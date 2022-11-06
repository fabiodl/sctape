import sys


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage {argv[0]} inputfile outputfile")
    else:
        inname, outname = sys.argv[1:3]
        firstHeader = True
        with open(inname) as f, open(outname, "w") as of:
            for w in f.read().split():
                w = w.strip()
                if w == "H":
                    if firstHeader:
                        of.write(" "*1200)
                        firstHeader = False
                    of.write("1"*3600)
                else:
                    of.write(w)
