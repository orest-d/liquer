from enum import Enum


class Status(Enum):
    NONE = "none"
    EVALUATING_PARENT = "evaluating parent"
    EVALUATION = "evaluation"
    EVALUATING_DEPENDENCIES = "evaluating dependencies"
    READY = "ready"
    ERROR = "error"
    OBSOLETE = "obsolete"
    RECIPE = "recipe"

MIMETYPES = dict(
    json="application/json",
    djson="application/json",
    js="text/javascript",
    txt="text/plain",
    html="text/html",
    htm="text/html",
    md="text/markdown",
    xls="application/vnd.ms-excel",
    xlsx="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ods="application/vnd.oasis.opendocument.spreadsheet",
    tsv="text/tab-separated-values",
    csv="text/csv",
    css="text/css",
    msgpack="application/x-msgpack",
    hdf5="application/x-hdf",
    h5="application/x-hdf",
    png="image/png",
    svg="image/svg+xml",
    jpg="image/jpeg",
    jpeg="image/jpeg",
    b="application/octet-stream",
    pkl="application/octet-stream",
    pickle="application/octet-stream",
    parquet="application/octet-stream",
    feather="application/octet-stream",
    wasm="application/wasm",
    mid="audio/midi",
    midi="audio/midi",
    pdf="application/pdf",
    ps="application/postscript",
    eps="image/eps",
)

def mimetype_from_extension(extension):
    return MIMETYPES.get(extension, "text/plain")
