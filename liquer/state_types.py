from io import BytesIO, StringIO
import json
from copy import deepcopy
import base64
import pickle
from liquer.constants import mimetype_from_extension, MIMETYPES

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

Serialization/deserialization may as well keep being unspecified. In that case, the state the capability
of a state being cached or served is limited.
"""



def get_type_qualname(cls):
    """Get a string uniquely identifying the supplied class"""
    if isinstance(cls, str):
        return cls
    if cls.__module__ == "__main__":
        return cls.__qualname__
    return f"{cls.__module__}.{cls.__qualname__}"


class StateTypesRegistry(object):
    """State type registry takes care of registering and lookup of state types.
    It is typically accessed as a singleton via state_type_registry() function.

    default_state_type attribute is used if state type is not recognized.
    """

    def __init__(self):
        self.state_types_dictionary = {}
        self.register(bytes, BytesStateType())
        self.register(str, TextStateType())
        self.register(dict, DictStateType())
        self.register(type(None), JsonStateType())
        self.register(int, JsonStateType())
        self.register(float, JsonStateType())
        self.default_state_type = PickleStateType()

    def register(self, type_qualname, state_type):
        """Register a new state type for a qualified type name"""
        type_qualname = get_type_qualname(type_qualname)
        self.state_types_dictionary[type_qualname] = state_type
        self.state_types_dictionary[state_type.identifier()] = state_type
        return self

    def get(self, type_qualname):
        """Get state type object for a qualified type name
        If the qualified type name is not recognized, default_state_type is returned.
        """
        if type_qualname is None:
            return self.default_state_type
        type_qualname = get_type_qualname(type_qualname)
        return self.state_types_dictionary.get(type_qualname, self.default_state_type)


_state_types_registry = None


def state_types_registry():
    """Returns the global state types registry (singleton)"""
    global _state_types_registry
    if _state_types_registry is None:
        _state_types_registry = StateTypesRegistry()
    return _state_types_registry


def data_characteristics(data):
    """Convenience function to return data characteristics for supplied data.
    Data characteristics must be a dictionary containing at least a "description"
    element with a string description of the data and a "type_identifier".
    Type identifier is duplicate of the type identifier found in metadata, but makes
    the data characteristics self-contained.
    """
    st = state_types_registry().get(get_type_qualname(type(data))) 
    ch = st.data_characteristics(data)
    if not isinstance(ch, dict):
        raise Exception(f"Data characteristics for {st.identifier()} must be a dictionary")
    ch['description'] = ch.get('description','')
    ch['type_identifier'] = ch.get("type_ident", st.identifier())
    return ch


def type_identifier_of(data):
    """Convenience function to return a state type identifier for supplied data"""
    return state_types_registry().get(get_type_qualname(type(data))).identifier()


def register_state_type(type_qualname, state_type):
    """Function to register new state type for a qualified type name
    type_qualname can be a string (module.ClassName) or a class/type object (not a data instance)
    """
    type_qualname = get_type_qualname(type_qualname)
    state_types_registry().register(type_qualname, state_type)


def encode_state_data(data, extension=None):
    """Helper function to encode state data.
    Extension decides which data format is used for encoding.
    If not supplied, a default extension defined for the state type is used.
    Returns a tuple with binary representation of the data, mime type and state type identifier.
    """
    reg = state_types_registry()
    t = reg.get(get_type_qualname(type(data)))
    b, mime = t.as_bytes(data, extension=extension)
    return b, mime, t.identifier()


def decode_state_data(b, type_identifier, extension=None):
    """Helper function to decode state data.
    Requires binary representation of the state data and state type identifier.
    Extension decides which data format is used for decoding.
    If not supplied, a default extension defined for the state type is used.
    Returns a tuple with binary representation of the data, mime type and state type identifier.
    """
    t = state_types_registry().get(type_identifier)
    return t.from_bytes(b, extension=extension)


def copy_state_data(data):
    """Helper function to get a deep copy of a state data."""
    reg = state_types_registry()
    t = reg.get(get_type_qualname(type(data)))
    return t.copy(data)


class StateType(object):
    """Abstract state type basis"""

    def identifier(self):
        """String identifier of the state type"""
        raise NotImplementedError(
            "State type class must define a state type identifier"
        )

    def default_extension(self):
        """Default file extension; determines the default data format
        Must be consistent with the default_mimetype.
        """
        raise NotImplementedError("State type class must define the default extension")

    def default_filename(self):
        """Default file name"""
        return "data." + self.default_extension()

    def default_mimetype(self):
        """Default mime type - must be consistent with the default_extension"""
        return MIMETYPES.get(self.default_extension(), "text/plain")

    def is_type_of(self, data):
        """Returns true if data is of this state type"""
        return False

    def as_bytes(self, data, extension=None):
        """Serialize data as bytes.
        Data must be of this state type. Extension determines the serialization format. If none, default extension is used.
        """
        raise NotImplementedError(
            "State type class must define serialization to bytes (as_bytes)"
        )

    def from_bytes(self, b: bytes, extension=None):
        """Deserialize data from bytes.
        Data must be a binary representation of this state type.
        Extension determines the serialization format. If none, default extension is used.
        """
        raise NotImplementedError(
            "State type class must define deserialization from bytes (from_bytes)"
        )

    def copy(self, data):
        """Create a deep copy of data.
        Data must be of this state type."""
        return self.from_bytes(self.as_bytes(data)[:])

    def data_characteristics(self, data):
        """Create state-type-dependent data characteristics for supplied data.
        Returned data characteristics must be a dictionary containing at least a "description"
        element with a string description of the data and a "type_identifier".
        Type identifier is duplicate of the type identifier found in metadata, but makes
        the data characteristics self-contained.

        This method should not be called directly, but via the data_characteristics function,
        which might fix and validate some issues.
        """
        return dict(description="")


class DictStateType(StateType):
    """JSON serializable data."""

    def identifier(self):
        return "dictionary"

    def default_extension(self):
        return "djson"

    def is_type_of(self, data):
        return isinstance(data, dict)

    def encode_element(self, data_element):
        if isinstance(data_element, (int, float, str)) or data_element is None:
            return json.dumps(data_element)
        else:
            reg = state_types_registry()
            t = reg.get(get_type_qualname(type(data_element)))
            extension = t.default_extension()
            b, mime = t.as_bytes(data_element, extension=extension)
            txt = base64.b64encode(b).decode("utf-8")
            return '[%-10s, %-4s, "%s"]' % (
                f'"{t.identifier()}"',
                f'"{extension}"',
                txt,
            )

    def decode_element(self, data_element_encoded):
        if isinstance(data_element_encoded, list):
            type_identifier, extension, b64 = data_element_encoded
            b = base64.b64decode(b64)
            return decode_state_data(b, type_identifier, extension)
        else:
            return data_element_encoded

    def as_bytes(self, data, extension=None):
        if extension is None:
            extension = self.default_extension()

        if extension == "djson":
            d = "{\n"
            sep = ""
            for key, value in data.items():
                assert isinstance(key, str)
                d += sep
                d += "%-20s%s" % (f'"{key}":', self.encode_element(value))
                sep = ",\n"
            d += "\n}"
            return d.encode("utf-8"), mimetype_from_extension("djson")
        elif extension == "json":
            return json.dumps(data).encode("utf-8"), mimetype_from_extension("json")

        raise Exception(f"Unsupported file extension: {extension}")

    def from_bytes(self, b: bytes, extension=None):
        if extension is None:
            extension = self.default_extension()
        if extension == "djson":
            d = {}
            for key, value in json.loads(b.decode("utf-8")).items():
                d[key] = self.decode_element(value)
            return d
        elif extension == "json":
            return json.loads(b.decode("utf-8"))

    def copy(self, data):
        return deepcopy(data)

    def data_characteristics(self, data):
        return dict(description=f"Dictionary with {len(data)} items.", keys=sorted(str(k) for k in data.keys()))

class JsonStateType(StateType):
    """JSON serializable data."""

    def identifier(self):
        return "generic"

    def default_extension(self):
        return "json"

    def is_type_of(self, data):
        return True

    def as_bytes(self, data, extension=None):
        if extension is None:
            extension = self.default_extension()

        if extension == "json":
            return json.dumps(data).encode("utf-8"), self.default_mimetype()
        elif extension in ["html", "htm"]:
            if isinstance(data, str):
                return data.encode("utf-8"), mimetype_from_extension("html")
            else:
                return (
                    f"<pre>{json.dumps(data)}</pre>".encode("utf-8"),
                    mimetype_from_extension("html"),
                )
        raise Exception(f"Unsupported file extension: {extension}")

    def from_bytes(self, b: bytes, extension=None):
        if extension is None:
            extension = self.default_extension()

        assert extension == "json"
        return json.loads(b.decode("utf-8"))

    def copy(self, data):
        return deepcopy(data)

    def data_characteristics(self, data):
        if isinstance(data, dict):
            return dict(description=f"Dictionary with {len(data)} items.", keys=sorted(str(k) for k in data.keys()))
        elif isinstance(data, dict):
            return dict(description=f"Array with {len(data)} items.")
        elif isinstance(data, str):
            return dict(description=f"Text {len(data)} characters long.")
        elif isinstance(data, bool):
            return dict(description=f"Bool {data}")
        elif isinstance(data, int):
            return dict(description=f"Integer {data}")
        elif isinstance(data, float):
            return dict(description=f"Float {data}")
        elif data is not None:
            return dict(description=f"None")
        else:
            return dict(description=f"Data of type {type(data)}")


class PickleStateType(StateType):
    """Pickle-serializable data."""

    def identifier(self):
        return "pickle"

    def default_extension(self):
        return "pickle"

    def is_type_of(self, data):
        return True

    def as_bytes(self, data, extension=None):
        if extension is None:
            extension = self.default_extension()

        if extension in ["pkl", "pickle"]:
            return pickle.dumps(data), mimetype_from_extension("pickle")
        elif extension == "json":
            return json.dumps(data).encode("utf-8"), mimetype_from_extension("json")
        elif extension in ["html", "htm"]:
            if isinstance(data, str):
                return data.encode("utf-8"), mimetype_from_extension("html")
            else:
                return (
                    f"<pre>{json.dumps(data)}</pre>".encode("utf-8"),
                    mimetype_from_extension("html"),
                )
        raise Exception(f"Unsupported file extension: {extension}")

    def from_bytes(self, b: bytes, extension=None):
        if extension is None:
            extension = self.default_extension()

        if extension in ["pkl", "pickle"]:
            return pickle.loads(b)
        elif extension == "json":
            return json.loads(b.decode("utf-8"))
        raise Exception(f"Unsupported file extension: {extension}")

    def copy(self, data):
        return deepcopy(data)

    def data_characteristics(self, data):
        if isinstance(data, dict):
            return dict(description=f"Dictionary with {len(data)} items.", keys=sorted(str(k) for k in data.keys()))
        elif isinstance(data, dict):
            return dict(description=f"Array with {len(data)} items.")
        elif isinstance(data, str):
            return dict(description=f"Text {len(data)} characters long.")
        elif isinstance(data, bool):
            return dict(description=f"Bool {data}")
        elif isinstance(data, int):
            return dict(description=f"Integer {data}")
        elif isinstance(data, float):
            return dict(description=f"Float {data}")
        elif data is not None:
            return dict(description=f"None")
        else:
            return dict(description=f"Data of type {type(data)}")

class BytesStateType(StateType):
    """Binary data"""

    def identifier(self):
        return "bytes"

    def default_extension(self):
        return "b"

    def default_mimetype(self):
        return "application/octet-stream"

    def is_type_of(self, data):
        return isinstance(data, bytes)

    def as_bytes(self, data, extension=None):
        return data, mimetype_from_extension(extension)

    def from_bytes(self, b: bytes, extension=None):
        return b

    def copy(self, data):
        return deepcopy(data)

    def data_characteristics(self, data):
        return dict(description=f"{len(data)} bytes")


class TextStateType(StateType):
    """Text data (string)"""

    def identifier(self):
        return "text"

    def default_extension(self):
        return "txt"

    def default_mimetype(self):
        return "text/plain"

    def is_type_of(self, data):
        return isinstance(data, str)

    def as_bytes(self, data, extension=None):
        return data.encode("utf-8"), mimetype_from_extension(extension)

    def from_bytes(self, b: bytes, extension=None):
        return b.decode("utf-8")

    def copy(self, data):
        return data[:]

    def data_characteristics(self, data):
        return dict(description=f"Text {len(data)} characters long.")
