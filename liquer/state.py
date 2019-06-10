from flask import jsonify, Response, send_file
import pandas as pd
from io import BytesIO, StringIO
import json
from liquer.state_types import type_identifier_of, copy_state_data
from copy import deepcopy

_vars = None


def get_vars():
    global _vars
    if _vars is None:
        _vars = {}
    return _vars


def vars_clone():
    """Return a copy of state variables dictionary
    This is used to set the initial content of State.vars for a newly created state.
    """
    return deepcopy(get_vars())


def set_var(name, value):
    """Set initial value of a state variable
    This is used to configure initial content of the state variables.

    It should be done before any query is evaluated.
    Calls at a later stage may lead to unintended behaviour like
    cache inconsistencies (query result may depend on initial value of a state variable,
    but this is not reflected in a query string).
    """
    get_vars()
    _vars[name] = value


class State(object):
    def __init__(self):
        self.query = ""
        self.sources = []
        self.log = []
        self.is_error = False
        self.vars = vars_clone()

        self.filename = None
        self.extension = None
        self.data = None
        self.message = ""
        self.commands = []
        self.type_identifier = None
        self.caching = True

    def with_caching(self, caching=True):
        self.caching = caching
        return self

    def with_data(self, data):
        self.data = data
        self.type_identifier = type_identifier_of(data)
        return self

    def with_source(self, source):
        self.sources = [source] + self.sources
        return self

    def get(self):
        if self.is_error:
            print("\n".join(m.get("traceback", "") for m in self.log))
            raise Exception(self.message)
        return self.data

    def log_command(self, qv, number):
        self.log.append(dict(kind="command", qv=qv, command_number=number))
        return self

    def log_error(self, message):
        self.log.append(
            dict(kind="error", message=message))
        self.is_error = True
        self.message = message
        return self

    def log_warning(self, message):
        self.log.append(dict(kind="warning", message=message))
        self.message = message
        return self

    def log_exception(self, message, traceback):
        self.log.append(dict(kind="error",
                             message=message, traceback=traceback))
        self.is_error = True
        self.message = message
        return self

    def log_info(self, message):
        self.log.append(dict(kind="info", message=message))
        self.message = message
        return self

    def as_dict(self):
        return dict(
            query=self.query,
            type_identifier=self.type_identifier,
            sources=self.sources,
            filename=self.filename,
            extension=self.extension,
            log=self.log,
            is_error=self.is_error,
            message=self.message,
            commands=self.commands,
            vars=dict(**self.vars)
        )

    def mimetype(self):
        return self.MIMETYPES.get(self.extension)

    def from_dict(self, state):
        if isinstance(state, self.__class__):
            state = state.__dict__
        self.query = state["query"]
        self.type_identifier = state["type_identifier"]
        self.sources = state["sources"]
        self.filename = state["filename"]
        self.extension = state["extension"]
        self.log = state["log"]
        self.is_error = state["is_error"]
        self.message = state["message"]
        self.commands = state["commands"]
        self.vars = state["vars"]
        return self

    def has_flag(self, name):
        return self.vars.get(name) == True

    def clone(self):
        state = self.__class__()
        state = state.from_dict(self.as_dict())
        state.data = copy_state_data(self.data)
        return state

    def add_source(self, source):
        if source not in self.sources:
            self.sources.append(source)
        return self

    def with_filename(self, filename):
        self.filename = filename
        if "." in filename:
            self.extension = filename.split(".")[-1].lower()
        return self
