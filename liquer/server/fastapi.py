"""[FastAPI](https://fastapi.tiangolo.com/) router for LiQuer server"""
from fastapi import APIRouter, Request, HTTPException, status, UploadFile

from liquer.query import evaluate
from liquer.state_types import encode_state_data, state_types_registry
from liquer.commands import command_registry
from liquer.state import get_vars
from liquer.cache import get_cache
from liquer.store import get_store, KeyNotFoundStoreException
import io
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
    UJSONResponse,
)

router = APIRouter()


@router.get("/")
@router.get("/index.html")
async def index():
    """Link to a LiQuer main service page"""
    return RedirectResponse(url="/liquer/static/index.html")


@router.get("/info.html")
def info():
    """Info page"""
    return HTMLResponse(
        content="""
<html>
    <head>
        <title>LiQuer</title>
    </head>
    <body>
        <h1>LiQuer server</h1>
        For more info, see the <a href="https://github.com/orest-d/liquer">repository</a>.
    </body>    
</html>
"""
    )


def response(state):
    """Create flask response from a State"""
    b, mimetype, type_identifier = encode_state_data(
        state.get(), extension=state.extension
    )
    filename = state.metadata.get("filename")
    if filename is None:
        filename = state_types_registry().get(type_identifier).default_filename()
    return Response(content=b, media_type=mimetype)


@router.get("/q/{query:path}")
async def serve(query, request: Request):
    """Main service for evaluating queries"""
    kwargs = {**request.query_params}

    try:
        return response(evaluate(query, extra_parameters=kwargs))
    except:
        traceback.print_exc()
        return Response(status_code=500)


@router.get("/submit/{query:path}")
async def detached_serve(query):
    """Main service for evaluating queries"""
    from liquer.pool import evaluate_in_background

    evaluate_in_background(query)
    return dict(status="OK", message="Submitted", query=query)


@router.get("/api/cache/get/{query:path}")
async def cache_get(query):
    """Get cached data"""
    state = get_cache().get(query)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Item {query} not found in cache")
    return response(state)


@router.get("/api/cache/meta/{query:path}")
async def cache_get_metadata(query: str) -> Response:
    """Get cached metadata"""
    metadata = get_cache().get_metadata(query)
    if metadata == False:
        metadata = dict(query=query, status="not available", cached=False)  # FIXME
    return JSONResponse(content=metadata)


@router.post("/api/cache/meta/{query:path}")
def cache_store_metadata(query, metadata: dict):
    """Store metadata in cache.
    Allows to use liquer server as a remote cache.
    """
    # metadata = request.get_json(force=True)
    try:
        result_code = get_cache().store_metadata(metadata)
        result = dict(
            query=query, result=result_code, status="OK", message="OK", traceback=""
        )
    except Exception as e:
        result = dict(
            query=query,
            result=False,
            status="ERROR",
            message=str(e),
            traceback=traceback.format_exc(),
        )

    return JSONResponse(content=result)


@router.get("/api/cache/remove/{query:path}")
def cache_remove(query):
    """interface to cache remove"""
    r = get_cache().remove(query)
    return JSONResponse(content=dict(query=query, removed=r))


@router.get("/api/cache/contains/{query:path}")
def cache_contains(query):
    """interface to cache contains"""
    contains = get_cache().contains(query)
    return JSONResponse(content=dict(query=query, cached=contains))


@router.get("/api/cache/keys.json")
def cache_keys():
    """interface to cache keys"""
    keys = dict(keys=list(get_cache().keys()))
    return JSONResponse(content=keys)


@router.get("/api/cache/clean")
def cache_clean():
    """interface to cache clean"""
    get_cache().clean()
    n = len(list(get_cache().keys()))
    keys = dict(status="OK", message=f"Cache cleaned, {n} keys left")
    return JSONResponse(content=keys)


@router.get("/api/commands.json")
def commands():
    """Returns a list of commands in json format"""
    return JSONResponse(content=command_registry().as_dict())


@router.get("/api/debug-json/{query:path}")
def debug_json(query):
    """Debug query - returns metadata from a state after a query is evaluated"""
    state = evaluate(query)
    state_json = state.as_dict()
    return JSONResponse(content=state_json)


@router.post("/api/build")
async def build(request: Request):
    """Build a query from a posted decoded query (list of lists of strings).
    Result is a dictionary with encoded query and link.
    """
    from liquer.parser import encode

    json = await request.json()
    query = encode(json["ql"])
    link = (
        get_vars().get("server", "http://localhost")
        + get_vars().get("api_path", "/q/")
        + query
    )
    return JSONResponse(content=dict(query=query, link=link, message="OK", status="OK"))


