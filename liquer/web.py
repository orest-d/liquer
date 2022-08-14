from liquer.template import expand_simple


def query_link(query):
    return f"http://127.0.0.1:5000/liquer/q/{query}"


def key_link(key):
    return f"http://127.0.0.1:5000/liquer/api/store/data/{key}"


def key_query(key):
    return f"{key}/-/dr"


def key_query_parameters(key=None, query=None):
    if key is None:
        if query is None:
            raise Exception("Neither key nor query specified")
        else:
            return dict(QUERY=query, QUERY_LINK=query_link(query))
    else:
        return dict(
            KEY=key,
            KEY_QUERY=key_query(key),
            QUERY=query or key_query(key),
            QUERY_LINK=key_link(key),
        )
