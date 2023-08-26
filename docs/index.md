# Welcome to LiQuer

LiQuer is a leightweighted open-source framework (see [repo](https://github.com/orest-d/liquer) )
covering a large number of usecases
associated with machine learning, data science and other computational experimentation tasks
requiring flexible analysis.

LiQuer is a versatile tool - it helps to create interactive dashboards and web applications,
working with tables, creating charts, images, reports - but as well non-interactive batch processes.
The core of Liquer is a minimalistic query language, that represents 
a sequence of actions as a compact (but still human readable) string, or as URL "link".
(Hence the name Link Query.) The second pillar of LiQuer is metadata: LiQuer always keeps track of metadata associated with the data.
LiQuer queries can
* execute interactively in a browser,
* execute non-interactively in a batch,
* referenced in reports,
* efficiently cache the final and intermediate results,
* improve the transparency, traceability and discoverability by the use of metadata - and more.

Design of LiQuer is guided by the following principles:

* **Simplicity and flexibility** - Make simple things simple, complex things possible.
* **Batteries included** - Provide useful features and integration of 3rd party libraries out of the box in a modular way.
* **Don't stand in the way - collaborate!** - Do not force one way of doing things. Be technology neutral and integrate well 
with other libraries and frameworks. LiQuer-enabled code should run as well without the framework and thus using LiQuer should be low risk in terms of dependencies. Make all parts modular, replaceable and customizable.

**LiQuer is extremely easy to use** - just decorate ordinary python functions with a simple decorator.
LiQuer provides integration of essential data-science tools like Pandas, Scikit-Learn and Keras without having a hard dependency on these frameworks - you need them only when you are going to use them.
LiQuer's main web-framework is Flask (because of its simplicity), but other frameworks can easily be supported (there is a basic Tornado support available, others will follow as needed).

LiQuer enabled code can be used (in most cases) exactly the same way as if LiQuer would not be there - so no LiQuer knowledge is needed to use your code.
That makes it easy for newcommers to use the existing code, but as well start quickly contributing to a LiQuer-enabled code base.

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

To learn more, please continue to the [user guide](guide.md).