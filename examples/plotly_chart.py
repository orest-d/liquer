# Make it run from the examples directory
import sys
sys.path.append("..")

import pandas as pd
import numpy as np
from liquer import *
import liquer.ext.lq_pandas
import liquer.ext.lq_plotly
from flask import Flask
import liquer.blueprint as bp
app = Flask(__name__)
app.register_blueprint(bp.app, url_prefix='/liquer')

@app.route('/')
@app.route('/index.html')
def index():
    return """<h1><a href="https://matplotlib.org/">Matplotlib</a> chart app</h1>
    <ul>
    <li><a href="/liquer/q/data/data.html">data</a></li>
    <li><a href="/liquer/q/data/data.csv">data (csv)</a></li>
    <li><a href="/liquer/q/data/plotly_chart-xy-xcol-ycol">chart</a></li>
    </ul>
    """

@first_command
def data():
    x = np.linspace(0,2*np.pi,100)
    y = np.sin(x)
    return pd.DataFrame(dict(xcol=x,ycol=y))


if __name__ == '__main__':
    app.run()
