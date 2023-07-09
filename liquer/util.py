from datetime import datetime


def format_datetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_time(dt):
    return dt.strftime("%H:%M:%S")


def now():
    return format_datetime(datetime.now())


def timestamp():
    date = datetime.now()
    return date.isoformat()


def to_datetime(x):
    if isinstance(x, datetime):
        return x
    if isinstance(x, str):
        try:
            return datetime.fromisoformat(x)
        except:
            return datetime.strptime(x, "%Y-%m-%d %H:%M:%S")

def eval_fully_qualified_name(name):
    """Evaluate fully qualified name to an object"""
    if name is None:
        return None
    if isinstance(name, str):
        if "." in name:
            module_name, object_name = name.rsplit(".", 1)
            module = __import__(module_name, fromlist=[object_name])
            return getattr(module, object_name)
        else:
            return globals()[name]
    else:
        return name