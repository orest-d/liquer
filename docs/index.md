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


## Three use-cases + two more
LiQuer was born from three quite different use-cases:
* When preparing the presentation on a larger demographics dataset, we have had many questions in mind: What if we show the results ony for the students? How is the geographic distribution? How is the geographics distribution of students? Can we show it graphically? Can we see the raw data in a spreadsheet? The questions started to multiply. There were too many questions to prepare a slide for each possibility and the Jupyter notebooks were too technical for the end-users. We needed to have some interface flexible enough to express all these demands in a simple form...
* We have been contributing to a large effort of consolidating data scraped from multiple sources. This has been usually performed by batch jobs, sometimes by specialized proxies. Proxy approach seems very promissing - data is fresh, on demand and there is no trouble with batch job monitoring - but proxies are not simple to construct. If only there would be a way how to make a flexible universal proxy, that would support tasks like filtering, basic processing and some visualization...
* When preparing an implementation of an important complex machine learning model in production, many questions about model reliability, expected performance, monitoring and ethical concerns have been raised. We have been producing report after report, presentation after presentation and we needed to document all the aspects of the model development in a concise,  transparent and reproducible way. A single data scientist can perform several analytic tasks a day - and a small team can easily create several hundreds of artefacts (reports, charts, data sets, numerical experiments) per month. It is very easy to loose track of what exactly has been done and how. It is difficult to refer to all those calculations and document them in such a way that they can be reproduced: it is not practical to have several hundred scripts and/or document several hundred ways of how the scripts can be configured. If there only would be a way to represent all those calculations in a concise way - and possibly refer to them via URLs...

After LiQuer was created, there appered more and more ways how to use it:
* Data scientists often store intermediate results to accelerate the development. LiQuer provides two natural ingrediences for a cache: a) each step of the pipeline has a natural key and b) each result has a defined way how to deal with serialization (which format to use or whether the data is serializable at all). Metadata can be used to control the caching mechanism - e.g. prevent caching of sensitive data to support GDPR compliance.
* Metadata allow discoverability and traceability of all the artefacts - all data sets, filters and reports can be equipped with tags and searchable from an user interface. This can be a big help for knowledge sharing. Data can be (in somo cases automatically) equipped with supplementary informations like required access rights, persons to contact, pointers to source code or SQL queries.


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
In this example, we just call them via the ``evaluate`` function.
Evaluate accepts a LiQuer query, which consists out of a chain of slash-separated commands;
output of each command becomes an input of a next command.

What is at the beginning of the chain? As you might have guessed, it is *None*.
However, to avoid passing meaningless arguments - and to highlight that some commands are meant to be "the first command" in the pipeline, there is the ``@first_command`` decorator. The only difference between the ``@first_command`` and ``@command``
if that the ``@first_command`` does not get the first argument from the previous step. (If such a command appears in the middle of a query, the query before the first_command is effectively ignored.)

The complete query ``hello/greet`` calls function hello() and then passes the return value as a
first argument of greet - i.e. ``hello/greet`` is equivalent to ``greet(hello())``.

Commands can as well pass arguments to the functions, which are dash-separated,
i.e. ``hello/greet-everybody`` query is equivalent to python expression ``greet(hello(), "everybody")``.
This way multiple function calls can be combined in a single query, which may combine
data fetching, filters, various analysis/calculations with parameters and visualizations.

Of course, the arguments must be represented as strings in the query. LiQuer takes care of
proper escaping and type conversion.

LiQuer always keeps track of the metadata associated with the data.
Metadata contain various supplementary data useful e.g. for debugging and tracking the data source - e.g. the query itself.
Metadata can be enhanced by the user in several ways.

The combination of data and metadata is the ``State`` object. The ``State`` object is as well returned by ``evaluate``.
The main payload (the "data") is extracted from ``State`` using the ``get()`` method.
