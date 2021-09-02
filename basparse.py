from  section import KeyCode
from util import removeExtension

def writeFile(filename,l):
    with open(filename,"wb") as f:
        f.write(bytes(l))

def writeBas(filename,d): #already parsed    
    fname=removeExtension(filename)
    codeChunks=[]
    for s in d["sections"]:
        if s["type"]=="bytes" and KeyCode.code[s["keycode"]]==KeyCode.BasicData:
            codeChunks.append(s["Program"])

    if len(codeChunks)==1:        
        writeFile(fname+".bas",codeChunks[0])
    else:
        for idx,c in enumerate(codeChunks):
            writeFile(f"{fname}{idx}.bas",c)



def writeBin(filename,d): #already parsed    
    fname=removeExtension(filename)
    codeChunks=[]
    idx=0
    for s in d["sections"]:
        if s["type"]=="bytes":
            writeFile(f"{fname}{idx}.bin",s["bytes"])            
            idx+=1


    
