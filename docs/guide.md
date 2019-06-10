# Instalation

Get LiQuer from [https://github.com/orest-d/liquer](repository):

``
git clone https://github.com/orest-d/liquer.git
``

# Hello, world!

The good tradition is to start with a Hello, world! example:

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

# Encoding and decoding a query
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

## Cache

By default there is no cache - i.e. the queries are always re-evaluated.
There are several cache implementations available in ``liquer.cache``.
They are configured by ``set_cache`` function, for example

``python
set_cache(FileCache("cache"))
``

configures a cache that will store all the (chache-able) results of queries
in a dictionary *cache*.
Cache should be configured before the queries are evaluated - and before state variables are set.

Currently there are three cache implementations: ``NoCache`` is a trivial do-nothing cache, ``FileCache`` stores data in files, ``MemoryCache`` caches
the object in the memory.

Custom cache can be created by defining a cache interface, see above mentioned classes. Cache will typically use query as a key and utilize the mechanism of serializing data into a bytes sequence (defined in ``liquer.state_types``), thus implementing a cache based either on a key-value store or blob-storage in SQL databases should be fairly straightforward (and probably quite similar to ``FileCache``).

