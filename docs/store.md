# Store

*Store* is a configurable virtual file system inside liquer. *Store* is designed to be able to deal with states. One notable extension of the *Store* compared to a regular file system is the ability to store (and work with) the metadata, which is essential for dealing with data in liquer.  

*Store* is basically a key/value store mapping a path to a sequence of bytes. By itself, *Store* does not define (or care) about serialization of the data. This differenciates it from *Cache*.

Even though the interface to *Cache* and *Store* is intentionaly very similar, these two mechanisms are different:

* *Cache* keeps *State* (i.e. data object with metadata). *Cache* deals with objects and stores *State* perhaps in a non-serialized form (e.g. MemoryStore).
* *Store* keeps resources - i.e. arbitrary binary data (*bytes*) complemented with metadata. 

One purpose of a *Store* is to provide an option to serve files into the pipeline. The pipeline may start with a resource path followed by a sequence of actions.
