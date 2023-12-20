# Make it run from the examples directory
import sys
sys.path.append("..")

from liquer import *

### Optional: setup logging
import logging
logging.basicConfig(level=logging.DEBUG)


@first_command
def hello():
    return "Hello"

@command
def greet(greeting, who="world"):
    return f"{greeting}, {who}!"

print (evaluate("hello/greet").get())
print (evaluate("hello/greet-everybody").get())