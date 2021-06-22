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
- 2020-11-08 - v3.2 - Support for matplotlib figures, SQL cache and other minor changes
- 2020-11-09 - v3.3 - SQL cache with base64 encoding, cache cleaning
- 2020-11-11 - v3.4 - XOR file cache allows simple encoding of cached data
- 2020-12-06 - v4.0 - big change: introduced context, parser, pool and progress monitoring
- 2020-12-07 - v4.1 - fixing buf in file cache remove
- 2020-12-07 - v4.2 - Fernet file cache support for metadata encoding and change of keys
- 2021-01-16 - v4.3 - Improvements of the query monitoring UI
- 2021-01-19 - v4.4 - state variables in context, html_preview
- 2021-01-31 - v4.5 - remove supported in query monitoring
- 2021-01-31 - v4.6 - basic support for parquet and feather
- 2021-06-22 - v4.7 - stores, resources and recipes

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

- [x] sub-queries as arguments
- [x] automatic dependent query recording via a context
- [x] debugging via context
- [x] messages and progress report via context
- [x] implied volatile (query result dependent on a volatile query should be volatile)

- [x] optional metadata storage in SQL - to support Hive
- [x] proper encoding of file cache
- [x] cache remove key 

- [x] progress reporting GUI
- [x] process monitoring GUI
- [x] parallel execution of multiple queries

- [x] state variables in context
- [x] html preview
- [ ] improve scheduling - prevent same queries to be scheduled
- [x] state enum in context
- [x] color coding of state in GUI query monitoring

- [ ] report template
- [ ] wasm library in frontend
- [ ] configurable frontend
- [ ] liquer frontent project

- [x] resources
- [x] store implementations: memory, file, mounting, filesystem
- [x] web api for store
- [x] resources with recipes
- [x] decode resource command
- [ ] remote store (based on web api)
- [ ] remote liquer service as cache
- [ ] web store GUI
- [x] resources-based cache
- [ ] filesystem from store
- [ ] fuse access to store
- [ ] dependency management

- [ ] SQL cache working on Hive
- [ ] debug transform query
- [ ] test and fix bug with incorrect query used in error reporting of link expansion (implement reporting query)

- [ ] better chart library
- [ ] better pandas functions (eq, lt, gt, leq, geq, isin, notin, between, groupby, random)
- [ ] conventions and ML library 

- [ ] remove menu from state variables
- [ ] consolidate is_error and status

- [ ] attribute to prevent cloning
- [ ] keras history support
- [ ] numpy support
- [x] parquet support
