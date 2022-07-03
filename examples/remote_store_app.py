# Example/test of a GUI

# Make it run from the examples directory
import sys
sys.path.append("..")

import liquer.server.blueprint as bp
import webbrowser
from flask import Flask, make_response, redirect
from liquer import *
from liquer.context import *
from liquer.store import mount, MemoryStore # MemoryStore is used in server mode
from liquer.remote_store import RemoteStore # RemoteStore connects to the server store
import liquer.ext.basic
import liquer.ext.meta
import liquer.ext.lq_pandas

try:                                        # Optionally enable Liquer GUI
    import liquer_gui
    GUI_AVAILABLE=True
except:
    GUI_AVAILABLE=False

app = Flask(__name__)
url_prefix='/liquer'
app.register_blueprint(bp.app, url_prefix=url_prefix)
 

@app.route('/', methods=['GET', 'POST'])
@app.route('/index.html', methods=['GET', 'POST'])
def index():
    """Link to a LiQuer main service page"""
    
    return f"""<html>
    <body>
        <h1>LiQuer remote store access demo</h1>
        <a href="/liquer/q/create_hello/message.txt">Create</a> - 
        <a href="/liquer/q/create_hello-LiQuer/message.txt">Create 2</a> - 
        <a href="/liquer/q/remove_hello/message.txt">Remove</a> -
        <a href="/liquer/q/show_hello/message.txt">Show</a>
    </body>
</html>
    """

def hello_key(context):
    if context.store().is_dir("remote"): # Remote store is mounted in "remote"
        return "remote/data/hello.txt"
    else:
        return "data/hello.txt"

@first_command
def create_hello(greet="world", context=None):
    context = get_context(context)
    key = hello_key(context)
    context.info(f"Store under {key}")
    text=f"Hello, {greet}!"

    context.store().store(key, text.encode("utf-8"), {})

    return f"Created '{text}' in {key}"

@first_command
def remove_hello(greet="world", context=None):
    context = get_context(context)
    key = hello_key(context)
    context.info(f"Remove {key}")
    context.store().remove(key)
    return "Removed " + key

@first_command
def show_hello(greet="world", context=None):
    context = get_context(context)
    key = hello_key(context)
    context.info(f"Show {key}")
    b = context.store().get_bytes(key)
    return f"Content of {key}: {repr(b)}"

SERVER_PORT = 8080
CLIENT_PORT = 8081

if __name__ == '__main__':
    import sys
    if len(sys.argv)<=1 or sys.argv[1] not in ("client", "server"):
        print (f"{sys.argv[0]} [client|server]")
        print (f"Server port is {SERVER_PORT}")
        print (f"Client port is {CLIENT_PORT}")
    else:
        if sys.argv[1] == 'server':
            mount("data", MemoryStore())
            webbrowser.open(f"http://localhost:{SERVER_PORT}")
            app.run(debug=True,threaded=False, port=SERVER_PORT)
        elif sys.argv[1] == 'client':
            mount("remote", RemoteStore(f"http://localhost:{SERVER_PORT}/liquer/api/"))
            webbrowser.open(f"http://localhost:{CLIENT_PORT}")
            app.run(debug=True,threaded=False, port=CLIENT_PORT)
        