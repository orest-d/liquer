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
