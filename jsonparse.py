import json
import numpy as np
from util import removeExtension

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


def jsonSerialize(d):
    return json.dumps(dictSerialize(d),indent=2)



def hexList(s):
    return [ int(s[i:i+2],16) for i in range(0,len(s),2)]

def writeJson(filename,d):
    outfile=removeExtension(filename)+".json"
    with open(outfile,"w") as f:
        f.write(jsonSerialize(d))

def jsonDeserialize(filename):
    d=json.loads(open(filename).read())
    for s in d["sections"]:
        if s["type"]=="bytes":
            s["bytes"]=hexList(s["bytes"])
    return d
