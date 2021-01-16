import io
from urllib.request import urlopen
import base64
from liquer.commands import command, first_command
from liquer.parser import encode, decode
from liquer.state_types import encode_state_data
from liquer.cache import get_cache
from liquer.constants import Status


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

@first_command(volatile=True)
def clean_cache():
    print(f"clean cache {get_cache()}")
    get_cache().clean()
    return "Cache cleaned"

@first_command(volatile=True)
def queries_status(include_ready=False, reduce=True):
    import traceback
    try:
        cache = get_cache()
        data=[]
        for key in sorted(cache.keys()):
            metadata = cache.get_metadata(key)
            if metadata is None:
                continue
            progress = metadata.get("progress_indicators",[]) + metadata.get("child_progress_indicators",[])
            d=dict(
                query=key,
                status=metadata.get("status","none"),
                updated=metadata.get("updated","?"),
                message=metadata.get("message",""),
                progress=progress[:3]
            )
            if include_ready or d["status"]!=Status.READY.value:
                data.append((key,d))
        data = [x[1] for x in sorted(data)]
        if reduce and len(data):
            reduced_data = [data[0]]
            for d, next_d in zip(data[1:],data[2:]):
                previous_d = reduced_data[-1]
                if not (
                    previous_d["status"] == Status.EVALUATING_PARENT.value
                    and d["status"] == Status.EVALUATING_PARENT.value
                    and d["query"].startswith(previous_d["query"])
                    and next_d["query"].startswith(d["query"])
                ):
                    reduced_data.append(d)
            reduced_data.append(data[-1])
            data = reduced_data            
        return data
    except:
        return [dict(
                query="",
                status="not available",
                updated="",
                message=traceback.format_exc(),
                progress=[]
            )]