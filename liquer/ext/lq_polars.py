from io import StringIO, BytesIO
import pickle
from liquer.state_types import StateType, register_state_type
from liquer.constants import mimetype_from_extension

from liquer.commands import command, first_command
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
            data.write_csv(output)
            return output.getvalue(), mimetype
        elif extension == "parquet":
            output = BytesIO()
            data.write_parquet(output)
            return output.getvalue(), mimetype
        elif extension == "json":
            output = BytesIO()
            data.write_json(output)
            return output.getvalue(), mimetype
        elif extension == "ndjson":
            output = BytesIO()
            data.write_ndjson(output)
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
        elif extension == "json":
            return pl.read_json(f)
        elif extension == "ndjson":
            return pl.read_ndjson(f)
        raise Exception(
            f"Deserialization: file extension {extension} is not supported by polars data-frame type."
        )
    
    def copy(self, data):
        return pl.from_pandas(data.to_pandas().copy())

    def data_characteristics(self, data):
        return dict(
            description=f"Polars data-frame with {data.width} columns and {data.height} rows.",
            columns=list(data.columns),
            number_of_columns=data.width,
            number_of_rows=data.height,

        )

POLARS_DATAFRAME_STATE_TYPE = PolarsDataframeStateType()
register_state_type(pl.DataFrame, POLARS_DATAFRAME_STATE_TYPE)

class PolarsLazyframeStateType(StateType):
    def identifier(self):
        return "polars_lazyframe"

    def default_extension(self):
        return "parquet"

    def is_type_of(self, data):
        return isinstance(data, pl.LazyFrame)

    def as_bytes(self, data, extension=None):
        if extension is None:
            extension = self.default_extension()
        assert self.is_type_of(data)
        mimetype = mimetype_from_extension(extension)

        if extension == "csv":
            output = BytesIO()
            data.collect().write_csv(output)
            return output.getvalue(), mimetype
        elif extension == "parquet":
            output = BytesIO()
            data.collect().write_parquet(output)
            return output.getvalue(), mimetype
        elif extension == "json":
            output = BytesIO()
            data.collect().write_json(output)
            return output.getvalue(), mimetype
        elif extension == "ndjson":
            output = BytesIO()
            data.collect().write_ndjson(output)
            return output.getvalue(), mimetype
        else:
            raise Exception(
                f"Serialization: file extension {extension} is not supported by polars lazy-frame type."
            )

    def from_bytes(self, b: bytes, extension=None):
        if extension is None:
            extension = self.default_extension()
        f = BytesIO()
        f.write(b)
        f.seek(0)
        if extension == "csv":
            return pl.scan_csv(f)
        elif extension == "parquet":
            return pl.scan_parquet(f)
        elif extension == "json":
            return pl.read_json(f).lazy()
        elif extension == "ndjson":
            return pl.scan_ndjson(f)
        raise Exception(
            f"Deserialization: file extension {extension} is not supported by polars lazy-frame type."
        )
    
    def copy(self, data):
        return pl.from_pandas(data.collect().to_pandas().copy()).lazy()

    def data_characteristics(self, data):
        return dict(
            description=f"Polars lazy-frame with {data.width} columns.",
            columns=list(data.columns),
            number_of_columns=data.width,
            number_of_rows=None,
        )

POLARS_LAZYFRAME_STATE_TYPE = PolarsLazyframeStateType()
register_state_type(pl.LazyFrame, POLARS_LAZYFRAME_STATE_TYPE)

class PolarsSQLContextStateType(StateType):
    def identifier(self):
        return "polars_sqlcontext"

    def default_extension(self):
        return "parquet"

    def is_type_of(self, data):
        return isinstance(data, pl.SQLContext)

    def as_bytes(self, data, extension=None):
        if extension is None:
            extension = self.default_extension()
        assert self.is_type_of(data)

        mimetype = mimetype_from_extension(extension)
        if extension in ["pkl", "pickle"]:
            return pickle.dumps(data), mimetype
        tables = data.tables()
        if len(tables) == 0:
            raise Exception("SQLContext is empty")
        if len(tables) > 1:
            raise Exception(f"SQLContext contains more than one table ({len(tables)})")
        df = data.execute(f"select * from {tables[0]}")
        return POLARS_LAZYFRAME_STATE_TYPE.as_bytes(df, extension=extension)
 
    def from_bytes(self, b: bytes, extension=None):
        if extension is None:
            extension = self.default_extension()

        if extension in ["pkl", "pickle"]:
            return pickle.loads(b)

        f = BytesIO()
        f.write(b)
        f.seek(0)
        if extension == "csv":
            df = pl.read_csv(f)
        elif extension == "parquet":
            df = pl.read_parquet(f)
        elif extension == "json":
            df = pl.read_json(f)
        elif extension == "ndjson":
            df = pl.read_ndjson(f)
        else:
            raise Exception(f"Unsupported file extension: {extension}")
        
        return pl.SQLContext(df=df)
    
    
    def copy(self, data):
        raise Exception(f"Copy is not supported by Polars SQLContext type.")

    def data_characteristics(self, data):
        tables = data.tables()
        if len(tables) == 0:
            return dict(
                description=f"Empty Polars SQL context.",
                tables=tables
            )
        elif len(tables) == 1:
            return dict(
                description=f"Polars SQL context with one table: {tables[0]}.",
                tables=tables
            )
        else:
            return dict(
                description=f"Polars SQL context with {len(tables)} tables: {', '.join(tables)}.",
                tables=tables
            )

POLARS_SQLCONTEXT_STATE_TYPE = PolarsSQLContextStateType()
register_state_type(pl.SQLContext, POLARS_SQLCONTEXT_STATE_TYPE)


@command
def polars_df(data, extension=None, context=None):
    """Convert bytes or a pandas data-frame to a Polars data-frame"""
    context = get_context(context)
    if type(data) == bytes:
        context.info(f"Polars data-frame from bytes. Extension:'{extension}'")
        return POLARS_DATAFRAME_STATE_TYPE.from_bytes(data, extension=extension)
    elif isinstance(data, pd.DataFrame):
        context.info("Polars data-frame from Pandas data-frame")
        return pl.DataFrame(data)
    elif isinstance(data, pl.DataFrame):
        context.info("Polars data-frame kept as it is")
        return data
    raise Exception(f"Unsupported polars dataframe type: {type(data)}")

@command
def polars2pandas(df, context=None):
    """Convert Polars data-frame to a Pandas data-frame"""
    return df.to_pandas()
