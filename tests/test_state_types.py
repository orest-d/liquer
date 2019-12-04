#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Unit tests for LiQuer State object.
'''
import pytest
from liquer.state_types import *

class SomeClass:
    def __init__(self,value):
        self.value=value
    def test(self): return self.value

class TestStateTypes:
    def test_generic_type(self):
        for data in [None, True, False, 123, [], [123,456]]:
            assert type_identifier_of(data) in ["generic", "pickle"]

    def test_dictionary_type(self):
        for data in [{}, {"abc":123}]:
            assert type_identifier_of(data) == "dictionary"

    def test_generic_encode_decode(self):
        for data in [None, True, False, 123, [], [123,456], {}, {"abc":123}]:
            encoded, mime, type_identifier = encode_state_data(data)
            assert type_identifier_of(data) == type_identifier
            decoded = decode_state_data(encoded, type_identifier)
            assert data == decoded

    def test_class_encode_decode(self):
        data = SomeClass(123)
        encoded, mime, type_identifier = encode_state_data(data)
        assert type_identifier_of(data) == type_identifier
        decoded = decode_state_data(encoded, type_identifier)
        assert data.test() == 123
        assert decoded.test() == 123

    def test_text_encode_decode(self):
        for data in ["", "Hello"]:
            encoded, mime, type_identifier = encode_state_data(data)
            assert type_identifier_of(data) == type_identifier == "text"
            assert mime == "text/plain"
            assert encoded == data.encode("utf-8")
            decoded = decode_state_data(encoded, type_identifier)
            assert data == decoded

    def test_copy(self):
        for data in [None, True, False, 123, [], [123,456], {}, {"abc":123}]:
            assert data == copy_state_data(data)
