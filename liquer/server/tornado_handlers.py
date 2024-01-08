"""[Tornado](https://www.tornadoweb.org/en/stable/) handlers and Tornado backend for Liquer server"""
import tornado.ioloop
import tornado.web
import liquer.server.handlers as h


def liquer_static_path():
    import liquer.server
    import os.path

    return os.path.join(os.path.dirname(liquer.server.__file__), "static")

class BaseHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        # CORS headers - e.g. to support Godot apps
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header('Cross-Origin-Embedder-Policy', 'require-corp')
        self.set_header('Cross-Origin-Opener-Policy', 'same-origin')

class LiquerIndexHandler(h.LiquerIndexHandler, BaseHandler):
    pass


class LiquerJsHandler(h.LiquerJsHandler, BaseHandler):
    pass


# /api/commands.json
class CommandsHandler(h.CommandsHandler, BaseHandler):
    pass


#'/submit/<query>
class SubmitHandler(h.SubmitHandler, BaseHandler):
    pass


# /q/<path:query>
class QueryHandler(h.QueryHandler, BaseHandler):
    pass


# /api/cache/get/<path:query>
class CacheGetDataHandler(h.CacheGetDataHandler, BaseHandler):
    pass


# /api/cache/meta/<path:query>
class CacheMetadataHandler(h.CacheMetadataHandler, BaseHandler):
    pass


# /api/cache/remove/<path:query>
class CacheRemoveHandler(h.CacheRemoveHandler, BaseHandler):
    pass


# /api/cache/contains/<path:query>
class CacheContainsHandler(h.CacheContainsHandler, BaseHandler):
    pass


# /api/cache/keys.json
class CacheKeysHandler(h.CacheKeysHandler, BaseHandler):
    pass


# /api/cache/clean
class CacheCleanHandler(h.CacheCleanHandler, BaseHandler):
    pass


# /api/commands.json
class CommandsHandler(h.CommandsHandler, BaseHandler):
    pass


# /api/debug-json/<path:query>
class GetMetadataHandler(h.GetMetadataHandler, BaseHandler):
    pass


# /api/stored_metadata/<path:query>
class GetStoredMetadataHandler(h.GetStoredMetadataHandler, BaseHandler):
    pass


# /api/build
class BuildHandler(h.BuildHandler, BaseHandler):
    pass


#'/api/register_command/
class RegisterCommandHandler(h.RegisterCommandHandler, BaseHandler):
    pass


# /api/store/data/<path:query>
class GetStoreDataHandler(h.GetStoreDataHandler, BaseHandler):
    pass

# /api/store/data/<path:query>
class StoreDataHandler(h.StoreDataHandler, BaseHandler):
    pass

# /api/store/upload/<path:query>
class StoreUploadHandler(h.StoreUploadHandler, BaseHandler):
    pass


# /api/store/metadata/<path:query>
class GetStoreMetadataHandler(h.GetStoreMetadataHandler, BaseHandler):
    pass

# /api/store/metadata/<path:query>
class StoreMetadataHandler(h.StoreMetadataHandler, BaseHandler):
    pass

# /web/<path:query>
class WebStoreHandler(h.WebStoreHandler, BaseHandler):
    pass


# /api/store/remove/<path:query>
class StoreRemoveHandler(h.StoreRemoveHandler, BaseHandler):
    pass


# /api/store/removedir/<path:query>
class StoreRemovedirHandler(h.StoreRemovedirHandler, BaseHandler):
    pass


# /api/store/contains/<path:query>
class StoreContainsHandler(h.StoreContainsHandler, BaseHandler):
    pass


# /api/store/is_dir/<path:query>
class StoreIsDirHandler(h.StoreIsDirHandler, BaseHandler):
    pass


# /api/store/keys")
class StoreKeysHandler(h.StoreKeysHandler, BaseHandler):
    pass


# /api/store/listdir/<path:query>
class StoreListdirHandler(h.StoreListdirHandler, BaseHandler):
    pass


# /api/store/makedir/<path:query>
class StoreMakedirHandler(h.StoreMakedirHandler, BaseHandler):
    pass


# class DebugQueryHandler(h.DebugQueryHandler, BaseHandler):
#    pass


