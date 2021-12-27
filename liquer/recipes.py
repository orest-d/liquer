from liquer.store import get_store, Store, KeyNotFoundStoreException, StoreException, join_key, parent_key
from liquer.context import get_context
from liquer.parser import parse
from liquer.constants import Status
from liquer.metadata import Metadata

from copy import deepcopy
import traceback
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

class RecipeException(Exception):
    def __init__(self, message, key=None):
        self.original_message = message
        if key is not None:
            message += f":\n  key: '{key}'"

        super().__init__(message)
        self.key = key

class RecipeRegistry(object):
    """Registry of recipes"""
    def __init__(self):
        self.recipe_dictionary = {}
    def register(self, recipe):
        if recipe.recipe_type() in self.recipe_dictionary:
            print(f"WARNING: Recipe type '{recipe.recipe_type()}' already registered")
        self.recipe_dictionary[recipe.recipe_type()] = recipe
    def from_dict(self, d):
        if type(d) != dict:
            raise Exception("Dictionary expected as recipe definition for registered recipes")
        if "type" not in d:
            raise Exception("Recipe definition is lacking a type")
        if d["type"] not in self.recipe_dictionary:
            t=d["type"]
            raise Exception(f"Recipe type '{t}' not registered")
        return self.recipe_dictionary[d["type"]].from_dict(d)

_recipe_registry = None


def recipe_registry():
    """Returns the global recipe registry (singleton)"""
    global _recipe_registry
    if _recipe_registry is None:
        _recipe_registry = RecipeRegistry()
    return _recipe_registry

def register_recipe(recipe):
    """Function to register new recipe type.
    """
    recipe_registry().register(recipe)

class Recipe:
    def __init__(self,d):
        if type(d) != dict:
            raise Exception("Dictionary expected as recipe definition")
        if "type" in d:
            if d["type"]!=self.recipe_type():
                t=d["type"]
                raise Exception(f"Recipe {self.recipe_type()} received definition with type='{t}'")
        self.data=d
    
    @classmethod
    def recipe_type(self):
        return "empty"

    @classmethod
    def from_dict(cls,d):
        return cls(d)
    
    def recipe_name(self):
        return self.data.get("recipe_name","")

    def provides(self):
        return self.data.get("provides",[])

    def can_create(self,name):
        return name in self.provides()

    def metadata(self, key):
        raise RecipeException("Recipe undefined (metadata)",key=key)
      
    def make(self, key, context=None):
        raise RecipeException("Recipe undefined (make)",key=key)

    def is_volatile(self):
        return self.data.get("volatile", False)

def resolve_recipe_definition(r, directory, metadata):
    if type(r) == str:
        try:
            query = parse(r)
            filename = query.filename()
            return dict(
                type="query",
                query=r,
                CWD = directory,
                filename=filename,
                provides=[filename]
            )
        except:
            metadata.warning(f"Can't resolve recipe '{r}'", traceback=traceback.format_exc())
            traceback.print_exc()
    elif isinstance(r, dict):
        if r.get("type") in (None, "query") and "query" in r:
            try:
                query = parse(r["query"])
                filename = r.get("filename", query.filename())
                title = r.get("title", filename)
                description = r.get("description", f'Generated from query: {r["query"]}')
                rkey =  join_key(directory, filename)
                return dict(
                    type="query",
                    query=r["query"],
                    title=title,
                    description=description,
                    CWD = directory,
                    filename=filename,
                    provides=[filename]
                )
            except:
                metadata.warning(f"Can't resolve query recipe", traceback=traceback.format_exc())
                traceback.print_exc()
    else:
        print(f"Unsupported recipe type: {type(r)}")
    if "filename" in r and "provides" not in r:
        r["provides"] = [r["filename"]]
    return r

class QueryRecipe(Recipe):
    @classmethod
    def recipe_type(self):
        return "query"

    @classmethod
    def from_dict(cls,d):
        return cls(d)
        
    def metadata(self, key):
        metadata = Metadata(dict())
        if "title" in self.data:
            metadata.metadata["title"] = self.data["title"]
        if "description" in self.data:
            metadata.metadata["description"] = self.data["description"]
        metadata.query = self.data["query"]
        metadata.key=key
        return metadata.as_dict()
      
    def make(self, key, store=None, context=None):
        context = get_context(context)
        if store is None:
            store = context.store()
        context.evaluate(
            self.data["query"],
            store_key=key,
            store_to=store,
        )

