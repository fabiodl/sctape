import pydub 
import numpy as np
import itertools
import json

from section import SectionList


#https://stackoverflow.com/questions/53633177/how-to-read-a-mp3-audio-file-into-a-numpy-array-save-a-numpy-array-to-mp3

def readAudio(f):  
    ext=f.split(".")[-1]
    loader={"mp3":pydub.AudioSegment.from_mp3,
          "wav":pydub.AudioSegment.from_wav}    
    a = loader[ext](f)
    y = np.array(a.get_array_of_samples())
    if a.channels == 2:
        y = np.mean(y.reshape((-1, 2)),axis=1)

    return a.frame_rate, y



def getHisteresis(data,levell,levelh):
    return np.where(data>levelh,1,np.where(data<levell,-1,0))   


#https://stackoverflow.com/questions/1066758/find-length-of-sequences-of-identical-values-in-a-numpy-array-run-length-encodi/32681075
def lre(bits):
  for bit, group in itertools.groupby(bits):
      yield (bit,len(list(group)))


def checkLengths(l,minv,maxv,ignoreBegin,ignoreEnd):
    if l[0]<minv:
        return False
    if l[0]>maxv and not ignoreBegin:
        return False
    for d in l[1:-1]:
        if d<minv or d>maxv:
            return False
    if l[-1]<minv:
        return False
    if l[-1]>maxv and not ignoreEnd:
        return False
    return True

def isZero(lop,lperiod,ignoreBegin,ignoreEnd):
    if len(lop)<2:
        return False
    l=[lop[i][1] for i in range(2)]
    ok=checkLengths(l,3/8*lperiod,3/4*lperiod,ignoreBegin,ignoreEnd)
    return ok and lop[0][0]*lop[1][0]==-1

def isOne(lop,lperiod,ignoreBegin,ignoreEnd):
    if len(lop)<4:
        return False
    l=[lop[i][1] for i in range(4)]
    ok=checkLengths(l,1/8*lperiod,3/8*lperiod,ignoreBegin,ignoreEnd)
    for i in range(3):
        if lop[i][0]*lop[i+1][0]!=-1:
            ok=False
    return ok
      


def maybeByte(pairs,period,firstByte):
    n=0
    offset=0
    if isZero(pairs[offset:offset+2],period,not firstByte,False):            
        offset+=2
    else:
        return None
    for i in range(8):
        if isZero(pairs[offset:offset+2],period,False,False):
            offset+=2
        elif isOne(pairs[offset:offset+4],period,False,False):
            offset+=4
            n+=(1<<i)
        else:
            return None
    if isOne(pairs[offset:offset+4],period,False,False) and isOne(pairs[offset+4:offset+8],period,False,True):
        offset+=8
    else:
        return None
    return offset,n
                

def getStarts(pairs):
    starts=[]
    tl=0
    for (v,l) in pairs:        
        starts.append(tl)
        tl+=l
    return starts


def getSections(filename,levell,levelh,lperiod):
    bitrate,data=readAudio(filename)
    period=bitrate*lperiod
    pairs=list(lre(getHisteresis(data,levell,levelh)))
    starts=getStarts(pairs)
    offset=0

    t=0
    sl=SectionList ()
    follower=False
    while offset<len(pairs):
        t=starts[offset]
        bi=maybeByte(pairs[offset:offset+4*11],period,offset==0)
        if bi is not None:
            follower=True
        if follower:
            #print(pairs[offset:offset+4*11],bi)
            if bi is None:
                follower=False
        if bi is not None:
            off,val=bi
            sl.pushByte(t,val)
            offset+=off
        elif isOne(pairs[offset:offset+4],period,True,False):
            sl.pushHeader(t)
            offset+=4
        else:
            sl.pushLevel(t,pairs[offset][0],pairs[offset][1])
            offset+=1
    sl.finalize()
    d={"bitrate":bitrate,"sections":sl.sections}
    return d




