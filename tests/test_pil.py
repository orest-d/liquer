#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for LiQuer pandas support.
"""
from PIL import Image
from liquer import *
from liquer.query import evaluate, evaluate_and_save
from liquer.parser import encode_token
from liquer.cache import set_cache, FileCache
import os.path
import inspect
import tempfile
from liquer.state import set_var
from liquer.store import set_store, MemoryStore
import importlib


class TestPIL:
    @classmethod
    def setup_class(cls):
        from liquer.commands import reset_command_registry
        import liquer.ext.lq_pil  # register PIL commands and state type
        import liquer.ext.basic   # to get ns

        reset_command_registry()  # prevent double-registration
        # Hack to enforce registering of the commands
        importlib.reload(liquer.ext.basic)
        importlib.reload(liquer.ext.lq_pil)

    @classmethod
    def teardown_class(cls):
        from liquer.commands import reset_command_registry

        reset_command_registry()

    def test_image(self):
        store = MemoryStore()
        set_store(store)

        @first_command
        def image():
            return Image.new(mode="RGB", size=(200, 300))

        assert evaluate("image").get().size == (200,300)
        evaluate_and_save("image/ns-pil/resize-400-600-bilinear/test.png",target_resource_directory="x")
        image = evaluate("x/test.png/-/dr").get()
        assert image.size == (400,600)

