"""
Handle global configuration.
Configuration is stored in a dictionary, which is accessible as *liquer.config.config()*.
The dictionary is initialized with default values.
FUnction *load_config* loads configuration from a file.
"""

from pathlib import Path
import yaml
import logging

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

logger = logging.getLogger(__name__)

_config = None


def config():
    """Return the config dictionary"""
    global _config
    if _config is None:
        _config = dict(setup=dict(preset="liquer.config.RichPreset"))
    return _config


def load_config(filename):
    """Load configuration from a file"""
    global _config
    if _config is None:
        _config = config()
    try:
        with open(filename, "r") as f:
            new_config = yaml.load(f, Loader=Loader)
            _config.update(new_config)
    except FileNotFoundError:
        print(f"Configuration file {filename} not found")
        print("Create a default configuration file with:")
        print()
        print("python -m liquer.app --create-config config.yaml")
        print()
    logger.info(f"Configuration loaded from {filename}")


_initializer = None


def initializer():
    """Return the initializer function"""
    global _initializer

    def __initializer(config, worker_environment=False):
        preset().initialize(config, worker_environment=worker_environment)

    if _initializer is None:
        _initializer = __initializer
    return _initializer


def set_initializer(f):
    """Set the initializer function.
    Initializer is a function taking the configuration dictionary and a boolean flag
    indicating whether the function is called in a worker process.
    By default, it is a function calling the preset initializer.

    """
    global _initializer
    _initializer = f


def initialize(worker_environment=False):
    """Initialize the configuration
    This function is called automatically when the configuration is loaded.
    *worker_environment* is True if the function is called in a worker process.
    """
    initializer()(config(), worker_environment=worker_environment)


_preset = None


def preset():
    """Return the preset object"""
    global _preset
    if _preset is None:
        set_preset()
    return _preset


async def run_tornado(port=5000, index_link="index"):
    from liquer.server.tornado_handlers import url_mapping
    from liquer.server.handlers import response
    import tornado.web
    import asyncio
    import traceback
    from liquer.query import evaluate

    class IndexHandler(tornado.web.RequestHandler):
        def get(self):
            self.redirect(index_link)

    application = tornado.web.Application(
        url_mapping()
        + [
            (r"/", IndexHandler),
            (r"/index.html", IndexHandler),
        ]
    )

    application.listen(port)
    await asyncio.Event().wait()


