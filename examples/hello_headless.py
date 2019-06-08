# Make it run from the examples directory
import sys
sys.path.append("..")

from liquer.commands import command, first_command
from liquer.query import evaluate

@first_command
def hello():
    return "Hello"

@command
def greet(greeting, who="world"):
    return f"{greeting}, {who}!"

print (evaluate("hello/greet").get())
print (evaluate("hello/greet-everybody").get())