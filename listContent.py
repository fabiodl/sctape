from bitparse import getSections
from  section import parseBytesSections,KeyCode

import glob, os,sys



def listBitContent(filename):
    d=getSections(filename)
    parseBytesSections(d["sections"],True)
    filenames=[]
    for s in d["sections"]:
        if s["type"]=="bytes":
            c=KeyCode.code[s["keycode"]]
            if c in [KeyCode.BasicHeader,KeyCode.MachineHeader]:                
                filenames.append(s["Filename"])
    return filenames
    

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
