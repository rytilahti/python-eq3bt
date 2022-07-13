# python-eq3bt

Python library and a command line tool for EQ3 Bluetooth smart thermostats, uses bleak (default), bluepy or gattlib for BTLE communication.

# Features

* Reading device status: locked, low battery, valve state, window open, target temperature, active mode
* Writing settings: target temperature, auto mode presets, temperature offset
* Setting the active mode: auto, manual, boost, away
* Reading the device serial number and firmware version
* Reading presets and temperature offset in more recent firmware versions.

## Not (yet) supported

* No easy-to-use interface for setting schedules.

# Installation

```bash
pip install python-eq3bt
```

# Command-line Usage

To test all available functionality a cli tool inside utils can be used:
```
$ eq3cli  --help
Usage: eq3cli [OPTIONS] COMMAND [ARGS]...

  Tool to query and modify the state of EQ3 BT smart thermostat.

Options:
  --mac TEXT                  [required]
  --interface TEXT
  --debug / --normal
  --backend [bleak|bluepy|gattlib]
  --help                      Show this message and exit.

Commands:
  away         Enables or disables the away mode.
  boost        Gets or sets the boost mode.
  device       Displays basic device information.
  locked       Gets or sets the lock.
  low-battery  Gets the low battery status.
  mode         Gets or sets the active mode.
  offset       Sets the temperature offset [-3,5 3,5]
  presets      Sets the preset temperatures for auto mode.
  schedule     Gets the schedule from the thermostat.
  state        Prints out all available information.
  temp         Gets or sets the target temperature.
  valve-state  Gets the state of the valve.
  window-open  Gets and sets the window open settings.
```

EQ3_MAC environment variable can be used to define mac to avoid typing it:
```bash
export EQ3_MAC=XX:XX
```

Without parameters current state of the device is printed out.
```bash
$ eq3cli

[00:1A:22:XX:XX:XX] Target 17.0 (mode: auto dst, away: no)
Locked: False
Batter low: False
Window open: False
Window open temp: 12.0
Window open time: 0:15:00
Boost: False
Current target temp: 17.0
Current comfort temp: 20.0
Current eco temp: 17.0
Current mode: auto dst locked
Valve: 0
```

Getting & setting values.
```bash
$ eq3cli temp

Current target temp: 17.0

eq3cli temp --target 20

Current target temp: 17.0
Setting target temp: 20.0
```

# Pairing

If you have thermostat with firmware version 1.20+ pairing may be needed. Below simple procedure to do that.

```
Press and hold wheel on thermostat until Pair will be displayed. Remember or write it.

$ sudo bluetoothctl
[bluetooth]# power on
[bluetooth]# agent on
[bluetooth]# default-agent
[bluetooth]# scan on
[bluetooth]# scan off
[bluetooth]# pair 00:1A:22:06:A7:83
[agent] Enter passkey (number in 0-999999): <enter pin>
[bluetooth]# trust 00:1A:22:06:A7:83
[bluetooth]# disconnect 00:1A:22:06:A7:83
[bluetooth]# exit

Optional steps:
[bluetooth]# devices - to list all bluetooth devices
[bluetooth]# info 00:1A:22:06:A7:83
Device 00:1A:22:06:A7:83 (public)
	Name: CC-RT-BLE
	Alias: CC-RT-BLE
	Paired: yes
	Trusted: yes
	Blocked: no
	Connected: no
	LegacyPairing: no
	UUID: Generic Access Profile    (00001800-0000-1000-8000-00805f9b34fb)
	UUID: Generic Attribute Profile (00001801-0000-1000-8000-00805f9b34fb)
	UUID: Device Information        (0000180a-0000-1000-8000-00805f9b34fb)
	UUID: Vendor specific           (3e135142-654f-9090-134a-a6ff5bb77046)
	UUID: Vendor specific           (9e5d1e47-5c13-43a0-8635-82ad38a1386f)
	ManufacturerData Key: 0x0000
	ManufacturerData Value:
  00 00 00 00 00 00 00 00 00                       .........
```

Be aware that sometimes if you pair your device then mobile application (calor BT) can't connect with thermostat and vice versa.


# Library Usage

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

## Setting schedule

The 'base_temp' and 'next_change_at' paramater define the first period for that 'day' (the period from midnight up till next_change_at).

The schedule can be set on a per day basis like follows:

```
from datetime import time
from eq3bt import Thermostat
from eq3bt import HOUR_24_PLACEHOLDER as END_OF_DAY

thermostat = Thermostat('12:34:56:78:9A:BC')
thermostat.set_schedule(
    dict(
        cmd="write",
        day="sun",
        base_temp=18,
        next_change_at=time(8, 0),
        hours=[
            dict(target_temp=23, next_change_at=time(20, 0)),
            dict(target_temp=18, next_change_at=END_OF_DAY),
            dict(target_temp=23, next_change_at=END_OF_DAY),
            dict(target_temp=23, next_change_at=END_OF_DAY),
            dict(target_temp=23, next_change_at=END_OF_DAY),
            dict(target_temp=23, next_change_at=END_OF_DAY)
        ]
    )
)
```

# Contributing

Feel free to open pull requests to improve the library!

This project uses github actions to enforce code formatting using tools like black, isort, flake8, and mypy.
You can run these checks locally either by executing `pre-commit run -a` or using `tox` which also runs the test suite.


# History

This library is a simplified version of bluepy_devices from Markus Peter (https://github.com/bimbar/bluepy_devices.git) with support for more features and robuster device handling.
