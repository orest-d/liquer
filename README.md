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

# TODO

- [x] namespaces
- [ ] support for dataframe iterator 
- [x] lift the requirement for a state to be cloneable - at least for some data types
- [x] make indicator of *volatile* state, that can never be cached (volatile=immutable?)
- [x] specify metadata in command decorator
- [x] cache categories/levels dependent on metadata
- [ ] remote liquer service as cache
- [ ] improve command catalogue
- [ ] automatic dependent query recording
- [ ] implied volatile (query result dependent on a volatile query should be volatile)
- [ ] attributes to prevent cloning and caching
- [ ] prevent crashing on non-cloneable types - automatic volatile ?
- [x] basic keras support
- [ ] keras history support
- [ ] numpy support
- [ ] scikit support
- [ ] command/query GUI
- [ ] fix volatility logic - now just the state does not get cloned 
- [ ] meta extension (in progress)
- [ ] parquet support
- [ ] simple GUI
- [ ] composite state (MVP: state can be a list or dict of 'normal' states)
