# python-eq3bt

Python library and a command line tool for EQ3 Bluetooth smart thermostats, uses bluepy for BTLE communication.

This library is a simplified version of bluepy_devices from Markus Peter (https://github.com/bimbar/bluepy_devices.git)
with support for more features and better device handling.

# Features

* Reading device status: locked, low battery, valve state, window open, target temperature, active mode
* Writing settings: target temperature, auto mode presets, temperature offset
* Setting the active mode: auto, manual, boost, away

## Not (yet) supported)

* Reading presets, temperature offset. This may not be possible.
* No easy-to-use interface for setting schedules.

# Installation

```bash
pip install python-eq3bt
```

# Usage

```
from eq3bt import Thermostat

thermostat = Thermostat('AB:CD:EF:12:23:45')
thermostat.update()  # fetches data from the thermostat

print(thermostat)
```

<aside class="notice">
Notice: The device in question has to be disconnected from bluetoothd, since BTLE devices can only hold one connection at a time.

The library will try to connect to the device second time in case it wasn't successful in the first time,
which can happen if you are running other applications connecting to the same thermostat.
</aside>

## Fetching schedule

The schedule is queried per day basis and the cached information can be
accessed through `schedule` property..

```
from eq3bt import Thermostat

thermostat = Thermostat('AB:CD:EF:12:34:45')
thermostat.query_schedule(0)
print(thermostat.schedule)
```

# Command-line tool

To test all available functionality a cli tool inside utils can be used.

EQ3_MAC environment variable can be used to define mac to avoid typing it:
```bash
export EQ3_MAC=XX:XX
```

Without parameters current state of the device is printed out.
```bash
eq3cli

[00:1A:22:XX:XX:XX] Target 17.0 (mode: auto dst, away: no)
Locked: False
Batter low: False
Window open: False
Boost: False
Current target temp: 17.0
Current mode: auto dst locked
Valve: 0
```

Getting & setting values.
```bash
eq3cli temp

Current target temp: 17.0

eq3cli temp --target 20

Current target temp: 17.0
Setting target temp: 20.0
```

For help, use --help
```bash
eq3cli --help
```
