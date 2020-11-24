import traceback
from liquer.state import State
from liquer.parser import encode, decode, parse, TransformQuerySegment, Query, ActionRequest, StringActionParameter, ExpandedActionParameter, LinkActionParameter
from liquer.cache import cached_part, get_cache
from liquer.commands import command_registry
from liquer.state_types import encode_state_data, state_types_registry
import os.path


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
        self.query = None
        self.parent_context = parent_context
        self.level = level
        self.direct_subqueries=[]
        self.parent_query=None
        self.progress_indicators=[]
        self.log=[]
        self.is_error=False
        self.message=""
        self.debug_messages=False

    def metadata(self):
        return dict(
            query=self.raw_query,
            parent_query=self.parent_query,
            log=self.log[:],
            is_error=self.is_error,
            direct_subqueries = self.direct_subqueries[:],
            progress_indicators=self.progress_indicators[:],
            message=self.message
        )

    def log_dict(self,d):
        self.log.append(d)
        if "message" in d:
            self.message=d["message"]
        return self

    def log_action(self, qv, number=0):
        """Log a command"""
        if isinstance(qv, ActionRequest):
            qv=qv.to_list()
        return self.log_dict(dict(kind="command", qv=qv, command_number=number))

    def error(self, message):
        """Log an error message"""
        self.is_error = True
        print ("ERROR:    ",message)
        return self.log_dict(dict(kind="error", message=message))

    def warning(self, message):
        """Log a warning message"""
        print ("WARNING:  ",message)
        return self.log_dict(dict(kind="warning", message=message))

    def exception(self, message, traceback):
        """Log an exception"""
        self.is_error = True
        print ("ERROR (x):",message)
        return self.log_dict(
            dict(kind="error", message=message, traceback=traceback)
        )

    def info(self, message):
        """Log a message (info)"""
        print ("INFO:     ",message)
        self.log_dict(dict(kind="info", message=message))
        return self

    def debug(self, message):
        """Log a message (info)"""
        if self.debug_messages:
            print ("DEBUG:    ",message)
            self.log_dict(dict(kind="debug", message=message))
        return self

    def child_context(self):
        return self.__class__(parent_context=self, level=self.level + 1)

    def root_context(self):
        return self if self.parent_context is None else self.parent_context.root_context()

    def log_subquery(self, query:str):
        assert type(query)==str
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
        cache = cache or self.cache()
        cr = self.command_registry()

        state.context=self

        if isinstance(action, TransformQuerySegment):
            if action.is_filename():
                return state.with_filename(action.filename)
            assert action.is_action_request()
            action = action.query[0]

        is_volatile = state.is_volatile()
        old_state = state if is_volatile else state.clone()

        state = state.next_state()
        state.context=self

        ns, command, cmd_metadata = cr.resolve_command(state, action.name)
        if command is None:
            self.error(f"Unknown action: {action.name} at {action.position}")
        else:
            parameters = []
            for p in action.parameters:
                if isinstance(p, StringActionParameter):
                    parameters.append(p)
                elif isinstance(p, LinkActionParameter):
                    if p.link.absolute:
                        self.debug(f"Expand absolute link parameter {p.link.encode()}")
                        value = self.evaluate(p.link)
                        if value.is_error:
                            self.error(f"Link parameter error {p.link.encode()} at {p.position}")
                        pp = ExpandedActionParameter(value.get(), p.link, p.position)
                        parameters.append(pp)
                    else:
                        self.debug(f"Expand relative link parameter {p.link.encode()} on {self.parent_query}")
                        value = self.apply(p.link)
                        if value.is_error:
                            self.error(f"Link parameter error {p.link.encode()} at {p.position}")
                        pp = ExpandedActionParameter(value.get(), p.link, p.position)
                        parameters.append(pp)
                else:
                    raise Exception(f"Unknown parameter type {type(p)} in {action.name} at {action.position}")

            try:
                state = command(old_state, *parameters, context=self)
                assert type(state.metadata) is dict
            except Exception as e:
                traceback.print_exc()
                self.exception(message=str(e), traceback=traceback.format_exc())
                state.exception = e
        arguments = getattr(state, "arguments", None)
        metadata = self.metadata()
        metadata["commands"]=metadata.get("commands",[]) + [action.to_list()]
        metadata["extended_commands"]=metadata.get("extended_commands",[])+[
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
            key: value for key, value in state.metadata["attributes"].items() if key[0].isupper()
        }

        if cmd_metadata is not None:
            metadata["attributes"] = dict(metadata.get("attributes",{}), **cmd_metadata.attributes)
        self.info(f"Action {action.encode()} at {action.position} completed")
        state.metadata.update(metadata)
        state.set_volatile(is_volatile or state.is_volatile())
        return state

    def create_initial_state(self):
        state = State()
        state.query = ""
        return state

    def apply(self, query):
        self.debug(f"APPLY {query}")
        if self.parent_query in (None,"","/"):
            self.debug(f"  no parent query in apply {query}")
            return self.evaluate(query)
        if isinstance(query, str):
            query = parse(query)
        if query.absolute:
            self.debug(f"  absolute link in apply {query}")
            return self.evaluate(query)
        tq = query.transform_query()
        if tq is None:
            raise Exception(f"Only transform query supported in apply ({query} on {self.parent_query})")
        q = (parse(self.parent_query) + tq).encode()
        self.debug(f"apply {query} on {self.parent_query} yields {q}")
        return self.evaluate(q)

    def evaluate(self, query, cache=None):
        self.debug(f"EVALUATE {query}")
        """Evaluate query, returns a State, cache the output in supplied cache"""
        if self.query is not None:
            state = self.child_context().evaluate(query)
            if not isinstance(query, str):
                query=query.encode()
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

        if cache is None:
            cache = self.cache()

        state = cache.get(query.encode())
        if state is not None:
            return state

        p, r = query.predecessor()
        self.debug(f"PROCESS Predecessor:{p} Action: {r}")
        if p is None or p.is_empty():
            self.parent_query=""
            state = self.create_initial_state()
            self.debug(f"INITIAL STATE")
        else:
            self.parent_query=p.encode()
            state = self.child_context().evaluate(p, cache=cache)

        if state.is_error:
            state = state.next_state()
            state.query = query.encode()
            self.debug(f"ERROR in '{state.query}'")
            return state

        if r is None:
            self.debug(
                f"RETURN '{query}' AFTER EMPTY ACTION ON '{state.query}'"
            )
            state.query = query.encode()
            return state

        state = self.evaluate_action(state, r)
        state.query = query.encode()

        if state.metadata["caching"] and not state.is_error and not state.is_volatile():
            cache.store(state)
        self.debug(f"RETURN '{state.query}' AFTER ACTION '{r}'")
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
                        qr=f"ERROR({q})"
                    else:
                        qr=str(state.get())
                    local_cache[q] = qr
                    result += qr
        return result
