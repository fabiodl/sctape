### Python Version

python 3

### Tapeconv

```bash
python3 tapeconv.py inputFile output
```
or 
```bash
python3 tapeconv.py "*.ext" output
```

## Examples

All wave files  to remastered bit

```bash
python3 tapeconv.py "*.wav" bit
```

All bit files to .bas

```bash
python3 tapeconv.py "*.bit" bas
```

All bit files to remastered wav

```bash
python3 tapeconv.py "*.bit" wav
```

### Floppy
```bash
python3 floppy.py --operation1[=val] --operation2[=val] ... --operationN[=val]
```


## Examples
Extract files to folder **basic**
```bash
python3 floppy.py --open=diskbasic.sf7 --extract=basic
```

Create floppy image form folder **basic**
```bash
python3 floppy.py  --pack=basic --save=basic.sf7
```
