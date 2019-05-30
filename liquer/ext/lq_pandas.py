from io import StringIO, BytesIO
from urllib.request import urlopen
import pandas as pd
from liquer.state_types import StateType, register_state_type, mimetype_from_extension
from liquer.commands import command, first_command

print ("LiQuer Pandas module")
class DataframeStateType(StateType):
    def identifier(self):
        return "dataframe"

    def default_extension(self):
        return "csv"

    def is_type_of(self, data):
        return isinstance(data, pd.DataFrame)

    def as_bytes(self, data, extension=None):
        if extension is None:
            extension = self.default_extension()
        assert self.is_type_of(data)
        mimetype = mimetype_from_extension(extension)
        if extension == "csv":
            output = StringIO()
            data.to_csv(output, index=False)
            return output.getvalue().encode("utf-8"), mimetype 
        elif extension == "tsv":
            output = StringIO()
            data.to_csv(output, index=False, sep="\t")
            return output.getvalue().encode("utf-8"), mimetype
        elif extension == "json":
            output = StringIO()
            data.to_json(output, index=False, orient="table")
            return output.getvalue().encode("utf-8"), mimetype
        elif extension in ("html", "htm"):
            output = StringIO()
            data.to_html(output, index=False)
            return output.getvalue().encode("utf-8"), mimetype
        elif extension == "xlsx":
            output = BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            data.to_excel(writer)
            writer.close()
            return output.getvalue()
        elif extension == "msgpack":
            output = BytesIO()
            data.to_msgpack(output)
            return output.getvalue()
        else:
            raise Exception(f"Serialization: file extension {extension} is not supported by dataframe type.")

    def from_bytes(self, b: bytes, extension=None):
        if extension is None:
            extension = self.default_extension()
        f = BytesIO()
        f.write(b)
        f.seek(0)

        if extension == "csv":
            return pd.read_csv(f)
        elif extension == "tsv":
            return pd.read_csv(f, sep="\t")
        elif extension == "json":
            return pd.read_json(f)
        elif extension == "xlsx":
            return pd.read_excel(f)
        elif extension == "msgpack":
            return pd.read_msgpack(f)
        raise Exception(f"Deserialization: file extension {extension} is not supported by dataframe type.")

    def copy(self, data):
        return data.copy()

DATAFRAME_STATE_TYPE = DataframeStateType()
register_state_type("DataFrame", DATAFRAME_STATE_TYPE)

@first_command
def df_from(url, extension=None):
    """Load data from URL
    """
    if extension is None:
        extension = url.split(".")[-1]
        if extension not in "csv tsv xls xlsx msgpack".split():
            extension = "csv"
    if url.startswith("http:") or url.startswith("https:") or url.startswith("ftp:"):
        f = BytesIO(urlopen(url).read())
    else:
        f = open(url)
    if extension == "csv":
        return pd.read_csv(f)
    elif extension == "tsv":
        return pd.read_csv(f, sep="\t")
    elif extension in ("xls", "xlsx"):
        return pd.read_excel(f)
    elif extension == "msgpack":
        return pd.read_msgpack(f)
    else:
        raise Exception(f"Unsupported file extension: {extension}")

@command
def append_df(df, url, extension=None):
    """Append dataframe from URL
    """
    df1 = df_from(url, extension=extension)
    return df.append(df1, ignore_index=True)
