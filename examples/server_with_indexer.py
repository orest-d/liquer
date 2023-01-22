# Make it run from the examples directory
import sys
sys.path.append("..")

from liquer import *
import liquer.ext.basic
import liquer.ext.meta
import liquer.ext.lq_pandas
import liquer.ext.lq_sweetviz

from liquer.indexer import register_tool_for_type
import pandas as pd

### Create Flask app and register LiQuer blueprint
from flask import Flask
import liquer.server.blueprint as bp
app = Flask(__name__)
app.register_blueprint(bp.app, url_prefix='/liquer')

@first_command
def df():
    return pd.DataFrame(dict(a=[1,2,3,4], b=[5,6,7,8]))

@command
def describe(df):
    return df.describe().reset_index()

register_tool_for_type("dataframe", "$$UNNAMED_URL$/describe/description.html", "Description")

@app.route('/')
@app.route('/index.html')
def index():
    return """<h1>Hello-world app</h1>
    <ul>
    <li><a href="/liquer/q/df/df.html">table</a></li>
    <li><a href="/liquer/q/df/ns-meta/metadata/metadata.json">metadata</a></li>
    <li><a href="/liquer/q/df/ns-meta/metadata_txt/metadata.txt">metadata txt</a></li>
    </ul>
    """

if __name__ == '__main__':
    app.run(debug=True)
