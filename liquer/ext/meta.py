from liquer.commands import command, first_command, command_registry
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
    for r in command_registry().as_dict().values():
        if len(filters)==0 or all(r["attributes"].get(key) == value for key,value in filters):
            c={key:r.get(key) for key in ["name", "label", "module", "doc"]}
            for key, value in r["attributes"].items():
                if key not in c:
                    c[key]=value
            d.append(c)
    return d

@command(ns="meta")
def state(state):
    return state.as_dict()
