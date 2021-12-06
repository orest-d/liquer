import json
from liquer.state_types import (
    type_identifier_of,
    copy_state_data,
    data_characteristics
)
from liquer.constants import mimetype_from_extension

from copy import deepcopy
from liquer.parser import QueryException, Position

_vars = None


class EvaluationException(QueryException):
    pass


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
    def __init__(self, data=None, metadata=None, context=None):
        self.data = data
        self.exception = None
        self.context = context
        self.metadata = (
            metadata
            if metadata is not None
            else dict(
                query="",
                sources=[],
                log=[],
                is_error=False,
                vars=vars_clone(),
                filename=None,
                extension=None,
                message="",
                commands=[],
                extended_commands=[],
                type_identifier=type_identifier_of(data),
                caching=True,
                attributes={},
                data_characteristics=data_characteristics(data)
            )
        )

    def next_state(self):
        state = self.__class__()
        state = state.from_dict(self.as_dict()).with_data(None)
        return state

    @property
    def query(self):
        return self.metadata["query"]

    @query.setter
    def query(self, value):
        self.metadata["query"] = value

    @property
    def is_error(self):
        return self.metadata["is_error"]

    @is_error.setter
    def is_error(self, value):
        self.metadata["is_error"] = value

    @property
    def vars(self):
        return self.metadata["vars"]

    @vars.setter
    def vars(self, value):
        self.metadata["vars"] = value

    @property
    def type_identifier(self):
        return self.metadata["type_identifier"]

    @type_identifier.setter
    def type_identifier(self, value):
        self.metadata["type_identifier"] = value

    #    def with_caching(self, caching=True):
    #        """Enables or disables caching for this state"""
    #        # TODO: Make sure caching is propagated to dependent states
    #        # TODO: Examples and documentation
    #        print(f"QUERY {self.query}\nWITH CACHING {caching}")
    #        if self.context is not None:
    #            self.context.caching = caching
    #            print(f"set context {id(self.context)} caching {self.context.caching}")
    #        self.metadata["caching"] = caching
    #        return self

    def with_data(self, data):
        """Set the data"""
        self.data = data
        self.metadata["type_identifier"] = type_identifier_of(data)
        self.metadata["data_characteristics"] = data_characteristics(data)
        return self

    def with_source(self, source):
        """Add sources to the state"""
        self.metadata["sources"] = [source] + self.metadata["sources"]
        return self

    def is_volatile(self):
        return self.metadata.get("attributes", {}).get("volatile", False)

    def set_volatile(self, flag):
        self.metadata["attributes"]["volatile"] = flag
        return self

    def get(self):
        """Get data from the state"""
        if self.is_error:
            tb = "\n".join(m.get("traceback", "") for m in self.metadata["log"])
            print(tb)
            position = None
            query = None
            for entry in self.metadata["log"]:
                if entry.get("kind") == "error":
                    position = Position.from_dict(entry.get("position"))
                    query = entry.get("query")

            if self.exception is None:
                raise EvaluationException(
                    tb + "\n" + self.metadata["message"], position=position, query=query
                )
            else:
                raise self.exception

        return self.data

    def log_command(self, qv, number):
        """Log a command"""
        if self.context is None:
            self.metadata["log"].append(
                dict(kind="command", qv=qv, command_number=number)
            )
        else:
            self.context.log_action(qv, number)
        return self

    def log_error(self, message):
        """Log an error message"""
        if self.context is None:
            self.metadata["log"].append(dict(kind="error", message=message))
            self.is_error = True
            self.metadata["message"] = message
        else:
            self.context.error(message)
        return self

    def log_warning(self, message):
        """Log a warning message"""
        if self.context is None:
            self.metadata["log"].append(dict(kind="warning", message=message))
            self.metadata["message"] = message
        else:
            self.context.warning(message)
        return self

    def log_exception(self, message, traceback):
        """Log an exception"""
        if self.context is None:
            self.metadata["log"].append(
                dict(kind="error", message=message, traceback=traceback)
            )
            self.is_error = True
            self.metadata["message"] = message
        else:
            self.context.exception(message, traceback)
        return self

    def log_info(self, message):
        """Log a message (info)"""
        if self.context is None:
            self.metadata["log"].append(dict(kind="info", message=message))
            self.metadata["message"] = message
        else:
            self.context.info(message)
        return self

    def as_dict(self):
        """Represent state metadata as a dictionary - suitable for json serialization
        State data is NOT part of the returned dictionary.
        """
        return deepcopy(self.metadata)

    def mimetype(self):
        """Return mime type of the data"""
        
        return self.metadata.get("mimetype", mimetype_from_extension(self.extension))

    def from_dict(self, metadata):
        """Fill state by valueas from a dictionary"""
        if isinstance(metadata, self.__class__):
            metadata = metadata.metadata
        self.metadata = deepcopy(metadata)
        return self

    def has_flag(self, name):
        return self.metadata["vars"].get(name) == True

    def clone(self):
        """Clone the state including the deep copy of the data"""
        state = self.__class__()
        state = state.from_dict(self.as_dict())
        state.data = copy_state_data(self.data)
        return state

    def with_filename(self, filename):
        """set filename"""
        self.metadata["filename"] = filename
        if "." in filename:
            self.metadata["extension"] = filename.split(".")[-1].lower()
        return self
