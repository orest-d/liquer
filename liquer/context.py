import traceback
from liquer.state import State, EvaluationException, vars_clone
from liquer.parser import (
    encode,
    decode,
    parse,
    QueryException,
    TransformQuerySegment,
    Query,
    ActionRequest,
    StringActionParameter,
    ExpandedActionParameter,
    LinkActionParameter,
)
from liquer.cache import cached_part, get_cache
from liquer.commands import command_registry
from liquer.state_types import (
    encode_state_data,
    state_types_registry,
    data_characteristics,
    type_identifier_of,
)
import os.path
from datetime import datetime
import json
from liquer.constants import Status, mimetype_from_extension
import liquer.util as util
from liquer.util import timestamp
from copy import deepcopy
from liquer.metadata import Metadata

from liquer.store import get_store, Store, KeyNotFoundStoreException, StoreException
from yaml import load, dump

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


def find_queries_in_template(template: str, prefix: str, sufix: str):
    try:
        start = template.index(prefix)
        end = template.index(sufix, start + len(prefix))
        yield template[:start], template[start + len(prefix) : end]
        for text, query in find_queries_in_template(
            template[end + len(sufix) :], prefix, sufix
        ):
            yield text, query
    except ValueError:
        yield template, None


class Vars(dict):
    def __init__(self, *arg, **kwarg):
        super().__init__(*arg, **kwarg)
        self._modified_vars = set()

    def __getattr__(self, name):
        return self[name]

    def __setattr__(self, name, value):
        if name == "_modified_vars":
            super().__setattr__(name, value)
        else:
            self._modified_vars.add(name)
            self[name] = value

    def __getstate__(self):
        return (self._modified_vars, dict(self))

    def __setstate__(self, x):
        mv, d = x
        super().__setattr__("_modified_vars", mv)
        self.clear()
        self.update(d)

    def get_modified(self):
        return {key: self[key] for key in self._modified_vars}


def log_time():
    date = datetime.now()
    return date.strftime("%H:%M:%S")


CONTEXT_CREATOR = None


def set_context_creator(context_creator):
    global CONTEXT_CREATOR
    CONTEXT_CREATOR = context_creator


def get_context(context=None):
    global CONTEXT_CREATOR
    if context is None:
        if CONTEXT_CREATOR is None:
            return Context()
        else:
            return CONTEXT_CREATOR()
    else:
        return context


