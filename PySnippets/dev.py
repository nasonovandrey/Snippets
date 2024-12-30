import asyncio
import functools
import json
import sys
import weakref
from enum import Enum
from threading import Thread
from typing import Type, TypeVar

from orion_py.types import Duration, Timestamp


def checkable_enum(cls):
    if not issubclass(cls, Enum):
        raise TypeError("checkable_enum decorator can only be used with subclasses of Enum")

    for name in cls.__members__:
        method_name = f"is_{name.lower()}"
        if not hasattr(cls, method_name):
            setattr(cls, method_name, lambda self, name=name: self.name == name)
    return cls


def async_rate_limited(duration: Duration, count: int):
    """
    Limits execution of the coroutine based based on timeframe.
    Maximum of `count` calls allowed during a `duration`.
    """

    def decorate(coro):
        calls = []

        async def rate_limited_coroutine(*args, **kargs):
            now = Timestamp.Now()

            while calls and now - calls[0] > duration:
                calls.pop(0)

            while len(calls) >= count:
                wait_duration = (calls[0] + duration) - now
                await asyncio.sleep(wait_duration.GetSecondsFloat())
                now = Timestamp.Now()
                while calls and now - calls[0] > duration:
                    calls.pop(0)

            ret = await coro(*args, **kargs)
            calls.append(Timestamp.Now())
            return ret

        return rate_limited_coroutine

    return decorate


T = TypeVar("T", bound="Configurable")


class Configurable:
    @classmethod
    def from_file(cls: Type[T], file_path: str) -> T:
        """
        Create an instance of a class extending Configurable from a JSON file.

        This method reads a JSON file, parses it, and uses its contents to
        instantiate an object of the class. The JSON structure should match
        the expected arguments of the class's __init__ method.

        Parameters:
        file_path (str): The path to the JSON file to be parsed.

        Returns:
        T: An instance of the class that extends Configurable.

        Raises:
        FileNotFoundError: If the specified file does not exist.
        json.JSONDecodeError: If the file is not a valid JSON.
        """
        with open(file_path, "r") as file:
            data = json.load(file)

        return cls(**data)


class ThreadedEventLoop:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = Thread(target=self._start_loop)
        self.thread.daemon = True
        self.thread.start()

    def _start_loop(self):
        """Run the event loop."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def submit(self, coro):
        """Submit a coroutine to the event loop."""
        asyncio.run_coroutine_threadsafe(coro, self.loop)

    def stop(self):
        """Stop the event loop and wait for the thread to finish."""
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()


_coroutine_references = {}


def strong_referenced(coro):
    @functools.wraps(coro)
    async def wrapper(*args, **kwargs):
        weak_coro = weakref.WeakValueDictionary()

        coroutine = coro(*args, **kwargs)

        _coroutine_references[id(coroutine)] = coroutine

        weak_coro[id(coroutine)] = coroutine

        try:
            result = await coroutine
        finally:
            del _coroutine_references[id(coroutine)]

        return result

    return wrapper


if "pytest" in sys.modules:

    def strong_referenced_during_tests(coro):
        return strong_referenced(coro)

else:

    def strong_referenced_during_tests(coro):
        return coro

