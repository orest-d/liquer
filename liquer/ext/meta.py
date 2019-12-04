from liquer.commands import command, first_command, command_registry
from liquer.query import evaluate_template
import liquer.ext.basic

@first_command(ns="meta")
def commands():
    """Returns a list of commands in json format"""
    return command_registry().as_dict()

@first_command(ns="meta")
def flat_commands(*pairs):
    """Returns a list of commands in json format"""
    filters = [(pairs[i-1],pairs[i]) for i in range(1,len(pairs),2)]
    d=[]
    for rl in command_registry().as_dict().values():
        for r in rl.values():
            if len(filters)==0 or all(r["attributes"].get(key) == value for key,value in filters):
                c={key:r.get(key) for key in ["name", "label", "module", "doc"]}
                for key, value in r["attributes"].items():
                    if key not in c:
                        c[key]=value
                d.append(c)
    return d

@first_command(ns="meta")
def flat_commands_nodoc(*pairs):
    """Returns a list of commands in json format"""
    filters = [(pairs[i-1],pairs[i]) for i in range(1,len(pairs),2)]
    d=[]
    for rl in command_registry().as_dict().values():
        for r in rl.values():
            if len(filters)==0 or all(r["attributes"].get(key) == value for key,value in filters):
                c={key:r.get(key) for key in ["name", "label", "module"]}
                for key, value in r["attributes"].items():
                    if key not in c and key!="context_menu":
                        c[key]=value
                d.append(c)
    return d

@command
def state(state):
    """Returns dictionary with all metadata for the resulting state"""
    return state.as_dict()

@command(ns="meta")
def help(state, command_name, ns="root"):
    """Returns a description of the command"""
    crd = command_registry().as_dict()
    make_link =  ("py" in crd) and ("pygments" in crd)
    try:
        r = crd[ns]
        try:
            c = r[command_name]
            html=f"<html><head><title>{command_name}</title></head>"
            html="<body\n>"
            html=f"<h1>{command_name} <em>({ns})</em></h1>\n"
            html+=f"<pre>{c['doc']}</pre>\n"
            html+="<h3>Arguments</h3>\n"
            html+="  <ul>\n"
            for a in c["arguments"]:
                html+=f"    <li><b>{a['name']}</b> - type: {a['type']}</li>\n"
            html+="  </ul>"
            html+="<h3>Attributes</h3>\n"
            html+="  <ul>\n"
            for key,value in sorted(c["attributes"].items()):
                if key == "example_link":
                    q=value
                    url=state.vars.get("server", "http://localhost")+state.vars.get("api_path", "/q/")+q
                    html+=f'    <li><b>{key}</b>:<a href="{url}">{value}</a></li>\n'
                else:
                    html+=f"    <li><b>{key}</b>:{value}</li>\n"
            html+="  </ul>"
            html+=f"<h3>Python module</h3>\n"
            module = c['module']
            if make_link:
                modfile = module.replace(".","_")
                html+=evaluate_template(f'<a href="$ns-py-pygments/module_source-{module}/highlight/link-url-html$/{modfile}.html">{module}</a>\n')
            else:
                html+=module

            html+="</body>"
            html+="</html>"
            return state.with_data(html).with_filename("help.html")
        except KeyError:
            html = f"<h1>Command <em>{command_name}</em> not registered in namespace <em>{ns}</em></h1>"
            candidates = ", ".join(key for key,value in crd.items() if command_name in value)
            if len(candidates):
                html+=f"Command can be found in: {candidates}"
            else:
                html+="There is no such command in available namespaces"
            return state.with_data(html).with_filename("help.html")
    except KeyError:
        return state.with_data(f"<h1>Unknown namespace <em>{ns}</em></h1>").with_filename("help.html")

if __name__=="__main__":
    from liquer import *
    print(evaluate("ns-meta/flat_commands").get())
    #print(evaluate("ns-meta/commands/state").get()["commands"])
    #evaluate_and_save("ns-meta/commands/state/state.json")