from enum import Enum


class Status(Enum):
    """Status of evaluated data.
    NONE         - status not available; should be rare
    SUBMITTED    - immediately after submission (e.g. with pool.evaluate_in_background)
    EVALUATING_PARENT - parent is being evaluated
    EVALUATION   - last action of the query is being evaluated
    EVALUATING_DEPENDENCIES - evaluating dependencies, e.g. parameters
    READY        - data is ready (after successful evaluation)
    ERROR        - evaluation terminated with an error
    OBSOLETE     - data exists, but it is obsolete
    RECIPE       - data are not in store, but a recipe is available
    SIDE_EFFECT  - data has been created as a side-effect of a query
    
    """
    NONE = "none" # If status does not exist for some reason
    SUBMITTED = "submitted" # Immediately after submission
    EVALUATING_PARENT = "parent"
    EVALUATION = "evaluation"
    EVALUATING_DEPENDENCIES = "dependencies"
    READY = "ready"
    ERROR = "error"
    OBSOLETE = "obsolete"
    RECIPE = "recipe"
    SIDE_EFFECT = "side-effect"

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
