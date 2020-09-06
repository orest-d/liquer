import traceback
import os.path
from liquer.context import Context, find_queries_in_template


def evaluate(query):
    """Evaluate query, returns a State, cache the output in supplied cache"""
    return Context().evaluate(query)


def evaluate_and_save(query, target_directory=None, target_file=None):
    """Evaluate query and save result.
    Output is saved either to
    - a target directory (current working directory by default) to a file deduced from the query, or
    - to target_file (if specified)
    Returns a state.
    """
    return Context().evaluate_and_save(query, target_directory=target_directory, target_file=target_file)


def evaluate_template(template: str, prefix="$", sufix="$"):
    """Evaluate a string template; replace all queries by their values
    Queries in the template are delimited by prefix and sufix.
    Queries should evaluate to strings and should not cause errors.
    """
    return Context().evaluate_template(template, prefix=prefix, sufix=sufix)