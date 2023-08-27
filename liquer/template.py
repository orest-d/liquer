"""Rich template engine for Liquer queries - in progress."""
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
    ParseException,
)
import liquer.parser as lqp
from liquer.parser import Position


class TemplateException(Exception):
    def __init__(self, message, source=None):
        self.message = message + ("" if link is None else f" in {source}")
        self.source = source
        super().__init__(message)

    @classmethod
    def from_parse_exception(cls, parse_exception, source=None):
        return TemplateParseException(parse_exception.explain(), source=source)


class TemplateParseException(TemplateException):
    pass


class SimpleTemplateEngine(object):
    def __init__(
        self, variables=None, expand_variables=True, variables_link=None, context=None
    ):
        self.context = context
        self.variables = variables or {}
        self.rendered_variables = {}
        self.expand_variables = expand_variables
        self.variables_link = variables_link

    def parse(self, text, source=None):
        "Parse text into a template AST. Use source for reference"
        try:
            return parse_simple(text)
        except ParseException as e:
            raise TemplateException.from_parse_exception(e, source)

    def variable_source(self, variable_name):
        "Turn variable name into source description. This will be a link if variables_link is defined."
        return (
            f"variable '{variable_name}'"
            if self.variables_link is None
            else f"$({self.variables_link}/{variable_name})$"
        )

    def check_stack(self, variable_name=None, stack=None):
        "Internal method to check stack for cyclic variables."
        if variable_name is not None:
            if stack is None:
                stack = [variable_name]
            else:
                if variable_name in stack:
                    chain = " -> ".join(stack + [variable_name])
                    raise TemplateException(
                        f"Cyclic variable expansion: {chain}",
                        source=self.variable_source(variable_name),
                    )
                stack.append(variable_name)
        return stack or []

    def get(self, variable_name, stack=None):
        "Get expanded variable value."
        if variable_name in self.rendered_variables:
            return self.rendered_variables[variable]
        if variable_name not in self.variables:
            raise TemplateException(
                f"Variable '{variable_name}' not found", source=self.variables_link
            )

        v = self.variables[variable_name]
        if self.expand_variables:
            if type(v) == str:
                v = self.parse(v, source=self.variable_source(variable_name))
            value = self.render(v, variable_name=variable_name, stack=stack)
        else:
            value = (
                v
                if type(v) == str
                else self.render(v, variable_name=variable_name, stack=stack)
            )
        self.rendered_variables[variable_name] = value
        return value

    def render(self, element, variable_name=None, stack=None):
        """Render element as text.
        Internally, variable name and stack are used to track variable expansion."""
        stack = self.check_stack(variable_name, stack)
        if type(element) == str:
            element = self.parse(element, source=self.variable_source(variable_name))

        if isinstance(element, Variable):
            return self.get(element.identifier, stack=stack)
        return element.render(self)


class Text(object):
    """Text element in the template AST"""

    def __init__(self, text, position=None):
        self.text = text
        self.position = position or Position()

    def encode(self):
        return self.text

    def render(self, engine):
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

    def render(self, engine):
        return self.encode()

    def __str__(self):
        return self.identifier

    def __repr__(self):
        return (
            f"{self.__class__.__name__}({repr(self.identifier)}, {repr(self.position)})"
        )


class Sequence(object):
    """Sequence of template elements in the template AST"""

    def __init__(self, sequence, position=None):
        self.sequence = sequence
        self.position = position or Position()

    def encode(self):
        return "".join(x.encode() for x in self.sequence)

    def render(self, engine):
        return "".join(engine.render(x) for x in self.sequence)

    def __str__(self):
        return self.encode()

    def __repr__(self):
        return (
            f"{self.__class__.__name__}({repr(self.sequence)}, {repr(self.position)})"
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

    def render(self, engine):
        return {"$$$": "$", "\\$": "$"}.get(self.text, "")


class Link(object):
    """Link to a query element in the template AST"""

    EXPAND = "expand"
    LINK = "link"
    IMAGE = "image"

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

    def render(self, engine):
        assert self.kind in ("expand", "link", "image")
        if self.description is not None:
            description = (
                self.description.replace("&", "&amp;")
                .replace(">", "&gt;")
                .replace("<", "&lt;")
            )
        else:
            description = self.query.encode()
        url = self.query.encode()
        if not url.startswith("/"):
            url = "/" + url
        url = "/liquer/q" + url
        if self.kind in ("expand", "link"):
            if self.description is None:
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
    if len(toks) == 1:
        return Link(toks[0], kind=Link.LINK, position=position)
    elif len(toks) == 2:
        return Link(toks[1], kind=Link.LINK, description=toks[0], position=position)
    else:
        assert toks[0] == "!"
        return Link(toks[2], kind=Link.IMAGE, description=toks[1], position=position)


link = (
    (
        Literal("$").suppress()
        + Optional(
            Optional(Literal("!"))
            + Literal("[").suppress()
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

simple_template = (
    ZeroOrMore(simple_item)
    .setParseAction(
        lambda s, loc, toks: Sequence(list(toks), position=Position.from_loc(loc, s))
    )
    .setName("simple_template")
)


def parse_simple(text):
    return simple_template.parseString(text, True)[0]


def expand_simple(
    text, variables=None, expand_variables=True, variables_link=None, context=None
):
    return SimpleTemplateEngine(
        variables=variables,
        expand_variables=expand_variables,
        variables_link=variables_link,
        context=context,
    ).render(text)


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
    x = parse_simple(
        """$![Hello, world!]
    (
        /hello
        /world
          - 1
          - abc
        /out.txt
    )$"""
    )
    print(repr(x))
    print(x.encode())

    print(SimpleTemplateEngine().render(x))
    print()
    print("*************************")
    print()

    print(
        SimpleTemplateEngine(dict(WORLD="$[world](link/to/world)$")).render(
            "Hello, $$WORLD$!"
        )
    )
