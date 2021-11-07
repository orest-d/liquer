from io import StringIO, BytesIO
from urllib.request import urlopen
import pandas as pd
import hxl
from liquer.state_types import StateType, register_state_type
from liquer.commands import command, first_command
from liquer.constants import mimetype_from_extension


class HxlStateType(StateType):
    def identifier(self):
        "Define an unique string identifier for the state type"
        return "hxl_dataset"

    def default_extension(self):
        "Default file extension for the state type"
        return "csv"

    def is_type_of(self, data):
        "Check if data is of this state type"
        return isinstance(data, hxl.model.Dataset)

    def as_bytes(self, data, extension=None):
        """Serialize data as bytes
        File extension may be provided and influence the serialization format.
        """
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
            raise Exception(
                f"Serialization: file extension {extension} is not supported by HXL dataset type."
            )

    def from_bytes(self, b: bytes, extension=None):
        """De-serialize data from bytes
        File extension may be provided and influence the serialization format.
        """
        if extension is None:
            extension = self.default_extension()
        f = BytesIO()
        f.write(b)
        f.seek(0)

        if extension == "csv":
            return hxl.data(f)
        raise Exception(
            f"Deserialization: file extension {extension} is not supported by HXL dataset type."
        )

    def copy(self, data):
        """Make a deep copy of the data"""
        return data

    def data_characteristics(self, data):
        return dict(description=f"HXL dataset")

HXL_DATASET_STATE_TYPE = HxlStateType()
register_state_type(hxl.Dataset, HXL_DATASET_STATE_TYPE)
register_state_type(hxl.io.HXLReader, HXL_DATASET_STATE_TYPE)


@first_command
def hxl_from(url):
    """Load data from URL"""
    return hxl.data(url)


@command
def hxl2df(data):
    """Convert hxl dataset to pandas dataframe"""
    f = BytesIO()
    for line in data.gen_csv(show_headers=True, show_tags=True):
        f.write(line.encode("utf-8"))
    f.seek(0)
    return pd.read_csv(f)


@command
def df2hxl(df):
    """Convert pandas dataframe to hxl dataset"""
    f = StringIO()
    df.to_csv(f, index=False)
    f = BytesIO(f.getvalue().encode("utf-8"))
    return hxl.data(f)


@command
def set_all_tags(df, *tags):
    """Set all tags in pandas dataframe. All tags should be specified in the same order as columns.
    If not all tags are specified, empty strings are appended.
    Creates a first row with tags in a dataframe.
    Hash characters are automatically prepended if not present.
    """

    tags = pd.DataFrame(
        [
            {
                c: tag.strip() if tag.strip().startswith("#") else "#" + tag.strip()
                for c, tag in zip(df.columns, tags)
            }
        ],
        columns=df.columns,
    )
    tags.fillna(value="", inplace=True)
    return tags.append(df, ignore_index=True)


@command
def set_tags(df, *column_tag):
    """Set tags in pandas dataframe, tags are specified as a list with alternating column, tag.
    Creates a first row with tags in a dataframe.
    Hash characters are automatically prepended if not present.
    """
    if len(column_tag) % 2 != 0:
        raise Exception(
            f"Columns-tags (len:{len(column_tag)})argument od set_tags do not form pairs {column_tag}"
        )
    tags = pd.DataFrame(
        [
            {
                column_tag[i]: column_tag[i + 1].strip()
                if column_tag[i + 1].strip().startswith("#")
                else "#" + column_tag[i + 1].strip()
                for i in range(0, len(column_tag), 2)
            }
        ],
        columns=df.columns,
    )
    tags.fillna(value="", inplace=True)
    return tags.append(df, ignore_index=True)
