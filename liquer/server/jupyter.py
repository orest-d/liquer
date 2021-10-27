from notebook.utils import url_path_join
from notebook.base.handlers import IPythonHandler
import liquer.server.handlers as h
import os.path


class LiquerIndexHandler(IPythonHandler):
    def prepare(self):
        header = "Content-Type"
        body = "text/html"
        self.set_header(header, body)

    def get(self):
        self.write(open(os.path.join(h.liquer_static_path(), "index.html")).read())


class LiquerJsHandler(IPythonHandler):
    def prepare(self):
        header = "Content-Type"
        body = "text/javascript"
        self.set_header(header, body)

    def get(self):
        self.write(open(os.path.join(h.liquer_static_path(), "liquer.js")).read())


# /api/commands.json
class CommandsHandler(h.CommandsHandler, IPythonHandler):
    pass


# /api/debug-json/<path:query>
class DebugQueryHandler(h.DebugQueryHandler, IPythonHandler):
    pass


# /q/<path:query>
class QueryHandler(h.QueryHandler, IPythonHandler):
    pass


class BuildHandler(h.BuildHandler, IPythonHandler):
    pass


class RegisterCommandHandler(h.RegisterCommandHandler, IPythonHandler):
    pass


def load_jupyter_server_extension(nb_server_app):
    """
    Called when the extension is loaded.

    Args:
        nb_server_app (NotebookWebApplication): handle to the Notebook webserver instance.
    """

    import liquer.ext.basic
    import liquer.ext.meta
    import liquer.ext.lq_pandas

    # import liquer.ext.lq_hxl
    import liquer.ext.lq_python
    import liquer.ext.lq_pygments
    from liquer.state import set_var, get_vars
    import liquer.commands

    liquer.commands.enable_remote_registration()

    web_app = nb_server_app.web_app
    host_pattern = ".*$"
    url_prefix = "/liquer"
    route_pattern = url_path_join(web_app.settings["base_url"], url_prefix)

    set_var("api_path", "/q/")
    set_var("server", route_pattern)

    web_app.add_handlers(
        host_pattern,
        [
            (route_pattern, LiquerIndexHandler),
            (url_path_join(route_pattern, "/index.html"), LiquerIndexHandler),
            (url_path_join(route_pattern, "/liquer.js"), LiquerJsHandler),
            (url_path_join(route_pattern, "/static/index.html"), LiquerIndexHandler),
            (url_path_join(route_pattern, "/static/liquer.js"), LiquerJsHandler),
            (url_path_join(route_pattern, "/api/commands.json"), CommandsHandler),
            (url_path_join(route_pattern, "/api/debug-json/(.*)"), DebugQueryHandler),
            (url_path_join(route_pattern, "/api/build"), BuildHandler),
            (
                url_path_join(route_pattern, "/api/register_command/(.*)"),
                RegisterCommandHandler,
            ),
            (url_path_join(route_pattern, "/q/(.*)"), QueryHandler),
        ],
    )
