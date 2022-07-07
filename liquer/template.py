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
import liquer.parser as lqp
from liquer.parser import Position



class Text(object):
    """Text element in the template AST"""
    def __init__(self, text, position=None):
        self.text = text
        self.position = position or Position()

    def encode(self):
        return self.text

    def expand(self):
        return self.encode()

    def __str__(self):
        return self.text

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.text)}, {repr(self.position)})"


class Variable(object):
    """Variable element in the template AST"""
    def __init__(self, identifier, position=None):
        self.identifier = identifier
        self.position = position or Position()

    def encode(self):
        return f"$${self.identifier}$"

    def expand(self):
        return self.encode()

    def __str__(self):
        return self.identifier

    def __repr__(self):
        return (
            f"{self.__class__.__name__}({repr(self.identifier)}, {repr(self.position)})"
        )


class Newline(Text):
    """Newline element in the template AST"""
    def __init__(self, text="\n", position=None):
        super().__init__(text, position)


class EscapeCharacter(Text):
    """Escape character element in the template AST"""
    def __init__(self, text="$", position=None):
        super().__init__(text, position)

    def encode(self):
        return "$$$"

    def expand(self):
        return {"$$$":"$","\\$":"$"}.get(self.text,"")


class Link(object):
    """Link to a query element in the template AST"""
    EXPAND = "expand"
    LINK="link"
    IMAGE="image"

    def __init__(self, query, description=None, kind="expand", position=None):
        self.query = query
        self.description = description
        self.kind = kind
        self.position = position or Position()

    def encode(self):
        assert self.kind in ("expand", "link", "image")
        if self.kind == "expand":
            return "$" + self.query.encode() + "$"
        if self.kind == "link":
            if self.description is None:
                return "$(" + self.query.encode() + ")$"
            else:
                return f"$[{self.description}](" + self.query.encode() + ")$"
        if self.kind == "image":
            return f"$![{self.description}](" + self.query.encode() + ")$"


    def expand(self):
        assert self.kind in ("expand", "link", "image")
        if self.description is not None:
            description = self.description.replace("&","&amp;").replace(">","&gt;").replace("<","&lt;")
        url = self.query.encode()
        if not url.startswith("/"):
            url="/"+url
        url="/liquer/q"+url
        if self.kind in ("expand", "link"):
            if self.description is not None:
                return f"<a href='{url}'></a>"
            else:
                return f"<a href='{url}'>{description}</a>"
        if self.kind == "image":
            return f"<img src='{url}' alt='{description}'></img>"

    def __str__(self):
        return self.encode()

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.query)},\n  description={repr(self.description)},\n  kind={repr(self.kind)},\n  position={repr(self.position)})"


identifier = Regex("[a-zA-Z_][a-zA-Z0-9_]*").setName("identifier")


def _variable_action(s, loc, toks):
    position = Position.from_loc(loc, s)
    return Variable(toks[1], position=position)


variable = (
    (Literal("$$") + identifier + Literal("$").suppress())
    .setParseAction(_variable_action)
    .setName("variable")
)


def _expand_link_action(s, loc, toks):
    position = Position.from_loc(loc, s)
    return Link(toks[1], position=position)


expand_link = (
    (Literal("$") + lqp.parse_query + Literal("$").suppress())
    .setParseAction(_expand_link_action)
    .setName("expand_link")
)


def _link_action(s, loc, toks):
    position = Position.from_loc(loc, s)
    if len(toks)==1:
        return Link(toks[0], kind=Link.LINK, position=position)
    elif len(toks)==2:
        return Link(toks[1], kind=Link.LINK, description=toks[0], position=position)
    else:
        assert toks[0] == "!"
        return Link(toks[2], kind=Link.IMAGE, description=toks[1], position=position)

link = (
    (
        Literal("$").suppress()
        + Optional(
            Optional(Literal("!")) +
            Literal("[").suppress()
            + Regex(r"[^\n^\r^\]]+").leaveWhitespace()
            + Literal("]").suppress()
        )
        + Literal("(").suppress()
        + lqp.parse_query
        + Literal(")").suppress()
        + Literal("$").suppress()
    )
    .setParseAction(_link_action)
    .setName("link")
)

text = (
    Regex(r"[^$^\n^\r]+")
    .leaveWhitespace()
    .setParseAction(
        lambda s, loc, toks: Text(toks[0], position=Position.from_loc(loc, s))
    )
    .setName("text")
)

newline = (
    Regex(r"[\n\r]")
    .leaveWhitespace()
    .setParseAction(
        lambda s, loc, toks: Newline(toks[0], position=Position.from_loc(loc, s))
    )
    .setName("newline")
)

escape_character = (
    Literal("$$$")
    .setParseAction(
        lambda s, loc, toks: EscapeCharacter(position=Position.from_loc(loc, s))
    )
    .setName("escape_character")
)

simple_item = text | variable | newline | escape_character | expand_link | link

simple_template = ZeroOrMore(simple_item)


def parse_simple(text):
    return simple_template.parseString(text, True)


if __name__ == "__main__":
    print(parse_simple("$$WORLD$"))
    print(parse_simple("Hello, $$WORLD$ !"))
    print(
        parse_simple(
            """Hello
    world"""
        )
    )
    print(
        parse_simple(
            """
    Hello, $$WORLD$ !
    Hello again...
    $$$
    $hello/link.txt$
    $-R/hello/link.txt$
    $-R/hello/-/dr/link.txt$
    """
        )
    )
    print()
    print()
    print(parse_simple("$(hello/world)$"))
    print(parse_simple("$[Hello, world!](hello/world)$"))
    print(parse_simple("$![Hello, world!](hello/world)$"))
