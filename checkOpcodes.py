import command_table


def encode(ln, prog):
    return bytes([len(prog),
                  (ln & 0xFF), (ln >> 8),
                  0, 0]+prog+[0x0D])


kcmd = command_table.COMMAND.keys()
kfnc = command_table.FUNCTION.keys()
allc = set([f"{i:02X}" for i in range(0x80, 0x100)])
ucmd = allc.difference(kcmd)
ufnc = allc.difference(kfnc)


for i in range(0xD0, 0x100, 0x10):
    print(f"{i>>4:x}")
    with open(f"/tmp/content/cmd{i>>4:x}.bas", "wb") as f:
        for j in range(16):
            x = i+j
            f.write(encode(x, [x]))
        f.write(bytes([0x00, 0x00]))

for i in range(0x90, 0x100, 0x10):
    print(f"{i>>4:x}")
    with open(f"/tmp/content/fnc{i>>4:x}.bas", "wb") as f:
        for j in range(16):
            x = i+j
            f.write(encode(x, [0x80, x]))
        f.write(bytes([0x00, 0x00]))
