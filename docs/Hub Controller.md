# Hub Controller

The hub controller is a MicroPython module to be run by a Pybricks device.
It can read and write data from the terminal,
which allows communication through bluetooth (BLE, to be specific).

## Installation

1. To install the hub controller onto a LEGO Mindstorms hub,
   the hub first needs to run Pybricks as its firmware.
   See the official Pybricks documentation for instructions.

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) on your PC.

1. From the repository root, install dependencies:

   ```sh
   uv sync
   ```

1. Flash the LEGO hub device by running:

   ```sh
   uv run pybricksdev run ble ./hub/hub_controller.py

   # Alternatively, using the makefile:
   # make flash
   ```

   Pybricksdev will search for a valid device running Pybricks using Bluetooth.
   Make sure the hub is turned on at this point, but not running.
   Once the device is detected, the `hub_controller.py` module will be installed.
   Afterwards, the controller can be started any time by pressing the center button.
