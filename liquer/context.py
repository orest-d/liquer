import traceback
from liquer.state import State
from liquer.parser import encode, decode, parse, TransformQuerySegment, Query
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
        self.messages=[]
        self.progress_indicators=[]

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
        print(f"{'- '*self.level}  EVALUATE ACTION '{action}' on '{state.query}'")
        cache = cache or self.cache()
        cr = self.command_registry()

        if isinstance(action, TransformQuerySegment):
            if action.is_filename():
                return state.with_filename(action.filename)
            assert action.is_action_request()
            action = action.query[0]

        is_volatile = state.is_volatile()
        old_state = state if is_volatile else state.clone()

        state = state.next_state()

        ns, command, metadata = cr.resolve_command(state, action.name)
        if command is None:
            print(f"Unknown action: {action.name} at {action.position}")
            return state.with_data(None).log_error(
                message=f"Unknown action {action.name} at {action.position}"
            )
        else:
            try:
                state = command(old_state, *action.parameters, context=self)
            except Exception as e:
                traceback.print_exc()
                state.log_exception(message=str(e), traceback=traceback.format_exc())
                state.exception = e
        arguments = getattr(state, "arguments", None)
        state.metadata["commands"].append(f"action {action.encode()} at {action.position}")
        state.metadata["extended_commands"].append(
            dict(
                command_name=action.name,
                ns=ns,
                qcommand=f"action {action.encode()} at {action.position}",
                command_metadata=metadata._asdict(),
                arguments=arguments,
            )
        )
        state.metadata["query"] = self.raw_query
        state.metadata["attributes"] = {
            key: value for key, value in state.metadata["attributes"].items() if key[0].isupper()
        }

        if metadata is not None:
            state.metadata["attributes"].update(metadata.attributes)
        state.set_volatile(is_volatile)
        state.log_info(f"Action {action.encode()} at {action.position} completed")
        return state

    def create_initial_state(self):
        state = State()
        state.query = ""
        return state

    def evaluate(self, query, cache=None):
        print(f"{'- '*self.level}EVALUATE {query}")
        """Evaluate query, returns a State, cache the output in supplied cache"""
        if self.query is not None:
            return self.child_context().evaluate(query)
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
        print(f"{'- '*self.level}  PROCESS Predecessor:{p} Action: {r}")
        if p is None or p.is_empty():
            state = self.create_initial_state()
            print(f"{'- '*self.level}  INITIAL STATE")
        else:
            state = self.child_context().evaluate(p, cache=cache)

        if state.is_error:
            state = state.next_state()
            state.query = query.encode()
            print(f"{'- '*self.level}  ERROR in '{state.query}'")
            return state

        if r is None:
            print(
                f"{'- '*self.level}  RETURN '{query}' AFTER EMPTY ACTION ON '{state.query}'"
            )
            state.query = query.encode()
            return state

        state = self.evaluate_action(state, r)
        state.query = query.encode()

        if state.metadata["caching"] and not state.is_error and not state.is_volatile():
            cache.store(state)
        print(f"{'- '*self.level}  RETURN '{state.query}' AFTER ACTION '{r}'")
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
                    qr = str(self.child_context().evaluate(q).get())
                    local_cache[q] = qr
                    result += qr
        return result
