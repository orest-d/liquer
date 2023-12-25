# Make it run from the examples directory
import sys
sys.path.append("..")

from liquer import *
from liquer.app import quickstart

@first_command
def hello():
    return "Hello"

@command
def greet(greeting, who="world"):
    return f"{greeting}, {who}!"

@first_command
def index():
    return """<h1>Hello-world app</h1>
    <ul>
    <li><a href="/liquer/q/hello">just hello</a></li>
    <li><a href="/liquer/q/hello/greet">simple greet</a></li>
    <li><a href="/liquer/q/hello/greet-everybody">greet everybody</a></li>
    <li><a href="/liquer/q/hello/greet?who=everybody">greet everybody by URL parameters</a></li>
    <li><a href="/liquer/web/gui">GUI</a></li>
    </ul>
    """

if __name__ == '__main__':
    quickstart(index_link="/liquer/q/index/index.html")
