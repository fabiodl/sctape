from sc3000decoder import read_bas_as_hex_string, decode_hex_string
from sc3000decoder import print_decoded, save_decoded_to, escape_char
from sc3000encoder import encode_script_string
import binascii
from basparse import getBasicSections

from section import KeyCode
from util import removeExtension
from pathlib import Path


def writeBasic(filename, d, opt):  # already parsed
    fname = removeExtension(filename)
    codeChunks = []
    for s in d["sections"]:
        if s["type"] == "bytes" and KeyCode.code[s["keycode"]] == KeyCode.BasicData:
            codeChunks.append(s["Program"])

    ext = Path(filename).suffix
    if len(codeChunks) == 1:
        decode(fname + ext, codeChunks[0])
    else:
        for idx, c in enumerate(codeChunks):
            decode(f"{fname}{idx}{ext}", c)


def writeFilename(filename, d, opt):
    fname = removeExtension(filename)
    names = []
    for s in d["sections"]:
        if s["type"] == "bytes" and KeyCode.code[s["keycode"]] == KeyCode.BasicHeader:
            names.append(s["Filename"])
    if len(names) == 1:
        open(fname + ".filename", "w").write(names[0])
    else:
        for idx, na in enumerate(names):
            open(f"{fname}{idx}.filename", "w").write(na)


def readBasic(filename, opts):
    if "basic_raw_encoding" in opts:
        raw = open(filename, "rb").read()
        # print("==RAW==", raw)
        script_string = "".join([escape_char(ch, toPass=[0x0A])
                                 for ch in raw if ch not in [0x01, 0x0D]])
    else:
        script_string = open(filename).read()
    suppress_error = False
    encoded = encode_script_string(script_string, suppress_error)
    result = ""
    for line in encoded:
        result += line["encoded"]
    resultb = list(binascii.a2b_hex(result))
    if "\\bin" not in encoded[-1]["raw"]:
        resultb += [0x00, 0x00]
    return getBasicSections(resultb, opts)


def decode(fname, chunk):
    hex_string = bytes(chunk).hex().upper()
    decoded = decode_hex_string(hex_string, suppress_error=True)
    save_decoded_to(fname, decoded)
