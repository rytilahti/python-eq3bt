# bluepy_devices
Simplified BTLE Device Interface for bluepy

Setup

python3 setup.py build
python3 setup.py install

or

pip3 install bluepy_devices

Provides a basic library to connect to a BTLE device, and has at present one device interface class for basic EQ3 Bluetooth Smart functionality.

CAVEAT: The device in question has to be disconnected from bluetoothd, since BTLE devices can only hold one connection at a time.