register_recipe(QueryRecipe)

class RecipeStore(Store):
    def __init__(self, store, recipes=None, context=None):
        self.substore = store
        self.substore.parent_store=self
        self._recipes = {} if recipes is None else recipes
        self.context = context

    def get_context(self):
        if self.context is None:
            return get_context()
        else:
            return self.context.new_empty()

    def with_context(self, context):
        return RecipeStore(self.substore, recipes=self.recipes, context=context)

    def mount_recipe(self, key, recipe):
        self._recipes[key] = recipe
        return self

    def ignore(self, key):
        return False

    def make(self, key):
        if self.ignore(key):
            raise Exception(f"Key {key} is ignored, can't make it")
        query = self.recipes().get(key)
        if query is None:
            raise KeyNotFoundStoreException(
                f"Key {key} not found, recipe unknown", key=key, store=self
            )
        target_resource_directory = self.parent_key(key)
        target_file = self.key_name(key)
        self.get_context().evaluate(
            query,
            store_key=key,
            store_to=self,
        )
        self.on_data_changed(key)
        self.on_metadata_changed(key)

    def recipes(self):
        return self._recipes

    def recipe_metadata(self, key):
        return {}

    def is_supported(self, key):
        if self.ignore(key):
            return False
        return self.substore.is_supported(key)

    def get_bytes(self, key):
        if self.ignore(key):
            return None
        if self.substore.contains(key):
            return self.substore.get_bytes(key)
        self.make(key)
        return self.substore.get_bytes(key)

    def get_metadata(self, key):
        if self.ignore(key):
            raise KeyNotFoundStoreException(key=key, store=self)
        if self.substore.contains(key):
            return self.substore.get_metadata(key)
        if self.is_dir(key):
            return self.finalize_metadata(
                self.default_metadata(key=key, is_dir=True), key=key, is_dir=True
            )
        if key in self.recipes():
            metadata = self.recipe_metadata(key)
            try:
                sub_metadata = self.substore.get_metadata(key)
                if sub_metadata is not None:
                    metadata.update(sub_metadata)
            except:
                pass
            return self.finalize_metadata(metadata, key=key, is_dir=False)
        raise KeyNotFoundStoreException(key=key, store=self)

    def store(self, key, data, metadata):
        if self.ignore(key):
            raise Exception(f"Key {key} is ignored, can't store into it")
        self.substore.store(
            key, data, self.finalize_metadata(metadata, key=key, is_dir=True, data=data)
        )
        self.on_data_changed(key)
        self.on_metadata_changed(key)

    def store_metadata(self, key, metadata):
        if self.ignore(key):
            raise Exception(f"Key {key} is ignored, can't store metadata into it")
        self.substore.store_metadata(key, metadata)
        self.on_metadata_changed(key)

    def remove(self, key):
        self.substore.remove(key)
        self.on_removed(key)

    def removedir(self, key):
        self.substore.removedir(key)
        self.on_removed(key)

    def contains(self, key):
        if self.ignore(key):
            return False
        if self.substore.contains(key):
            return True
        for k in self.recipes():
            if k == key or k.startswith(key + "/"):
                return True
        return False

    def is_dir(self, key):
        if self.ignore(key):
            return False
        if self.substore.is_dir(key):
            return True
        for k in self.recipes():
            if k == key:
                return False
            if k.startswith(key + "/"):
                return True
        return False

    def keys(self):
        return [
            key
            for key in sorted(set(self.substore.keys()).union(self.recipes().keys()))
            if not self.ignore(key)
        ]

    def listdir(self, key):
        if self.ignore(key):
            return []
        d = set(self.substore.listdir(key) or [])
        key_split = key.split("/")
        if len(key_split) == 1 and key_split[0] == "":
            key_split = []
        key_depth = len(key_split)
        for k in self.recipes().keys():
            if k.startswith(key + "/") or key in (None, ""):
                v = k.split("/")
                d.add(v[key_depth])
        return [key for key in sorted(d) if not self.ignore(key)]

    def makedir(self, key):
        if self.ignore(key):
            raise Exception(f"Key {key} is ignored, can't makedir")
        self.substore.makedir(key)
        self.on_data_changed(key)
        self.on_metadata_changed(key)

    def openbin(self, key, mode="r", buffering=-1):
        if self.ignore(key):
            raise Exception(f"Key {key} is ignored, can't openbin")
        return self.substore.openbin(key, mode=mode, buffering=buffering)

    def __str__(self):
        return f"Recipe store on ({self.substore})"

    def __repr__(self):
        return f"RecipeStore({repr(self.substore)}, recipes={repr(self.recipes())})"


