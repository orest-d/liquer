#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Unit tests for LiQuer meta extension.
'''
import pytest
from liquer.query import evaluate
from liquer.state import set_var


class TestMeta:
    def test_state(self):
        import liquer.ext.meta
        state = evaluate("ns-meta/commands/state").get() 
        assert state["query"] == "ns-meta/commands"