class Context(object):
    def __init__(self, parent_context=None, debug=False):
        self.parent_context = parent_context  # parent context - when in child context

        self.raw_query = None  # String with the evaluated query
        self.query = None  # Query object of the evaluated query
        self.status = Status.NONE  # Status: ready, error...
        self.is_error = False  # True is evaluation failed

        self.started = ""  # Evaluation start time
        self.created = ""  # Created time (evaluation finished)

        self.direct_subqueries = (
            []
        )  # list of subqueries specified as dictionaries with description and query
        self.parent_query = None  # parent query or None
        self.argument_queries = (
            []
        )  # list of argument subqueries specified as dictionaries with description and query

        self.progress_indicators = []  # progress indicators as a list of dictionaries
        self.log = []  # log of messages as a list of dictionaries
        self.child_progress_indicators = []  # progress indicator of a child
        self.child_log = []  # log of messages from child queries
        self.message = ""  # Last message from the log
        self.debug_messages = debug  # Turn the debug messages on/off
        self.caching = True  # caching of the results enabled
        self.enable_store_metadata = True  # flag to controll storing of metadata

        self.last_report_time = None  # internal time stamp of the last report
        self._progress_indicator_identifier = (
            1  # counter for creating unique progress identifiers
        )
        self.description = ""
        self.title = None
        self.mimetype = None

        self.vars = Vars(vars_clone())
        self.html_preview = ""
        self.store_key = None
        self.store_to = None

    def new_empty(self):
        return Context(debug=self.debug_messages)

    def metadata(self):
        title = self.title
        description = self.description
        if title is None:
            if self.raw_query is None:
                title = ""
            else:
                p = parse(self.raw_query)
                if (
                    p.filename() is not None
                    and self.parent_context is not None
                    and self.parent_context.raw_query is not None
                    and self.raw_query
                    == self.parent_context.raw_query + "/" + p.filename()
                ):
                    title = self.parent_context.metadata().get("title")
                    if description is None:
                        description = self.parent_context.metadata().get("description")
                if title in ("", None):
                    title = p.filename() or ""

        mimetype = self.mimetype
        if mimetype is None:
            if self.query is not None:
                if self.query.extension() is None:
                    mimetype = "application/octet-stream"
                else:
                    mimetype = mimetype_from_extension(self.query.extension())

        message = self.message
        if message in (None, ""):
            log = self.log
            if len(log):
                message = log[-1]["message"]
        if message in (None, ""):
            log = self.child_log
            if len(log):
                message = log[-1]["message"]

        return dict(
            status=self.status.value,
            title=title,
            description=description,
            mimetype=mimetype,
            query=self.raw_query,
            parent_query=self.parent_query,
            argument_queries=self.argument_queries,
            log=self.log[:],
            is_error=self.is_error,
            direct_subqueries=self.direct_subqueries[:],
            progress_indicators=self.progress_indicators[:],
            child_progress_indicators=self.child_progress_indicators[:],
            child_log=self.child_log,
            message=message,
            started=self.started,
            updated=self.now(),
            created=self.created,
            caching=self.caching,
            vars=dict(self.vars),
            html_preview=self.html_preview,
            side_effect=False,
        )

    def store_data(self, key, data):
        """Convenience method to store data in the store including metadata.
        Note that the metadata are taken from the context.metadata() and slightly updated.
        They might not be 100% correct, since the store_data will probably be called as
        a side-effect of a query, not a result of a query.
        This is indicated by the side_effect flag in the metadata and status Status.SIDE_EFFECT.value.
        """
        metadata = self.metadata()
        store = self.store()
        v = store.key_name(key).split(".")
        extension = v[-1] if len(v) > 1 else None
        metadata["type_identifier"] = type_identifier
        metadata["mimetype"] = mimetype
        metadata["data_characteristics"] = data_characteristics(data)
        metadata["side_effect"] = True
        metadata["status"] = Status.SIDE_EFFECT.value
        try:
            b, mimetype, type_identifier = encode_state_data(data, extension=extension)
            store.store(key, b, metadata)
        except:
            traceback.print_exc()
            m = Metadata(metadata)
            m.status = Status.ERROR
            m.exception(
                f"Failed to encode data for key '{key}'",
                traceback=traceback.format_exc(),
            )
            store.store_metadata(key, m.as_dict())

    def can_report(self):
        if self.last_report_time is None:
            self.last_report_time = datetime.now()
        return True
        return (datetime.now() - self.last_report_time).total_seconds() > 0.1

    def set_html_preview(self, html):
        self.html_preview = html
        self.store_metadata()
        return self

    def set_description(self, description):
        self.description = description
        self.store_metadata()
        return self

    def set_title(self, title):
        self.title = title
        self.store_metadata()
        return self

    def enable_cache(self, enable=True):
        self.caching = enable
        return self

    def disable_cache(self):
        self.enable_cache(False)
        return self

    def create_state(self):
        return State(metadata=self.metadata(), context=self)

    def store_metadata(self, force=False):
        if self.raw_query is not None and self.enable_store_metadata:
            if force or self.can_report():
                metadata = self.metadata()
                self.cache().store_metadata(self.metadata())
                self.last_report_time = datetime.now()
                if self.store_key is not None:
                    store = self.store() if self.store_to is None else self.store_to
                    store.store_metadata(self.store_key, metadata)

    def new_progress_indicator(self):
        self._progress_indicator_identifier += 1
        self.progress_indicators.append(
            dict(
                id=self._progress_indicator_identifier,
                step=0,
                total_steps=None,
                message="",
                timestamp=timestamp(),
            )
        )
        return self._progress_indicator_identifier

    def remove_progress_indicator(self, identifier):
        self.progress_indicators = [
            x for x in self.progress_indicators if x["id"] != identifier
        ]
        if self.parent_context is not None:
            self.parent_context.remove_child_progress(self.raw_query)

    def progress_indicator_index(self, identifier):
        if identifier is None:
            if len(self.progress_indicators):
                return len(self.progress_indicators) - 1
            self.new_progress_indicator()
            return len(self.progress_indicators) - 1

        for i, x in enumerate(self.progress_indicators):
            if x["id"] == identifier:
                return i
        return None

    def now(self):
        return util.now()

    def progress(
        self, step=0, total_steps=None, message="", identifier=None, autoremove=True
    ):
        index = self.progress_indicator_index(identifier)

        progress = dict(
            step=step, total_steps=total_steps, message=message, timestamp=timestamp()
        )
        self.progress_indicators[index].update(progress)

        removed = False
        if autoremove and total_steps is not None and step >= total_steps:
            self.remove_progress_indicator(index)
            removed = True

        self.store_metadata()

        if self.parent_context is not None:
            if removed:
                self.parent_context.remove_child_progress(self.raw_query)
            else:
                d = dict(origin=self.raw_query, **progress)
                self.parent_context.log_child_progress(d)

    def progress_iter(self, iterator, show_value=False):
        try:
            total_steps = len(iterator)
        except:
            total_steps = None
        identifier = self.new_progress_indicator()
        for i, x in enumerate(iterator):
            if total_steps is None:
                message = f"{x} ({i+1})" if show_value else f"{i+1}"
            else:
                message = (
                    f"{x} ({i+1}/{total_steps})"
                    if show_value
                    else f"{i+1}/{total_steps}"
                )
            self.progress(
                i, total_steps=total_steps, message=message, identifier=identifier
            )
            yield x
        self.remove_progress_indicator(identifier)

    def remove_child_progress(self, origin):
        "Remove all child progress indicators from a given origin"
        self.child_progress_indicators = [
            x for x in self.child_progress_indicators if x.get("origin") != origin
        ]
        self.store_metadata()
        if self.parent_context is not None:
            self.parent_context.remove_child_progress(origin)

    def log_child_progress(self, d):
        "Put dictionary with a child progress entry into the child progress indicators and notify parent"
        self.child_progress_indicators = [
            x
            for x in self.child_progress_indicators
            if x.get("origin") != d.get("origin")
        ]
        self.child_progress_indicators.append(d)
        self.store_metadata()
        if self.parent_context is not None:
            self.parent_context.log_child_progress(d)
        return self

    def log_dict(self, d):
        "Put dictionary with a log entry into the log"
        d["timestamp"] = timestamp()
        self.log.append(d)
        if "message" in d:
            self.message = d["message"]
        self.store_metadata(force=(d.get("kind") == "error"))
        if self.parent_context is not None:
            if d.get("origin") is None:
                d = dict(origin=self.raw_query, **d)
            self.parent_context.log_child_dict(d)
        return self

    def log_child_dict(self, d):
        "Put dictionary with a child log entry into the child log"
        d = dict(**d)
        if d.get("origin") is None:
            if self.parent_context is None:
                d["origin"] = None
            else:
                d["origin"] = self.parent_context.raw_query
        self.child_log.append(d)
        self.child_log = self.child_log[:5]
        self.store_metadata()
        if self.parent_context is not None:
            self.parent_context.log_child_dict(d)
        return self

    def log_action(self, qv, number=0):
        """Log a command"""
        if isinstance(qv, ActionRequest):
            qv = qv.to_list()
        return self.log_dict(dict(kind="command", qv=qv, command_number=number))

    def error(self, message, position=None, query=None):
        """Log an error message"""
        self.is_error = True
        self.status = Status.ERROR
        if position is None:
            print(f"{log_time()} ERROR:    ", message)
        else:
            print(f"{log_time()} ERROR:    ", message, f" at {position}")
        return self.log_dict(
            dict(
                kind="error",
                message=message,
                position=None if position is None else position.to_dict(),
                query=query,
            )
        )

    def warning(self, message, traceback=None):
        """Log a warning message"""
        print(f"{log_time()} WARNING:  ", message)
        return self.log_dict(dict(kind="warning", message=message, traceback=traceback))

    def exception(self, message, traceback, position=None, query=None):
        """Log an exception"""
        self.is_error = True
        self.status = Status.ERROR
        if position is None:
            print(f"{log_time()} EXCEPTION:", message)
        else:
            print(f"{log_time()} EXCEPTION:", message, f" at {position}")
        return self.log_dict(
            dict(
                kind="error",
                message=message,
                traceback=traceback,
                position=None if position is None else position.to_dict(),
                query=query,
            )
        )

    def info(self, message):
        """Log a message (info)"""
        print(f"{log_time()} INFO:     ", message)
        self.log_dict(dict(kind="info", message=message))
        return self

    def debug(self, message):
        """Log a message (info)"""
        if self.debug_messages:
            print(f"{log_time()} DEBUG:    ", message)
            self.log_dict(dict(kind="debug", message=message))
        return self

    def child_context(self):
        return self.__class__(parent_context=self)

    def root_context(self):
        return (
            self if self.parent_context is None else self.parent_context.root_context()
        )

    def log_subquery(self, query: str, description=None):
        assert type(query) == str
        if query not in self.direct_subqueries:
            if description is None:
                description = query
            self.direct_subqueries.append(dict(description=description, query=query))

    def command_registry(self):
        return command_registry()

    def cache(self):
        return get_cache()

    def state_types_registry(self):
        return state_types_registry()

    def evaluate_parameter(self, p, action):
        if isinstance(p, StringActionParameter):
            return p
        elif isinstance(p, LinkActionParameter):
            if p.link.absolute:
                self.argument_queries.append(
                    dict(
                        description=f"{p.link.encode()} at {p.position}",
                        query=p.link.encode(),
                    )
                )
                self.debug(f"Expand absolute link parameter {p.link.encode()}")
                value = self.evaluate(p.link)
                if value.is_error:
                    self.error(
                        f"Error while evaluating absolute link parameter {p.link.encode()}",
                        position=p.position,
                        query=self.raw_query,
                    )
                    self.status = Status.ERROR
                    self.store_metadata(force=True)

                    raise EvaluationException(
                        f"Error while evaluating absolute link parameter {p.link.encode()} in action {action.name}",
                        position=p.position,
                        query=self.raw_query,
                    )
                pp = ExpandedActionParameter(value.get(), p.link, p.position)
                return pp
            else:
                self.argument_queries.append(
                    dict(
                        description=f"{p.link.encode()} at {p.position}",
                        query=p.link.encode(),
                    )
                )
                self.debug(
                    f"Expand relative link parameter {p.link.encode()} on {self.parent_query}"
                )
                value = self.apply(p.link)
                if value.is_error:
                    self.error(
                        f"Error while evaluating relative link parameter {p.link.encode()} at {p.position}",
                        position=p.position,
                        query=self.raw_query,
                    )
                    self.status = Status.ERROR
                    self.store_metadata(force=True)

                    raise EvaluationException(
                        f"Error while evaluating relative link parameter {p.link.encode()} in action {action.name}",
                        position=p.position,
                        query=self.raw_query,
                    )
                pp = ExpandedActionParameter(value.get(), p.link, p.position)
                return pp
        else:
            self.status = Status.ERROR
            self.store_metadata(force=True)
            raise EvaluationException(
                f"Unknown parameter type {type(p)} in {action.name}",
                position=action.position,
                query=self.raw_query,
            )

    def evaluate_action(self, state: State, action, cache=None):
        self.debug(f"EVALUATE ACTION '{action}' on '{state.query}'")
        self.status = Status.EVALUATION
        self.store_metadata(force=True)
        cache = cache or self.cache()
        cr = self.command_registry()

        state.context = self

        if isinstance(action, TransformQuerySegment):
            if action.is_filename():
                return state.with_filename(action.filename)
            assert action.is_action_request()
            action = action.query[0]

        is_volatile = state.is_volatile()
        old_state = state if is_volatile else state.clone()

        state = state.next_state()
        state.context = self

        ns, command, cmd_metadata = cr.resolve_command(state, action.name)
        if command is None:
            self.error(
                f"Unknown action: '{action.name}'",
                position=action.position,
                query=self.raw_query,
            )
        else:
            parameters = []
            self.status = Status.EVALUATING_DEPENDENCIES
            self.store_metadata(force=True)
            for p in action.parameters:
                parameters.append(self.evaluate_parameter(p, action))
            self.status = Status.EVALUATION
            self.store_metadata(force=True)

            try:

                state = command(old_state, *parameters, context=self)
                assert type(state.metadata) is dict
            except EvaluationException as ee:
                print("EE:", ee)
                # traceback.print_exc()
                state.is_error = True
                state.exception = ee
            except Exception as e:
                traceback.print_exc()
                state.is_error = True
                self.exception(
                    message=str(e),
                    position=action.position,
                    query=self.raw_query,
                    traceback=traceback.format_exc(),
                )
                state.exception = EvaluationException(
                    traceback.format_exc() + "\n" + str(e),
                    position=action.position,
                    query=self.raw_query,
                )
        arguments = getattr(state, "arguments", None)
        if arguments is not None:

            def to_arg(arg):
                x, meta = arg
                try:
                    s = json.dumps(x)
                    if len(s) > 100:
                        return [s[:50], meta]
                    return [x, meta]
                except:
                    return [None, meta]

            arguments = [to_arg(a) for a in arguments]

        metadata = self.metadata()
        metadata["commands"] = metadata.get("commands", []) + [action.to_list()]
        try:
            cmd_metadata_d = cmd_metadata._asdict()
        except:
            cmd_metadata_d = {}
        metadata["extended_commands"] = metadata.get("extended_commands", []) + [
            dict(
                command_name=action.name,
                ns=ns,
                qcommand=action.to_list(),
                action=f"{action.encode()} at {action.position}",
                command_metadata=cmd_metadata_d,
                arguments=arguments,
            )
        ]
        metadata["query"] = self.raw_query
        metadata["attributes"] = {
            key: value
            for key, value in state.metadata["attributes"].items()
            if key[0].isupper()
        }

        if cmd_metadata is not None:
            metadata["attributes"] = dict(
                metadata.get("attributes", {}), **cmd_metadata.attributes
            )

        metadata["caching"] = metadata.get("caching", True) and state.metadata.get(
            "caching", True
        )
        is_error = state.is_error or self.is_error

        if is_error:
            self.status = Status.ERROR
            metadata["status"] = self.status.value
            self.info(f"Action {action.encode()} at {action.position} failed")
            state.metadata.update(metadata)
            state.status = Status.ERROR.value
            state.is_error = True
        else:
            self.status = Status.READY
            metadata["status"] = self.status.value
            self.info(f"Action {action.encode()} at {action.position} completed")
            state_vars = dict(self.vars)
            state_vars.update(state.vars)
            state_vars.update(self.vars.get_modified())
            self.vars = Vars(state_vars)
            metadata["vars"] = dict(state_vars)
            state.metadata.update(metadata)

        state.set_volatile(is_volatile or state.is_volatile())

        cache.store_metadata(state.metadata)
        return state

    def store(self):
        return get_store()

    def evaluate_resource(self, resource_query):
        self.info(f"Evaluate resource: {resource_query}")
        if resource_query.header is not None:
            if resource_query.header.encode() not in ("-R", "-R-meta"):
                raise Exception(
                    f"Header '{resource_query.header}' not supported in resource query {resource_query}"
                )
        key = resource_query.path()
        store = self.store()
        state = self.create_initial_state()
        try:
            metadata = store.get_metadata(key)
            if metadata is None:
                if store.contains(key):
                    state.error(
                        f"Key '{key}' was found in store, but the metadata is missing."
                    )
                else:
                    state.error(f"Metadata for key '{key}' not found in store")
            if (
                resource_query.header is not None
                and len(resource_query.header.parameters) > 0
                and resource_query.header.parameters[-1].encode() == "meta"
            ):
                self.info(f"Resource metadata query {resource_query}")
                data = metadata
                metadata = dict(
                    description=f"Metadata for {key}",
                    key=key,
                    query=resource_query.encode(),
                )
            else:
                data = store.get_bytes(key)
                if data is None:
                    if store.contains(key):
                        if store.is_dir(key):
                            state.error(
                                f"Key '{key}' is a directory, hence there is no data."
                            )
                        else:
                            state.error(
                                f"Key '{key}' was found in store, but the data is missing."
                            )
                    else:
                        state.error(f"Key '{key}' not found in store")

            state = state.with_data(data)
            state.metadata["resource_metadata"] = metadata
        except:
            self.exception(
                message=f"Error evaluating resource {resource_query}",
                traceback=traceback.format_exc(),
                position=resource_query.position,
                query=resource_query.encode(),
            )
            traceback.print_exc()
        return state

    def create_initial_state(self):
        state = State()
        state.query = ""
        return state

    @classmethod
    def to_query(cls, query):
        if query is None:
            return "", Query()
        if isinstance(query, str):
            return query, parse(query)
        elif isinstance(query, Query):
            return query.encode(), query
        else:
            raise Exception(f"Unsupported query type: {type(query)}")

    def apply(self, query, description=None):
        self.debug(f"APPLY {query}")
        if self.parent_query in (None, "", "/"):
            self.debug(f"  no parent query in apply {query}")
            return self.evaluate(query, description=description)
        if isinstance(query, str):
            query = parse(query)
        if query.absolute:
            self.debug(f"  absolute link in apply {query}")
            return self.evaluate(query, description=description)
        tq = query.transform_query()
        if tq is None:
            raise Exception(
                f"Only transform query supported in apply ({query} on {self.parent_query})"
            )
        q = (parse(self.parent_query) + tq).encode()
        self.debug(f"apply {query} on {self.parent_query} yields {q}")
        return self.evaluate(q, description=description)

    def _store_state(self, state):
        if self.store_key is not None:
            metadata = state.metadata
            store = self.store() if self.store_to is None else self.store_to
            if state.is_error:
                store.store_metadata(self.store_key, metadata)
            else:
                data = state.get()
                reg = self.state_types_registry()
                t = reg.get(type(data))
                try:
                    if state.metadata.get("extension") is None:
                        b, mime, typeid = encode_state_data(data)
                    else:
                        b, mime, typeid = encode_state_data(
                            data, extension=state.metadata["extension"]
                        )
                    store.store(self.store_key, b, metadata)
                except:
                    traceback.print_exc()
                    m = Metadata(metadata)
                    m.status = Status.ERROR
                    m.exception(
                        f"Failed to encode data for key '{self.store_key}'",
                        traceback=traceback.format_exc(),
                    )
                    store.store_metadata(self.store_key, m.as_dict())

    def evaluate(
        self, query, cache=None, description=None, store_key=None, store_to=None
    ):
        """Evaluate query, returns a State.
        This method can be used in a command to evaluate a subquery,
        which will be recorded in metadata and can be inspected during the query execution.

        When evaluating such a subquery, it is good to give it a description (via a description argument).
        If this is not a sub-query, description parameter will set the description in the metadata (see set_description).
        Note that this might be overridden by the subsequent calls to set_description.
        Parameter cache can be used to set a cache object. In most cases default cache is the safest choice.

        Evaluation can be (besides cache) stored in the store under the key specified by the store_key (if not None).
        A store can be specified too via the store_to option. If None (default), the default store (from the store method) is used.
        """
        self.enable_store_metadata = False  # Prevents overwriting cache with metadata
        self.status = Status.EVALUATION
        self.debug(f"EVALUATE {query}")
        self.vars = Vars(vars_clone())

        if self.query is not None:
            self.enable_store_metadata = True
            print(f"Subquery {query} called from {self.query.encode()}")
            state = self.child_context().evaluate(
                query, store_key=store_key, store_to=store_to
            )
            if not isinstance(query, str):
                query = query.encode()
            self.log_subquery(query=query, description=description)
            if state.is_error:
                print("Subquery failed")
                for d in state.metadata.get("log", []):
                    self.log_dict(d)
            #            self.enable_store_metadata = True
            self.store_metadata(force=True)
            self.enable_store_metadata = False
            return state

        self.raw_query, query = self.to_query(query)
        self.query = query
        self.store_key = store_key
        self.store_to = store_to
        self.started = self.now()
        if description is not None:
            self.set_description(description)

        if cache is None:
            cache = self.cache()

        self.debug(f"Using cache {repr(cache)}")
        self.debug(f"Try cache {query}")
        state = cache.get(query.encode())
        if state is not None:
            self.debug(f"Cache hit {query}")
            self._store_state(state)
            return state
        self.enable_store_metadata = (
            True  # Metadata can be only written after trying to read from cache,
        )
        # so that cache does not get overwritten
        self.debug(f"Cache miss {query}")

        if query.is_resource_query():
            state = self.evaluate_resource(query.resource_query())
            state.query = query.encode()
            state.metadata["created"] = self.now()
            self._store_state(state)
            return state
        else:
            p, r = query.predecessor()
            self.debug(f"PROCESS Predecessor:{p} Action: {r}")
            if p is None or p.is_empty():
                self.parent_query = ""
                state = self.create_initial_state()
                state.metadata["created"] = self.now()
                self.debug(f"INITIAL STATE")
            else:
                self.parent_query = p.encode()
                self.status = Status.EVALUATING_PARENT
                self.store_metadata(force=True)
                state = self.child_context().evaluate(p, cache=cache)
            if state.is_error:
                self.status = Status.ERROR
                self.store_metadata()
                state = state.next_state()
                state.query = query.encode()
                state.metadata["created"] = self.now()
                self.debug(f"ERROR in '{state.query}'")
                self._store_state(state)
                return state
        self.vars = Vars(state.vars)
        if r is None:
            self.debug(f"RETURN '{query}' AFTER EMPTY ACTION ON '{state.query}'")
            state.query = query.encode()
            state.metadata["created"] = self.now()
            self._store_state(state)
            return state
        elif r.is_filename():
            state.metadata["filename"] = r.filename
            state.metadata["extension"] = ".".join(r.filename.split(".")[1:])

        state = self.evaluate_action(state, r)
        state.query = query.encode()
        state.metadata["created"] = self.now()

        if (
            state.metadata.get("caching", True)
            and not state.is_error
            and not state.is_volatile()
        ):
            print("CACHE", state.query)
            #            self.status = "cache"
            #            self.store_metadata()
            cache.store(state)
        else:
            if state.is_error:
                cache.store_metadata(state.metadata)
            else:
                print("REMOVE CACHE", state.query)
                if not cache.remove(state.query):
                    self.status = Status.OBSOLETE
                    self.store_metadata()

        self._store_state(state)
        return state

    def evaluate_and_save(
        self,
        query,
        target_directory=None,
        target_file=None,
        target_resource_directory=None,
        store=None,
    ):
        """Evaluate query and save result.
        Output is saved either to
        - a target directory (current working directory by default) to a file deduced from the query, or
        - to target_file (if specified)
        Returns a state.
        """

        print(f"*** Evaluate and save {query} started")
        state = self.evaluate(query)
        if state.is_error:
            print(f"*** Evaluate and save {query} failed")
            if target_resource_directory is not None and target_file is not None:
                filename = target_file
                key = (
                    filename
                    if target_resource_directory == ""
                    else target_resource_directory + "/" + filename
                )
                if store is None:
                    store = self.store()

                print(state.metadata)
                store.store_metadata(key, state.metadata)

        data = state.get()
        reg = self.state_types_registry()
        t = reg.get(type(data))

        filename = target_file
        if state.metadata.get("extension") is None:
            b, mime, typeid = encode_state_data(data)
            filename = t.default_filename() if target_file is None else target_file
        else:
            b, mime, typeid = encode_state_data(
                data, extension=state.metadata["extension"]
            )
            filename = (
                (
                    t.default_filename()
                    if state.metadata.get("filename") is None
                    else state.metadata["filename"]
                )
                if target_file is None
                else target_file
            )
        if target_directory is None:
            path = filename
        else:
            path = os.path.join(target_directory, filename)

        if target_directory is not None:
            print(f"*** Evaluate and save {query} to {path}")
            with open(path, "wb") as f:
                f.write(b)

        if target_resource_directory is not None:
            filename = os.path.split(path)[1]
            key = (
                filename
                if target_resource_directory == ""
                else target_resource_directory + "/" + filename
            )
            print(f"*** Store evaluated {query} to {key}")
            if store is None:
                store = self.store()

            store.store(key, b, state.metadata)

        return state

    def evaluate_template(self, template: str, prefix="$", sufix="$", cache=None):
        """Evaluate a string template; replace all queries by their values
        Queries in the template are delimited by prefix and sufix.
        Queries should evaluate to strings and should not cause errors.
        """
        local_cache = {}
        result = ""
        for text, q in find_queries_in_template(template, prefix, sufix):
            result += text
            if q is not None:
                if q in local_cache:
                    result += local_cache[q]
                else:
                    state = self.evaluate(q, description=f"template expansion of {q}")
                    if state.is_error:
                        self.error(f"Template failed to expand {q}")
                        qr = f"ERROR({q})"
                    else:
                        qr = str(state.get())
                    local_cache[q] = qr
                    result += qr
        return result


