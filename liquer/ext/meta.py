from liquer.commands import command, first_command, command_registry
from liquer.query import evaluate_template
import liquer.ext.basic
from liquer.context import *
import traceback


@first_command(ns="meta")
def commands():
    """Returns a list of commands in json format"""
    return command_registry().as_dict()


@first_command(ns="meta")
def flat_commands(*pairs):
    """Returns a list of commands in json format"""
    filters = [(pairs[i - 1], pairs[i]) for i in range(1, len(pairs), 2)]
    d = []
    for rl in command_registry().as_dict().values():
        for r in rl.values():
            if len(filters) == 0 or all(
                r["attributes"].get(key) == value for key, value in filters
            ):
                c = {key: r.get(key) for key in ["name", "label", "module", "doc"]}
                for key, value in r["attributes"].items():
                    if key not in c:
                        c[key] = value
                d.append(c)
    return d


@first_command(ns="meta")
def flat_commands_nodoc(*pairs):
    """Returns a list of commands in json format"""
    filters = [(pairs[i - 1], pairs[i]) for i in range(1, len(pairs), 2)]
    d = []
    for rl in command_registry().as_dict().values():
        for r in rl.values():
            if len(filters) == 0 or all(
                r["attributes"].get(key) == value for key, value in filters
            ):
                c = {key: r.get(key) for key in ["name", "label", "module"]}
                for key, value in r["attributes"].items():
                    if key not in c and key != "context_menu":
                        c[key] = value
                d.append(c)
    return d


@command
def state(state):
    """Returns dictionary with all metadata for the resulting state"""
    return state.as_dict()

@command(ns="meta")
def metadata(state):
    """Returns dictionary with all metadata for the resulting state"""
    return {**state.metadata}

@command(ns="meta")
def help(state, command_name, ns="root"):
    """Returns a description of the command"""
    crd = command_registry().as_dict()
    make_link = ("py" in crd) and ("pygments" in crd)
    try:
        r = crd[ns]
        try:
            c = r[command_name]
            html = f"<html><head><title>{command_name}</title></head>"
            html = "<body\n>"
            html = f"<h1>{command_name} <em>({ns})</em></h1>\n"
            html += f"<pre>{c['doc']}</pre>\n"
            html += "<h3>Arguments</h3>\n"
            html += "  <ul>\n"
            for a in c["arguments"]:
                html += f"    <li><b>{a['name']}</b> - type: {a['type']}</li>\n"
            html += "  </ul>"
            html += "<h3>Attributes</h3>\n"
            html += "  <ul>\n"
            for key, value in sorted(c["attributes"].items()):
                if key == "example_link":
                    q = value
                    url = (
                        state.vars.get("server", "http://localhost")
                        + state.vars.get("api_path", "/q/")
                        + q
                    )
                    html += f'    <li><b>{key}</b>:<a href="{url}">{value}</a></li>\n'
                else:
                    html += f"    <li><b>{key}</b>:{value}</li>\n"
            html += "  </ul>"
            html += f"<h3>Python module</h3>\n"
            module = c["module"]
            if make_link:
                modfile = module.replace(".", "_")
                html += evaluate_template(
                    f'<a href="$ns-py-pygments/module_source-{module}/highlight/link-url-html$/{modfile}.html">{module}</a>\n'
                )
            else:
                html += module

            html += "</body>"
            html += "</html>"
            return state.with_data(html).with_filename("help.html")
        except KeyError:
            html = f"<h1>Command <em>{command_name}</em> not registered in namespace <em>{ns}</em></h1>"
            candidates = ", ".join(
                key for key, value in crd.items() if command_name in value
            )
            if len(candidates):
                html += f"Command can be found in: {candidates}"
            else:
                html += "There is no such command in available namespaces"
            return state.with_data(html).with_filename("help.html")
    except KeyError:
        return state.with_data(
            f"<h1>Unknown namespace <em>{ns}</em></h1>"
        ).with_filename("help.html")

