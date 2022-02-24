#!/usr/bin/false
# The Loader class file is not a class but a static function list
# for loading and creating module class files and objects directly
# from the module folders.
#
# System Management Daemon
#
# Copyright (C) 2016 - 2022 iDigitalFlame
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

from os import listdir
from inspect import isclass
from lib.constants import EMPTY
from importlib import import_module
from os.path import isdir, basename
from lib.structs.hook import Hook, HookList


def try_get_attr(obj, name, call):
    if obj is None or not isinstance(name, str):
        return None
    if len(name) == 0:
        return None
    x = None
    try:
        x = getattr(obj, name)
    except AttributeError:
        try:
            x = getattr(obj, name.lower())
        except AttributeError:
            try:
                x = getattr(obj, name.upper())
            except AttributeError:
                try:
                    x = getattr(obj, name.capitalize())
                except AttributeError:
                    pass
    if x is not None and callable(x) and call:
        try:
            return x()
        except TypeError:
            pass
    return x


def load_modules(service, directory):
    if not isdir(directory):
        raise OSError(f'Path "{directory}" is not a valid directory')
    e = dict()
    x = listdir(directory)
    for m in x:
        if ".py" not in m:
            continue
        n = m.replace(".py", EMPTY).lower()
        if "/" in n or "\\" in n:
            n = basename(n)
        service.debug(f'Attempting to load module "{n}"..')
        try:
            x = import_module(f"lib.modules.{n}")
        except ImportError as err:
            service.error(f'Error loading module "{n}"!', err=err)
            continue
        finally:
            del n
        _load_module_hooks(
            service,
            service,
            e,
            x,
            "hooks_server" if service.is_server() else "hooks",
        )
        del m
    del x
    service.info(f'Loaded {len(e)} Hooks from "{directory}".')
    return e


def _get_class(class_module, class_name):
    try:
        x = getattr(class_module, class_name)
    except AttributeError:
        return None
    if x is None:
        return None
    if not isclass(x):
        return None
    try:
        obj = x()
    except Exception as err:
        raise err
    finally:
        del x
    return obj


def _get_function(obj, func_name, func_args=0):
    try:
        x = getattr(obj, func_name)
    except AttributeError:
        return None
    if x is None:
        return None
    if not callable(x):
        del x
        return None
    if x.__code__.co_argcount != func_args:
        del x
        return None
    return x


def _load_hook(log, hook, hook_class, hook_name):
    f = None
    for x in range(5, -1, -1):
        f = _get_function(hook_class, hook_name, x)
        if f is not None:
            break
    if not callable(f):
        log.error(
            f'Hook 0x{hook:02X}: Module "{hook_class.__name__}" does not contain function "{hook_name}"!'
        )
        return None
    log.debug(
        f'Hook 0x{hook:02X}: Registered function "{hook_name}" in module "{hook_class.__name__}"!'
    )
    return Hook(None, f, hook_class)


def _load_module_hooks(log, service, hooks, module, module_func):
    log.debug(f'Module "{module.__name__}" loaded, getting hook information..')
    try:
        e = try_get_attr(module, module_func, True)
    except Exception as err:
        return log.debug(
            f'Error reading module "{module.__name__}" ({module_func})!', err=err
        )
    if e is None:
        return log.debug(
            f'Module "{module.__name__}" ({module_func}) did not return any hooks!'
        )
    if not isinstance(e, dict):
        del e
        return log.error(
            f'Module "{module.__name__}" "{module_func}" function returned an incorrect '
            "object, it must be a Dict!"
        )
    log.debug(
        f'Module "{module.__name__}" exposed the following ({len(e)}) hooks: <{str(e)}>'
    )
    v = dict()
    for h, c in e.items():
        if h not in hooks:
            hooks[h] = HookList()
        if isinstance(c, list):
            for s in c:
                if "." in s:
                    o = _load_hook_obj(log, service, v, h, module, s)
                else:
                    o = _load_hook(log, h, module, s)
                if isinstance(o, Hook):
                    hooks[h].append(o)
                del o
            continue
        if "." in c:
            o = _load_hook_obj(log, service, v, h, module, c)
        else:
            o = _load_hook(log, h, module, c)
        if isinstance(o, Hook):
            hooks[h].append(o)
        del o
    del v
    del e
    log.info(f'Module "{module.__name__}" loaded.')


def _load_hook_obj(log, service, loaded, hook, hook_class, hook_name):
    n = hook_name.split(".")
    if len(n) != 2 and (len(n[0]) == 0 or len(n[1]) == 0):
        log.error(f'Hook 0x{hook:02X}: Name of class "{hook_name}" is invalid!')
        del n
        return None
    if n[0] not in loaded:
        log.debug(
            f'Hook 0x{hook:02X}: Class "{n[0]}" is not loaded, attempting to load and create!'
        )
        try:
            o = _get_class(hook_class, n[0])
        except Exception as err:
            log.error(
                f'Hook 0x{hook:02X}: Error creating class "{n[0]}" object!', err=err
            )
            del n
            return None
        if o is None:
            log.error(
                f'Hook 0x{hook:02X}: Class "{n[0]}" does not exist in "{hook_class.__name__}"!'
            )
            del n
            return None
        e = _get_function(o, "setup_server" if service.is_server() else "setup", 2)
        if callable(e):
            log.debug(
                f'Hook 0x{hook:02X}: Class "{n[0]}" created, attempting to call setup function!'
            )
            try:
                e(service)
            except Exception as err:
                log.error(
                    f'Hook 0x{hook:02X}: Class "{n[0]}" setup function failed!',
                    err=err,
                )
                del n
                return None
            finally:
                del e
        else:
            log.debug(f'Hook 0x{hook:02X}: Class "{n[0]}" created!')
        loaded[n[0]] = o
        del o
    f = None
    o = loaded[n[0]]
    for x in range(5, -1, -1):
        f = _get_function(o, n[1], x)
        if callable(f):
            break
    if not callable(f):
        log.error(
            f'Hook 0x{hook:02X}: Class "{n[0]}" object does not contain function "{n[1]}"!'
        )
        return None
    log.debug(
        f'Hook 0x{hook:02X}: Registered object function "{hook_name}" in module "{hook_class.__name__}"!'
    )
    return Hook(o, f, hook_class)
