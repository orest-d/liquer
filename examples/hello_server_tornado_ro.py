# Make it run from the examples directory

# Example of server exposing just read-only services
# This does not allow writing, modifying, deleting or executing queries.
# Only cached results will be available.
# Therefore we create cache ane evaluate couple of queries before starting server.
# The url_mapping_ro is used to select "safe" tornado handlers.

import sys
sys.path.append("..")

from liquer import *
from liquer.server.tornado_handlers import url_mapping_ro, liquer_static_path, CacheCleanHandler
import tornado.ioloop
import tornado
import asyncio
from liquer.cache import set_cache, MemoryCache

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
    <li><a href="/liquer/q/hello/greet?who=everybody">greet everybody by URL parameters - not working correctly</a></li>
    <li><a href="/liquer/api/cache/clean">clean cache (once cache is cleaned, queries will stop working)</a></li>
    </ul>
    """)



async def main():
    port = 5000

    application = tornado.web.Application(
        url_mapping_ro() + [
            (
                r"/liquer/static/(.*)",
                tornado.web.StaticFileHandler,
                {"path": liquer_static_path()},
            ),
            (r"/liquer/api/cache/clean", CacheCleanHandler), # Clean cache is explicitly enabled
            (r"/", IndexHandler),
            (r"/index.html", IndexHandler),
        ]
    )
    application.listen(port)
    await asyncio.Event().wait()

if __name__ == '__main__':
    set_cache(MemoryCache())
    evaluate("hello")
    evaluate("hello/greet")
    evaluate("hello/greet-everybody")
    asyncio.run(main())
