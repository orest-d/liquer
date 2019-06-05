# Example of a wizard for 
import sys
sys.path.append("..")

import logging
import liquer.blueprint as bp
import webbrowser
from flask import Flask
from liquer.cache import FileCache, set_cache
from liquer.state import set_var
import liquer.ext.basic
import liquer.ext.lq_pandas
import liquer.ext.lq_hxl

app = Flask(__name__)
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.INFO)
url_prefix='/liquer'
app.register_blueprint(bp.app, url_prefix=url_prefix)
set_var("api_path",url_prefix+"/q/")
set_var("server","http://localhost:5000")

@app.route('/', methods=['GET', 'POST'])
@app.route('/index.html', methods=['GET', 'POST'])
def index():
    return open("hdx_wizard.html").read()


set_cache(FileCache("../cache"))

if __name__ == '__main__':
    webbrowser.open("http://localhost:5000")
    app.run(debug=True,threaded=False)
