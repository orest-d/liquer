import traceback
from collections import namedtuple
import inspect
from liquer.state import State
from liquer.parser import encode
import marshal
import pickle
import types
import traceback
import base64
from liquer.parser import (
    StringActionParameter,
    ActionParameter,
    QueryException,
    ExpandedActionParameter,
)


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

Though commands can be registered with a low level method 'register' of CommandRegistry (which allows the greatest flexibility),
the "mainstream" way of command registration is by simply decorating a function with @command or @first_command.

"""

CommandMetadata = namedtuple(
    "CommandMetadata",
    ["name", "label", "module", "doc", "state_argument", "arguments", "attributes", "version"],
)


_remote_registration = False


def is_remote_registration_enabled():
    """Returns true if remote registration is enabled.
    This is a flag that a web interface can use to enable or disable the remote command registration.

    WARNING: Remote command registration allows to deploy arbitrary python code on LiQuer server,
    therefore it is a HUGE SECURITY RISK and it only should be used if other security measures are taken
    (e.g. on localhost or intranet where only trusted users have access).
    This is on by default on Jupyter server extension.
    """
    return _remote_registration


def enable_remote_registration():
    """Enable remote registration service

    WARNING: Remote command registration allows to deploy arbitrary python code on LiQuer server,
    therefore it is a HUGE SECURITY RISK and it only should be used if other security measures are taken
    (e.g. on localhost or intranet where only trusted users have access).
    This is on by default on Jupyter server extension.
    """
    global _remote_registration
    _remote_registration = True


def disable_remote_registration():
    "Disable remote registration service"
    global _remote_registration
    _remote_registration = True


class RegisterRemoteMixin:
    def register_remote_serialized(self, b):
        """Helper method used to register serialized command in remote registration"""
        if is_remote_registration_enabled():
            try:
                f, metadata, modify = self.decode_registration(b)
                self.register_command(f, metadata, modify=modify)
                ns = metadata.attributes.get("ns", "root")
                return dict(
                    message=f"Function {f.__name__} in namespace {ns} is registered as command",
                    status="OK",
                )
            except:
                return dict(
                    message="Error while registering command",
                    traceback=traceback.format_exc(),
                    status="ERROR",
                )
        else:
            return dict(
                message="Remote command registration is disabled.", status="ERROR"
            )

    @classmethod
    def encode_registration(cls, f, metadata, modify=False):
        code = marshal.dumps(f.__code__)
        return b"B" + pickle.dumps(
            (
                code,
                f.__name__,
                f.__defaults__,
                f.__closure__,
                metadata._asdict(),
                modify,
            )
        )

    @classmethod
    def encode_registration_base64(cls, f, metadata, modify=False):
        return b"E" + base64.urlsafe_b64encode(
            cls.encode_registration(f, metadata, modify)
        )

    @classmethod
    def decode_registration(cls, b):
        assert type(b) == bytes
        if b[0] == b"E"[0]:
            print("DECODE E:", b[:20])
            print()
            b = base64.urlsafe_b64decode(b[1:])
        print("DECODE B:", b[:20])
        print()
        print()
        assert b[0] == b"B"[0]
        b = b[1:]

        code, name, defaults, closure, metadata, modify = pickle.loads(b)
        bc = marshal.loads(code)
        f = types.FunctionType(bc, globals(), name, defaults, closure)
        return (f, CommandMetadata(**metadata), modify)


class RemoteCommandRegistry(RegisterRemoteMixin, object):
    """Remote command registry allows to register commands into a remote LiQuer server, e.g. Jupyter server extension"""

    def __init__(self, url, use_get_method=False):
        self.url = url
        self.use_get_method = use_get_method

    def register_command(self, f, metadata, modify=False):
        import requests

        url = self.url
        url += "" if url[-1] == "/" else "/"

        if self.use_get_method:
            b = self.encode_registration_base64(f, metadata, modify)
            encoded = b.decode("ascii")
            response = requests.get(url=url + encoded)
        else:
            b = self.encode_registration(f, metadata, modify)
            response = requests.post(url=url, data=b)

        if response.ok:
            response = response.json()
            if response["status"] != "OK":
                print(response.get("traceback", ""))
                raise Exception(
                    "Remote registration failed: "
                    + response.get("message", f"Error registering {f.__name__}")
                )
        else:
            response.raise_for_status()


class CommandRegistry(RegisterRemoteMixin, object):
    """Class responsible for registering all commands and their metadata"""

    def __init__(self):
        """Create empty command registry"""
        self.executables = {}
        self.metadata = {}
        self.namespaces = {}

    def is_doubleregistered(self, executable, metadata):
        """Returns True if the same function is already registered as a command.
        Another function registered under the same name would return False.
        """
        name = metadata.name
        ns = metadata.attributes.get("ns", "root")
        self.executables[ns] = self.executables.get(ns, {})
        self.metadata[ns] = self.metadata.get(ns, {})

        if name in self.executables[ns]:
            registered = self.metadata[ns][name]
            return (
                name == registered.name
                and executable.inner_id() == self.executables[ns][name].inner_id()
            )
        return False

    def register_command(self, f, metadata, modify=False):
        parser = argument_parser_from_command_metadata(metadata)
        if metadata.state_argument is None:
            executable = FirstCommandExecutable(f, metadata, parser)
        else:
            executable = CommandExecutable(f, metadata, parser)
        return self.register(executable, metadata)

    def register(self, executable, metadata, modify=False):
        """Create command
        executable is an CommandExecutable of the command,
        metadata is CommandMetadata
        """
        name = metadata.name
        ns = metadata.attributes.get("ns", "root")

        modify = modify or metadata.attributes.get("modify_command", False)
        can_register = modify
        self.executables[ns] = self.executables.get(ns, {})
        self.metadata[ns] = self.metadata.get(ns, {})
        if name in self.executables[ns]:
            if self.is_doubleregistered(executable, metadata):
                can_register = True
        else:
            can_register = True
        if can_register:
            self.executables[ns][name] = executable
            self.metadata[ns][name] = metadata
        else:
            raise Exception(f"Command {name} is already registered")

    def as_dict(self):
        """Returns dictionary representation of the registry, safe to serialize as json"""
        return {
            ns: {name: cmd._asdict() for name, cmd in metadata.items()}
            for ns, metadata in self.metadata.items()
        }

    def evaluate_command_old(self, state, qcommand: list):
        if not state.is_volatile():
            state = state.clone()
        command_name = qcommand[0]
        ns, command, metadata = self.resolve_command(state, command_name)
        if command is None:
            print(f"Unknown command: {command_name}")
            return state.with_data(None).log_error(
                message=f"Unknown command: {command_name}"
            )
        else:
            try:
                state = command(state, *qcommand[1:])
            except Exception as e:
                traceback.print_exc()
                state.log_exception(message=str(e), traceback=traceback.format_exc())
                state.exception = e
        arguments = getattr(state, "arguments", None)
        state.metadata["commands"].append(qcommand)
        state.metadata["extended_commands"].append(
            dict(
                command_name=command_name,
                ns=ns,
                qcommand=qcommand,
                command_metadata=metadata._asdict(),
                arguments=arguments,
            )
        )
        state.query = encode(state.metadata["commands"])
        state.metadata["attributes"] = {
            key: value
            for key, value in state.metadata["attributes"].items()
            if key[0].isupper()
        }
        if metadata is not None:
            state.metadata["attributes"].update(metadata.attributes)

        return state

    def resolve_command(self, state, command_name):
        for ns in state.vars.get("active_namespaces", ["root"]):
            if ns not in self.executables:
                print(f"Unknown namespace: {ns}")
                continue
            if command_name in self.executables[ns]:
                break

        if command_name in self.executables[ns]:
            command = self.executables[ns][command_name]
            if command_name in self.metadata[ns]:
                return ns, command, self.metadata[ns][command_name]
            else:
                print(f"Unknown command (metadata): {command_name}")
                return ns, command, None

        return None, None, None


_command_registry = None


def command_registry():
    """Return global the command registry object"""
    global _command_registry
    if _command_registry is None:
        _command_registry = CommandRegistry()
    return _command_registry


def remote_command_registry(url, use_get_method=False):
    """Configure the command registry to use remote LiQuer server
    Provide url to the registration service
    """
    global _command_registry
    _command_registry = RemoteCommandRegistry(url, use_get_method=use_get_method)
    return _command_registry


def reset_command_registry():
    """Create empty global command registry"""
    global _command_registry
    _command_registry = CommandRegistry()
    return _command_registry


class ArgumentParserException(QueryException):
    def __init__(self, message, position=None, query=None):
        super().__init__(message, position, query)


class ArgumentParser(object):
    is_argv = False

    def __add__(self, ap):
        return SequenceArgumentParser(self, ap)

    def parse(self, metadata, args):
        return args[0], args[1:]

    def parse_meta(self, metadata, args, context=None):
        query = None if context is None else context.raw_query
        if isinstance(args[0], str):
            return args[0], (args[0], metadata), args[1:]
        elif isinstance(args[0], StringActionParameter):
            return args[0].string, (args[0].string, metadata), args[1:]
        elif isinstance(args[0], ExpandedActionParameter):
            return args[0].value, (args[0].value, metadata), args[1:]
        elif isinstance(args[0], ActionParameter):
            raise ArgumentParserException(
                f"Unsupported action parameter {repr(args[0])}  in ArgumentParser",
                position=args[0].position,
                query=query,
            )
        else:
            return args[0], (args[0], metadata), args[1:]


class SequenceArgumentParser(ArgumentParser):
    def __init__(self, *sequence):
        self.sequence = list(sequence)

    def __add__(self, ap):
        return SequenceArgumentParser(*(self.sequence + [ap]))

    def __iadd__(self, ap):
        self.sequence.append(ap)
        return self

    def parse(self, metadata, args):
        parsed_arguments = []
        for ap, meta in zip(self.sequence, metadata):
            parsed, args = ap.parse(meta, args)
            if ap.is_argv:
                parsed_arguments.extend(parsed)
            else:
                parsed_arguments.append(parsed)
        return parsed_arguments, args

    def parse_meta(self, metadata, args, context=None):
        parsed_arguments = []
        parsed_meta = []
        for ap, meta in zip(self.sequence, metadata):
            parsed, argmeta, args = ap.parse_meta(meta, args, context=context)
            if ap.is_argv:
                parsed_arguments.extend(parsed)
            else:
                parsed_arguments.append(parsed)
            parsed_meta.append(argmeta)
        return parsed_arguments, parsed_meta, args


class ContextArgumentParser(ArgumentParser):
    def parse(self, metadata, args):
        return None, args

    def parse_meta(self, metadata, args, context=None):
        return context, (context, metadata), args


class IntArgumentParser(ArgumentParser):
    def parse(self, metadata, args):
        return int(args[0]), args[1:]

    def parse_meta(self, metadata, args, context=None):
        query = None if context is None else context.raw_query
        if isinstance(args[0], str):
            try:
                value = int(args[0])
            except:
                raise ArgumentParserException(
                    f"""Error parsing integer argument '{metadata["name"]}' from string {repr(args[0])}""",
                    query=query,
                )
        elif isinstance(args[0], StringActionParameter):
            try:
                value = int(args[0].string)
            except:
                raise ArgumentParserException(
                    f"""Error parsing integer argument '{metadata["name"]}' from {repr(args[0].string)}""",
                    position=args[0].position,
                    query=query,
                )
        elif isinstance(args[0], ExpandedActionParameter):
            try:
                value = int(args[0].value)
            except:
                raise ArgumentParserException(
                    f"""Error parsing integer argument '{metadata["name"]}' from link {repr(args[0].link.encode())}""",
                    position=args[0].position,
                    query=query,
                )
        elif isinstance(args[0], ActionParameter):
            raise ArgumentParserException(
                f"Unsupported action parameter type {repr(args[0])} in IntArgumentParser",
                position=args[0].position,
                query=query,
            )
        else:
            try:
                value = int(args[0])
            except:
                raise ArgumentParserException(
                    f"""Error parsing integer argument '{metadata["name"]}' from object {repr(args[0])}""",
                    query=query,
                )

        return value, (value, metadata), args[1:]


class FloatArgumentParser(ArgumentParser):
    def parse(self, metadata, args):
        return float(args[0]), args[1:]

    def parse_meta(self, metadata, args, context=None):
        query = None if context is None else context.raw_query
        if isinstance(args[0], str):
            try:
                value = float(args[0])
            except:
                raise ArgumentParserException(
                    f"""Error parsing float argument '{metadata["name"]}' from string {repr(args[0])}""",
                    query=query,
                )
        elif isinstance(args[0], StringActionParameter):
            try:
                value = float(args[0].string)
            except:
                raise ArgumentParserException(
                    f"""Error parsing float argument '{metadata["name"]}' from {repr(args[0].string)}""",
                    position=args[0].position,
                    query=query,
                )
        elif isinstance(args[0], ExpandedActionParameter):
            try:
                value = float(args[0].value)
            except:
                raise ArgumentParserException(
                    f"""Error parsing float argument '{metadata["name"]}' from link {repr(args[0].link.encode())}""",
                    position=args[0].position,
                    query=query,
                )
        elif isinstance(args[0], ActionParameter):
            raise ArgumentParserException(
                f"Unsupported action parameter type {repr(args[0])} in FloatArgumentParser",
                position=args[0].position,
                query=query,
            )
        else:
            try:
                value = float(args[0])
            except:
                raise ArgumentParserException(
                    f"""Error parsing float argument '{metadata["name"]}' from object {repr(args[0])}""",
                    query=query,
                )

        return value, (value, metadata), args[1:]


class BooleanArgumentParser(ArgumentParser):
    def parse(self, metadata, args):
        return (
            dict(
                y=True,
                yes=True,
                n=False,
                no=False,
                t=True,
                true=True,
                f=False,
                false=False,
            ).get(str(args[0]).lower(), False),
            args[1:],
        )

    def parse_meta(self, metadata, args, context=None):
        query = None if context is None else context.raw_query

        def to_bool(x):
            return dict(
                y=True,
                yes=True,
                n=False,
                no=False,
                t=True,
                true=True,
                f=False,
                false=False,
            ).get(str(x).lower(), False)

        if isinstance(args[0], str):
            try:
                value = to_bool(args[0])
            except:
                raise ArgumentParserException(
                    f"""Error parsing boolean argument '{metadata["name"]}' from string {repr(args[0])}""",
                    query=query,
                )
        elif isinstance(args[0], StringActionParameter):
            try:
                value = to_bool(args[0].string)
            except:
                raise ArgumentParserException(
                    f"""Error parsing boolean argument '{metadata["name"]}' from value {repr(args[0].string)}""",
                    position=args[0].position,
                    query=query,
                )
        elif isinstance(args[0], ExpandedActionParameter):
            try:
                value = to_bool(args[0].value)
            except:
                raise ArgumentParserException(
                    f"""Error parsing boolean argument '{metadata["name"]}' from link {repr(args[0].link.encode())}""",
                    position=args[0].position,
                    query=query,
                )
        elif isinstance(args[0], ActionParameter):
            raise ArgumentParserException(
                f"Unsupported action parameter type {repr(args[0])} in BooleanArgumentParser",
                position=args[0].position,
                query=query,
            )
        else:
            try:
                value = dict(
                    y=True,
                    yes=True,
                    n=False,
                    no=False,
                    t=True,
                    true=True,
                    f=False,
                    false=False,
                ).get(str(args[0]).lower(), False)
            except:
                raise ArgumentParserException(
                    f"""Error parsing boolean argument '{metadata["name"]}' from object {repr(args[0])}""",
                    query=query,
                )

        return value, (value, metadata), args[1:]


class ListArgumentParser(ArgumentParser):
    def parse(self, metadata, args):
        return args, []

    def parse_meta(self, metadata, args, context=None):
        query = None if context is None else context.raw_query

        value = []
        for x in args:
            if isinstance(x, str):
                value.append(x)
            elif isinstance(x, StringActionParameter):
                value.append(x.string)
            elif isinstance(x, ExpandedActionParameter):
                value.append(x.value)
            elif isinstance(x, ActionParameter):
                raise ArgumentParserException(
                    f"Unsupported action parameter type {repr(x)} in ListArgumentParser",
                    position=x.position,
                    query=query,
                )
            else:
                raise ArgumentParserException(
                    f"Unsupported action parameter object {repr(x)} in ListArgumentParser",
                    query=query,
                )

        return value, (value, metadata), []


class ArgvArgumentParser(ListArgumentParser):
    is_argv = True


GENERIC_AP = ArgumentParser()
CONTEXT_AP = ContextArgumentParser()
INT_AP = IntArgumentParser()
FLOAT_AP = FloatArgumentParser()
BOOLEAN_AP = BooleanArgumentParser()
LIST_AP = ListArgumentParser()
ARGV_AP = ArgvArgumentParser()


def identifier_to_label(identifier):
    """Tries to convert an identifier to a more human readable text label.
    Replaces underscores by spaces and may do other tweaks.
    """
    txt = identifier.replace("_", " ")
    txt = txt.replace(" id", "ID")
    txt = dict(url="URL").get(txt, txt)
    txt = txt[0].upper() + txt[1:]
    return txt

def callable_hash(f):
    import hashlib
    h = hashlib.md5()
    h.update(f.__code__.co_code)
    separator=b"__sep3024325ab2a7__" #random string of bytes
    for x in f.__code__.co_consts:
        try:
            h.update(pickle.dumps(x))
        except:
            continue
        h.update(separator)

    sig = inspect.signature(f)
    for argname in list(sig.parameters):
        h.update(argname.encode('utf-8'))
        h.update(separator)
        p = sig.parameters[argname]
        if p.default != inspect.Parameter.empty:
            try:
                h.update(pickle.dumps(x))
            except:
                continue
        h.update(separator)

    return h.hexdigest()

def command_metadata_from_callable(f, has_state_argument=True, attributes=None):
    """Extract command metadata structure from a callable.
    Function interprets function name, document string, argument names and annotations into command metadata.
    """
    name = f.__name__
    doc = f.__doc__
    module = f.__module__
    annotations = f.__annotations__
    if attributes is None:
        attributes = dict(ns=None)
    if doc is None:
        doc = ""
    arguments = []
    sig = inspect.signature(f)
    for argname in list(sig.parameters):
        arg = dict(name=argname, label=identifier_to_label(argname))
        if argname == "context":
            p = sig.parameters[argname]
            if p.default != inspect.Parameter.empty:
                if p.default is not None:
                    raise Exception(
                        f"Default value for context in command {name} should be None"
                    )
                arg["default"] = p.default
            if argname in annotations:
                raise Exception(
                    f"Context in command {name} should not have type annotations"
                )
            arg["multiple"] = False
            arg["optional"] = True
            arg["type"] = "context"
            arg["editor"] = "ignore"
            arguments.append(arg)
            continue

        arg_type = None
        if argname in annotations:
            arg_annotation = annotations[argname]
            if type(arg_annotation) == type:
                arg_type = arg_annotation.__name__

        p = sig.parameters[argname]
        if p.default != inspect.Parameter.empty:
            arg["default"] = p.default
            arg["optional"] = True
            if arg_type is None and p.default is not None:
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

    return CommandMetadata(
        name=name,
        label=identifier_to_label(name),
        module=module,
        doc=doc,
        state_argument=state_argument,
        arguments=arguments,
        attributes=attributes,
        version=callable_hash(f)
    )


def argument_parser_from_command_metadata(command_metadata):
    """Create argument parser from command metadata"""
    ap = SequenceArgumentParser()
    for arg in command_metadata.arguments:
        if arg.get("multiple", False):
            ap += ARGV_AP
            break
        arg_type = arg.get("type")
        ap += dict(
            context=CONTEXT_AP,
            str=GENERIC_AP,
            int=INT_AP,
            float=FLOAT_AP,
            bool=BOOLEAN_AP,
            list=LIST_AP,
        ).get(arg_type, GENERIC_AP)
    return ap


class CommandExecutable(object):
    """Wrapper around a registered command
    Adapts arbitrary function to be used as a command.
    Function needs to be described by a command metadata structure and accompanied by an argument parser.
    This decodes all the arguments, executes the command and (if needed) wraps the result as a State.
    """

    def __init__(self, f, metadata, argument_parser):
        self.f = f
        self.metadata = metadata
        self.argument_parser = argument_parser

    def inner_id(self):
        return id(self.f)

    def parse_argv(self, args, context=None):
        query = None if context is None else context.raw_query
        args = list(args)
        try:
            position = args[-1].position
        except:
            position = None
        for i, a in list(enumerate(self.metadata.arguments))[len(args) :]:
            try:
                position = args[i].position
            except:
                position = None
            if not a.get("multiple", False) and a["name"] != "context":
                if "default" in a:
                    args.append(a["default"])
                else:
                    raise ArgumentParserException(
                        f"Expected '{a['name']}' argument for '{self.metadata.name}', no default",
                        position=position,
                        query=query,
                    )
        try:
            argv, argmeta, remainder = self.argument_parser.parse_meta(
                self.metadata.arguments, args, context=context
            )
        except ArgumentParserException as e:
            raise ArgumentParserException(
                f"{e.original_message} while executing '{self.metadata.name}'",
                position=e.position,
                query=query,
            ) from e
        if len(remainder) != 0:
            position = (
                remainder[0].position
                if isinstance(remainder[0], ActionParameter)
                else None
            )
            raise ArgumentParserException(
                f"Too many arguments for '{self.metadata.name}': {repr(remainder)}",
                position=position,
                query=query,
            )
        return argv, argmeta

    def __call__(self, state, *args, context=None):
        argv, argmeta = self.parse_argv(args, context=context)
        state_arg = state if self.metadata.state_argument["pass_state"] else state.get()
        result = self.f(state_arg, *argv)
        if isinstance(result, State):
            result.arguments = argmeta
            return result
        else:
            state.arguments = argmeta
            return state.with_data(result)


class FirstCommandExecutable(CommandExecutable):
    """Wrapper around a registered first command"""

    def __call__(self, state, *args, context=None):
        argv, argmeta = self.parse_argv(args, context=context)
        result = self.f(*argv)
        if isinstance(result, State):
            result.arguments = argmeta
            return result
        else:
            state.arguments = argmeta
            return state.with_data(result)


def command(*arg, **kwarg):
    """Register a callable as a command.
    Callable is expected to take a state data as a first argument.

    This function typically can be used as a decorator.
    As a decorator it can be used directly (@command) or it can have parameters,
    e.g. @command(ns="MyNameSpace")
    """
    if len(arg) == 1:
        assert callable(arg[0])
        f = arg[0]
        if "ns" not in kwarg:
            kwarg["ns"] = "root"
        metadata = command_metadata_from_callable(f, attributes=kwarg)
        command_registry().register_command(f, metadata)
        return f
    else:
        assert len(arg) == 0
        return lambda f, attributes=kwarg: command(f, **attributes)


def first_command(*arg, **kwarg):
    """Register a callable as a command.
    Unlike in command(), callable is expected NOT to take a state data as a first argument.
    Thus first_command can be a first command in the query - does not require a state to be applied on.
    However, first_command is a perfectly valid command, so it can as well be used inside the query and
    then the state passed to the command is ignored (and not passed to f).
    This typically can be used as a decorator.
    """
    if len(arg) == 1:
        assert callable(arg[0])
        f = arg[0]
        if "ns" not in kwarg:
            kwarg["ns"] = "root"
        metadata = command_metadata_from_callable(
            f, has_state_argument=False, attributes=kwarg
        )
        command_registry().register_command(f, metadata)
        return f
    else:
        assert len(arg) == 0
        return lambda f, attributes=kwarg: first_command(f, **attributes)
