from liquer import *
import json
from liquer.commands import command_registry
from liquer.state_types import encode_state_data, state_types_registry
import traceback
import requests
from liquer.query import evaluate
from liquer.state import get_vars
from liquer.cache import get_cache
from liquer.store import get_store, KeyNotFoundStoreException
import io
import traceback


def liquer_static_path():
    import liquer.server
    import os.path

    return os.path.join(os.path.dirname(liquer.server.__file__), "static")


class LiquerIndexHandler:
    def get(self):
        self.redirect("/static/index.html")


class LiquerJsHandler:
    def get(self):
        self.redirect("/static/liquer.js")


# /api/commands.json
class CommandsHandler:
    def get(self):
        """Returns a list of commands in json format"""
        self.write(json.dumps(command_registry().as_dict()))


def response(state):
    """Create flask response from a State"""
    filename = state.metadata.get("filename")
    b, mimetype, type_identifier = encode_state_data(state.get(), extension=state.extension)
    if filename is None:
        filename = state_types_registry().get(type_identifier).default_filename()
    return b, mimetype, filename


#'/submit/<query>
class SubmitHandler:
    """Submit query.
    Starts query in the background.
    """
    def prepare(self):
        header = "Content-Type"
        body = "application/json"
        self.set_header(header, body)

    def get(self, query):
        from liquer.pool import evaluate_in_background
        evaluate_in_background(query)
        self.write(
            json.dumps(
                dict(status="OK", message="Submitted", query=query)
            )
        )

    def post(self, param):
        self.write(
            json.dumps(command_registry().register_remote_serialized(self.request.body))
        )

# /q/<path:query>
class QueryHandler:
    def get(self, query):
        """Main service for evaluating queries"""        
        b, mimetype, filename = response(evaluate(query))

        header = "Content-Type"
        body = mimetype
        self.set_header(header, body)

        self.write(b)


#/api/cache/get/<path:query>
class CacheGetDataHandler:
    def get(self, query):
        """Main service for evaluating queries"""
        state = get_cache().get(query)
        if state is None:
            self.set_status(404)
            self.finish(f"404 - {query} not found in cache")

        b, mimetype, filename = response(state)
        header = "Content-Type"
        body = mimetype
        self.set_header(header, body)

        self.write(b)

#/api/cache/meta/<path:query>
class CacheMetadataHandler:
    def get(self, query):
        metadata = get_cache().get_metadata(query)
        if metadata == False:
            metadata = dict(query=query, status="not available", cached=False)
            self.write(metadata)
        mimetype = "application/json"
        header = "Content-Type"
        body = mimetype
        self.set_header(header, body)
        self.write(json.dumps(metadata))
    def post(self, param):
        try:
            metadata = json.loads(self.request.body)
            query = metadata.get('query')
            result_code = get_cache().store_metadata(metadata)
            result = dict(
                query=query, result=result_code, status="OK", message="OK", traceback=""
            )
        except Exception as e:
            result = dict(
                query=query,
                result=False,
                status="ERROR",
                message=str(e),
                traceback=traceback.format_exc(),
            )
        mimetype = "application/json"
        header = "Content-Type"
        body = mimetype
        self.set_header(header, body)
        self.write(json.dumps(result))


#/api/cache/remove/<path:query>
class CacheRemoveHandler:
    def get(self, query):
        r = get_cache().remove(query)
        mimetype = "application/json"
        header = "Content-Type"
        body = mimetype
        self.set_header(header, body)
        self.write(json.dumps(dict(query=query, removed=r)))


#/api/cache/contains/<path:query>
class CacheContainsHandler:
    def get(self, query):
        contains = get_cache().contains(query)
        mimetype = "application/json"
        header = "Content-Type"
        body = mimetype
        self.set_header(header, body)
        self.write(json.dumps(dict(query=query, cached=contains)))


#/api/cache/keys.json
class CacheKeysHandler:
    def get(self, query):
        keys = dict(keys=list(get_cache().keys()))
        mimetype = "application/json"
        header = "Content-Type"
        body = mimetype
        self.set_header(header, body)
        self.write(json.dumps(keys))


#/api/cache/clean
class CacheCleanHandler:
    def get(self):
        get_cache().clean()
        n = len(list(get_cache().keys()))
        keys = dict(status="OK", message=f"Cache cleaned, {n} keys left")
        mimetype = "application/json"
        header = "Content-Type"
        body = mimetype
        self.set_header(header, body)
        self.write(json.dumps(keys))


