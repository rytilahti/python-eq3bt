"""
A simple wrapper for bluepy's btle.Connection.
Handles Connection duties (reconnecting etc.) transparently.
"""
import logging

from bluepy import btle

DEFAULT_TIMEOUT = 1

_LOGGER = logging.getLogger(__name__)


class BTLEConnection(btle.DefaultDelegate):
    """Representation of a BTLE Connection."""

    def __init__(self, mac):
        """Initialize the connection."""
        btle.DefaultDelegate.__init__(self)

        self._conn = None
        self._mac = mac
        self._callbacks = {}

    def __enter__(self):
        """
        Context manager __enter__ for connecting the device
        :rtype: btle.Peripheral
        :return:
        """
        self._conn = btle.Peripheral()
        self._conn.withDelegate(self)
        _LOGGER.debug("Trying to connect to %s", self._mac)
        try:
            self._conn.connect(self._mac)
        except btle.BTLEException:
            _LOGGER.warning("Unable to connect to the device %s, retrying..", self._mac)
            try:
                self._conn.connect(self._mac)
            except Exception as ex2:
                _LOGGER.error("Second connection try to %s failed: %s", self._mac, ex2)
                raise

        _LOGGER.debug("Connected to %s", self._mac)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn:
            self._conn.disconnect()
            self._conn = None

    def handleNotification(self, handle, data):
        """Handle Callback from a Bluetooth (GATT) request."""
        _LOGGER.debug("Got notification from %s: %s", handle, data)
        if handle in self._callbacks:
            self._callbacks[handle](data)

    @property
    def mac(self):
        """Return the MAC address of the connected device."""
        return self._mac

    def set_callback(self, handle, function):
        """Set the callback for a Notification handle. It will be called with the parameter data, which is binary."""
        self._callbacks[handle] = function

    def make_request(self, handle, value, timeout=DEFAULT_TIMEOUT, with_response=True):
        """Write a GATT Command without callback - not utf-8."""
        try:
            with self:
                _LOGGER.debug("Writing to %s to %s with with_response=%s", handle, value, with_response)
                self._conn.writeCharacteristic(handle, value, withResponse=with_response)
                if timeout:
                    _LOGGER.debug("Waiting for notifications for %s", timeout)
                    self._conn.waitForNotifications(timeout)
        except btle.BTLEException as ex:
            _LOGGER.error("Got btle exception: %s", ex, exc_info=True)
