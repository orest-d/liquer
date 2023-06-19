# Commands

By decorating a function with ``@command`` or ``@first_command``, 
the function is registered in a command registry.
Function is only registered, not modified or wrapped in any way - therefore it can be used as if it would not be decorated at all.
Commands (command functions) typically need to be enabled in a LiQuer application simply by importing a module
with command-decorated functions. Built-in modules need to be imported as well - this gives control about enabled features
and as well allows to limit dependencies (e.g. in principle LiQuer application only requires pandas when ``liquer.ext.lq_pandas`` is imported.) 

When a command function is registered, metadata are extracted based on available informations and conventions:

* Function name becomes a name of the command. Modules can not be distinguished inside the query, therefore command (and hence functions) should have unique names even when they are defined in multiple modules.
* When decorated with ``@command``, the first argument of the function will always be a state.
* If the first argument is called ``state``, command function will receive the state as an instance of ``State``,
otherwise it will be just plain data. Plain data can be obtained from ``state`` by ``state.get()``.  
* When decorated with ``@first_command``, command will not receive a state at all.
* Command registration tries to identify all the arguments and their types. The types are guessed either from type annotations (if available) or from default values. Default values and ``*args`` are suported, the ``**kwargs`` are not supported in commands.
* Parsed string arguments are converted to estimated types before they are passed to the command. This is done with help of argument parsers (see ``liquer.commands.ArgumentParser``).
* Command function may return any data type. If it does not return an instance of ``State``, the returned data is automatically wrapped as a ``State`` when evaluated.

The main purpose of ``State`` instance is to add metadata to the data (e.g. the query executed sofar, data sources used, type of the data, file name). It as well provides a logging functionality, which can record messages and errors during the execution of the query. See ``liquer.state`` for more info. 


