"""Module liquer.pool provides functions for running Liquer queries in a multiprocessing pool.
Use *evaluate_in_background* and *evaluate_and_save_in_background* to run Liquer in background
using a pool.

The pool module relies on liquer.config to configure the cache and store.
"""
import multiprocessing as mp
from multiprocessing.managers import BaseManager
from os import getpid
from time import sleep
from liquer.cache import set_cache, CacheProxy, NoCache
from liquer.store import set_store, ProxyStore, Store
from liquer import *
from liquer.constants import *
import logging

logger = logging.getLogger(__name__)
worker_logger = logging.getLogger(__name__ + ".worker")

class SafeProxyStore(ProxyStore):
    """Proxy store that fixes non-picklable results."""
    def keys(self):
        return list(super().keys())

class PoolManager(BaseManager):
    """Multiprocessing manager for the pool.
    Makes available the cache proxy to the pool workers.
    """
    pass


PoolManager.register("CacheProxy", CacheProxy)
PoolManager.register("ProxyStore", SafeProxyStore)

_pool = None


def start_pool(processes=None):
    """Initializes/starts a multiprocessing pool.
    If a pool is not running, this function is called automatically by the *get_pool*,
    thus this does not need to be called by the user.
    """
    global _pool
    _pool = mp.Pool(processes=processes)
    return _pool


def get_pool():
    """Get a configured *multiprocessing* *Pool* object."""
    global _pool
    if mp.current_process().name != "MainProcess":
        raise Exception("Pool should only be accessed from the main process")
    if _pool is None:
        start_pool()
    return _pool


_worker_config = None


def get_cache(worker_config, is_worker=False):
    """Get a configured cache object.
    This is used by the pool workers to get the cache object.
    """
    lg = worker_logger if is_worker else logger
    lg.debug(f"get_cache({worker_config})")

    if worker_config is None:
        lg.warning("worker config missing => No cache")
        return NoCache()
    if "cache" in worker_config:
        cache = worker_config["cache"]
        lg.info(f"Central cache {repr(cache)}")
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
        lg.warning(f"Local cache {repr(cache)}")
        return cache
    else:
        lg.warning(f"Worker confing missging cache description: {worker_config}")
    return NoCache()

def get_store(worker_config, is_worker=False):
    """Get a configured store object.
    This is used by the pool workers to get the store object.
    """
    lg = worker_logger if is_worker else logger
    lg.debug(f"get_store({worker_config})")

    if worker_config is None:
        lg.warning("worker config missing => No store")
        return Store()
    if "store" in worker_config:
        store = worker_config["store"]
        lg.info(f"Central store {repr(store)}")
        return store
    elif "store_constructor" in worker_config:
        f = worker_config["store_constructor"]
        arg = worker_config.get("store_arg", [])
        if arg is None:
            arg = []
        kwarg = worker_config.get("store_kwarg", {})
        if kwarg is None:
            kwarg = {}
        store = f(*arg, **kwarg)
        lg.warning(f"Local store {repr(store)}")
        return store
    else:
        lg.warning(f"Worker confing missging store description: {worker_config}")
    return Store()

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
    if arg is None:
        arg = []
    if kwarg is None:
        kwarg = {}
    cache = constructor(*arg, **kwarg)
    set_cache(cache)

def set_local_store_constructor(constructor, arg=None, kwarg=None):
    """Set the pool store to use a locally constructed store.
    This means that each pool worker will construct its store locally
    applying arguments arg and keyword arguments kwarg to the constructor.
    This is suitable for FileStore (more or less) or a server-based store (e.g. s3 store).

    In general this is a less secure solution. Even for FileStore there might be collisions if multiple workers
    try to access the same file. The set_central_store should be a safe alternative.
    """
    global _worker_config
    if _worker_config is None:
        _worker_config = {}
    _worker_config.update(
        dict(store_constructor=constructor, store_arg=arg, store_kwarg=kwarg)
    )
    if arg is None:
        arg = []
    if kwarg is None:
        kwarg = {}
    store = constructor(*arg, **kwarg)
    set_store(store)


