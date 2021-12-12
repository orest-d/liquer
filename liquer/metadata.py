from liquer.constants import Status
from liquer.util import timestamp
from copy import deepcopy

class Metadata:
    """Metadata wrapper"""

    def __init__(self, metadata={}):
        self.set_metadata(metadata)

    def set_metadata(self, metadata):
        if "log" not in metadata:
            metadata["log"] = []
        if "query" not in metadata:
            metadata["query"] = None
        if "status" not in metadata:
            metadata["status"] = Status.NONE.value
        if "is_error" not in metadata:
            metadata["is_error"] = False
        self.metadata = metadata
        return self

    @property
    def query(self):
        return self.metadata["query"]

    @query.setter
    def query(self, value):
        self.metadata["query"] = value

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

    def log_dict(self, d):
        "Put dictionary with a log entry into the log"
        d["timestamp"] = timestamp()
        self.log.append(d)
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