@router.get("/api/register_command/{data}")
def register_command(data):
    """Remote command registration service.
    This has to be enabled by liquer.commands.enable_remote_registration()

    WARNING: Remote command registration allows to deploy arbitrary python code on LiQuer server,
    therefore it is a HUGE SECURITY RISK and it only should be used if other security measures are taken
    (e.g. on localhost or intranet where only trusted users have access).
    This is on by default on Jupyter server extension.
    """
    return JSONResponse(
        content=command_registry().register_remote_serialized(data.encode("ascii"))
    )


@router.post("/api/register_command/")
async def register_command1(request: Request):
    """Remote command registration service.
    This has to be enabled by liquer.commands.enable_remote_registration()

    WARNING: Remote command registration allows to deploy arbitrary python code on LiQuer server,
    therefore it is a HUGE SECURITY RISK and it only should be used if other security measures are taken
    (e.g. on localhost or intranet where only trusted users have access).
    This is on by default on Jupyter server extension.
    """
    data = await request.body()
    return JSONResponse(content=command_registry().register_remote_serialized(data))


@router.get("/api/store/data/{query:path}")
def store_get(query):
    """Get data from store. Equivalent to Store.get_bytes.
    Content type (MIME) is obtained from the metadata.
    """
    store = get_store()
    try:
        metadata = store.get_metadata(query)
        mimetype = metadata.get("mimetype", "application/octet-stream")
        return Response(content=store.get_bytes(query), media_type=mimetype)
    except:
        return JSONResponse(
            content=dict(query=query, message=traceback.format_exc(), status="ERROR"),
            status_code=404,
        )


@router.get("/web/{query:path}")
def web_store_get(query):
    """Shortcut to the 'web' directory in the store.
    Similar to /store/data/web, except the index.html is automatically added if query is a directory.
    The 'web' directory hosts web applications and visualization tools, e.g. liquer-pcv or liquer-gui.
    """
    store = get_store()
    try:
        query = "web/" + query
        if query.endswith("/"):
            query += "index.html"
        if store.is_dir(query):
            query += "/index.html"
        metadata = store.get_metadata(query)
        mimetype = metadata.get("mimetype", "application/octet-stream")
        return Response(content=store.get_bytes(query), media_type=mimetype)
    except:
        return JSONResponse(
            content=dict(query=query, message=traceback.format_exc(), status="ERROR"),
            status_code=404,
        )


@router.post("/api/store/data/{query:path}")
async def store_set(query, request: Request):
    """Set data in store. Equivalent to Store.store.
    Unlike store method, which stores both data and metadata in one call,
    the api/store/data POST only stores the data. The metadata needs to be set in a separate POST of api/store/metadata
    either before or after the api/store/data POST.
    """
    store = get_store()
    try:
        metadata = store.get_metadata(query)
    except KeyNotFoundStoreException:
        metadata = {}
        traceback.print_exc()
    try:
        data = await request.body()
        store.store(query, data, metadata)
        return JSONResponse(
            content=dict(query=query, message="Data stored", status="OK")
        )
    except:
        return JSONResponse(
            content=dict(query=query, message=traceback.format_exc(), status="ERROR"),
            status_code=404,
        )


@router.get("/api/store/upload/{query:path}")
def store_upload_get(query):
    """Upload data to store - similar to /api/store/data, but using upload. Equivalent to Store.store.
    Unlike store method, which stores both data and metadata in one call,
    the api/store/data POST only stores the data. The metadata needs to be set in a separate POST of api/store/metadata
    either before or after the api/store/data POST.
    """

    return HTMLResponse(
        content=f"""
    <!doctype html>
    <title>Upload File</title>
    <h1>Upload to {query}</h1>
    <form method="post" enctype="multipart/form-data">
      <input type="file" name="file"/>
      <input type="submit" value="Upload"/>
    </form>
    """
    )


