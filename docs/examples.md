# HDX disaggregation wizard

LiQuer is a small server-side framework that can be quite helpful
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

# Integration of libhxl (example of a new state type)

Pandas is great, but there are other
good libraries too e.g. [tabulate](https://bitbucket.org/astanin/python-tabulate).
If you want to to use other data type (tabular or other),
it will typically require (besides some useful commands) defining how that data can be serialized.
This is done by implementing a *state type*.
State type does several things associated with state type handling,
but the most important role is handling serialization and deserialization.

One excelent library used for working with humanitarian data is
[libhxl](https://github.com/HXLStandard/libhxl-python).
Libhxl plays somewhat similar role as pandas: it reads, writes and manipulates tabular data - but it does as well understand [HXL](http://hxlstandard.org),
which pandas doesn't - hence the ``liquer.ext.lq_hxl`` module.
In order to allow libhxl objects to be used in liquer, 
we need to define a state type: ``HxlStateType``.

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

