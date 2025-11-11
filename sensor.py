import os
import subprocess
import time
import math
import traceback
from datetime import datetime
from multiprocessing.connection import Connection

from bicycleinit.BicycleSensor import BicycleSensor


def main(bicycleinit: Connection, name: str, args: dict):
  sensor = BicycleSensor(bicycleinit, name, args)
  sensor.write_header(['file'])

  try:
    interval = float(args.get('interval', 5.0))    # seconds between pictures
    if interval <= 0:
      raise ValueError("interval must be > 0")
    output_format = args.get('format', 'png')  # lossless format: png
    session = args['session']

    raw = args.get('raw', False)
    rotation = args.get('rotation', 180) # 0 or 180
    shutter = args.get('shutter', 10000) # exposure in microseconds

    temp_dir = os.path.join('temp', session)

    t = time.monotonic() - interval

    while True:
      tn = time.monotonic()
      if tn < t+interval:
        time.sleep(0.1)
        continue

      # Align t forward by the number of full intervals that passed.
      # Use integer count to avoid issues with float floor-division precision.
      count = int((tn - t) / interval)
      if count > 0:
        t += interval * count

      # Create a timestamped filename
      timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")
      filename = f"{name}_{timestamp}.{output_format}"
      output_path = os.path.join(temp_dir, filename)

      # Take a picture with fixed settings and capture output to check success
      proc_args = [
        "/usr/bin/rpicam-still",
        "--encoding", output_format,
        "--output", output_path,
        "--shutter", f"{shutter}",    # exposure in microseconds
        "--gain", "1.0",         # ISO/gain
        "--awbgains", "1,1",       # disable auto white balance
        "--ev", "0",
        "--autofocus-on-capture", "0",
        "--zsl", "0",
        "--rotation", f"{rotation}",
        "--immediate",       # capture immediately
        "--nopreview",
      ]
      if raw:
        proc_args.append("--raw")

      result = subprocess.run(proc_args, capture_output=True, text=True)
      if result.returncode == 0:
        # Record only the filename (not full path) as the measurement
        sensor.write_measurement([filename])
        sensor.send_msg({'type': 'upload', 'file': filename})
        sensor.send_msg({'type': 'upload', 'file': f"{name}_{timestamp}.dng"})
      else:
        msg = (
          f"rpicam-still failed for {filename} (rc={result.returncode}). "
          f"stdout: {result.stdout!r} stderr: {result.stderr!r}"
        )
        raise RuntimeError(msg)

  except KeyboardInterrupt:
    pass
  except Exception as e:
    sensor.send_msg({'type': 'log', 'level': 'error', 'msg': str(e)})
    if raw:
      sensor.send_msg({'type': 'log', 'level': 'error', 'msg': traceback.format_exc()})
  finally:
    sensor.shutdown()

if __name__ == "__main__":
  main(None, "bicyclecam", {'interval': '5', 'format': 'png'})
