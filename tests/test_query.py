#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Unit tests for LiQuer State object.
'''
import pytest
from liquer.query import *
from liquer.commands import command, first_command

class TestQuery:
    def test_evaluate(self):
        @first_command
        def abc():
            return 123
        assert evaluate("abc").get() == 123