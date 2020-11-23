# LiQuer (Link Query) 

LiQuer is a minimalistic python framework on top of flask, which simplifies creation of web services and web interfaces,
particularly in connection to data science: working with data frames, charts and reports.
The core of LiQuer is a simplistic query language, that can represent a chain of transformations (*commands*)
applied to an arbitrary data object (e.g. a dataframes, text, json, images). LiQuer query is safe to use inside URLs
and is interpreted and executed by a LiQuer server that is available as a flask blueprint.
LiQuer is very modular and designed to be extremely easy to extend (typically just by simple decorators and use of conventions).
Results of LiQuer queries can be cached for added performance.

Please visit [LiQuer website](https://orest-d.github.io/liquer/) for more info.

# Install

```
pip install liquer-framework
```

# News
2020-11-08 - v3.2 - Support for matplotlib figures, SQL cache and other minor changes
2020-11-09 - v3.3 - SQL cache with base64 encoding, cache cleaning
2020-11-11 - v3.4 - XOR file cache allows simple encoding of cached data

# TODO

- [x] improve command catalogue (in progress)
- [x] support for dataframe iterator - kind of supported by pickling
- [x] namespaces
- [x] lift the requirement for a state to be cloneable - at least for some data types
- [x] make indicator of *volatile* state, that can never be cached (volatile=immutable?)
- [x] specify metadata in command decorator
- [x] cache categories/levels dependent on metadata
- [x] basic keras support
- [x] basic scikit support
- [x] composite state (djson)
- [x] meta extension
- [x] command/query GUI
- [x] simple GUI

- [x] advanced query parser
- [x] improved error reporting with positions in a query
- [x] read/write of metadata independent from data

- [ ] sub-queries as arguments
- [ ] automatic dependent query recording via a context
- [ ] debugging via context
- [ ] messages and progress report via context
- [ ] implied volatile (query result dependent on a volatile query should be volatile)

- [ ] remote liquer service as cache
- [ ] dependency management
- [ ] resources

- [ ] attributes to prevent cloning and caching
- [ ] keras history support
- [ ] numpy support
- [ ] parquet support
