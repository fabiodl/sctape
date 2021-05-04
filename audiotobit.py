import sys
import numpy as np
from audioparse import getSections
from section import parseBytesSections,KeyCode
from  util import removeExtension,getParam,rhoSweep



def encodeByte(b):
    return "0"+ "".join(["1" if ((b>>i)&0x01)==1 else "0" for i in range(8)])+"11"

def encodeBytes(x):
    return "".join([encodeByte(b) for b in x])


def toBitRaw(d):
    data=""
    bitrate=d["bitrate"]
    for s in d["sections"]:
        stype=s["type"]
        if stype=="level":
            data+=" "*int(np.round(s["length"]/bitrate*1200))
        elif stype=="header":
            data+="1"*s["count"]
        elif stype=="bytes":
            data+=encodeBytes(s["bytes"])                
        
    return data


def toBitRemaster(d,fastStart=True):
    data=""
    for s in d["sections"]:
        stype=s["type"]
        if stype=="bytes":
            code=KeyCode.code[s["keycode"]]
            if fastStart:
                n=0
            elif code==KeyCode.BasicHeader or code==KeyCode.MachineHeader:
                n=10*1200
            elif code==KeyCode.BasicData or code==KeyCode.MachineData:
                n=1*1200
            data+=" "*n+"1"*3600+encodeBytes(s["bytes"])
            fastStart=False
    return data



def audioToRawBit(filename,levell,levelh,lperiod):
    d=getSections(filename,levell,levelh,lperiod)
    outfile=removeExtension(filename)+".bit"
    with open(outfile,"w") as f:
        f.write(toBitRaw(d))

def audioToRemasteredBit(filename,levell,levelh,lperiod): #levels are referred to max value, lperiod in seconds
    d=getSections(filename,levell,levelh,lperiod)
    parseBytesSections(d["sections"],True)
    outfile=removeExtension(filename)+".bit"
    with open(outfile,"w") as f:
        f.write(toBitRemaster(d))

                       
if __name__=="__main__":
    if len(sys.argv)<2:
        print("Usage ",sys.argv[0]," filename [threshold] [remaster/raw]")
    else:
        filename=sys.argv[1]        
        rho=getParam(2,0.25)
        if rho!="auto":
            rho=float(rho)
        mode=getParam(3,"remaster")
        lperiod=1/1200
        if mode=="remaster":
            rhoSweep(audioToRemasteredBit,filename,rho,lperiod)
        elif mode=="raw":            
            audioToRawBit(filename,rho,rho,lperiod)
        else:
            print("Unknown mode",mode)
