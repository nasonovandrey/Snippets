import argparse
import inspect
import re
import asyncio
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Type,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)


def parse_docstring(func: Callable) -> Dict[str, str]:
    docstring = func.__doc__
    if not docstring:
        return {}

    args_section_match = re.search(r"Arguments:\n\s*((?:.*\n)*)", docstring)

    if not args_section_match:
        return {}

    args_section = args_section_match.group(1)

    arg_lines = args_section.split("\n")

    args_dict = {}
    current_arg = None
    current_desc = []
    for line in arg_lines:
        arg_match = re.match(r"\s*(\w+) \(([\w\[\], ]+)\): (.*)", line)
        if arg_match:
            if current_arg:
                args_dict[current_arg] = " ".join(current_desc).strip()
            current_arg = arg_match.group(1)
            current_desc = [arg_match.group(3)]
        elif current_arg:
            current_desc.append(line.strip())

    if current_arg:
        args_dict[current_arg] = " ".join(current_desc).strip()

    return args_dict


def noop(*args, **kwargs):
    """No-op function that does nothing."""


def is_optional_type(param_type) -> bool:
    """Check if the parameter type is Optional."""
    if get_origin(param_type) is Union:
        args = get_args(param_type)
        if type(None) in args:
            return True
    return False


def is_list_type(param_type) -> bool:
    """Check if the parameter type is List."""
    return get_origin(param_type) is list


def add_function_parameters_to_parser(
    func: Callable,
    parser: argparse.ArgumentParser,
    type_action_map: Dict[Type, Any] = None,
    group_name: str = "",
    blacklist: List[str] = None,
):
    if type_action_map is None:
        type_action_map = {}
    if blacklist is None:
        blacklist = []

    signature = inspect.signature(func)
    type_hints = get_type_hints(func)
    group = parser.add_argument_group(group_name)

    # Parse docstrings to get argument descriptions
    arg_docs = parse_docstring(func)

    for param_name, param in signature.parameters.items():
        if param_name in ("self", "cls") or param_name in blacklist:
            continue

        param_type = type_hints.get(param_name, param.annotation)
        is_optional = is_optional_type(param_type) or param.default is not inspect.Parameter.empty

        if is_optional and is_optional_type(param_type):
            param_type = [arg for arg in get_args(param_type) if arg is not type(None)][0]

        help_string = arg_docs.get(param_name, "")
        default_value = param.default if param.default is not inspect.Parameter.empty else None

        if is_list_type(param_type):
            element_type = get_args(param_type)[0]
            if element_type in type_action_map:
                type_action = type_action_map[element_type]
                if type_action != noop:
                    group.add_argument(
                        f"--{param_name}",
                        type=type_action,
                        nargs="+",
                        required=not is_optional,
                        help=help_string,
                        default=default_value,
                    )
            else:
                raise ValueError(f"Unknown type {element_type} for parameter {param_name}")
        elif param_type in type_action_map:
            type_action = type_action_map[param_type]
            if type_action != noop:
                group.add_argument(
                    f"--{param_name}",
                    type=type_action,
                    required=not is_optional,
                    help=help_string,
                    default=default_value,
                )
        else:
            if param_name == "loop":
                continue

            raise ValueError(f"Unknown type {param_type} for parameter {param_name}")


def extract_group_arguments(args, parser, groupname):
    group = None
    for action_group in parser._action_groups:
        if action_group.title == groupname:
            group = action_group
            break

    if group is None:
        raise ValueError(f"No argument group named '{groupname}' found")

    group_args = {
        arg: getattr(args, arg) for arg in vars(args) if arg in {action.dest for action in group._group_actions}
    }
    return group_args

