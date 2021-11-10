from liquer import *
from tempfile import TemporaryDirectory
from pathlib import Path

@command
def sweetviz_analyze(df, context=None):
    import sweetviz as sv
    context = get_context(context)
    context.info(f"Sweetviz analyze")
    report = sv.analyze(df)
    with TemporaryDirectory() as tempdir:
        path = Path(tempdir)/"sweetviz_analyze_report.html"
        context.info(f"Using temporary file {path}")
        report.show_html(filepath=str(path), open_browser=False)
        with path.open() as f:
            return f.read()
