import traceback
from collections import namedtuple
import inspect
from liquer.state import State
from liquer.parser import encode

"""This module is responsible for registering commands
Commands are composed of a command executable and command metadata, which are collected in a command registry.
CommandRegistry is a singleton that can be obtained by get_command_registry().

Command metadata (CommandMetadata tuple) contain informations about the command and its arguments
(type, parsing and editing of each argument). These metadata are a basis for parsing of arguments as well as command editor creation.

Argument parsers are responsible for parsing command arguments into desired types.
ArgumentParser has a parse method, which takes argument metadata and list of arguments (typically supplied as list of strings
resulting from liquer.parser.decode). Parsing may extract arbitrary amount of arguments and thus support more complex data structures.
Parse method returns a tuple with the parsed argument and remaining unparsed arguments.
Argument parsers which do not need multiple instances (typical case) have predefined constants.
Multiple argument parsers may be collected in a SequenceArgumentParser by use of + operator (e.g. INT_AP + FLOAT_AP).
"""

CommandMetadata = namedtuple(
    "Command", ["name", "label", "module", "doc", "state_argument", "arguments"])


class CommandRegistry(object):
    """Class responsible for registering all commands and their metadata"""

    def __init__(self):
        """Create empty command registry"""
        self.executables = {}
        self.metadata = {}

    def register(self, executable, metadata):
        """Create command
        executable is an CommandExecutable of the command,
        metadata is CommandMetadata
        """
        name = metadata.name
        self.executables[name] = executable
        self.metadata[name] = name

    def to_dict(self):
        """Returns dictionary representation of the registry, safe to serialize as json"""
        return {name: cmd._asdict() for name, cmd in self.metadata}

    def evaluate_command(self, state, qcommand: list):
        state = state.clone()
        state.commands.append(qcommand)
        state.query = encode(state.commands)
        command_name = qcommand[0]
        if command_name in self.executables:
            try:
                state = self.executables[command_name](state, *qcommand[1:])
            except Exception as e:
                traceback.print_exc()
                state.log_exception(message=str(
                    e), traceback=traceback.format_exc())
        else:
            return state.with_data(None).log_error(message=f"Unknown command: {command_name}")
        return state


_command_registry = None


def command_registry():
    """Return global the command registry object"""
    global _command_registry
    if _command_registry is None:
        _command_registry = CommandRegistry()
    return _command_registry


def reset_command_registry():
    """Create empty global command registry"""
    global _command_registry
    _command_registry = CommandRegistry()
    return _command_registry


class ArgumentParser(object):
    def __add__(self, ap):
        return SequenceArgumentParser(self, ap)

    def parse(self, metadata, args):
        return args[0], args[1:]


class SequenceArgumentParser(ArgumentParser):
    def __init__(self, *sequence):
        self.sequence = list(sequence)

    def __add__(self, ap):
        return SequenceArgumentParser(*(self.sequence+[ap]))

    def __iadd__(self, ap):
        self.sequence.append(ap)
        return self

    def parse(self, metadata, args):
        parsed_arguments = []
        for ap, meta in zip(self.sequence, metadata):
            parsed, args = ap.parse(meta, args)
            parsed_arguments.append(parsed)
        return parsed_arguments, args


class IntArgumentParser(ArgumentParser):
    def parse(self, metadata, args):
        return int(args[0]), args[1:]


class FloatArgumentParser(ArgumentParser):
    def parse(self, metadata, args):
        return float(args[0]), args[1:]


class BooleanArgumentParser(ArgumentParser):
    def parse(self, metadata, args):
        return dict(y=True, yes=True, n=False, no=False, t=True, true=True, f=False, false=False).get(str(args[0]).lower(), False), args[1:]


class ListArgumentParser(ArgumentParser):
    def parse(self, metadata, args):
        return args, []


GENERIC_AP = ArgumentParser()
INT_AP = IntArgumentParser()
FLOAT_AP = FloatArgumentParser()
BOOLEAN_AP = BooleanArgumentParser()
LIST_AP = ListArgumentParser()


