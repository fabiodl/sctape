#!/usr/bin/env python3

import sys
import glob
import os
import pathlib

src=glob.glob(sys.argv[1])
dstExt=sys.argv[2]


for fname in sorted(src):
    print("==="+fname)
    cmd=" ".join(sys.argv[3:])
    cmd+=" '"+fname+"' '"+str(pathlib.Path(fname).with_suffix("."+dstExt))+"'"
    #print("###"+cmd)
    os.system(cmd  )
