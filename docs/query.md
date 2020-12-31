# Query

## Basic query

Query is in the simplest case composed out of a sequence of actions.
Action is nothing else than a function (closure) with all arguments specified except the first one.
All actions consume a single input and produce a single output - so they can be chained into a pipeline. 

In the *Hello, world!* example from earlier, the ```hello/greet-everybody``` is a sequence of two actions.
The first action is ```hello``` does not have any explicit parameters. (Technically it accepts an input - but that input is ignored, so this function is suitable to be at the beginning of the pipeline.)
The ```greet-everybody``` is and action calling a command ```greet``` with an argument "everybody".

The general structure of a query is

* **actions** are separated by "/",
* **arguments** are separated by "-":

```
identifier1-arg11-arg12/identifier2-arg21-arg22-arg23/identifier3-arg31...
```

Action starts with an identifier, which is interpreted as a command name. In practice, the command is always defined
via a python function with the same name. Therefore identifier must be a valid python identifier plus it can't start with an upper case. Thus "my_command" is a valid identifier, but "MyCommand", "1command" or "my.command" is not.

Query is optionaly terminated by a filename. A valid filename must fulfill the following conditions:

* Filename is the last element in a query, i.e. there is no "/" after the filename.
* Filename must contain ".".
* Filename can not contain "-".

These rules assure that a filename can be recognized from a command name or an argument.
For example ```readme.txt``` is a valid filename, but ```readme-now.txt``` would be interpreted as an action composed from a command ```readme``` with an argument "now.txt".

The main role of a filename is to specify the file extension, which determines the format in which the data are serialized when saved or returned via a web interface. The filename before the extension is arbitrary.

## Escaping and query entities

Query only allows to use the characters allowed in the path part of the URL, and the following characters have a special meaning:

* **slash** "/" separates the actions,
* **dash** "-" separates action arguments and query segments,
* **tilde** "~" is used as an escape character.

There are two mechanisms that can be used for escaping:
* **Percentage encoding** used for encoding special characters in URL - see e.g. https://en.wikipedia.org/wiki/Percent-encoding
* **Query entities** are constructs starting with the tilde character "~". Query entities have special meaning, e.g. they can be used for encoding of "-", "/" and "~". Though encoding of these characters with the percentage encoding might work as well,
it is safer to use query entities (tilde encoding).

The following entities are defined:

* **tilde entity** "~~" expands to "~"
* **minus entity** "~_" expands to "-"
* **slash entities** "~I" and "~/" expand to "/"
* **https entity** "~H" expands to "https://"
* **http entity** "~h" expands to "http://"
* **file entity** "~f" expands to "file://"
* **protocol entity** "~P" expands to "://"
* **negative number entities** "~0","~1","~2" ... "~9" expand to "-0", "-1", "-2" ... "-9". (This is a more convenient alternative syntax for writing negative numbers like "~123" instead of "~_123".
* **space entity** "~." expands to " "
* **expand entity** "~X~*query*~E" evaluates the query and expands to a result
* **end_entity** "~E" is not a real entity, but can only be part of a complex entity like the **expand entity**.

**Expand entity** supports two types of queries - absolute starting with "/" and relative (not starting with "/").
Absolute entities are simply evaluated as they are, but relative entities are pre-pended with the current query before the execution. For example ```hello/greet-~X~/everybody~E``` is interpreted as ```greet(hello(), everybody())```,
but the relative query in an argument ```hello/greet-~X~everybody~E``` is interpreted as
```greet(hello(), everybody(hello()))```.