def url_mapping():
    return [
        (r"/liquer/api/commands.json", CommandsHandler),
        (r"/liquer/submit/(.*)", SubmitHandler),
        (r"/liquer/q/(.*)", QueryHandler),
        (r"/liquer/api/cache/get/(.*)", CacheGetDataHandler),
        (r"/liquer/api/cache/meta/(.*)", CacheMetadataHandler),
        (r"/liquer/api/cache/remove/(.*)", CacheRemoveHandler),
        (r"/liquer/api/cache/contains/(.*)", CacheContainsHandler),
        (r"/liquer/api/cache/keys.json", CacheKeysHandler),
        (r"/liquer/api/cache/clean", CacheCleanHandler),
        (r"/liquer/api/debug-json/(.*)", GetMetadataHandler),
        (r"/liquer/api/metadata/(.*)", GetMetadataHandler),
        (r"/liquer/api/stored_metadata/(.*)", GetStoredMetadataHandler),
        (r"/liquer/api/build", BuildHandler),
        (r"/liquer/api/register_command", RegisterCommandHandler),
        (r"/liquer/api/store/data/(.*)", StoreDataHandler),
        (r"/liquer/api/store/upload/(.*)", StoreUploadHandler),
        (r"/liquer/api/store/metadata/(.*)", StoreMetadataHandler),
        (r"/liquer/web/(.*)", WebStoreHandler),
        (r"/liquer/api/store/remove/(.*)", StoreRemoveHandler),
        (r"/liquer/api/store/removedir/(.*)", StoreRemovedirHandler),
        (r"/liquer/api/store/contains/(.*)", StoreContainsHandler),
        (r"/liquer/api/store/is_dir/(.*)", StoreIsDirHandler),
        (r"/liquer/api/store/keys", StoreKeysHandler),
        (r"/liquer/api/store/listdir/(.*)", StoreListdirHandler),
        (r"/liquer/api/store/makedir/(.*)", StoreMakedirHandler),
    ]

def url_mapping_ro():
    return [
        (r"/liquer/api/commands.json", CommandsHandler),
        (r"/liquer/api/cache/get/(.*)", CacheGetDataHandler),
        (r"/liquer/api/cache/meta/(.*)", CacheMetadataHandler),
        #(r"/liquer/api/cache/remove/(.*)", CacheRemoveHandler),
        (r"/liquer/api/cache/contains/(.*)", CacheContainsHandler),
        (r"/liquer/api/cache/keys.json", CacheKeysHandler),
        (r"/liquer/q/(.*)", CacheGetDataHandler),
        (r"/liquer/api/debug-json/(.*)", GetStoredMetadataHandler),
        (r"/liquer/api/metadata/(.*)", GetStoredMetadataHandler),
        (r"/liquer/api/stored_metadata/(.*)", GetStoredMetadataHandler),
        (r"/liquer/api/store/data/(.*)", GetStoreDataHandler),
        (r"/liquer/api/store/metadata/(.*)", GetStoreMetadataHandler),
        (r"/liquer/web/(.*)", WebStoreHandler),
        (r"/liquer/api/store/contains/(.*)", StoreContainsHandler),
        (r"/liquer/api/store/is_dir/(.*)", StoreIsDirHandler),
        (r"/liquer/api/store/keys", StoreKeysHandler),
        (r"/liquer/api/store/listdir/(.*)", StoreListdirHandler),
    ]


if __name__ == "__main__":
    import liquer.ext.basic
    import liquer.ext.meta
    import liquer.ext.lq_pandas

    #    import liquer.ext.lq_hxl
    import liquer.ext.lq_python
    import liquer.ext.lq_pygments
    from liquer.state import set_var, get_vars

    #    import liquer.commands
    #    liquer.commands.enable_remote_registration()

    url_prefix = "/liquer"
    port = 8080
    set_var("api_path", url_prefix + "/q/")
    set_var("server", f"http://localhost:{port}")

    application = tornado.web.Application(
        url_mapping()
        + [
            (
                r"/static/(.*)",
                tornado.web.StaticFileHandler,
                {"path": h.liquer_static_path()},
            ),
            (
                r"/liquer/static/(.*)",
                tornado.web.StaticFileHandler,
                {"path": h.liquer_static_path()},
            ),
            (r"/", LiquerIndexHandler),
            (r"/index.html", LiquerIndexHandler),
            (r"/liquer.js", LiquerJsHandler),
        ]
    )
    application.listen(port)
    tornado.ioloop.IOLoop.current().start()
