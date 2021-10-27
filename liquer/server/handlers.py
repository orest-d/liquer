from liquer import *
import json
from liquer.commands import command_registry
from liquer.state_types import encode_state_data, state_types_registry
import traceback
import requests


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


# /api/debug-json/<path:query>
class DebugQueryHandler:
    def prepare(self):
        header = "Content-Type"
        body = "application/json"
        self.set_header(header, body)

    def get(self, query):
        """Debug query - returns metadata from a state after a query is evaluated"""
        state = evaluate(query)
        state_json = state.as_dict()
        self.write(json.dumps(state_json))


# /q/<path:query>
class QueryHandler:
    def get(self, query):
        """Main service for evaluating queries"""
        state = evaluate(query)
        filename = state.filename
        extension = None
        if filename is not None:
            if "." in filename:
                extension = filename.split(".")[-1]

        b, mimetype, type_identifier = encode_state_data(
            state.get(), extension=extension
        )
        if filename is None:
            filename = state_types_registry().get(type_identifier).default_filename()

        header = "Content-Type"
        body = mimetype
        self.set_header(header, body)

        self.write(b)


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
