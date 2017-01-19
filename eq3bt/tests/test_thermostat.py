from unittest import TestCase
from eq3bt import Thermostat, TemperatureException

class FakeConnection:
    def __init__(self, mac):
        pass

    def set_callback(self, handle, cb):
        pass


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
        self.fail()

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
        self.fail()

    def test_window_open(self):
        self.fail()

    def test_window_open_config(self):
        self.fail()

    def test_locked(self):
        self.fail()

    def test_low_battery(self):
        self.fail()

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
