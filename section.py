from util import bigEndian, printable
import numpy as np
import itertools


class KeyCode:
    BasicHeader, MachineHeader = 0x16, 0x26
    BasicData, MachineData = 0x17, 0x27
    name = {
        BasicHeader: "Basic header",
        BasicData: "Basic data",
        MachineHeader: "ML header",
        MachineData: "ML data"
    }
    code = {v: k for k, v in name.items()}


class SectionList:
    def __init__(self):
        self.sections = []
        self.currSection = None

    def pushByte(self, t, val):
        if self.currSection is None or self.currSection["type"] != "bytes":
            self.finalize()
            self.currSection = {"t": t, "type": "bytes", "bytes": []}
        self.currSection["bytes"].append(val)

    def pushHeader(self, t):
        if self.currSection is None or self.currSection["type"] != "header":
            self.finalize()
            self.currSection = {"t": t, "type": "header", "count": 0}
        self.currSection["count"] += 1

    def pushLevel(self, t, val, count):
        if self.currSection is None or self.currSection["type"] != "level" or self.currSection["value"] != val:
            self.finalize()
            self.currSection = {"t": t, "type": "level",
                                "value": val, "length": 0}
        self.currSection["length"] += count

    def finalize(self):
        if self.currSection != None:
            self.sections.append(self.currSection)


def splitChunks(data, chunkLens):
    idx = 0
    chunks = []
    for l in chunkLens:
        chunks.append(data[idx:idx+l])
        idx += l
    return chunks


def parseBytes(si, so):
    d = si["bytes"]
    secType = d[0]
    if secType in KeyCode.name:
        d = d[1:]
        if secType == KeyCode.BasicHeader:
            cl = [16, 2, 1, 2]
            if (len(d) < np.sum(cl)):
                so["fail.short"] = np.sum(cl)
                return False
            filename, programLength, parity, dummyData = splitChunks(d, cl)
            checkSum = np.sum(filename+programLength+parity) & 0xFF
            if checkSum != 0:
                so["fail.checksum"] = checkSum
                print("*checksum fail")
                return False
            else:
                print(f"header checksum ok, prog len {bigEndian(programLength)}")
            so["keycode"] = KeyCode.name[secType]
            so["Filename"] = "".join([chr(c) for c in filename])
            so["ProgramLength"] = bigEndian(programLength)
            so["Parity"] = parity
            so["Dummy"] = dummyData
        if secType == KeyCode.MachineHeader:
            cl = [16, 2, 2, 1, 2]
            if (len(d) < np.sum(cl)):
                so["fail.short"] = np.sum(cl)
                return False
            filename, programLength, startAddr, parity, dummyData = splitChunks(
                d, cl)
            checkSum = np.sum(filename+programLength+startAddr+parity) & 0xFF
            if checkSum != 0:
                print("*checksum fail")
                so["fail.checksum"] = checkSum
                return False
            so["keycode"] = KeyCode.name[secType]
            so["Filename"] = "".join([chr(c) for c in filename])
            so["ProgramLength"] = bigEndian(programLength)
            so["StartAddr"] = f"{bigEndian(startAddr):04x}"
            so["Parity"] = parity
            so["Dummy"] = dummyData
        elif secType == KeyCode.BasicData or secType == KeyCode.MachineData:
            program, parity, dummyData = d[:-3], d[-3:-2], d[-2:]
            if not program or not parity:
                so["fail.notenoughData"] = d
                return False
            checkSum = np.sum(program+parity) & 0xFF
            if checkSum != 0:
                print("*checksum fail")
                so["fail.checksum"] = checkSum
                so["fail.length"] = len(program)
                return False
            else:
                print("checksum ok")
            so["keycode"] = KeyCode.name[secType]
            so["Program"] = program
            so["Patity"] = parity
            so["Dummy"] = dummyData
            so["length"] = len(program)
    else:
        so["fail.keycode"] = hex(secType)
        print("Unknown Keycode", secType)
        return False
    return True


def parseBytesSections(sl, exceptOnError):
    error = False
    for s in sl:
        if s["type"] == "bytes":
            if not parseBytes(s, s):
                error = True

    if error:
        print(s)
        print("Section errors, decoded", len(sl), "sections")
        if len(sl) < 10:
            for sec in sl:
                print("  Section at", sec["t"], sec["type"])
        if exceptOnError:
            raise Exception("Error in parsing Section")


