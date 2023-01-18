import pytest
from liquer.template import *


class TestTemplate:
    def test_simple_template(self):
        assert expand_simple("Hello, $$who$!", dict(who="world")) == "Hello, world!"
