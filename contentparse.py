import zlib
from section import KeyCode


class Static:
    fd = None


def printAsIs(ch):
    return 0x20 <= ord(ch) <= 0x7A


def parseName(filename):
    return '"' + "".join([ch if printAsIs(ch) else f"\\x{ord(ch):02X}" for ch in filename]) + '"'


def listContent(filename, d, opts):
    if Static.fd is None:
        Static.fd = open(filename, "w")
    content = []
    for s in d["sections"]:
        if s["type"] == "bytes":
            chunk = s["bytes"]
            k = chunk[0]
            props = {}
            props["Type"] = f"{KeyCode.name.setdefault(k,f'Unknown {k:02x}')}"
            if k in [KeyCode.BasicHeader, KeyCode.MachineHeader]:
                if "Filename" in s:
                    props["Name"] = parseName(s["Filename"])
                if "ProgramLength" in s:
                    props["ProgramLength"] = s["ProgramLength"]
            props["CRC"] = f"{(zlib.crc32(bytes(chunk)) & 0xff_ff_ff_ff):08X}"

            content.append(",".join([f"{k}={v}" for k, v in props.items()]))
    contentStr = "; ".join([d["args"]["infilename"]]+content)+"\n"
    Static.fd.write(contentStr)
    Static.fd.flush()
