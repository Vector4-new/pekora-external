import subprocess
import tempfile

def CompileSource(source : str):
    inFilePath = tempfile.mktemp()
    outFilePath = tempfile.mktemp()

    with open(inFilePath, "w") as f:
        f.write(source)

    subprocess.run([ "./luac5.1.exe", "-o", outFilePath, inFilePath ])

    return open(outFilePath, "rb").read()