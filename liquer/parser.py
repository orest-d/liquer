from urllib.parse import quote, unquote
import re
from pyparsing import (
    Literal,
    Word,
    alphas,
    alphanums,
    nums,
    delimitedList,
    Regex,
    OneOrMore,
    Group,
    Combine,
    ZeroOrMore,
    Optional,
    Forward,
    lineno,
    col,
    FollowedBy,
)

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


def indent(text, prefix="  "):
    return "\n".join(prefix + x for x in text.split("\n"))


def list_indent(lst, prefix="  "):
    if len(lst):
        return "[\n" + ",\n".join(indent(repr(x), prefix) for x in lst) + "\n]"
    else:
        return "[]"


class Position:
    def __init__(self, offset=0, line=0, column=0):
        self.offset = offset
        self.line = line
        self.column = column

    @classmethod
    def from_loc(cls, loc, string):
        return cls(loc, line=lineno(loc, string), column=col(loc, string))

    @classmethod
    def from_dict(cls, d):
        if d is None:
            return cls()
        else:
            return cls(offset=d["offset"], line=d["line"], column=d["column"])

    def to_dict(self):
        return dict(offset=self.offset, line=self.line, column=self.column)

    def __str__(self):
        if self.line == 0:
            return "(unknown position)"
        elif self.line > 1:
            return f"line {self.line}, position {self.column}"
        else:
            return f"position {self.column}"

    def __repr__(self):
        if self.line == 0:
            return "Position()"
        return f"Position(offset={self.offset}, line={self.line}, column={self.column})"


class QueryException(Exception):
    def __init__(self, message, position=None, query=None):
        self.original_message = message
        if position is not None:
            message += f" at {position}"
            if query is not None:
                message += f":\n  query: {query[:position.offset]}\n     {' '*position.offset}--> {query[position.offset:]}"
        else:
            if query is not None:
                message += f":\n  query: {query}"

        super().__init__(message)
        self.position = position
        self.query = query


class ActionParameter(object):
    def __init__(self, position=None):
        self.position = position or Position()

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.position)})"

    def __str__(self):
        return f"{self.__class__.__name__} at {self.position}"


class LinkActionParameter(ActionParameter):
    def __init__(self, link, position=None):
        super().__init__(position)
        self.link = link

    def encode(self):
        return "~X~" + self.link.encode() + "~E"

    def __repr__(self):
        return f"""LinkActionParameter(
{indent(repr(self.link))},
  {repr(self.position)})"""

    def __str__(self):
        return self.encode()


class ExpandedActionParameter(ActionParameter):
    def __init__(self, value, link, position=None):
        super().__init__(position)
        self.value = value
        self.link = link

    def encode(self):
        return "~X~" + self.link.encode() + "~E"

    def __repr__(self):
        return f"""ExpandedActionParameter(
{indent(repr(self.value))}
{indent(repr(self.link))},
  {repr(self.position)})"""

    def __str__(self):
        return str(self.value)


class StringActionParameter(ActionParameter):
    def __init__(self, string: str, position=None):
        super().__init__(position)
        self.string = string

    def encode(self):
        #        encoded = self.string.replace("~","~~").replace("/","~/").replace("://","~P")
        encoded = encode_token(self.string)
        return encoded

    def __repr__(self):
        return f"StringActionParameter({repr(self.string)}, {repr(self.position)})"

    def __str__(self):
        return self.string


class ResourceName(ActionParameter):
    def __init__(self, name: str, position=None):
        self.position = position or Position()
        self.name = name

    def encode(self):
        return self.name

    def __repr__(self):
        return f"ResourceName({repr(self.name)}, {repr(self.position)})"

    def __str__(self):
        return self.encode()