#/api/commands.json
class CommandsHandler:
    def get(self):
        mimetype = "application/json"
        header = "Content-Type"
        body = mimetype
        self.set_header(header, body)
        self.write(json.dumps(command_registry().as_dict()))


#/api/debug-json/<path:query>
class GetMetadataHandler:
    """Debug query - returns metadata from a state after a query is evaluated"""
    def prepare(self):
        header = "Content-Type"
        body = "application/json"
        self.set_header(header, body)
    def get(self, query):
        state = evaluate(query)
        state_json = state.as_dict()
        self.write(json.dumps(state_json))


#/api/stored_metadata/<path:query>
class GetStoredMetadataHandler:
    """Get metadata stored in a store or cache"""
    def prepare(self):
        header = "Content-Type"
        body = "application/json"
        self.set_header(header, body)
    def get(self, query):
        import liquer.tools
        metadata = liquer.tools.get_stored_metadata(query)
        self.write(json.dumps(metadata))


# /api/build
class BuildHandler:
    """Build a query from a posted decoded query (list of lists of strings).
    Result is a dictionary with encoded query and link.
    """

    def prepare(self):
        header = "Content-Type"
        body = "application/json"
        self.set_header(header, body)

    def post(self):
        from liquer.parser import encode

        query = encode(json.loads(self.request.body)["ql"])
        link = (
            get_vars().get("server", "http://localhost")
            + get_vars().get("api_path", "/q/")
            + query
        )
        self.write(json.dumps(dict(query=query, link=link, message="OK", status="OK")))


#'/api/register_command/
class RegisterCommandHandler:
    """Remote command registration service.
    This has to be enabled by liquer.commands.enable_remote_registration()

    WARNING: Remote command registration allows to deploy arbitrary python code on LiQuer server,
    therefore it is a HUGE SECURITY RISK and it only should be used if other security measures are taken
    (e.g. on localhost or intranet where only trusted users have access).
    This is on by default on Jupyter server extension.
    """

    def prepare(self):
        header = "Content-Type"
        body = "application/json"
        self.set_header(header, body)

    def get(self, param):
        self.write(
            json.dumps(
                command_registry().register_remote_serialized(param.encode("ascii"))
            )
        )

    def post(self, param):
        self.write(
            json.dumps(command_registry().register_remote_serialized(self.request.body))
        )

#/api/store/data/<path:query>
class StoreDataHandler:
    def get(self, query):
        """Get data from store. Equivalent to Store.get_bytes.
        Content type (MIME) is obtained from the metadata.
        """
        store = get_store()
        metadata = store.get_metadata(query)

        try:
            mimetype = metadata.get("mimetype", "application/octet-stream")
            b=store.get_bytes(query)
        except:
            mimetype = "application/json"
            b = json.dumps(
                dict(query=query, message=traceback.format_exc(), status="ERROR")
            )
 
        header = "Content-Type"
        body = mimetype
        self.set_header(header, body)
        self.write(b)

    def post(self, query):
        """Set data from store. Equivalent to Store.store.
        Unlike store method, which stores both data and metadata in one call,
        the api/store/data POST only stores the data. The metadata needs to be set in a separate POST of api/store/metadata
        either before or after the api/store/data POST.
        """
        store = get_store()
        try:
            metadata = store.get_metadata(query)
        except KeyNotFoundStoreException:
            metadata={}
        try:        
            data = self.request.body
            store.store(query, data, metadata)
            response = dict(query=query, message="Data stored", status="OK")
        except:
            response = dict(query=query, message=traceback.format_exc(), status="ERROR")

        mimetype = "application/json"
        header = "Content-Type"
        body = mimetype
        self.set_header(header, body)
        self.write(json.dumps(response))

#/api/store/metadata/<path:query>
class StoreMetadataHandler:
    def get(self, query):
        """Get data from store. Equivalent to Store.get_bytes.
        Content type (MIME) is obtained from the metadata.
        """
        store = get_store()
        metadata = store.get_metadata(query)
 
        mimetype = "application/json"
        header = "Content-Type"
        body = mimetype
        self.set_header(header, body)
        self.write(json.dumps(metadata))

    def post(self, param):
        """Set data from store. Equivalent to Store.store.
        Unlike store method, which stores both data and metadata in one call,
        the api/store/data POST only stores the data. The metadata needs to be set in a separate POST of api/store/metadata
        either before or after the api/store/data POST.
        """
        store = get_store()
        try:
            metadata = json.loads(self.request.body)
            query = metadata.get('query')
            store.store_metadata(query, metadata)
            response = dict(query=query, message="Metadata stored", status="OK")
        except:
            response = dict(query=query, message=traceback.format_exc(), status="ERROR")

        mimetype = "application/json"
        header = "Content-Type"
        body = mimetype
        self.set_header(header, body)
        self.write(json.dumps(response))

