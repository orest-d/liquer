from urllib.parse import quote, unquote

"""
This module provides functions to decode and encode query.
A query is a sequence of commands, each command being a list of strings starting with the command name as a first element.
Commands are separated by a COMMAND_SEPARATOR, parts of the command (tokens) by PARAMETER_SEPARATOR.
Having special charachers (like COMMAND_SEPARATOR or PARAMETER_SEPARATOR) inside the commands is possible
by escaping with ESCAPE character and using escape sequences.
Query is URL-safe and URL escaping is applied to other special characters.
Empty commands are ignored (e.g. two consecutive COMMAND_SEPARATORs are equivalent to a single COMMAND_SEPARATOR).

Query can be decoded from string to a list of lists of strings by decode (or encoded by encode).
Encode and decode use encode_token and decode_token that are acting on a token level.
"""

COMMAND_SEPARATOR = "/"
PARAMETER_SEPARATOR = "-"
ESCAPE = "~"
ESCAPE_SEQUENCES = [
    (ESCAPE, ESCAPE + ESCAPE),
    ("https://", ESCAPE + "H"),
    ("http://", ESCAPE + "h"),
    ("file://", ESCAPE + "f"),
    ("://", ESCAPE + "P"),
    (COMMAND_SEPARATOR, ESCAPE + "I"),
    (PARAMETER_SEPARATOR, ESCAPE + "_"),
    (" ", ESCAPE + "."),
]


def decode(query: str):
    """Decode query string into a list of lists of strings."""
    ql = [
        [decode_token(etoken) for etoken in eqv.split(PARAMETER_SEPARATOR)]
        for eqv in query.split(COMMAND_SEPARATOR)
    ]
    return [qcommand for qcommand in ql if len(qcommand) and len(qcommand[0])]


def encode_token(token: str):
    "Encode single token by escaping special characters and character sequences"
    for sequence, encoding in ESCAPE_SEQUENCES:
        token = token.replace(sequence, encoding)
    return quote(token).replace("%7E", "~").replace("%7e", "~")


def decode_token(token: str):
    "Decode single token by un-escaping special characters and character sequences"
    encoding = {e: s for s, e in ESCAPE_SEQUENCES}
    if token == "":
        return ""
    try:
        index = token.index(ESCAPE)
        head = token[:index]
        mid = token[index : index + 2]
        tail = token[index + 2 :]
        return unquote(head + encoding.get(mid, mid)) + decode_token(tail)
    except ValueError:
        return unquote(token)


def encode(ql: list):
    """Decode query list (list of lists of strings) into an properly escaped query string."""
    return COMMAND_SEPARATOR.join(
        PARAMETER_SEPARATOR.join(encode_token(token) for token in qv) for qv in ql
    )


def all_splits(query):
    """Make all splits of the query into two parts (biginning and remainder)
    by progressively increasing the remainder.
    query == beginning + COMMAND_SEPARATOR + remainder
    """
    ql = decode(query)
    for i in range(len(ql), -1, -1):
        yield encode(ql[:i]), encode(ql[i:])


class Position:
    def __init__(self, offset=0, line=0, column=0):
        self.offset = offset
        self.line = line
        self.column = column

    def __repr__(self):
        if self.line == 0:
            return "(unknown position)"
        elif self.line > 1:
            return f"line {self.line}, position {self.column}"
        else:
            return f"position {self.column}"


class ActionParameter(object):
    pass


class LinkActionParameter(ActionParameter):
    def __init__(self, link: str):
        self.link = link


class StringActionParameter(ActionParameter):
    def __init__(self, string: str):
        self.string = string


class ActionRequest(object):
    def __init__(self, name: str, parameters: list, position=None):
        self.name = name
        self.parameters = parameters
        self.position = position or Position()

    def encode(self):
        if len(self.parameters):
            p = "-".join(x.encode() for x in self.parameters)
            return f"{self.name}-{p}"
        else:
            return self.name


class SegmentHeader(object):
    def __init__(self, name: str, level: int, parameters: list = None, position=None):
        self.name = name
        self.level = level
        self.parameters = parameters or []
        self.position = position or Position()

    def encode(self):
        assert self.level >= 1
        encoded = "-" * self.level
        encoded += self.name
        if len(self.parameters):
            assert len(self.name) > 0
            for parameter in self.parameters:
                encoded += "-"
                encoded += parameter.encode()
        return encoded


class QuerySegment(object):
    def __init__(self, header=None, query=None):
        "header can be SegementHeader, query is a list of ActionRequest objects"
        self.header = header
        self.query = query or []

    def encode(self):
        query = "/".join(x.encode() for x in self.query)
        if self.header is None:
            return query
        else:
            if len(query):
                return self.header.encode()
            else:
                return f"{self.header.encode()}/{query}"


class Query(object):
    def __init__(self, segments: list = None):
        self.segments = segments or []

    def add_segment(self, name: str, level=1):
        qs = QuerySegment(SegmentHeader(name, level=level))
        self.segments.append(qs)
        return qs

    def encode(self):
        return "/".join(x.encode() for x in self.segments)
