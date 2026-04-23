#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AGS10 sensor driver for Raspberry Pi using smbus2
Original MicroPython version © 2023 Gavesha Labs
Ported to Python3 (Raspbian) by Dennis
"""

import time
from smbus2 import SMBus

AGS10_I2C_ADDR_DEFAULT = 0x1A  # Default I2C address

class AGS10:
    def __init__(self, busnum=1, address=AGS10_I2C_ADDR_DEFAULT, validate_crc=False):
        self.bus = SMBus(busnum)
        self.address = address
        self._dbuf = [0] * 5
        self._rbuf = [0] * 5
        self._dbuf_read_time = 0
        self._rbuf_read_time = 0
        self._init_time = time.time()
        self._validate = validate_crc
        self._version = [0] * 5

    def _read_version(self):
        self._version = self.bus.read_i2c_block_data(self.address,0x11,5)
        

    def _read_to_dbuf(self):
        if time.time() - self._dbuf_read_time < 2:
            # min 1.5s delay is required between successive resistance reads
            return
        self._dbuf = self.bus.read_i2c_block_data(self.address, 0x00, 5)
        self._dbuf_read_time = time.time()

    def _read_to_rbuf(self):
        if time.time() - self._rbuf_read_time < 2:
            # min 1.5s delay is required between successive resistance reads
            return
        self._rbuf = self.bus.read_i2c_block_data(self.address, 0x20, 5)
        self._rbuf_read_time = time.time()

    @staticmethod
    def _calc_crc8(data):
        crc = 0xFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = ((crc << 1) ^ 0x31) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF
        return crc

    @property
    def version(self):
        self._read_version()
        return self._version

    @property
    def status(self):
        self._read_to_dbuf()
        return self._dbuf[0]

    @property
    def is_ready(self):
        return not (self.status & 0x01)

    @property
    def volatile_organic_compounds_ppb(self):
        self._read_to_dbuf()
        if self._validate and self._calc_crc8(self._dbuf[:4]) != self._dbuf[4]:
            raise AssertionError("CRC mismatch in VOC data")
        return int.from_bytes(self._dbuf[1:4], 'big')

    @property
    def resistance_kohm(self):
        self._read_to_rbuf()
        if self._validate and self._calc_crc8(self._rbuf[:4]) != self._rbuf[4]:
            raise AssertionError("CRC mismatch in resistance data")
        return int.from_bytes(self._rbuf[1:4], 'big') * 0.1

    def set_baseline(self, baseline_value):
        data = list(int(baseline_value*0.1).to_bytes(2, 'big'))
        crc = self._calc_crc8(data + [0x00])
        payload = [0, 0x0C, data[0], data[1], crc]
        self.bus.write_i2c_block_data(self.address, 0x01, bytearray(payload))

    def set_baseline_factorydefault(self):
        payload = [0x00,0x0C,0xFF,0xFF,0x81]
        self.bus.write_i2c_block_data(self.address, 0x01, bytearray(payload))

    def update_address(self, new_addr):
        new_addr_inv = ~new_addr & 0xFF
        buf = [new_addr, new_addr_inv, new_addr, new_addr_inv]
        crc = self._calc_crc8(buf)
        buf = [new_addr, new_addr_inv, new_addr, new_addr_inv, crc]
        self.bus.write_i2c_block_data(self.address, 0x21, bytearray(buf))

    def close(self):
        self.bus.close()
