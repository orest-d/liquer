# LiQuer (Link Query) 

LiQuer is a simplistic syntax (mini query language) aimingto be used inside URLs
 - either as a part of the path or as an anchor string.
It represents a sequence of operations performed applied to a state.
The state can in principle be any type of data, but the main usecase
is dataframes, documents and images.

Liquer can be used to do simple manipulation of tabular data sources, typically csv files stored on the internet.
Liquer can easily be extended with new commands.
Flask integration is provided by a blueprint.

Query consists of a sequence of commands, each command is a sequence of string tokens, the first token identifies the command.
Syntactically the sequences are separated by "/".

