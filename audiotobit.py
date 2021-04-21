import pydub 
import numpy as np
import itertools
import sys

Bit0=(0,None)
Bit1=(1,None)
Space=(0,0)

BitVal={Bit0:0,Bit1:1}
BitString={Bit0:"0",Bit1:"1"}
class KeyCode:
    BasicHeader,MachineHeader=0x16,0x26
    BasicData,MachineData=0x17,0x27
    name={
        BasicHeader:"Basic header",
        BasicData:"Basic data",
        MachineHeader:"ML header",
        MachineData:"ML data"
    }



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


def isZero(lop,lperiod):
    if len(lop)<2:
        return False

    ok=True
    for i in range(2):
        if not (lperiod*3/8<lop[i][1]<lperiod*3/2 ):
            ok=False        
   

    return lop[0][0]*lop[1][0]==-1 and ok

def isOne(lop,lperiod):
    if len(lop)<4:
        return False
    ok=True
    for i in range(4):
        if not (lperiod/8<lop[i][1]<lperiod*3/8 ):
            ok=False        
    for i in range(3):
        if lop[i][0]*lop[i+1][0]!=-1:
            ok=False
    return ok
      
def decodeBits(data,levell,levelh,lperiodAbs,bitrate):
    lperiod=lperiodAbs*bitrate
    pairs=list(lre(getHisteresis(data,levell,levelh)))
    lop=[]
    starts=[]
    tl=0
    for (v,l) in pairs:        
        if l>lperiod/8:
            lop.append((v,l))
            starts.append(tl)
        tl+=l
        
    i=0
    bits=[]
    while i<len(lop):
        if isZero(lop[i:i+2],lperiod):
            bits.append(Bit0)
            #print(f"0[{starts[i]}]",end="")
            i+=2

        elif isOne(lop[i:i+4],lperiod):
            bits.append(Bit1)
            #print("1",end="")
            i+=4
        else:
            badt=starts[i]/bitrate
            print("unknown bitstream at idx=",starts[i],"t=",badt,lop[i])
            bits.append(lop[i])
            i+=1

    return bits

def getByte(bits):
    if len(bits)<11:
        return None
    #print(bits[:11])
    for b in bits:
        if b not in BitVal:
            return None
    if bits[0]!=Bit0 or bits[9]!=Bit1 or bits[10]!=Bit1:
        return None
    v=0
    for i,b in enumerate(bits[1:9]):
        v+=BitVal[b]* (2**i)
    return v
        

def getNBytes(bits,n):
    return [getByte(bits[i*11:(i+1)*11]) for i in range(n)]

class BitStream:
    def __init__(self,bits):
        self.bits=bits
        self.ptr=0

        
    def read(self,n):        
        d=getNBytes(self.bits[self.ptr:],n)
        #if None in d:
        #    for i in range(n):
        #        print(self.bits[self.ptr+i*11:self.ptr+(i+1)*11])
        self.ptr+=11*n
        return d        

    def findStart(self):
        ones=0
        while self.ptr<len(self.bits) and self.bits[self.ptr]!=Bit0:
            if self.bits[self.ptr]==Bit1:
                ones+=1
            self.ptr+=1
        return ones


    def hasData(self):
        return self.ptr<len(self.bits)
        
        
def bigEndian(x):
    return np.sum([v*(256**i) for i,v in enumerate(x[::-1])])

def findSections(bs,verbose=True):
    sections=[]
    while bs.hasData():
        
        ones=bs.findStart()
        if ones==0:
            if bs.hasData():
                bs.read(1)
            continue
        if verbose:
            print("Leader length",ones)
        if ones<180:
            break
        keyCode=bs.read(1)[0]
        if verbose:
            print(f"keyCode {keyCode:02x}")
            print("type",KeyCode.name[keyCode])
        chunk=None
        checkSum=None
        if keyCode==KeyCode.BasicHeader:
            chunk=[bs.read(l) for l in [16,2,1,2]]
            filename,programLength,parity,dummyData=chunk
            checkSum=np.sum(filename+programLength+parity)&0xFF
            if verbose:
                print("Filename",[chr(c) for c in filename])            
                print("ProgramLength",bigEndian(programLength))
                print("checksum",checkSum)
                print("dummy",dummyData)
        elif keyCode==KeyCode.MachineHeader:
            chunk=[bs.read(l) for l in [16,2,2,1,2]]
            filename,programLength,startAddr,parity,dummyData=chunk
            checkSum=np.sum(filename+programLength+startAddr+parity)&0xFF
            if verbose:
                print("Filename",[chr(c) for c in filename])            
                print("ProgramLength",bigEndian(programLength))
                print("Start addr",bigEndian(startAddr))
                print("checksum",checkSum)
                print("dummy",dummyData)
        elif keyCode==KeyCode.BasicData or keyCode==KeyCode.MachineData:
            chunk=[bs.read(l) for l in [bigEndian(programLength),1,2]] 
            program,parity,dummyData=chunk
            checkSum=np.sum(program+parity)&0xFF
            if verbose:
                print("checksum",checkSum)
                print("dummy",dummyData)
        sections.append((keyCode,chunk,checkSum))
    return sections


