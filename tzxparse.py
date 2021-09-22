import numpy as np
from itertools import chain
def leint(x,n):
    l=[]
    for i in range(n):
        l.append(x&0xFF)
        x=x>>8
    return l



class Encoder:
    def __init__(self,trate):
        self.data=bytearray()
        self.trate=trate
        self.openChunk()

    def openChunk(self):
        self.chunk=bytearray()
        self.byteval=0
        self.bi=0
        self.trailingPause=False
        self.pauseCount=0
        
    def pushBit(self,b):
        self.byteval|=b<<(7-self.bi)
        self.bi+=1
        if self.bi==8:
            self.bi=0
            self.chunk.append(self.byteval)
            self.byteval=0

    def pushBlock(self):
        if self.trailingPause:
            dt=int(np.round(self.pauseCount*self.trate/3500))
        else:
            dt=0
        ub=self.bi if self.bi!=0 else 8
        self.chunk.append(self.byteval)
        self.data+=bytearray([0x15]+leint(self.trate,2)+leint(dt,2)+[ub]+leint(len(self.chunk),3))
        self.data+=self.chunk
        #print("pushing chunk of len",len(self.chunk),"pause",dt)
        
                    
    def pushLevel(self,lev):
        #print(lev)
        if self.trailingPause:
            if lev==0:
                self.pauseCount+=1
            else:
                if self.pauseCount>2:                  
                    self.pushBlock()
                    self.openChunk()
                else:            
                    self.pushBit(0)
                    if self.pauseCount>1:
                        self.pushBit(1)
                    self.trailingPause=False

        if not self.trailingPause:
            if lev!=0:
                self.pushBit(1 if lev==1 else 0)
            else:
                self.trailingPause=True
                self.pauseCount=1



def getFileHeader():                
    data=bytearray()
    data+="ZXTape!".encode()
    data+=bytearray([0x1A,1,20])
    return data

def encode(trate,d):
    #print("data len",len(d))
    enc=Encoder(trate)
    for lev in d:
        enc.pushLevel(1 if lev==1 else -1)
    enc.pushBlock()
    return enc.data


class BitEncoder:
    def __init__(self):
        self.sampleRate=44100
        val=1
        Space= np.zeros(int(self.sampleRate/1200))
        Zero= np.hstack([v*np.ones(int(self.sampleRate/1200/2)) for v in [val,-val]])
        One=np.hstack([v*np.ones(int(self.sampleRate/1200/4)) for v in [val,-val,val,-val]])
        self.conv={' ':Space,'0':Zero,'1':One}


def writeTzxFromBs(filename,bs):
    be=BitEncoder()
    d=np.hstack([be.conv[s] for s in bs])
    data=getFileHeader()
    trate=int(np.round(3.5E6/be.sampleRate))
    data+=encode(trate,d)
    with open(filename,"wb") as f:
        f.write(data)


def writeTzx(filename,d):
    resample=44100
    trate=int(np.round(3.5E6/resample))
    bitrate=d["bitrate"]
    lsignal=len(d["signal"])
    idx=[int(x) for x in np.clip(np.round(bitrate*np.arange(0,lsignal/bitrate,1/resample)),0,lsignal-1)]
    data=getFileHeader()
    data+=encode(trate,d["signal"][idx])
    with open(filename,"wb") as f:
        f.write(data)


def le(x):
    r=0
    for i,v in enumerate(x):
        r+=(256**i)*v
    return r
        

def getBlocks(fname):
    blocks=[]
    with open(fname,"rb") as f:
        data=f.read()
        ptr=0
        while ptr<len(data):            
            begin=ptr
            bid=data[ptr]        
            ptr+=1
            if bid==0x5A:
                ptr+=9
            elif bid==0x15:
                ptr+=le(data[ptr+5:ptr+8])+8
            else:
                raise Exception("Unknow block "+bid)
            blocks.append(data[begin:ptr])
    return blocks





def tzxByteExpand(b):
    return [1 if b&(1<<i) else -1 for i in range(7,-1,-1)]  


tzxBet=np.array([tzxByteExpand(i) for i in range(256)])

def readTzx(filename,opts=None):
    blocks=getBlocks(filename)
    d=np.zeros(0)
    for bl in blocks:
        if bl[0]==0x15:
            print("found block")
            conv=tzxBet[list(bl[9:])]    
            d=np.hstack([d,conv.reshape(-1)])
    dic={
        "signal":np.array(d),
        "bitrate":44100 #FIX ME
    }
    print("signal shape",np.shape(dic["signal"]))
    return dic
        

def writeTzxNoresample(filename,d):
    filename=removeExtension(filename)+".tzx"
    trate=int(np.round(3500000/d["bitrate"]))
    #print("bitrate", d["bitrate"],"trate",trate)
    data=getFileHeader()
    data+=encode(trate,d["signal"])
    with open(filename,"wb") as f:
        f.write(data)


