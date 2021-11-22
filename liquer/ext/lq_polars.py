from io import StringIO, BytesIO
from liquer.state_types import StateType, register_state_type
from liquer.constants import mimetype_from_extension

from liquer.commands import command, first_command
from tempfile import NamedTemporaryFile
from liquer.context import get_context
import pandas as pd
import polars as pl

class PolarsDataframeStateType(StateType):
    def identifier(self):
        return "polars_dataframe"

    def default_extension(self):
        return "parquet"

    def is_type_of(self, data):
        return isinstance(data, pl.DataFrame)

    def as_bytes(self, data, extension=None):
        if extension is None:
            extension = self.default_extension()
        assert self.is_type_of(data)
        mimetype = mimetype_from_extension(extension)

        if extension == "csv":
            output = BytesIO()
            data.to_csv(output)
            return output.getvalue(), mimetype
        elif extension == "parquet":
            output = BytesIO()
            data.to_parquet(output)
            return output.getvalue(), mimetype
        else:
            raise Exception(
                f"Serialization: file extension {extension} is not supported by polars data-frame type."
            )

    def from_bytes(self, b: bytes, extension=None):
        if extension is None:
            extension = self.default_extension()
        f = BytesIO()
        f.write(b)
        f.seek(0)
        if extension == "csv":
            return pl.read_csv(f)
        elif extension == "parquet":
            return pl.read_parquet(f)
        raise Exception(
            f"Deserialization: file extension {extension} is not supported by polars data-frame type."
        )

    def copy(self, data):
        return self.from_bytes(self.as_bytes(data)[0])

    def data_characteristics(self, data):
        return dict(description=f"Polars data-frame with {len(data.columns)} and {len(data)} rows.")
        

POLARS_DATAFRAME_STATE_TYPE = PolarsDataframeStateType()
register_state_type(pl.DataFrame, POLARS_DATAFRAME_STATE_TYPE)

@command
def polars_df(data, extension=None, context=None):
    """Convert bytes or a dataframe to a workbook"""
    context=get_context(context)
    if type(data)==bytes:
        context.info(f"Polars data-frame from bytes. Extension:'{extension}'")
        return POLARS_DATAFRAME_STATE_TYPE.from_bytes(data, extension=extension)
    elif isinstance(data,pd.DataFrame):
        context.info("Polars data-frame from Pandas data-frame")
        return pl.DataFrame(data)
    elif isinstance(data,pl.DataFrame):
        context.info("Polars data-frame kept as it is")
        return data
    raise Exception(f"Unsupported polars dataframe type: {type(data)}")
