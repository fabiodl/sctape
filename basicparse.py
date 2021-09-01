from sc3000decoder import  read_bas_as_hex_string,decode_hex_string,   print_decoded,save_decoded_to

from  section import KeyCode
from util import removeExtension


def writeBasic(filename,d): #already parsed
    fname=removeExtension(filename)
    codeChunks=[]
    for s in d["sections"]:
        if s["type"]=="bytes" and KeyCode.code[s["keycode"]]==KeyCode.BasicData:
            codeChunks.append(s["Program"])

    
    if len(codeChunks)==1:        
        decode(fname+".basic",codeChunks[0])
    else:
        for idx,c in enumerate(codeChunks):
            decode(f"{fname}{idx}.basic",c)


def decode( fname,chunk):
    hex_string = bytes(chunk).hex().upper()
    decoded = decode_hex_string(hex_string, suppress_error=False)
    save_decoded_to(fname, decoded)
