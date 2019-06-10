# Welcome to LiQuer

LiQuer is a leightweighted framework that can turn your python functions into
a web service with just a couple of lines of code.
In fact just one line. A very short line... 
OK, I am not that good at lying: You will need a small start script and some import statements.)

LiQuer is a flexible tool targeted at data scientists, that allows to represent and evaluate
a sequence of transformations (actions, or in LiQuer lingo "commands") as a query string,
which can be a part of URL. For example: if you would like to read a csv file, filter it,
expose it a xlsx or make a chart out of it, cache it and make all that awailable as a web service - LiQuer does all this out of the box.

But when it is not supported out of the box ... that's where LiQuer really shines!
LiQuer is designed to make it very easy - even when you are not an expert on web application development.

  
LiQuer tries to find a sweet spot by considering these values:
- simple things very simple, complex things possible (convention over configuration)
- modularity and extensibility (it should be possible to override or change anything - within reason)
- technology neutral (limit necessary dependencies, decide what packages you want to use)
- feature completeness (Most important features should be supported out of the box - but they need to be enabled to keep neutrality.)


## Hello, world!

The good tradition is to start with a Hello, world! example:

```
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