def set_central_cache(cache, manager=None, use_cache_proxy_locally=True):
    """Set the pool cache to use a cache object.
    The cache object lives in a single process, which is then accessed from workers using IPC.
    This is suitable for all types of cache objects, particularly it is important for a MemoryCache.

    Limitations:
    - The cached objects have to support pickle.
    - Large objects may fail to transfer between processes due to limitations of IPC buffer (see https://docs.python.org/3/library/multiprocessing.html#connection-objects)
    - Large objects may be slow to transfer between processes.

    In general this is a more secure solution, but it requires all data to support pickle.
    It has to be noted that the cache lives in a single process and relies on IPC to work, thus this solution
    may possibly be outperformed by set_local_cache_constructor.

    PoolManager instance can be provided via manager. If None, PoolManager will be created and started.
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

def set_central_store(store, manager=None, use_store_proxy_locally=True):
    """Set the pool store to use a store object.
    The store object lives in a single process, which is then accessed from workers using IPC.
    This is suitable for all types of store objects.

    Limitations:
    - The stored objects have to support pickle.
    - Large objects may fail to transfer between processes due to limitations of IPC buffer (see https://docs.python.org/3/library/multiprocessing.html#connection-objects)
    - Large objects may be slow to transfer between processes.
    
    In general this is a more secure solution, but it requires all data to support pickle.
    It has to be noted that the store lives in a single process and relies on IPC to work, thus this solution
    may possibly be outperformed by set_local_store_constructor.

    PoolManager instance can be provided via manager. If None, PoolManager will be created and started.
    The manager instance is returned.

    The use_store_proxy_locally controls if store is proxied when used locally (which should be the safe choice).
    """
    global _worker_config
    if manager is None:
        manager = PoolManager()
        manager.start()
    if _worker_config is None:
        _worker_config = {}
    store_proxy = manager.ProxyStore(store)
    _worker_config.update(dict(store=store_proxy))
    if use_store_proxy_locally:
        set_store(store_proxy)
    else:
        set_store(store)
    return manager


def _evaluate_worker(query, worker_config):
    """Internal function called by the worker to evaluate a query."""    
    worker_logger.info(f"Evaluate worker started for {query}")
    set_cache(get_cache(worker_config, is_worker=True))
    worker_logger.debug(f"Cache configured for {query}")
    set_store(get_store(worker_config, is_worker=True))
    worker_logger.debug(f"Store configured for {query}")
    evaluate(query)
    worker_logger.info(f"Evaluate worker finished for {query}")
    return f"Done evaluating {query}"


def _evaluate_and_save_worker(query, target_directory, target_file, worker_config):
    """Internal function called by the worker to evaluate and save a query."""    
    worker_logger.info(f"Evaluate and save worker started for {query}")
    set_cache(get_cache(worker_config, is_worker=True))
    worker_logger.debug(f"Cache configured for {query}")
    set_store(get_store(worker_config, is_worker=True))
    worker_logger.debug(f"Store configured for {query}")
    evaluate_and_save(query, target_directory=target_directory, target_file=target_file)
    worker_logger.info(f"Evaluate and save worker finished for {query}")
    return f"Done evaluate and save {query}"


def evaluate_in_background(query):
    """Like evaluate, but returns immediately and runs in the background.
    This creates immediately a submitted state in the cache,
    which is replaced by a resulting state once available.    

    If there is no metadata associated with the query after calling this function,
    then either there is no cache or the resulting state is volatile.
    This can be used by GUI to identify situations when waiting for the result to appear
    in the cache is not a viable strategy, but requesting the object directly is necessary.
    """
    global _worker_config
    print(f"Evaluate {query} in background")
    metadata = get_context().metadata()
    metadata["query"] = query
    metadata["status"] = Status.SUBMITTED.value
    cache = get_cache(_worker_config)
    cache.store_metadata(metadata)

    if _worker_config is None:
        logger.warning("Evaluated in main process")
        logger.warning(
            "Please configure the cache using set_local_cache_constructor or set_central_cache"
        )
        return evaluate(query)
    else:
        return get_pool().apply_async(
            _evaluate_worker, [query, _worker_config], callback=logger.info
        )


def evaluate_and_save_in_background(query, target_directory=None, target_file=None):
    """Like evaluate_and_save, but returns immediately and runs in the background.
    Note that the saving occurs on o worker. Eventual remote workers will save the results in their local filesystem.
    """
    global _worker_config
    logger.info(f"Evaluate and save {query} in background")
    if _worker_config is None:
        logger.warning("Evaluated in main process")
        logger.warning(
            "Please configure the cache using set_local_cache_constructor or set_central_cache"
        )
        return evaluate_and_save(
            query, target_directory=target_directory, target_file=target_file
        )
    return get_pool().apply_async(
        _evaluate_and_save_worker,
        [query, target_directory, target_file, _worker_config],
        callback=logger.info,
    )
