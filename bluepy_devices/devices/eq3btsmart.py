"""
Support for eq3 Bluetooth Smart thermostats.

All temperatures in Celsius.

To get the current state, update() has to be called for powersaving reasons.
"""

import struct
from datetime import datetime, timedelta
from ..lib.connection import BTLEConnection
import logging

_LOGGER = logging.getLogger(__name__)

EQ3BTSMART_UNKOWN = -1
EQ3BTSMART_CLOSED = 0
EQ3BTSMART_OPEN = 1
EQ3BTSMART_AUTO = 2
EQ3BTSMART_MANUAL = 3
EQ3BTSMART_AWAY = 4
EQ3BTSMART_BOOST = 5

EQ3BTSMART_OFF = 0x09
EQ3BTSMART_ON = 0x3c

EQ3BTSMART_NO_TEMP_MODES = [EQ3BTSMART_UNKOWN,
                            EQ3BTSMART_CLOSED,
                            EQ3BTSMART_OPEN]

PROP_WRITE_HANDLE = 0x411
PROP_NTFY_HANDLE = 0x421

PROP_ID_QUERY = 0
PROP_ID_RETURN = 1
PROP_INFO_QUERY = 3
PROP_INFO_RETURN = 2
PROP_COMFORT_ECO_CONFIG = 0x11
PROP_WINDOW_OPEN_CONFIG = 0x14
PROP_SCHEDULE_QUERY = 0x20
PROP_SCHEDULE_RETURN = 0x21

PROP_MODE_WRITE = 0x40
PROP_TEMPERATURE_WRITE = 0x41
PROP_COMFORT = 0x43
PROP_ECO = 0x44
PROP_BOOST = 0x45
PROP_LOCK = 0x80

