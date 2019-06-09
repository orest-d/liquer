# Make it run from the examples directory
import sys
sys.path.append("..")

from liquer import *
from liquer.parser import encode, encode_token
import liquer.ext.lq_pandas

url = "https://raw.githubusercontent.com/orest-d/liquer/master/tests/test.csv"

query = encode([["df_from",url]])
print (f"Query: {query}")
print (evaluate(query).get())

query = "df_from-"+encode_token(url)
print (f"Query: {query}")
print (evaluate(query).get())

query = f"{query}/eq-a-3"
print (f"Query: {query}")
print (evaluate(query).get())
