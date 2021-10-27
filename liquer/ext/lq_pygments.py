from liquer.commands import command, first_command, command_registry
import liquer.ext.basic
import pygments
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter


@command(ns="pygments")
def highlight(code, lexer="py", style="default"):
    """Syntax highlighting by Pygments
    Returns html-formatted code.
    Lexer specifies the syntax (currently only "py" for python).
    Style is the style parameter for the Pygments formatter.
    """
    if lexer == "py":
        html = pygments.highlight(
            code, PythonLexer(), HtmlFormatter(noclasses=True, style=style)
        )
    else:
        raise Exception(f"Unsupported lexer: {lexer}")
    return html
