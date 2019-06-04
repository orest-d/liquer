import traceback
from liquer.state import State
from liquer.parser import encode, decode
from liquer.cache import cached_part, get_cache
from liquer.commands import command_registry


def evaluate(query, cache=None):
    """Evaluate query, returns a State, cache the output in supplied cache"""
    state, remainder = cached_part(query, cache=cache)
    return evaluate_query_on(remainder, state=state, cache=cache)


def evaluate_query_on(query, state=None, cache=None):
    """Evaluate query on state, returns a State, cache the output in supplied cache
    Unlike evaluate function, this function does not try to fetch state from cache,
    but it uses a supplied state (if available).
    """
    ql = decode(query)
    return evaluate_ql_on(ql, state=state, cache=cache)


def evaluate_ql_on(ql, state=None, cache=None):
    """This is equivalen to evaluate_query_on, but accepts decoded query
    (list of lists of strings)."""
    if cache is None:
        cache = get_cache()
    if state is None:
        state = State()
    elif not isinstance(state, State):
        state = State().with_data(state)
        
    cr = command_registry()
    for i, qcommand in enumerate(ql):
        if i == len(ql)-1:
            if len(qcommand) == 1 and '.' in qcommand[0]:
                state.with_filename(qcommand[0])
                break
        state = cr.evaluate_command(state, qcommand)
        if state.caching:
            cache.store(state)

    return state
