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

class RecipeVersionCollisionException(VersionCollisionException):
    def __init__(self, message=None, query=None, recipe_name=None):
        if message is None:
            message = f"Version collision for recipe '{recipe_name}' for query '{query}'"
        super().__init__(message=message, query=query)

class Dependencies:
    def __init__(self, dependencies=None):
        if dependencies is None:
            dependencies={}
        self.set_dependencies(dependencies)

    def set_dependencies(self, dependencies):
        if "query" not in dependencies:
            dependencies["query"] = ""
        if "commands" not in dependencies:
            dependencies["commands"] = {}
        if "recipe" not in dependencies:
            dependencies["recipe"] = {}
        dependencies["recipe"]["version"]=dependencies["recipe"].get("version")

        self.dependencies = dependencies
        return self

    def as_dict(self):
        return deepcopy(self.dependencies)

    @property
    def query(self):
        return self.dependencies["query"]

    @query.setter
    def query(self, value):
        self.dependencies["query"] = value

    def add_command_dependency(self, ns, command_metadata, detect_collisions=True):
        key = f"ns-{ns}/{command_metadata.name}"
        version = command_metadata.version
        if detect_collisions:
            if key in self.dependencies["commands"]:
                old_version=self.dependencies["commands"][key]
                if old_version!=version:
                    print(f"Version collision for command '{command_metadata.name}' in namespace '{ns}' for query '{self.query}'")
                    print(f"Existing version: {old_version}")
                    print(f"New version:      {version}")
                    raise CommandVersionCollisionException(command=command_metadata.name, ns=ns, query=self.query)
        self.dependencies["commands"][key]=version
        return self
        
    def add_recipe_dependency(self, recipe, detect_collisions=True):
        recipe_name = recipe.recipe_name()
        version = recipe.version()
        if detect_collisions:
            old_version = self.dependencies["recipe"].get("version")
            if old_version is not None:
                if old_version!=version:
                    print(f"Version collision for recipe '{recipe_name}' for query '{self.query}'")
                    print(f"Existing version: {old_version}")
                    print(f"New version:      {version}")
                    raise RecipeVersionCollisionException(recipe_name=recipe_name, query=self.query)
        self.dependencies["recipe"]["name"]=recipe_name
        self.dependencies["recipe"]["version"]=version
        return self