class ActionRequest(object):
    def __init__(self, name: str, parameters=None, position=None):
        self.name = name
        self.parameters = [] if parameters is None else parameters
        self.position = position or Position()

    @classmethod
    def from_arguments(cls, name: str, *parameters):
        assert type(name) == str
        typedparam = []
        for p in parameters:
            if isinstance(p, ActionParameter):
                typedparam.append(p)
            else:
                assert type(p) in (str, int, float, bool)
                typedparam.append(StringActionParameter(str(p)))

        return cls(name, typedparam)

    def to_list(self):
        lst = [self.name]
        for x in self.parameters:
            if isinstance(x, StringActionParameter):
                lst.append(x.string)
            elif isinstance(x, LinkActionParameter):
                lst.append(x.encode())
            else:
                raise Exception(
                    f"Unsupported action parameter type: {type(x)} ({repr(x)})"
                )
        return lst

    @classmethod
    def from_list(cls, lst):
        return cls.from_arguments(lst[0], *lst[1:])

    def encode(self):
        if len(self.parameters):
            p = "-".join(x.encode() for x in self.parameters)
            return f"{self.name}-{p}"
        else:
            return self.name

    def __repr__(self):
        return f"""ActionRequest(
  {repr(self.name)},
{indent(list_indent(self.parameters))},
  {repr(self.position)}
)"""

    def __str__(self):
        return self.encode()


class SegmentHeader(object):
    def __init__(
        self,
        name: str = "",
        level: int = 1,
        parameters: list = None,
        resource: bool = False,
        position=None,
    ):
        self.name = name
        self.level = level
        self.parameters = parameters or []
        self.resource = resource
        self.position = position or Position()

    def encode(self):
        assert self.level >= 1
        encoded = "-" * self.level
        if self.resource:
            encoded += "R"
        encoded += self.name
        if len(self.parameters):
            assert len(self.name) > 0 or self.resource
            for parameter in self.parameters:
                encoded += "-"
                encoded += parameter.encode()
        return encoded

    def __repr__(self):
        return f"""SegmentHeader(
  name       ={repr(self.name)},
  level      ={self.level},
  parameters ={indent(list_indent(self.parameters))},
  resource   ={self.resource},
  position   ={repr(self.position)}
)"""

    def __str__(self):
        return self.encode()


class TransformQuerySegment(object):
    def __init__(self, header=None, query=None, filename=None):
        "header can be SegmentHeader, query is a list of ActionRequest objects"
        self.header = header
        self.query = query or []
        self.filename = filename

    def predecessor(self):
        if self.filename is None:
            if len(self.query):
                p = TransformQuerySegment(
                    header=self.header, query=self.query[:-1], filename=None
                )
                r = TransformQuerySegment(
                    header=self.header, query=[self.query[-1]], filename=None
                )
                return p, r
            else:
                return None, None
        else:
            p = TransformQuerySegment(
                header=self.header, query=self.query, filename=None
            )
            r = TransformQuerySegment(
                header=self.header, query=[], filename=self.filename
            )
            return p, r

    def is_empty(self):
        return len(self.query) == 0 and self.filename is None

    def is_filename(self):
        return len(self.query) == 0 and self.filename is not None

    def is_action_request(self):
        return len(self.query) == 1 and self.filename is None

    def action(self):
        if self.is_action_request():
            return self.query[0]
        else:
            return None

    def encode(self):
        query = "/".join(x.encode() for x in self.query)
        if self.filename is not None:
            query = f"{query}/{self.filename}" if len(query) else self.filename

        if self.header is None:
            return query
        else:
            if len(query):
                return f"{self.header.encode()}/{query}"
            else:
                return self.header.encode()

    def append(self, q):
        if q is None:
            return self
        if isinstance(q, TransformQuerySegment):
            self.query.extend(q.query)
            self.filename = q.filename
            return self
        if isinstance(q, Query):
            if q.is_transform_query():
                return self.append(q.segments[0])
            else:
                raise Exception(
                    f"Appending general query {q} to transform query {self.encode()} not supported"
                )
        if isinstance(q, ActionRequest):
            self.query.append(q)
            return self
        if isinstance(q, str):
            return self.append(parse(q))

        raise Exception(
            f"Transform query {self.encode()} can't append object {repr(q)}"
        )

    def __add__(self, q):
        if q is None:
            return self
        if isinstance(q, TransformQuerySegment):
            return TransformQuerySegment(
                header=self.header, query=self.query + q.query, filename=q.filename
            )

        raise Exception(f"Unsupported operation (add): {self.encode()} + {repr(q)}")

    def __radd__(self, q):
        if q is None:
            return self
        if isinstance(q, TransformQuerySegment):
            return q + self
        raise Exception(f"Unsupported operation (radd): {repr(q)} + {self.encode()}")

    def __repr__(self):
        return f"""TransformQuerySegment(
  header   = {indent(repr(self.header))},
  query    = {indent(list_indent(self.query))},
  filename = {repr(self.filename)}
)"""

    def __str__(self):
        return self.encode()


