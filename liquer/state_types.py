from io import BytesIO, StringIO
import json
from copy import deepcopy

"""State types represent the additional properties of data types that can be used as a state:
- state type must be representable as a (short) string identifier
- state must be serializable (and deserializable) as bytes
- mime type must be known for a serialized form
State types are registered in a state type registry, where they can be looked up either by
a qualified type name or a state type identifier. (Therefore state type identifiers should be carefully chosen
to not to clash with qualified names. It is encouraged to only use lower case characters as state type identifiers.)

Intended use:
- state can be served via a web service,
- state can be serialized into a file, database or key/value store.

Deserialization requires (besides the byte representation of the data) as well identifier of the state type,
which identifies a registered state type and thus the deserialization method.
Though state type provides a prefered (default) format,
multiple formats may be used for serialization (and deserialization) if needed.
The serialization format is selected by file extension passed to serialization (as_bytes) or deserialization (from_bytes) method.
Since the format determines the mime type, as bytes return besides serialized data as well the actual mime type relevant for the serialization.

Note that for the successful serialization/deserialization strategy (e.g. for caching), the following approaches
can be used:
- use the default extension/format/mimetype - i.e. do not specify the extension or set extension=None in as_bytes/from_bytes
- specify fixed extension 
"""

MIMETYPES = dict(
    json="application/json",
    txt='text/plain',
    html='text/html',
    htm='text/html',
    md='text/markdown',
    xls='application/vnd.ms-excel',
    xlsx='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    ods='application/vnd.oasis.opendocument.spreadsheet',
    tsv='text/tab-separated-values',
    csv='text/csv',
    msgpack='application/x-msgpack',
    hdf5='application/x-hdf',
    h5='application/x-hdf',
    png='image/png',
    svg='image/svg+xml',
    jpg='image/jpeg',
    jpeg='image/jpeg'
)

def mimetype_from_extension(extension):
    return MIMETYPES.get(extension,"text/plain")
    
class StateTypesRegistry(object):
    """State type registry takes care of registering and lookup of state types.
    It is typically accessed as a singleton via state_type_registry() function.

    default_state_type attribute is used if state type is not recognized.
    """

    def __init__(self):
        self.state_types_dictionary = {}
        self.default_state_type = JsonStateType()

    def register(self, type_qualname, state_type):
        """Register a new state type for a qualified type name"""
        self.state_types_dictionary[type_qualname] = state_type
        self.state_types_dictionary[state_type.identifier()] = state_type
        return self

    def get(self, type_qualname):
        """Get state type object for a qualified type name
        If the qualified type name is not recognized, default_state_type is returned.
        """
        return self.state_types_dictionary.get(type_qualname, self.default_state_type)


_state_types_registry = None


def state_types_registry():
    """Returns the global state types registry (singleton)"""
    global _state_types_registry
    if _state_types_registry is None:
        _state_types_registry = StateTypesRegistry()
    return _state_types_registry


def type_identifier_of(data):
    """Convinience function to return a state type identifier for supplied data"""
    return state_types_registry().get(type(data).__qualname__).identifier()


def register_state_type(type_qualname, state_type):
    """Function to register new state type for a qualified type name"""
    state_types_registry().register(type_qualname, state_type)


def encode_state_data(data, extension=None):
    reg = state_types_registry()
    t = reg.get(type(data).__qualname__)
    b, mime = t.as_bytes(data, extension=extension)
    return b, mime, t.identifier()


def decode_state_data(b, type_identifier, extension=None):
    t = state_types_registry().get(type_identifier)
    return t.from_bytes(b, extension=extension)


def copy_state_data(data):
    reg = state_types_registry()
    t = reg.get(type(data).__qualname__)
    return t.copy(data)


class StateType(object):
    def identifier(self):
        raise NotImplementedError(
            "State type class must define a state type identifier")

    def default_extension(self):
        raise NotImplementedError(
            "State type class must define the default extension")

    def default_filename(self):
        return "data."+self.default_extension()

    def default_mimetype(self):
        return MIMETYPES.get(self.default_extension(), "text/plain")

    def is_type_of(self, data):
        return False

    def as_bytes(self, data, extension=None):
        raise NotImplementedError(
            "State type class must define serialization to bytes (as_bytes)")

    def from_bytes(self, b: bytes, extension=None):
        raise NotImplementedError(
            "State type class must define deserialization from bytes (from_bytes)")

    def copy(self, data):
        return self.from_bytes(self.as_bytes(data)[:])


class JsonStateType(StateType):
    def identifier(self):
        return "generic"

    def default_extension(self):
        return "json"

    def is_type_of(self, data):
        return True

    def as_bytes(self, data, extension=None):
        if extension is None:
            extension = self.default_extension()

        assert extension == "json"
        return json.dumps(data).encode("utf-8"), self.default_mimetype()

    def from_bytes(self, b: bytes, extension=None):
        if extension is None:
            extension = self.default_extension()

        assert extension == "json"
        return json.loads(b.decode("utf-8"))

    def copy(self, data):
        return deepcopy(data)