class OldRecipeSpecStore(RecipeStore):
    RECIPES_FILE = "recipes.yaml"
    LOCAL_RECIPES = "RECIPES"
    STATUS_FILE = "recipes_status.txt"

    def __init__(self, store, context=None):
        RecipeStore.__init__(self, store, recipes=None, context=context)
        self.recipes_info = {}
        self.update_recipes()
        self.update_all_status_files()

    def update_all_status_files(self):
        if self.STATUS_FILE is not None:
            for dir_key in set(self.parent_key(key) for key in self.recipes().keys()):
                self.create_status(dir_key)

    def ignore(self, key):
        if key is None:
            return True
        return any(x.startswith(".") for x in key.split("/"))

    def recipe_metadata(self, key):
        metadata = deepcopy(self.recipes_info.get(key, {}))
        metadata["status"] = Status.RECIPE.value
        if metadata.get("query") is not None:
            metadata["has_recipe"] = True
            if self.recipes_info[key].get("recipes_directory") == self.LOCAL_RECIPES:
                metadata["recipes_directory"] = ""
            else:
                metadata["recipes_directory"] = self.recipes_info[key].get(
                    "recipes_directory"
                )
        return metadata

    def make(self, key):
        print(f"### MAKE {key}")
        super().make(key)
        metadata = self.substore.get_metadata(key)
        status = metadata.get("status", Status.RECIPE.value)
        fileinfo = metadata["fileinfo"]
        metadata.update(self.recipe_metadata(key))
        metadata["status"] = status
        metadata["fileinfo"] = fileinfo
        self.substore.store_metadata(key, metadata)
        self.on_metadata_changed(key)

    def update_recipes(self):
        import yaml

        recipes = {}
        for key in self.substore.keys():
            spec = None
            if self.key_name(key) == self.RECIPES_FILE and not self.substore.is_dir(
                key
            ):
                spec = yaml.load(self.substore.get_bytes(key), Loader=Loader)
            recipes_key = key
            if spec is not None:
                parent = self.parent_key(key)
                for directory, items in spec.items():
                    for r in items:
                        if type(r) == str:
                            try:
                                query = parse(r)
                                filename = query.filename()
                                parent = self.parent_key(key)
                                if len(parent) > 0 and not parent.endswith("/"):
                                    parent += "/"
                                rkey = (
                                    f"{parent}{filename}"
                                    if directory == self.LOCAL_RECIPES
                                    else f"{parent}{directory}/{filename}"
                                )
                                recipes[rkey] = r
                                self.recipes_info[rkey] = dict(
                                    query=r,
                                    title=filename,
                                    description="",
                                    recipes_key=recipes_key,
                                    recipes_directory=directory,
                                )
                            except:
                                traceback.print_exc()
                        elif isinstance(r, dict):
                            try:
                                query = parse(r["query"])
                                filename = r.get("filename", query.filename())
                                title = r.get("title", filename)
                                description = r.get("description", r["query"])
                                parent = self.parent_key(key)
                                if len(parent) > 0 and not parent.endswith("/"):
                                    parent += "/"
                                rkey = (
                                    f"{parent}{filename}"
                                    if directory == self.LOCAL_RECIPES
                                    else f"{parent}{directory}/{filename}"
                                )
                                recipes[rkey] = r["query"]
                                self.recipes_info[rkey] = dict(
                                    query=r["query"],
                                    title=title,
                                    description=description,
                                    recipes_key=recipes_key,
                                    recipes_directory=directory,
                                )
                            except:
                                traceback.print_exc()
                        else:
                            print(f"Unsupported recipe type: {type(r)}")
        self._recipes = recipes
        return recipes

    def create_status_text(self, dir_key):
        txt = ""
        if self.substore.is_dir(dir_key):
            for d in self.listdir(dir_key):
                key = f"{dir_key}/{d}" if len(dir_key) else d
                if d == self.STATUS_FILE:
                    continue
                if not self.is_dir(key):
                    metadata = self.get_metadata(key)
                    if metadata is None:
                        txt += "%-14s %-30s %s\n" % ("MISSING", d, "Missing metadata")
                    else:
                        try:
                            t = metadata.get("created")
                            if t in ("", None):
                                t = metadata["updated"]
                            time = util.format_datetime(util.to_datetime(t))
                        except:
                            time = ""
                        status = metadata.get("status", Status.NONE.value)
                        message = metadata.get("message", "").strip()
                        if status == Status.READY.value:
                            try:
                                message = metadata["data_characteristics"][
                                    "description"
                                ]
                            except:
                                pass
                        if "\n" in message:
                            txt += "%-20s %-14s %-32s|" % (time, status, d)
                            txt += "\n=============================================================\n"
                            txt += message
                            txt += "\n=============================================================\n\n"
                        else:
                            txt += "%-20s %-14s %-32s| %s\n" % (
                                time,
                                status,
                                d,
                                message,
                            )
                        trace = ""
                        for entry in metadata.get("log", []) + metadata.get(
                            "child_log", []
                        ):
                            tb = entry.get("traceback")
                            if tb is not None:
                                if len(tb):
                                    if "timestamp" in entry:
                                        trace += f"Time:    {entry['timestamp']}"
                                    if "origin" in entry:
                                        trace += f"Origin:  {entry['origin']}"
                                    if "message" in entry:
                                        trace += f"Message: {entry['message']}"
                                    trace += "\n"
                                    trace += tb
                                    tb += "\n------------------------\n"
                        if len(trace):
                            txt += "\n### TRACEBACK ###############################################\n"
                            txt += trace
                            txt += "\n#############################################################\n\n"
        return txt

    def create_status(self, key):
        if self.key_name(key) != self.STATUS_FILE:
            if not self.is_dir(key):
                key = self.parent_key(key)
            status_key = f"{key}/{self.STATUS_FILE}" if len(key) else self.STATUS_FILE
            data = self.create_status_text(key).encode("utf-8")
            self.substore.store(
                status_key,
                data,
                dict(
                    type_identifier="text",
                    status=Status.SIDE_EFFECT.value,
                    title=f"Status of '{key}'",
                    description="This file is generated automatically by the recipe store",
                ),
            )

    def on_metadata_changed(self, key):
        super().on_metadata_changed(key)
        if self.STATUS_FILE is not None:
            if self.key_name(key) == self.RECIPES_FILE:
                self.update_all_status_files()
            elif self.key_name(key) != self.STATUS_FILE:
                self.create_status(key)

    def on_data_changed(self, key):
        super().on_data_changed(key)
        if self.key_name(key) == self.RECIPES_FILE:
            self.update_recipes()
            self.update_all_status_files()
        else:
            self.create_status(key)

    def on_removed(self, key):
        super().on_removed(key)
        if self.key_name(key) == self.RECIPES_FILE:
            self.update_recipes()
            self.update_all_status_files()
        else:
            self.create_status(key)

