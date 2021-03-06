"""A USB vehicle interface data source."""
from __future__ import absolute_import

import logging
import usb.core

from .base import BytestreamDataSource, DataSourceError

LOG = logging.getLogger(__name__)


class UsbDataSource(BytestreamDataSource):
    """A source to receive data from an OpenXC vehicle interface via USB."""
    DEFAULT_VENDOR_ID = 0x1bc4
    DEFAULT_PRODUCT_ID = 0x0001
    DEFAULT_READ_REQUEST_SIZE = 512
    DEFAULT_READ_TIMEOUT = 1000000

    DEFAULT_INTERFACE_NUMBER = 0
    TRANSLATED_IN_ENDPOINT = 2
    LOG_IN_ENDPOINT = 11

    def __init__(self, callback=None, vendor_id=None, product_id=None,
            log_mode=None):
        """Initialize a connection to the USB device's IN endpoint.

        Kwargs:
            vendor_id (str or int) - optionally override the USB device vendor
                ID we will attempt to connect to, if not using the OpenXC
                hardware.

            product_id (str or int) - optionally override the USB device product
                ID we will attempt to connect to, if not using the OpenXC
                hardware.

            log_mode - optionally record or print logs from the USB device, which
                are on a separate channel.

        Raises:
            DataSourceError if the USB device with the given vendor ID is not
            connected.
        """
        super(UsbDataSource, self).__init__(callback, log_mode)
        if vendor_id is not None and not isinstance(vendor_id, int):
            vendor_id = int(vendor_id, 0)
        self.vendor_id = vendor_id or self.DEFAULT_VENDOR_ID

        if product_id is not None and not isinstance(product_id, int):
            product_id = int(product_id, 0)
        self.product_id = product_id or self.DEFAULT_PRODUCT_ID

        devices = usb.core.find(find_all=True, idVendor=self.vendor_id,
                idProduct=self.product_id)
        for device in devices:
            self.device = device
            try:
                self.device.set_configuration()
            except usb.core.USBError as e:
                LOG.warn("Skipping USB device: %s", e)
            else:
                return

        raise DataSourceError("No USB vehicle interface detected - is one plugged in?")

    def read(self, timeout=None):
        return self._read(self.TRANSLATED_IN_ENDPOINT, timeout)

    def read_logs(self, timeout=None):
        return self._read(self.LOG_IN_ENDPOINT, timeout, 64)

    def _read(self, endpoint_address, timeout=None,
            read_size=DEFAULT_READ_REQUEST_SIZE):
        timeout = timeout or self.DEFAULT_READ_TIMEOUT
        try:
            return self.device.read(0x80 + endpoint_address,
                    read_size, self.DEFAULT_INTERFACE_NUMBER, timeout
                    ).tostring()
        except (usb.core.USBError, AttributeError) as e:
            raise DataSourceError("USB device couldn't be read", e)
