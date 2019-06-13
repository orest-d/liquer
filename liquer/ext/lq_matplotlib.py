import pandas as pd
import io
from urllib.request import urlopen
from matplotlib.figure import Figure
from matplotlib import pyplot as plt
import numpy as np
from liquer.commands import command


@command
def mpl(state, *series):
    """Matplotlib chart
    """
    fig = plt.figure(figsize=(8, 6), dpi=300)
    axis = fig.add_subplot(1, 1, 1)
    series = list(reversed(list(series)))
    df = state.get()
    extension = "png"
    
    while len(series):
        t = series.pop()
        if t in ["jpg","png","svg"]:
            extension = t
            continue
        elif t == "xy":
            xcol = series.pop()
            ycol = series.pop()
            state.log_info(f"Chart XY ({xcol} {ycol})")
            axis.plot(df[xcol],df[ycol],label=ycol)
            continue
        elif t == "xye":
            xcol = series.pop()
            ycol = series.pop()
            ecol = series.pop()
            state.log_info(f"Chart XY ({xcol} {ycol}) Error:{ecol}")
            axis.errorbar(df[xcol],df[ycol],yerr=df[ecol],label=ycol)
            continue
        elif t == "xyee":
            xcol = series.pop()
            ycol = series.pop()
            e1col = series.pop()
            e2col = series.pop()
            state.log_info(f"Chart XY ({xcol} {ycol}) Error:({e1col},{e2col})")
            axis.errorbar(df[xcol],df[ycol],yerr=[df[e1col],df[e2col]],label=ycol)
            continue
        elif t == "cxy":
            c = series.pop()
            xcol = series.pop()
            ycol = series.pop()
            axis.plot(df[xcol],df[ycol],c,label=ycol)
            continue
        else:
            state.log_warning(f"Unrecognized MPL parameter {t}")
    #fig.legend()
    output = io.BytesIO()
    fig.savefig(output, dpi=300, format=extension)
    return state.with_data(output.getvalue()).with_filename(f"image.{extension}")
