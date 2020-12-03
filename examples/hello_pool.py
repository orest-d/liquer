# Make it run from the examples directory
import sys
sys.path.append("..")

from liquer import *
from liquer.pool import set_central_cache, evaluate_and_save_in_background, get_pool
from liquer.cache import MemoryCache
from time import sleep

@first_command
def hello():
    sleep(0.5)
    return "Hello"

@command
def greet(greeting, who="world"):
    sleep(0.5)
    return f"{greeting}, {who}!"

if __name__=="__main__":
    set_central_cache(MemoryCache())

#    evaluate_and_save("hello/greet/hello_greet.txt")
#    evaluate_and_save("hello/greet-everybody/hello_greet_everybody.txt")

    evaluate_and_save_in_background("hello/greet/hello_greet.txt")
    evaluate_and_save_in_background("hello/greet-everybody/hello_greet_everybody.txt")

    get_pool().close()
    get_pool().join()

