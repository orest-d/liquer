# Overview

LiQuer has multiple concepts which will be explained, following its natural order,
intervened with practical examples.

This is a list of topics - currently work in progress.
First part should give a relatively fast introduction to the subject,
is followed by more in-depth "advanced topics": 

Guide:
- Installation (PARTLY DONE)
- Basic introduction into forming queries and how to execute them. (PARTLY DONE)
- Introduction to the store - files in the query. (TBD)
- Introduction to recipes - organizing pipelines (TBD)
- CLI, server, web applications and tools (TBD)
- A littlebit more about commands: context, logging, modules and namespaces (TBD)
- Caching - what is cache, cleaning cache, no_cache and volatile commands, iterators (TBD) 
- Working with data-frames: pandas and polars (TBD)
- Charts with matplotlib and plotly (TBD)
- Creating reports with templates (TBD)
- Machine learning (TBD)
- Dependencies (not implemented yet) (TBD)

Advanced topics:
- Query in detail (TBD)
- Indexing - supporting web tools and search engines (TBD)
- Writing support for existing libraries, defining own state types (TBD)
- Implementing own store (TBD)
- Implementing own cache (TBD)
- Implementing own recipe interpreter (TBD)
- Server component and integration with an existing web application (TBD)
- Pool - parallel execution of queries (TBD)
- Config presets (TBD)
- Implementing reusable web-based tools (TBD)
- Web service specification (TBD)
- Commands in depth, command registry and remote command registration (TBD)

# Instalation

LiQuer requires (at minimum) python 3.6 with flask. It can be installed by
```
python3 -m pip install liquer-framework
```

Alternatively you can get LiQuer from [repository](https://github.com/orest-d/liquer):

```
git clone https://github.com/orest-d/liquer.git

python3 -m venv venv
source venv/bin/activate
cd liquer
python3 setup.py install
```

TBD: install further dependencies

# Getting started

The good tradition is starting with a *Hello, world!* example:

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

In this example we first create to *commands* - *hello* and *greet*.
Commands are ordinary python functions decorated with
either ```@first_command``` or ```@command```.

A sequence of commands can be written as a *link query*
(the main concept of LiQuer).
Simple query is a sequence of actions (commands with parameters) separated by *slash* ("/").
A query is evaluated from left to right,
always passing the output as a first argument to the next action.
For example the query ```hello/greet```
is roughly equivalent to evaluating

```python
greet(hello())
```

Query ```hello/greet-everybody``` (in the end of the example) is equivalent
to

```python
greet(hello(), "everybody")
```

Here we specify the second argument to the function greet
in the query. the arguments are separated by dash ("-").
(This choice might look unusual, but it allows using such a *query*
as a part of [URL](https://en.wikipedia.org/wiki/URL).

(Link query syntax requires treating "/" and "-" as special characters
and escape them when needed - as we will explain in the [query](query.md) chapter.

*If the actions are always passing the result into the next action,
what is passed into the very first action?*

The very first action in the pipeline will not receive anything as a first
argument (more precisely, it will receive ```None```).
To avoid having such a useless
argument in commands that are used at the beginning of the query,
(in our example the ```hello``` function), we can use the
decorator ```@first_command``` instead of ```@command```.
This is more a convenience than necessity though.
Commands and actions are explained in [this chapter](commands.md)

Queries can be executed in multiple ways in LiQuer
(programatically from scripts or commands,
from recipes/batch jobs or interactively from a web API).
In this example we just evaluate them in the script by the ```evaluate```
function. 

# What did we actually gain?
*Link query* syntax allows to represent pipelines as short strings.
More importantly, *link query* can be used as
a path part of the [URL](https://en.wikipedia.org/wiki/URL).
Unlike the more conventional web services typically a separate request
for each action, *link query* can specify
sequences of actions (pipelines) in the URL.
This gives LiQuer an incredible amount of  flexibility and expressiveness.

LiQuer has a well-defined [web service API](web_service.md)



A server version of the same example:

```python
from liquer import *
from liquer.app import quickstart

@first_command
def hello():
    return "Hello"

@command
def greet(greeting, who="world"):
    return f"{greeting}, {who}!"

if __name__ == '__main__':
    quickstart(index_link="/liquer/q/hello/greet/readme.txt")
```

This is a quick way how to start a liquer server. It should automatically call the link ```/liquer/q/hello/greet/readme.txt```,
which executes the query ```hello/greet```. The result is exposed as ```readme.txt```. The name (readme) is arbitrary, but the file extension (txt)
is significant, since it determines the output format.
The ```/liquer/q``` is an [endpoint](https://en.wikipedia.org/wiki/Web_API#Endpoints) for executing a query (see [web service API](web_service.md)).

The ```quickstart``` is one of the simplest methods to start the LiQuer in server mode.
LiQuer framework offers, however, many ways to configure and adapt the solution.

# Working with pandas

Pandas example:
```python
from liquer import *
import liquer.ext.lq_pandas

@first_command
def data():
    return pd.DataFrame(dict(a=[1, 2, 3], b=[40, 50, 60]))

@command
def sum_columns(df, column1="a", column2="b", target="c"):
    df.loc[:, target] = df[column1]+df[column2]
    return df
```

When queried via a web interface, the data is automatically converted
to a most suitable format. If the last element of a query is a command
without arguments containing a dot in the name, it is interpreted as a file name and the extension is used to determine the format.
The format conversion only happens when query is run over the service,
not when using the ``evaluate`` function. 

* **data** - default format is used (which is csv)
* **data/data.html** - data is converted to html and displayed in the browser
* **data/data.csv** - data is converted to csv
* **data/data.xlsx** - dataframe is converted to xlsx
* **data/eq-b-50** - built in equality filter selects rows with b==50
* **data/sum_columns** - sum_columns is applied to a dataframe; this is equivalent to `sum_columns(data())`
* **data/sum_columns/sum_columns-a-c-d/sum2.html** - multiple actions are chained: sum_columns(sum_columns(data()),"a","c","d") and result is served as html.
* **df_from-URL** - built in command loads a dataframe from URL

# Charts
LiQuer has a rudimentary support for [matplotlib](https://matplotlib.org/) and [plotly](https://plot.ly/python/)
residing in packages ``liquer.ext.lq_matplotlib`` and ``liquer.ext.lq_plotly``
Examples are in [matplotlib_chart.py](https://github.com/orest-d/liquer/blob/master/examples/matplotlib_chart.py)
and [plotly_chart.py](https://github.com/orest-d/liquer/blob/master/examples/plotly_chart.py)
show how to make simple plots with the commands already built in. This functionality is very basic at the moment and is likely to change.


