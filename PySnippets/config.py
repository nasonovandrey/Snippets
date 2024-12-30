from time import sleep

class ConfigMeta(type):
    def __new__(cls, name, bases, class_dict):
        combined_dict = {**class_dict, **class_dict.get('__annotations__', {})}
        config_fields = {
            k: v for k, v in combined_dict.items() if isinstance(v, type) and issubclass(v, Config)
        }
        orig_init = class_dict.get('__init__')

        def __init__(self, dictionary):
            for field_name, field_type in config_fields.items():
                setattr(self, field_name, field_type(dictionary.get(field_name, {})))
            if orig_init:
                orig_init(self, dictionary)

        class_dict['__init__'] = __init__
        return super().__new__(cls, name, bases, class_dict)

class Config(metaclass=ConfigMeta):
    def __getattr__(self, name):
        for field_name, field_value in self.__dict__.items():
            if isinstance(field_value, Config) and hasattr(field_value, name):
                return getattr(field_value, name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


class LogConfig(Config):
    def __init__(self, d):
        self._logging = d.get("logging", True)
        self._target = d.get("target", None)
    def disable_logging(self):
        self._logging = False
    def enable_logging(self):
        self._logging = True
    def set_target(self, path):
        self._target = path

class DatabaseConfig(Config):
    def __init__(self, d):
        self._host = d.get("host", "localhost")
        self._port = d.get("port", 1234)
        self._username = d.get("username", "admin")
        self._password = d.get("password", "1234")
    def set_username(self, username):
        self._username = username
    def set_password(self, password):
        self._password = password
    def connect(self):
        for _ in range(10):
            sleep(1)


class AppConfig(Config):
    log_config: LogConfig
    database_config: DatabaseConfig

    def __init__(self, d):
        self._app = d.get("app", "new_app")
