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

from liquer.store import get_store, Store, KeyNotFoundStoreException, StoreException, key_extension


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

class MetadataContextMixin:
    def metadata(self):
        metadata = self._metadata.as_dict()
        title = self.title
        description = self.description
        if title is None:
            if self.raw_query is None:
                title = ""
            else:
                p = parse(self.raw_query)
                if title in ("", None):
                    title = p.filename() or ""

        mimetype = self.mimetype
        if mimetype is None:
            if self.query is not None:
                if self.query.extension() is None:
                    mimetype = "application/octet-stream"
                else:
                    mimetype = mimetype_from_extension(self.query.extension())

        message = self._metadata.message
        if message in (None, ""):
            log = self._metadata.get("log",[])
            if len(log):
                message = log[-1]["message"]
        if message in (None, ""):
            log = self._metadata.get("child_log",[])
            if len(log):
                message = log[-1]["message"]

        metadata.update(dict(
            status=self.status.value,
            title=title,
            description=description,
            mimetype=mimetype,
            query=self.raw_query,
            parent_query=self.parent_query,
            argument_queries=self.argument_queries,
#            log=self.log[:],
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
        ))
        return metadata

    def log_dict(self, d):
        "Put dictionary with a log entry into the log"
        d["timestamp"] = timestamp()
        self._metadata.log_dict(d)
        self.store_metadata(force=(d.get("kind") == "error"))
        if self.parent_context is not None:
            if d.get("origin") is None:
                d = dict(origin=self.raw_query, **d)
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

    @property
    def raw_query(self):
        return self._metadata.query

    @raw_query.setter
    def raw_query(self, value):
        self._metadata.query = value

class Context(MetadataContextMixin, object):
    def __init__(self, parent_context=None, debug=False):
        self.parent_context = parent_context  # parent context - when in child context

#        self.raw_query = None  # String with the evaluated query
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
        #self.log = []  # log of messages as a list of dictionaries
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

        self._metadata = Metadata()

    def new_empty(self):
        return Context(debug=self.debug_messages)


    def store_data(self, key, data):
        """Convenience method to store data in the store including metadata.
        Note that the metadata are taken from the context.metadata() and slightly updated.
        They might not be 100% correct, since the store_data will probably be called as
        a side-effect of a query, not a result of a query.
        This is indicated by the side_effect flag in the metadata and status Status.SIDE_EFFECT.value.
        """
        metadata = self.metadata()
        store = self.store()
        extension = key_extension(key)
        metadata["data_characteristics"] = data_characteristics(data)
        metadata["side_effect"] = True
        metadata["status"] = Status.SIDE_EFFECT.value
        try:
            b, mimetype, type_identifier = encode_state_data(data, extension=extension)
            metadata["type_identifier"] = type_identifier
            metadata["mimetype"] = mimetype
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
            self._metadata.add_command_dependency(ns, cmd_metadata)
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
        metadata["type_identifier"]=state.type_identifier
        metadata["commands"] = metadata.get("commands", []) + [action.to_list()]
        if metadata.get("mimetype","application/octet-stream") == "application/octet-stream":
            metadata["mimetype"] = state.mimetype()
            
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
        self.debug(f"EVALUATE {query} ")

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

        raw_query, query = self.to_query(query)
        self.raw_query=raw_query
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
                    self.status = Status.EXPIRED
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

        if target_directory==None and target_file==None and target_resource_directory==None and store==None:
            target_directory = "."

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

