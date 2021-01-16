import sys

sys.path.append("..")

import logging
import liquer.server.blueprint as bp
import webbrowser
from flask import Flask, make_response, redirect, jsonify
from liquer.cache import FileCache, set_cache, get_cache
from liquer.state import set_var, get_vars
from liquer import *
import liquer.ext.basic
import liquer.ext.meta
import liquer.ext.lq_pandas
import liquer.ext.lq_hxl
import liquer.ext.lq_python
import liquer.ext.lq_pygments
from time import sleep


from liquer.pool import set_central_cache

app = Flask(__name__)
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
werkzeug_logger = logging.getLogger("werkzeug")
werkzeug_logger.setLevel(logging.INFO)
url_prefix = "/liquer"
app.register_blueprint(bp.app, url_prefix=url_prefix)
set_var("api_path", url_prefix + "/q/")
set_var("server", "http://localhost:5000")


@app.route("/", methods=["GET", "POST"])
@app.route("/index.html", methods=["GET", "POST"])
def index():
    """Link to a LiQuer main service page"""
    return redirect("/liquer/static/index.html")


set_var(
    "menu",
    [
        dict(
            title="Progress Demo",
            items=[
                dict(title="Start", link="start"),
                dict(title="Start long", link="start-200"),
                dict(title="Start 2", link="start2"),
                dict(title="Nested", link="start-50/nested"),
                dict(title="Long nested", link="start-50/nested/nested/nested-10-10/nested-20-20/nested"),
                dict(title="Recursive", link="recursive-5"),
            ],
        )
    ],
)


@first_command
def start(count=5, context=None):
    for i in range(count):
        print(i)
        context.progress(i+1, count, message=f"Step {i+1} out of {count}")
        sleep(0.1)
    return f"Done {count}"


@first_command
def start2(count1=10, count2=10, context=None):
    from time import sleep

    p1 = context.new_progress_indicator() # low level progress reporting - create progress report handle
    p3 = context.new_progress_indicator()
    for i in range(count1):
        context.progress(
            i, count1, message=f"Outer loop {i} out of {count1}", identifier=p1
        ) # do the report with the andle
        p2 = context.new_progress_indicator()
        context.info(f"Step {i} started")
        for j in range(count2):
            print(i, j)
            context.progress(
                j, count2, message=f"Inner loop {j} out of {count2}", identifier=p2
            )
            context.progress(j, message=f"Undifferentiated {j}", identifier=p3)
            sleep(0.1)
        context.info(f"Step {i} finished")
        context.remove_progress_indicator(p2)
    context.remove_progress_indicator(p1) #remove the handle after use
    context.remove_progress_indicator(p3) #remove the handle after use

    return f"Done {count1}x{count2}"


@command
def nested(x, count1=5, count2=5, context=None):
    context.info("Nested command")
    text = "Nested: "+str(x)+"\n"
    for i in context.progress_iter(range(count1)):
        context.info(f"Nested command iteration {i}")
        text += str(context.evaluate(f"start-{count2+i}").get())+"\n"
    return text

@first_command
def recursive(count=5, context=None):
    context.info(f"Recursive command {count}")
    if count>0:
        text=""
        x = str(context.evaluate(f"recursive-{count-1}").get())+"\n"
        for i in context.progress_iter(range(count), True):
            text += x
            sleep(0.1)
        text+="\n"
    else:
        return "*"
    return text


if __name__ == "__main__":
    set_central_cache(FileCache("cache"))
#    set_cache(FileCache("cache"))           # the solution will still work with without the pool (evaluation in main process) 
    webbrowser.open("http://localhost:5000")
    app.run(debug=True, threaded=True)
