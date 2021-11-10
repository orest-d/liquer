# Make it run from the examples directory
import sys
sys.path.append("..")

from liquer import *

### Get Pandas, numpy and sweetviz support
import pandas as pd
import numpy as np
import liquer.ext.lq_pandas
import liquer.ext.lq_sweetviz

### Create Flask app and register LiQuer blueprint
from flask import Flask
import liquer.server.blueprint as bp
app = Flask(__name__)
app.register_blueprint(bp.app, url_prefix='/liquer')

@first_command
def harmonic(n=100):
    a = np.linspace(0,2*np.pi,n)
    segment = np.array(a*10/(2*np.pi),dtype=int)
    return pd.DataFrame(
        dict(
            a=a,
            x=np.sin(a),
            y=np.cos(a),
            x2=np.sin(2*a),
            y2=np.cos(2*a),
            x3=np.sin(3*a),
            y3=np.cos(3*a),
            x4=np.sin(4*a),
            y4=np.cos(4*a),
            segment=segment,
            label=[f"{i+1}/{n}" for i in range(n)]
        )
    )

@command
def noise(df, sigma=0.1):
    columns = [c for c in df.columns if c.startswith("x") or c.startswith("y")]
    for c in columns:
        noise = np.random.normal(0.0,sigma,len(df))
        df[c]+=noise
    return df

@app.route('/')
@app.route('/index.html')
def index():
    return """<h1>Sweetviz example</h1>
    If you don't have <a href="https://github.com/fbdesignpro/sweetviz">sweetviz</a>, please install it with
    <pre>
    pip install sweetviz
    </pre>
    <ul>
    <li><a href="/liquer/q/harmonic/harmonic.html">simple example: harmonic 100 rows</a></li>
    <li><a href="/liquer/q/harmonic/sweetviz_analyze/report.html">harmonic 100 in sweetviz</a></li>
    <li><a href="/liquer/q/harmonic-1000/noise-0.1/sweetviz_analyze/report.html">noisy harmonic with 1000 rows in sweetviz</a></li>
    </ul>
    """

if __name__ == '__main__':
    app.run()
