# -*- coding: utf-8 -*-
from gateway import stubs

def test_packetization():
    expected = "\x00\x01\x02\x03"
    result = stubs.packetize("\x00\x01\x02\x03")

    assert(result == expected)

def test_depacketization():
    expected = "\x00\x01\x02\x03"
    result = stubs.depacketize("\x00\x01\x02\x03")

    assert(result == expected)

def test_encryption():
    expected = "\x00\x01\x02\x03"
    result = stubs.encrypt("\x00\x01\x02\x03")

    assert(result == expected)

def test_decryption():
    expected = "\x00\x01\x02\x03"
    result = stubs.decrypt("\x00\x01\x02\x03")

    assert(result == expected)

