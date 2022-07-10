"""
A simple adapter to gattlib.
Handles Connection duties (reconnecting etc.) transparently.
"""
import codecs
import logging
import threading

import gattlib

from . import BackendException

DEFAULT_TIMEOUT = 1

_LOGGER = logging.getLogger(__name__)


class BTLEConnection:
    """Representation of a BTLE Connection."""

    def __init__(self, mac, iface):
        """Initialize the connection."""

        self._conn = None
        self._mac = mac
        self._iface = iface
        self._callbacks = {}
        self._notifyevent = None

    def __enter__(self):
        """
        Context manager __enter__ for connecting the device
        :rtype: BTLEConnection
        :return:
        """
        _LOGGER.debug("Trying to connect to %s", self._mac)
        if self._iface is None:
            self._conn = gattlib.GATTRequester(self._mac, False)
        else:
            self._conn = gattlib.GATTRequester(self._mac, False, self._iface)
        self._conn.on_notification = self.on_notification
        try:
            self._conn.connect()
        except gattlib.BTBaseException as ex:
            _LOGGER.debug(
                "Unable to connect to the device %s, retrying: %s", self._mac, ex
            )
            try:
                self._conn.connect()
            except Exception as ex2:
                _LOGGER.debug("Second connection try to %s failed: %s", self._mac, ex2)
                raise BackendException(
                    "unable to connect to device using gattlib"
                ) from ex2

        _LOGGER.debug("Connected to %s", self._mac)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn:
            self._conn.disconnect()
            self._conn = None

    def on_notification(self, handle, data):
        """Handle Callback from a Bluetooth (GATT) request."""
        _LOGGER.debug(
            "Got notification from %s: %s", handle, codecs.encode(data, "hex")
        )
        if handle in self._callbacks:
            self._callbacks[handle](data[3:])
        if self._notifyevent:
            self._notifyevent.set()

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
                _LOGGER.debug(
                    "Writing %s to %s",
                    codecs.encode(value, "hex"),
                    handle,
                )
                self._notifyevent = threading.Event()
                self._conn.write_by_handle(handle, value)
                if timeout:
                    _LOGGER.debug("Waiting for notifications for %s", timeout)
                    self._notifyevent.wait(timeout)
        except gattlib.BTBaseException as ex:
            _LOGGER.debug("Got exception from gattlib while making a request: %s", ex)
            raise BackendException("Exception on write using gattlib") from ex
