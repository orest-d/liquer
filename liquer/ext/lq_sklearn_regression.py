from liquer.commands import command, first_command
import pandas as pd
import numpy as np


def label_columns(df):
    return [c for c in df.columns if len(str(c)) and str(c)[0].isupper()]


def feature_columns(df):
    return [c for c in df.columns if len(str(c)) and str(c)[0].islower()]


def default_ycolumn(df):
    ycolumns = label_columns(df)
    if len(ycolumns):
        return ycolumns[-1]
    else:
        return df.columns[-1]


def to_numpy(df):
    try:
        return df.to_numpy()
    except:
        return df.values


@command(ns="sklearn")
def linear_regression(df, ycolumn=None, fit_intercept=True, normalize=False):
    from sklearn.linear_model import LinearRegression

    if ycolumn is None:
        ycolumn = default_ycolumn(df)
    assert ycolumn in df.columns

    xcolumns = feature_columns(df)
    X = to_numpy(df[xcolumns])
    Y = to_numpy(df[ycolumn]).flatten()
    fit = LinearRegression(fit_intercept=fit_intercept, normalize=normalize).fit(X, Y)
    coefficients = list(fit.coef_)
    model_df = pd.DataFrame([coefficients], columns=xcolumns)
    if fit_intercept:
        model_df.loc[:, "intercept"] = fit.intercept_
    return model_df


@command(ns="sklearn")
def ridge(df, alpha=0.1, ycolumn=None, fit_intercept=True, normalize=False):
    from sklearn.linear_model import Ridge

    if ycolumn is None:
        ycolumn = default_ycolumn(df)
    assert ycolumn in df.columns

    xcolumns = feature_columns(df)
    X = to_numpy(df[xcolumns])
    Y = to_numpy(df[ycolumn]).flatten()
    fit = Ridge(alpha=alpha, fit_intercept=fit_intercept, normalize=normalize).fit(X, Y)
    coefficients = list(fit.coef_)
    model_df = pd.DataFrame([coefficients], columns=xcolumns)
    if fit_intercept:
        model_df.loc[:, "intercept"] = fit.intercept_
    return model_df
