# flake8: noqa: E122,W504
__all__ = (
    'ModuleDocstring',
    'check_reinit_states',
    'debugcls',
    'display_repl_code',
    'importcore',
    'warn_object_not_found',
    'refresh',
    'select_parser',
    'shortcuts',
    'snoop',
)

import importlib as _importlib
import os as _os
import re as _re
import sys as _sys
import typing as _t
import warnings as _warnings
from functools import wraps as _wraps
from types import ModuleType as _ModuleType

from parsers.datatypes import Sample as _Sample
from parsers.exceptions import ParameterValueError as _ParameterValueError
from parsers.format.colors import Colors as _Colors


def warn_object_not_found(__obj: object) -> None:
    _warnings.warn(
        f'\n\t{_Colors.RED}'
        f"{getattr(__obj, '__name__', __obj)!r}"
        f'{_Colors.NC} is not found\v',
        category=ImportWarning
    )


try:
    import snoop
except ModuleNotFoundError:
    def snoop(func):
        """Dummy decorator for `snoop` (if it doesn't exist).

        `snoop` is a Python debugging tools
            see https://github.com/alexmojaki/snoop

            `pip install snoop`
        """
        @_wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        warn_object_not_found(snoop)
        return wrapper

try:
    from parsers.debug import debugcls
except ImportError:
    def debugcls(*args, **kwargs):
        """Dummy decorator for `debugcls` (if it doesn't exist).

        `debugcls` is a class decorator (for methods and/or properties)
        """
        warn_object_not_found(debugcls)
        return args[0]


def select_parser() -> _ModuleType:
    """Return mapped parser script by sys.argv or raise.

    Exceptions:
        IndexError (parser name forgotten)
        ModuleNotFoundError (parser name does not exist)

    """
    BRED = '\t\033[1;31m'
    YELLOW = '\t\033[0;33m'
    NC = '\033[0m'
    try:
        parser = _sys.argv[1]
    except IndexError:
        print(f'{BRED}You forgot to enter the parser name!')
        print(f'{YELLOW}Usage: make run parser_name{NC}')
        raise
    try:
        return _importlib.import_module(f'parsers.user_parsers.{parser}')
    except ModuleNotFoundError:
        print(f'{BRED}Non-existent parser name passed!')
        print(f'{YELLOW}Enter correct parser name{NC}')
        print(f'{YELLOW}Or create new: make new parser_name{NC}')
        raise


def importcore(__pkg, alternative_root=None) -> _ModuleType:
    # (lambda: __import__('parsers.user_parsers.foo.parser', fromlist=[None]))()
    root = alternative_root or 'parsers.user_parsers'
    return _importlib.import_module(f'{root}.{__pkg}.parser')


def display_repl_code(script: _ModuleType) -> None:
    """Match REPL code from script.info and print"""
    print(''.join(__import__('re').findall(r"(?=>>>).*?\n", script.info)) or script.info)


def check_reinit_states() -> bool:
    for name, module in reversed(_sys.modules.items()):
        if _re.match(r'^.*\.user_parsers\..*\.(parser|core)$', name):
            return vars(module).get('reinit')
    return False


class ModuleDocstring:

    def __init__(self, docstring: str = None):
        self.__doc__ = self.doc = docstring

    def __call__(self) -> str:
        # Display doc, but not empty string if doc is empty
        return print(self.doc) if self.doc else '' or ''

    def __mul__(self, n: bool | _t.Literal[0, 1]) -> _t.Self:  # type: ignore [valid-type]
        self.doc *= ModuleDocstring.number(n)
        return self

    def __imul__(self, n: bool | _t.Literal[0, 1]) -> _t.Self:  # type: ignore [valid-type]
        return self.__mul__(n)

    __repr__ = __call__


    @staticmethod
    def number(n: int) -> int:
        """Return 1 replaced by 0 or 0 by 1"""
        if not isinstance(n, int):
            raise _ParameterValueError(f'{n=} must be integer')
        if not 0 <= n <= 1:
            raise _ParameterValueError(f'{n=} must by 0 or 1')
        return ~n


_Parser: _t.TypeAlias = object


def shortcuts(fn: _t.Callable, nb: _t.Callable, pa: _Parser, ss: _Sample) -> _t.Callable:
    """Updates globals() of the `module` namespace

    Shortcuts:
        `fn`: main func or your parser
        `nb`: simple dict-like container
        `pa`: parser for interactive mode using
        `ss`: container to add samples

        `sh`: os.system

    """
    import parsers as p
    from parsers import settings  # not reloaded yet
    def _shortcuts(module='__main__', ns=True) -> None:
        """CALLME to use shortcuts in REPL

        `module`
            Module whose globals() will be updated
        `ns`
            Three-state flag. Expected True, False or None
        `ns = True`
            include shortcut `p`: parsers (root name space)
        `ns = False`
            include shortcuts for a root package modules
            `mc`: parsers.constants
            `md`: parsers.datatypes
            `me`: parsers.exceptions
            `ms`: parsers.settings
        `ns = None`
            without modules

        """
        vars(_sys.modules[module]).update(
            {
                'sh': _os.system
            }
            |
            {
                'fn': fn,
                'nb': nb,
                'pa': pa,
                'ss': ss,
            }
            | ({'p': p} if not ns else
                {} if ns is None else
            {
                'mc': p.constants,
                'md': p.datatypes,
                'me': p.exceptions,
                'ms': settings,
            }
        ))

    _shortcuts.__doc__ = shortcuts.__doc__ + _shortcuts.__doc__
    return _shortcuts


# REFACTORME: create Loader
def refresh(pkg: _ModuleType = None, _prefix='parsers.'):  # noqa: max-complexity: 13
    """Reloads all imported modules of this app

    Base modules first, then rest, sorted by longest name.
    """
    def refresh_modules_in_special_order() -> None:
        # print(msg1, end=right_padding - len(<module name>); print(msg2)
        right_padding, count = 50, 0
        # Level-app, level-user_parsers lists of tuples('name', <module>)
        basem: list[tuple[str, _ModuleType]] = []
        userm: list[tuple[str, _ModuleType]] = []
        for name, module in _sys.modules.items():
            if name.startswith(_prefix) and not name.endswith('user_parsers'):
                (userm if 'user_parsers.' in name else basem).append((name, module))
        for (_, module) in (*basem, *sorted(userm, key=lambda w: len(w[0]), reverse=1)):  # type: ignore
            print(f"  reloading '{module.__name__}'...", end='')
            _importlib.reload(module)
            print(' [ok]'.rjust(right_padding - len(module.__name__)))
            count += 1
        print(f'  └── {count} modules successfully reloaded\n')

    def refresh_user_parser_package() -> _t.Callable:

        def find_pkg_by_name(pattern=r'^.*\.user_parsers\..*%s$'):
            """find <package> by basename or fullname module or package"""
            nonlocal pkg
            pattern %= pkg if pkg.isalpha() else pkg.split('.')[-1]
            for n, m in _sys.modules.items():
                if _re.match(pattern, n):
                    break
            else:
                raise ModuleNotFoundError
            pkg = m.__package__
            if m.__name__ is m.__package__:
                reload.pkg = m
            else:
                find_pkg_by_name()
            pkg = m

        def reload():
            """Reloads package or raise ModuleNotFoundError"""
            print(f"reloading '{reload.pkg.__name__}'...")
            _importlib.reload(reload.pkg)
            print(f"- '{reload.pkg.__name__}' successfully reloaded\n")

        if not hasattr(pkg, '__name__'):
            find_pkg_by_name()
        return reload

    if pkg:
        return refresh_user_parser_package()
    refresh_modules_in_special_order()
