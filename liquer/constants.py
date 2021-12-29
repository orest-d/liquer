from enum import Enum


class Status(Enum):
    """Status of evaluated data.
    NONE         - status not available (default value)
    SUBMITTED    - immediately after submission (e.g. with pool.evaluate_in_background)
    EVALUATING_PARENT - parent is being evaluated
    EVALUATION   - last action of the query is being evaluated
    EVALUATING_DEPENDENCIES - evaluating dependencies, e.g. parameters
    READY        - data is ready (after successful evaluation)
    ERROR        - evaluation terminated with an error
    EXPIRED      - data exists, but it is obsolete or expired
    RECIPE       - data are not in store, but a recipe is available
    EXTERNAL     - data is from external source or modified by a user
    SIDE_EFFECT  - data has been created as a side-effect of a query
    
    """
    NONE = "none" # If status does not exist for some reason
    SUBMITTED = "submitted" # Immediately after submission
    EVALUATING_PARENT = "parent"
    EVALUATION = "evaluation"
    EVALUATING_DEPENDENCIES = "dependencies"
    ERROR = "error"
    RECIPE = "recipe"
    READY = "ready"
    EXPIRED = "expired"
    EXTERNAL = "external"
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
    pptx="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ods="application/vnd.oasis.opendocument.spreadsheet",
    tsv="text/tab-separated-values",
    csv="text/csv",
    css="text/css",
    yaml="application/x-yaml",
    msgpack="application/x-msgpack",
    hdf5="application/x-hdf",
    h5="application/x-hdf",
    b="application/octet-stream",
    bin="application/octet-stream",
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
    png="image/png",
    svg="image/svg+xml",
    jpg="image/jpeg",
    jpeg="image/jpeg",
    tga="image/tga",
    tiff="image/tiff",
    bmp="image/bmp",
    pcx="image/x-pcx",
    ppm="image/x-portable-pixmap",
    xbm="image/x-xbitmap",
    ico="image/x-icon",
    gif="image/gif",
    pcd="application/octet-stream",
    psd="application/octet-stream",
    wmf="image/wmf",
    aiff="audio/aiff",
    avi="video/avi",
)

TYPE_IDENTIFIER_BY_EXTENSION = dict(
    json="generic",
    djson="dictionary",
    js="text",
    txt="text",
    html="text",
    htm="text",
    md="text",
    yaml="text",
    xlsx="openpyxl_workbook",
    pptx="pptx_presentation",
    tsv="text",
    csv="dataframe",
    css="text",
    svg="text",
    b="bytes",
    pkl="pickle",
    pickle="pickle",
    parquet="dataframe",
    feather="dataframe",
    eps="image",
    png="image",
    jpg="image",
    jpeg="image",
    tga="image",
    tiff="image",
    bmp="image",
    pcx="image",
    ppm="image",
    xbm="image",
    ico="image",
    gif="image",
    pcd="image",
    psd="image",
    wmf="image",
)

def mimetype_from_extension(extension, default = "application/octet-stream"):
    return MIMETYPES.get(extension, default)

def type_identifier_from_extension(extension):
    return TYPE_IDENTIFIER_BY_EXTENSION.get(extension)