@router.post("/api/store/upload/{query:path}")
async def store_upload_post(query, f: UploadFile):
    """Upload data to store - similar to /api/store/data, but using upload. Equivalent to Store.store.
    Unlike store method, which stores both data and metadata in one call,
    the api/store/data POST only stores the data. The metadata needs to be set in a separate POST of api/store/metadata
    either before or after the api/store/data POST.
    """

    if f.filename in ("", None):
        response = JSONResponse(
            content=dict(
                query=query,
                message="Request contains 'file' with an empty filename",
                status="ERROR",
            ),
            status_code=404,
        )
        return response

    try:
        data = await f.file.read()
    except:
        response = JSONResponse(
            content=dict(query=query, message=traceback.format_exc(), status="ERROR"),
            status_code=404,
        )
        return response
    store = get_store()
    try:
        metadata = store.get_metadata(query)
    except KeyNotFoundStoreException:
        metadata = {}
        traceback.print_exc()
    try:
        store.store(query, data, metadata)
        return JSONResponse(
            content=dict(
                query=query, message="Data stored", size=len(data), status="OK"
            )
        )
    except:
        response = JSONResponse(
            content=dict(query=query, message=traceback.format_exc(), status="ERROR"),
            status_code=404,
        )
        return response


@router.get("/api/store/metadata/{query:path}")
def store_get_metadata(query):
    store = get_store()
    metadata = store.get_metadata(query)
    return JSONResponse(content=metadata)


@router.post("/api/store/metadata/{query:path}")
async def store_set_metadata(query, request: Request):
    store = get_store()
    try:
        metadata = await request.json()
        store.store_metadata(query, metadata)

        return JSONResponse(
            content=dict(query=query, message="Metadata stored", status="OK")
        )
    except:
        response = JSONResponse(
            content=dict(query=query, message=traceback.format_exc(), status="ERROR"),
            status_code=404,
        )
        return response


@router.get("/api/stored_metadata/{query:path}")
def get_stored_metadata(query):
    """Get metadata stored in a store or cache"""
    import liquer.tools

    metadata = liquer.tools.get_stored_metadata(query)
    return JSONResponse(content=metadata)


@router.get("/api/store/remove/{query:path}")
def store_remove(query):
    """Remove file from the store"""
    store = get_store()
    try:
        store.remove(query)
        return JSONResponse(
            content=dict(query=query, message=f"Removed {query}", status="OK")
        )
    except:
        return JSONResponse(
            content=dict(query=query, message=traceback.format_exc(), status="ERROR")
        )


@router.get("/api/store/removedir/{query:path}")
def store_removedir(query):
    """Remove directory from the store"""
    store = get_store()
    try:
        store.removedir(query)
        return JSONResponse(
            content=dict(query=query, message=f"Removed directory {query}", status="OK")
        )
    except:
        return JSONResponse(
            content=dict(query=query, message=traceback.format_exc(), status="ERROR")
        )


@router.get("/api/store/contains/{query:path}")
def store_contains(query):
    """Check if the store contains a file"""
    store = get_store()
    try:
        contains = store.contains(query)
        return JSONResponse(
            content=dict(
                query=query, message=f"Contains {query}", contains=contains, status="OK"
            )
        )
    except:
        return JSONResponse(
            content=dict(query=query, message=traceback.format_exc(), status="ERROR")
        )


@router.get("/api/store/is_dir/{query:path}")
def store_is_dir(query):
    store = get_store()
    try:
        is_dir = store.is_dir(query)
        return JSONResponse(
            content=dict(
                query=query, message=f"Is directory {query}", is_dir=is_dir, status="OK"
            )
        )
    except:
        return JSONResponse(
            content=dict(query=query, message=traceback.format_exc(), status="ERROR")
        )


@router.get("/api/store/keys")
def store_keys():
    store = get_store()
    try:
        keys = store.keys()
        return JSONResponse(
            content=dict(query=None, message=f"Keys obtained", keys=keys, status="OK")
        )
    except:
        return JSONResponse(
            content=dict(query=None, message=traceback.format_exc(), status="ERROR")
        )


@router.get("/api/store/listdir/{query:path}")
def store_listdir(query):
    store = get_store()
    try:
        listdir = store.listdir(query)
        return JSONResponse(
            content=dict(
                query=query, message=f"Keys obtained", listdir=listdir, status="OK"
            )
        )
    except:
        return JSONResponse(
            content=dict(query=query, message=traceback.format_exc(), status="ERROR")
        )


@router.get("/api/store/makedir/{query:path}")
def store_makedir(query):
    store = get_store()
    try:
        store.makedir(query)
        return JSONResponse(
            content=dict(query=query, message=f"Makedir succeeded", status="OK")
        )
    except:
        return JSONResponse(
            content=dict(query=query, message=traceback.format_exc(), status="ERROR")
        )
