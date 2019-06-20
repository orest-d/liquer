import logging
from flask import Blueprint, jsonify, redirect, send_file, request, make_response
from liquer.query import evaluate
from liquer.state_types import encode_state_data, state_types_registry
from liquer.commands import command_registry
from liquer.state import get_vars
import io

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
    filename = state.filename
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
