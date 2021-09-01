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




def audioToRemasteredBit(filename,levell,levelh,pitch): #levels are referred to max value, lperiod in seconds
    d=audioparse.getSections(filename,levell,levelh,pitch)
    if len([s for s in d["sections"] if s["type"]=="bytes"])<2:
        raise Exception("nothing to parse")

    parseBytesSections(d["sections"],True)
    return d


def audioRead(filename):
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
}


def convert(filename,outputtype):
    if outputtype=="tzx":        
        d=audioparse.getRawSection(filename,0.33,0.33,1)
    else:
        ext=filename.split(".")[-1]
        d=readers[ext](filename)
        parseBytesSections(d["sections"],False)
        if outputtype!="list":
            printSummary(d,False)
    writers[outputtype](filename,d)


if __name__=="__main__":
    if len(sys.argv)<3:
        print("Usage ",sys.argv[0]," inputfile outputtype")
    else:
        for filename in sorted(glob.glob(sys.argv[1])):
            try:
                convert(filename,sys.argv[2])
            except Exception as e:
                print("Impossible to convert",filename,":",e)
                raise
