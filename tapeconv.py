import glob
import sys
import jsonparse
import audioparse
import bitparse
import basparse
import wavparse
import tzxparse
import basicparse
from section import parseBytesSections,printSummary,listContent
from  util import removeExtension,rhoSweep
import getopt



def audioToRemasteredBit(filename,levell,levelh,pitch): #levels are referred to max value, lperiod in seconds
    d=audioparse.getSections(filename,levell,levelh,pitch)
    if len([s for s in d["sections"] if s["type"]=="bytes"])<2:
        raise Exception("nothing to parse")

    parseBytesSections(d["sections"],True)
    return d


def audioRead(filename,opts):
    if "level" in opts:
        lev=float(opts["level"])
        d=audioparse.getSections(filename,lev,lev,1)                   
        return d
    else:    
        return rhoSweep(audioToRemasteredBit,filename,"auto",1)


def wavRemaster(filename,d):
    bs=bitparse.toBitRemaster(d)
    filename="R_"+removeExtension(filename)+".wav"
    wavparse.writeWav(filename,bs)


readers={
    "mp3":audioRead,
    "wav":audioRead,
    "bit":bitparse.getSections,
    "json":jsonparse.jsonDeserialize
}

writers={
    "json":jsonparse.writeJson,
    "bit":lambda f,d: bitparse.writeBit(f,d,True),
    "rawbit":lambda f,d: bitparse.writeBit(f,d,False),
    "bas":basparse.writeBas,
    "wav":wavRemaster,
    "list":lambda f,d: print(f,listContent(d)),
    "summary":lambda f,d: None,
    "tzx":tzxparse.writeTzx,
    "basic":basicparse.writeBasic,
    "bin":basparse.writeBin
}


def convert(filename,outputtype,opts):
    #print("specified options",opts)
    if outputtype=="tzx":        
        d=audioparse.getRawSection(filename,0.33,0.33,1)
    else:
        ext=filename.split(".")[-1]
        d=readers[ext](filename,opts)
        parseBytesSections(d["sections"],"ignore_section_errors" not in opts)
        if outputtype!="list":
            printSummary(d,False)
    writers[outputtype](filename,d)


if __name__=="__main__":
    if len(sys.argv)<3:
        print("Usage ",sys.argv[0]," inputfile outputtype")
    else:
        optlist,args=getopt.getopt(sys.argv[1:],"",["level=","ignore_section_errors"])
        for filename in sorted(glob.glob(args[0])):
            try:
                convert(filename,args[1],{k[2:]:v for k,v in optlist})
            except Exception as e:
                print("Impossible to convert",filename,":",e)
                raise
