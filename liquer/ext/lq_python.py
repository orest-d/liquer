from liquer.commands import command, first_command, command_registry
import liquer.ext.basic
import inspect


@first_command(ns="py")
def module_source(module_name):
    "Return source code for the module"
    assert all((c.isalnum() or (c in "._")) for c in module_name)
    exec(f"import {module_name}")
    mod = eval(module_name)
    return inspect.getsource(mod)
