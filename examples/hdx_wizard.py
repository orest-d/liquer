# Example of a wizard for Humanitarian Data Exchange

# Make it run from the examples directory
import sys
sys.path.append("..")

# Flask-related imports
import logging
import webbrowser
from flask import Flask
import liquer.blueprint as bp # This is the LiQuer blueprint containing the liquer web service 

# Modules needed to configure LiQuer
from liquer.cache import FileCache, set_cache  # Setting cache
from liquer.state import set_var               # Configuring the state variables

# Modules 
import liquer.ext.basic                        # basic modules (needed for the link command)
import liquer.ext.lq_pandas                    # pandas support
import liquer.ext.lq_hxl                       # libhxl support (not used by the wizard, but may be useful)

app = Flask(__name__)

# Setting the logger to make debugging info visible
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.INFO)

# Registering the liquer blueprint under a given url prefix and letting LiQuer know where it is...
url_prefix='/liquer'
app.register_blueprint(bp.app, url_prefix=url_prefix)
set_var("api_path",url_prefix+"/q/")
set_var("server","http://localhost:5000")

# Setting the cache
set_cache(FileCache("../cache"))

# Standard Flask way of showing a index.html (not LiQuer specific) 
@app.route('/', methods=['GET', 'POST'])
@app.route('/index.html', methods=['GET', 'POST'])
def index():
    return open("hdx_wizard.html").read()


# Start a service and open a browser
if __name__ == '__main__':
    webbrowser.open("http://localhost:5000")
    app.run(debug=True,threaded=False)
