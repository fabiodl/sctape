from pathlib import Path
import json


class BasicAliasTable:

    def __init__(self):
        self.table = {}
        self.revtable = {}
        self.decoding = None
        self.deckeys = []

    def load(self, fname, decoding):
        self.decoding = decoding
        print("Using ", fname, self.decoding)
        if fname == "export":
            fname = Path(__file__).parent/"exportBasicAlias.json"
        elif fname == "japanese":
            fname = Path(__file__).parent/"japaneseBasicAlias.json"
        if Path(fname).is_file():
            # print("loaded", fname)
            with open(fname, "r", encoding="utf-8") as f:
                self.table = json.load(f)
                self.revtable = {ve: k for k, vl in self.table.items()
                                 for vk, ve in vl.items()}
                self.deckeys = sorted(
                    self.revtable.keys(), key=len, reverse=True)
            # print("revtable", self.revtable)

    def decode(self, ch):
        h = f"{ch:02X}"
        if h in self.table and self.decoding in self.table[h]:
            dec = self.table[h][self.decoding]
            return dec

        return f"\\x{ch:02X}"

    def encode(self, command):
        for k in self.deckeys:
            kl = len(k)
            if command[:kl] == k:
                return self.revtable[k], k, kl

        if command[0] == "\\" and command[1] == "x":
            return command[2]+command[3], command[0:4], 4

        return f"{ord(command[0]):02x}", command[0], 1


basic_alias_table = BasicAliasTable()
