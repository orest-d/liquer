"""Defines S3Store class with the Liquer store interface.
S3Store is a store using Amazon S3 buckets."""
from liquer.store import Store, parent_key
from liquer.metadata import Metadata
import json
import boto3


class S3Store(Store):
    """S3Store class with the Liquer store interface.
    S3Store is a store using Amazon S3 buckets."""
    DELIMITER = "/"

    def __init__(self, bucket_name, prefix="", s3_resource=None):
        if s3_resource is None:
            s3_resource = boto3.resource("s3")
        self.bucket_name = bucket_name
        self.prefix = prefix
        self.s3_resource = s3_resource
        if len(self.prefix) and self.prefix[-1] != self.DELIMITER:
            self.prefix += self.DELIMITER
        self.data_prefix = self.prefix + "data" + self.DELIMITER
        self.metadata_prefix = self.prefix + "metadata" + self.DELIMITER

    def finalize_metadata(self, metadata, key, is_dir=False, data=None, update=False):
        metadata = super().finalize_metadata(
            metadata, key=key, is_dir=is_dir, data=data, update=update
        )
        return Metadata(metadata).as_dict()

    def object_for_key(self, key):
        return self.s3_resource.Object(
            bucket_name=self.bucket_name, key=self.data_prefix + key
        )

    def metadata_object_for_key(self, key):
        return self.s3_resource.Object(
            bucket_name=self.bucket_name, key=self.metadata_prefix + key + ".json"
        )

    def get_bytes(self, key):
        return self.object_for_key(key).get()["Body"].read()

    def get_metadata(self, key):
        is_dir = self.is_dir(key)
        metadata = self.default_metadata(key, is_dir)

        if is_dir:
            return self.finalize_metadata(metadata, key=key, is_dir=True)
        else:
            try:
                metadata_bin = self.metadata_object_for_key(key).get()["Body"].read()
            except:
                raise KeyNotFoundStoreException(key=key, store=self)

            try:
                metadata.update(json.loads(metadata_bin))
            except:
                traceback.print_exc()
                print(f"Removing {key} due to corrupted metadata (a)")
                self.remove(key)
                raise KeyNotFoundStoreException(key=key, store=self)

        return self.finalize_metadata(metadata, key=key, is_dir=False)

    def store(self, key, data, metadata):
        self.object_for_key(key).put(Body=data)
        self.store_metadata(
            key, self.finalize_metadata(metadata, key=key, is_dir=False, data=data)
        )
        self.on_data_changed(key)
        self.on_metadata_changed(key)

    def store_metadata(self, key, metadata):
        metadata = self.finalize_metadata(
            metadata, key=key, is_dir=self.is_dir(key), update=True
        )
        metadata_bin = json.dumps(metadata).encode("utf-8")
        self.metadata_object_for_key(key).put(Body=metadata_bin)
        self.on_metadata_changed(key)

    def remove(self, key):
        try:
            self.object_for_key(key).delete()
        except:
            pass
        try:
            self.metadata_object_for_key(key).delete()
        except:
            pass

        self.on_removed(key)

    def removedir(self, key):
        self.on_removed(key)

    def object_keys(self, keyprefix=""):
        response = self.s3_resource.meta.client.list_objects(
            Bucket=self.bucket_name, Prefix=self.data_prefix + keyprefix
        )
        if "Contents" in response:
            return [x["Key"] for x in response["Contents"]]
        else:
            return []

    def metadata_object_keys(self, keyprefix=""):
        response = self.s3_resource.meta.client.list_objects(
            Bucket=self.bucket_name, Prefix=self.metadata_prefix + keyprefix
        )
        if "Contents" in response:
            return [x["Key"] for x in response["Contents"]]
        else:
            return []

    def contains(self, key):
        if key in ("", None):
            return True
        keys = self.object_keys(key)
        ekey = self.data_prefix + key
        if ekey in keys:
            return True
        ekey = ekey + "/"
        return any(x.startswith(ekey) for x in keys)

    def is_dir(self, key):
        if key in ("", None):
            return True
        keys = self.object_keys(key)
        ekey = self.data_prefix + key + "/"
        return any(x.startswith(ekey) for x in keys)

    def keys(self, keyprefix=""):
        directories = set()
        for x in self.object_keys(keyprefix):
            if x.startswith(self.data_prefix):
                key = x[len(self.data_prefix) :]
                yield key
                pkey = key
                while True:
                    pkey = parent_key(pkey)
                    if pkey in ("", None):
                        break
                    if pkey not in directories:
                        yield pkey
                        directories.add(pkey)

    def listdir(self, key):
        if key in ("", None):
            return [k for k in self.keys() if parent_key(k) in ("", None)]
        else:
            return [
                k[len(key) + 1 :] for k in self.keys(key + "/") if parent_key(k) == key
            ]

    def makedir(self, key):
        self.on_data_changed(key)
        self.on_metadata_changed(key)

    def openbin(self, key, mode="rb", buffering=-1):
        import io

        if not self.contains(key) and not self.is_dir(key) and mode in ("r", "rb"):
            return io.BytesIO(self.get_bytes(key))
        else:
            raise Exception(
                "S3Store only supports openbin for reading of existing objects"
            )

    def is_supported(self, key):
        return True

    def __str__(self):
        return f"S3 bucket {self.bucket_name} with prefix {repr(self.prefix)}"

    def __repr__(self):
        return f"S3Store('{self.bucket_name}', {repr(self.prefix)})"
