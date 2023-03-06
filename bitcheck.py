import sys

with open(sys.argv[1]) as f:
    for lno,line in enumerate(f.readlines()):
        tok=line.split()
        for t in tok:
            if t=="H":
                continue
            if len(t)!=11:
                print(f"{lno}:{t} length()={len(t)}")
                continue
            if t[0]!="0":
                print(f"{lno}:{t} no start bit")
                continue
            if t[-2:]!="11":
                print(f"{lno}:{t} no stop bits")
                continue
