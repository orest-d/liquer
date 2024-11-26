# TODO

## Critical Bugs
- [x] pandas append in dataframe_batches - e.g. line 46 - removed in pandas 2
- [ ] fix removedir (plus recursive) in S3 store
- [ ] removedir in remote store
- [ ] removedir recursive in recipes 
- [ ] store crashing on corrupted metadata; investigate cache too
- [ ] sql should be displayed in UI !
- [x] make sure file store removedir removes metadata when empty
- [x] recurent store.removedir

## Bugs
- [ ] handle undefined and null in COntent.vue 207 (just_load)s
- [ ] metadata viewer lacks length
- [x] specify escape character in lq_pandas to_csv
- [x] import Metadata in lq_pandas
- [x] recipes.py line 128 - improve error reporting 
- [?] context.py line 754 metadata referenced before assignment
- [ ] looks like that GUI executes the query even when just metadata should be shown for #-i-km
- [ ] ambiguity interpreting ~X - absolute path starting with -R does not make sense
- [x] datafusion sql recipe does not log the error if SQL is faulty
- [x] state vars not preserved - check, test
- [x] pandas_concat missing data characteristics, recipes_key and recipes_directory
- [x] failed resource query should pass on the error (test_recipe_error_in_query_metadata in test_query)
- [x] recipe title is changing during execution - fixed but untested
- [x] liquer-gui content - resource should be loaded from store, not via query
- [x] Error in recipe make is not stored
- [x] missing status with parquet_sql recipe
- [x] rooting/prefix store not getting to correct root_store implementation - MountPointStore.mount
- [x] stored metadata created by a recipe do not contain logs and message from the query
- [x] error in server response() is not shown
- [x] screen should be empty in GUI when unsupported type is shown
- [x] parser failure when capital case in resource path (?) - probably faulty logic in context.py:896, resource query should be handled separately - seems to be working
- [x] root "-R/-/"

## High priority features
- context evaluate_template should support input_value
- support openbin in recipes
- support path to stored objects (copy to tmp) to support Polars LazyDataframe

## Unsorted
- [ ] make separators, quotes and escape characters configurable in config
- [ ] OpenDAL store support
- [ ] Separate recipes identification into metadata from recipe execution (store)
- [ ] has_warnings in metadata and gui
- [ ] identify better command runtime errors from framework errors - color output? 
- [ ] Avoid multiple sync in store initialization - require sync or init after setup
- [ ] Lazy generation of recipes_status.txt
- [ ] Lazy initialization of recipes description?
- [x] Make failed serialization when writing to cache not fatal
- [ ] PandasAI support
- [x] fsspec support
- [ ] DuckDB support
- [x] support for Polars SQLContext
- [x] support for Polars LazyFrame
- [ ] basic portable dataframe operations
- [ ] Redis cache
- [?] GIT read only store - via fsspec
- [ ] refactor store to always have prefix
- [?] (pending) auto lookup of command modules in presets

## Refactoring and celanup
- [ ] remove commands and extended commands from metadata
- [ ] change /api/debug-json to /api/metadata
- [ ] consolidate meta and basic module

## User interface

