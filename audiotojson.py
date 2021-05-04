import sys
from jsonparse import jsonSerialize
from audioparse import getSections
from section import parseBytesSections,printSummary
from util import getParam,removeExtension,rhoSweep


def audioToJson(filename,levell,levelh,lperiod,exceptOnError=True):    
    d=getSections(filename,levell,levelh,lperiod)
    parseBytesSections(d["sections"],exceptOnError)
    printSummary(d)
    outfile=removeExtension(filename)+".json"
    with open(outfile,"w") as f:
            f.write(jsonSerialize(d))

if __name__=="__main__":
    if len(sys.argv)<2:
        print("Usage ",sys.argv[0]," filename [threshold/auto]")
    try:
        filename=sys.argv[1]        
        rho=getParam(2,0.25)
        lperiod=1/1200
        rhoSweep(audioToJson,filename,rho,lperiod)
    except:
        print("===Giving up with decoding===")
        rho=0.25
        audioToJson(filename,rho,rho,lperiod,False)
        