@command(ns="meta")
def status_md(metadata):
    txt = ""
    txt+="# %s%s\n\n"%(metadata.get("title","???"), " (ERROR)" if metadata.get("is_error") else "")
    if metadata.get("key") is not None:
        txt+="KEY:             %s\n"%(metadata.get("key",""))
        if metadata.get("has_recipe",False):
            txt+="Resource has a recipe\n"

    txt+="QUERY:           %s\n"%(metadata.get("query","???"))
    txt+="STATUS:          %s\n"%(metadata.get("status","???"))
    txt+="TYPE IDENTIFIER: %s\n"%(metadata.get("type_identifier","???"))
    txt+="MIME:            %s\n"%(metadata.get("mimetype","???"))
    txt+="PARENT:          %s\n"%(metadata.get("parent_query","???"))
    txt+="\nMESSAGE:         %s\n\n"%(metadata.get("message",""))

    txt+="STARTED: %s\n"%(metadata.get("started","-"))
    txt+="UPDATED: %s\n"%(metadata.get("updated","-"))
    txt+="CREATED: %s\n"%(metadata.get("created","-"))
    txt+="\n"

    fileinfo = metadata.get("fileinfo")
    if fileinfo is not None:
        txt+="\n## FILEINFO%s\n"%(" (DIRECTORY)" if fileinfo.get("is_dir") else "")
        txt+="NAME   : %s\n"%(fileinfo.get("name",""))
        txt+="PATH   : %s\n"%(fileinfo.get("filesystem_path","-"))
        txt+="SIZE   : %s\n"%(fileinfo.get("size","?"))
        txt+="\n"

    txt+="\n## DESCRIPTION:\n%s\n"%(metadata.get("description",""))

    
    txt+="\n## DATA CHARACTERISTICS:\n%s\n\n"%(metadata.get("data_characteristics",{}).get("description",""))

    for key,value in sorted(metadata.get("data_characteristics",{}).items()):
        if key not in ("description","type_identifier"):
            txt+="%-20s:%s\n"%(key, repr(value))

    txt+="\n## STATE VARIABLES\n"
    for key, value in sorted(metadata.get("vars",{}).items()):
        txt+="%-20s:%s\n"%(key, repr(value))
    
    txt+="\n## LOGS\n"
    for name, log in [
        ("Main log",metadata.get("log")),
        ("Child log",metadata.get("child_log")),
        ("Resource log",metadata.get("resource_metadata",{}).get("log")),
        ("Resource child log",metadata.get("resource_metadata",{}).get("child_log"))
        ]:
        if log is not None and len(log):
            txt+=f"\n### {name}\n"
            for entry in log:
                if type(entry)!=dict:
                    txt+=f"INVALID ENTRY {repr(entry)}\n"
                else:
                    txt+="%-10s %-28s %s\n"%(entry.get("kind","?????"), entry.get("timestamp",""), entry.get("origin",""))
                    txt+="%-10s %s\n"%("",entry.get("message"))
                    tb = entry.get('traceback')
                    if tb is not None:
                        if len(tb):
                            txt+=tb
                            txt+="\n"

#    txt+="## LOG\n"
#    for record in metadata.get("log",[]):
#        txt+=str(record)
    return txt

@command(ns="meta")
def dir_status(metadata, context=None):
    context = get_context(context)
    if metadata is None:
        key=""
    else:
        key = metadata.get("key")
    print("context", context)
    context.set_title(f"Status of directory {key}")
    context.set_description(f"Status overview of data in the directory {key}")
    store = context.store()
    data = []
    if store.is_dir(key):
        for name in store.listdir(key):
            metadata = store.get_metadata(store.join_key(key,name))
            fileinfo = metadata.get("fileinfo",{})
            data.append(dict(
                name=name,
                key=metadata.get("key"),
                query=metadata.get("query"),
                title=metadata.get("title"),
                description=metadata.get("description"),
                status=metadata.get("status"),
                is_error=metadata.get("is_error"),
                message=metadata.get("message",""),
                data_characteristics=metadata.get("data_characteristics",{}).get("description",""),
                is_dir=fileinfo.get("is_dir"),
                size=fileinfo.get("size"),
                started=metadata.get("started"),
                created=metadata.get("created"),
                updated=metadata.get("updated"),
                ))
        return dict(status="OK", message="OK", data=data)
    else:
        return dict(status="ERROR", message=f"Not a directory:{key}", data=[])

@command(ns="meta")
def dir_status_df(metadata, context=None):
    import pandas as pd
    context = get_context(context)
    data = dir_status(metadata, context=context)
    return pd.DataFrame(data["data"], columns=[
        "name", "title", "status", "is_error", "message", "data_characteristics", "started", "created", "updated",
        "key", "query", "description", "is_dir", "size"])

@command(ns="meta")
def clean_recipes(metadata, recursive=False, context=None):
    """Remove specific key or all the data in the directory of store that has a recipe.
    This is supposed to be used together with a RecipeStore, that creates has_recipe flag in the metadata.
    Data can be optionally cleaned recursively in all the subdirectories.

    Examples:
    -R-meta/my_dir/-/ns-meta/clean_recipes    - deletes all data with recipes in my_dir (but not its subfolders)
    -R-meta/my_dir/-/ns-meta/clean_recipes-t  - deletes all data with recipes in my_dir and its subfolders
    -R-meta/-/ns-meta/clean_recipes-t         - clean all the data with recipes everywhere
    """
    context = get_context(context)

    if not isinstance(metadata, dict) or "key" not in metadata:
        raise Exception("Valid metadata with a key expected in clean_recipes")

    key = metadata["key"]
    store=context.store()
    removed=[]

    if store.is_dir(key):
        if key in ("",None):
            if recursive:
                keys = store.keys()
            else:
                keys = store.listdir(key)
        else:
            if recursive:
                keys = [k for k in store.keys() if k.startswith(f"{key}/")]
            else:
                keys = [f"{key}/{name}" for name in store.listdir(key)]
    for key in keys:
        if store.is_dir(key):
            continue
        try:
            metadata = store.get_metadata(key)
            if metadata.get("has_recipe",False):
                context.info(f"Remove {key}")
                store.remove(key)
                removed.append(key)
        except:
            context.warning(f"Failed to process {key} ")
            context.warning(traceback.format_exc())
    context.info(f"Removed {len(removed)} items")
    return dict(status="OK", message=f"Removed {len(removed)} items", removed=removed)

if __name__ == "__main__":
    from liquer import *

    print(evaluate("ns-meta/flat_commands").get())
    # print(evaluate("ns-meta/commands/state").get()["commands"])
    # evaluate_and_save("ns-meta/commands/state/state.json")
