from liquer import *
import pandas as pd
from liquer.store import get_store
from liquer.state_types import (
    data_characteristics,
    state_types_registry,
    StateType,
    register_state_type,
)
from liquer.constants import mimetype_from_extension
import json


@command
def concat_batches(idf, max_batches=None, context=None):
    """Concatenates an iterator of dataframes (batches) into a single dataframe
    A maximum limit of batches to be processed can be specified with max_batches.
    By default all the batches will be concatenated.
    """
    context = get_context(context)
    context.info(f"Concatenate batches")
    if isinstance(idf, pd.DataFrame):
        context.info(f"Single dataframe received")
        idf = [idf]
    batch_number = 0
    if max_batches in ("0", "", None):
        max_batches = 0
    else:
        max_batches = int(max_batches)
    buffer = pd.DataFrame()
    for df in context.progress_iter(idf):
        if not len(df):
            continue
        context.info(
            f"Receiving dataframe with {len(df)} rows and {len(df.columns)} columns"
        )
        if len(buffer) > 0:
            if len(df.columns) != len(buffer.columns):
                context.warning(
                    f"Number of columns in the batches differs - before:{len(buffer.columns)}, now:{len(df.columns)}"
                )
        batch_number += 1
        if max_batches:
            context.info(f"Concatenate batch {batch_number}/{max_batches}")
        else:
            context.info(f"Concatenate batch {batch_number}")
        buffer = buffer.append(df, ignore_index=True)
        if max_batches and batch_number >= max_batches:
            context.info(f"Maximum number of batches reached")
            break
    return buffer


@command(volatile=True, cache=False)
def repackage_batches(idf, batch_size=1024, max_batches=0, context=None):
    """Repackages an iterator of dataframes (batches) into fixed-length batches.
    Results in an iterator of dataframes where each dataframe (with the exception of the last one)
    has a the batch_size number of rows.
    Note: Since the result is an iterator, it is volatile and can't be cached.
    A maximum limit of batches to be processed can be specified with max_batches.
    By default all the batches will be repackaged.
    """
    context = get_context(context)
    context.info(f"Repackage batches")
    if isinstance(idf, pd.DataFrame):
        context.info(f"Single dataframe received")
        idf = [idf]
    buffer = pd.DataFrame()
    if max_batches in ("0", "", None):
        max_batches = 0
    else:
        max_batches = int(max_batches)
    batch_number = 0
    for df in context.progress_iter(idf):
        if not len(df):
            continue
        context.info(
            f"Receiving dataframe with {len(df)} rows and {len(df.columns)} columns"
        )
        if len(buffer) > 0:
            if len(df.columns) != len(buffer.columns):
                context.warning(
                    f"Number of columns in the batches differs - before:{len(buffer.columns)}, now:{len(df.columns)}"
                )
        buffer = buffer.append(df, ignore_index=True)
        while len(buffer) >= batch_size:
            batch_number += 1
            if max_batches:
                context.info(f"Yield batch {batch_number}/{max_batches}")
            else:
                context.info(f"Yield batch {batch_number}")
            result = buffer.iloc[:batch_size, :]
            buffer = buffer.iloc[batch_size:, :]
            yield result
            if max_batches and batch_number >= max_batches:
                context.info(f"Maximum number of batches reached")
                return
    while len(buffer) >= batch_size:
        batch_number += 1
        if max_batches:
            context.info(f"Yield batch {batch_number}/{max_batches} (finishing)")
        else:
            context.info(f"Yield batch {batch_number} (finishing)")
        result = buffer.iloc[:batch_size, :]
        buffer = buffer.iloc[batch_size:, :]
        yield result
        if max_batches and batch_number >= max_batches:
            context.info(f"Maximum number of batches reached")
            return
    if len(buffer):
        batch_number += 1
        if max_batches:
            context.info(f"Yield batch {batch_number}/{max_batches} (last)")
        else:
            context.info(f"Yield batch {batch_number} (last)")
        yield buffer


