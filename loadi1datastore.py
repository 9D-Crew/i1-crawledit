import os
import sys
import json

if len(sys.argv) < 2:
    print("please launch from the main script!")
    sys.exit(1)

dsdict = {}

directory = sys.argv[1]
if not os.path.exists(directory):
    print("directory does not exist!")
    sys.exit(1)

datpath = os.path.join(directory, "ds.dat")
statpath = os.path.join(directory, "ds.stat")
if not os.path.exists(datpath):
    print("missing ds.dat!")

if not os.path.exists(statpath):
    print("missing ds.stat!")

if not (os.path.exists(datpath) and os.path.exists(statpath)):
    sys.exit(1)

def chunk_data(data, size):
    for i in range(0, len(data), size):
        yield data[i:i + size]

for file in [datpath, statpath]:
    with open(file) as f:
        data = f.read()

    filepos = 0
    while True:
        fs = "\x1c"
        nameix = data.find(fs, filepos)
        if nameix == -1:
            break
        name = data[filepos:nameix]
        filepos = nameix + 1
        
        valix = data.find(fs, filepos)
        if valix == -1:
            break
        
        val = data[filepos:valix]
        filepos = valix + 1
        
        expireix = data.find("\n", filepos)
        if expireix == -1:
            break
        
        expire = data[filepos:expireix]
        filepos = expireix + 1
        
        dsdict[name] = [val, expire]

with open("ds.json", "w") as f:
    f.write(json.dumps(dsdict, indent=4))
print("Success!")
