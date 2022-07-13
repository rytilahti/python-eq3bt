"""
Bleak connection backend.
This creates a new event loop that is used to integrate bleak's
asyncio functions to synchronous architecture of python-eq3bt.
"""
import asyncio
import codecs
import contextlib
import logging
from typing import Optional

from bleak import BleakClient, BleakError

from . import BackendException

DEFAULT_TIMEOUT = 1

# bleak backends are very loud on debug, this reduces the log spam when using --debug
logging.getLogger("bleak.backends").setLevel(logging.WARNING)

_LOGGER = logging.getLogger(__name__)


class BleakConnection:
    """Representation of a BTLE Connection."""

    def __init__(self, mac, iface):
        """Initialize the connection."""

        self._conn: Optional[BleakClient] = None
        self._mac = mac
        self._iface = iface
        self._callbacks = {}
        self._notifyevent = asyncio.Event()
        self._notification_handle = None
        self._loop = asyncio.new_event_loop()

    def __enter__(self):
        """
        Context manager __enter__ for connecting the device
        :rtype: BTLEConnection
        :return:
        """
        _LOGGER.debug("Trying to connect to %s", self._mac)

        kwargs = {}
        if self._iface is not None:
            kwargs["adapter"] = self._iface
        self._conn = BleakClient(self._mac, **kwargs)
        try:
            self._loop.run_until_complete(self._conn.connect())
        except BleakError as ex:
            _LOGGER.debug(
                "Unable to connect to the device %s, retrying: %s", self._mac, ex
            )
            try:
                self._loop.run_until_complete(self._conn.connect())
            except Exception as ex2:
                _LOGGER.debug("Second connection try to %s failed: %s", self._mac, ex2)
                raise BackendException(
                    "unable to connect to device using bleak"
                ) from ex2

        # The notification handles are off-by-one compared to gattlib and bluepy
        self._loop.run_until_complete(
            self._conn.start_notify(self._notification_handle - 1, self.on_notification)
        )
        _LOGGER.debug("Connected to %s", self._mac)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn:
            self._loop.run_until_complete(self._conn.disconnect())
            self._conn = None

    async def on_notification(self, handle, data):
        """Handle Callback from a Bluetooth (GATT) request."""
        # The notification handles are off-by-one compared to gattlib and bluepy
        handle = handle + 1
        _LOGGER.debug(
            "Got notification from %s: %s", handle, codecs.encode(data, "hex")
        )
        self._notifyevent.set()

        if handle in self._callbacks:
            self._callbacks[handle](data)

    @property
    def mac(self):
        """Return the MAC address of the connected device."""
        return self._mac

    def set_callback(self, handle, function):
        """Set the callback for a Notification handle. It will be called with the parameter data, which is binary."""
        self._notification_handle = handle
        self._callbacks[handle] = function

    async def wait_for_response(self, timeout):
        with contextlib.suppress(asyncio.TimeoutError):
            await asyncio.wait_for(self._notifyevent.wait(), timeout)

    def make_request(self, handle, value, timeout=DEFAULT_TIMEOUT, with_response=True):
        """Write a GATT Command without callback - not utf-8."""
        try:
            with self:
                _LOGGER.debug(
                    "Writing %s to %s",
                    codecs.encode(value, "hex"),
                    handle,
                )
                self._notifyevent.clear()

                self._loop.run_until_complete(
                    self._conn.write_gatt_char(handle - 1, value)
                )
                if timeout:
                    _LOGGER.debug("Waiting for notifications for %s", timeout)
                    self._loop.run_until_complete(self.wait_for_response(timeout))

        except BleakError as ex:
            _LOGGER.debug("Got exception from bleak while making a request: %s", ex)
            raise BackendException("Exception on write using bleak") from ex
