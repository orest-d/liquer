from io import BytesIO

from liquer.commands import command
from liquer.state_types import StateType, register_state_type
from liquer.constants import mimetype_from_extension

import PIL

class PILImageStateType(StateType):
    def identifier(self):
        return "image"

    def default_extension(self):
        return "png"

    def is_type_of(self, data):
        return isinstance(data, PIL.Image.Image)

    def format_from_extension(self, extension):
        if extension is None:
            extension = self.default_extension()
        if extension.lower() in ("bmp", "eps", "jpeg", "pcx", "png", "ppm", "tga", "tiff", "xbm", "ico", "gif"):
            return extension.upper(), True, True
        if extension.lower() == "jpg":
            return "JPEG", True, True
        if extension.lower() in ("pcd", "psd", "wmf"):
            return extension.upper(), True, False
        if extension.lower() == "pdf":
            return extension.upper(), False, True

    def as_bytes(self, data, extension=None):
        if extension is None:
            extension = self.default_extension()
        assert self.is_type_of(data)
        mimetype = mimetype_from_extension(extension)
        format_name, can_read, can_write = self.format_from_extension(extension)
        if can_write: 
            output = BytesIO()
            data.save(output, format=format_name)
            return output.getvalue(), mimetype
        else:
            if can_read:
                raise Exception(
                    f"Serialization: PIL Image only supports reading, but not writing for file extension {extension}."
                )
            else:
                raise Exception(
                    f"Serialization: file extension {extension} is not supported by PIL Image."
                )

    def from_bytes(self, b: bytes, extension=None):
        format_name, can_read, can_write = self.format_from_extension(extension)
        if extension is None:
            formats=None
        else:
            formats=[format_name]

        if can_read:
            f = BytesIO()
            f.write(b)
            f.seek(0)
            return PIL.Image.open(f, formats=formats)
        else:
            if can_write:
                raise Exception(
                    f"Deserialization: PIL Image only supports writing, but not reading for file extension {extension}."
                )
            else:
                raise Exception(
                    f"Deserialization: file extension {extension} is not supported by PIL Image type."
                )

    def copy(self, data):
        return data.copy()

    def data_characteristics(self, data):
        width, height = data.size
        return dict(description=f"Image {width}x{height}")


PIL_IMAGE_STATE_TYPE = PILImageStateType()
register_state_type(PIL.Image.Image, PIL_IMAGE_STATE_TYPE)


@command(ns="pil")
def resize(image, width, height, resample=None):
    """Resize image"""
    resample = dict(
        nearest=PIL.Image.NEAREST,
        box=PIL.Image.BOX,
        bilinear=PIL.Image.BILINEAR,
        hamming=PIL.Image.HAMMING,
        bicubic=PIL.Image.BICUBIC,
        lanczos=PIL.Image.LANCZOS,
    ).get(str(resample).lower())     
    
    return image.copy().resize((int(width), int(height)), resample=resample)