class ResourceQuerySegment(object):
    def __init__(self, header=None, query=None):
        "header can be SegmentHeader, query is a list of ActionRequest objects"
        self.header = header
        self.query = query or []

    @property
    def position(self):
        if self.header is not None:
            return self.header.position
        else:
            if len(self.query):
                return self.query[0].position

    def path(self):
        return "/".join(x.encode() for x in self.query)

    def encode(self):
        query = self.path()
        if self.header is None:
            rqs = ""
        else:
            rqs = self.header.encode()
        if len(rqs):
            rqs += "/"
        if len(query):
            return f"{rqs}{query}"
        else:
            return rqs

    def __repr__(self):
        return f"""ResourceQuerySegment(
  header = {indent(repr(self.header))},
  query  = {indent(list_indent(self.query))}
)"""

    def __str__(self):
        return self.encode()


class Query(object):
    def __init__(self, segments: list = None, absolute=False):
        self.segments = segments or []
        self.absolute = absolute

    def filename(self):
        if len(self.segments):
            segment = self.segments[-1]
            if (
                isinstance(segment, TransformQuerySegment)
                and segment.filename is not None
            ):
                return str(segment.filename)
            if (
                isinstance(segment, ResourceQuerySegment)
                and segment.query is not None
                and len(segment.query)
            ):
                return str(segment.query[-1])
        return None

    def extension(self):
        filename = self.filename()
        if filename is not None:
            v = filename.split(".")
            if len(v)>1:
                return v[-1]
        return None
    def is_empty(self):
        return len(self.segments) == 0

    def is_transform_query(self):
        return len(self.segments) == 1 and isinstance(
            self.segments[0], TransformQuerySegment
        )

    def transform_query(self):
        if self.is_transform_query():
            return self.segments[0]
        else:
            return None

    def is_resource_query(self):
        return len(self.segments) == 1 and isinstance(
            self.segments[0], ResourceQuerySegment
        )

    def resource_query(self):
        if self.is_resource_query():
            return self.segments[0]
        else:
            return None

    def is_action_request(self):
        return self.is_transform_query() and self.segments[0].is_action_request()

    def action(self):
        if self.is_action_request():
            return self.segments[0].action()
        else:
            return None

    def predecessor(self):
        if len(self.segments):
            if isinstance(self.segments[-1], TransformQuerySegment):
                p, r = self.segments[-1].predecessor()
                if p is None or p.is_empty():
                    qp = Query(self.segments[:-1], absolute=self.absolute)
                    qr = r
                    return qp, qr
                else:
                    qp = Query(self.segments[:-1] + [p], absolute=self.absolute)
                    qr = r
                    return qp, qr
            else:
                return None, None
        else:
            return None, None

    def short(self):
        _, r = self.predecessor()
        if r is None:
            q = str(self)
            if len(self) > 30:
                q = "..." + q[-30:]
            return q
        else:
            return str(r)

    def all_predecessors(self):
        qp, qr = self, None
        while qp is not None:
            yield qp, qr
            qp, r = qp.predecessor()
            qr = r + qr

    def create_segment(self, name: str = "", level=1):
        qs = TransformQuerySegment(SegmentHeader(name, level=level))
        self.segments.append(qs)
        return qs

    def last_transform_query_segment(self):
        if not self.is_empty():
            if isinstance(self.segments[-1], TransformQuerySegment):
                return self.segments[-1]
        return self.create_segment()

    def with_action(self, name: str, *parameters):
        self.last_transform_query_segment().append(
            ActionRequest.from_arguments(name, *parameters)
        )
        return self

    def __add__(self, tq):
        assert isinstance(tq, TransformQuerySegment)
        return Query(self.segments + [tq], absolute=self.absolute)

    def encode(self):
        return ("/" if self.absolute else "") + "/".join(
            x.encode() for x in self.segments
        )

    def __repr__(self):
        return f"""Query(
{indent(list_indent(self.segments))},
  absolute = {self.absolute}
)"""

    def __str__(self):
        return self.encode()


