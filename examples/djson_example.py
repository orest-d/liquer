# Make it run from the examples directory
import sys
sys.path.append("..")

from liquer import *
from liquer.state_types import decode_state_data
import pandas as pd
import liquer.ext.lq_pandas

@first_command
def test():
    """Creates a dictionary with a DataFrame
    Dictionaries can be serialized to "djson" (decodable json), where complex types (like DataFrame)
    can use their own default encoding converted to base64.
    """
    return dict(hello="world", df=pd.DataFrame(dict(a=[1,2], b=[3,4])))

evaluate_and_save("test/test.djson", target_directory=".")

d = decode_state_data(open("test.djson","rb").read(),"dictionary","djson")
print(d)