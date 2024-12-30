import subprocess
import tempfile

def CompileSource(source : str):
    inFilePath = tempfile.mktemp()
    outFilePath = tempfile.mktemp()

    with open(inFilePath, "w") as f:
        f.write(source)

    result = subprocess.run([ "./luac5.1.exe", "-o", outFilePath, inFilePath ], capture_output=True, text=True)

    if result.returncode == 1:
        colon = result.stderr.find(":")

        raise ValueError(result.stderr[colon + 1:-1])

    return open(outFilePath, "rb").read()