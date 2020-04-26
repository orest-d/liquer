# Make it run from the examples directory
import sys
sys.path.append("..")

from liquer import *
from liquer.commands import remote_command_registry

remote_command_registry("http://127.0.0.1:5000/liquer/api/register_command/", use_get_method=True)  # Configure the remote command registration


hello_text = "Hello"
@first_command(modify_command=True)  # modify_command allows to change the command (register multiple times)
def hello(hello_text=hello_text):    # global variables will not work with the command, pass them as arguments
    return hello_text
