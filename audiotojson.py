import sys
import numpy as np
from audioparse import getSections
from section import parseBytesSections,printSummary
from util import getParam,removeExtesion,rhoSweep
import json

def hexString(d):
    return "".join([f"{v:02x}" for v in d])

def elemSerialize(x):
    t=type(x)
    #print("type",t)
    if t in serializers:
        return serializers[t](x)
    return x


def listSerialize(x):
    if type(x[0])==np.int64 or type(x[0])==int:
        return hexString(x)
    else:
        return [elemSerialize(e) for e in x]
    

def dictSerialize(inp):
    out={}
    for k,v in inp.items():
        out[k]=elemSerialize(v)
    return out

    
serializers={
    np.int64:lambda x:int(x),
    list: listSerialize,
    dict: dictSerialize
}


def audioToJson(filename,levell,levelh,lperiod,exceptOnError=True):    
    d=getSections(filename,levell,levelh,lperiod)
    parseBytesSections(d["sections"],exceptOnError)
    printSummary(d)
    outfile=removeExtesion(filename)+".json"
    with open(outfile,"w") as f:
            f.write(json.dumps(dictSerialize(d),indent=2))

if __name__=="__main__":
    if len(sys.argv)<2:
        print("Usage ",sys.argv[0]," filename [threshold/auto]")
    try:
        filename=sys.argv[1]        
        rho=getParam(2,0.25)
        lperiod=1/1200
        rhoSweep(audioToJson,filename,rho,lperiod)
    except:
        audioToJson(filename,rho,rho,lperiod,False)
        
