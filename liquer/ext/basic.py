import io
from urllib.request import urlopen
import base64
from liquer.commands import command, first_command
from liquer.parser import encode, decode
from liquer.state_types import encode_state_data


@command
def let(state, name, value):
    """Set the state variable
    Sets a state variable with 'name' to 'value'.
    """
    state.vars[name] = value
    return state


@command
def flag(state, name, value: bool = True):
    """Set the state variable as a flag (boolean value)
    """
    state.vars[name] = bool(value)
    return state


@command
def state_variable(state, name):
    """Get the state variable value
    Useful mainly for debugging and testing
    """
    return state.with_data(state.vars.get(name))


@command
def link(state, linktype=None, extension=None):
    """Return a link to the result.
    Linktype can be specified as parameter or as a state variable (e.g. Set~linktype~query)
    linktype can be
    - query : just a query from the state - without the last command (Link) if removelast is True
    - dataurl : data URL (base64-encoded)
    - htmlimage : html image element
    - path : absolute url path (without server)
    - url : complete url
    """
    q = state.query
    if linktype in (None, "default"):
        linktype = state.vars.get("linktype", "query")
    if linktype == "query":
        return state.with_data(q)
    elif linktype == "dataurl":
        b, mime, typeid = encode_state_data(state.get(), extension=extension)
        encoded = base64.b64encode(b).decode('ascii')
        return state.with_data(f'data:{mime};base64,{encoded}')
    elif linktype == "htmlimage":
        b, mime, typeid = encode_state_data(state.get(), extension=extension)
        encoded = base64.b64encode(b).decode('ascii')
        return state.with_filename("image.html").with_data(f'<img src="data:{mime};base64,{encoded}"/>')
    elif linktype == 'path':
        return state.with_data(state.vars.get("api_path", "/q/")+q)
    elif linktype == 'url':
        return state.with_data(state.vars.get(
            "server", "http://localhost")+state.vars.get("api_path", "/q/")+q)

    raise Exception(f"Unsupported link type: {linktype}")


@first_command
def fetch(url):
    """Load binary data from URL
    """
    return urlopen(url).read()


@first_command
def fetch_utf8(url):
    """Load text data encoded as utf-8 from URL
    """
    return urlopen(url).read().decode("utf-8")


@command
def filename(state, name):
    """Set filename"""
    return state.with_filename(name)
