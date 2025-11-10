import subprocess
import time
import traceback
from datetime import datetime
from multiprocessing.connection import Connection

from bicycleinit.BicycleSensor import BicycleSensor


def main(bicycleinit: Connection, name: str, args: dict):
  sensor = BicycleSensor(bicycleinit, name, args)
  sensor.write_header(['file'])

  try:
    interval = int(args.get('interval', 5))    # seconds between pictures
    output_format = args.get('format', 'png')  # lossless format: png

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

      # Take a picture with fixed settings and capture output to check success
      result = subprocess.run([
        "/usr/bin/rpicam-still",
        "-o", filename,
        "--shutter", "10000",    # exposure in microseconds (20 ms)
        "--gain", "1.0",         # ISO/gain
        "--awb", "custom",       # disable auto white balance
        "--ev", "0",
        "--autofocus-on-capture", "0",
        "--zsl", "0",
        "--nopreview",
      ], capture_output=True, text=True)

      if result.returncode == 0:
        sensor.write_measurement([filename])
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
    sensor.send_msg({'type': 'log', 'level': 'error', 'msg': traceback.format_exc()})
  finally:
    sensor.shutdown()

if __name__ == "__main__":
  main(None, "bicyclecam", {'interval': '5', 'format': 'png'})
