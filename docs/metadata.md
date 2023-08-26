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
