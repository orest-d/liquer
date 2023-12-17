"""Main liquer module. Importing this module is sufficient to use liquer.
It exposes command registration decorators (*command* and *first_command*),
query evaluation functions (*evaluate*, *evaluate_and_save*) and context access (*get_context*).
"""
from liquer.commands import command, first_command
from liquer.query import evaluate, evaluate_and_save, evaluate_template
from liquer.context import get_context

__version__ = "0.9.4"