#/web/<path:query>
class WebStoreHandler:
    def get(self, query):
        """Shortcut to the 'web' directory in the store.
        Similar to /store/data/web, except the index.html is automatically added if query is a directory.
        The 'web' directory hosts web applications and visualization tools, e.g. liquer-pcv or liquer-gui. 
        """
        store = get_store()

        try:
            query="web/"+query
            if query.endswith("/"):
                query+="index.html"
            if store.is_dir(query):
                query+="/index.html"
            metadata = store.get_metadata(query)
            mimetype = metadata.get("mimetype", "application/octet-stream")
            b=store.get_bytes(query)
        except:
            mimetype = "application/json"
            b = json.dumps(
                dict(query=query, message=traceback.format_exc(), status="ERROR")
            )
 
        header = "Content-Type"
        body = mimetype
        self.set_header(header, body)
        self.write(b)


#/api/store/remove/<path:query>
class StoreRemoveHandler:
    """Handler to remove data from store"""
    def prepare(self):
        header = "Content-Type"
        body = "application/json"
        self.set_header(header, body)
    def get(self, query):
        store = get_store()
        try:
            store.remove(query)
            self.write(json.dumps(dict(query=query, message=f"Removed {query}", status="OK")))
        except:
            self.write(json.dumps(dict(query=query, message=traceback.format_exc(), status="ERROR")))


#/api/store/removedir/<path:query>
class StoreRemovedirHandler:
    def prepare(self):
        header = "Content-Type"
        body = "application/json"
        self.set_header(header, body)
    def get(self, query):
        store = get_store()
        try:
            store.removedir(query)
            self.write(json.dumps(dict(query=query, message=f"Removed directory {query}", status="OK")))
        except:
            self.write(json.dumps(dict(query=query, message=traceback.format_exc(), status="ERROR")))


#/api/store/contains/<path:query>
class StoreContainsHandler:
    def prepare(self):
        header = "Content-Type"
        body = "application/json"
        self.set_header(header, body)
    def get(self, query):
        store = get_store()
        try:
            contains = store.contains(query)
            self.write(json.dumps(
                dict(
                    query=query, message=f"Contains {query}", contains=contains, status="OK"
                )
            ))
        except:
            self.write(json.dumps(dict(query=query, message=traceback.format_exc(), status="ERROR")))


#/api/store/is_dir/<path:query>
class StoreIsDirHandler:
    def prepare(self):
        header = "Content-Type"
        body = "application/json"
        self.set_header(header, body)
    def get(self, query):
        store = get_store()
        try:
            is_dir = store.is_dir(query)
            self.write(json.dumps(
                dict(
                    query=query, message=f"Is directory {query}", is_dir=is_dir, status="OK"
                )
            ))
        except:
            self.write(json.dumps(dict(query=query, message=traceback.format_exc(), status="ERROR")))


#/api/store/keys")
class StoreKeysHandler:
    def prepare(self):
        header = "Content-Type"
        body = "application/json"
        self.set_header(header, body)
    def get(self, query):
        store = get_store()
        try:
            keys = store.keys()
            self.write(json.dumps(
                dict(query=None, message=f"Keys obtained", keys=keys, status="OK")
            ))
        except:
            self.write(json.dumps(dict(query=query, message=traceback.format_exc(), status="ERROR")))


#/api/store/listdir/<path:query>
class StoreListdirHandler:
    def prepare(self):
        header = "Content-Type"
        body = "application/json"
        self.set_header(header, body)
    def get(self, query):
        store = get_store()
        try:
            listdir = store.listdir(query)
            self.write(json.dumps(
                dict(query=query, message=f"Keys obtained", listdir=listdir, status="OK")
            ))
        except:
            self.write(json.dumps(dict(query=query, message=traceback.format_exc(), status="ERROR")))


#/api/store/makedir/<path:query>
class StoreMakedirHandler:
    def prepare(self):
        header = "Content-Type"
        body = "application/json"
        self.set_header(header, body)
    def get(self, query):
        store = get_store()
        try:
            store.makedir(query)
            self.write(json.dumps(
                dict(query=query, message=f"Makedir succeeded", status="OK")
            ))
        except:
            self.write(json.dumps(dict(query=query, message=traceback.format_exc(), status="ERROR")))