class StoredDataframeIterator(object):
    def __init__(
        self,
        key,
        item_keys=None,
        extension="parquet",
        number_format="%04d",
        batch_number=0,
        store=None,
    ):
        self.key = key
        self.item_keys = item_keys or []
        self.extension = extension
        self.number_format = number_format
        self.batch_number = batch_number
        self.state_type = state_types_registry().get("dataframe")

        if store is None:
            store = get_store()
        self.store= store

    def to_dict(self, with_batch_number=False):
        d = dict(
            key=self.key,
            item_keys=self.item_keys[:],
            extension=self.extension,
            number_format=self.number_format,
        )
        if with_batch_number:
            d["batch_number"] = self.batch_number
        return d

    @classmethod
    def from_dict(cls, d):
        return cls(
            d["key"],
            item_keys=d.get("item_keys", []),
            extension=d.get("extension"),
            number_format=d.get("number_format"),
            batch_number=d.get("batch_number", 0),
        )

    def copy(self):
        return StoredDataframeIterator(
            self.key,
            item_keys=self.item_keys,
            extension=self.extension,
            number_format=self.number_format,
            batch_number=self.batch_number,
            store=self.store,
        )

    def _key_to_value(self, key):
        if not self.store.contains(key):
            raise Exception(f"Batch {self.batch_number} failure: '{key}' not in store")
        if self.store.is_dir(key):
            raise Exception(
                f"Batch {self.batch_number} failure: '{key}' is a directory"
            )
        metadata = self.store.get_metadata(key)
        if metadata is None:
            print(f"WARNING: Batch {self.batch_number}, key '{key}' missing metadata")
        b = self.store.get_bytes(key)
        if b is None:
            raise Exception(f"Batch {self.batch_number} failure: '{key}' has no data")
        assert type(b) == bytes

        v = key.split(".")
        extension = self.extension if len(v) <= 1 else v[-1]

        df = self.state_type.from_bytes(b, extension=extension)

        return df

    def new_key(self):
        batch_number = len(self.item_keys) + 1
        if self.number_format is None:
            name = str(batch_number)
        else:
            name = self.number_format % batch_number
        if self.extension in (None, ""):
            key = f"{self.key}/{name}"
        else:
            key = f"{self.key}/{name}.{self.extension}"
        if key in self.item_keys:
            raise Exception(f"New key '{key}' already exists")
        return key

    def append(self, df):
        key = self.new_key()
        store = self.store
        b, mimetype = self.state_type.as_bytes(df, self.extension)
        dc = data_characteristics(df)
        assert dc["type_identifier"] == "dataframe"
        metadata = dict(
            type_identifier=dc.get("type_identifier"),
            data_characteristics=data_characteristics(df),
        )
        store.store(key, b, metadata)
        self.item_keys.append(key)

    def rewind(self):
        self.batch_number = 0
        return self

    def __len__(self):
        return len(self.item_keys)

    def __iter__(self):
        return self.copy().rewind()

    def __next__(self):
        if len(self.item_keys) > self.batch_number:
            key = self.item_keys[self.batch_number]
            self.batch_number += 1
            return self._key_to_value(key)
        raise StopIteration

    def __str__(self):
        return f"Dataframe iterator stored in {self.key}"

    def __repr__(self):
        return f"StoredDataframeIterator('{self.key}')"

