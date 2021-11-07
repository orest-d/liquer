#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for LiQuer State object.
"""
import pytest
from liquer.state import *


class TestState:
    def test_as_dict(self):
        state = State().with_data(123)
        d = state.as_dict()
        assert d["type_identifier"] in ["generic", "pickle"]

    def test_data_characteristics(self):
        for data in [None, True, False, 123, [], [123, 456], {}, {"abc": 123}]:
            state = State().with_data(data)
            d = state.as_dict()
            assert type(d["data_characteristics"]["description"]) == str
            assert d["data_characteristics"]["type_identifier"] == type_identifier_of(data)
