# Make it run from the examples directory
import sys
sys.path.append("..")

from liquer import *
from liquer.server.tornado_handlers import url_mapping, liquer_static_path
import tornado.ioloop
import tornado


@first_command
def hello():
    return "Hello"

@command
def greet(greeting, who="world"):
    return f"{greeting}, {who}!"


class IndexHandler(tornado.web.RequestHandler):
    def prepare(self):
        header = "Content-Type"
        body = "text/html"
        self.set_header(header, body)
    def get(self):
        self.write(b"""<h1>Hello-world app</h1>
    <ul>
    <li><a href="/liquer/q/hello">just hello</a></li>
    <li><a href="/liquer/q/hello/greet">simple greet</a></li>
    <li><a href="/liquer/q/hello/greet-everybody">greet everybody</a></li>
    <li><a href="/liquer/q/hello/greet?who=everybody">greet everybody by URL parameters</a></li>
    </ul>
    """)


if __name__ == '__main__':
    port = 5000

    application = tornado.web.Application(
        url_mapping() + [
            (
                r"/liquer/static/(.*)",
                tornado.web.StaticFileHandler,
                {"path": liquer_static_path()},
            ),
            (r"/", IndexHandler),
            (r"/index.html", IndexHandler),
        ]
    )
    application.listen(port)
    tornado.ioloop.IOLoop.current().start()
