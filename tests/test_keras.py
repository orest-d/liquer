#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Unit tests for LiQuer pandas support.
"""
from liquer import *
from keras.models import Model
from keras.layers import Input, Dense
from os import remove


class TestKeras:
    def test_model(self):
        import liquer.ext.lq_keras  # register keras commands and state type

        @first_command(modify_command=True)
        def model():
            a = Input(shape=(32,))
            b = Dense(32)(a)
            model = Model(inputs=a, outputs=b)
            model.compile(loss="mean_squared_error", optimizer="sgd")
            return model

        evaluate_and_save("model/model.h5")
        model = liquer.ext.lq_keras.KERASMODEL_STATE_TYPE.from_bytes(
            open("model.h5", "rb").read()
        )
        remove("model.h5")
        assert isinstance(model, Model)

    def test_plot_model(self):
        import liquer.ext.lq_keras  # register keras commands and state type

        @first_command(modify_command=True)
        def model():
            a = Input(shape=(32,))
            b = Dense(32)(a)
            model = Model(inputs=a, outputs=b)
            model.compile(loss="mean_squared_error", optimizer="sgd")
            return model

        evaluate_and_save("model/keras_plot_model/model.png")
        remove("model.png")

    def test_summary(self):
        import liquer.ext.lq_keras  # register keras commands and state type

        @first_command(modify_command=True)
        def model():
            a = Input(shape=(32,))
            b = Dense(32)(a)
            model = Model(inputs=a, outputs=b)
            model.compile(loss="mean_squared_error", optimizer="sgd")
            return model

        assert "1056" in evaluate("model/keras_summary").get()
