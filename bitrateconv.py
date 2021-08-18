import numpy as np
import wave, struct
import sys
from audioparse import readAudio


def writeWav(filename,sampleRate,data):
    obj = wave.open(filename,'wb')
    obj.setnchannels(1) # mono
    obj.setsampwidth(2)
    obj.setframerate(sampleRate)
    rd=data.astype(np.int16).tobytes()
    obj.writeframesraw(rd)
    obj.close()


def getIdx(i,N,sfr,dfr):
    return 
    
if __name__=="__main__":
    sfr,d=readAudio(sys.argv[1])
    dfr=int(sys.argv[2])
    sn=len(d)
    dn=int(np.ceil(sn/sfr*dfr))
    print("src",sn,"dst",dn)
    i=np.arange(dn)
    idx=np.clip(np.round(i/dfr*sfr),0,sn-1).astype(int)
    rd=np.where(d[idx]>0,32767,-32767)
    writeWav(sys.argv[3],dfr,rd)


