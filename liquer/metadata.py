from liquer.constants import Status
from liquer.util import timestamp
from liquer.dependencies import Dependencies
from copy import deepcopy
import json


class Metadata:
    """Metadata wrapper
    Highlevel getters/setters and validation on top of a metadata dictionary object.
    Metadata dictionary is a simple JSON-able python dictionary.
    The Metadata class takes care that all required fields are filled in in the right format.
    High-level logging functionality into the metadata is provided as well. 
    """

    def __init__(self, metadata=None):
        if metadata is None:
            metadata={}
        self.set_metadata(metadata)

    @classmethod
    def from_string(cls, string):
        return cls(json.loads(string))

    def set_metadata(self, metadata):
        """Fills the missing fields and sets the metadata from a dictionary"""
        if "log" not in metadata:
            metadata["log"] = []
        if "child_log" not in metadata:
            metadata["child_log"] = []
        if "query" not in metadata:
            metadata["query"] = None
        if "status" not in metadata:
            metadata["status"] = Status.NONE.value
        if "type_identifier" not in metadata:
            metadata["type_identifier"] = None
        if "message" not in metadata:
            metadata["message"] = ""
        if "is_error" not in metadata:
            metadata["is_error"] = False
        metadata["dependencies"] = Dependencies(metadata.get("dependencies",dict(query=metadata["query"]))).as_dict()
        self.metadata = metadata
        return self

    def get(self, key, default=None):
        return self.metadata.get(key, default)

    @property
    def query(self):
        return self.metadata["query"]

    @query.setter
    def query(self, value):
        self.metadata["query"] = value
        self.metadata["dependencies"]["query"] = value

    @property
    def key(self):
        return self.metadata.get("key")

    @key.setter
    def key(self, value):
        self.metadata["key"] = value

    @property
    def status(self):
        return self.metadata["status"]

    @status.setter
    def status(self, value):
        if isinstance(value, Status):
            value = value.value
        self.metadata["status"] = value
        if value == Status.ERROR.value:
            self.metadata["is_error"] = True

    @property
    def type_identifier(self):
        return self.metadata["type_identifier"]

    @type_identifier.setter
    def type_identifier(self, value):
        self.metadata["type_identifier"] = value

    @property
    def message(self):
        return self.metadata["message"]

    @message.setter
    def message(self, value):
        self.metadata["message"] = value

    @property
    def is_error(self):
        return self.metadata["is_error"]

    @query.setter
    def is_error(self, value):
        value = bool(value)
        self.metadata["is_error"] = value
        if value:
            self.metadata["status"] = Status.ERROR.value

    @property
    def log(self):
        return self.metadata["log"]

    def as_dict(self):
        """Represent metadata as a dictionary - suitable for json serialization
        State data is NOT part of the returned dictionary.
        """
        return deepcopy(self.metadata)

    def add_command_dependency(self, ns, command_metadata, detect_collisions=True):
        dependencies = Dependencies(self.metadata["dependencies"])
        dependencies.add_command_dependency(ns, command_metadata, detect_collisions)
        self.metadata["dependencies"]=dependencies.as_dict()
        return self

    def log_dict(self, d):
        "Put dictionary with a log entry into the log"
        d["timestamp"] = timestamp()
        self.log.append(d)
        if "message" in d:
            self.message = d["message"]
        return self

    def error(self, message, position=None, query=None):
        """Log an error message"""
        self.status = Status.ERROR
        return self.log_dict(
            dict(
                kind="error",
                message=message,
                position=None if position is None else position.to_dict(),
                query=query,
            )
        )

    def warning(self, message, traceback=None):
        """Log a warning message"""
        return self.log_dict(dict(kind="warning", message=message, traceback=traceback))

    def exception(self, message, traceback, position=None, query=None):
        """Log an exception"""
        self.status = Status.ERROR
        return self.log_dict(
            dict(
                kind="error",
                message=message,
                traceback=traceback,
                position=None if position is None else position.to_dict(),
                query=query,
            )
        )

    def info(self, message):
        """Log a message (info)"""
        self.log_dict(dict(kind="info", message=message))
        return self

    def debug(self, message):
        """Log a message (debug)"""
        self.log_dict(dict(kind="debug", message=message))
        return self
