# Instalation

LiQuer requires at least python 3.6 with flask. It can be installed by
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

# Getting started

The good tradition is to start with a *Hello, world!* example:

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
*Link query* syntax allows to represent pipelines are relatively short strings.
More importantly, *link query* can be used as
a path part of the [URL](https://en.wikipedia.org/wiki/URL).
Unlike the more conventional web services typically a separate request
for each action, *link query* can specify
sequences of actions (pipelines) in the URL.
This gives LiQuer an incredible amount of  flexibility and expressiveness.



A server version of the same example:

```python
from liquer import *

### Create Flask app and register LiQuer blueprint
from flask import Flask
import liquer.blueprint as bp
app = Flask(__name__)
app.register_blueprint(bp.app, url_prefix='/liquer')

@first_command
def hello():
    return "Hello"

@command
def greet(greeting, who="world"):
    return f"{greeting}, {who}!"

if __name__ == '__main__':
    app.run()
```

This is a normal [flask](http://flask.pocoo.org/) server, registering LiQuer
[blueprint](http://flask.pocoo.org/docs/1.0/blueprints/) which makes all the LiQuer functionality available
in the web service.

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

# Encoding and decoding

In many cases, particularly when supplying a URL as a parameter to a query, 
some charactes need to be escaped.

A comprehensive example shows two ways how to do it:
```python
from liquer import *
from liquer.parser import encode, encode_token
import liquer.ext.lq_pandas

url = "https://raw.githubusercontent.com/orest-d/liquer/master/tests/test.csv"

query = encode([["df_from",url]]) # encode complete query
print (f"Query: {query}")
# Query: df_from-~Hraw.githubusercontent.com~Iorest~_d~Iliquer~Imaster~Itests~Itest.csv

print (evaluate(query).get())

query = "df_from-"+encode_token(url) # encode a single token of the query 
print (f"Query: {query}")
print (evaluate(query).get())
```

A query is a list of commands; each command being a list of strings (*tokens*).
The first string token in a command is the name of the command and the rest are the parameters.
A string token is simply a string which can be escaped by ``encode_token`` and unescaped by ``decode_token``.

A *decoded query* is simply a list of lists of strings. To convert a *decoded query* to a string (*encoded query*) use ``encode``,
for the inverse operation use ``decode``. 

The encode can as well be done via a web service by ``api/build`` (see ``liquer/blueprint``).

# State variables

In some situations it is useful to pass some values along the query.
For example if we want to specify some value once and use it in multiple commands.

```python
from liquer import *
from liquer.state import set_var
import liquer.ext.basic

@command
def hello(state, who=None):
    if who is None:
        who = state.vars.get("greet","???")
    return f"Hello, {who}!"

set_var("greet","world")

print (evaluate("hello").get())
# Hello, world! : uses state variable defined above

print (evaluate("state_variable-greet").get())
# world : shows the content of the state variable

print (evaluate("hello-everybody").get())
# Hello, everybody! : uses the argument

print (evaluate("let-greet-variable/hello").get())
# Hello, variable! : defines the variable in the query

print (evaluate("hello").get())
# Hello, world! : let is local to a query
```

There are two variables that are important to set up in some cases:
* **server**  should contain the URL of the LiQuer server
* **api_path** should contain the path to the query service
So ``server + api_path + query`` should become a valid url that would yield a query result. Several commands (e.g. link or split_df) depend on
correct definition of these variables, so they should be set together
with setting up the flask blueprint - e.g.

```python
url_prefix='/liquer'
app.register_blueprint(bp.app, url_prefix=url_prefix)
set_var("api_path",url_prefix+"/q/")
set_var("server","http://localhost:5000")
```

# Cache

By default there is no cache - i.e. the queries are always re-evaluated.
There are several cache implementations available in ``liquer.cache``.
They are configured by ``set_cache`` function, for example

```python
set_cache(FileCache("cache"))
```

configures a cache that will store all the (chache-able) results of queries
in a dictionary *cache*.
Cache should be configured before the queries are evaluated - and before state variables are set.

Currently there are three cache implementations: ``NoCache`` is a trivial do-nothing cache, ``FileCache`` stores data in files, ``MemoryCache`` caches
the object in the memory.

Custom cache can be created by defining a cache interface, see above mentioned classes. Cache will typically use query as a key and utilize the mechanism of serializing data into a bytes sequence (defined in ``liquer.state_types``), thus implementing a cache based either on a key-value store or blob-storage in SQL databases should be fairly straightforward (and probably quite similar to ``FileCache``).

Command may optionally decide not to cache its output. This may be useful when command produces volatile data, e.g. time.
In such a case command (operating on a state) can disable cache by ``state.with_caching(False)``.

# Store

*Store* is a configurable virtual file system inside liquer. *Store* is designed to be able to deal with states. One notable extension of the *Store* compared to a regular file system is the ability to store (and work with) the metadata, which is essential for dealing with data in liquer.  

*Store* is basically a key/value store mapping a path to a sequence of bytes. By itself, *Store* does not define (or care) about serialization of the data. This differenciates it from *Cache*.

Even though the interface to *Cache* and *Store* is intentionaly very similar, these two mechanisms are different:

* *Cache* keeps *State* (i.e. data object with metadata). *Cache* deals with objects and stores *State* perhaps in a non-serialized form (e.g. MemoryStore).
* *Store* keeps resources - i.e. arbitrary binary data (*bytes*) complemented with metadata. 

One purpose of a *Store* is to provide an option to serve files into the pipeline. The pipeline may start with a resource path followed by a sequence of actions.
