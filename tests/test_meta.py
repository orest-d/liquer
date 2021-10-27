#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for LiQuer meta extension.
"""
import pytest
from liquer.query import evaluate
from liquer.state import set_var


class TestMeta:
    @classmethod
    def setup_class(cls):
        import importlib
        from liquer.commands import reset_command_registry
        import liquer.ext.basic
        import liquer.ext.meta

        reset_command_registry()  # prevent double-registration
        # Hack to enforce registering of the commands
        importlib.reload(liquer.ext.basic)
        importlib.reload(liquer.ext.meta)

    @classmethod
    def teardown_class(cls):
        from liquer.commands import reset_command_registry

        reset_command_registry()

    def test_state(self):
        from liquer.commands import command_registry

        state = evaluate("ns-meta/commands/state").get()
        assert state["query"] == "ns-meta/commands"
