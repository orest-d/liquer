#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for LiQuer metadata.
"""
import pytest
from liquer.metadata import Metadata


class TestMetadata:
    def test_create(self):
        m = Metadata()
        assert "status" in m.as_dict()
