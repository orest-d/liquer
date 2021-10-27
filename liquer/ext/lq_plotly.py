import pandas as pd
import io
from urllib.request import urlopen
import numpy as np
from liquer.commands import command
import plotly.graph_objs as go
from plotly.offline import download_plotlyjs, plot


@command
def plotly_chart(state, *series):
    """Plotly chart"""
    series = list(reversed(list(series)))
    df = state.get()
    extension = "html"
    output_type = "page"
    include_plotlyjs = True
    html = ""

    while len(series):
        t = series.pop()
        if t in ["div"]:
            output_type = t
        elif t in ["cdn"]:
            include_plotlyjs = t
        elif t == "xy":
            xcol = series.pop()
            ycol = series.pop()
            state.log_info(f"Chart XY ({xcol} {ycol})")
            html = plot(
                [go.Scatter(x=df[xcol], y=df[ycol])], show_link=False, output_type="div"
            )
            continue
        elif t == "xys":
            xcol = series.pop()
            ycol = series.pop()
            scol = series.pop()
            state.log_info(f"Chart XY Set ({xcol} {ycol} {scol})")
            datasets = list(sorted(df[scol].unique()))
            p = []
            for ds in datasets:
                index = df[scol] == ds
                p.append(
                    go.Scatter(
                        x=df.loc[index, xcol],
                        y=df.loc[index, ycol],
                        mode="lines+markers",
                        name=ds,
                    )
                )
            html = plot(p, show_link=False, output_type="div")
        elif t == "piexs":
            xcol = series.pop()
            scol = series.pop()
            state.log_info(f"Pie X Set ({xcol} {scol})")
            html = plot(
                [
                    go.Pie(
                        labels=df[scol],
                        values=df[xcol],
                        hoverinfo="label+percent",
                        textinfo="value",
                    )
                ],
                show_link=False,
                output_type="div",
            )
        else:
            state.log_warning(f"Unrecognized plotly_chart parameter {t}")
    if output_type == "page":
        html = f"""<html><body>{html}</body></html>"""
    return state.with_data(html).with_filename(f"image.{extension}")
