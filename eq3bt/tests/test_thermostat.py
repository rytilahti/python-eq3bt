from unittest import TestCase

import codecs
from datetime import datetime

from eq3bt import Thermostat, TemperatureException
from eq3bt.eq3btsmart import (PROP_NTFY_HANDLE, PROP_ID_QUERY,
                              PROP_INFO_QUERY, Mode)


ID_RESPONSE = b'01780000807581626163606067659e'
STATUS_RESPONSES = {
    'auto': b'020100000428',
    'manual': b'020101000428',
    'window': b'020110000428',
    'away': b'0201020004231d132e03',
    'boost': b'020104000428',
    'low_batt': b'020180000428',
    'valve_at_22': b'020100160428',
}


class FakeConnection:
    def __init__(self, mac):
        self._callbacks = {}
        self._res = 'auto'

    def set_callback(self, handle, cb):
        self._callbacks[handle] = cb

    def set_status(self, key):
        if key in STATUS_RESPONSES:
            self._res = key
        else:
            raise ValueError("Invalid key for status test response.")

    def make_request(self, handle, value, timeout=1, with_response=True):
        """Write a GATT Command without callback - not utf-8."""
        if with_response:
            cb = self._callbacks.get(PROP_NTFY_HANDLE)

            if value[0] == PROP_ID_QUERY:
                data = ID_RESPONSE
            elif value[0] == PROP_INFO_QUERY:
                data = STATUS_RESPONSES[self._res]
            else:
                return
            cb(codecs.decode(data, 'hex'))


class TestThermostat(TestCase):
    def setUp(self):
        self.thermostat = Thermostat(_mac=None, connection_cls=FakeConnection)

    def test__verify_temperature(self):
        with self.assertRaises(TemperatureException):
            self.thermostat._verify_temperature(-1)
        with self.assertRaises(TemperatureException):
            self.thermostat._verify_temperature(35)

        self.thermostat._verify_temperature(8)
        self.thermostat._verify_temperature(25)

    def test_parse_schedule(self):
        self.fail()

    def test_handle_notification(self):
        self.fail()

    def test_update(self):
        th = self.thermostat

        th._conn.set_status('auto')
        th.update()
        self.assertEqual(th.valve_state, 0)
        self.assertEqual(th.mode, Mode.Auto)
        self.assertEqual(th.target_temperature, 20.0)
        self.assertFalse(th.locked)
        self.assertFalse(th.low_battery)
        self.assertFalse(th.boost)
        self.assertFalse(th.window_open)

        th._conn.set_status('manual')
        th.update()
        self.assertTrue(th.mode, Mode.Manual)

        th._conn.set_status('away')
        th.update()
        self.assertEqual(th.mode, Mode.Away)
        self.assertEqual(th.target_temperature, 17.5)
        self.assertEqual(th.away_end, datetime(2019, 3, 29, 23, 00))

        th._conn.set_status('boost')
        th.update()
        self.assertTrue(th.boost)
        self.assertEqual(th.mode, Mode.Boost)

    def test_query_schedule(self):
        self.fail()

    def test_schedule(self):
        self.fail()

    def test_set_schedule(self):
        self.fail()

    def test_target_temperature(self):
        self.fail()

    def test_mode(self):
        self.fail()

    def test_mode_readable(self):
        self.fail()

    def test_boost(self):
        self.fail()

    def test_valve_state(self):
        th = self.thermostat
        th._conn.set_status('valve_at_22')
        th.update()
        self.assertEqual(th.valve_state, 22)

    def test_window_open(self):
        th = self.thermostat
        th._conn.set_status('window')
        th.update()
        self.assertTrue(th.window_open)

    def test_window_open_config(self):
        self.fail()

    def test_locked(self):
        self.fail()

    def test_low_battery(self):
        th = self.thermostat
        th._conn.set_status('low_batt')
        th.update()
        self.assertTrue(th.low_battery)

    def test_temperature_offset(self):
        self.fail()

    def test_activate_comfort(self):
        self.fail()

    def test_activate_eco(self):
        self.fail()

    def test_min_temp(self):
        self.fail()

    def test_max_temp(self):
        self.fail()

    def test_away_end(self):
        self.fail()

    def test_decode_mode(self):
        self.fail()
