# Example of making a report from WFP data

# Make it run from the examples directory
import sys
sys.path.append("..")

import logging
from flask import Flask
import liquer.blueprint as bp # This is the LiQuer blueprint containing the liquer web service 

from liquer.cache import MemoryCache, set_cache  # Setting cache
from liquer.state import set_var               # Configuring the state variables
from liquer.parser import encode_token
from liquer import *

# Modules 
import liquer.ext.basic
import liquer.ext.lq_pandas
import liquer.ext.lq_matplotlib
import liquer.ext.lq_plotly

app = Flask(__name__)

# Registering the liquer blueprint under a given url prefix and letting LiQuer know where it is...
url_prefix='/liquer'
app.register_blueprint(bp.app, url_prefix=url_prefix)
set_var("api_path",url_prefix+"/q/")
set_var("server","http://localhost:5000")

# Setting the cache
set_cache(MemoryCache())

wfp_url = "https://data.humdata.org/dataset/4fdcd4dc-5c2f-43af-a1e4-93c9b6539a27/resource/12d7c8e3-eff9-4db0-93b7-726825c4fe9a/download/wfpvam_foodprices.csv"
wfp_url = "https://raw.githubusercontent.com/orest-d/liquer/master/tests/test.csv"
wfp_query = "df_from-"+encode_token(wfp_url)

@command
def report(state, linktype=None):
    def makelink(url):
        if linktype is None:
            return url
        extension = url.split(".")[-1]
        return evaluate(f"fetch-{encode_token(url)}/link-{linktype}-{extension}").get()

    try:
        source = state.sources[0]
    except:
        source = "???"

    return state.with_filename("report.html").with_data(evaluate_template(f"""
<html>
    <head>
        <title>Report</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        <link rel="stylesheet" href="{makelink('https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css')}" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">
    </head>
    <body>
        <a class="nav-link active" href="https://data.humdata.org"><img src="{makelink('https://centre.humdata.org/wp-content/uploads/hdx_new_logo_accronym2.png')}" style="height:30px;" alt="HDX"></a>
        <br/>
        <h1>Report</h1>
        Data obtained from <a href="{source}">{source}</a> and processed via service (<a href="${state.query}/link-url$">data</a>).

    </body>
</html>
    """))

@app.route('/')
@app.route('/index.html')
def index():
    return f"""<h1>Report app</h1>
    <ul>
    <li><a href="/liquer/q/{wfp_query}/eq-a-1/report">make report</a></li>
    </ul>
    """


# Start a service and open a browser
if __name__ == '__main__':
    app.run(debug=True,threaded=False)
