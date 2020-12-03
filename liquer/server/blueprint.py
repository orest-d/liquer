import logging
from flask import Blueprint, jsonify, redirect, send_file, request, make_response, abort
from liquer.query import evaluate
from liquer.state_types import encode_state_data, state_types_registry
from liquer.commands import command_registry
from liquer.state import get_vars
from liquer.cache import get_cache
import io
import traceback

app = Blueprint('liquer', __name__, static_folder='static')
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@app.route('/', methods=['GET', 'POST'])
@app.route('/index.html', methods=['GET', 'POST'])
def index():
    """Link to a LiQuer main service page"""
    return redirect("/liquer/static/index.html")


@app.route('/info.html', methods=['GET', 'POST'])
def info():
    """Info page"""
    return """
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


def response(state):
    """Create flask response from a State"""
    filename = state.metadata.get("filename")
    extension = None
    if filename is not None:
        if "." in filename:
            extension = filename.split(".")[-1]
    b, mimetype, type_identifier = encode_state_data(
        state.get(), extension=extension)
    if filename is None:
        filename = state_types_registry().get(type_identifier).default_filename()
    r = make_response(b)
    
    r.headers.set('Content-Type', mimetype)
    if mimetype not in ["application/json",
                        'text/plain',
                        'text/html',
                        'text/csv',
                        'image/png',
                        'image/svg+xml']:
        r.headers.set(
            'Content-Disposition', 'attachment', filename=filename)
    return r


@app.route('/q/<path:query>')
def serve(query):
    """Main service for evaluating queries"""
    return response(evaluate(query))

@app.route("/submit/<path:query>")
def detached_serve(query):
    """Main service for evaluating queries"""
    from liquer.pool import evaluate_in_background
    evaluate_in_background(query)
    return jsonify(dict(status="OK", message="Submitted", query=query))

@app.route('/cache/get/<path:query>')
def cache_get(query):
    """Get cached metadata"""
    state = get_cache().get(query)
    if state is None:
        abort(404)
    return response(state)

@app.route('/cache/meta/<path:query>')
def cache_get_metadata(query):
    """Get cached metadata"""
    metadata = get_cache().get_metadata(query)
    if metadata == False:
        metadata = dict(query = query, status = "not available", cached=False)
    return jsonify(metadata)

@app.route('/cache/meta/<path:query>', methods=["GET", "POST"])
def cache_store_metadata(query):
    """Get cached metadata"""
    metadata = request.get_json(force=True)
    try:
        result_code = get_cache().store_metadata(metadata)
        result = dict(query=query, result=result_code, status = "OK", message="OK", traceback="")
    except Exception as e:
        result = dict(query=query, result=False, status= "ERROR", message=str(e), traceback=traceback.format_exc())

    return jsonify(result)

@app.route('/cache/remove/<path:query>')
def cache_remove(query):
    """interface to cache remove"""
    r = get_cache().remove(query)
    return jsonify(dict(query = query, removed=r))

@app.route('/cache/contains/<path:query>')
def cache_contains(query):
    """interface to cache contains"""
    contains = get_cache().contains(query)
    return jsonify(dict(query = query, cached=contains))

@app.route('/cache/keys.json')
def cache_keys():
    """interface to cache keys"""
    keys = dict(keys=list(get_cache().keys()))
    return jsonify(keys)

@app.route('/cache/clean')
def cache_clean():
    """interface to cache clean"""
    get_cache().clean()
    n=len(list(get_cache().keys()))
    keys = dict(status="OK", message=f"Cache cleaned, {n} keys left")
    return jsonify(keys)

@app.route('/api/commands.json')
def commands():
    """Returns a list of commands in json format"""
    return jsonify(command_registry().as_dict())


@app.route('/api/debug-json/<path:query>')
def debug_json(query):
    """Debug query - returns metadata from a state after a query is evaluated"""
    state = evaluate(query)
    state_json = state.as_dict()
    return jsonify(state_json)


@app.route('/api/build', methods=['POST'])
def build():
    """Build a query from a posted decoded query (list of lists of strings).
    Result is a dictionary with encoded query and link.
    """
    from liquer.parser import encode
    query = encode(request.get_json(force=True)["ql"])
    link = get_vars().get("server", "http://localhost") + \
        get_vars().get("api_path", "/q/") + query
    return jsonify(dict(
        query=query,
        link=link,
        message="OK",
        status="OK")
    )


@app.route('/api/register_command/<data>', methods=['GET'])
def register_command(data):
    """Remote command registration service.
    This has to be enabled by liquer.commands.enable_remote_registration() 

    WARNING: Remote command registration allows to deploy arbitrary python code on LiQuer server,
    therefore it is a HUGE SECURITY RISK and it only should be used if other security measures are taken
    (e.g. on localhost or intranet where only trusted users have access).
    This is on by default on Jupyter server extension.    
    """
    return jsonify(command_registry().register_remote_serialized(data.encode('ascii')))

@app.route('/api/register_command/', methods=['POST'])
def register_command1():
    """Remote command registration service.
    This has to be enabled by liquer.commands.enable_remote_registration() 

    WARNING: Remote command registration allows to deploy arbitrary python code on LiQuer server,
    therefore it is a HUGE SECURITY RISK and it only should be used if other security measures are taken
    (e.g. on localhost or intranet where only trusted users have access).
    This is on by default on Jupyter server extension.    
    """
    data = request.get_data()
    return jsonify(command_registry().register_remote_serialized(data))
