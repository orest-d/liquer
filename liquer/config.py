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
        _config = dict(setup=dict(preset="liquer.config.Preset"))
    return _config

def load_config(filename):
    """Load configuration from a file"""
    global _config
    if _config is None:
        _config = {}
    with open(filename, "r") as f:
        new_config = yaml.load(f, Loader=Loader)
    _config.update(new_config)
    logger.info(f"Configuration loaded from {filename}")

_initializer = None

def initializer():
    """Return the initializer function"""
    global _initializer
    if _initializer is None:
        _initializer = lambda config, worker_environment=False: preset().initialize(config, worker_environment=worker_environment)
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

async def run_tornado(port=5000, index_query="index"):
    from liquer.server.tornado_handlers import url_mapping, response
    import tornado.web
    import asyncio
    import traceback
    from liquer.query import evaluate

    class IndexHandler(tornado.web.RequestHandler):
        def prepare(self):
            header = "Content-Type"
            body = "text/html"
            self.set_header(header, body)
        def get(self):
            try:
                b, mimetype, filename = response(evaluate(index_query))
                self.write(b)
            except:
                traceback.print_exc()
                self.set_status(500)
                self.finish(f"500 - Failed to create a response to {index_query}")
                return

    application = tornado.web.Application(
        url_mapping() + [
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
    def __init__(self):
        pass

    @classmethod
    def preset_class(cls):
        """Return the preset class name"""
        x = __package__
        if x is None:
            x=""
        x=x.strip()
        if len(x):
            x+="."
        x+=cls.__class__.__name__
        return x
    
    def default_config(self):
        """Return a default configuration file in yaml format"""
        return f"""
setup:
    preset:            {self.preset_class():<40} # Preset class name
    modules:           {"":<40} # Modules with commands to import
      - liquer.ext.meta
      - liquer.ext.basic

    cache:             {"off":<40} # Cache type (off, memory, file, ...)
    cache_path:        {"cache":<40} # Cache path (for file cache)
    cache_concurrency: {"central":<40} # Cache concurrency (off, local, central)
    recipe_folders:    {"[]":<40} # Recipe folders

    server_type:       {"flask":<40} # Server type (flask, tornado, ...)
    url_prefix:        {'"/liquer"':<40} # URL prefix for the server
    port:              {5000:<40} # Server port
"""
    
    def initialize(self, config, worker_environment=False):        
        """Initialize from configuration.
        If worker_environment is True, then initialize specificallz the worker environment,
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
        return config["setup"].get(name,default)
    
    def load_modules(self, config):
        """Load modules scpecified in the configuration
        List of modules is taken from config["setup"]["modules"]
        """
        for module in self.get_setup_parameter(config, "modules", []):
            logger.info(f"Loading module {module}")
            __import__(module, fromlist=["*"])

    def create_cache(self, config):
        "Create cache object from configuration"
        import liquer.cache
        cache=self.get_setup_parameter(config, "cache", "off")
        if cache in ["off","none", "no", None, False]:
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

    def initialize_cache(self, config):
        """Initialize cache from configuration"""
        import liquer.cache
        liquer.cache.set_cache(self.create_cache(config))
        
    def initialize_store(self, config):
        """Initialize store from configuration"""
        import liquer.store
        from liquer.recipes import RecipeSpecStore
        recipe_folders=self.get_setup_parameter(config, "recipe_folders", [])
        for folder_name in recipe_folders:
            logger.info(f"Adding recipe folder {folder_name}")
            s = RecipeSpecStore(liquer.store.FileStore(folder_name)).with_indexer()
            liquer.store.mount(folder_name, s)

    def initialize_pool(self, config):
        """Initialize pool from configuration"""
        import liquer.pool
        import liquer.cache
        cache_concurrency=self.get_setup_parameter(config, "cache_concurrency")
        if cache_concurrency in["off","none", "no", None, False]:
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

    def start_server(self, config):
        """Start server from configuration"""
        from liquer.state import set_var
        from liquer.query import evaluate

        server_type=self.get_setup_parameter(config, "server_type", "flask")
        if server_type in ["flask"]:
            logger.info(f"Starting flask server")
            import flask
            import liquer.server.blueprint as bp
            import traceback
            app = flask.Flask(__name__)
            url_prefix=self.get_setup_parameter(config, "url_prefix", "/liquer")
            port=self.get_setup_parameter(config, "port", "5000")
            flask_debug=self.get_setup_parameter(config, "debug", False)
            host=self.get_setup_parameter(config, "host", "127.0.0.1")
            flask_threaded=self.get_setup_parameter(config, "threaded", False)
            index_query=self.get_setup_parameter(config, "index_query", "index")

            app.register_blueprint(bp.app, url_prefix=url_prefix)
            
            @app.route('/')
            @app.route('/index.html')
            def index():
                try:
                    return bp.response(evaluate(index_query))
                except:
                    traceback.print_exc()
                    flask.abort(500)

            set_var("api_path",url_prefix+"/q/")
            set_var("server",f"http://{host}:{port}")
            app.run(debug=flask_debug, host=host, port=port, threaded=flask_threaded)
        elif server_type in ["tornado"]:
            import asyncio
            logger.info(f"Starting tornado server")
            port=self.get_setup_parameter(config, "port", "5000")
            url_prefix=self.get_setup_parameter(config, "url_prefix", "/liquer")
            index_query=self.get_setup_parameter(config, "index_query", "index")
            host=self.get_setup_parameter(config, "host", "127.0.0.1")
            set_var("api_path",url_prefix+"/q/")
            set_var("server",f"http://{host}:{port}")
            asyncio.run(run_tornado(port, index_query=index_query))
        else:
            raise Exception(f"Unknown server type: {server_type}")

def set_preset(preset=None):
    """Set the preset object
    Preset can either be a preset object (instance of Preset class), a preset class name (string) or configuration (dictionary).
    If preset is None, preset is loaded based on the configuration file.
    """
    import liquer.util
    global _preset
    if preset is None:
        preset = config()
    if isinstance(preset, dict):
        if "setup" not in preset:
            raise Exception("No setup section in configuration")
        if "preset" not in preset["setup"]:
            raise Exception("No preset specified in the setup section in configuration")
        preset = preset["setup"]["preset"]
        if not isinstance(preset, str):
            raise Exception("Preset must be a fully qualified class name")
    if isinstance(preset, str):
        logger.info(f"Instantiating preset {preset}")
        preset = liquer.util.eval_fully_qualified_name(preset)()    
    if isinstance(preset, Preset):
        logger.info(f"Instantance of {preset.preset_class()} used as preset")
        _preset = preset
    else:
        raise Exception(f"Unknown preset type {repr(preset)}")