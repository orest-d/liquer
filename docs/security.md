# Security

LiQuer was so far only deployed on intranet. More development is needed to make interent deployment of LiQuer safe.

LiQuer exposes only services defined in the ``liquer.blueprint`` module - and by extension all the registered commands.
Only enable commands that do not put your system to risk.

A big source of security concerns are DOS attacks:
* It is easy to overload LiQuer server with huge queries. To solve this issue, queries need to be validated in some way.
* Badly implemented cache may quickly exceed the storage capacity. (Default ``NoCache`` is a safe choice in this respect.) 

