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
from os.path import isdir
from inspect import isclass
from lib.constants import EMPTY
from importlib import import_module
from lib.structs.hook import Hook, HookList


def load_modules(service, directory):
    if not isdir(directory):
        raise OSError(f'Directory path "{directory}" is not a valid directory!')
    loaded = dict()
    modules = listdir(directory)
    for module in modules:
        if ".py" in module:
            name = module.replace(".py", EMPTY).lower()
            service.debug(f'Attempting to load module "{name}"...')
            instance = None
            try:
                instance = import_module(f"lib.modules.{name}")
            except ImportError as err:
                service.error(f'Exception occurred loading module "{name}"!', err=err)
                continue
            finally:
                del name
            _load_module_hooks(
                service,
                service,
                loaded,
                instance,
                "hooks_server" if service.is_server() else "hooks",
            )
            del instance
    del modules
    service.info(f'Loaded {len(loaded)} Hooks from "{directory}".')
    return loaded


def try_get_attr(obj, name, func=True):
    if obj is not None and isinstance(name, str):
        obj_attr = None
        try:
            obj_attr = getattr(obj, name)
        except AttributeError:
            try:
                obj_attr = getattr(obj, name.lower())
            except AttributeError:
                try:
                    obj_attr = getattr(obj, name.upper())
                except AttributeError:
                    try:
                        obj_attr = getattr(obj, name.capitalize())
                    except AttributeError:
                        pass
        if obj_attr is not None:
            if callable(obj_attr) and not func:
                return obj_attr
            try:
                return obj_attr()
            except Exception:
                pass
        return obj_attr
    return None


def _get_class(class_module, class_name):
    try:
        instance = getattr(class_module, class_name)
    except AttributeError:
        return None
    if instance is None:
        return None
    if not isclass(instance):
        return None
    try:
        obj = instance()
    except Exception as err:
        raise err
    finally:
        del instance
    return obj


def _get_function(obj, func_name, func_args=0):
    try:
        instance = getattr(obj, func_name)
    except AttributeError:
        return None
    if instance is None:
        return None
    if not callable(instance):
        return None
    if instance.__code__.co_argcount != func_args:
        del instance
        return None
    return instance


def _load_hook(log, hook, hook_class, hook_name):
    func = None
    for x in range(5, -1, -1):
        func = _get_function(hook_class, hook_name, x)
        if func is not None:
            break
    if not callable(func):
        log.error(
            f'Hook 0x{hook:02X}: Module "{hook_class.__name__}" object does not contain function "{hook_name}"!'
        )
        return None
    log.debug(
        f'Hook 0x{hook:02X}: Registered function "{hook_name}" in module "{hook_class.__name__}"!'
    )
    return Hook(None, func, hook_class)


def _load_module_hooks(log, service, hooks, module, module_func):
    log.debug(f'Module "{module.__name__}" loaded, getting hook information..')
    hook_list = try_get_attr(module, module_func, True)
    if hook_list is None:
        return log.debug(
            f'Module "{module.__name__}" ({module_func}) did not return any hooks!'
        )
    if not isinstance(hook_list, dict):
        del hook_list
        return log.error(
            f'Module "{module.__name__}" "{module_func}" function returned an incorrect object, '
            f"it must be a Python dict!"
        )
    log.debug(
        f'Module "{module.__name__}" exposed the following ({len(hook_list)}) hooks: <{str(hook_list)}>'
    )
    loaded = dict()
    for hook, hook_class in hook_list.items():
        if hook not in hooks:
            hooks[hook] = HookList()
        if isinstance(hook_class, list):
            for hook_sub in hook_class:
                if "." in hook_sub:
                    hook_obj = _load_hook_obj(
                        log, service, loaded, hook, module, hook_sub
                    )
                else:
                    hook_obj = _load_hook(log, hook, module, hook_sub)
                if isinstance(hook_obj, Hook):
                    hooks[hook].append(hook_obj)
                    del hook_obj
            continue
        if "." in hook_class:
            hook_obj = _load_hook_obj(log, service, loaded, hook, module, hook_class)
        else:
            hook_obj = _load_hook(log, hook, module, hook_class)
        if isinstance(hook_obj, Hook):
            hooks[hook].append(hook_obj)
            del hook_obj
    del loaded
    log.info(f'Module "{module.__name__}" loaded.')


def _load_hook_obj(log, service, loaded, hook, hook_class, hook_name):
    name = hook_name.split(".")
    if len(name) != 2 and (len(name[0]) == 0 or len(name[1]) == 0):
        log.Error(f'Hook 0x{hook:02X}: Name of class "{hook_name}" is invalid!')
        del name
        return None
    if name[0] not in loaded:
        log.debug(
            f'Hook 0x{hook:02X}: Class "{name[0]}" is not loaded, attempting to load and create!'
        )
        try:
            obj = _get_class(hook_class, name[0])
        except Exception as err:
            log.error(
                f'Hook 0x{hook:02X}: Exception occurred when creating class "{name[0]}" object!',
                err=err,
            )
            del name
            return None
        if obj is None:
            log.error(
                f'Hook 0x{hook:02X}: Class "{name[0]}" does not exist in "{hook_class.__name__}"!'
            )
            del name
            return None
        setup = _get_function(
            obj, "setup_server" if service.is_server() else "setup", 2
        )
        if callable(setup):
            log.debug(
                f'Hook 0x{hook:02X}: Class "{name[0]}" created, attempting to call setup function!'
            )
            try:
                setup(service)
            except Exception as err:
                log.error(
                    f'Hook 0x{hook:02X}: Class "{name[0]}" object setup function raised an exception!',
                    err=err,
                )
                del name
                return None
            finally:
                del setup
        else:
            log.debug(f'Hook 0x{hook:02X}: Class "{name[0]}" created!')
        loaded[name[0]] = obj
        del obj
    func = None
    obj = loaded[name[0]]
    for x in range(5, -1, -1):
        func = _get_function(obj, name[1], x)
        if callable(func):
            break
    if not callable(func):
        log.error(
            f'Hook 0x{hook:02X}: Class "{name[0]}" object does not contain function "{name[1]}"!'
        )
        return None
    log.debug(
        f'Hook 0x{hook:02X}: Registered object function "{hook_name}" in module "{hook_class.__name__}"!'
    )
    return Hook(obj, func, hook_class)
