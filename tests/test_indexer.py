import pytest
from liquer.indexer import *
from liquer.commands import reset_command_registry, command, first_command
from liquer.context import get_context

class TestIndexer:
    def test_indexer(self):
        reset_command_registry()
        reset_index_registry()

        @first_command
        def hello(x):
            return f"Hello, {x}"

        assert get_context().evaluate("hello-world").get() == "Hello, world"
        assert get_context().evaluate("hello-world").metadata.get("tools") is None

        init_indexer_registry()

        assert get_context().evaluate("hello-world").metadata.get("tools") is not None
