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


