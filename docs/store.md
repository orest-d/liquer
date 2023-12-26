# Store

## Why we need a store?

Working with simple queries, several wishes appear:

- It would be useful to make shortcuts for the most frequent queries.
- It would be nice if these frequent queries would only need to be executed once and the results of these queries would be stored.
- Results of frequent queries should be stored in a desirable format - e.g. csv or xlsx.
- We still want to know how the result was created, eventually have a log file associated with it.
- It would be useful to use files as input to queries.
- These files might be stored in local filesystem, but possibly in some key-value store (e.g. an S3 bucket), on an FTP server or in a database.

All these wishes are satisfied by a *LiQuer store*:
- Store works as an abstraction over a file system: it can access a local directory, a key-value store (e.g. S3) or a remote file-system (e.g. FTP) via a unified interface.
- LiQuer query can reference a file in the store as an input to the pipeline.
- Queries can be stored in recipes, where they can be evaluated on demand.
- Store is extensible: New types of store (e.g. support for a key-value store) can be implemented. Different stores can be combined by mounting them into the file tree.
- Store is accessible via a web server, where basic operations can be done via a web GUI: browsing, inspecting log files, deleting, creating and editing of text files.  

## What is a store?
*Store* is a configurable virtual file system inside liquer. *Store* is designed to be able to deal with states. One notable extension of the *Store* compared to a regular file system is the ability to store (and work with) the metadata, which is essential for dealing with data in liquer.  

*Store* is basically a key/value store mapping a path to a sequence of bytes. By itself, *Store* does not define (or care) about serialization of the data. This differenciates it from *Cache*.

Even though the interface to *Cache* and *Store* is intentionaly very similar, these two mechanisms are different:

* *Cache* keeps *State* (i.e. data object with metadata). *Cache* deals with objects and stores *State* perhaps in a non-serialized form (e.g. MemoryStore).
* *Store* keeps resources - i.e. arbitrary binary data (*bytes*) complemented with metadata. 

One purpose of a *Store* is to provide an option to serve files into the pipeline. The pipeline may start with a resource path followed by a sequence of actions.

# Cache

By default there is no cache - i.e. the queries are always re-evaluated.
There are several cache implementations available in ``liquer.cache``.
They are configured by ``set_cache`` function, for example

```python
set_cache(FileCache("cache"))
```

configures a cache that will store all the (chache-able) results of queries
in a dictionary *cache*.
Cache should be configured before the queries are evaluated - and before state variables are set.

Currently there are three cache implementations: ``NoCache`` is a trivial do-nothing cache, ``FileCache`` stores data in files, ``MemoryCache`` caches
the object in the memory.

Custom cache can be created by defining a cache interface, see above mentioned classes. Cache will typically use query as a key and utilize the mechanism of serializing data into a bytes sequence (defined in ``liquer.state_types``), thus implementing a cache based either on a key-value store or blob-storage in SQL databases should be fairly straightforward (and probably quite similar to ``FileCache``).

Command may optionally decide not to cache its output. This may be useful when command produces volatile data, e.g. time.
In such a case command (operating on a state) can disable cache by ``state.with_caching(False)``.

