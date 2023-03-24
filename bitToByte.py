import sys


def toByte(s):
    if len(s)!=11 or s[0]!='0' or s[-2:]!="11":
        print(f"invalid [{s}]")
        return
    n=0
    for i,ch in enumerate(s[1:-2]): 
        if ch=="1":
            n+=1<<i
        elif ch!="0":
            raise Exception("Unknown chunck",s)
    return f"{n:02X}"
    



if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage {argv[0]} inputfile outputfile")
    else:
        with open(sys.argv[1]) as f, open(sys.argv[2],"w") as g:
            for chunk in f.read().split():
                ab=toByte(chunk)
                if ab:
                    g.write(ab)
                else:
                    g.write(chunk)
                g.write(" ")
        
            
