import sys
import numpy as np

def bigEndian(x):
    return np.sum([v*(256**i) for i,v in enumerate(x[::-1])])


def printable(s):
    return "".join([c for c in s if c.isprintable()])



def getParam(index,default):
    if len(sys.argv)>index:
        return sys.argv[index]
    return default
        
def removeExtension(filename):
    return ".".join(filename.split(".")[:-1])

def rhoSweep(func,filename,rho,lperiod):
    if rho=="auto":
        for rho in np.linspace(1,0.1,99):
            try:
                func(filename,rho,rho,lperiod)
                print(f"OK for {rho:0.2f}")
                return
            except Exception as e:
                print(f"Level at {rho:0.2f} failed:"+str(e),end="\r")
        print("")
        raise Exception("No level found")
    else:
        func(filename,rho,rho,lperiod)