class RecipeStore(Store):
    def __init__(self, store, recipes=None, context=None):
        self.substore = store
        self._recipes = {} if recipes is None else recipes
        if context is None:
            self.context = Context()
        else:
            self.context = context

    def with_context(self, context):
        return RecipeStore(self.substore, recipes=self.recipes, context=context)

    def mount_recipe(self, key, recipe):
        self._recipes[key] = recipe
        return self

    def ignore(self, key):
        return False

    def make(self, key):
        if self.ignore(key):
            raise Exception(f"Key {key} is ignored, can't make it")
        query = self.recipes().get(key)
        if query is None:
            raise KeyNotFoundStoreException(
                f"Key {key} not found, recipe unknown", key=key, store=self
            )
        target_resource_directory = self.parent_key(key)
        target_file = self.key_name(key)
        #        self.context.new_empty().evaluate_and_save(
        #            query,
        #            target_resource_directory=target_resource_directory,
        #            target_file=target_file,
        #            store=self.substore,
        #        )
        self.context.new_empty().evaluate(
            query,
            store_key=key,
            store_to=self,
        )
        self.on_data_changed(key)
        self.on_metadata_changed(key)

    def recipes(self):
        return self._recipes

    def recipe_metadata(self, key):
        return {}

    def is_supported(self, key):
        if self.ignore(key):
            return False
        return self.substore.is_supported(key)

    def get_bytes(self, key):
        if self.ignore(key):
            return None
        if self.substore.contains(key):
            return self.substore.get_bytes(key)
        self.make(key)
        return self.substore.get_bytes(key)

    def get_metadata(self, key):
        if self.ignore(key):
            raise KeyNotFoundStoreException(key=key, store=self)

        if self.substore.contains(key):
            return self.substore.get_metadata(key)
        if self.is_dir(key):
            return self.finalize_metadata(
                self.default_metadata(key=key, is_dir=True), key=key, is_dir=True
            )
        if key in self.recipes():
            metadata = self.recipe_metadata(key)
            try:
                sub_metadata = self.substore.get_metadata(key)
                if sub_metadata is not None:
                    metadata.update(sub_metadata)
            except:
                pass
            return self.finalize_metadata(metadata, key=key, is_dir=False)
        raise KeyNotFoundStoreException(key=key, store=self)

    def store(self, key, data, metadata):
        if self.ignore(key):
            raise Exception(f"Key {key} is ignored, can't store into it")
        self.substore.store(
            key, data, self.finalize_metadata(metadata, key=key, is_dir=True, data=data)
        )
        self.on_data_changed(key)
        self.on_metadata_changed(key)

    def store_metadata(self, key, metadata):
        if self.ignore(key):
            raise Exception(f"Key {key} is ignored, can't store metadata into it")
        self.substore.store_metadata(key, metadata)
        self.on_metadata_changed(key)

    def remove(self, key):
        self.substore.remove(key)
        self.on_removed(key)

    def removedir(self, key):
        self.substore.removedir(key)
        self.on_removed(key)

    def contains(self, key):
        if self.ignore(key):
            return False
        if self.substore.contains(key):
            return True
        for k in self.recipes():
            if k == key or k.startswith(key + "/"):
                return True
        return False

    def is_dir(self, key):
        if self.ignore(key):
            return False
        if self.substore.is_dir(key):
            return True
        for k in self.recipes():
            if k == key:
                return False
            if k.startswith(key + "/"):
                return True
        return False

    def keys(self):
        return [
            key
            for key in sorted(set(self.substore.keys()).union(self.recipes().keys()))
            if not self.ignore(key)
        ]

    def listdir(self, key):
        if self.ignore(key):
            return []
        d = set(self.substore.listdir(key) or [])
        key_split = key.split("/")
        if len(key_split) == 1 and key_split[0] == "":
            key_split = []
        key_depth = len(key_split)

        for k in self.recipes().keys():
            if k.startswith(key + "/") or key in (None, ""):
                v = k.split("/")
                d.add(v[key_depth])
        return [key for key in sorted(d) if not self.ignore(key)]

    def makedir(self, key):
        if self.ignore(key):
            raise Exception(f"Key {key} is ignored, can't makedir")
        self.substore.makedir(key)
        self.on_data_changed(key)
        self.on_metadata_changed(key)

    def openbin(self, key, mode="r", buffering=-1):
        if self.ignore(key):
            raise Exception(f"Key {key} is ignored, can't openbin")
        return self.substore.openbin(key, mode=mode, buffering=buffering)

    def __str__(self):
        return f"Recipe store on ({self.substore})"

    def __repr__(self):
        return f"RecipeStore({repr(self.substore)}, recipes={repr(self.recipes())})"


