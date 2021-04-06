import sys
import os
import pathlib

SECTORSIZE=256
SECTORSPERCLUSTER=4
DIRTRACK=20
DIRSECTOR=0
FATTRACK=20
FATSECTOR=12
class Floppy:
    def __init__(self, filename):
        self.data=open(filename,"rb").read()
        self.listdir()

        
    def get(self,track,sector,length=SECTORSIZE):
        start=(track*16+sector)*SECTORSIZE
        return self.data[start:start+length]
    
    def listdir(self):
        self.files={}
        dd=self.get(DIRTRACK,DIRSECTOR,12*SECTORSIZE)
        for f in range(int(len(dd)/16)):
            i=f*16
            fd=dd[i:i+16]
            if fd[0]!=0x00:
                self.files[fd[:12].decode("utf-8")]=[int(x) for x in fd[12:14]]


    def getDiskIPL(self):
        return self.get(0,0)

    def getDiskName(self):
        return self.get(0,0,0x20)

    def getCluster(self,cluster,sectors):
        start=cluster*SECTORSPERCLUSTER*SECTORSIZE
        return self.data[start:start+sectors*SECTORSIZE]

                
    def getChain(self,start):
        f=self.get(FATTRACK,FATSECTOR,160)
        l=[start]
        while f[start]<160:
            start=f[start]
            l.append(start)
        return l,f[start]&0x0F


    def getFreeClusters(self):
        f=self.get(FATTRACK,FATSECTOR,160)
        return [i for i,v in enumerate(f) if v==0xFF]
            
        
    def getFile(self,name):
        start,_=self.files[name]
        chain,lastUsage=self.getChain(start)
        fdata=bytearray()
        for c in chain[:-1]:
            fdata+=self.getCluster(c,4)
        fdata+=self.getCluster(chain[-1],lastUsage)
        return fdata
        
        


def extract(f,dirname):
    pathlib.Path(sys.argv[3]).mkdir(parents=True, exist_ok=True)
    for fname in f.files:
        with open(os.path.join(dirname,fname),"wb") as of:
            of.write(f.getFile(fname))

    
        
        

if __name__=="__main__":
    if len(sys.argv)<2:
        print("Usage",sys.argv[0],"filename [extract directory]")
    else:
        f=Floppy(sys.argv[1])
        print(f.getDiskName())
        print("Free ",len(f.getFreeClusters()),"K")
        for fname,sc in f.files.items():
            print(fname,len(f.getFile(fname)),"bytes")
        if len(sys.argv)>3:
            if sys.argv[2]=="extract":
               extract(f,sys.argv[3])
                                  
                
