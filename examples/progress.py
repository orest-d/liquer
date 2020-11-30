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

import multiprocessing as mp

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

set_cache(FileCache("cache"))

set_var(
    "menu",
    [
        dict(
            title="Progress Demo",
            items=[
                dict(title="Start", link="start"),
                dict(title="Start long", link="start-200"),
                dict(title="Start 2", link="start2"),
            ],
        )
    ],
)

_pool = None


def pool():
    global _pool
    if _pool is None:
        _pool = mp.Pool(8)
    return _pool


@first_command
def start(count=5, context=None):
    from time import sleep

    for i in range(count):
        print(i)
        context.progress(i, count, message=f"Step {i} out of {count}")
        sleep(0.1)
    return "Done"


@first_command
def start2(count1=10, count2=10, context=None):
    from time import sleep

    p1 = context.new_progress_indicator()
    p3 = context.new_progress_indicator()
    for i in range(count1):
        context.progress(
            i, count1, message=f"Outer loop {i} out of {count1}", identifier=p1
        )
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
    return "Done"


@app.route("/liquer/submit/<path:query>")
def detached_serve(query):
    """Main service for evaluating queries"""
    pool().apply_async(detached_process_evaluate, args=[query])
    return jsonify(dict(status="OK", message="Submitted", query=query))


def detached_process_evaluate(query):
    set_cache(FileCache("cache"))
    evaluate(query)

def main():
    set_cache(FileCache("cache"))
    webbrowser.open("http://localhost:5000")
    app.run(debug=True, threaded=True)

if __name__ == "__main__":
    main()