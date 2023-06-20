# Web service

Web service is typically installed with an absolute paths
starting with */liquer*, e.g. */liquer/q/hello*.
Though this can be changed (and should be fully configurable in the future),
some extensions currently (e.g. [liquer gui](https://github.com/orest-d/liquer-gui))
currently rely on this absolute location.

## Core service for query execution

### Route /q/QUERY (GET, POST)

Main service for evaluating queries.
Service allows to supply named arguments, that will be passed
to the last command in the query. These arguments can be passed as URL query
or POSTed as [JSON](https://en.wikipedia.org/wiki/JSON) dictionary.


### Route /submit/QUERY (GET)

Main service for evaluating queries.
Like */q/QUERY*, but the *QUERY* is executed in the background.
Service returns status as a JSON document.
Status contains

* **status** OK or ERROR
* **message** short text message describing the status of the submission
* **query** query that was submitted

## Cache interface
 
### Route/api/cache/get/QUERY (GET, POST)

FIXME: POST not implemented(?)

Get cached data. If the result of the *QUERY* is stored in cache,
it is returned immediately, otherwise the call fails.
POST method may be supported, which allows using the service as a remote cache.


### Route /api/cache/meta/QUERY (GET, POST)
Get cached metadata as JSON for *QUERY* if available, a status JSON otherwise:
POST method may be supported, which allows using the service as a remote cache.

* **status** FIXME
* **message** (FIXME: missing) short text message describing the status of the submission
* **query** query that was submitted
* **cached** boolean, True when cached.


### Route /api/cache/remove/QUERY (GET)
FIXME: Support http DELETE ?
Interface to cache remove. Removes the query from cache.
Returns status JSON:

* **status** FIXME
* **message** (FIXME: missing) short text message describing the status of the submission
* **query** query that was submitted
* **removed** boolean, True when the remove operation was successful.


### /api/cache/contains/QUERY (GET)
Interface to cache contains. Returns whether *QUERY* is cached in
a JSON status document: 

* **status** FIXME
* **message** (FIXME: missing) short text message describing the status of the submission
* **query** query that was submitted
* **cached** boolean, True when query is in the cache


### Route /api/cache/keys.json (GET)

FIXME Remove .json or unify with /api/store
Interface to cache keys. Returns list of all keys in the cache as a JSON list.


### Route /api/cache/clean (GET)
Interface to cache clean. Cleans the whole cache. Returns a JSON document.

* **status** OK or ERROR
* **message** Short text describing the result of the operation.

## Miscellaneous services

### Route /api/commands.json (GET)

Returns a list of commands in json format


### Route /api/debug-json/QUERY (GET)

FIXME: Obsolete?
Debug query - returns metadata from a state after a query is evaluated


### Route /api/build (POST)

FIXME: Obsolete?
Build a query from a posted decoded query (list of lists of strings).
Result is a dictionary with encoded query and link.

### Route /api/register_command/DATA (GET, POST)

Remote command registration service.
This has to be enabled by liquer.commands.enable_remote_registration()

    WARNING: Remote command registration allows to deploy arbitrary python code on LiQuer server,
    therefore it is a HUGE SECURITY RISK and it only should be used if other security measures are taken
    (e.g. on localhost or intranet where only trusted users have access).
    This is on by default on Jupyter server extension.


## Store interface

### Route /api/store/data/QUERY, (GET, POST)

Get or set data in store.

GET method is equivalent to Store.get_bytes.
Content type (MIME) is obtained from the metadata.

POST method sets data in store. Equivalent to Store.store.
Unlike store method, which stores both data and metadata in one call,
the api/store/data POST only stores the data. The metadata needs to be set in a separate POST of api/store/metadata
either before or after the api/store/data POST.

On failure, a 404 error is returned with a JSON in the body:

* **status** ERROR
* **message** Short text describing the error. (typically a python traceback)
* **query** *QUERY* passed as an argument

### Route /api/store/upload/KEY (POST, optional GET)

Upload data to store - similar to /api/store/data, but using upload. Equivalent to Store.store.
Unlike store method, which stores both data and metadata in one call,
the api/store/data POST only stores the data. The metadata needs to be set in a separate POST of api/store/metadata
either before or after the api/store/data POST.

On failure, a 404 error is returned with a JSON in the body:

* **status** ERROR
* **message** Short text describing the error. (typically a python traceback)
* **query** *QUERY* passed as an argument

GET method (if supported) may return a basic html interface to facilitate the
file upload.

### Route /api/store/metadata/KEY (GET, POST)

FIXME: KEY, not QUERY
Getting or setting the metadata for KEY.
On successful GET returns the metadata as JSON.
Otherwise a status JSON document is returned:

* **status** OK or ERROR
* **message** Short text describing the status. (typically a python traceback on error)
* **query** *QUERY* passed as an argument
* **key** FIXME: *KEY* passed as an argument

### Route /web/KEY (GET)

FIXME: it should be key, not query in the code

Shortcut to the 'web' directory in the store.
Similar to /store/data/web, except the index.html is automatically added if query is a directory.
The 'web' directory hosts web applications and visualization tools, e.g. liquer-pcv or liquer-gui.

On failure, a 404 error is returned with a JSON in the body:

* **status** ERROR
* **message** Short text describing the error. (typically a python traceback)
* **query** *QUERY* passed as an argument
* **key** FIXME: *KEY* passed as an argument

### Route /api/stored_metadata/QUERY (GET)

Get metadata stored in a store or cache.
This will not trigger an execution of a query or recipe.

FIXME: Make sure that recipes are not executed.

### Route /api/store/remove/KEY (GET)

Remove key from store.
FIXME KEY
FIXME support http DELETE

Status JSON document is returned:

* **status** OK or ERROR
* **message** Short text describing the status. (typically a python traceback on error)
* **query** *QUERY* passed as an argument
* **key** FIXME: *KEY* passed as an argument


### Route /api/store/removedir/KEY (GET)

Remove directory key from store.
FIXME KEY
FIXME support http DELETE

Status JSON document is returned:

* **status** OK or ERROR
* **message** Short text describing the status. (typically a python traceback on error)
* **query** *QUERY* passed as an argument
* **key** FIXME: *KEY* passed as an argument


### Route /api/store/contains/KEY (GET)

Check whether the *KEY* exists in the store.
FIXME KEY
FIXME support http DELETE

Status JSON document is returned:

* **status** OK or ERROR
* **message** Short text describing the status. (typically a python traceback on error)
* **contains** result of *store.contains* if operation is successful (true if *KEY* is in the store)
* **query** *QUERY* passed as an argument
* **key** FIXME: *KEY* passed as an argument


### Route /api/store/is_dir/KEY (GET)
Check whether the *KEY* is a directory in the store.
FIXME KEY
FIXME support http DELETE

Status JSON document is returned:

* **status** OK or ERROR
* **message** Short text describing the status. (typically a python traceback on error)
* **is_dir** result of *store.is_dir* if operation is successful (true if *KEY* is a directory)
* **query** *QUERY* passed as an argument
* **key** FIXME: *KEY* passed as an argument


### Route /api/store/keys (GET)

Return the list of keys in the store.
Returns JSON document with a result:

* **status** OK or ERROR
* **message** Short text describing the status. (typically a python traceback on error)
* **keys** list of keys (on success)


### Route /api/store/listdir/KEY (GET)
Get list of names in a directory *KEY*.
FIXME KEY

Returns JSON document with a result:

* **status** OK or ERROR
* **message** Short text describing the status. (typically a python traceback on error)
* **listdir** list of names (on success)
FIXME key, query


### Route /api/store/makedir/KEY (GET)

Make a directory specified by *KEY*.
FIXME KEY
Returns JSON document with a result:

* **status** OK or ERROR
* **message** Short text describing the status. (typically a python traceback on error)
* **query** *QUERY* passed as an argument
* **key** FIXME: *KEY* passed as an argument
