from liquer.store import Store
from liquer.metadata import Metadata
import json
import boto3

class S3Store(Store):
    DELIMITER="/"

    def __init__(self, bucket_name, prefix="", s3_resource=None):
        if s3_resource is None:
            s3_resource = boto3.resource('s3') 
        self.prefix=prefix
        self.s3_resource=s3_resource
        if len(self.prefix) and self.prefix[-1]!=self.DELIMITER:
            self.prefix += self.DELIMITER
        self.data_prefix = self.prefix + "data" + self.DELIMITER
        self.metadata_prefix = self.prefix + "metadata" + self.DELIMITER


    def finalize_metadata(self, metadata, key, is_dir=False, data=None, update=False):
        metadata = super().finalize_metadata(
            metadata, key=key, is_dir=is_dir, data=data, update=update
        )
        return Metadata(metadata).as_dict()

    def object_for_key(self, key):
        return self.s3_resource.Object(bucket_name=self.bucket_name, key=self.data_prefix+key)

    def metadata_object_for_key(self, key):
        return self.s3_resource.Object(bucket_name=self.bucket_name, key=self.metadata_prefix+key+".json")

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
                metadata.update(
                    json.loads(metadata_bin)
                )
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
        metadata = self.finalize_metadata(metadata, key=key, is_dir=self.is_dir(key), update=True)
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
        (self.path_for_key(key) / self.METADATA).rmdir()
        self.path_for_key(key).rmdir()
        self.on_removed(key)

    def contains(self, key):
        if key in ("",None):
            return True
        return self.path_for_key(key).exists()

    def is_dir(self, key):
        if key in ("",None):
            return True
        return self.path_for_key(key).is_dir()

    def keys(self, parent=None):
        d = self.listdir(parent)
        if d is None:
            return []
        else:
            for k in d:
                key = k if parent is None else parent + "/" + k
                yield key
                for kk in self.keys(key):
                    yield kk

    def listdir(self, key):
        if self.is_dir(key):
            return [
                d.name
                for d in self.path_for_key(key).iterdir()
                if d.name != self.METADATA
            ]

    def makedir(self, key):
        self.on_data_changed(key)
        self.on_metadata_changed(key)

    def openbin(self, key, mode="rb", buffering=-1):
        import io
        if not self.contains(key) and not self.is_dir(key) and mode in ("r", "rb"):
            return io.BytesIO(self.get_bytes(key))
        else:
            raise Exception("S3Store only supports openbin for reading of existing objects")

    def is_supported(self, key):
        return True

    def __str__(self):
        return f"S3 bucket {self.bucket_name} with prefix {repr(self.prefix)}"

    def __repr__(self):
        return f"S3Store('{self.bucket_name}', {repr(self.prefix)})"
