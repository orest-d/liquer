# Make it run from the examples directory
import sys
sys.path.append("..")

from liquer import *
from liquer.store import web_mount, MemoryStore, get_store
import liquer.ext.meta
import liquer.ext.lq_pandas
import liquer.ext.lq_whoosh as whs


### Create Flask app and register LiQuer blueprint
from flask import Flask
import liquer.server.blueprint as bp
app = Flask(__name__)
app.register_blueprint(bp.app, url_prefix='/liquer')

# Mount a new store into the web/hello. This will be just in memory (MemoryStore).
web_mount("hello",MemoryStore())

# Initialize whoosh with a temporary directory
import tempfile
temp_dir = tempfile.mkdtemp()
whs.init(temp_dir)

# Create some files in the web store 
get_store().store("web/hello/index.html", "Hello from web store!", {"title":"Hello document", "description":"This is a hello document"})
# Create some files in the web store 
get_store().store("web/hello/another.html", "Another document", {"title":"Another document", "description":"This is another document"})

@command
def display(txt):
    if type(txt) == bytes: # Data from store come as bytes, so they need to be decoded
        txt = txt.decode("utf-8")
    return f"""<html>
<body>
<h1>Display</h1>
<pre>{txt}</pre>
</body>
</html>"""

@app.route('/')
@app.route('/index.html')
def index():
    return f"""<h1>Hello Whoosh</h1>
    Index is in {temp_dir}
    <hr/>
    <ul>
    <li><a href="/liquer/q/ns-whoosh/web/index.html">Search</a></li>
    <li><a href="/liquer/q/ns-whoosh/search-document/result.json">Search 'document' (json)</a></li>
    <li><a href="/liquer/q/ns-whoosh/search_json?query=document">Search 'document' (query parameter API)</a></li>
    <li><a href="/liquer/q/ns-whoosh/search-document/to_html/result.html">Search 'document' (html)</a></li>
    <li><a href="/liquer/q/ns-whoosh/search-another/result.json">Search 'another' (json)</a></li>
    <li><a href="/liquer/q/ns-whoosh/search-another/to_html/result.html">Search 'another' (html)</a></li>
    <li><a href="/liquer/q/ns-whoosh/reindex_store">reindex store</a></li>
    </ul>
    <br/>
    <hr/>
    <ul>
    <li><a href="/liquer/web/hello/index.html">Shortcut to web store</a></li>
    <li><a href="/liquer/web/hello">This works too</a></li>
    <li><a href="/liquer/api/store/data/web/hello/index.html">Store API</a></li>
    <li><a href="/liquer/api/store/metadata/web/hello/index.html">Store API (metadata)</a></li>
    <li><a href="/liquer/q/web/hello/index.html/-/display/index.html">Query with display command</a></li>
    <li><a href="/liquer/q/-R-meta/web/hello/index.html/-/ns-meta/status_md/status.txt">Status of the file in store</a></li>
    <li><a href="/liquer/q/web/hello/index.html/-/display/ns-meta/state/status_md/status.txt">Display status</a></li>
    <li><a href="/liquer/q/-R-meta/web/hello/-/ns-meta/status_md/status.txt">Dir status</a></li>
    <li><a href="/liquer/q/-R-meta/web/hello/-/ns-meta/dir_status/status.json">Dir status (json)</a></li>
    <li><a href="/liquer/q/-R-meta/web/hello/-/ns-meta/dir_status_df/status.html">Dir status (html)</a></li>
    <li><a href="/liquer/api/store/upload/web/hello/test.txt">Upload test.txt</a></li>
    <li><a href="/liquer/web/hello/test.txt">test.txt</a></li>
    </ul>
    """

if __name__ == '__main__':
    app.run()
