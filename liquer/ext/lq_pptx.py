import pptx
from io import BytesIO
import pandas as pd
from liquer.state_types import StateType, register_state_type
from liquer.constants import mimetype_from_extension

from liquer.commands import command, first_command
from tempfile import TemporaryDirectory
from pathlib import Path
from liquer.context import get_context
class ResilientBytesIO(BytesIO):
    "Workaround to prevent closing the stream"

    def close(self):
        pass  # Refuse to close to avoid pandas bug

    def really_close(self):
        super().close()

class PPTXPresentationStateType(StateType):
    def identifier(self):
        return "pptx_presentation"

    def default_extension(self):
        return "pptx"

    def is_type_of(self, data):
        if isinstance(data, pptx.presentation.Presentation):
            return True
        return False

    def as_bytes(self, data, extension=None):
        if extension is None:
            extension = self.default_extension()
        assert self.is_type_of(data)
        mimetype = mimetype_from_extension(extension)

        if extension == "pptx":
            output = ResilientBytesIO()
            data.save(output)
            b = output.getvalue()
            output.really_close()
            return b, mimetype
        else:
            raise Exception(
                f"Serialization: file extension {extension} is not supported by pptx Presentation type."
            )

    def from_bytes(self, b: bytes, extension=None):
        if extension is None:
            extension = self.default_extension()
        f = BytesIO()
        f.write(b)
        f.seek(0)
        if extension == "pptx":
            return pptx.Presentation(f)
        raise Exception(
            f"Deserialization: file extension {extension} is not supported by pptx Presentation type."
        )

    def copy(self, data):
        return self.from_bytes(self.as_bytes(data)[0])

    def data_characteristics(self, data):
        return dict(description=f"Presentation (pptx) with {len(data.slides)} slides.")
        

PPTX_PRESENTATION_STATE_TYPE = PPTXPresentationStateType()
register_state_type(pptx.Presentation, PPTX_PRESENTATION_STATE_TYPE)
register_state_type(pptx.presentation.Presentation, PPTX_PRESENTATION_STATE_TYPE)
