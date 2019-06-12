# LiQuer (Link Query) 

LiQuer is a minimalistic python framework on top of flask, which simplifies creation of web services and web interfaces,
particularly in connection to data science: working with data frames, charts and reports.
The core of LiQuer is a simplistic query language, that can represent a chain of transformations (*commands*)
applied to an arbitrary data object (e.g. a dataframes, text, json, images). LiQuer query is safe to use inside URLs
and is interpreted and executed by a LiQuer server that is available as a flask blueprint.
LiQuer is very modular and designed to be extremely easy to extend (typically just by simple decorators and use of conventions).
Results of LiQuer queries can be cached for added performance.

Please visit [https://orest-d.github.io/liquer/](LiQuer website) for more info.