BITMASK_MANUAL = 0x01
BITMASK_AWAY = 0x02
BITMASK_BOOST = 0x04
BITMASK_DST = 0x08
BITMASK_WINDOW = 0x10
BITMASK_LOCKED = 0x20
BITMASK_BATTERY = 0x80

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

        self._target_temperature = EQ3BTSMART_UNKOWN
        self._raw_mode = EQ3BTSMART_UNKOWN
        self._mode = EQ3BTSMART_UNKOWN
        self._valve_state = EQ3BTSMART_UNKOWN

        self._away_temp = 12.0
        self._away_duration = timedelta(days=30)
        self._away_end = None

        self._conn = BTLEConnection(_mac)
        self._conn.set_callback(PROP_NTFY_HANDLE, self.handle_notification)

    def __str__(self):
        if self.mode == EQ3BTSMART_AWAY:
            away_end = " away end: " + str(self._away_end)
        else:
            away_end = ""
        return "MAC: " + self._conn.mac + " Mode: " + str(self.mode) + " = " + self.mode_readable + " T: " + str(self.target_temperature) + away_end

    def _verify_temperature(self, temp):
        """Verifies that the temperature is valid, raises \
        EQ3BTSmartTemperatureError otherwise."""
        if temp < self.min_temp or temp > self.max_temp:
            raise EQ3BTSmartTemperatureError('Temperature {} out of range [{}, {}]'.format(temp, self.min_temp, self.max_temp))

    def handle_notification(self, data):
        """Handle Callback from a Bluetooth (GATT) request."""
        _LOGGER.debug("Received notification from the device..")
        away_end = None
        if data[0] == PROP_INFO_RETURN:
            self._raw_mode = data[2]
            self._valve_state = data[3]

            self._target_temperature = data[5] / 2.0

            if self._raw_mode & BITMASK_BOOST:
                self._mode = EQ3BTSMART_BOOST
            elif self._raw_mode & BITMASK_AWAY:
                self._mode = EQ3BTSMART_AWAY
                if len(data) == 10:
                    year = 2000 + data[7]
                    month = data[9]
                    day = data[6]
                    hour = data[8] >> 1
                    minute = 30 * (data[8] & 1)
                    away_end = datetime(year, month, day, hour, minute)
            elif self._raw_mode & BITMASK_MANUAL:
                if data[5] == EQ3BTSMART_OFF:
                    self._mode = EQ3BTSMART_CLOSED
                    self._target_temperature = float(EQ3BTSMART_UNKOWN)
                elif data[5] == EQ3BTSMART_ON:
                    self._mode = EQ3BTSMART_OPEN
                    self._target_temperature = float(EQ3BTSMART_UNKOWN)
                else:
                    self._mode = EQ3BTSMART_MANUAL
            else:
                self._mode = EQ3BTSMART_AUTO
            self._away_end = away_end

            _LOGGER.debug("Valve state: %s", self._valve_state)
            _LOGGER.debug("Mode:        %s", self.mode_readable)
            _LOGGER.debug("Target temp: %s", self._target_temperature)
            _LOGGER.debug("Away end:    %s", self._away_end)

        else:
            _LOGGER.debug("Unknown notification %s (%s)", (data[0], data))

    def update(self):
        """Update the data from the thermostat. Always sets the current time."""
        _LOGGER.debug("Querying the device..")
        time = datetime.now()
        value = struct.pack('BBBBBBB', PROP_INFO_QUERY,
                            time.year % 100, time.month, time.day,
                            time.hour, time.minute, time.second)

        self._conn.write_request_raw(PROP_WRITE_HANDLE, value)

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        if self._mode in EQ3BTSMART_NO_TEMP_MODES:
            return None
        return self._target_temperature

    @target_temperature.setter
    def target_temperature(self, temperature):
        """Set new target temperature."""
        _LOGGER.debug("Setting new target temperature: %s", temperature)
        self._verify_temperature(temperature)
        if self._mode in EQ3BTSMART_NO_TEMP_MODES:
            return
        value = struct.pack('BB', PROP_TEMPERATURE_WRITE, int(temperature * 2))
        # Returns INFO_QUERY, so use that

        self._conn.write_request_raw(PROP_WRITE_HANDLE, value)

    @property
    def mode(self):
        """Return the current operation mode"""
        return self._mode

    @mode.setter
    def mode(self, mode):
        """Set the operation mode."""
        _LOGGER.debug("Setting new mode: %s", mode)
        mode_byte = 0
        away_end = None
        if self.mode == EQ3BTSMART_BOOST and mode != EQ3BTSMART_BOOST:
            self.boost = False

        if mode == EQ3BTSMART_BOOST:
            self.boost = True
            return
        elif mode == EQ3BTSMART_AWAY:
            mode_byte = 0x80 | int(self._away_temp * 2)
            end = datetime.now() + self._away_duration
            away_end = struct.pack('BBBB', end.day, end.year % 100,
                                   (end.hour * 2) | (end.minute >= 30),
                                   end.month)
        elif mode == EQ3BTSMART_CLOSED:
            mode_byte = 0x40 | EQ3BTSMART_OFF
        elif mode == EQ3BTSMART_OPEN:
            mode_byte = 0x40 | EQ3BTSMART_ON
        elif mode == EQ3BTSMART_MANUAL:
            mode_byte = 0x40

        value = struct.pack('BB', PROP_MODE_WRITE, mode_byte)
        if away_end is not None:
            value += away_end

        self._conn.write_request_raw(PROP_WRITE_HANDLE, value)

    @property
    def mode_readable(self):
        """Return a readable representation of the mode.."""
        return self.decode_mode(self._raw_mode)

    @property
    def boost(self):
        """Returns True if the thermostat is in boost mode."""
        return self.mode == EQ3BTSMART_BOOST

    @boost.setter
    def boost(self, boost):
        """Sets boost mode."""
        _LOGGER.debug("Setting boost mode: %s", boost)
        value = struct.pack('BB', PROP_BOOST, bool(boost))
        self._conn.write_request_raw(PROP_WRITE_HANDLE, value)

    @property
    def valve_state(self):
        """Returns the valve state. Probably reported as percent open."""
        return self._valve_state

    @property
    def window_open(self):
        """Returns True if the thermostat reports a open window
           (detected by sudden drop of temperature)"""
        return bool(self._raw_mode & BITMASK_WINDOW)

    def window_open_config(self, temperature, duration):
        """Configures the window open behavior. The duration is specified in
        5 minute increments."""
        _LOGGER.debug("Window open config, temperature: %s duration: %s", temperature, duration)
        self._verify_temperature(temperature)
        if duration.seconds < 0 and duration.seconds > 3600:
            raise ValueError

        value = struct.pack('BBB', PROP_WINDOW_OPEN_CONFIG,
                            int(temperature * 2), int(duration.seconds / 300))
        self._conn.write_request_raw(PROP_WRITE_HANDLE, value)

    @property
    def locked(self):
        """Returns True if the thermostat is locked."""
        return bool(self._raw_mode & BITMASK_LOCKED)

    @locked.setter
    def locked(self, lock):
        """Locks or unlocks the thermostat."""
        _LOGGER.debug("Setting the lock: %s", lock)
        value = struct.pack('BB', PROP_LOCK, bool(lock))
        self._conn.write_request_raw(PROP_WRITE_HANDLE, value)

    @property
    def low_battery(self):
        """Returns True if the thermostat reports a low battery."""
        return bool(self._raw_mode & BITMASK_BATTERY)

    def temperature_presets(self, comfort, eco):
        """Set the thermostats preset temperatures comfort (sun) and
        eco (moon)."""
        _LOGGER.debug("Setting temperature presets, comfort: %s eco: %s", comfort, eco)
        self._verify_temperature(comfort)
        self._verify_temperature(eco)
        value = struct.pack('BBB', PROP_COMFORT_ECO_CONFIG, int(comfort * 2),
                            int(eco * 2))
        self._conn.write_request_raw(PROP_WRITE_HANDLE, value)

    def activate_comfort(self):
        """Activates the comfort temperature."""
        value = struct.pack('B', PROP_COMFORT)
        self._conn.write_request_raw(PROP_WRITE_HANDLE, value)

    def activate_eco(self):
        """Activates the comfort temperature."""
        value = struct.pack('B', PROP_ECO)
        self._conn.write_request_raw(PROP_WRITE_HANDLE, value)

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
        if mode & BITMASK_MANUAL:
            ret = "manual"
        else:
            ret = "auto"

        if mode & BITMASK_AWAY:
            ret = ret + " holiday"
        if mode & BITMASK_BOOST:
            ret = ret + " boost"
        if mode & BITMASK_DST:
            ret = ret + " dst"
        if mode & BITMASK_WINDOW:
            ret = ret + " window"
        if mode & BITMASK_LOCKED:
            ret = ret + " locked"
        if mode & BITMASK_BATTERY:
            ret = ret + " low battery"

        return ret
