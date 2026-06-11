import os
import shutil
import subprocess

piper_bin = shutil.which("piper")
if not piper_bin:
    piper_bin = os.path.expanduser("~/.local/bin/piper")

print("Piper path:", piper_bin)
if os.path.exists(piper_bin):
    print("Piper executable exists.")
else:
    print("Piper executable NOT FOUND.")

model_path = "/home/adler/Downloads/jarvis-windows/jarvis/voice/piper/tr_TR-dfki-medium.onnx"
print("Model path:", model_path)
if os.path.exists(model_path):
    print("Model exists.")
else:
    print("Model NOT FOUND.")

cmd = [piper_bin, "-m", model_path, "-f", "test_out.wav"]
print("Running command:", " ".join(cmd))
try:
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate(input=b"Merhaba, ben Jarvis.")
    print("Exit code:", p.returncode)
    if p.returncode != 0:
        print("Stderr:", stderr.decode("utf-8", errors="ignore"))
    else:
        print("Generated test_out.wav")
        if shutil.which("pw-play"):
            print("Playing test_out.wav via pw-play")
            subprocess.run(["pw-play", "test_out.wav"])
except Exception as e:
    print("Error:", e)
