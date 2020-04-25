from notebook.utils import url_path_join
from notebook.base.handlers import IPythonHandler
import liquer.server.handlers as h

class LiquerIndexHandler(h.LiquerIndexHandler, IPythonHandler):
    pass

class LiquerIndexJsHandler(h.LiquerIndexJsHandler, IPythonHandler):
    pass
#/api/commands.json
class CommandsHandler(h.CommandsHandler, IPythonHandler):
    pass

#/api/debug-json/<path:query>
class DebugQueryHandler(h.DebugQueryHandler, IPythonHandler):
    pass

#/q/<path:query>
class QueryHandler(h.QueryHandler, IPythonHandler):
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
    import liquer.ext.lq_hxl
    import liquer.ext.lq_python
    import liquer.ext.lq_pygments
    from liquer.state import set_var, get_vars
    import tornado.web

    web_app = nb_server_app.web_app
    host_pattern = '.*$'
    url_prefix='/liquer'
    route_pattern = url_path_join(web_app.settings['base_url'], url_prefix)

    set_var("api_path","/q/")
    set_var("server",route_pattern)

    web_app.add_handlers(host_pattern, [
        (route_pattern, LiquerIndexHandler),
        (url_path_join(route_pattern,'/index.html'), LiquerIndexHandler),
        (url_path_join(route_pattern,'/index.js'), LiquerIndexJsHandler),
        (url_path_join(route_pattern,'/api/commands.json'), CommandsHandler),
        (url_path_join(route_pattern,'/api/debug-json/(.*)'), DebugQueryHandler),
        (url_path_join(route_pattern,'/q/(.*)'), QueryHandler),
        (url_path_join(route_pattern,'/static/(.*)'), tornado.web.StaticFileHandler, {'path': h.liquer_static_path()}),
    ])
