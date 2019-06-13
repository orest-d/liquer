# Make it run from the examples directory
import sys
sys.path.append("..")

from liquer import *

@first_command
def hello():
    return "Hello"

@command
def greet(greeting, who="world"):
    return f"{greeting}, {who}!"

# with default delimiters
print (evaluate_template("""
Template example [[]]

- $hello$
- $hello/greet$
- $hello/greet-everybody$

"""))

# with custom delimiters
print (evaluate_template("""
Template example $$$

- [[hello]]
- [[hello/greet]]
- [[hello/greet-everybody]]

""","[[","]]"))