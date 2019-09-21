import json
from liquer.state_types import type_identifier_of, copy_state_data, mimetype_from_extension
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
        self.exception = None
        self.attributes = {}

    def with_caching(self, caching=True):
        """Enables or disables caching for this state"""
        # TODO: Make sure caching is propagated to dependent states
        # TODO: Examples and documentation
        self.caching = caching
        return self

    def with_data(self, data):
        """Set the data"""
        self.data = data
        self.type_identifier = type_identifier_of(data)
        return self

    def with_source(self, source):
        """Add sources to the state"""
        self.sources = [source] + self.sources
        return self

    def is_volatile(self):
        return self.attributes.get("volatile",False)
        
    def get(self):
        """Get data from the state"""
        if self.is_error:
            print("\n".join(m.get("traceback", "") for m in self.log))
            if self.exception is None:
                raise Exception(self.message)
            else:
                raise self.exception

        return self.data

    def log_command(self, qv, number):
        """Log a command"""
        self.log.append(dict(kind="command", qv=qv, command_number=number))
        return self

    def log_error(self, message):
        """Log an error message"""
        self.log.append(
            dict(kind="error", message=message))
        self.is_error = True
        self.message = message
        return self

    def log_warning(self, message):
        """Log a warning message"""
        self.log.append(dict(kind="warning", message=message))
        self.message = message
        return self

    def log_exception(self, message, traceback):
        """Log an exception"""
        self.log.append(dict(kind="error",
                             message=message, traceback=traceback))
        self.is_error = True
        self.message = message
        return self

    def log_info(self, message):
        """Log a message (info)"""
        self.log.append(dict(kind="info", message=message))
        self.message = message
        return self

    def as_dict(self):
        """Represent state metadata as a dictionary - suitable for json serialization
        State data is NOT part of the returned dictionary.
        """
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
            vars=dict(**self.vars),
            attributes=self.attributes
        )

    def mimetype(self):
        """Return mime type of the data"""
        return mimetype_from_extension(self.extension)

    def from_dict(self, state):
        """Fill state by valueas from a dictionary"""
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
        self.attributes = state["attributes"]
        return self

    def has_flag(self, name):
        return self.vars.get(name) == True

    def clone(self):
        """Clone the state including the deep copy of the data"""
        state = self.__class__()
        state = state.from_dict(self.as_dict())
        state.data = copy_state_data(self.data)
        return state

    def with_filename(self, filename):
        """set filename"""
        self.filename = filename
        if "." in filename:
            self.extension = filename.split(".")[-1].lower()
        return self
