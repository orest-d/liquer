from copy import deepcopy

class DependencyException(Exception):
    def __init__(self, message, query=None):
        self.original_message = message
        if query is not None:
            message += f":\n  query: '{query}'"

        super().__init__(message)
        self.query = query

class VersionCollisionException(Exception):
    def __init__(self, message, query=None):
        self.original_message = message
        if query is not None:
            message += f":\n  query: '{query}'"

        super().__init__(message)
        self.query = query

class CommandVersionCollisionException(VersionCollisionException):
    def __init__(self, message=None, query=None, command=None, ns=None):
        if message is None:
            message = f"Version collision for command '{command}' in namespace '{ns}' for query '{query}'"
        super().__init__(message=message, query=query)


class Dependencies:
    def __init__(self, dependencies={}):
        self.set_dependencies(dependencies)

    def set_dependencies(self, dependencies):
        if "query" not in dependencies:
            dependencies["query"] = ""
        if "commands" not in dependencies:
            dependencies["commands"] = {}
        self.dependencies = dependencies
        return self

    def as_dict(self):
        return deepcopy(self.dependencies)

    @property
    def query(self):
        return self.metadata["query"]

    @query.setter
    def query(self, value):
        self.metadata["query"] = value

    def add_command_dependency(self, ns, command_metadata, detect_collisions=True):
        key = f"ns-{ns}/{command_metadata.name}"
        version = command_metadata.version
        if detect_collisions:
            if key in self.dependencies["commands"]:
                if self.dependencies["commands"][key]!=version:
                    raise CommandVersionCollisionException(command=command_metadata.name, ns=ns, query=self.query)
        self.dependencies["commands"][key]=version
        return self