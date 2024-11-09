# Make it run from the examples directory
import sys
sys.path.append("..")

from liquer import *
import liquer.ext.lq_pandas
import pandas as pd

from liquer.cache import MemoryCache, FileCache, SQLCache, set_cache  # Setting cache

@first_command(my_cache="a")
def square(count=10):
    df = pd.DataFrame()
    data=[]
    for i in range(count):
        print("square", i)
        data.append(dict(x=i,y=i*i))
    df = pd.concat([df, pd.DataFrame(data)], ignore_index=True)
    return df

@first_command(my_cache="b")
def cube(count=10):
    df = pd.DataFrame()
    data=[]
    for i in range(count):
        print("cube", i)
        data.append(dict(x=i,y=i*i*i))
    df = pd.concat([df,pd.DataFrame(data)], ignore_index=True)
    return df

if __name__ == "__main__":
    set_cache(
        FileCache("cache_a").if_attribute_equal("my_cache","a") + 
        SQLCache.from_sqlite("cache_b.db").if_attribute_equal("my_cache","b") +
        MemoryCache() # Everything else 
    )
    evaluate_and_save("square/square.csv")
    evaluate_and_save("cube/cube.csv")
    evaluate_and_save("square/square.csv") # from cache a
    evaluate_and_save("cube/cube.csv") # from cache b