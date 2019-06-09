# Make it run from the examples directory
import sys
sys.path.append("..")

from liquer import *
import liquer.blueprint as bp
from flask import Flask
import pandas as pd
import liquer.ext.lq_pandas

# Create Flask app and register LiQuer blueprint
app = Flask(__name__)
app.register_blueprint(bp.app, url_prefix='/liquer')


@first_command
def data():
    return pd.DataFrame(dict(a=[1, 2, 3], b=[40, 50, 60]))


@command
def sum_columns(df, column1="a", column2="b", target="c"):
    df.loc[:, target] = df[column1]+df[column2]
    return df


@app.route('/')
@app.route('/index.html')
def index():
    return """<h1>Pandas example</h1>
    <ul>
    <li><a href="/liquer/q/data">data (default format)</a></li>
    <li><a href="/liquer/q/data/data.html">data (html)</a></li>
    <li><a href="/liquer/q/data/data.csv">data (csv)</a></li>
    <li><a href="/liquer/q/data/data.xlsx">data (xlsx)</a></li>
    <li><a href="/liquer/q/data/eq-b-50/eq.html">Built in equality command</a></li>
    <li><a href="/liquer/q/data/sum_columns/sum.html">sum</a></li>
    <li><a href="/liquer/q/data/sum_columns/sum_columns-a-c-d/sum2.html">sum 2</a></li>
    </ul>
    """


if __name__ == '__main__':
    app.run()
