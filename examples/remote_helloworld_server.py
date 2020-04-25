# Make it run from the examples directory
import sys
sys.path.append("..")

from liquer import *

### Create Flask app and register LiQuer blueprint
from flask import Flask
import liquer.blueprint as bp
import liquer.commands

liquer.commands.enable_remote_registration()

app = Flask(__name__)
app.register_blueprint(bp.app, url_prefix='/liquer')

@first_command
def hi():
    return "Hi"

@command
def greet(greeting, who="world"):
    return f"{greeting}, {who}!"

@app.route('/')
@app.route('/index.html')
def index():

    result = """<h1>Hello-world servcer app with command registration enabled</h1>
    <h2>Commands registered directly by the server</h2>
    <ul>
    <li><a href="/liquer/q/hi">just hi</a></li>
    <li><a href="/liquer/q/hi/greet">simple greet</a></li>
    <li><a href="/liquer/q/hi/greet-everybody">greet everybody</a></li>
    </ul>
    """

    registered_commands = liquer.commands.command_registry().as_dict().get("root",{}).keys() 
    if "hello" in registered_commands:
        result += """
    <h2>Command hello registered remotely</h2>
    Now you can now run these:
    <ul>
    <li><a href="/liquer/q/hello">just hello</a></li>
    <li><a href="/liquer/q/hello/greet">simple greet</a></li>
    <li><a href="/liquer/q/hello/greet-everybody">greet everybody</a></li>
    </ul>
    """
    else:
        result += """
    <h2>Command hello not registered</h2>
    Please run <em>remote_helloworld_client.py</em> to register <em>hello</em> command. 
    """
    result += """
    <h2>Registered commands</h2>
    """+(", ".join(registered_commands))

    return result

if __name__ == '__main__':
    app.run()
