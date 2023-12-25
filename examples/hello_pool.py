# Make it run from the examples directory
import sys
sys.path.append("..")

from liquer import *
from liquer.pool import set_central_cache, evaluate_and_save_in_background, get_pool
from liquer.cache import MemoryCache
from time import sleep

### Optional: setup logging
import logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(name)s %(message)s")

@first_command
def hello():
    print("hello 1")
    sleep(0.5)
    print("hello 2")
    return "Hello"

@command
def greet(greeting, who="world"):
    print(f"greet 1 {greeting} {who}")
    sleep(0.5)
    print(f"greet 2 {greeting} {who}")
    return f"{greeting}, {who}!"

if __name__=="__main__":
    set_central_cache(MemoryCache()) # without configuring cache, the evaluation will run in the main process

#    evaluate_and_save("hello/greet/hello_greet.txt", target_directory=".")
#    evaluate_and_save("hello/greet-everybody/hello_greet_everybody.txt", target_directory=".")

    evaluate_and_save_in_background("hello/greet/hello_greet.txt")
    evaluate_and_save_in_background("hello/greet-everybody/hello_greet_everybody.txt")

    get_pool().close()
    get_pool().join()

