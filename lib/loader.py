#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame 2018
#
# The Loader class file is not a class but a static function list
# for loading and creating module class files and objects directly
# from the module folders.
# Updated 10/2018

from os import listdir
from os.path import isdir
from inspect import isclass
from importlib import import_module
from lib.structs.hook import Hook, HookList


def load_modules(service, directory):
    if not isdir(directory):
        raise OSError('Directory "%s" is not a valid directory!' % directory)
    loaded = dict()
    modules = listdir(directory)
    for module in modules:
        if ".py" in module:
            name = module.replace(".py", "").lower()
            service.debug('Attempting to load module "%s"..' % name)
            try:
                instance = import_module("lib.modules.%s" % name)
            except ImportError as err:
                service.error('Exception occured loading module "%s"!' % name, err=err)
            else:
                _load_module_hooks(
                    service,
                    service,
                    loaded,
                    instance,
                    "hooks_server" if service.is_server() else "hooks",
                )
                del instance
            finally:
                del name
    del modules
    service.info('Loaded %d Hooks from "%s".' % (len(loaded), directory))
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
            else:
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
    else:
        if instance is None:
            return None
        if not isclass(instance):
            return None
        try:
            obj = instance()
        except Exception as err:
            raise err
        else:
            return obj
        finally:
            del instance
    return None


def _get_function(obj, func_name, func_args=0):
    try:
        instance = getattr(obj, func_name)
    except AttributeError:
        return None
    else:
        if instance is None:
            return None
        if not callable(instance):
            return None
        if instance.__code__.co_argcount != func_args:
            del instance
            return None
        return instance
    return None


def _load_hook(log, hook, hook_class, hook_name):
    for x in range(5, -1, -1):
        func = _get_function(hook_class, hook_name, x)
        if func is not None:
            break
    if not callable(func):
        log.error(
            'Hook %s: Module "%s" object does not contain function "%s"!'
            % (hook, hook_class.__name__, hook_name)
        )
        return None
    log.debug(
        'Hook %s: Registered function "%s" in module "%s"!'
        % (hook, hook_name, hook_class.__name__)
    )
    return Hook(None, func, hook_class)


def _load_module_hooks(log, service, hooks, module, module_func):
    log.debug('Module "%s" loaded, getting hook information..' % module.__name__)
    hook_list = try_get_attr(module, module_func, True)
    if hook_list is None:
        log.debug(
            'Module "%s" (%s) did not return any hooks!'
            % (module.__name__, module_func)
        )
        return
    if not isinstance(hook_list, dict):
        log.error(
            'Module "%s" "%s" function returned an incorrect object, must be a Python dict!'
            % (module.__name__, module_func)
        )
        del hooks_exposed
        return
    log.debug(
        'Module "%s" exposed the following (%s) hooks: <%s>'
        % (module.__name__, len(hook_list), str(hook_list))
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
        else:
            if "." in hook_class:
                hook_obj = _load_hook_obj(
                    log, service, loaded, hook, module, hook_class
                )
            else:
                hook_obj = _load_hook(log, hook, module, hook_class)
            if isinstance(hook_obj, Hook):
                hooks[hook].append(hook_obj)
                del hook_obj
    del loaded
    log.info('Module "%s" loaded.' % module.__name__)


def _load_hook_obj(log, service, loaded, hook, hook_class, hook_name):
    name = hook_name.split(".")
    if len(name) != 2 and (len(name[0]) == 0 or len(name[1]) == 0):
        log.Error('Hook %s: Name of class "%s" is invalid!' % (hook, hook_name))
        del name
        return None
    if name[0] not in loaded:
        log.debug(
            'Hook %s: Class "%s" is not loaded, attempting to load and create!'
            % (hook, name[0])
        )
        try:
            obj = _get_class(hook_class, name[0])
        except Exception as err:
            log.error(
                'Hook %s: Exception occured when creating class "%s" object!'
                % (hook, name[0]),
                err=err,
            )
            del name
            return None
        if obj is None:
            log.error(
                'Hook %s: Class "%s" does not exist in "%s"!'
                % (hook, name[0], hook_class.__name__)
            )
            del name
            return None
        setup = _get_function(
            obj, "setup_server" if service.is_server() else "setup", 2
        )
        if callable(setup):
            log.debug(
                'Hook %s: Class "%s" created, attempting to call setup function!'
                % (hook, name[0])
            )
            try:
                setup(service)
            except Exception as err:
                log.error(
                    'Hook %s: Class "%s" object setup function raised an exception!'
                    % (hook, name[0]),
                    err=err,
                )
                del name
                return None
            finally:
                del setup
        else:
            log.debug('Hook %s: Class "%s" created!' % (hook, name[0]))
        loaded[name[0]] = obj
        del obj
    obj = loaded[name[0]]
    for x in range(5, -1, -1):
        func = _get_function(obj, name[1], x)
        if callable(func):
            break
    if not callable(func):
        log.error(
            'Hook %s: Class "%s" object does not contain function "%s"!'
            % (hook, name[0], name[1])
        )
        del hook_object
        return None
    log.debug(
        'Hook %s: Registered object function "%s" in module "%s"!'
        % (hook, hook_name, hook_class.__name__)
    )
    return Hook(obj, func, hook_class)


# EOF
