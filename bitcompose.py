import sys
from bitparse import encodeByte

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage {argv[0]} inputfile outputfile")
    else:
        inname, outname = sys.argv[1:3]
        firstHeader = True
        with open(inname) as f, open(outname, "w") as of:
            for w in f.read().split():
                w = w.strip()
                if len(w)==2:
                    w=encodeByte(int(w,16))
                if w == "H":
                    if firstHeader:
                        firstHeader = False
                    else:
                        of.write(" "*1200)
                    of.write("1"*3600)
                else:
                    of.write(w)
