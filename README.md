# LiQuer (Link Query) 

LiQuer is a minimalistic python framework. LiQuer gives superpowers to python function:
they can become part of a pipeline and become accessible over the web api, results can be cached, stored in a virtual file system, served via web api and eventually displayed in specialized web applications.
LiQuer is something like an operating system for python functions.

LiQuer's main focus is data-science, but due to its simplicity and universality it can be applied in many other domains.
LiQuer simplifies creation of web services and web interfaces, working with data frames, charts and reports.

The core of LiQuer is a query language, that represent a chain of transformations (*commands*)
applied to an arbitrary data object (e.g. a dataframes, text, json, images or even music). LiQuer query is safe to use inside URLs and is interpreted and executed by a LiQuer server that is available as a flask blueprint.
LiQuer is very modular and designed to be extremely easy to extend. It can be used with or without web interface,
it can use either build-in web interface or host third party web applications.

LiQuer currently it supports Flask and Tornado, drivers for other web framework can be easily implemented and thus LiQuer can integrate into many new or existing python web applications.

Please visit [LiQuer website](https://orest-d.github.io/liquer/) for more info.

# Features

* Pipeline management via a flexible query language.
* Advanced metadata handling: all the data is equipped with metadata containing status info, data description, log messages and other relevant information about a successfull or failed calculation.
* Virtual file system allows to mount different data sources into a single file-system like tree.
* Virtual file system may contain physical data, but as well recipes how to create the data. (A bit like makefiles.)
* Optional flexible cache that may automatically store steps in a pipeline execution.
* Web API allows to control all elements of the system: pipeline execution, cache, store and metadata.
* Web interface makes it easier to access the functionality, quickly produce and inspect the data in the virtual filesystem and eventually visualize the data, create dashboards and reports.

# Install

```
pip install liquer-framework
```

# News

## Changes in v0.8
- Early indexer support - customized updating of metadata, future integration into search engines
- Specialized indexers allow to specify/customize *tools* that can be used for viewing and editing in GUI.
- Added S3 store
- Remote store allows to mount a remote LiQuer server as a store


## Changes in v0.7

### Breaking changes
- liquer/cache api changed to liquer/api/cache to be consistent with the rest of the api (like store)
- recipes refactored to its own module, therefore the e.g. RecipeSpecStore needs to be imported from liquer.recipes, not liquer.context 
- metadata handling refactored to a separate metadata module, the refactoring is ongoing
- lq_keras fixed, now depends on a more recent keras
- liquer.ext.midi removed, code moved to an example
- liquer.server.jupyter removed, to be reimplemented in a separate project (archived in liquer-prototyping)
- OBSOLETE status changed to EXPIRED

## Changelog
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
- 2022-01-03 - v0.7.0  - many enhancements - e.g. modular recipes, support for datafusion, pptx, pillow
- 2022-01-04 - v0.7.1  - root path bugfix, sync store
- 2022-01-05 - v0.7.2  - several small fixes, e.g. fixing missing log in recipe-created metadata
- 2022-01-06 - v0.7.3  - two bugfixes, recipe version
- 2022-01-07 - v0.7.4  - more bugfixes
- 2022-01-12 - v0.7.5  - more bugfixes, pandas_concat recipe
- 2022-01-25 - v0.7.6  - bugfixes in recipe metadata, development of extra parameters to evaluate
- 2022-01-22 - v0.8.0  - tools, indexers, S3 store, remote liquer as a store, 

### New features
- API documentation improved on multiple places
- EXTERNAL status
- Basic support for DataFusion, pptx-python, Pillow images
- Tornado driver updated
- Extensible recipes; parquet_sql recipe type
- Read-only store proxy
- v0.7 is accompanied with new GUI [liquer-gui v0.1.0](https://github.com/orest-d/liquer-gui)