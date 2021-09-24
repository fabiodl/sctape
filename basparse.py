from  section import KeyCode
from util import removeExtension,beint
import numpy as np

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


def parity(x):
    return 0x100-(0xFF&int(np.sum(x)))
            
def getBasicSections(program,opts):
    d={
        "sections":[]
    }
    sections=d["sections"]
    if "program_name" not in opts:
        print("\nWarning: program name not specified\n")
    else:
        header=[KeyCode.BasicHeader]
        filename=opts["program_name"].ljust(16)[:16]
        filename=[ord(c) for c in filename]
        programLength=beint(len(program),2)
        p=parity(filename+programLength)
        sections.append({
            "t":-1,
            "type":"bytes",
            "bytes": header+filename+programLength+[p,0x00,0x00]})
    
    header=[KeyCode.BasicData]
    p=parity(program)

    sections.append({
        "t":-1,
        "type":"bytes",
        "bytes":header+program+[p,0x00,0x00]})
    return d
    
        
    
def readBas(filename,opts):
    program=list(open(filename,"rb").read())
    return getBasicSections(program,opts)

    
