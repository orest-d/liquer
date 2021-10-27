import tornado.ioloop
import tornado.web
import liquer.server.handlers as h


class LiquerIndexHandler(h.LiquerIndexHandler, tornado.web.RequestHandler):
    pass


class LiquerJsHandler(h.LiquerIndexJsHandler, tornado.web.RequestHandler):
    pass


# /api/commands.json
class CommandsHandler(h.CommandsHandler, tornado.web.RequestHandler):
    pass


# /api/debug-json/<path:query>
class DebugQueryHandler(h.DebugQueryHandler, tornado.web.RequestHandler):
    pass


# /q/<path:query>
class QueryHandler(h.QueryHandler, tornado.web.RequestHandler):
    pass


class BuildHandler(h.BuildHandler, tornado.web.RequestHandler):
    pass


class RegisterCommandHandler(h.RegisterCommandHandler, tornado.web.RequestHandler):
    pass


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
        [
            (r"/liquer/api/commands.json", CommandsHandler),
            (r"/liquer/api/debug-json/(.*)", DebugQueryHandler),
            (r"/liquer/api/build", BuildHandler),
            (r"/liquer/api/register_command/(.*)", RegisterCommandHandler),
            (r"/liquer/q/(.*)", QueryHandler),
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