def decodeSections(data,levell,levelh,lperiod,bitrate):
    bs=BitStream(decodeBits(data,levell,levelh,lperiod,bitrate))
    return findSections(bs)


def encodeByte(b):
    return "0"+ "".join(["1" if ((b>>i)&0x01)==1 else "0" for i in range(8)])+"11"



def encodeSections(sections,fastStart=True):
    data=""
    for keyCode,chunk,_ in sections:
        if fastStart:
            n=0
        elif keyCode==KeyCode.BasicHeader or keyCode==KeyCode.MachineHeader:
            n=10*1200
        elif keyCode==KeyCode.BasicData or keyCode==Keycode.MachineData:
            n=1*1200
        else:
            raise Exception("Unknown section keycode",keyCode)
        if fastStart:
            fastStart=False
        data+=" "*n+"1"*3600+"".join([encodeByte(b) for bs in [[keyCode]]+chunk for b in bs])
    return data
        

def checkKeycodePair(k,keyCodes,found,shouldhave):
    if k==found and shouldhave not in keyCodes:
        raise Exception(KeyCode.name[found]+" without "+keyCode.name[shouldhave])

def checkSections(sections):
    if len(sections)<2:
        raise Exception("Empty file")
    for _,_,csum in sections:
        if csum!=0x00:
            raise Exception("Bad checksum")
    keyCodes=[keyCode for keyCode,_,_ in sections]
    for k in keyCodes:
        for f,s in [(KeyCode.BasicHeader,KeyCode.BasicData),(KeyCode.MachineHeader,KeyCode.MachineData)]:        
            checkKeycodePair(k,keyCodes,f,s)
            checkKeycodePair(k,keyCodes,s,f)



def audioToRemasteredBit(filename,levell,levelh,lperiod): #levels are referred to max value, lperiod in seconds
    bitrate,data=readAudio(filename)    
    print("levels ",min(data),max(data))
    sections=decodeSections(data,np.min(data)*levell,np.max(data)*levelh,lperiod,bitrate)
    checkSections(sections)
    encoded=encodeSections(sections)
    outfile=".".join(filename.split(".")[:-1])+".bit"
    with open(outfile,"w") as f:
        f.write(encoded)



def audioToRemasteredBitAuto(filename):
    bitrate,data=readAudio(filename)
    lperiod=1.0/1200
    for rho in np.linspace(1,0,100):
        try:
            sections=decodeSections(data,np.min(data)*rho,np.max(data)*rho,lperiod,bitrate)
            checkSections(sections)
            encoded=encodeSections(sections)
            outfile=".".join(filename.split(".")[:-1])+".bit"
            with open(outfile,"w") as f:
                f.write(encoded)
            print(f"OK for {rho:0.2f}")
            return
        except:
            print(f"Level at {rho:0.2f} failed",end="\r")
    print("")



def audioToRawBit(filename,levell,levelh,lperiod): #levels are referred to max value, lperiod in seconds
    bitrate,data=readAudio(filename)    
    print("levels ",min(data),max(data))
    bits=decodeBits(data,min(data)*levell,max(data)*levelh,lperiod,bitrate)
    
    outfile=".".join(filename.split(".")[:-1])+".bit"
    with open(outfile,"w") as f:
        for b in bits:
            if b in BitString:                
                f.write(BitString[b])
            else:
                for i in range(int(np.round(b[1]/bitrate*1200))):
                    f.write(" ")



    
def getParam(index,default):
    if len(sys.argv)>index:
        return sys.argv[index]
    return default
        
    
if __name__=="__main__":
    if len(sys.argv)<2:
        print("Usage ",sys.argv[0]," filename [threshold] [remaster/raw] [pitch]")
    else:
        filename=sys.argv[1]        
        rho=getParam(2,0.25)
        if rho!="auto":
            rho=float(rho)
        mode=getParam(3,"remaster")
        pitch=float(getParam(4,1))            
        lperiod=pitch/1200
        if mode=="remaster":
            if rho=="auto":
                audioToRemasteredBitAuto(filename)                            
            else:
                audioToRemasteredBit(filename,rho,rho,lperiod)
        else:            
            audioToRawBit(filename,rho,rho,lperiod)
            
