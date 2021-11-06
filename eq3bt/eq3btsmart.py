"""
Support for eq3 Bluetooth Smart thermostats.

All temperatures in Celsius.

To get the current state, update() has to be called for powersaving reasons.
Schedule needs to be requested with query_schedule() before accessing for similar reasons.
"""

import logging
import struct
import codecs
from datetime import datetime, timedelta
from construct import Byte
from enum import IntEnum

from .connection import BTLEConnection
from .structures import AwayDataAdapter, DeviceId, Schedule, Status

_LOGGER = logging.getLogger(__name__)

PROP_WRITE_HANDLE = 0x411
PROP_NTFY_HANDLE = 0x421

PROP_ID_QUERY = 0
PROP_ID_RETURN = 1
PROP_INFO_QUERY = 3
PROP_INFO_RETURN = 2
PROP_COMFORT_ECO_CONFIG = 0x11
PROP_OFFSET = 0x13
PROP_WINDOW_OPEN_CONFIG = 0x14
PROP_SCHEDULE_QUERY = 0x20
PROP_SCHEDULE_RETURN = 0x21

PROP_MODE_WRITE = 0x40
PROP_TEMPERATURE_WRITE = 0x41
PROP_COMFORT = 0x43
PROP_ECO = 0x44
PROP_BOOST = 0x45
PROP_LOCK = 0x80

EQ3BT_AWAY_TEMP = 12.0
EQ3BT_MIN_TEMP = 5.0
EQ3BT_MAX_TEMP = 29.5
EQ3BT_OFF_TEMP = 4.5
EQ3BT_ON_TEMP = 30.0


class Mode(IntEnum):
    """ Thermostat modes. """
    Unknown = -1
    Closed = 0
    Open = 1
    Auto = 2
    Manual = 3
    Away = 4
    Boost = 5


MODE_NOT_TEMP = [Mode.Unknown,
                 Mode.Closed,
                 Mode.Open]


class TemperatureException(Exception):
    """Temperature out of range error."""
    pass


