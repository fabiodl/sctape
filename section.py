from util import bigEndian,printable
import numpy as np

class KeyCode:
    BasicHeader,MachineHeader=0x16,0x26
    BasicData,MachineData=0x17,0x27
    name={
        BasicHeader:"Basic header",
        BasicData:"Basic data",
        MachineHeader:"ML header",
        MachineData:"ML data"
    }
    code={v:k for k,v in name.items() }


class SectionList:
    def __init__(self):
        self.sections=[]
        self.currSection=None

        
    def pushByte(self,t,val):
        if self.currSection is None or self.currSection["type"]!="bytes":
            self.finalize()
            self.currSection={"t":t,"type":"bytes","bytes":[]}            
        self.currSection["bytes"].append(val)
        
    def pushHeader(self,t):
        if self.currSection is None or self.currSection["type"]!="header":
            self.finalize()
            self.currSection={"t":t,"type":"header","count":0}            
        self.currSection["count"]+=1
        
    def pushLevel(self,t,val,count):
        if self.currSection is None or self.currSection["type"]!="level" or self.currSection["value"]!=val:
            self.finalize()
            self.currSection={"t":t,"type":"level","value":val,"length":0}
        self.currSection["length"]+=count

            
    def finalize(self):
        if self.currSection!=None:
            self.sections.append(self.currSection)
        
            
    
def splitChunks(data,chunkLens):
    idx=0
    chunks=[]
    for l in chunkLens:
        chunks.append(data[idx:idx+l])
        idx+=l
    return chunks

def parseBytes(si,so):
    d=si["bytes"]
    secType=d[0]
    if secType in KeyCode.name:
        d=d[1:]
        if secType==KeyCode.BasicHeader:
            cl=[16,2,1,2]
            if (len(d)<np.sum(cl)):
                so["fail.short"]=np.sum(cl)
                return False
            filename,programLength,parity,dummyData=splitChunks(d, cl)
            checkSum=np.sum(filename+programLength+parity)&0xFF
            if checkSum!=0:
                so["fail.checksum"]=checkSum
                return False
            so["keycode"]=KeyCode.name[secType]            
            so["Filename"]="".join([chr(c) for c in filename])
            so["ProgramLength"]=bigEndian(programLength)
            so["Parity"]=parity
            so["Dummy"]=dummyData
        if secType==KeyCode.MachineHeader:
            cl=[16,2,2,1,2]
            if (len(d)<np.sum(cl)):
                so["fail.short"]=np.sum(cl)
                return False            
            filename,programLength,startAddr,parity,dummyData=splitChunks(d,cl)
            checkSum=np.sum(filename+programLength+startAddr+parity)&0xFF
            if checkSum!=0:
                so["fail.checksum"]=checkSum
                return False
            so["keycode"]=KeyCode.name[secType]            
            so["Filename"]="".join([chr(c) for c in filename])
            so["ProgramLength"]=bigEndian(programLength)
            so["StartAddr"]=f"{bigEndian(startAddr):04x}"
            so["Parity"]=parity
            so["Dummy"]=dummyData
        elif secType==KeyCode.BasicData or secType==KeyCode.MachineData:
            program,parity,dummyData=d[:-3],d[-3:-2],d[-2:]
            checkSum=np.sum(program+parity)&0xFF
            if checkSum!=0:
                so["fail.checksum"]=checkSum
                so["fail.length"]=len(program)
                return False
            so["keycode"]=KeyCode.name[secType]            
            so["Program"]=program
            so["Dummy"]=dummyData
            so["length"]=len(program)
    else:
        so["fail.keycode"]=hex(secType)
        print("Unknown Keycode",secType)
        return False
    return True

def parseBytesSections(sl,exceptOnError):
  for s in sl:
      if s["type"]=="bytes":
          if not parseBytes(s,s) and exceptOnError:
              raise Exception("Error in parsing Section")



def printSummary(d):
    for s in d["sections"]:
        if s["type"]=="header":
            c=s["count"]
            print(f"Header count={c}")
        elif s["type"]=="level":
            t=s["length"]/d["bitrate"]
            if t>1.0/1200:
                print(f"Silence t={t:0.1f}s")            
        elif "keycode" in s:
            print(s["keycode"],end=" ")
            c=KeyCode.code[s["keycode"]]
            if c==KeyCode.BasicHeader or c==KeyCode.MachineHeader:
                fname=printable(s["Filename"])
                l=s["ProgramLength"]
                print(f'filename ="{fname}" length={l}')
            else:
                l=s["length"]
                print(f"length={l}")


