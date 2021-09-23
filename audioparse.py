import pydub 
import numpy as np

import json
from scipy import signal

from section import SectionList
from numba import njit

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



def getAbsolute(data,levell,levelh):
    return np.where(data>levelh,1,np.where(data<levell,-1,0))   



hs=44100 # resample sample rate

@njit
def binarize(res,pth,nth,delta):
    s=np.zeros_like(res)
    v=0
    #alpha s.t. for 10 period far it's 0.1
    alpha=  0.1**(1 /(hs/1200*10)) 
    thalpha= 0.1**(1/hs/1200*3)
    m=0
    hth,lth=pth,nth #dynamic thresholds

    

    for t in range(delta,len(res)-delta):
        #print("lth,hth",lth,hth)
        m=alpha*m+(1-alpha)*res[t]
        if res[t]>pth:
            hth=thalpha*hth+(1-thalpha)*res[t]
        if res[t]<nth:
            lth=thalpha*lth+(1-thalpha)*res[t]
        
        if  res[t-delta]<lth  and res[t+delta]>hth and res[t-1]<m and res[t]>m:
            v=1
        elif res[t-delta]>hth  and res[t+delta]<lth and res[t-1]>m and res[t]<m:
            v=-1
        s[t]=v
    return s
    
@njit
def diffBinarize(dr,levell,levelh):
    t=0
    startt=0
    sign=1 if dr[0]>0 else -1

    concdr=np.zeros_like(dr)
    for t in range(len(dr)):
        s=1 if dr[t]>0 else -1
        if s!=sign:
            #med=int(np.round((startt+t-1)/2))
            tot=np.sum(dr[startt:t])
            med=np.argmin(np.abs(np.cumsum(dr[startt:t])-tot/2))            
            concdr[startt+med]=tot
            startt=t
            sign=s

    s=np.zeros_like(dr)
    v=-1        
    hth=levelh*np.max(concdr)
    lth=levell*np.min(concdr)
    for t in range(len(dr)):

        if concdr[t]>hth:
            v=1
        elif concdr[t]<lth:
            v=-1
        s[t]=v
    return s


class Cache:
    def __init__(self):
        self.name=None
        self.data=None
        
    def set(self,filename):
        if self.name!=filename:
            self.data=None
            self.name=filename
            
cache=Cache()            

def getResampled(y,levell,levelh,fr):
    if cache.data is None:
        print("resampling")
        res=signal.resample(y,int(np.ceil(len(y)*hs/fr)))
        dr=np.diff(res)
        cache.data=dr
    dr=cache.data

    #print("levels",levell,levelh)    
    #pth=levelh*np.max(res)
    #nth=levell*np.min(res)
    #delta=int(round(hs/4800/3))
    #return binarize(res,pth,nth,delta)

    return diffBinarize(dr,levell,levelh)
    


def getRawSection(filename,rhol,rhoh,opts):
    bitrate,data=readAudio(filename)
    cache.set(filename)
    mode="diff"
    if "mode" in opts:
        mode=opts["mode"]
    if "pitch" in opts:
        pitch=float(opts["pitch"])
    else:
        pitch=1

    if mode=="absolute":
        pitch=1                
        period=bitrate*pitch/1200
        levell=np.min(data)*rhol
        levelh=np.max(data)*rhoh
        #print("levels",levell,levelh,"period",period)
        d={"bitrate":bitrate,
           "signal":getAbsolute(data,levell,levelh)
        }
    elif mode=="diff":
        d={
            "bitrate":44100,
            "signal":getResampled(data,rhol,rhoh,bitrate)
        }
    else:
        raise Exception("Unkown mode",mode+" known modes are "+" ".join(["absolute","diff"]))

    d["info"]={
        "tool":{
            "settings":{
                "mode":mode,
                "level":[rhol,rhoh]
            }
        }
    }
    
    return d
    