class Preset(object):
    """A preset is a configuration object, which can be used to initialize liquer.
    It's role is to
    * interpret the configuration file
    * initialize commands
    * initialize caches
    * initialize store

    It as well can create default configuration files,
    initialize and start the pool, server and other services
    """

    modules = []

    def __init__(self):
        pass

    @classmethod
    def preset_class(cls):
        """Return the preset class name"""
        x = ""
        if cls.__module__ != "__main__":
            x += cls.__module__
            x += "."
        x += cls.__name__
        return x

    def _find_modules(self, path):
        """Find modules in a path containing LiQuer commands"""
        from glob import glob
        import os

        for filename in glob(os.path.join(path, "*.py")):
            with open(filename, "r") as f:
                mod = f.read()
                if "@command" in mod or "@first_command" in mod:
                    yield os.path.splitext(os.path.basename(filename))[0]

    def find_modules(self, path):
        """Find modules in a path containing LiQuer commands"""
        import os

        for root, dirs, files in os.walk(path):
            rootpath = os.path.relpath(root, path)
            module = rootpath.replace(os.path.sep, ".")
            while module.startswith("."):
                module = module[1:]

            for file in files:
                if (
                    file.endswith(".py")
                    and not file.startswith("_")
                    and not file.startswith("test_")
                ):
                    with open(os.path.join(root, file), "r") as f:
                        mod = f.read()
                        if "@command" in mod or "@first_command" in mod:
                            x = module + "." + os.path.splitext(file)[0]
                            print(x, "found in", root)
                            self.modules.append(x)
        return self.modules

    def default_config(self):
        """Return a default configuration file in yaml format"""
        modules = sorted(set(self.modules + ["liquer.ext.meta", "liquer.ext.basic"]))
        modules_list = "\n".join([f"      - {m}" for m in modules])
        return f"""
setup:
    preset:            {self.preset_class():<35} # Preset class name
    modules:           {"":<35} # Modules with commands to import
{modules_list}
    cache:             {"off":<35} # Cache type (off, memory, file, ...)
    cache_path:        {"cache":<35} # Cache path (for file cache)
    cache_concurrency: {"central":<35} # Cache concurrency (off, local, central)
    recipe_folders:    {"[]":<35} # Recipe folders

    server_type:       {"flask":<35} # Server type (flask, tornado, FastAPI ...)
    url_prefix:        {'"/liquer"':<35} # URL prefix for the server
    port:              {5000:<35} # Server port
    index_link:        {"/liquer/q/index/index.html":<35} # Index query
"""

    def initialize(self, config, worker_environment=False):
        """Initialize from configuration.
        If worker_environment is True, then initialize specifically the worker environment,
        i.e. the worker pool should not be initialized.
        """
        self.load_modules(config)
        self.initialize_cache(config)
        self.initialize_store(config)
        if not worker_environment:
            self.initialize_pool(config)

    @classmethod
    def get_setup_parameter(cls, config, name, default=None):
        """Helper method to get a parameter from the setup section of the configuration"""
        if "setup" not in config:
            raise Exception("No setup section in configuration")
        return config["setup"].get(name, default)

    def load_modules(self, config):
        """Load modules scpecified in the configuration
        List of modules is taken from config["setup"]["modules"]
        """
        for module in self.get_setup_parameter(config, "modules", self.modules):
            logger.info(f"Loading module {module}")
            __import__(module, fromlist=["*"])

    def create_cache(self, config):
        "Create cache object from configuration"
        import liquer.cache

        cache = self.get_setup_parameter(config, "cache", "off")
        if cache in ["off", "none", "no", None, False]:
            logger.info(f"Cache disabled")
            return liquer.cache.NoCache()
        elif cache in ["memory"]:
            logger.info(f"Enabling memory cache")
            return liquer.cache.MemoryCache()
        elif cache in ["file"]:
            path = self.get_setup_parameter(config, "cache_path", "cache")
            logger.info(f"Enabling file cache in {path}")
            return liquer.cache.FileCache(path)
        else:
            raise Exception(f"Unknown cache type {cache}")

    def create_store(self, config):
        "Create store object from configuration"
        import liquer.store

        self.initialize_store(config)
        return liquer.store.get_store() # TODO: make a proper store construction


    def initialize_cache(self, config):
        """Initialize cache from configuration"""
        import liquer.cache

        liquer.cache.set_cache(self.create_cache(config))

    def initialize_store(self, config):
        """Initialize store from configuration"""
        import liquer.store
        from liquer.recipes import RecipeSpecStore
        from pathlib import Path

        liquer.store.get_web_store()
        recipe_folders = self.get_setup_parameter(config, "recipe_folders", [])
        for folder_name in recipe_folders:
            logger.info(f"Adding recipe folder {folder_name}")
            p=Path(folder_name)
            if not p.exists():
                print(f"Creating folder {folder_name}")
                p.mkdir(parents=True)
            s = RecipeSpecStore(liquer.store.FileStore(folder_name)).with_indexer()
            liquer.store.mount(folder_name, s)

    def initialize_pool(self, config):
        """Initialize pool from configuration"""
        import liquer.pool
        import liquer.cache
        import liquer.store

        cache_concurrency = self.get_setup_parameter(config, "cache_concurrency")
        if cache_concurrency in ["off", "none", "no", None, False]:
            logger.info(f"Cache not configured for concurrency")
            logger.warning(f"Distributed execution will not work properly")
        elif cache_concurrency == "central":
            logger.info(f"Enabling central cache")
            liquer.pool.set_central_cache(liquer.cache.get_cache())
        elif cache_concurrency == "local":
            logger.info(f"Enabling worker-local cache")
            liquer.pool.set_local_cache_constructor(self.create_cache, arg=[config])
        else:
            raise Exception(f"Unknown cache concurrency setting: {cache_concurrency}")

        store_concurrency = self.get_setup_parameter(config, "cache_concurrency")
        if store_concurrency in ["off", "none", "no", None, False]:
            logger.info(f"Store not configured for concurrency")
            logger.warning(f"Distributed execution will not work properly")
        elif store_concurrency == "central":
            logger.info(f"Enabling central store")
            liquer.pool.set_central_store(liquer.store.get_store())
        elif cache_concurrency == "local":
            logger.info(f"Enabling worker-local store")
            liquer.pool.set_local_store_constructor(self.create_store, arg=[config])
        else:
            raise Exception(f"Unknown store concurrency setting: {store_concurrency}")

    def start_server(self, config):
        """Start server from configuration"""
        from liquer.state import set_var
        from liquer.query import evaluate

        server_type = self.get_setup_parameter(config, "server_type", "flask")
        if server_type in ["flask"]:
            logger.info(f"Starting flask server")
            import flask
            import liquer.server.blueprint as bp
            import traceback

            app = flask.Flask(__name__)
            url_prefix = self.get_setup_parameter(config, "url_prefix", "/liquer")
            port = self.get_setup_parameter(config, "port", "5000")
            flask_debug = self.get_setup_parameter(config, "debug", False)
            host = self.get_setup_parameter(config, "host", "127.0.0.1")
            flask_threaded = self.get_setup_parameter(config, "threaded", False)
            index_link = self.get_setup_parameter(config, "index_link", "/liquer/q/index/index.html")
            print(f"Index link: {index_link}")

            app.register_blueprint(bp.app, url_prefix=url_prefix)

            @app.route("/")
            @app.route("/index.html")
            def index():
                print(f"Redirect to index link: {index_link}")
                return flask.redirect(index_link, code=302)

            set_var("api_path", url_prefix + "/q/")
            set_var("server", f"http://{host}:{port}")
            app.run(debug=flask_debug, host=host, port=port, threaded=flask_threaded)
        elif server_type in ["tornado"]:
            import asyncio

            logger.info(f"Starting tornado server")
            port = self.get_setup_parameter(config, "port", "5000")
            url_prefix = self.get_setup_parameter(config, "url_prefix", "/liquer")
            index_link = self.get_setup_parameter(config, "index_link", "/liquer/q/index/index.html")
            host = self.get_setup_parameter(config, "host", "127.0.0.1")
            set_var("api_path", url_prefix + "/q/")
            set_var("server", f"http://{host}:{port}")
            asyncio.run(run_tornado(port, index_link=index_link))
        elif server_type.lower() in ["fastapi"]:
            import uvicorn
            import liquer.server.fastapi as fa
            import fastapi
            import fastapi.responses

            app = fastapi.FastAPI()
            @app.middleware("http")
            async def add_coi_header(request: fastapi.Request, call_next):
                response = await call_next(request)
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
                response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'

                return response

            logger.info(f"Starting fastapi server")
            port = self.get_setup_parameter(config, "port", "5000")
            url_prefix = self.get_setup_parameter(config, "url_prefix", "/liquer")
            index_link = self.get_setup_parameter(config, "index_link", "/liquer/q/index/index.html")
            host = self.get_setup_parameter(config, "host", "127.0.0.1")

            @app.get('/')
            def index():
                return fastapi.responses.RedirectResponse(url=index_link)

            set_var("api_path", url_prefix + "/q/")
            set_var("server", f"http://{host}:{port}")

            app.include_router(fa.router, prefix=url_prefix)
            uvicorn.run(app, host=host, port=int(port))
        else:
            raise Exception(f"Unknown server type: {server_type}")


