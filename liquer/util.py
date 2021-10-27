from datetime import datetime


def format_datetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def now():
    return format_datetime(datetime.now())


def to_datetime(x):
    if isinstance(x, datetime.datetime):
        return x
    if isinstance(x, str):
        return datetime.datetime.strptime(x, "%Y-%m-%d %H:%M:%S")
