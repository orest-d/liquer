import pandas as pd
from io import BytesIO
from urllib.request import urlopen
from matplotlib.figure import Figure
from matplotlib import pyplot as plt
import numpy as np
from liquer.commands import command
from liquer.state_types import StateType, register_state_type
from liquer.constants import mimetype_from_extension

import pickle


class MatplotlibFigureStateType(StateType):
    def identifier(self):
        return "matplotlibfigure"

    def default_extension(self):
        return "pickle"

    def is_type_of(self, data):
        return isinstance(data, plt.Figure)

    def as_bytes(self, data, extension=None):
        if extension is None:
            extension = self.default_extension()
        assert self.is_type_of(data)
        mimetype = mimetype_from_extension(extension)
        if extension in ("html", "htm"):
            output = StringIO()
            data.to_html(output, index=False)
            return output.getvalue().encode("utf-8"), mimetype
        elif extension in ("pkl", "pickle"):
            output = BytesIO()
            pickle.dump(data, output)
            return output.getvalue(), mimetype
        elif extension in ("png", "svg", "pdf", "ps", "eps"):
            output = BytesIO()
            data.savefig(output, dpi=300, format=extension)
            return output.getvalue(), mimetype
        else:
            raise Exception(
                f"Serialization: file extension {extension} is not supported by Matplotlib Figure type."
            )

    def from_bytes(self, b: bytes, extension=None):
        if extension is None:
            extension = self.default_extension()
        f = BytesIO()
        f.write(b)
        f.seek(0)

        if extension in ("pickle", "pkl"):
            return pd.read_pickle(f)
        raise Exception(
            f"Deserialization: file extension {extension} is not supported by Matplotlib Figure type."
        )

    def copy(self, data):
        return data.copy()

    def data_characteristics(self, data):
        return dict(description=f"Matplotlib figure")


MATPLOTLIB_FIGURE_STATE_TYPE = MatplotlibFigureStateType()
register_state_type(plt.Figure, MATPLOTLIB_FIGURE_STATE_TYPE)


@command
def mpl(state, *series):
    """Matplotlib chart"""
    fig = plt.figure(figsize=(8, 6), dpi=300)
    axis = fig.add_subplot(1, 1, 1)
    series = list(reversed(list(series)))
    df = state.get()
    extension = "png"

    while len(series):
        t = series.pop()
        if t in ["jpg", "png", "svg"]:
            extension = t
            continue
        elif t == "xy":
            xcol = series.pop()
            ycol = series.pop()
            state.log_info(f"Chart XY ({xcol} {ycol})")
            axis.plot(df[xcol], df[ycol], label=ycol)
            continue
        elif t == "xye":
            xcol = series.pop()
            ycol = series.pop()
            ecol = series.pop()
            state.log_info(f"Chart XY ({xcol} {ycol}) Error:{ecol}")
            axis.errorbar(df[xcol], df[ycol], yerr=df[ecol], label=ycol)
            continue
        elif t == "xyee":
            xcol = series.pop()
            ycol = series.pop()
            e1col = series.pop()
            e2col = series.pop()
            state.log_info(f"Chart XY ({xcol} {ycol}) Error:({e1col},{e2col})")
            axis.errorbar(df[xcol], df[ycol], yerr=[df[e1col], df[e2col]], label=ycol)
            continue
        elif t == "cxy":
            c = series.pop()
            xcol = series.pop()
            ycol = series.pop()
            axis.plot(df[xcol], df[ycol], c, label=ycol)
            continue
        else:
            state.log_warning(f"Unrecognized MPL parameter {t}")
    # fig.legend()
    output = BytesIO()
    fig.savefig(output, dpi=300, format=extension)
    return state.with_data(output.getvalue()).with_filename(f"image.{extension}")
