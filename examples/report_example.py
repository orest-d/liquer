# Example of making a report from WFP data

# Make it run from the examples directory
import sys
sys.path.append("..")

import logging
from flask import Flask
import liquer.blueprint as bp # This is the LiQuer blueprint containing the liquer web service 

from liquer.cache import MemoryCache, FileCache, set_cache  # Setting cache
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
set_cache(FileCache("../cache"))
#set_cache(MemoryCache())

wfp_url = "https://data.humdata.org/dataset/4fdcd4dc-5c2f-43af-a1e4-93c9b6539a27/resource/12d7c8e3-eff9-4db0-93b7-726825c4fe9a/download/wfpvam_foodprices.csv"
#wfp_url = "https://raw.githubusercontent.com/orest-d/liquer/master/tests/test.csv"
wfp_query = "df_from-"+encode_token(wfp_url)

@command
def datemy(df,y="mp_year",m="mp_month",target="date"):
    df.loc[:,target]=["%04d-%02d-01"%(int(year),int(month)) for year,month in zip(df[y],df[m])]
    return df

@command
def count(df, *groupby_columns):
    df.loc[:,"count"]=1
    return df.groupby(groupby_columns).count().reset_index().loc[:,list(groupby_columns)+["count"]]

@command
def geq(df, column, value:float):
    index = df.loc[:,column] >= value 
    return df.loc[index,:]

@command
def table(state):
    df = state.get()
    html=evaluate_template(f"""<a href="${state.query}/link-url-csv$">(data)</a> """)
    return html+df.to_html(index=False, classes="table table-striped")

@command
def report(state, from_year=2017, linktype=None):
    state = state.with_caching(False)
    def makelink(url):
        if linktype is None:
            return url
        extension = url.split(".")[-1]
        return evaluate(f"fetch-{encode_token(url)}/link-{linktype}-{extension}").get()

    try:
        source = state.sources[0]
    except:
        source = "???"
    
    LiQuer='<a href="https://github.com/orest-d/liquer">&nbsp;LiQuer&nbsp;</a>'
    df = state.get()
    try:
        title = ",".join(sorted(df.adm0_name.unique())) + f" since {from_year}"
    except:
        title = "report"
    return state.with_filename("report.html").with_data(evaluate_template(f"""
<html>
    <head>
        <title>{title}</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
        <link rel="stylesheet" href="{makelink('https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css')}" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">
    </head>
    <body>
        <div class="p-3 mb-2 bg-success text-white fixed-top shadow-sm">
            <a class="nav-link active" href="https://data.humdata.org"><img src="{makelink('https://centre.humdata.org/wp-content/uploads/hdx_new_logo_accronym2.png')}" style="height:30px;" alt="HDX"></a>
        </div>
        <div class="bg-light fixed-bottom border-top">
        Generated with {LiQuer} <span class="float-right">&#169; 2019 Orest Dubay</span>
        </div>
        <br/>
        <br/>
        <br/>
        <br/>
        <h1>{title}</h1>
        <div class="container-fluid">
            <div class="row">
                Data originate from <a href="{source}">&nbsp;{source}&nbsp;</a> were processed via a {LiQuer} service.
                Only data after {from_year} are shown (<a href="${state.query}/datemy/geq-mp_year-{from_year}/link-url-csv$">data</a>),
                complete data are <a href="${state.query}/datemy/link-url$">&nbsp;here</a>. 
            </div>
            <div class="row">
                <div class="col-md-6" style="height:50%;">${state.query}/datemy/geq-mp_year-{from_year}/groupby_mean-mp_price-date-cm_name/plotly_chart-xys-date-mp_price-cm_name$</div>
                <div class="col-md-6" style="height:50%;">${state.query}/datemy/geq-mp_year-{from_year}/count-adm1_name/plotly_chart-piexs-count-adm1_name$</div>
            </div>
            <div class="row">
                <div class="col-md-6" style="height:50%;">
                <h2>Average prices</h2>
                ${state.query}/datemy/geq-mp_year-{from_year}/groupby_mean-mp_price-cm_name/table$</div>
                <div class="col-md-6" style="height:50%;">
                <h2>Observations</h2>
                ${state.query}/datemy/geq-mp_year-{from_year}/count-adm1_name/table$</div>
            </div>
    </body>
</html>
    """))

@app.route('/')
@app.route('/index.html')
def index():
    return f"""<h1>Report app</h1>
    <ul>
    <li><a href="/liquer/q/{wfp_query}/eq-adm0_name-Afghanistan/report">Afghanistan</a></li>
    <li><a href="/liquer/q/{wfp_query}/eq-adm0_name-Yemen/report">Yemen</a></li>
    </ul>
    """


# Start a service and open a browser
if __name__ == '__main__':
    app.run(debug=True,threaded=False)