class RecipeSpecStore(RecipeStore):
    RECIPES_FILE = "recipes.yaml"
    LOCAL_RECIPES = "RECIPES"
    STATUS_FILE = "recipes_status.txt"

    def __init__(self, store, context=None):
        RecipeStore.__init__(self, store, recipes=None, context=context)
        self.recipes_info = {}
        self.update_recipes()
        self.update_all_status_files()

    def update_all_status_files(self):
        if self.STATUS_FILE is not None:
            for dir_key in set(self.parent_key(key) for key in self.recipes().keys()):
                self.create_status(dir_key)

    def ignore(self, key):
        if key is None:
            return True
        return any(x.startswith(".") for x in key.split("/"))

    def recipe_metadata(self, key):
        metadata = deepcopy(self.recipes_info.get(key, {}))
        metadata["status"] = Status.RECIPE.value
        if metadata.get("query") is not None:
            metadata["has_recipe"] = True
            if self.recipes_info[key].get("recipes_directory") == self.LOCAL_RECIPES:
                metadata["recipes_directory"] = ""
            else:
                metadata["recipes_directory"] = self.recipes_info[key].get(
                    "recipes_directory"
                )
        return metadata

    def make(self, key):
        print(f"### MAKE {key}")
        super().make(key)
        metadata = self.substore.get_metadata(key)
        status = metadata.get("status", Status.RECIPE.value)
        fileinfo = metadata["fileinfo"]
        metadata.update(self.recipe_metadata(key))
        metadata["status"] = status
        metadata["fileinfo"] = fileinfo
        self.substore.store_metadata(key, metadata)
        self.on_metadata_changed(key)

    def update_recipes(self):
        import yaml

        recipes = {}
        for key in self.substore.keys():
            spec = None
            if self.key_name(key) == self.RECIPES_FILE and not self.substore.is_dir(
                key
            ):
                spec = yaml.load(self.substore.get_bytes(key), Loader=Loader)
            recipes_key = key
            if spec is not None:
                parent = self.parent_key(key)
                for directory, items in spec.items():
                    for r in items:
                        if type(r) == str:
                            try:
                                query = parse(r)
                                filename = query.filename()
                                parent = self.parent_key(key)
                                if len(parent) > 0 and not parent.endswith("/"):
                                    parent += "/"
                                rkey = (
                                    f"{parent}{filename}"
                                    if directory == self.LOCAL_RECIPES
                                    else f"{parent}{directory}/{filename}"
                                )
                                recipes[rkey] = r
                                self.recipes_info[rkey] = dict(
                                    query=r,
                                    title=filename,
                                    description="",
                                    recipes_key=recipes_key,
                                    recipes_directory=directory,
                                )
                            except:
                                traceback.print_exc()
                        elif isinstance(r, dict):
                            try:
                                query = parse(r["query"])
                                filename = r.get("filename", query.filename())
                                title = r.get("title", filename)
                                description = r.get("description", r["query"])
                                parent = self.parent_key(key)
                                if len(parent) > 0 and not parent.endswith("/"):
                                    parent += "/"
                                rkey = (
                                    f"{parent}{filename}"
                                    if directory == self.LOCAL_RECIPES
                                    else f"{parent}{directory}/{filename}"
                                )
                                recipes[rkey] = r["query"]
                                self.recipes_info[rkey] = dict(
                                    query=r["query"],
                                    title=title,
                                    description=description,
                                    recipes_key=recipes_key,
                                    recipes_directory=directory,
                                )
                            except:
                                traceback.print_exc()

                        else:
                            print(f"Unsupported recipe type: {type(r)}")

        self._recipes = recipes
        return recipes

    def create_status_text(self, dir_key):
        txt = ""
        if self.substore.is_dir(dir_key):
            for d in self.listdir(dir_key):
                key = f"{dir_key}/{d}" if len(dir_key) else d
                if d == self.STATUS_FILE:
                    continue
                if not self.is_dir(key):
                    metadata = self.get_metadata(key)
                    if metadata is None:
                        txt += "%-14s %-30s %s\n" % ("MISSING", d, "Missing metadata")
                    else:
                        try:
                            t = metadata.get("created")
                            if t in ("", None):
                                t = metadata["updated"]
                            time = util.format_datetime(util.to_datetime(t))
                        except:
                            time = ""
                        status = metadata.get("status", Status.NONE.value)
                        message = metadata.get("message", "").strip()
                        if status == Status.READY.value:
                            try:
                                message = metadata["data_characteristics"][
                                    "description"
                                ]
                            except:
                                pass
                        if "\n" in message:
                            txt += "%-20s %-14s %-32s|" % (time, status, d)
                            txt += "\n=============================================================\n"
                            txt += message
                            txt += "\n=============================================================\n\n"
                        else:
                            txt += "%-20s %-14s %-32s| %s\n" % (
                                time,
                                status,
                                d,
                                message,
                            )
                        trace = ""
                        for entry in metadata.get("log", []) + metadata.get(
                            "child_log", []
                        ):
                            tb = entry.get("traceback")
                            if tb is not None:
                                if len(tb):
                                    if "timestamp" in entry:
                                        trace += f"Time:    {entry['timestamp']}"
                                    if "origin" in entry:
                                        trace += f"Origin:  {entry['origin']}"
                                    if "message" in entry:
                                        trace += f"Message: {entry['message']}"
                                    trace += "\n"
                                    trace += tb
                                    tb += "\n------------------------\n"
                        if len(trace):
                            txt += "\n### TRACEBACK ###############################################\n"
                            txt += trace
                            txt += "\n#############################################################\n\n"

        return txt

    def create_status(self, key):
        if self.key_name(key) != self.STATUS_FILE:
            if not self.is_dir(key):
                key = self.parent_key(key)
            status_key = f"{key}/{self.STATUS_FILE}" if len(key) else self.STATUS_FILE
            data = self.create_status_text(key).encode("utf-8")
            self.substore.store(
                status_key,
                data,
                dict(
                    title=f"Status of {key}",
                    description="This file is generated automatically by the recipe store",
                ),
            )

    def on_metadata_changed(self, key):
        super().on_metadata_changed(key)
        if self.STATUS_FILE is not None:
            if self.key_name(key) == self.RECIPES_FILE:
                self.update_all_status_files()
            elif self.key_name(key) != self.STATUS_FILE:
                self.create_status(key)

    def on_data_changed(self, key):
        super().on_data_changed(key)
        if self.key_name(key) == self.RECIPES_FILE:
            self.update_recipes()
            self.update_all_status_files()
        else:
            self.create_status(key)

    def on_removed(self, key):
        super().on_removed(key)
        if self.key_name(key) == self.RECIPES_FILE:
            self.update_recipes()
            self.update_all_status_files()
        else:
            self.create_status(key)
