import io
from urllib.request import urlopen
import base64
from liquer.commands import command, first_command
from liquer.parser import encode, decode
from liquer.state_types import encode_state_data
from liquer.cache import get_cache
from liquer.constants import Status, type_identifier_from_extension


@command
def let(state, name, value):
    """Set the state variable
    Sets a state variable with 'name' to 'value'.
    """
    state.vars[name] = value
    return state


@command
def flag(state, name, value: bool = True):
    """Set the state variable as a flag (boolean value)"""
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
        encoded = base64.b64encode(b).decode("ascii")
        return state.with_data(f"data:{mime};base64,{encoded}")
    elif linktype == "htmlimage":
        b, mime, typeid = encode_state_data(state.get(), extension=extension)
        encoded = base64.b64encode(b).decode("ascii")
        return state.with_filename("image.html").with_data(
            f'<img src="data:{mime};base64,{encoded}"/>'
        )
    elif linktype == "path":
        return state.with_data(state.vars.get("api_path", "/q/") + q)
    elif linktype == "url":
        return state.with_data(
            state.vars.get("server", "http://localhost")
            + state.vars.get("api_path", "/q/")
            + q
        )

    raise Exception(f"Unsupported link type: {linktype}")


@command
def html_a(state, linktype=None, value=None, extension=None):
    """Create a html link tag
    If value is None, query is displayed as a value.
    """
    if value is None:
        value = state.query

    lnk = link(state, linktype=linktype, extension=extension)
    return state.with_data(f'<a href="{lnk}">{value}</a>')


@first_command
def fetch(url):
    """Load binary data from URL"""
    return urlopen(url).read()


@first_command
def fetch_utf8(url):
    """Load text data encoded as utf-8 from URL"""
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
    import liquer.parser as lp
    import traceback

    try:
        cache = get_cache()
        data = []
        for key in sorted(cache.keys()):
            metadata = cache.get_metadata(key)
            if metadata is None:
                continue
            progress = metadata.get("progress_indicators", []) + metadata.get(
                "child_progress_indicators", []
            )
            d = dict(
                query=key,
                short=lp.parse(key).short(),
                status=metadata.get("status", "none"),
                updated=metadata.get("updated", "?"),
                message=metadata.get("message", ""),
                progress=progress[:3],
            )
            if include_ready or d["status"] != Status.READY.value:
                data.append((key, d))
        data = [x[1] for x in sorted(data)]
        if reduce and len(data):
            reduced_data = [data[0]]
            for d, next_d in zip(data[1:], data[2:]):
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
        return [
            dict(
                query="",
                status="not available",
                updated="",
                message=traceback.format_exc(),
                progress=[],
            )
        ]


@command
def dr(state, type_identifier=None, extension=None, context=None):
    """Decode resource
    Decodes the bytes into a data structure. This is meant to be used in connection to a resource query.
    Resource part of the query will typically fetch the data from a store and thus return bytes (together with metadata).
    Command dr will convert the bytes (assuming proper metadata are provided) into a data structure.
    The metadata must contain type_identifier in metadata or metadata['resource_metadata'], a filename with extension
    or extension with known decoding.
    """
    from liquer.state_types import state_types_registry
    from liquer.parser import parse

    if state.data is None:
        context.error(
            f"Bytes expected, None received in dr from {state.query}")
        return

    if type_identifier is None:
        type_identifier = state.metadata.get(
            "type_identifier",
            state.metadata.get("resource_metadata", {}).get("type_identifier"),
        )

    if type_identifier in (None, "bytes"):
        type_identifier = state.metadata.get(
            "resource_metadata", {}).get("type_identifier")

    if extension is None:
        extension = state.metadata.get("extension")
    if extension is None:
        query = state.metadata.get("query")
        if query is not None:
            filename = parse(query).filename()
        if filename is not None:
            v = filename.split(".")
            if len(v) > 1:
                extension = v[-1]
                context.info(f"Extension: {extension} - from query '{query}'")
        else:
            key = state.metadata.get("resource_metadata", {}).get("key")
            if key is not None:
                filename = context.store().key_name(key)
            v = filename.split(".")
            if len(v) > 1:
                extension = v[-1]
                context.info(f"Extension: {extension} - from key '{key}'")

    if type_identifier in (None, "bytes"):
        type_identifier = type_identifier_from_extension(extension)
        context.info(
            f"Type identifier: {type_identifier} - from extension '{extension}'")

    if type_identifier is not None:
        if extension in ("parquet", "xlsx", "csv", "tsv") and type_identifier in ("generic", "dictionary", "pickle"):
            context.warning(f"Type identifier '{type_identifier}' seems to be inconsistent with the extension '{extension}'")
            context.warning(f"This might indicate a problem with executing the partent query '{context.parent_query}'")
            type_identifier = type_identifier_by_extension.get(extension)
            context.warning(
                f"To fix the inconsistency, type identifier: {type_identifier} is used from extension '{extension}'")
            
        context.info(
            f"Type identifier: {type_identifier},  Extension: {extension}")
        t = state_types_registry().get(type_identifier)
        data = t.from_bytes(state.data, extension=extension)
        return state.with_data(data)
    else:
        context.error(f"Decode resource (dr) command failed")
        raise Exception(f"Failed to resolve type for query {state.metadata.get('query')}")
    return state