class RichPreset(Preset):
    modules = [
        "liquer.ext.dataframe_batches",
        "liquer.ext.lq_matplotlib",
        "liquer.ext.lq_openpyxl",
        "liquer.ext.lq_pandas",
        "liquer.ext.lq_pil",
        "liquer.ext.lq_plotly",
        "liquer.ext.lq_polars",
        "liquer.ext.lq_pygments",
        "liquer.ext.lq_python",
        "liquer.ext.lq_sweetviz",
        "liquer.ext.basic",
        "liquer.ext.meta",
        "liquer_pcv",
        "liquer_gui"
    ]
    def default_config(self):
        """Return a default configuration file in yaml format"""
        modules = sorted(set(self.modules + ["liquer.ext.meta", "liquer.ext.basic"]))
        modules_list = "\n".join([f"      - {m}" for m in modules])
        recipe_folders ="\n".join (f"      - {m}" for m in ["data", "reports"])
        return f"""
setup:
    preset:            {self.preset_class():<35} # Preset class name
    modules:           {"":<35} # Modules with commands to import
{modules_list}
    cache:             {"off":<35} # Cache type (off, memory, file, ...)
    cache_path:        {"cache":<35} # Cache path (for file cache)
    cache_concurrency: {"central":<35} # Cache concurrency (off, local, central)
    store_concurrency: {"central":<35} # Store concurrency (off, local, central)
    recipe_folders:    {"":<35} # Recipe folders
{recipe_folders}
    server_type:       {"flask":<35} # Server type (flask, tornado, FastAPI ...)
    url_prefix:        {'"/liquer"':<35} # URL prefix for the server
    port:              {5000:<35} # Server port
    index_query:       {"/liquer/web/gui":<35} # Index query
"""
    @classmethod
    def get_setup_parameter(cls, config, name, default=None):
        """Helper method to get a parameter from the setup section of the configuration"""
        if "setup" not in config:
            raise Exception("No setup section in configuration")
        if name == "index_link":
            return config["setup"].get("index_link", "/liquer/web/gui")
        if name == "recipe_folders":
            return config["setup"].get("recipe_folders", ["data", "reports"])
        if name == "cache_concurrency":
            return config["setup"].get("cache_concurrency", "central")
        if name == "store_concurrency":
            return config["setup"].get("store_concurrency", "central")
        return config["setup"].get(name, default)

def set_preset(preset_def=None):
    """Set the preset object
    Preset can either be a preset object (instance of Preset class), a preset class name (string) or configuration (dictionary).
    If preset is None, preset is loaded based on the configuration file.
    """
    import liquer.util

    global _preset
    if preset_def is None:
        preset_def = config()
    if isinstance(preset_def, dict):
        if "setup" not in preset_def:
            raise Exception("No setup section in configuration")
        if "preset" not in preset_def["setup"]:
            raise Exception("No preset specified in the setup section in configuration")
        preset_def = preset_def["setup"]["preset"]
        if not isinstance(preset_def, str):
            raise Exception("Preset must be a fully qualified class name")
    if isinstance(preset_def, str):
        logger.info(f"Instantiating preset {preset_def}")
        preset_def = liquer.util.eval_fully_qualified_name(preset_def)()
    if isinstance(preset_def, Preset):
        logger.info(f"Instantance of {preset_def.preset_class()} used as preset")
        _preset = preset_def
    else:
        raise Exception(f"Unknown preset type {repr(preset_def)}")
