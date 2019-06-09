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

## Instalation

Get LiQuer from [https://github.com/orest-d/liquer](repository):

``
git clone https://github.com/orest-d/liquer.git
``

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

A server version of the same example:
```
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

## Working with pandas

Pandas example:
```
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

## Encoding and decoding a query
```
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

## State variables

In some situations it is useful to pass some values along the query.
For example if we want to specify some value once and use it in multiple commands.

```
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

```
url_prefix='/liquer'
app.register_blueprint(bp.app, url_prefix=url_prefix)
set_var("api_path",url_prefix+"/q/")
set_var("server","http://localhost:5000")
```

## Cache

By default there is no cache - i.e. the queries are always re-evaluated.
There are several cache implementations available in ``liquer.cache``.
They are configured by ``set_cache`` function, for example

``
set_cache(FileCache("cache"))
``

configures a cache that will store all the (chache-able) results of queries
in a dictionary *cache*.
Cache should be configured before the queries are evaluated - and before state variables are set.

Currently there are three cache implementations: ``NoCache`` is a trivial do-nothing cache, ``FileCache`` stores data in files, ``MemoryCache`` caches
the object in the memory.

Custom cache can be created by defining a cache interface, see above mentioned classes. Cache will typically use query as a key and utilize the mechanism of serializing data into a bytes sequence (defined in ``liquer.state_types``), thus implementing a cache based either on a key-value store or blob-storage in SQL databases should be fairly straightforward (and probably quite similar to ``FileCache``).

## Web-application example: HDX disaggregation wizard

LiQuer is a framework rather than an end-user product.
Not everybody enjoys writing a complex query in
a browser URL line to achieve their goals...
However, LiQuer flexibility on the server side can be very helpful
when building data-oriented web applications.

One such example is HDX disaggregation wizard.
It is tool solving a simple task:
You have a data sheet (csv) that you would like to split
into multiple sheets based on a column value (or multiple column
values). Such functionality is built into ``liquer.ext.lq_pandas``,
the main hero being the ``eq`` command.

The idea is simple:
* fetch data (command ``df_from``)
* find unique values in a column (or multiple columns) and use them
to create a list (table) of queries (command ``qsplit_df``)
* the queries use ``eq`` to filter dataframe by value(s).

So, use a query like ``df_from-URL/qsplit_df-COLUMN``
and you will get a table with queries like ``df_from-URL/eq-COLUMN-VALUE1``,
``df_from-URL/eq-COLUMN-VALUE2``...

## Defining own state type: libhxl, a Case study

Sometimes pandas does not cover fit the pandas - there are other
good libraries e.g. [tabulate](https://bitbucket.org/astanin/python-tabulate). If you want to support other data type or library,
typically this (besides defining some useful commands) usually requires implementing a state type.
State type does several things associated with state type handling,
but the most important role is defining a serialization and deserialization
of the type.

One excelent library used for working with humanitarian data is
[libhxl](https://github.com/HXLStandard/libhxl-python). Libhxl which plays somewhat similar role as pandas: it reads, writes and manipulates tabular data - but it does as well understand [HXL](http://hxlstandard.org),
which pandas doesn't... Hence the ``liquer.ext.lq_hxl`` module - and
here is a short explanation how the HxlStateType is defiend

```
import hxl
from liquer.state_types import StateType, register_state_type, mimetype_from_extension

class HxlStateType(StateType):
    def identifier(self):
        "Define an unique string identifier for the state type"
        return "hxl_dataset"
```
The ``identifier`` is important e.g. for caching, 
where it is stored as a part of metadata and it
tells what StateType should be used for deserialization.

```
    def default_extension(self):
        "Default file extension for the state type"
        return "csv"

    def is_type_of(self, data):
        "Check if data is of this state type"
        return isinstance(data, hxl.model.Dataset)
```
Default extension is used when the extension is not specified otherwise - for example if query does not end with a filename.

The ``as_bytes`` and ``from_bytes`` are two most important methods,
which take care of the serialization and deserialization.
A state data can be serialized into multiple formats (e.g. csv, html, json...), therefore ``as_bytes`` optionally accepts a file extension
and returns (besides the bytes) as well the mimetype.
Th mimetype (when queried through the liquer server) becomes a part of the web service response.

Note that serialization and deserialization do not necessarily need
to support the same formats. E.g. html is quite nice to support
in serialization, but it is too unspecific for a deserialization.

```
    def as_bytes(self, data, extension=None):
        """Serialize data as bytes
        File extension may be provided and influence the serialization format.
        """
        if extension is None:
            extension = self.default_extension()
        assert self.is_type_of(data)
        mimetype = mimetype_from_extension(extension)
        if extension == "csv":
            output = "".join(data.gen_csv(show_headers=True, show_tags=True))
            return output.encode("utf-8"), mimetype
        elif extension == "json":
            output = "".join(data.gen_json(show_headers=True, show_tags=True))
            return output.encode("utf-8"), mimetype
        else:
            raise Exception(
                f"Serialization: file extension {extension} is not supported by HXL dataset type.")

    def from_bytes(self, b: bytes, extension=None):
        """De-serialize data from bytes
        File extension may be provided and influence the serialization format.
        """
        if extension is None:
            extension = self.default_extension()
        f = BytesIO()
        f.write(b)
        f.seek(0)

        if extension == "csv":
            return hxl.data(f)
        raise Exception(
            f"Deserialization: file extension {extension} is not supported by HXL dataset type.")
```

Sometimes a deep copy of state data is needed - e.g. to assure
that the data in the cache will not become unintentionally
modified. That's why the state type should define ``copy`` method.
Since libhxl dataset is immutable (?), it is OK to return just the data without making a copy. 

```
    def copy(self, data):
        """Make a deep copy of the data"""
        return data
```

Once the state type class is defined, a state type instance
is created and registered

``` 
HXL_DATASET_STATE_TYPE = HxlStateType()
register_state_type(hxl.Dataset, HXL_DATASET_STATE_TYPE)
register_state_type(hxl.io.HXLReader, HXL_DATASET_STATE_TYPE)
```

This is (currently) done for all relevant types.
State types are registered in a global ``StateTypesRegistry``
object, which is responsible for registering and finding a state type
instance for any state data.

For more details see ``liquer.ext.lq_hxl`` module.

Actually, the state type may not define a serialization and/or deserialization. There are objects that either can't be reliably serialized
(e.g. matplotlib figure - as of time of writing)
or serialization is otherwise undesirable. Such state types would be perfectly legal - they just could be neither cached nor served by the liquer web server. However, they could be inside the query, e.g.
if matplotlib figure would be followed by image creation command,
the image could be both served and cached.

