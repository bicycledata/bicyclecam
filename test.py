import subprocess
import time
from datetime import datetime

# Settings
interval = 5  # seconds between pictures
output_format = "png"  # lossless format: png or tiff

t = time.monotonic() - interval

while True:
    tn = time.monotonic()
    if tn < t+interval:
        time.sleep(0.1)
        continue

    t += interval * ((tn - t) // interval)

    # Create a timestamped filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"photo_{timestamp}.{output_format}"

    # Take a picture with fixed settings
    subprocess.run([
        "/usr/bin/rpicam-still",       # or "rpicam-still" depending on your system
        "-o", filename,
        "--shutter", "10000",    # exposure in microseconds (20 ms)
        "--gain", "1.0",         # ISO/gain
        "--awb", "custom",       # disable auto white balance
        "--ev", "0",
        "--autofocus-on-capture", "0",
        "--zsl", "0",
        "--nopreview",
    ])

    subprocess.run([
        "cp",
        filename,
        f"latest.{output_format}"
    ])

    print(f"Saved {filename}")
