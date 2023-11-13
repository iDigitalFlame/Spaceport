#!/usr/bin/false
################################
### iDigitalFlame  2016-2024 ###
#                              #
#            -/`               #
#            -yy-   :/`        #
#         ./-shho`:so`         #
#    .:- /syhhhh//hhs` `-`     #
#   :ys-:shhhhhhshhhh.:o- `    #
#   /yhsoshhhhhhhhhhhyho`:/.   #
#   `:yhyshhhhhhhhhhhhhh+hd:   #
#     :yssyhhhhhyhhhhhhhhdd:   #
#    .:.oyshhhyyyhhhhhhddd:    #
#    :o+hhhhhyssyhhdddmmd-     #
#     .+yhhhhyssshdmmddo.      #
#       `///yyysshd++`         #
#                              #
########## SPACEPORT ###########
### Spaceport + SMD
#
# Copyright (C) 2016 - 2024 iDigitalFlame
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

# loader.py
#   The Loader class file is not a class but a static function list for loading
#   and creating module class files and objects directly from the module folders.

from os import listdir
from io import StringIO
from inspect import isclass
from importlib import import_module
from os.path import isdir, basename
from lib.util.file import perm_check
from lib.structs.hook import Hook, HookList
from lib.command import try_get_attr, module_base


def _hooks_to_str(hooks):
    if not isinstance(hooks, dict) or len(hooks) == 0:
        return "[]"
    b, c = StringIO(), 0
    for k, v in hooks.items():
        if c > 0:
            b.write(", ")
        b.write(f"0x{k:02X}: ")
        if not isinstance(v, str):
            b.write(f"{v}")
        else:
            b.write(v)
        c += 1
    r = b.getvalue()
    b.close()
    del b, c
    return f"[{r}]"


def _get_class(module, name):
    try:
        x = getattr(module, name)
    except AttributeError:
        return None
    if not isclass(x):
        return None
    try:
        o = x()
    finally:
        del x
    return o


def _get_func(obj, name, args=0):
    try:
        x = getattr(obj, name)
    except AttributeError:
        return None
    if not callable(x) or x.__code__.co_argcount != args:
        del x
        return None
    return x


def load_modules(service, directory):
    if not isdir(directory):
        raise OSError(f'path "{directory}" is not a directory')
    e, x, b = dict(), listdir(directory), module_base(directory)
    f = "hooks_server" if service.is_server() else "hooks"
    for m in x:
        if not m.endswith(".py"):
            continue
        # NOTE(dij): Only root can own these file and they cannot be writable by
        #            non-root users.
        perm_check(f"{directory}/{m}", 0o7022, 0, 0)
        n = m[:-3].lower()
        if "/" in n or "\\" in n:
            n = basename(n)
        service.debug(f'[loader]: Loading module "{directory}/{m}"..')
        try:
            i = import_module(f"{b}.{n}")
        except ImportError as err:
            service.error(f'[loader]: Cannot import module "{directory}/{m}"!', err)
            continue
        finally:
            del n
        try:
            _load_module_hooks(service, e, i, f)
        except Exception as err:
            service.error(f'[loader]: Cannot load module "{directory}/{m}"!', err)
        del i, m
    del x, f
    service.info(f'[loader]: Loaded {len(e)} Hooks from "{directory}".')
    return e


def _load_hook(service, hook, cls, name):
    for x in range(5, -1, -1):
        f = _get_func(cls, name, x)
        if not callable(f):
            continue
        service.debug(
            f'[loader/hook/0x{hook:02X}]: Registered function "{name}" in module "{cls.__name__}"!'
        )
        return Hook(None, f, cls)
    return service.error(
        f'[loader/hook/0x{hook:02X}]: Module "{cls.__name__}" does not contain function "{name}"!'
    )


def _load_module_hooks(service, hooks, module, func):
    service.debug(
        f'[loader/m]: Module "{module.__name__}" loaded, getting Hook information..'
    )
    try:
        e = try_get_attr(module, func, True)
    except Exception as err:
        return service.debug(
            f'[loader/m]: Cannot read module "{module.__name__}" ({func})!', err
        )
    if e is None:
        del e
        return service.debug(
            f'[loader/m]: Module "{module.__name__}" ({func}) did not return any Hooks!'
        )
    if not isinstance(e, dict):
        return service.error(
            f'[loader/m]: Module "{module.__name__}" "{func}" function returned an invalid '
            f"object type ({type(e)}) it must be a dict!"
        )
    service.debug(
        f'[loader/m]: Module "{module.__name__}" exposed the following ({len(e)}) hooks: {_hooks_to_str(e)}.'
    )
    v = dict()
    for h, c in e.items():
        if h not in hooks:
            hooks[h] = HookList()
        if isinstance(c, list):
            for s in c:
                if "." in s:
                    o = _load_hook_obj(service, v, h, module, s)
                else:
                    o = _load_hook(service, h, module, s)
                if isinstance(o, Hook):
                    hooks[h].append(o)
                del o
            continue
        if "." in c:
            o = _load_hook_obj(service, v, h, module, c)
        else:
            o = _load_hook(service, h, module, c)
        if isinstance(o, Hook):
            hooks[h].append(o)
        del o
    del v, e
    service.info(f'[loader/m]: Module "{module.__name__}" loaded.')


def _load_hook_obj(service, loaded, hook, cls, name):
    x = name.find(".")
    if x < 1 or x + 1 >= len(name):
        return service.error(
            f'[loader/hook/0x{hook:02X}]: name of class "{name}" is invalid!'
        )
    i, v = name[0:x], name[x + 1 :]
    del x
    if i not in loaded:
        service.debug(
            f'[loader/hook/0x{hook:02X}]: Loading and creating object from Class "{i}".'
        )
        try:
            o = _get_class(cls, i)
        except Exception as err:
            return service.error(
                f'[loader/hook/0x{hook:02X}]: Cannot create Class "{i}" object!', err
            )
        if o is None:
            return service.error(
                f'[loader/hook/0x{hook:02X}]: Class "{i}" does not exist in "{cls.__name__}"!'
            )
        e = _get_func(o, "setup_server" if service.is_server() else "setup", 2)
        if callable(e):
            service.debug(
                f'[loader/hook/0x{hook:02X}]: Class "{i}" created, running setup..'
            )
            try:
                e(service)
            except Exception as err:
                return service.error(
                    f'[loader/hook/0x{hook:02X}]: Cannot execute Class "{i}" setup function!',
                    err,
                )
        else:
            service.debug(f'[loader/hook/0x{hook:02X}]: Class "{i}" created!')
        loaded[i] = o
        del o, e
    o = loaded[i]
    for x in range(5, -1, -1):
        f = _get_func(o, v, x)
        if callable(f):
            service.debug(
                f'[loader/hook/0x{hook:02X}]: Registered object function "{name}" in module "{cls.__name__}"!'
            )
            return Hook(o, f, cls)
    return service.error(
        f'[loader/hook/0x{hook:02X}]: Class "{i}" object does not contain function "{v}"!'
    )
