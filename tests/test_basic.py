#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for LiQuer basic extension.
"""
import pytest
from liquer.query import evaluate
from liquer.state import set_var
from liquer.cache import set_cache, NoCache


class TestBasic:
    def test_vars(self):
        set_cache(NoCache())
        import liquer.ext.basic

        assert evaluate("state_variable-abc").get() is None
        assert evaluate("let-abc-1/state_variable-abc").get() == "1"
        assert evaluate("state_variable-abc").get() is None
        set_var("abc", "123")
        assert evaluate("state_variable-abc").get() == "123"
        assert evaluate("let-abc-1/state_variable-abc").get() == "1"

    def test_link(self):
        import liquer.ext.basic

        assert (
            evaluate("let-hello-world/state_variable-hello/link").get()
            == "let-hello-world/state_variable-hello"
        )
        assert (
            evaluate("let-hello-world/state_variable-hello/link-dataurl").get()
            == "data:text/plain;base64,d29ybGQ="
        )

        assert (
            evaluate("let-hello-world/state_variable-hello/link-path").get()
            == "/q/let-hello-world/state_variable-hello"
        )
        assert (
            evaluate("let-hello-world/state_variable-hello/link-url").get()
            == "http://localhost/q/let-hello-world/state_variable-hello"
        )
        set_var("server", "http://localhost:1234")
        set_var("api_path", "/liquer/q/")
        assert (
            evaluate("let-hello-world/state_variable-hello/link-path").get()
            == "/liquer/q/let-hello-world/state_variable-hello"
        )
        assert (
            evaluate("let-hello-world/state_variable-hello/link-url").get()
            == "http://localhost:1234/liquer/q/let-hello-world/state_variable-hello"
        )
        set_var("server", "http://localhost")
        set_var("api_path", "/q/")
