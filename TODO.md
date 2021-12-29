# TODO

## User interface

- [ ] icons (in metadata and web)
- [ ] data viewers and editors support
- [ ] new menu - remove menu from state variables
- [x] liquer frontent project - exists: liquer-gui 
- [ ] wasm library in frontend
- [x] web store GUI (in progress: https://github.com/orest-d/liquer-gui)

### LiQuer-GUI project

- [x] dir info not properly refreshed
- [x] anchor
- [x] display text, html and images properly
- [ ] optionally load whole dataframe
- [ ] text editing
- [x] store manager: reload dir
- [x] store manager: clean dir
- [x] store manager: submit dir

## Server, Backend

- [ ] a faster server (FastAPI?)
- [x] update tornado backend
- [ ] configure the start page, Response support?
- [ ] update Jupyter plugin
- [x] unified metadata api for cache and store
- [ ] change /api/debug-json to /api/metadata

## Store and Cache enhancements

- [x] deal with corrupted metadata in store
- [ ] key tracing
- [ ] command/query to zip store directory
- [ ] encoded store
- [ ] database store
- [ ] cashing store (to be used e.g. with a database store)
- [ ] metadata for external files in store
- [x] readonly store modifier
- [ ] store to_dict and from_dict
- [ ] store with autobackup
- [x] file-system paths and url links to physical file in store (when possible) 
- [ ] remote store (based on web api)
- [ ] remote liquer service as cache
- [x] resources-based cache
- [ ] filesystem from store
- [ ] fuse access to store
- [ ] cleanup errors (on start?)
- [ ] status on directories
- [x] external status
- [ ] date, size and detection of modifications
- [ ] system store(s): commands, cache, running operations, configuration 

## Dependency management

- [ ] expiration for files in store
- [ ] expiration for cache
- [x] command version/hash code

## Recipes

- [x] refactor recipes to a separate module
- [x] checksum in store metadata
- [x] refactor recipes to make them modular
- [ ] database access in recipes
- [ ] parametric recipes - recipe templates
- [ ] CWD
- [ ] multiple files created in recipe
- [ ] recipe version
- [x] more powerful recipes - description and url/file links, nested structure ?
- [x] ignore dot directories in recipes store in order to support jupyter notebooks
- [ ] volatile recipes
- [x] datafusion parquet_sql recipe

## Integration of external components

- [x] sweetviz support
- [x] polars support
- [ ] spark support - spark dataframes
- [x] python-pptx integration
- [ ] d-tale support
- [ ] markdown support
- [x] PIL
- [ ] bokeh
- [x] datafusion support - context and sql
- [ ] keras history support
- [ ] numpy support
- [x] parquet support
- [x] integrate pointcloud explorer - see [Pointcloud Explorer](https://github.com/orest-d/pointcloud-viewer-rs)
- [ ] SQL cache working on Hive
- [ ] pandas series and groupby objects
- [ ] geopandas and folium
- [ ] jinja and/or other templating engines
- [ ] onnx
- [ ] TF Lite
- [ ] pdf
- [ ] epub
- [ ] 3d formats stl, obj
- [ ] gcode

## Core functionality and Metadata

- [ ] fix parser test_root
- [ ] query origin (file, line number if possible)
- [ ] search engine(s) integration
- [x] refactor metadata handling to a separate class from context and state
- [ ] finalize refactoring of Context to Metadata
- [ ] python logging integration with metadata and context

- [ ] commands from methods
- [ ] automatic state type from classes
- [ ] query meta modifier similar to -R-meta
- [ ] automatic argument type conversion
- [x] split context to mixins
- [ ] improve scheduling - prevent same queries to be scheduled
- [ ] remove commands and extended commands from metadata
- [ ] dependency injection input type
- [ ] debug transform query
- [ ] attribute to prevent cloning
- [ ] git support

## Highlevel features, useful commands, Examples and Documentation

- [ ] start liquer-ml
- [x] dataframe batches
- [ ] report template
- [ ] default data-science app example
- [ ] better chart library
- [ ] better pandas functions (eq, lt, gt, leq, geq, isin, notin, between, groupby, random)
- [ ] conventions and ML library 

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