identifier = Regex("[a-z_][a-zA-Z0-9_]*").setName("identifier")
filename = Regex(r"[a-zA-Z0-9_]*\.[a-zA-Z0-9._-]*").setName("filename")


def _resource_name_parse_action(s, loc, toks):
    position = Position.from_loc(loc, s)
    name = unquote("".join(toks))
    return ResourceName(name, position=position)


resource_name = (
    Regex(r"[a-zA-Z0-9._][a-zA-Z0-9._-]*")
    .setParseAction(_resource_name_parse_action)
    .setName("resource_name")
)
parameter_text = Regex("[a-zA-Z0-9_+.]+").setName("parameter_text")
percent_encoding = Regex("%[0-9a-fA-F][0-9a-fA-F]").setName("percent_encoding")
parse_query = Forward()

tilde_entity = (
    Literal("~~").setParseAction(lambda s, loc, toks: ["~"]).setName("tilde_entity")
)
minus_entity = (
    Literal("~_").setParseAction(lambda s, loc, toks: ["-"]).setName("minus_entity")
)
islash_entity = (
    Literal("~I").setParseAction(lambda s, loc, toks: ["/"]).setName("islash_entity")
)
slash_entity = (
    Literal("~/").setParseAction(lambda s, loc, toks: ["/"]).setName("slash_entity")
)

https_entity = (
    Literal("~H")
    .setParseAction(lambda s, loc, toks: ["https://"])
    .setName("https_entity")
)
http_entity = (
    Literal("~h")
    .setParseAction(lambda s, loc, toks: ["http://"])
    .setName("http_entity")
)
file_entity = (
    Literal("~f")
    .setParseAction(lambda s, loc, toks: ["file://"])
    .setName("file_entity")
)
protocol_entity = (
    Literal("~P")
    .setParseAction(lambda s, loc, toks: ["://"])
    .setName("protocol_entity")
)

negative_number_entity = (
    Regex("~[0-9]")
    .setParseAction(lambda s, loc, toks: ["-" + toks[0][1:]])
    .setName("negative_number_entity")
)
space_entity = (
    Literal("~.").setParseAction(lambda s, loc, toks: [" "]).setName("space_entity")
)
end_entity = Literal("~E")


def _expand_entity_parse_action(s, loc, toks):
    position = Position.from_loc(loc, s)
    return LinkActionParameter(toks[0], position=position)


expand_entity = (
    (Literal("~X~").suppress() + parse_query + end_entity.suppress())
    .setParseAction(_expand_entity_parse_action)
    .setName("expand_entity")
)

entities = (
    tilde_entity
    | minus_entity
    | negative_number_entity
    | space_entity
    | islash_entity
    | slash_entity
    | http_entity
    | https_entity
    | file_entity
    | protocol_entity
)


def _parameter_parse_action(s, loc, toks):
    position = Position.from_loc(loc, s)
    par = unquote("".join(toks))
    return StringActionParameter(par, position=position)


