import numpy as np
import wave, struct
import sys

sampleRate = 48000 # hertz
val=32767

Space= np.zeros(int(sampleRate/1200),dtype=np.int16).tobytes()
Zero= np.hstack([v*np.ones(int(sampleRate/1200/2),dtype=np.int16) for v in [val,-val]]).tobytes()
One=np.hstack([v*np.ones(int(sampleRate/1200/4),dtype=np.int16) for v in [val,-val,val,-val]]).tobytes()
conv={' ':Space,'0':Zero,'1':One}

def writeWav(filename,data):
    obj = wave.open(filename,'wb')
    obj.setnchannels(1) # mono
    obj.setsampwidth(2)
    obj.setframerate(sampleRate)
    for d in data:
       obj.writeframesraw( conv[d] )
    obj.close()



def bittowav(filename):
    with open(filename) as f:
        data=f.read()        
        outname=".".join(filename.split(".")[:-1])+".wav"
        writeWav(outname,data)
        print("Wrote",outname)

