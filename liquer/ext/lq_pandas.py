from io import StringIO, BytesIO
from urllib.request import urlopen
import pandas as pd
import numpy as np
from liquer.state_types import StateType, register_state_type
from liquer.constants import mimetype_from_extension

from liquer.commands import command, first_command
from liquer.parser import encode, decode
from liquer.query import evaluate
from liquer.state import State


class ResilientBytesIO(BytesIO):
    "Workaround to prevent closing the stream"

    def close(self):
        pass  # Refuse to close to avoid pandas bug

    def really_close(self):
        super().close()


class DataframeStateType(StateType):
    def identifier(self):
        return "dataframe"

    def default_extension(self):
        return "pickle"

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
        elif extension in ("pkl", "pickle"):
            output = ResilientBytesIO()
            data.to_pickle(output, compression=None)
            b = output.getvalue()
            output.really_close()
            return b, mimetype
        elif extension == "parquet":
            output = ResilientBytesIO()
            data.to_parquet(output, engine="pyarrow")
            b = output.getvalue()
            output.really_close()
            return b, mimetype
        elif extension == "feather":
            output = ResilientBytesIO()
            data.to_feather(output)
            b = output.getvalue()
            output.really_close()
            return b, mimetype
        elif extension == "xlsx":
            output = BytesIO()
            writer = pd.ExcelWriter(output, engine="xlsxwriter")
            data.to_excel(writer)
            writer.close()
            return output.getvalue(), mimetype
        elif extension == "msgpack":
            output = BytesIO()
            data.to_msgpack(output)
            return output.getvalue(), mimetype
        else:
            raise Exception(
                f"Serialization: file extension {extension} is not supported by dataframe type."
            )

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
        elif extension == "parquet":
            return pd.read_parquet(f)
        elif extension == "feather":
            return pd.read_feather(f)
        elif extension in ("pickle", "pkl"):
            return pd.read_pickle(f, compression=None)
        elif extension == "xlsx":
            return pd.read_excel(f, engine="openpyxl")
        elif extension == "msgpack":
            return pd.read_msgpack(f)
        raise Exception(
            f"Deserialization: file extension {extension} is not supported by dataframe type."
        )

    def copy(self, data):
        return data.copy()

    def data_characteristics(self, data):
        return dict(description=f"Dataframe with {len(data.columns)} columns and {len(data)} rows.",
        columns=[str(c) for c in data.columns],
        number_of_columns = len(data.columns),
        number_of_rows = len(data),
        )
        

DATAFRAME_STATE_TYPE = DataframeStateType()
register_state_type(pd.DataFrame, DATAFRAME_STATE_TYPE)


@command
def to_df(data):
    "Convert data to DataFrame; data should be list of dicts or dict of lists."
    return pd.DataFrame(data)


@first_command
def df_from(url, extension=None):
    """Load data from URL"""
    if extension is None:
        extension = url.split(".")[-1]
        if extension not in "csv tsv xls xlsx msgpack".split():
            extension = "csv"
    if url.startswith("http:") or url.startswith("https:") or url.startswith("ftp:"):
        f = BytesIO(urlopen(url).read())
    else:
        f = open(url)
    state = State().with_source(url)
    if extension == "csv":
        return state.with_data(pd.read_csv(f))
    elif extension == "tsv":
        return state.with_data(pd.read_csv(f, sep="\t"))
    elif extension in ("xls", "xlsx"):
        return state.with_data(pd.read_excel(f))
    elif extension == "msgpack":
        return state.with_data(pd.read_msgpack(f))
    else:
        raise Exception(f"Unsupported file extension: {extension}")


@command
def append_df(df, url, extension=None):
    """Append dataframe from URL"""
    df1 = df_from(url, extension=extension).get()
    return df.append(df1, ignore_index=True)


@command
def eq(state, *column_values):
    """Equals filter
    Accepts one or more column-value pairs. Keep only rows where value in the column equals specified value.
    Example: eq-column1-1
    """
    df = state.get()
    assert state.type_identifier == "dataframe"
    for i in range(0, len(column_values), 2):
        c = column_values[i]
        v = column_values[i + 1]
        state.log_info(f"Equals: {c} == {v}")
        index = np.array([x == v for x in df[c]], np.bool)
        try:
            if int(v) == float(v):
                index = index | (df[c] == int(v))
            else:
                index = index | (df[c] == float(v))
        except:
            pass
        df = df.loc[index, :]
    return state.with_data(df)


@command
def teq(state, *column_values):
    """Tag-Equals filter. Expects, that a first row contains tags and/or metadata
    Tag row is ignored in comparison, but prepended to the result (in order to maintain the first row in the results).
    Accepts one or more column-value pairs. Keep only rows where value in the column equals specified value.
    Example: teq-column1-1
    """
    df = state.get()
    tags = df.iloc[:1, :]
    df = df.iloc[1:, :]
    assert state.type_identifier == "dataframe"
    for i in range(0, len(column_values), 2):
        c = column_values[i]
        v = column_values[i + 1]
        state.log_info(f"Equals: {c} == {v}")
        index = np.array([x == v for x in df[c]], np.bool)
        try:
            if int(v) == float(v):
                index = index | (df[c] == int(v))
            else:
                index = index | (df[c] == float(v))
        except:
            pass
        df = df.loc[index, :]
    df = tags.append(df, ignore_index=True)
    return state.with_data(df)


