# Make it run from the examples directory
import sys
sys.path.append("..")

from flask import Flask
import liquer.blueprint as bp # This is the LiQuer blueprint containing the liquer web service 

from liquer import *

@first_command
def hello():
    return "Hello"

@command
def greet(greeting, who="world"):
    return f"{greeting}, {who}!"

app = Flask(__name__)
url_prefix='/liquer'
app.register_blueprint(bp.app, url_prefix=url_prefix)

@app.route('/')
@app.route('/index.html')
def index():
    return """<h1>Hello-world app</h1>
    <ul>
    <li><a href="/liquer/q/hello">just hello</a></li>
    <li><a href="/liquer/q/hello/greet">simple greet</a></li>
    <li><a href="/liquer/q/hello/greet-everybody">greet everybody</a></li>
    </ul>
    """

if __name__ == '__main__':
    app.run(debug=True,threaded=False)