def printSummary(d, withSilence=True):
    for s in d["sections"]:
        if s["type"] == "header":
            c = s["count"]
            print(f"Header count={c}")
        elif s["type"] == "level":
            t = s["length"]/d["bitrate"]
            if t > 1.0/1200 and withSilence:
                print(f"Silence t={t:0.1f}s")
        elif "keycode" in s:
            print(s["keycode"], end=" ")
            c = KeyCode.code[s["keycode"]]
            if c == KeyCode.BasicHeader or c == KeyCode.MachineHeader:
                fname = printable(s["Filename"])
                l = s["ProgramLength"]
                print(f'filename ="{fname}" length={l}')
            else:
                l = s["length"]
                print(f"length={l}")


def listContent(d):
    filenames = []
    for s in d["sections"]:
        if s["type"] == "bytes":
            c = KeyCode.code[s["keycode"]]
            if c in [KeyCode.BasicHeader, KeyCode.MachineHeader]:
                filenames.append(s["Filename"])
    return filenames

# https://stackoverflow.com/questions/1066758/find-length-of-sequences-of-identical-values-in-a-numpy-array-run-length-encodi/32681075


def lre(bits):
    for bit, group in itertools.groupby(bits):
        yield (bit, len(list(group)))


def getStarts(pairs):
    starts = []
    tl = 0
    for (v, l) in pairs:
        starts.append(tl)
        tl += l
    return starts


def checkLengths(l, minv, maxv, ignoreBegin, ignoreEnd):
    if l[0] < minv:
        return False
    if l[0] > maxv and not ignoreBegin:
        return False
    for d in l[1:-1]:
        if d < minv or d > maxv:
            return False
    if l[-1] < minv:
        return False
    if l[-1] > maxv and not ignoreEnd:
        return False
    return True


def isZero(lop, lperiod, ignoreBegin, ignoreEnd):
    if len(lop) < 2:
        return False
    l = [lop[i][1] for i in range(2)]
    ok = checkLengths(l, 3/8*lperiod, 3/4*lperiod, ignoreBegin, ignoreEnd)
    return ok and lop[0][0]*lop[1][0] == -1


def isOne(lop, lperiod, ignoreBegin, ignoreEnd):
    if len(lop) < 4:
        return False
    l = [lop[i][1] for i in range(4)]
    ok = checkLengths(l, 1/8*lperiod, 3/8*lperiod, ignoreBegin, ignoreEnd)
    for i in range(3):
        if lop[i][0]*lop[i+1][0] != -1:
            ok = False
    return ok


def maybeByte(pairs, period, firstByte):
    n = 0
    offset = 0
    if isZero(pairs[offset:offset+2], period, not firstByte, False):
        offset += 2
    else:
        return None
    for i in range(8):
        if isZero(pairs[offset:offset+2], period, False, False):
            offset += 2
        elif isOne(pairs[offset:offset+4], period, False, False):
            offset += 4
            n += (1 << i)
        else:
            return None
    if isOne(pairs[offset:offset+4], period, False, False) and isOne(pairs[offset+4:offset+8], period, False, True):
        offset += 8
    else:
        return None
    return offset, n


def getBitSequence(fname, d):
    if "signal" not in d:
        print("No signal analysis")
        return
    sl = SectionList()
    period = d["bitrate"]*1/1200
    pairs = list(lre(d["signal"]))
    ones = 0
    bits = ""
    for v, l in pairs:
        if v == 1:
            #print(l, period, l < 3.0/16*period)
            if l < 3.0/8*period:
                ones += 1
                if ones == 2:
                    bits += "1"
                    #print("1", end="")
                    ones = 0
            else:
                bits += "0"
                #print("0", end="")
                ones = 0
    with open(fname, "w") as f:
        f.write(bits)


def getSections(d, pitch, removeSpikes=True):
    # print("levels",levell,levelh,"period",period)
    if "signal" not in d:
        print("No signal analysis")
        return
    pairs = list(lre(d["signal"]))
    period = d["bitrate"]*pitch/1200

    starts = getStarts(pairs)
    if removeSpikes:
        #print("before removal",len(pairs))
        idx = [i for i, (v, l) in enumerate(pairs) if l > period/8]
        pairs = [pairs[i] for i in idx]
        starts = [starts[i] for i in idx]
        #print("after removal",len(pairs))

    offset = 0

    t = 0
    sl = SectionList()
    follower = False
    while offset < len(pairs):
        t = starts[offset]
        bi = maybeByte(pairs[offset:offset+4*11], period, offset == 0)
        if bi is not None:
            follower = True
        if follower:
            # print(pairs[offset:offset+4*11],bi)
            if bi is None:
                follower = False
        if bi is not None:
            off, val = bi
            sl.pushByte(t, val)
            offset += off
        elif isOne(pairs[offset:offset+4], period, True, False):
            sl.pushHeader(t)
            offset += 4
        else:
            sl.pushLevel(t, pairs[offset][0], pairs[offset][1])
            offset += 1
    sl.finalize()
    d["sections"] = sl.sections
    return d
