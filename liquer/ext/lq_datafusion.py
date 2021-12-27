from io import StringIO, BytesIO
from liquer.state_types import StateType, register_state_type
from liquer.constants import mimetype_from_extension
from liquer.commands import command, first_command
from liquer.context import get_context
from liquer.recipes import Recipe, register_recipe
from liquer.parser import parse
from liquer.store import key_extension, key_name, key_name_without_extension
from tempfile import TemporaryDirectory
from pathlib import Path

import pandas as pd
import datafusion as daf
import pyarrow
import pyarrow.parquet
import pyarrow.csv
import pyarrow.feather


class DatafusionDataframeStateType(StateType):
    def identifier(self):
        return "datafusion_dataframe"

    def default_extension(self):
        return "parquet"

    def is_type_of(self, data):
        return isinstance(data, daf.DataFrame)

    def as_bytes(self, data, extension=None):
        if extension is None:
            extension = self.default_extension()
        assert self.is_type_of(data)
        mimetype = mimetype_from_extension(extension)

        if extension == "parquet":
            with TemporaryDirectory() as tmpdir:
                path = Path(tmpdir) / f"data.{extension}"
                table = pyarrow.Table.from_batches(data.collect())
                pyarrow.parquet.write_table(table, str(path))
                b = path.read_bytes()
                return b, mimetype
        elif extension == "csv":
            with TemporaryDirectory() as tmpdir:
                path = Path(tmpdir) / f"data.{extension}"
                table = pyarrow.Table.from_batches(data.collect())
                pyarrow.csv.write_csv(table, str(path))
                b = path.read_bytes()
                return b, mimetype
        elif extension == "feather":
            with TemporaryDirectory() as tmpdir:
                path = Path(tmpdir) / f"data.{extension}"
                table = pyarrow.Table.from_batches(data.collect())
                pyarrow.feather.write_feather(table, str(path))
                b = path.read_bytes()
                return b, mimetype
        else:
            raise Exception(
                f"Serialization: file extension {extension} is not supported by DataFusion data-frame type."
            )

    def from_bytes(self, b: bytes, extension=None):
        raise Exception(
            f"Deserialization is not supported by DataFusion data-frame type."
        )

    def copy(self, data):
        return self.from_bytes(self.as_bytes(data)[0])

    def data_characteristics(self, data):
        return dict(description=f"DataFusion data-frame")


DATAFUSION_DATAFRAME_STATE_TYPE = DatafusionDataframeStateType()
register_state_type(daf.DataFrame, DATAFUSION_DATAFRAME_STATE_TYPE)


class DatafusionContextStateType(StateType):
    def identifier(self):
        return "datafusion_context"

    def default_extension(self):
        return "pickle"

    def is_type_of(self, data):
        return isinstance(data, daf.ExecutionContext)

    def as_bytes(self, data, extension=None):
        raise Exception(
            f"Serialization is not supported by DataFusion ExecutionContext type."
        )

    def from_bytes(self, b: bytes, extension=None):
        raise Exception(
            f"Deserialization is not supported by DataFusion ExecutionContext type."
        )

    def copy(self, data):
        raise Exception(
            f"Copy is not supported by DataFusion ExecutionContext type."
        )

    def data_characteristics(self, data):
        return dict(description=f"DataFusion execution context")


DATAFUSION_CONTEXT_STATE_TYPE = DatafusionContextStateType()
register_state_type(daf.ExecutionContext, DATAFUSION_CONTEXT_STATE_TYPE)


@command
def datafusion_to_pandas(df):
    """Convert DataFusion data-frame to pandas data-frame"""
    table = pyarrow.Table.from_batches(df.collect())
    return table.to_pandas()


class ParquetSQLRecipe(Recipe):
    @classmethod
    def recipe_type(self):
        return "parquet_sql"

    @classmethod
    def from_dict(cls, d):
        return cls(d)

    def metadata(self, key):
        metadata = {}
        if "title" in self.data:
            metadata["title"] = self.data["title"]
        if "description" in self.data:
            metadata["description"] = self.data["description"]
        return metadata

    def provides(self):
        if "filename" not in self.data:
            raise Exception(
                f"Recipe {self.recipe_name()} of type {self.recipe_type()} does not have a filename.")
        return self.data.get("provides", [self.data["filename"]])

    def make_execution_context(self, tmpdir, store, context):
        import datafusion as daf
        ctx = daf.ExecutionContext()
        register = self.data.get("register", [])
        store = store.root_store()

        path = Path(tmpdir)
        for query in register:
            try:
                q = parse(query)
            except:
                context.warning(
                    f"Could not parse query '{query}' in parquet_sql recipe {self.recipe_name()}", traceback=traceback.format_exc())
            if q.is_resource_query():
                key = q.resource_query().path()
                if store.is_dir(key):
                    for k in store.listdir_keys(key):
                        if not store.is_dir(k) and key_extension(k) == "parquet":
                            (path / key_name(k)).write_bytes(store.get_bytes(k))
                            context.info(
                                f"Registering {key_name_without_extension(k)} from {key}")
                            ctx.register_parquet(key_name_without_extension(
                                k), str(path / key_name(k)))
                else:
                    (path / key_name(key)).write_bytes(store.get_bytes(key))
                    context.info(f"Registering {key}")
                    ctx.register_parquet(key_name_without_extension(
                        key), str(path / key_name(key)))
            else:
                filename = q.filename()
                if filename is None:
                    context.warning(
                        f"Skipping '{query}' registering because it is lacking a filename")
                    continue
                v = filename.split(".")
                context.info(f"Evaluating query {query}")
                context.evaluate_and_save(
                    query, target_directory=str(tmpdir), target_file=filename)
                context.info(f"Registering {v[0]} from query {query}")
                ctx.register_parquet(v[0], str(path / filename))
        return ctx

    def make(self, key, store=None, context=None):
        context = get_context(context)
        if "sql" not in self.data:
            raise Exception(
                f"Recipe {self.recipe_name()} of type {self.recipe_type()} does not have sql.")
        if "filename" not in self.data:
            raise Exception(
                f"Recipe {self.recipe_name()} of type {self.recipe_type()} does not have a filename.")
        if store is None:
            store = context.store()
        with TemporaryDirectory() as tmpdir:
            ctx = self.make_execution_context(tmpdir, store, context)
            df = ctx.sql(self.data["sql"])
            table = pyarrow.Table.from_batches(df.collect())
            path = Path(tmpdir) / self.data["filename"]
            pyarrow.parquet.write_table(table, str(path))
            b = path.read_bytes()
            metadata = self.metadata(key)
            store.store(key, b, metadata)

register_recipe(ParquetSQLRecipe)