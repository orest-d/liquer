import traceback
from liquer.state import State, EvaluationException
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
from liquer.state_types import encode_state_data, state_types_registry
import os.path
from datetime import datetime


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


class Context(object):
    def __init__(self, parent_context=None, level=0):
        self.raw_query = None
        self.status = "none"
        self.started = ""
        self.created = ""
        self.query = None
        self.parent_context = parent_context
        self.level = level
        self.direct_subqueries = []
        self.parent_query = None
        self.progress_indicators = []
        self.log = []
        self.is_error = False
        self.message = ""
        self.debug_messages = False
        self.caching=True

    def metadata(self):
        return dict(
            status=self.status,
            query=self.raw_query,
            parent_query=self.parent_query,
            log=self.log[:],
            is_error=self.is_error,
            direct_subqueries=self.direct_subqueries[:],
            progress_indicators=self.progress_indicators[:],
            message=self.message,
            started=self.started,
            updated=self.now(),
            created=self.created,
            caching=self.caching
        )

    def enable_cache(self, enable=True):
        self.caching = enable
        return self

    def disable_cache(self):
        self.enable_cache(False)
        return self

    def create_state(self):
        return State(metadata=self.metadata(), context=self)

    def store_metadata(self):
        self.cache().store_metadata(self.metadata())

    def new_progress_indicator(self):
        i = 1
        for x in self.progress_indicators:
            i = max(int(x["id"]), i)
        self.progress_indicators.append(
            dict(id=i + 1, step=0, total_steps=None, message="")
        )
        return i + 1

    def remove_progress_indicator(self, identifier):
        self.progress_indicators = [
            x for x in self.progress_indicators if x["id"] != identifier
        ]

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
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def progress(self, step=0, total_steps=None, message="", identifier=None):
        index = self.progress_indicator_index(identifier)
        self.progress_indicators[index].update(
            dict(step=step, total_steps=total_steps, message=message)
        )
        self.store_metadata()

    def log_dict(self, d):
        self.log.append(d)
        if "message" in d:
            self.message = d["message"]
        self.store_metadata()
        return self

    def log_action(self, qv, number=0):
        """Log a command"""
        if isinstance(qv, ActionRequest):
            qv = qv.to_list()
        return self.log_dict(dict(kind="command", qv=qv, command_number=number))

    def error(self, message, position=None, query=None):
        """Log an error message"""
        self.is_error = True
        self.status = "error"
        if position is None:
            print("ERROR:    ", message)
        else:
            print("ERROR:    ", message, f" at {position}")
        return self.log_dict(
            dict(
                kind="error",
                message=message,
                position=None if position is None else position.to_dict(),
                query=query,
            )
        )

    def warning(self, message):
        """Log a warning message"""
        print("WARNING:  ", message)
        return self.log_dict(dict(kind="warning", message=message))

    def exception(self, message, traceback, position=None, query=None):
        """Log an exception"""
        self.is_error = True
        self.status = "error"
        if position is None:
            print("EXCEPTION:", message)
        else:
            print("EXCEPTION:", message, f" at {position}")
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
        print("INFO:     ", message)
        self.log_dict(dict(kind="info", message=message))
        return self

    def debug(self, message):
        """Log a message (info)"""
        if self.debug_messages:
            print("DEBUG:    ", message)
            self.log_dict(dict(kind="debug", message=message))
        return self

    def child_context(self):
        return self.__class__(parent_context=self, level=self.level + 1)

    def root_context(self):
        return (
            self if self.parent_context is None else self.parent_context.root_context()
        )

    def log_subquery(self, query: str):
        assert type(query) == str
        if query not in self.direct_subqueries:
            self.direct_subqueries.append(query)

    def command_registry(self):
        return command_registry()

    def cache(self):
        return get_cache()

    def state_types_registry(self):
        return state_types_registry()

    def evaluate_action(self, state: State, action, cache=None):
        self.debug(f"EVALUATE ACTION '{action}' on '{state.query}'")
        self.status = "action"
        self.store_metadata()
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
            self.error(f"Unknown action: {action.name} at {action.position}")
        else:
            parameters = []
            self.status = "evaluate arguments"
            self.store_metadata()
            for p in action.parameters:
                if isinstance(p, StringActionParameter):
                    parameters.append(p)
                elif isinstance(p, LinkActionParameter):
                    if p.link.absolute:
                        self.debug(f"Expand absolute link parameter {p.link.encode()}")
                        value = self.evaluate(p.link)
                        if value.is_error:
                            self.error(
                                f"Link parameter error {p.link.encode()} at {p.position}"
                            )
                            return self.create_state()

                        pp = ExpandedActionParameter(value.get(), p.link, p.position)
                        parameters.append(pp)
                    else:
                        self.debug(
                            f"Expand relative link parameter {p.link.encode()} on {self.parent_query}"
                        )
                        value = self.apply(p.link)
                        if value.is_error:
                            self.error(
                                f"Link parameter error {p.link.encode()} at {p.position}"
                            )
                            return self.create_state()
                        pp = ExpandedActionParameter(value.get(), p.link, p.position)
                        parameters.append(pp)
                else:
                    self.status = "error"
                    self.store_metadata()
                    raise EvaluationException(
                        f"Unknown parameter type {type(p)} in {action.name}",
                        position=action.position,
                        query=self.raw_query,
                    )

            try:
                state = command(old_state, *parameters, context=self)
                assert type(state.metadata) is dict
            except EvaluationException as ee:
                print("EE:", qe)
                #traceback.print_exc()
                state.is_error=True
                state.exception = ee
            except Exception as e:
                traceback.print_exc()
                state.is_error=True
                self.exception(
                    message=str(e),
                    position=action.position,
                    query=self.raw_query,
                    traceback=traceback.format_exc(),
                )
                state.exception = EvaluationException(traceback.format_exc()+"\n"+str(e), position=action.position, query=self.raw_query)
        arguments = getattr(state, "arguments", None)
        metadata = self.metadata()
        metadata["commands"] = metadata.get("commands", []) + [action.to_list()]
        metadata["extended_commands"] = metadata.get("extended_commands", []) + [
            dict(
                command_name=action.name,
                ns=ns,
                qcommand=action.to_list(),
                action=f"{action.encode()} at {action.position}",
                command_metadata=cmd_metadata._asdict(),
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

        if state.is_error:
            self.info(f"Action {action.encode()} at {action.position} failed")
        else:
            self.info(f"Action {action.encode()} at {action.position} completed")

        state.metadata.update(metadata)
        state.set_volatile(is_volatile or state.is_volatile())
        self.status = "action done"
        self.store_metadata()
        return state

    def create_initial_state(self):
        state = State()
        state.query = ""
        return state

    def apply(self, query):
        self.debug(f"APPLY {query}")
        if self.parent_query in (None, "", "/"):
            self.debug(f"  no parent query in apply {query}")
            return self.evaluate(query)
        if isinstance(query, str):
            query = parse(query)
        if query.absolute:
            self.debug(f"  absolute link in apply {query}")
            return self.evaluate(query)
        tq = query.transform_query()
        if tq is None:
            raise Exception(
                f"Only transform query supported in apply ({query} on {self.parent_query})"
            )
        q = (parse(self.parent_query) + tq).encode()
        self.debug(f"apply {query} on {self.parent_query} yields {q}")
        return self.evaluate(q)

    def evaluate(self, query, cache=None):
        self.status = "started"
        self.debug(f"EVALUATE {query}")
        """Evaluate query, returns a State, cache the output in supplied cache"""
        if self.query is not None:
            state = self.child_context().evaluate(query)
            if not isinstance(query, str):
                query = query.encode()
            self.direct_subqueries.append(query)
            return state

        if isinstance(query, str):
            self.raw_query = query
            self.query = parse(query)
            query = self.query
        elif isinstance(query, Query):
            self.raw_query = query.encode()
            self.query = query
        else:
            raise Exception(f"Unsupported query type: {type(query)}")
        self.store_metadata()

        if cache is None:
            cache = self.cache()

        state = cache.get(query.encode())
        if state is not None:
            return state

        p, r = query.predecessor()
        self.debug(f"PROCESS Predecessor:{p} Action: {r}")
        if p is None or p.is_empty():
            self.parent_query = ""
            state = self.create_initial_state()
            state.metadata["created"] = self.now()
            self.debug(f"INITIAL STATE")
        else:
            self.parent_query = p.encode()
            self.status = "evaluate parent"
            self.store_metadata()
            state = self.child_context().evaluate(p, cache=cache)

        if state.is_error:
            self.status = "error"
            self.store_metadata()
            state = state.next_state()
            state.query = query.encode()
            state.metadata["created"] = self.now()
            self.debug(f"ERROR in '{state.query}'")
            return state

        if r is None:
            self.debug(f"RETURN '{query}' AFTER EMPTY ACTION ON '{state.query}'")
            state.query = query.encode()
            state.metadata["created"] = self.now()
            state.metadata["state"] = "ready"
            return state

        state = self.evaluate_action(state, r)
        state.query = query.encode()
        state.metadata["created"] = self.now()
        state.metadata["state"] = "ready"

        if state.metadata.get("caching", True) and not state.is_error and not state.is_volatile():
            print("CACHE",state.query)
            self.status = "cache"
            self.store_metadata()
            cache.store(state)
        else:
            print("REMOVE CACHE",state.query)
            if not cache.remove(state.query):
                self.status = "obsolete"
                self.store_metadata()

        return state

    def evaluate_and_save(self, query, target_directory=None, target_file=None):
        """Evaluate query and save result.
        Output is saved either to
        - a target directory (current working directory by default) to a file deduced from the query, or
        - to target_file (if specified)
        Returns a state.
        """

        state = self.evaluate(query)
        data = state.get()
        reg = self.state_types_registry()
        t = reg.get(type(data))

        path = target_file
        if path is None:
            if state.extension is None:
                b, mime, typeid = encode_state_data(data)
                path = t.default_filename()
            else:
                b, mime, typeid = encode_state_data(data, extension=state.extension)
                path = (
                    t.default_filename() if state.filename is None else state.filename
                )
            if target_directory is not None:
                path = os.path.join(target_directory, path)

        with open(path, "wb") as f:
            f.write(b)

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
                    state = self.evaluate(q)
                    if state.is_error:
                        self.error(f"Template failed to expand {q}")
                        qr = f"ERROR({q})"
                    else:
                        qr = str(state.get())
                    local_cache[q] = qr
                    result += qr
        return result