class NewRecipeSpecStore(Store):
    RECIPES_FILE = "recipes.yaml"
    LOCAL_RECIPES = "RECIPES"
    STATUS_FILE = "recipes_status.txt"

    def __init__(self, store):
        self.substore = store
        self.substore.parent_store=self
        self._recipes = {}
        self.update_recipes()
        self.update_all_status_files()

    def recipes(self):
        return self._recipes

    def make(self, key):
        print(f"### MAKE {key}")
        if self.ignore(key):
            raise Exception(f"Key {key} is ignored, can't make it")

        recipe = self.recipes().get(key)
        if recipe is None:
            raise KeyNotFoundStoreException(
                f"Key {key} not found, recipe unknown", key=key, store=self
            )
        recipe.make(key, store=self.substore)

        metadata = self.substore.get_metadata(key)
        status = metadata.get("status", Status.RECIPE.value)
        fileinfo = metadata["fileinfo"]
        metadata.update(self.recipe_metadata(key))
        metadata["status"] = status
        metadata["fileinfo"] = fileinfo
        self.substore.store_metadata(key, metadata)
        self.on_data_changed(key)
        self.on_metadata_changed(key)


    def recipe_metadata(self, key):
        if self.ignore(key):
            raise Exception(f"Key {key} is ignored, can't make it")

        recipe = self.recipes().get(key)
        if recipe is None:
            raise KeyNotFoundStoreException(
                f"Key {key} not found, recipe unknown", key=key, store=self
            )
        metadata = recipe.metadata(key)
        metadata["status"] = Status.RECIPE.value
        metadata["has_recipe"] = True

        return metadata

    def is_supported(self, key):
        if self.ignore(key):
            return False
        return self.substore.is_supported(key)

    def get_bytes(self, key):
        if self.ignore(key):
            return None
        if self.substore.contains(key):
            return self.substore.get_bytes(key)
        self.make(key)
        return self.substore.get_bytes(key)

    def get_metadata(self, key):
        if self.ignore(key):
            raise KeyNotFoundStoreException(key=key, store=self)
        if self.substore.contains(key):
            return self.substore.get_metadata(key)
        if self.is_dir(key):
            return self.finalize_metadata(
                self.default_metadata(key=key, is_dir=True), key=key, is_dir=True
            )
        if key in self.recipes():
            metadata = self.recipe_metadata(key)
            try:
                sub_metadata = self.substore.get_metadata(key)
                if sub_metadata is not None:
                    metadata.update(sub_metadata)
            except:
                pass
            return self.finalize_metadata(metadata, key=key, is_dir=False)
        raise KeyNotFoundStoreException(key=key, store=self)

    def store(self, key, data, metadata):
        if self.ignore(key):
            raise Exception(f"Key {key} is ignored, can't store into it")
        self.substore.store(
            key, data, self.finalize_metadata(metadata, key=key, is_dir=True, data=data)
        )
        self.on_data_changed(key)
        self.on_metadata_changed(key)

    def store_metadata(self, key, metadata):
        if self.ignore(key):
            raise Exception(f"Key {key} is ignored, can't store metadata into it")
        self.substore.store_metadata(key, metadata)
        self.on_metadata_changed(key)

    def remove(self, key):
        self.substore.remove(key)
        self.on_removed(key)

    def removedir(self, key):
        self.substore.removedir(key)
        self.on_removed(key)

    def contains(self, key):
        if self.ignore(key):
            return False
        if self.substore.contains(key):
            return True
        for k in self.recipes():
            if k == key or k.startswith(key + "/"):
                return True
        return False

    def is_dir(self, key):
        if self.ignore(key):
            return False
        if self.substore.is_dir(key):
            return True
        for k in self.recipes():
            if k == key:
                return False
            if k.startswith(key + "/"):
                return True
        return False

    def keys(self):
        return [
            key
            for key in sorted(set(self.substore.keys()).union(self.recipes().keys()))
            if not self.ignore(key)
        ]

    def listdir(self, key):
        if self.ignore(key):
            return []
        d = set(self.substore.listdir(key) or [])
        key_split = key.split("/")
        if len(key_split) == 1 and key_split[0] == "":
            key_split = []
        key_depth = len(key_split)
        for k in self.recipes().keys():
            if k.startswith(key + "/") or key in (None, ""):
                v = k.split("/")
                d.add(v[key_depth])
        return [key for key in sorted(d) if not self.ignore(key)]

    def makedir(self, key):
        if self.ignore(key):
            raise Exception(f"Key {key} is ignored, can't makedir")
        self.substore.makedir(key)
        self.on_data_changed(key)
        self.on_metadata_changed(key)

    def openbin(self, key, mode="r", buffering=-1):
        if self.ignore(key):
            raise Exception(f"Key {key} is ignored, can't openbin")
        return self.substore.openbin(key, mode=mode, buffering=buffering)

    def __str__(self):
        return f"Recipe spec store n ({self.substore})"

    def __repr__(self):
        return f"RecipeSpecStore({repr(self.substore)})"


    def update_all_status_files(self):
        if self.STATUS_FILE is not None:
            for dir_key in set(parent_key(key) for key in self.recipes().keys()):
                self.create_status(dir_key)

    def ignore(self, key):
        if key is None:
            return True
        return any(x.startswith(".") for x in key.split("/"))


    def update_recipes(self):
        import yaml

        recipes = {}
        for key in self.substore.keys():
            spec = None
            if self.key_name(key) == self.RECIPES_FILE and not self.substore.is_dir(
                key
            ):
                spec = yaml.load(self.substore.get_bytes(key), Loader=Loader)
            recipes_key = key
            metadata = Metadata(self.substore.get_metadata(key))
            if spec is not None:
                parent = parent_key(key)
                for directory, items in spec.items():
                    for i, r in enumerate(items):
                        cwd = parent if directory == self.LOCAL_RECIPES else join_key(parent, directory)
                        d = resolve_recipe_definition(r, cwd, metadata)
                        d["recipe_name"] = self.to_root_key(recipes_key)+f":{directory}[{i}]"+d.get("filename","")
                        recipe = recipe_registry().from_dict(d)
                        for name in recipe.provides():
                            key = join_key(cwd, name)
                            recipes[key]=recipe
        self._recipes = recipes
        return recipes

    def create_status_text(self, dir_key):
        txt = ""
        if self.substore.is_dir(dir_key):
            for d in self.listdir(dir_key):
                key = f"{dir_key}/{d}" if len(dir_key) else d
                if d == self.STATUS_FILE:
                    continue
                if not self.is_dir(key):
                    metadata = self.get_metadata(key)
                    if metadata is None:
                        txt += "%-14s %-30s %s\n" % ("MISSING", d, "Missing metadata")
                    else:
                        try:
                            t = metadata.get("created")
                            if t in ("", None):
                                t = metadata["updated"]
                            time = util.format_datetime(util.to_datetime(t))
                        except:
                            time = ""
                        status = metadata.get("status", Status.NONE.value)
                        message = metadata.get("message", "").strip()
                        if status == Status.READY.value:
                            try:
                                message = metadata["data_characteristics"][
                                    "description"
                                ]
                            except:
                                pass
                        if "\n" in message:
                            txt += "%-20s %-14s %-32s|" % (time, status, d)
                            txt += "\n=============================================================\n"
                            txt += message
                            txt += "\n=============================================================\n\n"
                        else:
                            txt += "%-20s %-14s %-32s| %s\n" % (
                                time,
                                status,
                                d,
                                message,
                            )
                        trace = ""
                        for entry in metadata.get("log", []) + metadata.get(
                            "child_log", []
                        ):
                            tb = entry.get("traceback")
                            if tb is not None:
                                if len(tb):
                                    if "timestamp" in entry:
                                        trace += f"Time:    {entry['timestamp']}"
                                    if "origin" in entry:
                                        trace += f"Origin:  {entry['origin']}"
                                    if "message" in entry:
                                        trace += f"Message: {entry['message']}"
                                    trace += "\n"
                                    trace += tb
                                    tb += "\n------------------------\n"
                        if len(trace):
                            txt += "\n### TRACEBACK ###############################################\n"
                            txt += trace
                            txt += "\n#############################################################\n\n"
        return txt

    def create_status(self, key):
        if self.key_name(key) != self.STATUS_FILE:
            if not self.is_dir(key):
                key = self.parent_key(key)
            status_key = f"{key}/{self.STATUS_FILE}" if len(key) else self.STATUS_FILE
            data = self.create_status_text(key).encode("utf-8")
            self.substore.store(
                status_key,
                data,
                dict(
                    type_identifier="text",
                    status=Status.SIDE_EFFECT.value,
                    title=f"Status of '{key}'",
                    description="This file is generated automatically by the recipe store",
                ),
            )

    def on_metadata_changed(self, key):
        super().on_metadata_changed(key)
        if self.STATUS_FILE is not None:
            if self.key_name(key) == self.RECIPES_FILE:
                self.update_all_status_files()
            elif self.key_name(key) != self.STATUS_FILE:
                self.create_status(key)

    def on_data_changed(self, key):
        super().on_data_changed(key)
        if self.key_name(key) == self.RECIPES_FILE:
            self.update_recipes()
            self.update_all_status_files()
        else:
            self.create_status(key)

    def on_removed(self, key):
        super().on_removed(key)
        if self.key_name(key) == self.RECIPES_FILE:
            self.update_recipes()
            self.update_all_status_files()
        else:
            self.create_status(key)

class RecipeSpecStore(NewRecipeSpecStore):
    pass