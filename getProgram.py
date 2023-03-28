import sys



def extractBas(bin):
    a=0x9800
    while (size:=bin[a])!=0:
        ret=a+4+size+1
        if bin[ret]!=0x0D:
            raise Exception("Line end not found")
        a=ret+1
    #print(f"final addr {a:04x}")
    return bin[0x9800:a+1]



with open(sys.argv[1],"rb") as f,open(sys.argv[2],"wb") as out:
    out.write(extractBas(f.read()))




#0x9800
