# bluepy_devices
Simplified BTLE Device Interface for bluepy

Setup

python3 setup.py build
python3 setup.py install

or

pip3 install bluepy_devices

Provides a basic library to connect to a BTLE device, and has at present one device interface class for basic EQ3 Bluetooth Smart functionality.

CAVEAT: The device in question has to be disconnected from bluetoothd, since BTLE devices can only hold one connection at a time.

# command-line client
To test all available functionality a cli tool inside utils can be used.

EQ3_MAC environment variable can be used to define mac to avoid typing it:
```bash
export EQ3_MAC=XX:XX
```

Without parameters current state of the device is printed out.
```bash
python -m utils.eq3cli

MAC: XX:XX:XX:XX:XX:XX Mode: 2 = auto dst locked T: 20.0
Locked: True
Batter low: False
Window open: False
Boost: False
Current target temp: 20.0
Current mode: auto dst locked
Valve: 0
```

Getting & setting values.
```bash
python -m utils.eq3cli temp

Current target temp: 17.0

python -m utils.eq3cli temp --target 20

Current target temp: 17.0
Setting target temp: 20.0
```

For help, use --help
```bash
python3 -m utils.cli --help
```
