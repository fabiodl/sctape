from mp3tobit import Bit0,Bit1,Space,BitStream,findSections,KeyCode
import glob, os,sys

conv={"0":Bit0,"1":Bit1," ":Space}


def listBitstreamContent(bs):
    sections=findSections(bs,False)
    filenames=[]
    for keyCode,chunk,_ in sections:
        if keyCode==KeyCode.BasicHeader or keyCode==KeyCode.MachineHeader:
            filenames.append("".join([chr(c) for c in chunk[0]]))
    return filenames



def listBitContent(filename):
    data=open(filename).read()
    bs=BitStream([conv[d] for d in data])
    return listBitstreamContent(bs)



    

if __name__=="__main__":

    if len(sys.argv)>1:
        dirname=sys.argv[1]
    else:
        dirname="."
    if ".bit" in dirname:
        print(dirname,listBitContent(dirname))
    else:    
        for name in sorted(glob.glob(os.path.join(dirname,"*.bit"))):
            print(name,listBitContent(name))
