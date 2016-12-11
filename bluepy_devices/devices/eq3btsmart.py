"""
Support for eq3 Bluetooth Smart thermostats.

All temperatures in Celsius.

To get the current state, update() has to be called for powersaving reasons.
"""

import struct
from datetime import datetime
from ..lib.connection import BTLEConnection

PROP_WRITE_HANDLE = 0x411
PROP_NTFY_HANDLE = 0x421

PROP_ID_QUERY = 0
PROP_ID_RETURN = 1
PROP_INFO_QUERY = 3
PROP_INFO_RETURN = 2
PROP_SCHEDULE_QUERY = 0x20
PROP_SCHEDULE_RETURN = 0x21

PROP_TEMPERATURE_WRITE = 0x41

EQ3BT_MIN_TEMP = 5.0
EQ3BT_MAX_TEMP = 30.0


class EQ3BTSmartTemperatureError(Exception):
    """Temperature out of range error."""
    pass


# pylint: disable=too-many-instance-attributes
class EQ3BTSmartThermostat:
    """Representation of a EQ3 Bluetooth Smart thermostat."""

    def __init__(self, _mac):
        """Initialize the thermostat."""

        self._target_temperature = -1
        self._mode = -1

        self._conn = BTLEConnection(_mac)

        self._conn.set_callback(PROP_NTFY_HANDLE, self.handle_notification)
        self._conn.connect()

        self.update()

    def __str__(self):
        return "MAC: " + self._conn.mac + " Mode: " + str(self.mode) + " = " + self.mode_readable + " T: " + str(self.target_temperature)

    def _verify_temperature(self, temp):
        """Verifies that the temperature is valid, raises \
        EQ3BTSmartTemperatureError otherwise."""
        if temp < self.min_temp or temp > self.max_temp:
            raise EQ3BTSmartTemperatureError('Temperature {} out of range [{}, {}]'.format(temp, self.min_temp, self.max_temp))

    def handle_notification(self, data):
        """Handle Callback from a Bluetooth (GATT) request."""
        if data[0] == PROP_INFO_RETURN:
            self._mode = data[2] & 1
            self._target_temperature = data[5] / 2.0

    def update(self):
        """Update the data from the thermostat. Always sets the current time."""
        time = datetime.now()
        value = struct.pack('BBBBBBB', PROP_INFO_QUERY,
                            time.year % 100, time.month, time.day,
                            time.hour, time.minute, time.second)
        self._conn.write_request_raw(PROP_WRITE_HANDLE, value)

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    @target_temperature.setter
    def target_temperature(self, temperature):
        """Set new target temperature."""
        self._verify_temperature(temperature)
        value = struct.pack('BB', PROP_TEMPERATURE_WRITE, int(temperature * 2))
        # Returns INFO_QUERY, so use that
        self._conn.write_request_raw(PROP_WRITE_HANDLE, value)

    @property
    def mode(self):
        """Return the mode (auto / manual)."""
        return self._mode

    @property
    def mode_readable(self):
        """Return a readable representation of the mode.."""
        return self.decode_mode(self._mode)

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return EQ3BT_MIN_TEMP

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return EQ3BT_MAX_TEMP

    @staticmethod
    def decode_mode(mode):
        """Convert the numerical mode to a human-readable description."""
        ret = ""
        if mode & 1:
            ret = "manual"
        else:
            ret = "auto"

        if mode & 2:
            ret = ret + " holiday"
        if mode & 4:
            ret = ret + " boost"
        if mode & 8:
            ret = ret + " dst"
        if mode & 16:
            ret = ret + " window"

        return ret
