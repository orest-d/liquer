#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Unit tests for LiQuer execution context.
'''
import pytest
from liquer.context import *
from liquer.parser import ActionRequest
from liquer.state import State
from liquer.commands import reset_command_registry, command


class TestContext:
    def test_evaluate_action(self):
        reset_command_registry()
        @command
        def test_callable(state, a: int, b=123):  # has state as a first argument
            return a+b
        context = Context()
        action = ActionRequest.from_arguments("test_callable", "1")
        result = context.evaluate_action(State(), action)
        assert result.get() == 124
        assert result.metadata["commands"][-1] == 'action test_callable-1 at (unknown position)'