# pylint: disable=too-many-instance-attributes
class Thermostat:
    """Representation of a EQ3 Bluetooth Smart thermostat."""

    def __init__(self, _mac, _iface=None, connection_cls=BTLEConnection):
        """Initialize the thermostat."""

        self._target_temperature = Mode.Unknown
        self._mode = Mode.Unknown
        self._valve_state = Mode.Unknown
        self._raw_mode = None

        self._schedule = {}

        self._window_open_temperature = None
        self._window_open_time = None
        self._comfort_temperature = None
        self._eco_temperature = None
        self._temperature_offset = None

        self._away_temp = EQ3BT_AWAY_TEMP
        self._away_duration = timedelta(days=30)
        self._away_end = None

        self._firmware_version = None
        self._device_serial = None

        self._conn = connection_cls(_mac, _iface)
        self._conn.set_callback(PROP_NTFY_HANDLE, self.handle_notification)

    def __str__(self):
        away_end = "no"
        if self.away_end:
            away_end = "end: %s" % self._away_end

        return "[%s] Target %s (mode: %s, away: %s)" % (self._conn.mac,
                                                        self.target_temperature,
                                                        self.mode_readable,
                                                        away_end)

    def _verify_temperature(self, temp):
        """Verifies that the temperature is valid.
            :raises TemperatureException: On invalid temperature.
        """
        if temp < self.min_temp or temp > self.max_temp:
            raise TemperatureException('Temperature {} out of range [{}, {}]'
                                       .format(temp, self.min_temp, self.max_temp))

    def parse_schedule(self, data):
        """Parses the device sent schedule."""
        sched = Schedule.parse(data)
        _LOGGER.debug("Got schedule data for day '%s'", sched.day)

        return sched

    def handle_notification(self, data):
        """Handle Callback from a Bluetooth (GATT) request."""
        _LOGGER.debug("Received notification from the device..")

        if data[0] == PROP_INFO_RETURN and data[1] == 1:
            _LOGGER.debug("Got status: %s" % codecs.encode(data, 'hex'))
            status = Status.parse(data)
            _LOGGER.debug("Parsed status: %s", status)

            self._raw_mode = status.mode
            self._valve_state = status.valve
            self._target_temperature = status.target_temp

            if status.mode.BOOST:
                self._mode = Mode.Boost
            elif status.mode.AWAY:
                self._mode = Mode.Away
                self._away_end = status.away
            elif status.mode.MANUAL:
                if status.target_temp == EQ3BT_OFF_TEMP:
                    self._mode = Mode.Closed
                elif status.target_temp == EQ3BT_ON_TEMP:
                    self._mode = Mode.Open
                else:
                    self._mode = Mode.Manual
            else:
                self._mode = Mode.Auto

            presets = status.presets
            if presets:
                self._window_open_temperature = presets.window_open_temp
                self._window_open_time = presets.window_open_time
                self._comfort_temperature = presets.comfort_temp
                self._eco_temperature = presets.eco_temp
                self._temperature_offset = presets.offset
            else:
                self._window_open_temperature = None
                self._window_open_time = None
                self._comfort_temperature = None
                self._eco_temperature = None
                self._temperature_offset = None

            _LOGGER.debug("Valve state:      %s", self._valve_state)
            _LOGGER.debug("Mode:             %s", self.mode_readable)
            _LOGGER.debug("Target temp:      %s", self._target_temperature)
            _LOGGER.debug("Away end:         %s", self._away_end)
            _LOGGER.debug("Window open temp: %s",
                          self._window_open_temperature)
            _LOGGER.debug("Window open time: %s", self._window_open_time)
            _LOGGER.debug("Comfort temp:     %s", self._comfort_temperature)
            _LOGGER.debug("Eco temp:         %s", self._eco_temperature)
            _LOGGER.debug("Temp offset:      %s", self._temperature_offset)

        elif data[0] == PROP_SCHEDULE_RETURN:
            parsed = self.parse_schedule(data)
            self._schedule[parsed.day] = parsed

        elif data[0] == PROP_ID_RETURN:
            parsed = DeviceId.parse(data)
            _LOGGER.debug("Parsed device data: %s", parsed)
            self._firmware_version = parsed.version
            self._device_serial = parsed.serial

        else:
            _LOGGER.debug("Unknown notification %s (%s)", data[0], codecs.encode(data, 'hex'))

    def query_id(self):
        """Query device identification information, e.g. the serial number."""
        _LOGGER.debug("Querying id..")
        value = struct.pack('B', PROP_ID_QUERY)
        self._conn.make_request(PROP_WRITE_HANDLE, value)

    def update(self):
        """Update the data from the thermostat. Always sets the current time."""
        _LOGGER.debug("Querying the device..")
        time = datetime.now()
        value = struct.pack('BBBBBBB', PROP_INFO_QUERY,
                            time.year % 100, time.month, time.day,
                            time.hour, time.minute, time.second)

        self._conn.make_request(PROP_WRITE_HANDLE, value)

    def query_schedule(self, day):
        _LOGGER.debug("Querying schedule..")

        if day < 0 or day > 6:
            _LOGGER.error("Invalid day: %s", day)

        value = struct.pack('BB', PROP_SCHEDULE_QUERY, day)

        self._conn.make_request(PROP_WRITE_HANDLE, value)

    @property
    def schedule(self):
        """ Returns previously fetched schedule.
         :return: Schedule structure or None if not fetched.
         """
        return self._schedule

    def set_schedule(self, data):
        """Sets the schedule for the given day. """
        value = Schedule.build(data)
        self._conn.make_request(PROP_WRITE_HANDLE, value)

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    @target_temperature.setter
    def target_temperature(self, temperature):
        """Set new target temperature."""
        dev_temp = int(temperature * 2)
        if temperature == EQ3BT_OFF_TEMP or temperature == EQ3BT_ON_TEMP:
            dev_temp |= 0x40
            value = struct.pack('BB', PROP_MODE_WRITE, dev_temp)
        else:
            self._verify_temperature(temperature)
            value = struct.pack('BB', PROP_TEMPERATURE_WRITE, dev_temp)

        self._conn.make_request(PROP_WRITE_HANDLE, value)

    @property
    def mode(self):
        """Return the current operation mode"""
        return self._mode

    @mode.setter
    def mode(self, mode):
        """Set the operation mode."""
        _LOGGER.debug("Setting new mode: %s", mode)

        if self.mode == Mode.Boost and mode != Mode.Boost:
            self.boost = False

        if mode == Mode.Boost:
            self.boost = True
            return
        elif mode == Mode.Away:
            end = datetime.now() + self._away_duration
            return self.set_away(end, self._away_temp)
        elif mode == Mode.Closed:
            return self.set_mode(0x40 | int(EQ3BT_OFF_TEMP * 2))
        elif mode == Mode.Open:
            return self.set_mode(0x40 | int(EQ3BT_ON_TEMP * 2))

        if mode == Mode.Manual:
            temperature = max(min(self._target_temperature, self.max_temp),
                              self.min_temp)
            return self.set_mode(0x40 | int(temperature * 2))
        else:
            return self.set_mode(0)

    @property
    def away_end(self):
        return self._away_end

    def set_away(self, away_end=None, temperature=EQ3BT_AWAY_TEMP):
        """ Sets away mode with target temperature.
            When called without parameters disables away mode."""
        if not away_end:
            _LOGGER.debug("Disabling away, going to auto mode.")
            return self.set_mode(0x00)

        _LOGGER.debug("Setting away until %s, temp %s", away_end, temperature)
        adapter = AwayDataAdapter(Byte[4])
        packed = adapter.build(away_end)

        self.set_mode(0x80 | int(temperature * 2), packed)

    def set_mode(self, mode, payload=None):
        value = struct.pack('BB', PROP_MODE_WRITE, mode)
        if payload:
            value += payload
        self._conn.make_request(PROP_WRITE_HANDLE, value)

    @property
    def mode_readable(self):
        """Return a readable representation of the mode.."""
        ret = ""
        mode = self._raw_mode

        if mode.MANUAL:
            ret = "manual"
            if self.target_temperature < self.min_temp:
                ret += " off"
            elif self.target_temperature >= self.max_temp:
                ret += " on"
            else:
                ret += " (%sC)" % self.target_temperature
        else:
            ret = "auto"

        if mode.AWAY:
            ret += " holiday"
        if mode.BOOST:
            ret += " boost"
        if mode.DST:
            ret += " dst"
        if mode.WINDOW:
            ret += " window"
        if mode.LOCKED:
            ret += " locked"
        if mode.LOW_BATTERY:
            ret += " low battery"

        return ret

    @property
    def boost(self):
        """Returns True if the thermostat is in boost mode."""
        return self.mode == Mode.Boost

    @boost.setter
    def boost(self, boost):
        """Sets boost mode."""
        _LOGGER.debug("Setting boost mode: %s", boost)
        value = struct.pack('BB', PROP_BOOST, bool(boost))
        self._conn.make_request(PROP_WRITE_HANDLE, value)

    @property
    def valve_state(self):
        """Returns the valve state. Probably reported as percent open."""
        return self._valve_state

    @property
    def window_open(self):
        """Returns True if the thermostat reports a open window
           (detected by sudden drop of temperature)"""
        return self._raw_mode and self._raw_mode.WINDOW

    def window_open_config(self, temperature, duration):
        """Configures the window open behavior. The duration is specified in
        5 minute increments."""
        _LOGGER.debug("Window open config, temperature: %s duration: %s", temperature, duration)
        self._verify_temperature(temperature)
        if duration.seconds < 0 and duration.seconds > 3600:
            raise ValueError

        value = struct.pack('BBB', PROP_WINDOW_OPEN_CONFIG,
                            int(temperature * 2), int(duration.seconds / 300))
        self._conn.make_request(PROP_WRITE_HANDLE, value)

    @property
    def window_open_temperature(self):
        """The temperature to set when an open window is detected."""
        return self._window_open_temperature

    @property
    def window_open_time(self):
        """Timeout to reset the thermostat after an open window is detected."""
        return self._window_open_time

    @property
    def locked(self):
        """Returns True if the thermostat is locked."""
        return self._raw_mode and self._raw_mode.LOCKED

    @locked.setter
    def locked(self, lock):
        """Locks or unlocks the thermostat."""
        _LOGGER.debug("Setting the lock: %s", lock)
        value = struct.pack('BB', PROP_LOCK, bool(lock))
        self._conn.make_request(PROP_WRITE_HANDLE, value)

    @property
    def low_battery(self):
        """Returns True if the thermostat reports a low battery."""
        return self._raw_mode and self._raw_mode.LOW_BATTERY

    def temperature_presets(self, comfort, eco):
        """Set the thermostats preset temperatures comfort (sun) and
        eco (moon)."""
        _LOGGER.debug("Setting temperature presets, comfort: %s eco: %s", comfort, eco)
        self._verify_temperature(comfort)
        self._verify_temperature(eco)
        value = struct.pack('BBB', PROP_COMFORT_ECO_CONFIG, int(comfort * 2),
                            int(eco * 2))
        self._conn.make_request(PROP_WRITE_HANDLE, value)

    @property
    def comfort_temperature(self):
        """Returns the comfort temperature preset of the thermostat."""
        return self._comfort_temperature

    @property
    def eco_temperature(self):
        """Returns the eco temperature preset of the thermostat."""
        return self._eco_temperature

    @property
    def temperature_offset(self):
        """Returns the thermostat's temperature offset."""
        return self._temperature_offset

    @temperature_offset.setter
    def temperature_offset(self, offset):
        """Sets the thermostat's temperature offset."""
        _LOGGER.debug("Setting offset: %s", offset)
        # [-3,5 .. 0  .. 3,5 ]
        # [00   .. 07 .. 0e ]
        if offset < -3.5 or offset > 3.5:
            raise TemperatureException("Invalid value: %s" % offset)

        current = -3.5
        values = {}
        for i in range(15):
            values[current] = i
            current += 0.5

        value = struct.pack('BB', PROP_OFFSET, values[offset])
        self._conn.make_request(PROP_WRITE_HANDLE, value)

    def activate_comfort(self):
        """Activates the comfort temperature."""
        value = struct.pack('B', PROP_COMFORT)
        self._conn.make_request(PROP_WRITE_HANDLE, value)

    def activate_eco(self):
        """Activates the comfort temperature."""
        value = struct.pack('B', PROP_ECO)
        self._conn.make_request(PROP_WRITE_HANDLE, value)

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return EQ3BT_MIN_TEMP

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return EQ3BT_MAX_TEMP

    @property
    def firmware_version(self):
        """Return the firmware version."""
        return self._firmware_version

    @property
    def device_serial(self):
        """Return the device serial number."""
        return self._device_serial

