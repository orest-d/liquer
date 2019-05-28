#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Unit tests for LiQuer State object.
'''
import pytest
from liquer.state import *

class TestState:
    def test_as_dict(self):
        state = State().with_data(123)
        d = state.as_dict()
        assert d["type_identifier"] == "generic"