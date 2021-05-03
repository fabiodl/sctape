from section import SectionList


def maybeByte(bs):
    if len(bs)<11:
        return None
    for b in bs[:11]:
        if b not in ["0","1"]:
            return None
    if bs[0]!="0" or bs[9]!="1" or bs[10]!="1":
        return None
    n=0
    for i in range(8):
        if bs[1+i]=="1":
            n+=(1<<i)
    return n


        


def getSections(filename):
    data=open(filename).read()
    sl=SectionList()    
    offset=0
    while offset<len(data):
        n=maybeByte(data[offset:offset+11])
        if n is not None:
            sl.pushByte(offset,n)
            offset+=11
        elif data[offset]=="1":
            sl.pushHeader(offset)
            offset+=1
        elif data[offset]==" ":
            sl.pushLevel(offset,0,1)
            offset+=1
        else:
            raise Exception("Invalid char in bit file",data[offset])
    sl.finalize()
    d={"bitrate":1200,"sections":sl.sections}
    return d