parameter = expand_entity | (
    ZeroOrMore(parameter_text | entities | percent_encoding)
    .setParseAction(_parameter_parse_action)
    .setName("parameter")
)


def _action_request_parse_action(s, loc, toks):
    position = Position.from_loc(loc, s)
    name = toks[0]
    parameters = list(toks[1:])
    return ActionRequest(name=name, parameters=parameters, position=position)


action_request = (
    (identifier + ZeroOrMore(Literal("-").suppress() + parameter))
    .setParseAction(_action_request_parse_action)
    .setName("action_request")
)


def _action_path_parse_action(s, loc, toks):
    ap = list(toks)
    if type(ap[-1]) is str:
        return (ap[:-1], ap[-1])
    else:
        return (ap, None)


# segment_indicator = (
#    OneOrMore(Literal("-"))
#    .setParseAction(lambda s, loc, toks: len(toks))
#    .setName("segment_indicator")
# )


def _segment_identifier_action(s, loc, toks):
    m = re.match("(-+)([a-zA-Z0-9_]*)", toks[0])
    assert m is not None
    return len(m.group(1)), m.group(2)


segment_identifier = (
    (Regex("-+[a-z][a-zA-Z0-9_]*") | (Regex("-+") + FollowedBy("/")))
    .setParseAction(_segment_identifier_action)
    .setName("segment_identifier")
)


def _resource_identifier_action(s, loc, toks):
    m = re.match("(-+)R([a-zA-Z0-9_]*)", toks[0])
    assert m is not None
    return len(m.group(1)), m.group(2)


resource_identifier = (
    (Regex("-+R[a-zA-Z0-9_]*"))
    .setParseAction(_resource_identifier_action)
    .setName("resource_identifier")
)

action_path_nonempty = (
    (
        (
            ZeroOrMore(
                action_request
                + (
                    Literal("/") + ~(resource_identifier | segment_identifier)
                ).suppress()
            )
            + (filename | action_request)
        )
    )
    .setParseAction(_action_path_parse_action)
    .setName("action_path_nonempty")
)


def _resource_path_parse_action(s, loc, toks):
    return list(toks)


resource_path = (
    delimitedList(resource_name, delim="/")
    .setParseAction(_resource_path_parse_action)
    .setName("resource_path")
)


def _segment_header_parse_action(s, loc, toks):
    position = Position.from_loc(loc, s)
    level, name = toks[0]
    if len(toks) > 1:
        parameters = list(toks[1:])
        return SegmentHeader(
            name=name, level=level, parameters=parameters, position=position
        )
    else:
        return SegmentHeader(level=level, name=name)


segment_header = (
    (segment_identifier + ZeroOrMore(Literal("-").suppress() + parameter))
    .setParseAction(_segment_header_parse_action)
    .setName("segment_header")
)


def _resource_segment_with_header_parse_action(s, loc, toks):
    position = Position.from_loc(loc, s)
    level, name = toks[0]
    header = SegmentHeader(
        name=name,
        level=level,
        parameters=list(toks[1]),
        resource=True,
        position=position,
    )
    if len(toks) == 3:
        return ResourceQuerySegment(header=header, query=list(toks[2]))
    else:
        return ResourceQuerySegment(header=header, query=[])


resource_segment_with_header = (
    (
        resource_identifier
        + Group(ZeroOrMore(Word("-").suppress() + parameter))
        + Literal("/").suppress()
        + Optional(Group(resource_path))
    )
    .setParseAction(_resource_segment_with_header_parse_action)
    .setName("resource_segment_with_header")
)


def _segment_with_header_parse_action(s, loc, toks):
    if len(toks) == 1:
        return TransformQuerySegment(header=toks[0])
    else:
        assert len(toks) == 3
        return TransformQuerySegment(
            header=toks[0], query=toks[2][0][0], filename=toks[2][0][1]
        )


