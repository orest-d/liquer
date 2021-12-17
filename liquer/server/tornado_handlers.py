import tornado.ioloop
import tornado.web
import liquer.server.handlers as h


def liquer_static_path():
    import liquer.server
    import os.path

    return os.path.join(os.path.dirname(liquer.server.__file__), "static")


class LiquerIndexHandler(h.LiquerIndexHandler, tornado.web.RequestHandler):
    pass

class LiquerJsHandler(h.LiquerJsHandler, tornado.web.RequestHandler):
    pass

# /api/commands.json
class CommandsHandler(h.CommandsHandler, tornado.web.RequestHandler):
    pass

#'/submit/<query>
class SubmitHandler(h.SubmitHandler, tornado.web.RequestHandler):
    pass

# /q/<path:query>
class QueryHandler(h.QueryHandler, tornado.web.RequestHandler):
    pass

#/api/cache/get/<path:query>
class CacheGetDataHandler(h.CacheGetDataHandler, tornado.web.RequestHandler):
    pass

#/api/cache/meta/<path:query>
class CacheMetadataHandler(h.CacheMetadataHandler, tornado.web.RequestHandler):
    pass

#/api/cache/remove/<path:query>
class CacheRemoveHandler(h.CacheRemoveHandler, tornado.web.RequestHandler):
    pass

#/api/cache/contains/<path:query>
class CacheContainsHandler(h.CacheContainsHandler, tornado.web.RequestHandler):
    pass

#/api/cache/keys.json
class CacheKeysHandler(h.CacheKeysHandler, tornado.web.RequestHandler):
    pass

#/api/cache/clean
class CacheCleanHandler(h.CacheCleanHandler, tornado.web.RequestHandler):
    pass

#/api/commands.json
class CommandsHandler(h.CommandsHandler, tornado.web.RequestHandler):
    pass

#/api/debug-json/<path:query>
class GetMetadataHandler(h.GetMetadataHandler, tornado.web.RequestHandler):
    pass

#/api/stored_metadata/<path:query>
class GetStoredMetadataHandler(h.GetStoredMetadataHandler, tornado.web.RequestHandler):
    pass

# /api/build
class BuildHandler(h.BuildHandler, tornado.web.RequestHandler):
    pass

#'/api/register_command/
class RegisterCommandHandler(h.RegisterCommandHandler, tornado.web.RequestHandler):
    pass

#/api/store/data/<path:query>
class StoreDataHandler(h.StoreDataHandler, tornado.web.RequestHandler):
    pass

#/api/store/metadata/<path:query>
class StoreMetadataHandler(h.StoreMetadataHandler, tornado.web.RequestHandler):
    pass

#/web/<path:query>
class WebStoreHandler(h.WebStoreHandler, tornado.web.RequestHandler):
    pass

#/api/store/remove/<path:query>
class StoreRemoveHandler(h.StoreRemoveHandler, tornado.web.RequestHandler):
    pass

#/api/store/removedir/<path:query>
class StoreRemovedirHandler(h.StoreRemovedirHandler, tornado.web.RequestHandler):
    pass

#/api/store/contains/<path:query>
class StoreContainsHandler(h.StoreContainsHandler, tornado.web.RequestHandler):
    pass

#/api/store/is_dir/<path:query>
class StoreIsDirHandler(h.StoreIsDirHandler, tornado.web.RequestHandler):
    pass

#/api/store/keys")
class StoreKeysHandler(h.StoreKeysHandler, tornado.web.RequestHandler):
    pass

#/api/store/listdir/<path:query>
class StoreListdirHandler(h.StoreListdirHandler, tornado.web.RequestHandler):
    pass

#/api/store/makedir/<path:query>
class StoreMakedirHandler(h.StoreMakedirHandler, tornado.web.RequestHandler):
    pass


#class DebugQueryHandler(h.DebugQueryHandler, tornado.web.RequestHandler):
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
        (r"/liquer/api/commands.json", CommandsHandler),
        (r"/liquer/api/debug-json/(.*)", GetMetadataHandler),
        (r"/liquer/api/metadata/(.*)", GetMetadataHandler),
        (r"/liquer/api/stored_metadata/(.*)", GetStoredMetadataHandler),
        (r"/liquer/api/build", BuildHandler),
        (r"/liquer/api/register_command", RegisterCommandHandler),
        (r"/liquer/api/store/data/(.*)", StoreDataHandler),
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
        url_mapping() + [
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