def identifier_to_label(identifier):
    """Tries to convert an identifier to a more human readable text label.
    Replaces underscores by spaces and may do other tweaks.
    """
    txt = identifier.replace("_", " ")
    txt = txt.replace(" id", "ID")
    txt = dict(url="URL").get(txt, txt)
    txt = txt[0].upper()+txt[1:]
    return txt


def command_metadata_from_callable(f, has_state_argument=True):
    """Extract command metadata structure from a callable.
    Function interprets function name, document string, argument names and annotations into command metadata. 
    """
    name = f.__name__
    doc = f.__doc__
    module = f.__module__
    annotations = f.__annotations__
    if doc is None:
        doc = ""
    arguments = []
    sig = inspect.signature(f)
    for argname in list(sig.parameters):
        arg = dict(name=argname, label=identifier_to_label(argname))
        arg_type = None
        if argname in annotations:
            arg_annotation = annotations[argname]
            if type(arg_annotation) == type:
                arg_type = arg_annotation.__name__

        p = sig.parameters[argname]
        if p.default != inspect.Parameter.empty:
            arg["default"] = p.default
            arg["optional"] = True
            if arg_type is None:
                arg_type = type(p.default).__name__
        else:
            arg["optional"] = False
        arg["multiple"] = p.kind is inspect.Parameter.VAR_POSITIONAL
        arg_editor = None
        if arg_type is not None:
            arg_editor = arg_type
        arg["type"] = arg_type
        arg["editor"] = arg_editor
        arguments.append(arg)

    if has_state_argument and len(arguments):
        state_argument = arguments[0]
        state_argument["pass_state"] = state_argument["name"] == "state"
        arguments = arguments[1:]
    else:
        state_argument = None

    return CommandMetadata(name=name,
                           label=identifier_to_label(name),
                           module=module,
                           doc=doc,
                           state_argument=state_argument,
                           arguments=arguments)


def argument_parser_from_command_metadata(command_metadata):
    """Create argument parser from command metadata"""
    ap = SequenceArgumentParser()
    for arg in command_metadata.arguments:
        if arg.get("multiple", False):
            ap += LIST_AP
            break
        arg_type = arg.get("type")
        ap += dict(
            str=GENERIC_AP,
            int=INT_AP,
            float=FLOAT_AP,
            bool=BOOLEAN_AP
        ).get(arg_type, GENERIC_AP)
    return ap


class CommandExecutable(object):
    def __init__(self, f, metadata, argument_parser):
        self.f = f
        self.metadata = metadata
        self.argument_parser = argument_parser

    def __call__(self, state, *args):
        args = list(args) + [a["default"]
                             for a in self.metadata.arguments[len(args):]]
        argv, remainder = self.argument_parser.parse(self.metadata, args)
        assert len(remainder) == 0
        state_arg = state if self.metadata.state_argument["pass_state"] else state.get(
        )
        result = self.f(state_arg, *argv)
        if isinstance(result, State):
            return result
        else:
            return state.with_data(result)


class FirstCommandExecutable(CommandExecutable):
    def __call__(self, state, *args):
        args = list(args) + [a["default"]
                             for a in self.metadata.arguments[len(args):]]
        argv, remainder = self.argument_parser.parse(self.metadata, args)
        assert len(remainder) == 0
        result = self.f(*argv)
        if isinstance(result, State):
            return result
        else:
            return state.with_data(result)


def _register_command(f, metadata):
    parser = argument_parser_from_command_metadata(metadata)
    if metadata.state_argument is None:
        executable = FirstCommandExecutable(f, metadata, parser)
    else:
        executable = CommandExecutable(f, metadata, parser)
    command_registry().register(executable, metadata)


def command(f):
    """Register a callable as a command.
    Callable is expected to take a state data as a first argument. 
    This typically can be used as a decorator 
    """
    metadata = command_metadata_from_callable(f)
    _register_command(f, metadata)
    return f


def first_command(f):
    """Register a callable as a command.
    Unlike in command(), callable is expected NOT to take a state data as a first argument.
    Thus first_command can be a first command in the query - does not require a state to be applied on.
    However, first_command is a perfectly valid command, so it can as well be used inside the query and
    then the state passed to the command is ignored (and not passed to f).
    This typically can be used as a decorator.
    """
    metadata = command_metadata_from_callable(f, has_state_argument=False)
    _register_command(f, metadata)
    return f