segment_with_header = (
    (segment_header + Optional(Literal("/") + Group(action_path_nonempty)))
    .setParseAction(_segment_with_header_parse_action)
    .setName("segment_with_header")
)


def _segment_without_header_parse_action(s, loc, toks):
    return TransformQuerySegment(query=list(toks[0][0][0]), filename=toks[0][0][1])


segment_without_header = (
    Group(action_path_nonempty)
    .setParseAction(_segment_without_header_parse_action)
    .setName("segment_without_header")
)

query_segment = (
    segment_with_header | segment_without_header | resource_segment_with_header
).setName("query_segment")


def _parse_query_parse_action(s, loc, toks):
    if toks[0] == "/":
        return Query(segments=list(toks[1:]), absolute=True)
    else:
        return Query(segments=list(toks), absolute=False)


parse_query << (
    (Optional(Literal("/")) + delimitedList(query_segment, "/"))
    .setParseAction(_parse_query_parse_action)
    .setName("parse_query")
)


def _resource_transform_query_action(s, loc, toks):
    if toks[0] == "/":
        assert len(toks) == 3
        resource = ResourceQuerySegment(query=list(toks[1]))
        transform = toks[2]
        return Query(segments=[resource, transform], absolute=True)
    else:
        assert len(toks) == 2
        resource = ResourceQuerySegment(query=list(toks[0]))
        transform = toks[1]
        return Query(segments=[resource, transform], absolute=False)


resource_transform_query = (
    (
        Optional(Literal("/"))
        + Group(resource_path)
        + Literal("/").suppress()
        + segment_with_header
    )
    .setParseAction(_resource_transform_query_action)
    .setName("resource_transform_query")
)


def parse(query):
    try:
        return resource_transform_query.parseString(query, True)[0]
    except:
        return parse_query.parseString(query, True)[0]


if __name__ == "__main__":
    #    print(action_path_nonempty.parseString("abc/def/file.txt", True))
    #    print(query_segment.parseString("abc/def/file.txt", True))
    # print(resource_path.parseString("abc/def/file.txt", True))
    #    print(query_segment.parseString("-qs/abc/def/file.txt", True))
    #    print(parse_query.parseString("abc/def/file.txt", True))
    #    print(parse_query.parseString("-/abc/def/file.txt", True))
    #    print(parse_query.parseString("-qs/abc/def/file.txt", True))
    #    print(parse_query.parseString("-/xxx", True))
    #    print(parse_query.parseString("abc/def/-/xxx", True))
    #    print(parse_query.parseString("abc/def/-/xxx/file.txt", True))
    #    print(repr(parse("abc/def/-/xxx/file.txt")))
    #    print(repr(parse("abc/def")))

    #    print(parse("abc-def/-/x-y/--xxx-y/aaa"))
    #    print(repr(parse("/abc-def/-/x-y/--xxx-y/aaa")))
    #    print(resource_segment_with_header.parseString("-R/abc/def"))
    # print(resource_segment_with_header.parseString("-R-1-2/"))
    print(repr(parse("-R/abc/def/-/ghi")))
    print((parse("-R/abc/def/-/ghi")))
    print()
    for p, r in parse("-R/abc/def/-/ghi/jkl/file.txt").all_predecessors():
        print(p.encode(), "   -   ", "NONE" if r is None else r.encode())
    #    print(parse("abc/xxx/-/def"))
    #    print(repr(parse("-/def")))
    #    print(repr(parse("def")))
    #    print(repr(action_path_nonempty.parseString("abc", True)))
    #    print(repr(expand_entity.parseString("~X~abc~E", True)))
    #    print(repr(parse("-/def-~X~abc~E")))
    print(parse("abc/def/-/xxx/-q/qqq"))
    print(parse("abc/def/-/xxx/-q/qqq-abc-~X~xxx/yyy~E-def"))
    print(repr(parse("abc/def/-/xxx/-q/qqq-abc-~X~xxx/yyy~E-def")))
