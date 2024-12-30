import copy
import json
from copy import deepcopy
from pathlib import Path
from pprint import pformat
from typing import Any, Iterable, Tuple, TypeVar, cast

import jsonschema
from jsonschema.exceptions import ValidationError
from orion_py.utils import hash_dict


class BaseConfiguration:
    _schema_paths = [
        Path("/usr/local/share/orion/config.schema.json"),
        Path("/builds/infrastructure/orion/build_release/config.schema.json"),
        Path("build_release/config.schema.json"),
    ]
    _schema = None
    """Flexible configuration object.

    The Configuration class is designed to create a configuration dictionary  from a given JSON file or a dictionary, along with additional named arguments.
    Supports recursive loading of JSON files specified within a JSON file using a special
    `__PATH__:` prefix in the value to indicate the path to another JSON file that should be loaded and inserted.

    Constructor:
        - Accepts `config`, which can be a dictionary, a `Path` object, or a `BaseConfiguration` object.
        - If `config` is a `Path` object, it loads a JSON file and converts its content into a dictionary.
        - Accepts an arbitrary number of named arguments. Arguments can be either simple values or `Path` objects.

    Processing Nested Keys:
        - Uses double underscore `__` to create nested dictionary structures.
        - Example: `path__to__other='123'` results in `{'path': {'to': {'other': '123'}}}`.

    Processing Lists:
        - Keys with `list_` indicate indices in a list.
        - Fill missing indices with `None` if necessary.
        - `list_00` is used to append to the end of the list.
        - Example: `key__list_1='value'` results in `{'key': [None, 'value']}`.

    Merging Dictionaries:
        - Merges `config` and named arguments into a single dictionary.
        - Named arguments have priority in case of key conflicts.

    Processing `Path` Objects in Arguments:
        - For each argument that is a `Path` object, load the content of the corresponding JSON file.
        - Convert the loaded data into an appropriate dictionary format.

    Processing `BaseConfiguration` Objects in Arguments:
        - For each argument that is a `BaseConfiguration` object, load the content of it.
          Example: `Configuration(config={"x": 2}, key__list_00=BaseConfiguration({'y': 3})`
          results in `{'x': 2, 'key': [{'y': 3}]}`.

    Recursive JSON Loading:
        - JSON files can include paths to other JSON files to be loaded and inserted.
        - Use the format `__PATH__:/path/to/other/config.json` in any value to specify a path to another JSON file.
        - Relative paths to json files nested to another json file resolved relative to this outer file.

    Examples:
        - `Configuration(Path('config.json'), path__to__list_1__other=Path('data.json'))`:
          - Loads and converts `config.json`.
          - Loads `data.json` and uses its content for `path__to__list_1__other`.
        - `Configuration(config={"a": 1}, path__to__list_1__other='123')` results in `{'a': 1, 'path': {'to': [None, {'other': '123'}]}}`.
        - `Configuration(config={"x": 2}, key__list_00=3)` results in `{'x': 2, 'key': [3]}`.
        - `Configuration(config={"minio_config": '__PATH__:file.json'})`.
        - `Configuration(config, configs__minio_config: '__PATH__:file.json')`.
    """

    def __init__(self, config=None, **kwargs):
        # If config is a Path, load and convert the JSON file
        if isinstance(config, Path):
            path_to_json = config.resolve().parent
            config = self.load_json(config)
            self.process_nested_jsons(config, path_to_json)
        elif isinstance(config, dict):
            config = deepcopy(config)
            self.process_nested_jsons(config)
        else:
            raise ValueError("config must be a dictionary or a Path object")
        self.config = config

        for key, value in kwargs.items():
            self._process_key(key, value)

        self.validate_config(self.config)

    @classmethod
    def process_nested_jsons(cls, obj, folder: Path = Path("")):
        """Recursively handles inner json file links.

        Args:
            folder: path to folder where json file names need to be resolved. Defaults to cwd.
        """
        iterator: Iterable[Tuple[Any, Any]]
        if isinstance(obj, dict):
            iterator = obj.items()
        elif isinstance(obj, list):
            iterator = enumerate(obj)
        else:
            return

        for key, value in iterator:
            if isinstance(value, str) and value.startswith("__PATH__:"):
                path = value.replace("__PATH__:", "", 1)
                value = cls.load_json(Path(path), folder)
                obj[key] = value
            if isinstance(value, str) and isinstance(key, str) and key.endswith("_path"):
                obj[key] = str((folder / value).resolve())

            cls.process_nested_jsons(value, folder)

    @classmethod
    def _load_schema(cls):
        """
        Load the JSON schema from the hardcoded path if it hasn't been loaded yet.
        """
        if cls._schema is None:
            schema_path = None
            for path in cls._schema_paths:
                if path.exists():
                    schema_path = path
                    break
            if schema_path is None:
                raise FileNotFoundError(f"Schema file not found")

            with open(schema_path, "r") as f:
                cls._schema = json.load(f)

    def validate_config(self, config: dict) -> bool:
        """
        Validates the current configuration against the loaded JSON schema.

        Returns:
            bool: True if the configuration is valid, otherwise raises a ValidationError.
        """
        if self._schema is None:
            self._load_schema()
        try:
            jsonschema.validate(instance=config, schema=self._schema)  # type: ignore
            return True
        except ValidationError as e:
            raise ValidationError(f"Configuration validation error: {e.message}")

    @classmethod
    def load_json(cls, path: Path, folder: Path = Path("")) -> dict:
        """Load and convert JSON file.

        Args:
            folder: specify where path to json file has to be resolved. Defaults to cwd.
        """
        with open(folder / path, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data

    def raise_assertion_error(self, value):
        assert False, "Root accessor should never be called"

    @staticmethod
    def get_item_accessor(obj, key):
        """Return a function that sets a value for a given key in the object."""

        def accessor(value):
            obj[key] = value

        return accessor

    def _process_key(self, key, value):
        """Process named argument."""
        keys = key.split("__")
        # When processing the key, we do not know what type of value we will need to write to its
        # address. We only find this out on the next iteration when processing the next key.
        # Therefore, we must be able to write the value into the object later.
        accessor = self.raise_assertion_error
        # When writing the value on the next iteration, we need to know what object was there. For
        # example, if on the next iteration we will be adding an element to the list, then we need
        # to make sure that there is a list. If not, then we will
        # create it
        cur_value = self.config
        for i, subkey in enumerate(keys):
            # Handle list patterns like 'list_n'
            if subkey.startswith("list_") and subkey[5:].isdigit():
                if subkey[5:] == "00":
                    append = True
                else:
                    append = False
                    index = int(subkey[5:])

                # If the place where we are adding is not a list, then set a list there
                if not isinstance(cur_value, list):
                    cur_value = []
                    accessor(cur_value)

                # If it's adding an element, then prepare a place for it
                if append:
                    cur_value.append(None)
                    index = len(cur_value) - 1
                else:
                    # Otherwise, if it's a replacement, but the index being replaced does not
                    # exist, then we will add it along with the missing previous indices.
                    cur_value.extend([None] * (index + 1 - len(cur_value)))  # noqa

                # Set accessor to have the ability on the next iteration to write the correct
                # element into the correct position of our list
                accessor = self.get_item_accessor(cur_value, index)
                # Save the current value, which is located in the list at the address where we will
                # write the element, so if we want to write a dictionary key into our list, we knew
                # whether we need to first write a dictionary there, or if it already exists. And
                # if it exists, do we need to create the needed key there, or does the key also
                # already exist.
                cur_value = cur_value[index]
            # if not a list, it means it's a dictionary key
            else:
                if not isinstance(cur_value, dict):
                    cur_value = {}
                    accessor(cur_value)

                accessor = self.get_item_accessor(cur_value, subkey)
                if subkey in cur_value:
                    # If there is already a value at the address for which we created the accessor,
                    # then we save it
                    # for the next iteration.
                    cur_value = cur_value[subkey]
                else:
                    # If not, then we save None, so that on the next iteration we understand that
                    # in any case there it's necessary to set a dictionary or a list.
                    cur_value = None

        if isinstance(value, Path):
            value = self.load_json(value)
        elif isinstance(value, BaseConfiguration):
            value = value.config
        elif isinstance(value, str) and value.startswith("__PATH__:"):
            path = value.replace("__PATH__:", "", 1)
            value = self.load_json(Path(path))

        self.process_nested_jsons(value)

        accessor(value)

    @property
    def plaintext(self) -> str:
        return json.dumps(self.config)

    def __getitem__(self, key: str) -> None:
        return self.config[key]

    def __setitem__(self, key: str) -> None:
        raise TypeError("Configuration objects cannot be modified directly")

    def to_hash(self) -> str:
        return hash_dict(self.config)

    def update_from(self, other: "BaseConfiguration") -> None:
        self.config = merge_configs(self.config, other.config)

    def merge_with(self, other: "BaseConfiguration") -> "BaseConfiguration":
        return BaseConfiguration(merge_configs(self.config, other.config))

    def write_config(self, path: Path) -> None:
        with open(path, "w") as f:
            json.dump(self.config, f)

    def to_dict(self) -> dict:
        return copy.deepcopy(self.config)

    def __repr__(self) -> str:
        return f"""Configuration(config={pformat(self.config)})"""


Config = TypeVar("Config", bound=dict[Any, Any])


def merge_configs(source: Config, target: Config) -> Config:
    """
    Merge two nested configs (dictionaries), returning a new config (dictionary).

    This function recursively merges the keys of the first dictionary (source)
    with the keys of the second dictionary (target), creating a new dictionary
    as the result. The input dictionaries remain unchanged.

    At each level of nesting, the function checks the type of value associated
    with each key:
    - If both values are dictionaries, it recursively merges them.
    - If both values are lists, it attempts a pairwise merge of their elements.
    If lists are of different lengths, it merges the elements of the shorter list
    with the corresponding elements of the longer list, and appends any remaining
    elements from the longer list to the result.
    - For any other type of value, or mismatched types, the value from the target
    replaces the value from the source.

    Parameters:
        source (dict): The first dictionary.
        target (dict): The second dictionary.

    Returns:
        dict: A new dictionary containing the merged keys and values of source and target.
    """

    result = source.copy()

    for key, value in target.items():
        if key in result:
            if isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_configs(result[key], value)
            elif isinstance(result[key], list) and isinstance(value, list):
                merged_list = []
                max_len = max(len(result[key]), len(value))
                for i in range(max_len):
                    if i < len(result[key]) and i < len(value):
                        if isinstance(result[key][i], dict) and isinstance(value[i], dict):
                            merged_list.append(merge_configs(result[key][i], value[i]))
                        else:
                            merged_list.append(value[i])
                    elif i < len(result[key]):
                        merged_list.append(result[key][i])
                    else:
                        merged_list.append(value[i])
                result[key] = merged_list
            else:
                result[key] = value
        else:
            result[key] = value

    return cast(Config, result)


"""
    access_map = {
        "logging": ["logging_config", "enable"],
        "stats_to_logs": ["logging_config", "save_stats_to_logs"],
        "config_to_logs": ["logging_config", "save_config_to_logs"],
        ###
        "stats": ["backtest_config", "stats_config", "enable_stats"],
        "minio_opt_stats": ["backtest_config", "stats_config", "write_stats_to_minio"],
        "minio_logging": ["backtest_config", "stats_config", "upload_logs"],
        ###
        "tick_stats": ["model_configs", 0, "metrics_manager", "include_tick_statistics"],
    }

    def set(self, key, val):
        _key_list = self.access_map.get(key)
        if not _key_list:
            raise KeyError(f"Configuration has no map to {key}")
        curconf = self.config
        for _key in _key_list[:-1]:
            curconf = curconf[_key]
        curconf[_key_list[-1]] = val

    def disable(self, flag):
        self.set(flag, False)

    def enable(self, flag):
        self.set(flag, True)
"""
