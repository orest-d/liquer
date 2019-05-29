from urllib.parse import quote, unquote

COMMAND_SEPARATOR="/"
PARAMETER_SEPARATOR="-"
ESCAPE="~"
ESCAPE_SEQUENCES=[
    (ESCAPE, ESCAPE + ESCAPE),
    ("https://", ESCAPE + "H"),
    ("http://", ESCAPE + "h"),
    ("://", ESCAPE + "P"),
    (COMMAND_SEPARATOR, ESCAPE + "I"),
    (PARAMETER_SEPARATOR, ESCAPE + "."),
    (" ", ESCAPE + "_")
]

def decode(query):
    ql = [[decode_token(etoken) for etoken in eqv.split(PARAMETER_SEPARATOR)] for eqv in query.split(COMMAND_SEPARATOR)]
    return [qcommand for qcommand in ql if len(qcommand) and len(qcommand[0])]
def encode_token(token):
    "Encode single token by escaping special characters and character sequences"
    for sequence, encoding in ESCAPE_SEQUENCES:
        token = token.replace(sequence,encoding)
    return quote(token).replace("%7E","~").replace("%7e","~")

def decode_token(token):
    "Decode single token by un-escaping special characters and character sequences"
    encoding = {e:s for s,e in ESCAPE_SEQUENCES}
    if token=="":
        return ""
    try:
        index = token.index(ESCAPE)
        head = token[:index]
        mid = token[index:index+2]
        tail = token[index+2:]
        return unquote(head + encoding.get(mid,mid)) + decode_token(tail)
    except ValueError:
        return unquote(token)

def encode(ql):
    return COMMAND_SEPARATOR.join(PARAMETER_SEPARATOR.join(encode_token(token) for token in qv) for qv in ql)

def all_splits(query):
    ql = decode(query)
    for i in range(len(ql),-1,-1):
        yield encode(ql[:i]),encode(ql[i:])
