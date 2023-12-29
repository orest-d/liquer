# Make it run from the examples directory
import sys
sys.path.append("..")

from liquer import *

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import gradio as gr
import liquer.server.fastapi as fa

app = FastAPI()

io = gr.Interface(lambda x: "Hello, " + x + "!", "textbox", "textbox")

app.include_router(fa.router, prefix="/liquer")
app = gr.mount_gradio_app(app, io, path="/gradio")

@first_command
def hello():
    return "Hello"

@command
def greet(greeting, who="world"):
    return f"{greeting}, {who}!"

@app.get('/')
def index():
    return HTMLResponse(content="""<h1>Hello-world app</h1>
    <ul>
    <li><a href="/gradio">hello gradio</a></li>
    <li><a href="/liquer/q/hello">just hello</a></li>
    <li><a href="/liquer/q/hello/greet">simple greet</a></li>
    <li><a href="/liquer/q/hello/greet-everybody">greet everybody</a></li>
    <li><a href="/liquer/q/hello/greet?who=everybody">greet everybody by URL parameters</a></li>
    </ul>
    """)

if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=8000)
