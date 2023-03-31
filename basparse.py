from  section import KeyCode
from util import removeExtension,beint
import numpy as np

def writeFile(filename,l):
    with open(filename,"wb") as f:
        f.write(bytes(l))

def writeBas(filename,d): #already parsed    
    codeChunks=[]
    for s in d["sections"]:
        if s["type"]=="bytes" and KeyCode.code[s["keycode"]]==KeyCode.BasicData:
            codeChunks.append(s["Program"])

    if len(codeChunks)==1:        
        writeFile(filename,codeChunks[0])
    else:
        fname=removeExtension(filename)
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

    if "program_type" in opts:
        ptype=opts["program_type"]
        if ptype=="machine":
            isMachine=True
        elif ptype=="basic":
            isMachine=False
        else:
            raise Exception("Unknown code type "+ctype+" options are either 'basic' or 'machine'")
    else:
        isMachine=False


    if isMachine:
        if "program_start_addr" in opts:
            startAddr=int(opts["program_start_addr"],16)
        else:
            print("\nWarning: start address not specified\n")
            startAddr=0xC000
        
        
    if "program_name" not in opts:
        print("\nWarning: program name not specified\n")
    else:
        if isMachine:
            header=[KeyCode.MachineHeader]
        else:
            header=[KeyCode.BasicHeader]
        filename=opts["program_name"].ljust(16)[:16]
        filename=[ord(c) for c in filename]
        programLength=beint(len(program),2)

        headerPayload=filename+programLength
        if isMachine:
            headerPayload+=beint(startAddr,2)        
        p=parity(headerPayload)
        sections.append({
            "t":-1,
            "type":"bytes",
            "bytes": header+headerPayload+[p,0x00,0x00]})
    
    if isMachine:
        header=[KeyCode.MachineData]
    else:
        header=[KeyCode.BasicData]
    p=parity(program)

    sections.append({
        "t":-1,
        "type":"bytes",
        "bytes":header+program+[p,0x00,0x00]})
    return d
    
        
    
def readBas(filename,opts):
    start,end=0,None
    d=open(filename,"rb").read()
    if "program_from" in opts:
        start=int(opts["program_from"],16)
    if "program_to" in opts:
        end=int(opts["program_to"],16)
    if "program_size" in opts:
        end=start+int(opts["program_size"],16)
    if "program_rstrip" in opts:
        endchar=int(opts["program_rstrip"],16)
        d=d.rstrip(bytes([endchar]))
    if end is None:
        end=len(d)
    print(f"Reading {filename} range {start:04x} : {end:04x}")
    program=list(d[start:end])
    return getBasicSections(program,opts)

    
