from liquer.template import expand_simple


def query_link(query, path_only=False):
    """Convert query to a full url.
    If path_only is true, it will be only the path part of the url (i.e. no protocol, server or port).
    """
    if path_only:
        return f"/liquer/q/{query}"
    else:
        return f"http://127.0.0.1:5000/liquer/q/{query}"


def key_link(key, path_only=False):
    """Convert store key to a full url to the content.
    If path_only is true, it will be only the path part of the url (i.e. no protocol, server or port).
    """
    if path_only:
        return f"/liquer/api/store/data/{key}"
    else:
        return f"http://127.0.0.1:5000/liquer/api/store/data/{key}"


def key_query(key):
    """Converts a store key to a query by adding a dr command."""
    return f"{key}/-/dr"


def unnamed_query(query):
    """Return query without a file name"""
    import liquer.parser as p

    return p.parse(query).without_filename().encode()


def key_query_parameters(key=None, query=None):
    """Defines a set of variables for a specified key and/or query:

    - KEY: The key itself,
    - KEY_QUERY: query accessing the key
    - QUERY: query itself or a key converted to a query using key_query
    - QUERY_LINK: full url link to a query result (using liquer/q api)
    - QUERY_PATH: path part of the url to a query result
    - UNNAMED_QUERY: query without the filename
    - UNNAMED_QUERY_LINK: like QUERY_LINK but without the filename 
    - UNNAMED_QUERY_PATH: like QUERY_PATH but without the filename

    In most cases for tool registration the UNNAMED_QUERY_PATH is used followed by desired filename,
    e.g. $$UNNAMED_QUERY_PATH$/describe/description.html.
    
    """
    if key is None:
        if query is None:
            raise Exception("Neither key nor query specified")
        else:
            return dict(
                QUERY=query,
                QUERY_LINK=query_link(query),
                QUERY_PATH=query_link(query, path_only=True),
                UNNAMED_QUERY=unnamed_query(query),
                UNNAMED_QUERY_LINK=query_link(unnamed_query(query)),
                UNNAMED_QUERY_PATH=query_link(unnamed_query(query), path_only=True),
            )
    else:
        return dict(
            KEY=key,
            KEY_QUERY=key_query(key),
            QUERY=query or key_query(key),
            QUERY_LINK=key_link(key),
            QUERY_PATH=key_link(key, path_only=True),
            UNNAMED_QUERY=unnamed_query(query or key_query(key)),
            UNNAMED_QUERY_LINK=key_link(key),
            UNNAMED_QUERY_PATH=key_link(key, path_only=True),
        )
