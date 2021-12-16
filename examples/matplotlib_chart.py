# Make it run from the examples directory
import sys
sys.path.append("..")

import pandas as pd
import numpy as np
from liquer import *
import liquer.ext.lq_pandas
import liquer.ext.lq_matplotlib
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
    <li><a href="/liquer/q/data/mpl-xy-xcol-ycol">chart</a></li>
    <li><a href="/liquer/q/data/mpl-xy-xcol-ycol">chart</a></li>
    <li><a href="/liquer/q/sin_cos_chart/sin_cos_chart.png">png</a>,
        <a href="/liquer/q/sin_cos_chart/sin_cos_chart.svg">svg</a>,
        <a href="/liquer/q/sin_cos_chart/sin_cos_chart.pdf">pdf</a></li>
    </ul>
    """

@first_command
def data():
    x = np.linspace(0,2*np.pi,100)
    y = np.sin(x)
    return pd.DataFrame(dict(xcol=x,ycol=y))

@first_command
def sin_cos_chart():
    import matplotlib.pyplot as plt
    x = np.linspace(0,2*np.pi,100)
    
    fig, ax = plt.subplots()
    ax.plot(x,np.sin(x))
    ax.plot(x,np.cos(x))
    return fig

if __name__ == '__main__':
    evaluate_and_save("data/mpl-xy-xcol-ycol/matplotlib_chart.png")
#    evaluate_and_save("sin_cos_chart/sin_cos_chart.png")
#    evaluate_and_save("sin_cos_chart/sin_cos_chart.pdf")
    app.run()