from io import StringIO, BytesIO
from urllib.request import urlopen
import pandas as pd
import hxl
from liquer.state_types import StateType, register_state_type, mimetype_from_extension
from liquer.commands import command, first_command

class HxlStateType(StateType):
    def identifier(self):
        return "hxl_dataset"

    def default_extension(self):
        return "csv"

    def is_type_of(self, data):
        return isinstance(data, hxl.model.Dataset)

    def as_bytes(self, data, extension=None):
        if extension is None:
            extension = self.default_extension()
        assert self.is_type_of(data)
        mimetype = mimetype_from_extension(extension)
        if extension == "csv":
            output = "".join(data.gen_csv(show_headers=True, show_tags=True))
            return output.encode("utf-8"), mimetype
        elif extension == "json":
            output = "".join(data.gen_json(show_headers=True, show_tags=True))
            return output.encode("utf-8"), mimetype
        else:
            raise Exception(f"Serialization: file extension {extension} is not supported by HXL dataset type.")

    def from_bytes(self, b: bytes, extension=None):
        if extension is None:
            extension = self.default_extension()
        f = BytesIO()
        f.write(b)
        f.seek(0)

        if extension == "csv":
            return hxl.data(f)
        raise Exception(f"Deserialization: file extension {extension} is not supported by HXL dataset type.")

    def copy(self, data):
        return data

HXL_DATASET_STATE_TYPE = HxlStateType()
register_state_type("Dataset", HXL_DATASET_STATE_TYPE)
register_state_type("HXLReader", HXL_DATASET_STATE_TYPE)

@first_command
def hxl_from(url):
    """Load data from URL
    """
    return hxl.data(url)

@command
def hxl2df(data):
    """Convert hxl dataset to pandas dataframe
    """
    f = BytesIO()
    for line in data.gen_csv(show_headers=True, show_tags=True):
        f.write(line.encode("utf-8"))
    f.seek(0)
    return pd.read_csv(f)

@command
def df2hxl(df):
    """Convert pandas dataframe to hxl dataset
    """
    f = StringIO()
    df.to_csv(f, index=False)
    f = BytesIO(f.getvalue().encode("utf-8"))
    return hxl.data(f)
