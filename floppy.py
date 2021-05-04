import sys
import os
import pathlib

TRACKS=40
SECTORSIZE=256
SECTORSPERCLUSTER=4
SECTORSPERTRACK=16
CLUSTERSPERTRACK=4


DIRTRACK=20
DIRSECTOR=0
DIRENTRYLEN=16
FATTRACK=20
FATSECTOR=12
class Floppy:
    def __init__(self, filename):
        self.data=bytearray(open(filename,"rb").read())
        self.listdir()

        
    def get(self,track,sector,length=SECTORSIZE):
        start=(track*SECTORSPERTRACK+sector)*SECTORSIZE
        return self.data[start:start+length]


    def save(self,filename):
        with open(filename,"wb") as f:
            f.write(self.data)
    
    def listdir(self):
        self.files={}
        dd=self.get(DIRTRACK,DIRSECTOR,12*SECTORSIZE)
        for f in range(int(len(dd)/DIRENTRYLEN)):
            i=f*16
            fd=dd[i:i+16]
            if fd[0]!=0x00:
                self.files[fd[:12].decode("utf-8")]=[int(x) for x in fd[12:14]]
            #print(fd)

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

    def getDiskUsage(self):
        f=self.get(FATTRACK,FATSECTOR,160)
        free=[i for i,v in enumerate(f) if v==0xFF]
        system=[i for i,v in enumerate(f) if v==0xFE]
        used=[i for i,v in enumerate(f) if v!=0xFE and v!=0xFF]
        fat=list(range(FATTRACK*CLUSTERSPERTRACK,(FATTRACK+1)*CLUSTERSPERTRACK))
        for i in fat:
            if f[i]!=0xFE:
                print("Fat track not marked as 0xFE")
        system=list(set(system)-set(fat))
                        
        return {"system":system,"fat":fat,"used":used,"free":free}

    

    def getSystem(self):
        fat=self.get(FATTRACK,FATSECTOR,160)
        reservedChunks=[[],]

        for i in range(int(DIRTRACK*SECTORSPERTRACK/SECTORSPERCLUSTER)):
            if fat[i]==0xFE:
                l=reservedChunks[-1]
                if len(l)>0 and l[-1]!=i-1:
                    reservedChunks.append([])
                reservedChunks[-1].append(i)

                
        data=[]
        print(f"Found {len(reservedChunks)} IPL chunks")
        for chunk in reservedChunks:
            print("Chunk size",(chunk[-1]-chunk[0]+1),"K")
            data.append(self.getCluster(chunk[0],chunk[-1]-chunk[0]+1))

        return data
        
            
        
    def getFile(self,name):
        start,_=self.files[name]
        chain,lastUsage=self.getChain(start)
        fdata=bytearray()
        for c in chain[:-1]:
            fdata+=self.getCluster(c,4)
        fdata+=self.getCluster(chain[-1],lastUsage)
        return fdata


    def delSector(self,c):
        fs=(FATTRACK*SECTORSPERTRACK+FATSECTOR)*SECTORSIZE
        self.data[fs+c]=0xFF
        secstart=c*SECTORSPERCLUSTER*SECTORSIZE
        secend=(c+1)*SECTORSPERCLUSTER*SECTORSIZE
        self.data[secstart:secend]=bytes([0xFF]*SECTORSPERCLUSTER*SECTORSIZE)   
    
    
    def delete(self,name):
        start,_=self.files[name]
        chain,lastUsage=self.getChain(start)        
        for c in chain:
            self.delSector(c)
        dd=self.get(DIRTRACK,DIRSECTOR,12*SECTORSIZE)
        for f in range(int(len(dd)/DIRENTRYLEN)):
            fd=dd[f*DIRENTRYLEN:(f+1)*DIRENTRYLEN]
            es=(DIRTRACK*SECTORSPERTRACK+DIRSECTOR)*SECTORSIZE+f*DIRENTRYLEN
            #print("fd",fd,"entry",self.data[es:es+DIRENTRYLEN])
            if fd[:12].decode("utf-8")==name:               
                print("Deleting entry",self.data[es:es+DIRENTRYLEN])
                self.data[es:es+DIRENTRYLEN]=bytes([0x00]*DIRENTRYLEN)

    def add(self,name,filename):
        d=open(filename,"rb").read()
        entry=bytearray([0x00]*DIRENTRYLEN)

        
        if "." in name:
            tok=name.split(".")
            n=".".join(tok[:-1])
            e=tok[-1]
            name=n[:8].ljust(8)+"."+e


        nl=min(len(name),12)
        entry[:nl]=bytes(name[:nl].encode("utf-8"))

        chain=[]
        fs=(FATTRACK*SECTORSPERTRACK+FATSECTOR)*SECTORSIZE
        n=int(len(d)/(SECTORSPERCLUSTER*SECTORSIZE) )
        if n*SECTORSPERCLUSTER*SECTORSIZE <len(d):
            n+=1
        lastUsage=0xC4-int((n*SECTORSPERCLUSTER*SECTORSIZE-len(d))/SECTORSIZE  );
        c=0
        while len(chain)<n and c<160:            
            if self.data[fs+c]==0xFF:
                chain.append(c)
            c+=1
        if len(chain)<n:
            raise Exception("Not enough space to store",filename)

        fp=0
        SECSIZE=SECTORSPERCLUSTER*SECTORSIZE
        print("chain",[hex(c) for c in chain],"lu",lastUsage)
        for c,n in zip(chain,chain[1:]+[lastUsage]):
            self.data[fs+c]=n
            secstart=c*SECSIZE
            chunk=d[fp:fp+SECSIZE]
            self.data[secstart:secstart+len(chunk)]=chunk
            fp+=SECSIZE

        entry[12]=chain[0]

        ds=(DIRTRACK*SECTORSPERTRACK+DIRSECTOR)*SECTORSIZE
        entryRec=False
        for f in range(int(12*SECTORSIZE/DIRENTRYLEN)):
            es=ds+f*DIRENTRYLEN
            if self.data[es]==0x00:
                self.data[es:es+DIRENTRYLEN]=entry
                entryRec=True
                break
        if not entryRec:
            raise Exception("No more directory entries available for",filename)

    def deleteUserfiles(self):
        f=self.get(FATTRACK,FATSECTOR,160)
        for idx,val in enumerate(f):
            if val!=0xFE:
                self.delSector(idx)
        ds=(DIRTRACK*SECTORSPERTRACK+DIRSECTOR)*SECTORSIZE
        self.data[ds:ds+12*SECTORSIZE]=bytes([0x00]*12*SECTORSIZE)


                                         
                          
    def printFat(self):
        fat=self.get(FATTRACK,FATSECTOR,160)
        chains=[-1]*160

        for idx,fname in enumerate(self.files):
            start,_=self.files[fname]
            chain,lastUsage=self.getChain(start)
            for c in chain:
                chains[c]=idx+1

        def clusterState(t,c):            
            idx=t*CLUSTERSPERTRACK+c
            s=f"[{idx:02x}]{fat[idx]:02x}"
            if chains[t*CLUSTERSPERTRACK+c]>=0:                
                s+=f"({chains[idx]:02d})"
            else:
               s+=" "*4
            return s

                
        for t in range(TRACKS):        
            status=" ".join([f"{clusterState(t,c)}" for c in range(CLUSTERSPERTRACK)])
            print(f"{t:2d}",status)

        


def extract(f,dirname):
    pathlib.Path(sys.argv[3]).mkdir(parents=True, exist_ok=True)
    for fname in f.files:
        with open(os.path.join(dirname,fname),"wb") as of:
            of.write(f.getFile(fname))

    for idx,d in enumerate(f.getSystem()):        
        with open(os.path.join(dirname,f"IPL{idx}"),"wb") as of:
            of.write(d)
    
        
        

if __name__=="__main__":
    if len(sys.argv)<2:
        print("Usage",sys.argv[0],"filename [extract directory]")
    else:
        f=Floppy(sys.argv[1])        
        print(f.getDiskName())
        summary=" ".join([f"{n}={len(c)}K" for n,c in f.getDiskUsage().items()])
        print(summary)
        for idx,(fname,sc) in enumerate(f.files.items()):
            print(f"{idx+1:2})",fname,len(f.getFile(fname)),"bytes")
        if len(sys.argv)>2:
            cmd=sys.argv[2]
            if cmd=="extract":
                if len(sys.argv)>2:
                    extract(f,sys.argv[3])
                else:
                    print("Specify destination folder")
            elif cmd=="fat":
                f.printFat()
            
                
