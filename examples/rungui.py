# Example/test of a GUI

# Make it run from the examples directory
import sys
sys.path.append("..")

import logging
import liquer.server.blueprint as bp
import webbrowser
from flask import Flask, make_response, redirect
from liquer.cache import FileCache, set_cache
from liquer.state import set_var, get_vars
from liquer import *
import liquer.ext.basic
import liquer.ext.meta
import liquer.ext.lq_pandas
import liquer.ext.lq_hxl
import liquer.ext.lq_python
import liquer.ext.lq_pygments

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
#set_var("menu",[
#    dict(title="Test", items=[
#        dict(title="Hello, world - html", link="hello_html/hello.html"),
#        dict(title="Hello, world - text", link="hello_text"),
#        dict(title="Logo", link="logo/logo.png"),
#    ]),
#   dict(title="Help", items=[
#        dict(title="Commands", link="ns-meta/flat_commands_nodoc/to_df"),
#        dict(title="Homepage", link="https://orest-d.github.io/liquer/"),
#    ])
#])

def add_menuitem(title, subtitle, link):
    menu = get_vars().get("menu",[])
    try:
        item_number = [i for i,item in enumerate(menu) if item["title"]==title][0]
    except:
        menu.append(dict(title=title,items=[]))
        item_number = len(menu)-1
    menu[item_number]["items"].append(dict(title=subtitle,link=link))
    set_var("menu",menu)

add_menuitem("Test", "Hello, world - html", "hello_html/hello.html")
add_menuitem("Test", "Hello, world - txt",  "hello_text")
add_menuitem("Help", "Commands",            "ns-meta/flat_commands_nodoc/to_df")
add_menuitem("Help", "Homepage",            "https://orest-d.github.io/liquer/")
 
@first_command(
    example_link="hello_html",
    context_menu=[
      dict(title="Hello help", link="/ns-meta/help-hello_html"),
      dict(title="Hello GUI", link="gui")
    ])
def hello_html(world="World"):
    "xxx this is a hello world example"
    return f"""
<html>
<body>
  <h1>Hello</h1>
  {world}!
</body>
</html>
    """

@first_command
def hello_text():
    return """
    Hello, world!
    """

@command
def gui(state):
    import liquer.parser as p
    d = state.as_dict()
    c = d["extended_commands"][-1]
    m = c["command_metadata"]
    ns = c['ns']
    name = m['name']
    title = d["attributes"].get("title",m["label"])
    help_link=( d["vars"].get("server", "http://localhost")+
                d["vars"].get("api_path", "/q/")+
                f"ns-meta/help-{name}-{ns}/help.html")
    query_start=p.encode(d["commands"][:-1]+[[d["commands"][-1][0]]])
    html=f"""
<!DOCTYPE html>
<html>

<head>
    <link href="https://fonts.googleapis.com/css?family=Roboto:100,300,400,500,700,900" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/@mdi/font@4.6.95/css/materialdesignicons.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/vuetify@2.1.12/dist/vuetify.min.css" rel="stylesheet">
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, minimal-ui">
    <title>{title}</title>
</head>
<body>
    <div id="app" color="indigo">
        <v-app>
            <v-content>
                <v-container class="fill-height" fluid>
                <v-card width="100%">
                    <v-toolbar color="secondary" dark>
                        <v-toolbar-title>{title}</v-toolbar-title>
                        <v-spacer></v-spacer>
                        <v-btn href="{help_link}">Help</v-btn>
                    </v-toolbar>
                    <v-content>
                    <v-container>
"""
    for value,a in c["arguments"]:
        html+=f"""<v-row><v-text-field v-model="{a['name']}" label="{a['label']}"></v-text-field></v-row>
        """
    html+="""<v-row><b>Query:</b>{{_query}}</v-row>
        """
    html+="""<v-row><b>Link:</b><a :href="_link">{{_link}}</a></v-row>
        """
    html+="""<v-row><v-spacer></v-spacer><v-btn :href="_link">Execute</v-btn></v-row>
        """


    html+="""       </v-container>
                    <v-content>
                </v-card>
                </v-container>
            </v-content>
        </v-app>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/vue@2.x/dist/vue.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/vue-resource@1.5.1"></script>
    <script src="https://cdn.jsdelivr.net/npm/vuetify@2.1.12/dist/vuetify.min.js"></script>
    <script>
    new Vue({
      el: '#app',
      data:{
"""
    qq=""
    for value, a in c["arguments"]:
        if isinstance(value,list):
            value = "-".join(p.encode_token(value))
        html+=f"""{a['name']}:"{value}",
        """
        qq+=f"+'-'+this.{a['name']}"
    html+="""
      },
      computed:{
        _query: function(){
            return '%s'%s;
        },          
        _link: function(){
            return '%s'+this._query;
        }          
      },
      vuetify: new Vuetify(),
    })    
    </script>
</body>

</html>    
    """%(query_start,qq,d["vars"].get("server", "http://localhost")+d["vars"].get("api_path", "/q/"))
    return state.with_data(html).with_filename("gui.html")

@app.route('/', methods=['GET', 'POST'])
@app.route('/index.html', methods=['GET', 'POST'])
def index():
    """Link to a LiQuer main service page"""
    return redirect("/liquer/static/index.html")

set_cache(FileCache("cache"))

if __name__ == '__main__':
    webbrowser.open("http://localhost:5000")
    app.run(debug=True,threaded=False)
