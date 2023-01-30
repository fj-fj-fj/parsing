#!/usr/bin/env python
__all__ = (
    'BaseError',
    'ElementNotFoundError',
    'DataNotFoundError',
    'ParameterValueError',
    'raise_notfound',
)

from typing import NoReturn as _NoReturn


class BaseError(Exception):
    """Base shell for all errors."""

    @staticmethod
    def set_tracebacklimit(limit):
        import sys
        sys.tracebacklimit = limit
        BaseError.tracebacklimit = limit


class ElementNotFoundError(BaseError):
    """Has no HTML element."""


class DataNotFoundError(BaseError):
    """Raw data does not exist."""


class ParameterValueError(BaseError):
    """Got an unexpected argument value."""


class EmptyError(BaseError):
    """Object cannot be empty."""


class URLError(BaseError):
    """URL is invalid"""


def raise_notfound(tag: str) -> _NoReturn:
    """Raise <tag>NotFoundError."""
    raise _notfound_factory(tag)


def _notfound_factory(prefix, bases=(ElementNotFoundError,)) -> ElementNotFoundError:
    """Return created <prefix>NotFoundError."""
    class NotFound:
        @classmethod
        def create(cls, exception_prefix):
            return cls._create_exception(exception_prefix)

        @staticmethod
        def _create_exception(prefix, bases=bases, **attributedict):
            msg = f"Parsed object has no tag '{prefix}'"
            fullname = f'{prefix.capitalize()}NotFoundError'
            attributedict['__init__'] = lambda self: bases[0].__init__(self, msg)
            attributedict['__repr__'] = lambda self: repr(msg)
            return type(fullname, bases, attributedict)

    return NotFound().create(prefix)


if __name__ == '__main__':
    # Display imformation about 'exceptions' module
    # names, docstrings, mro
    information = '\nexception classes:\n'
    information += '-' * len(information)
    for name, obj in globals().copy().items():
        if isinstance(obj, type):
            information += f'\n{name}:\n'
            information += f"\t'''{obj.__doc__}'''\n"
            information += f'\tmro={[o.__name__ for o in obj.mro()]}'
    print(__doc__, information, sep='\n')
