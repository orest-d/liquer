from io import StringIO, BytesIO
from urllib.request import urlopen
from tempfile import NamedTemporaryFile

from keras.models import Model, model_from_json, model_from_yaml, load_model, clone_model
from keras.utils import plot_model, print_summary

from liquer.state_types import StateType, register_state_type, mimetype_from_extension
from liquer.commands import command, first_command
from liquer.parser import encode, decode
from liquer.query import evaluate
from liquer.state import State

class KerasModelStateType(StateType):
    def identifier(self):
        return "kerasmodel"

    def default_extension(self):
        return "h5"

    def is_type_of(self, data):
        return isinstance(data, Model)

    def as_bytes(self, data, extension=None):
        if extension is None:
            extension = self.default_extension()
        assert self.is_type_of(data)
        mimetype = mimetype_from_extension(extension)
        if extension == "json":
            output = StringIO()
            output.write(data.to_json())
            return output.getvalue().encode("utf-8"), mimetype
        elif extension == "yaml":
            output = StringIO()
            output.write(data.to_yaml())
            return output.getvalue().encode("utf-8"), mimetype
        elif extension in ("h5", "hdf5"):
            with NamedTemporaryFile(prefix="keras_model_",suffix="."+extension) as f:
                data.save(f.name)            
                b = open(f.name,"rb").read()
            return b, mimetype
        else:
            raise Exception(
                f"Serialization: file extension {extension} is not supported by kerasmodel type.")

    def from_bytes(self, b: bytes, extension=None):
        if extension is None:
            extension = self.default_extension()

        if extension == "json":
            return model_from_json(b)
        elif extension == "yaml":
            return model_from_yaml(b)
        elif extension in ["h5", "hdf5"]:
            with NamedTemporaryFile(prefix="keras_model_",suffix="."+extension) as f:
                f.write(b)
                return load_model(f.name)
        raise Exception(
            f"Deserialization: file extension {extension} is not supported by kerasmodel type.")

    def copy(self, data):
        model = clone_model(data)
        model.set_weights(data.get_weights())
        return model


KERASMODEL_STATE_TYPE = KerasModelStateType()
register_state_type(Model, KERASMODEL_STATE_TYPE)

@command
def keras_plot_model(model, show_shapes=False, show_layer_names=True, rankdir='TB', expand_nested=False, dpi=96):
    "Keras plot model as png"
    assert isinstance(model, Model)
    with NamedTemporaryFile(prefix="keras_model_",suffix=".png") as f:
        plot_model(model, to_file=f.name, show_shapes=show_shapes, show_layer_names=show_layer_names, rankdir=rankdir, expand_nested=expand_nested, dpi=96)
        b = open(f.name,"rb").read()
    return b

@command
def keras_summary(model):
    "Keras model summary"
    s = StringIO()
    print_summary(model, print_fn=lambda x,s=s:s.write(str(x)+"\n") )
    return s.getvalue()