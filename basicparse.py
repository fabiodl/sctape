from sc3000decoder import  read_bas_as_hex_string,decode_hex_string,   print_decoded,save_decoded_to
from sc3000encoder import encode_script_string
import binascii
from basparse import getBasicSections

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



def readBasic(filename,opts):
    script_string=open(filename).read()
    suppress_error=False
    encoded = encode_script_string(script_string, suppress_error)
    result = ""
    for line in encoded:
        result += line["encoded"]
    resultb = list(binascii.a2b_hex(result))+[0x00,0x00]
    return getBasicSections(resultb,opts)

            
def decode( fname,chunk):
    hex_string = bytes(chunk).hex().upper()
    decoded = decode_hex_string(hex_string, suppress_error=True)
    save_decoded_to(fname, decoded)
