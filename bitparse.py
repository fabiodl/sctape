import numpy as np
from section import SectionList, KeyCode


def maybeByte(bs):
    if len(bs) < 11:
        return None
    for b in bs[:11]:
        if b not in ["0", "1"]:
            return None
    if bs[0] != "0" or bs[9] != "1" or bs[10] != "1":
        return None
    n = 0
    for i in range(8):
        if bs[1+i] == "1":
            n += (1 << i)
    return n


def readBit(filename, opts):
    return getSections(open(filename).read())


def getSections(data):
    sl = SectionList()
    offset = 0
    while offset < len(data):
        n = maybeByte(data[offset:offset+11])
        if n is not None:
            sl.pushByte(offset, n)
            offset += 11
        elif data[offset] == "1":
            sl.pushHeader(offset)
            offset += 1
        elif data[offset] == " ":
            sl.pushLevel(offset, 0, 1)
            offset += 1
        else:
            raise Exception("Invalid char in bit file",
                            data[offset], "at position", offset)
    sl.finalize()
    d = {"bitrate": 1200, "sections": sl.sections}
    return d


def encodeByte(b):
    return "0" + "".join(["1" if ((b >> i) & 0x01) == 1 else "0" for i in range(8)])+"11"


def encodeBytes(x):
    return "".join([encodeByte(b) for b in x])


def toBitRaw(d):
    data = ""
    bitrate = d["bitrate"]
    for s in d["sections"]:
        stype = s["type"]
        if stype == "level":
            data += " "*int(np.round(s["length"]/bitrate*1200))
        elif stype == "header":
            data += "1"*s["count"]
        elif stype == "bytes":
            data += encodeBytes(s["bytes"])

    return data


def toBitRemaster(d, fastStart=True):
    data = ""
    for s in d["sections"]:
        stype = s["type"]
        # print("section", s)
        if stype == "bytes":
            code = KeyCode.code[s["keycode"]]
            if fastStart:
                n = 0
            elif code == KeyCode.BasicHeader or code == KeyCode.MachineHeader:
                n = 10*1200
            elif code == KeyCode.BasicData or code == KeyCode.MachineData:
                n = 1*1200
            data += " "*n+"1"*3600+encodeBytes(s["bytes"])
            fastStart = False
    return data


def genSignal(d, sampleRate, sectionRemaster):
    val = 1
    Space = np.zeros(int(sampleRate/1200))
    Zero = np.hstack([v*np.ones(int(sampleRate/1200/2)) for v in [val, -val]])
    One = np.hstack([v*np.ones(int(sampleRate/1200/4))
                    for v in [val, -val, val, -val]])
    conv = {' ': Space, '0': Zero, '1': One}

    if sectionRemaster:
        bits = toBitRemaster(d, True)
    else:
        bits = toBitRaw(d)
    sig = np.hstack([conv[b] for b in bits])

    return sig


def writeBit(filename, d, remaster):
    with open(filename, "w") as f:
        if remaster:
            f.write(toBitRemaster(d))
        else:
            f.write(toBitRaw(d))
