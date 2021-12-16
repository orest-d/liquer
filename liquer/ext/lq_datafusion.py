from io import StringIO, BytesIO
from liquer.state_types import StateType, register_state_type
from liquer.constants import mimetype_from_extension
from liquer.commands import command, first_command
from liquer.context import get_context
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
                b=path.read_bytes()
                return b, mimetype
        elif extension == "csv":
            with TemporaryDirectory() as tmpdir:
                path = Path(tmpdir) / f"data.{extension}"
                table = pyarrow.Table.from_batches(data.collect())
                pyarrow.csv.write_csv(table, str(path))
                b=path.read_bytes()
                return b, mimetype
        elif extension == "feather":
            with TemporaryDirectory() as tmpdir:
                path = Path(tmpdir) / f"data.{extension}"
                table = pyarrow.Table.from_batches(data.collect())
                pyarrow.feather.write_feather(table, str(path))
                b=path.read_bytes()
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