- [ ] icons (in metadata and web)
- [ ] new menu - remove menu from state variables
- [ ] wasm library in frontend
- [x] liquer frontent project - exists: liquer-gui 
- [x] web store GUI (in progress: https://github.com/orest-d/liquer-gui)

## Indexer

- [x] data viewers and editors support, plugable tools
- [x] plugable tools - New Edit View Metadata
- [ ] field statistics
- [ ] metadata dimensions and quantities
- [ ] dataframe catalogue
- [x] search engine support
- [ ] customizable dataframe search engine


### LiQuer-GUI project

- [ ] #-i-qm bug in child log references
- [ ] text editing syntax highlight
- [ ] right top menu
- [ ] optionally load whole dataframe
- [ ] progress in recipe execution
- [ ] progressive status in directory (auto-update of directory status)
- [ ] websockets status update
- [x] error in store should have a delete button
- [x] message should be cleared after fetching
- [x] directory name should be visible
- [x] reload recipes
- [x] dir info not properly refreshed
- [x] anchor
- [x] display text, html and images properly
- [x] text editing (experimental)
- [x] store manager: reload dir
- [x] store manager: clean dir
- [x] store manager: submit dir

## Server, Backend

- [ ] REST command arguments to make web apps easier (post, json-encoded arguments)
- [x] REST command arguments to make web apps easier (url parameters)
- [x] REST command arguments preparation - evaluate with extra parameters
- [ ] server info with supported features
- [x] make a server suitable for publishing (read only access to store) - tornado only
- [ ] server driver - function to start server from a particular driver
- [ ] configure the start page, Response support?
- [ ] update Jupyter plugin
- [x] a faster server - FastAPI
- [ ] websockets status update
- [x] update tornado backend
- [x] unified metadata api for cache and store

## Store and Cache enhancements

- [x] S3 store
- [ ] external file storage - like file storage, but without storable metadata 
- [ ] local file using context manager - enter, exit
- [ ] async store and cache access to support async server frameworks
- [ ] ability to dig into a zip file -Rzip/.../--R/.../-/query
- [ ] ability to dig into a json or yaml file -Rjson/.../--R/.../-/query - important for recipe links
- [ ] remove directory recursively
- [ ] validate key
- [ ] ignore files with an ivalid name in the store - e.g. starting with ~ 
- [ ] metadata for external files in store
- [ ] date, size and detection of modifications
- [ ] system store(s): commands, cache, running operations, configuration 
- [ ] SQL cache working on Hive
- [ ] SQL store working on Hive
- [x] remote store (based on web api)
- [ ] remote liquer service as cache
- [ ] encoded store
- [ ] database store
- [ ] filesystem from store
- [ ] fuse access to store
- [ ] key tracing
- [ ] command/query to zip store directory
- [ ] cashing store (to be used e.g. with a database store)
- [ ] store with autobackup
- [x] deal with corrupted metadata in store
- [x] readonly store modifier
- [x] file-system paths and url links to physical file in store (when possible) 
- [x] resources-based cache
- [x] cleanup errors (ns-meta/clean)
- [x] external status

## Dependency management

- [ ] expiration for files in store
- [ ] expiration for cache
- [x] command version/hash code

## Recipes

- [ ] dictionary of recipes in recipes.yaml
- [ ] validate filename
- [ ] create report of parsing recipes.yaml
- [ ] use line numbers in recipes.yaml (see https://stackoverflow.com/questions/13319067/parsing-yaml-return-with-line-number)
- [x] recipe version
- [ ] volatile recipes
- [x] CWD
- [ ] links in the description
- [ ] parametric recipes - recipe templates
- [ ] matplotlib charting recipe type
- [ ] database access in recipes
- [x] refactor recipes to a separate module
- [x] checksum in store metadata
- [x] refactor recipes to make them modular
- [x] more powerful recipes - description and url/file links, nested structure ?
- [x] ignore dot directories in recipes store in order to support jupyter notebooks
- [x] datafusion parquet_sql recipe

## Integration of external components

- [ ] graphviz
- [ ] Jupyter ipynb viewer
- [ ] XGBoost
- [ ] LightGBM
- [ ] zip file as a state type
- [ ] spark support - spark dataframes
- [ ] jinja and/or other templating engines
- [ ] d-tale support
- [ ] onnx
- [ ] geopandas and folium
- [ ] markdown support
- [ ] bokeh
- [ ] numpy support
- [ ] pandas series and groupby objects
- [ ] TF Lite
- [ ] pdf
- [ ] epub
- [ ] 3d formats stl, obj
- [ ] gcode
- [x] gradio
- [x] sweetviz support
- [x] polars support
- [x] python-pptx integration
- [x] PIL
- [x] datafusion support - context and sql
- [x] parquet support
- [x] integrate pointcloud explorer - see [Pointcloud Explorer](https://github.com/orest-d/pointcloud-viewer-rs)

## Core functionality and Metadata

### Iterative evaluation
- [ ] improve scheduling - prevent same queries to be scheduled
- [ ] debug transform query
- [ ] enable websockets
- [ ] finalize refactoring of Context to Metadata
- [ ] query meta modifier similar to -R-meta
- [x] python logging integration with metadata and context
- [ ] iterative resource evaluation
- [ ] trampoline to handle subqueries and parent queries
- [ ] cyclic dependencies detection
- [ ] clarify state/context metadata flow

### Other
- [ ] dependency injection input type
- [ ] default parameter value from query (combined with dependency injection)
- [ ] default state parameter value ? from query ? (combined with dependency injection)
- [x] template engine with query expansion
- [ ] references in metadata
- [ ] query origin (file, line number if possible)
- [ ] attribute to prevent cloning
- [ ] git support
- [x] search engine(s) integration
- [ ] commands from methods
- [ ] automatic state type from classes
- [ ] automatic argument type conversion
- [x] refactor metadata handling to a separate class from context and state
- [x] split context to mixins
- [ ] Anchor support in query parser

## Highlevel features, useful commands, Examples and Documentation

- [ ] filter capability in resources
- [ ] ability to have resources as actions in a pipeline
- [ ] start liquer-ml
- [ ] conventions and ML library 
- [ ] default data-science app example
- [ ] better chart library
- [ ] better pandas functions (eq, lt, gt, leq, geq, isin, notin, between, groupby, random)
- [ ] report template
- [x] dataframe batches

## LiQuer ML and Application

- [ ] field database - data type, statistics, label, presentation
- [ ] field conventions
- [ ] feature definition

## Misc and Experimental

- [ ] rust query parser

## Old/Done
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
- [x] state enum in context
- [x] color coding of state in GUI query monitoring

- [x] timestamp in context log messages
- [x] test and fix bug with incorrect query used in error reporting of link expansion (implement reporting query)
- [x] resource path in ~X link

- [x] default store for webapp extensions
- [x] configurable frontend - kind-of possible with web store
- [x] human readable metadata extract and store report (can be improved, but the basic functionality is there)

- [x] fix context.warning and tracebacks
- [x] dr extension - explicity type_identifier, extension, better errors and metadata handling
- [x] link to relevant recipes.yaml in metadata
- [x] fix updated time in finalize metadata - time should only be updated on storing, not on reading
- [x] fix time display in recipes_status.txt
- [x] progressive metadata storing when evaluating to store
- [x] data characteristics generated by state type
- [x] clean recipes store - remove recipes, but keep external files
- [x] on change action in store, dir summary
- [x] get_context function to create context

- [x] resources
- [x] store implementations: memory, file, mounting, filesystem
- [x] web api for store
- [x] resources with recipes
- [x] decode resource command
- [x] consolidate is_error and status
