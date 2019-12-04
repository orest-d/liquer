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

@command
def html_a(state, linktype=None, value=None, extension=None):
    """Create a html link tag
    If value is None, query is displayed as a value.
    """
    if value is None:
        value = state.query

    lnk = link(state,linktype=linktype, extension=extension)
    return state.with_data(f'<a href="{lnk}">{value}</a>')


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

@command
def ns(state, *namespaces):
    """Set command namespaces to be included

    By default only the root namespace is enabled. The 'ns' command enables commands present in specified namespaces.
    This works by setting "active_namespaces" state variable.
    The "root" namespace is appended to the active_namespaces if not already present.    
    When command is executed, all the active namespaces are searched one by one until the command is found.
    Note that order of active_namespaces is significant. 
    """
    namespaces = list(namespaces)
    if "root" not in namespaces:
        namespaces.append("root")
    state.vars["active_namespaces"] = namespaces
    
    return state
