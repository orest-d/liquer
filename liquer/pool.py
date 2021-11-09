import multiprocessing as mp
from multiprocessing.managers import BaseManager
from os import getpid
from time import sleep
from liquer.cache import set_cache, CacheProxy, NoCache
from liquer import *
from liquer.constants import *

class PoolManager(BaseManager):
    pass


PoolManager.register("CacheProxy", CacheProxy)

_pool = None


def start_pool(processes=None):
    global _pool
    _pool = mp.Pool(processes=processes)
    return _pool


def get_pool():
    global _pool
    if mp.current_process().name != "MainProcess":
        raise Exception("Pool should only be accessed from the main process")
    if _pool is None:
        start_pool()
    return _pool


_worker_config = None


def get_cache(worker_config):
    print(f"get_cache({worker_config})")
    if worker_config is None:
        print("worker config missing => No cache")
        return NoCache()
    if "cache" in worker_config:
        cache = worker_config["cache"]
        print(f"Central cache {repr(cache)}")
        return cache
    elif "cache_constructor" in worker_config:
        f = worker_config["cache_constructor"]
        arg = worker_config.get("cache_arg", [])
        if arg is None:
            arg = []
        kwarg = worker_config.get("cache_kwarg", {})
        if kwarg is None:
            kwarg = {}
        cache = f(*arg, **kwarg)
        print(f"Local cache {repr(cache)}")
        return cache
    else:
        print(f"Worker confing missging cache description: {worker_config}")
    return NoCache()


def set_local_cache_constructor(constructor, arg=None, kwarg=None):
    """Set the pool cache to use a locally constructed cache.
    This means that each pool worker will construct its cache locally
    applying arguments arg and keyword arguments kwarg to the constructor.
    This is suitable for FileCache (more or less) or a server-based cache (e.g. SQLCache with a database server),
    but it is not suitable for MemoryCache, since each worker will have its own memory cache and thus the cache will not be shared.

    In general this is a less secure solution. Even for FileCache there might be collisions if multiple workers
    try to access the same file. The set_central_cache should be a safe alternative.
    """
    global _worker_config
    if _worker_config is None:
        _worker_config = {}
    _worker_config.update(
        dict(cache_constructor=constructor, cache_arg=arg, cache_kwarg=kwarg)
    )
    cache = constructor(*arg, **kwarg)
    set_cache(cache)


def set_central_cache(cache, manager=None, use_cache_proxy_locally=True):
    """Set the pool cache to use a cache object.
    The cache object lives in a single process, which is then accessed from workers using IPC.
    This is suitable for all types of cache objects, particularly it is important for a MemoryCache.

    In general this is a more secure solution, but it requires all data to support pickle.
    It has to be noted that the cache lives in a single process and relies on IPC to work, thus this solution
    may possibly be outperformed by set_local_cache_constructor.

    PoolManager instance can be provided via manager. If None, PollManager will be created and started.
    The manager instance is returned.

    The use_cache_proxy_locally controls if cache is proxied when used locally (which should be the safe choice).
    """
    global _worker_config
    if manager is None:
        manager = PoolManager()
        manager.start()
    if _worker_config is None:
        _worker_config = {}
    cache_proxy = manager.CacheProxy(cache)
    _worker_config.update(dict(cache=cache_proxy))
    if use_cache_proxy_locally:
        set_cache(cache_proxy)
    else:
        set_cache(cache)
    return manager


def _evaluate_worker(query, worker_config):
    print(f"Evaluate worker started for {query}")
    set_cache(get_cache(worker_config))
    evaluate(query)
    return f"Done evaluating {query}"


def _evaluate_and_save_worker(query, target_directory, target_file, worker_config):
    print(f"Evaluate and save worker started for {query}")
    set_cache(get_cache(worker_config))
    evaluate_and_save(query, target_directory=target_directory, target_file=target_file)
    return f"Done evaluate and save {query}"


def evaluate_in_background(query):
    """Like evaluate, but returns immediately and runs in the background.
    Note that this creates immediately a submitted state in the cache.

    If there is no metadata associated with the query after calling this function,
    then either there is no cache or the resulting state is volatile.
    This can be used by GUI to identify situations when waiting for the result to appear
    in the cache is not a viable strategy, but requesting the object directly is necessary.
    """
    global _worker_config
    print(f"Evaluate {query} in background")
    metadata = get_context().metadata()
    metadata["query"]=query
    metadata["status"]=Status.SUBMITTED.value
    cache = get_cache(_worker_config)
    cache.store_metadata(metadata)

    if _worker_config is None:
        print("WARNING: Evaluated in main process")
        print(
            "         Please configure the cache using set_local_cache_constructor or set_central_cache"
        )
        return evaluate(query)
    else:
        return get_pool().apply_async(
            _evaluate_worker, [query, _worker_config], callback=print
        )


def evaluate_and_save_in_background(query, target_directory=None, target_file=None):
    """Like evaluate_and_save, but returns immediately and runs in the background.
    Note that the saving occurs on o worker. Eventual remote workers will save the results in their local filesystem.
    """
    global _worker_config
    print(f"Evaluate and save {query} in background")
    if _worker_config is None:
        print("WARNING: Evaluated in main process")
        print(
            "         Please configure the cache using set_local_cache_constructor or set_central_cache"
        )
        return evaluate_and_save(
            query, target_directory=target_directory, target_file=target_file
        )
    return get_pool().apply_async(
        _evaluate_and_save_worker,
        [query, target_directory, target_file, _worker_config],
        callback=print,
    )
