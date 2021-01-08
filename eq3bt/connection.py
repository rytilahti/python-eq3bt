"""
A simple wrapper for bluepy's btle.Connection.
Handles Connection duties (reconnecting etc.) transparently.
"""
import logging
import codecs

from bluepy import btle

DEFAULT_TIMEOUT = 1

_LOGGER = logging.getLogger(__name__)


class BTLEConnection(btle.DefaultDelegate):
    """Representation of a BTLE Connection."""

    def __init__(self, mac, iface=None):
        """Initialize the connection."""
        btle.DefaultDelegate.__init__(self)

        self._iface = iface
        self._keep_connected = False
        self._conn = None
        self._mac = mac
        self._callbacks = {}

    def __enter__(self):
        """
        Context manager __enter__ for connecting the device
        :rtype: btle.Peripheral
        :return:
        """
        conn_state = "conn"
        if self._conn:
            # connection active, check if still connected
            try:
                conn_state = self._conn.getState()
            except (btle.BTLEInternalError, btle.BTLEDisconnectError):
                # connection not active, set _conn object to None
                self._conn = None

        if self._conn is None or conn_state != "conn":
            # no active connection, connect now
            self._conn = btle.Peripheral()
            self._conn.withDelegate(self)
            _LOGGER.debug("Trying to connect to %s", self._mac)
            self.connect(self._iface)
            _LOGGER.debug("Connected to %s", self._mac)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn and self._keep_connected is False:
            self._conn.disconnect()
            self._conn = None

    def connect(self, iface):
        self._keep_connected = True
        self._connect(iface)
    
    def _connect(self, iface):
        try:
            self._conn.connect(self._mac, iface=iface)
        except btle.BTLEException as ex:
            _LOGGER.debug("Unable to connect to the device %s using iface %s, retrying: %s", self._mac, iface, ex)
            try:
                self._conn.connect(self._mac, iface=iface)
            except Exception as ex2:
                _LOGGER.debug("Second connection try to %s using ifaces %s failed: %s", self._mac, iface, ex2)
                raise
    
    def disconnect(self):
        self._conn.disconnect()
        self._conn = None

    def handleNotification(self, handle, data):
        """Handle Callback from a Bluetooth (GATT) request."""
        _LOGGER.debug("Got notification from %s: %s", handle, codecs.encode(data, 'hex'))
        if handle in self._callbacks:
            for callback in self._callbacks[handle]:
                callback(data)

    @property
    def mac(self):
        """Return the MAC address of the connected device."""
        return self._mac

    def set_callback(self, handle, function):
        """Set the callback for a Notification handle. It will be called with the parameter data, which is binary."""
        if handle not in self._callbacks:
            self._callbacks[handle] = []
        self._callbacks[handle].append(function)

    def make_request(self, handle, value, timeout=DEFAULT_TIMEOUT, with_response=True):
        """Write a GATT Command without callback - not utf-8."""
        try:
            with self:
                _LOGGER.debug("Writing %s to %s with with_response=%s", codecs.encode(value, 'hex'), handle, with_response)
                self._conn.writeCharacteristic(handle, value, withResponse=with_response)
                if timeout:
                    _LOGGER.debug("Waiting for notifications for %s", timeout)
                    self._conn.waitForNotifications(timeout)
        except btle.BTLEException as ex:
            _LOGGER.debug("Got exception from bluepy while making a request: %s", ex)
            raise
