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

```python
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

```python
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

```python
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

```python
    def copy(self, data):
        """Make a deep copy of the data"""
        return data
```

Once the state type class is defined, a state type instance
is created and registered

```python
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

# Reports and visualizations

With the help of LiQuer, it is very easy to create both resuable visualizations with multiple views
as well as documents viewable offline or suitable for printing. Probably the easiest way to achieve that
is creating a command, which will return a html document.
(Alternatively other markup can be used, e.g. LaTeX, but we will focus on html.)
Creation of text is simplified by ``evaluate_template`` function, which processes a string (*template*)
containing LiQuer queries and replaces those queries by their results.

```python
@command
def datemy(df,y="mp_year",m="mp_month",target="date"):
    df.loc[:,target]=["%04d-%02d-01"%(int(year),int(month)) for year,month in zip(df[y],df[m])]
    return df

@command
def count(df, *groupby_columns):
    df.loc[:,"count"]=1
    return df.groupby(groupby_columns).count().reset_index().loc[:,list(groupby_columns)+["count"]]

@command
def geq(df, column, value:float):
    index = df.loc[:,column] >= value 
    return df.loc[index,:]

@command
def table(state):
    df = state.get()
    html=evaluate_template(f"""<a href="${state.query}/link-url-csv$">(data)</a> """)
    return html+df.to_html(index=False, classes="table table-striped")

@command
def report(state, from_year=2017, linktype=None):
    state = state.with_caching(False)
    def makelink(url):
        if linktype is None:
            return url
        extension = url.split(".")[-1]
        return evaluate(f"fetch-{encode_token(url)}/link-{linktype}-{extension}").get()

    try:
        source = state.sources[0]
    except:
        source = "???"
    
    LiQuer='<a href="https://github.com/orest-d/liquer">&nbsp;LiQuer&nbsp;</a>'
    df = state.get()
    try:
        title = ",".join(sorted(df.adm0_name.unique())) + f" since {from_year}"
    except:
        title = "report"
    return state.with_filename("report.html").with_data(evaluate_template(f"""
<html>
    <head>
        <title>{title}</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        <link rel="stylesheet" href="{makelink('https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css')}" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">
    </head>
    <body>
        <div class="p-3 mb-2 bg-success text-white fixed-top shadow-sm">
            <a class="nav-link active" href="https://data.humdata.org"><img src="{makelink('https://centre.humdata.org/wp-content/uploads/hdx_new_logo_accronym2.png')}" style="height:30px;" alt="HDX"></a>
        </div>
        <div class="bg-light fixed-bottom border-top">
        Generated with {LiQuer} <span class="float-right">&#169; 2019 Orest Dubay</span>
        </div>
        <br/>
        <br/>
        <br/>
        <br/>
        <h1>{title}</h1>
        <div class="container-fluid">
            <div class="row">
                Data originate from <a href="{source}">&nbsp;{source}&nbsp;</a> were processed via a {LiQuer} service.
                Only data after {from_year} are shown (<a href="${state.query}/datemy/geq-mp_year-{from_year}/link-url-csv$">data</a>),
                complete data are <a href="${state.query}/datemy/link-url$">&nbsp;here</a>. 
            </div>
            <div class="row">
                <div class="col-md-6" style="height:50%;">${state.query}/datemy/geq-mp_year-{from_year}/groupby_mean-mp_price-date-cm_name/plotly_chart-xys-date-mp_price-cm_name$</div>
                <div class="col-md-6" style="height:50%;">${state.query}/datemy/geq-mp_year-{from_year}/count-adm1_name/plotly_chart-piexs-count-adm1_name$</div>
            </div>
            <div class="row">
                <div class="col-md-6" style="height:50%;">
                <h2>Average prices</h2>
                ${state.query}/datemy/geq-mp_year-{from_year}/groupby_mean-mp_price-cm_name/table$</div>
                <div class="col-md-6" style="height:50%;">
                <h2>Observations</h2>
                ${state.query}/datemy/geq-mp_year-{from_year}/count-adm1_name/table$</div>
            </div>
    </body>
</html>
    """))
```