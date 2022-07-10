# flake8: noqa
from .eq3btsmart import Mode, TemperatureException, Thermostat
from .structures import *


class BackendException(Exception):
    """Exception to wrap backend exceptions."""