@command
def qsplit_df(state, *columns):
    """Quick/query split of dataframe by columns
    Creates a dataframe with unique (combinations of) value from supplied columns and queries
    to obtain the corresponding filtered dataframes from the original dataframe.
    Resulting queries are put in query column. Name of the query column
    can be overriden by query_column state variable.
    """
    df = state.get()
    if len(columns) == 1:
        keys = [(x,) for x in sorted(df.groupby(by=list(columns)).groups.keys())]
    else:
        keys = sorted(df.groupby(by=list(columns)).groups.keys())

    query_column = state.vars.get("query_column")
    if query_column is None:
        query_column = "query"

    sdf = pd.DataFrame(columns=list(columns) + [query_column])
    data = []
    ql = decode(state.query)
    for row in keys:
        pairs = list(zip(columns, row))
        d = dict(pairs)
        query = encode(ql + [["eq"] + [str(x) for p in pairs for x in p]])
        d[query_column] = query
        sdf = sdf.append(d, ignore_index=True)

    return state.with_data(sdf)


@command
def qtsplit_df(state, *columns):
    """Quick/query split of dataframe by columns (version expecting a first row with tags)
    Creates a dataframe with unique (combinations of) value from supplied columns and queries
    to obtain the corresponding filtered dataframes from the original dataframe.
    Resulting queries are put in query column. Name of the query column
    can be overriden by query_column state variable.
    """
    df = state.get()
    tags = df.iloc[0]
    df = df.iloc[1:]

    if len(columns) == 1:
        keys = [(x,) for x in sorted(df.groupby(by=list(columns)).groups.keys())]
    else:
        keys = sorted(df.groupby(by=list(columns)).groups.keys())

    query_column = state.vars.get("query_column")
    if query_column is None:
        query_column = "query"

    sdf = pd.DataFrame(columns=list(columns) + [query_column])
    sdf = sdf.append({c: tags[c] for c in columns}, ignore_index=True)
    data = []
    ql = decode(state.query)
    for row in keys:
        pairs = list(zip(columns, row))
        d = dict(pairs)
        query = encode(ql + [["teq"] + [str(x) for p in pairs for x in p]])
        d[query_column] = query
        sdf = sdf.append(d, ignore_index=True)

    return state.with_data(sdf)


@command
def split_df(state, *columns):
    """Split of dataframe by columns
    Creates a dataframe with unique (combinations of) value from supplied columns and queries
    to obtain the corresponding filtered dataframes from the original dataframe.

    This behaves like qsplit_df, with two important differenced:
    - each generated query is evaluated (and thus eventually cached)
    - link is generated and put into link column (state variable link_column)
    The split_link_type state variable is used to determine the link type; url by default.
    """
    from liquer.parser import parse

    state = qsplit_df(state, *columns)
    df = state.get().copy()

    query_column = state.vars.get("query_column")
    if query_column is None:
        query_column = "query"

    link_column = state.vars.get("link_column")
    if link_column is None:
        link_column = "link"

    split_link_type = state.vars.get("split_link_type")
    if split_link_type is None:
        split_link_type = "url"

    #    df.loc[:,link_column] = [evaluate(encode(decode(q)+[["link",split_link_type]])).get() for q in df[query_column]]
    df.loc[:, link_column] = [
        evaluate(parse(q).with_action("link", split_link_type).encode()).get()
        for q in df[query_column]
    ]
    return state.with_data(df)


@command
def tsplit_df(state, *columns):
    """Split of dataframe by columns (version of split_df expecting a first row with tags)"""
    from liquer.parser import parse

    state = qtsplit_df(state, *columns)
    df = state.get().copy()

    query_column = state.vars.get("query_column")
    if query_column is None:
        query_column = "query"

    link_column = state.vars.get("link_column")
    if link_column is None:
        link_column = "link"

    split_link_type = state.vars.get("split_link_type")
    if split_link_type is None:
        split_link_type = "url"

    #    df.loc[:,link_column] = [""]+[evaluate(encode(decode(q)+[["link",split_link_type]])).get() for q in list(df[query_column])[1:]]
    df.loc[:, link_column] = [""] + [
        evaluate(parse(q).with_action("link", split_link_type).encode()).get()
        for q in list(df[query_column])[1:]
    ]
    return state.with_data(df)


@command
def df_columns(df):
    return list(df.columns)


@command
def columns_info(df):
    if len(df):
        tags = {str(key): str(value) for key, value in dict(df.iloc[0, :]).items()}
        has_tags = any(str(tag).strip().startswith("#") for tag in tags.values())
    else:
        tags = None
        has_tags = False

    return dict(
        columns=list(map(str, df.columns)),
        tags=tags,
        has_tags=has_tags,
        types={str(key): str(value) for key, value in df.dtypes.items()},
    )


@command
def head_df(df, count=50):
    if count < len(df):
        return df.iloc[:count, :]
    else:
        return df


@command
def groupby_mean(df, mean_column, *groupby_columns):
    return (
        df.groupby(groupby_columns)
        .mean()
        .reset_index()
        .loc[:, list(groupby_columns) + [mean_column]]
    )