class StoredDataframeIteratorStateType(StateType):
    def identifier(self):
        return "dataframe_iterator"

    def default_extension(self):
        return "idf"

    def is_type_of(self, data):
        return isinstance(data, StoredDataframeIterator)

    def as_bytes(self, data, extension=None):
        if extension is None:
            extension = self.default_extension()
        assert self.is_type_of(data)
        if extension in ["idf", "json"]:
            mimetype = mimetype_from_extension("json")
            d = data.to_dict()
            return json.dumps(d).encode("utf-8"), mimetype
        else:
            raise Exception(
                f"Serialization: file extension {extension} is not supported by stored dataframe iterator type."
            )

    def from_bytes(self, b: bytes, extension=None):
        if extension is None:
            extension = self.default_extension()

        if extension in ["idf", "json"]:
            return StoredDataframeIterator.from_dict(json.loads(b.decode("utf-8")))
        raise Exception(
            f"Deserialization: file extension {extension} is not supported by dataframe type."
        )

    def copy(self, data):
        return data.copy()

    def data_characteristics(self, data):
        return dict(
            description=f"Dataframe iterator with {len(data.item_keys)} batches."
        )


STORED_DATAFRAME_ITERATOR_STATE_TYPE = StoredDataframeIteratorStateType()
register_state_type(StoredDataframeIterator, STORED_DATAFRAME_ITERATOR_STATE_TYPE)


def _store_batches(idf, key, max_batches=None, context=None):
    """Store iterator of dataframes (batches) in a store.
    The key specifies a directory in the store where the items will be stored.
    Helper function yielding StoredDataframeIterator object and dataframes.
    """
    context = get_context(context)
    context.info(f"Store iterator")
    batch_number = 0
    if max_batches in ("0", "", None):
        max_batches = 0
    else:
        max_batches = int(max_batches)
    store = context.store()
    if store.contains(key):
        if store.is_dir(key):
            context.info(f"Cleaning {key}")
            for x in store.listdir_keys(key):
                context.info(f"Remove {x}")
                store.remove(x)
        else:
            raise Exception(
                f"Can't store the iterator in '{key}'. The key exists and it is not a directory."
            )
    sdfi_key = store.join_key(key, "dataframe_iterator.json")

    sdfi = StoredDataframeIterator(key)
    for df in context.progress_iter(idf):
        if not len(df):
            continue
        batch_number += 1
        if max_batches:
            context.info(f"Storing batch {batch_number}/{max_batches}")
        else:
            context.info(f"Storing batch {batch_number}")
        sdfi.append(df)
        context.store_data(sdfi_key, sdfi)
        yield sdfi, df
#        sdfi_bytes, mimetype = STORED_DATAFRAME_ITERATOR_STATE_TYPE.as_bytes(sdfi)
#        dc = data_characteristics(sdfi)
#        sdfi_metadata = context.metadata()
#        sdfi_metadata.update(
#            dict(type_identifier=dc["type_identifier"], data_characteristics=dc)
#        )
#        store.store(sdfi_key, sdfi_bytes, sdfi_metadata)
        if max_batches and batch_number > max_batches:
            context.info(f"Maximum number of batches reached")
            break
@command
def store_batches(idf, key, max_batches=None, context=None):
    """Store iterator of dataframes (batches) in a store.
    The key specifies a directory in the store where the items will be stored.
    Results in a StoredDataframeIterator object after all batches have been processed.
    This object can be serialized or stored in the object.
    After each iteration step, the StoredDataframeIterator is stored as well in key/dataframe_iterator.json as a side-effect.
    Thus for long-running iterations, the partial data is stored even if the evaluation does not finish.
    """
    context = get_context(context)
    sdfi = StoredDataframeIterator(key)
    for sdfi, df in _store_batches(idf, key, max_batches=max_batches, context=context):
        pass
    return sdfi

@command(cache=False, volatile=True)
def store_batches_pass_through(idf, key, max_batches=None, context=None):
    """Store iterator of dataframes (batches) in a store.
    The key specifies a directory in the store where the items will be stored.
    Unlike store_batches, this immediately yields the dataframes,
    thus the result is a volatile iterator which can not be stored in cache.
    The StoredDataframeIterator is, however, stored in key/dataframe_iterator.json as a side-effect after each iteration step.
    """
    context = get_context(context)
    for sdfi, df in _store_batches(idf, key, max_batches=max_batches, context=context):
        yield df
