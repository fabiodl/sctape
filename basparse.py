from  section import KeyCode

def writeFile(filename,l):
    with open(filename,"wb") as f:
        f.write(bytes(l))

def writeBas(fname,d): #already parsed    
    codeChunks=[]
    for s in d["sections"]:
        if s["type"]=="bytes" and KeyCode.code[s["keycode"]]==KeyCode.BasicData:
            codeChunks.append(s["Program"])

    if len(codeChunks)==1:        
        writeFile(fname+".bas",codeChunks[0])
    else:
        for idx,c in enumerate(codeChunks):
            writeFile(f"{fname}{idx}.bas",c)

    
