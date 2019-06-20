# Welcome to LiQuer

LiQuer is a leightweighted framework that turns ordinary python functions into
a flexible web service with just a couple of lines of code.
In fact just one line. A very short line... 

OK, this not exactly true: yes, to make a function available as a web service,
you just need to use a simple decorator (``@command`` or perhaps ``@first_command``),
but there have to be as well some import statements and a little code (which you can copy and paste from examples)
to configure and start flask.

LiQuer is a flexible tool targeted at data scientists, helping to create web applications
working with manupulating tables (or other data), creating charts, images, reports or interactive applications.
The core of Liquer is a small query language, which represents 
a sequence of transformations (or "commands") as a string safe to use as a part of URL.

For example: if you would like to read a csv file, filter it,
expose it a xlsx or make a chart out of it, cache it and make all that awailable as a web service - LiQuer does all this out of the box.

And when it is not supported out of the box ... that's where LiQuer really shines!
LiQuer is designed to make web-services very easy - even when you are not an expert on web application development.

LiQuer tries to find a sweet among these values:
- simple things simple, complex things possible (convention over configuration)
- modularity and extensibility (it should be possible to override or change anything - within reason)
- technology neutral (limit necessary dependencies, decide what packages you want to use)
- feature completeness (Most important features should be supported out of the box - but they need to be enabled to keep neutrality.)
- safety should be achievable

LiQuer sorce is [here](https://github.com/orest-d/liquer)

## Hello, world!

Let's start with a Hello, world! example:

```python
from liquer import *

@first_command
def hello():
    return "Hello"

@command
def greet(greeting, who="world"):
    return f"{greeting}, {who}!"

print (evaluate("hello/greet").get())
print (evaluate("hello/greet-everybody").get())
```

What is happening here? There are two functions: ``hello`` and ``greet``.
Both of them are turned into "commands" with the decorators (``@first_command`` and ``@command``).
This means, that they are "published" and can be called via a web interface.
To make the example simple, we just call them by calling ``evaluate``.
Evaluate accepts a LiQuer query, which consists out of a chain of slash-separated commands;
output of each command becomes an input of a next command.
Hence ``@first_command``: a command first in the chain that does not need any input from
a previous command.

For example ``hello/greet`` calls function hello() and then passes the return value as a
first argument of greet - i.e. ``hello/greet`` is equivalent to ``greet(hello())``.

Commands can as well pass arguments to the functions, which are dash-separated,
i.e. ``hello/greet-everybody`` query is equivalent to python expression ``greet(hello(), "everybody")``.
This way multiple function calls can be combined in a single query, which may combine
data fetching, filters, various analysis/calculations with parameters and visualizations.

Of course, the arguments must be represented as strings in the query. LiQuer takes care of
proper escaping and type conversion.
The result of the query returned by ``evaluate`` is wrapped in a ``State`` object.
``State`` object contains various metadata useful for debugging and tracking the data source - e.g. the query itself.

