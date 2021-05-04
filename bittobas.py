from bitparse import getSections
from basparse import writeBas
from  util import removeExtension
from section import parseBytesSections

import glob, os,sys



if __name__=="__main__":
    filename=sys.argv[1]
    d=getSections(filename)
    parseBytesSections(d["sections"],True)
    fname=removeExtension(filename)            
    writeBas(fname,d)
