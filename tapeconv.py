import jsonparse
from section import parseBytesSections
from  util import removeExtension

import basparse
import sys



readers={"json":jsonparse.jsonDeserialize}
writers={"bas":basparse.writeBas}



if __name__=="__main__":
    if len(sys.argv)<2:
        print("Usage ",sys.argv[0]," filename inputfile outputtype")
    filename=sys.argv[1]
    outputtype=sys.argv[2]
    ext=filename.split(".")[-1]
    d=readers[ext](filename)
    parseBytesSections(d["sections"],True)
    fname=removeExtension(filename)            
    writers[outputtype](fname,d)
