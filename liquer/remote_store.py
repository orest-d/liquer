from liquer.store import Store, StoreException
import requests

class RemoteStore(Store):
    """RemoteStore is a store implementation that can connect to a remote liquer server
    via liquer server store API.
    """
    def __init__(self, url_api_prefix="/liquer/api/"):
        self.url_api_prefix = url_api_prefix

    @classmethod
    def concat_api(cls, api, key):
        assert not api.endswith("/")
        if not key.startswith("/"):
            key="/"+key
        return api+key

    def fetch(self, api):
        response = requests.get(self.url_api_prefix+api)
        response.raise_for_status()
        return response

    def fetch_json(self, api):
        return self.fetch(api).json()

    def fetch_bytes(self,api):
        return self.fetch(api).content

    def post_json(self, api, json):
        response = requests.post(self.url_api_prefix+api, json=json)
        response.raise_for_status()
        return response

    def post_bytes(self, api, data):
        response = requests.post(self.url_api_prefix+api, data=data, headers={'Content-Type': 'application/octet-stream'})
        response.raise_for_status()
        return response

    def get_bytes(self, key):
        return self.fetch_bytes(self.concat_api("store/data",key))

    def get_metadata(self, key):
        metadata = self.fetch_json(self.concat_api("store/metadata",key))
        return self.finalize_metadata(metadata, key=key, is_dir=self.is_dir(key))

    def store(self, key, data, metadata):
        metadata = self.finalize_metadata(
            metadata, key=key, is_dir=False, data=data
        )
        self.post_json(self.concat_api("store/metadata",key), metadata)
        self.post_bytes(self.concat_api("store/data",key), data)
        self.on_data_changed(key)
        self.on_metadata_changed(key)

    def store_metadata(self, key, metadata):
        metadata = self.finalize_metadata(
            metadata, key=key, is_dir=False, data=data
        )
        self.post_json(self.concat_api("store/metadata",key), metadata)
        self.on_metadata_changed(key)

    def remove(self, key):
        res = self.fetch_json(self.concat_api("store/remove",key))
        if res['status'] != "OK":
            raise StoreException(res["message"], key=key, store=self)
        self.on_removed(key)

    def removedir(self, key):
        res = self.fetch_json(self.concat_api("store/removedir",key))
        if res['status'] != "OK":
            raise StoreException(res["message"], key=key, store=self)
        self.on_removed(key)

    def contains(self, key):
        res = self.fetch_json(self.concat_api("store/remove",key))
        if res['status'] != "OK":
            raise StoreException(res["message"], key=key, store=self)
        return res["contains"]


    def is_dir(self, key):
        res = self.fetch_json(self.concat_api("store/is_dir",key))
        if res['status'] != "OK":
            raise StoreException(res["message"], key=key, store=self)
        return res["is_dir"]

    def keys(self):
        res = self.fetch_json("store/keys")
        if res['status'] != "OK":
            raise StoreException(res["message"], store=self)
        return sorted(res["keys"])

    def listdir(self, key):
        res = self.fetch_json(self.concat_api("store/listdir",key))
        if res['status'] != "OK":
            raise StoreException(res["message"], key=key, store=self)
        return res["listdir"]

    def makedir(self, key):
        while key not in (None, ""):
            self.directories.add(key)
            key = self.parent_key(key)
        self.on_data_changed(key)
        self.on_metadata_changed(key)


    def openbin(self, key, mode="r", buffering=-1):
        mode = dict(r="rb", w="wb").get(mode, mode)
        if mode == "rb":
            return BytesIO(self.get_bytes(key))
        raise Exception("openbin not supported for write yet")

    def is_supported(self, key):
        return True

    def __str__(self):
        return f"Remote store in {self.url_api_prefix}"

    def __repr__(self):
        return f"MemoryStore('{self.url_api_prefix}')"
