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

- 2020-11-08 - v0.3.2  - Support for matplotlib figures, SQL cache and other minor changes
- 2020-11-09 - v0.3.3  - SQL cache with base64 encoding, cache cleaning
- 2020-11-11 - v0.3.4  - XOR file cache allows simple encoding of cached data
- 2020-12-06 - v0.4.0  - big change: introduced context, parser, pool and progress monitoring
- 2020-12-07 - v0.4.1  - fixing buf in file cache remove
- 2020-12-07 - v0.4.2  - Fernet file cache support for metadata encoding and change of keys
- 2021-01-16 - v0.4.3  - Improvements of the query monitoring UI
- 2021-01-19 - v0.4.4  - state variables in context, html_preview
- 2021-01-31 - v0.4.5  - remove supported in query monitoring
- 2021-01-31 - v0.4.6  - basic support for parquet and feather
- 2021-06-22 - v0.4.7  - stores, resources and recipes
- 2021-06-23 - v0.4.8  - multiple fixes
- 2021-08-18 - v0.4.9  - small fixes
- 2021-08-19 - v0.4.10 - local recipes in RecipeSpecStore
- 2021-10-31 - v0.4.11 - multiple improvements with store and metadata reporting
- 2021-11-07 - v0.4.12 - recipes cleaning, recipes status file, progressive metadata storing in stores
- 2021-11-08 - v0.4.13 - fixing recipes status performance issue and minor improvements in status commands
- 2021-11-09 - v0.4.14 - minor fixes and enhancements
- 2021-11-10 - v0.5.0  - dataframe_batches and rudimentary Sweetviz support
- 2021-11-11 - v0.5.1  - fixing a bug in the dr (decode resource) command
- 2021-11-11 - v0.5.2  - fixing a bug in created/updated time in store
- 2021-11-22 - v0.6.0  - basic support for openpyxl and polars
- 2021-11-23 - v0.6.1  - bug fixes and minor enhancements
- 2021-11-28 - v0.6.2  - fixing bugs necessary to operate liquer-gui
- 2021-11-29 - v0.6.3  - several important bugfixes
- 2021-12-06 - v0.6.4  - minor fixes
- 2021-12-12 - v0.6.5  - fixes and refactoring

