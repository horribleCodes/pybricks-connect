# Pybricks Connect

Pybricks Connect can be used to connect a PC to a LEGO hub
(such as the Inventor Hub from the last Mindstorms or Spike sets)
and send instructions to the device to either run motors or read data.
Implements the [Pybricks](https://pybricks.com/) library to flash and run your device.

## Setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then from the repository root:

```sh
uv sync
```

Start the server with `./start.sh`.
Alternatively, you can use `make sync` and `make server` to install and run the server, respectively.

## Components

This repository contains two individual modules:

- [**Hub Controller**](docs/Hub%20Controller.md):
  This MicroPython module uses the terminal to readand write data through a bluetooth connection.
  It also contains a library of commands used to interact with hub components
  such as motors and the ultrasonic sensor.
  It is flashed onto the hub itself.
- [**Server App**](docs/Server%20App.md):
  This module concurrently runs a flask server and a controller.
  The flask server is used to receive requests,
  while the controller handles the connection and workload of the hub.
