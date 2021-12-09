#!/usr/bin/false
# The Utils Python file is used to help assist with simple repeatable functions that
# may be used across the System Management Daemon. Functions here are basic functions
# for file writing, reading and other simple operations.
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

from re import compile
from io import StringIO
from hashlib import md5
from sys import stderr, exit
from threading import Thread
from traceback import format_exc
from signal import SIGKILL, SIGINT
from os.path import isfile, dirname, exists
from json import loads, dumps, JSONDecodeError
from os import environ, remove, makedirs, stat, chmod, kill
from subprocess import (
    PIPE,
    Popen,
    STDOUT,
    DEVNULL,
    run as sub_run,
    SubprocessError,
)

_ENV_REGEX = compile("\\$[\\w\\d_-]+|\\$\\{[\\w\\d_-]+\\}")


def eval_env(val):
    if not isinstance(val, str):
        return val
    if len(val) == 0:
        return val
    m = _ENV_REGEX.search(val)
    if m is None:
        return val
    b = StringIO()
    p = 0
    while m is not None:
        x = m.start()
        if x > p:
            b.write(val[p:x])
        e = m.end()
        if val[x] == "$":
            x += 1
        p = e
        if val[x] == "{" and val[e - 1] == "}":
            e -= 1
            x += 1
        v = val[x:e]
        if v not in environ:
            b.write(val[m.start() : m.end()])
        else:
            b.write(environ[v])
        m = _ENV_REGEX.search(val, pos=m.end())
        del v
        del e
        del x
    if p < len(val):
        b.write(val[p:])
    r = b.getvalue()
    del b
    del p
    return r


def get_pid_uid(pid):
    try:
        return stat(f"/proc/{pid}").st_uid
    except OSError:
        pass
    return None


def boolean(bool_value):
    if isinstance(bool_value, str):
        if len(bool_value) == 0:
            return False
        value = bool_value.lower().strip()
        return (
            value == "1"
            or value == "on"
            or value == "yes"
            or value == "true"
            or value[0] == "t"
        )
    if isinstance(bool_value, bool):
        return bool_value
    if isinstance(bool_value, int) or isinstance(bool_value, float):
        return bool_value > 0
    return False


def stop(process_object):
    if not isinstance(process_object, Popen):
        return
    if process_object.poll() is not None:
        return process_object.wait()
    else:
        try:
            process_object.send_signal(SIGINT)
        except (OSError, SubprocessError):
            pass
    try:
        process_object.terminate()
    except (OSError, SubprocessError):
        pass
    try:
        process_object.kill()
    except (OSError, SubprocessError):
        pass
    try:
        kill(process_object.pid, SIGKILL)
    except OSError:
        pass
    try:
        process_object.communicate(timeout=5)
    except (OSError, SubprocessError):
        pass
    process_object.wait(timeout=5)
    del process_object


def remove_file(file_path):
    if not isinstance(file_path, str) or not isfile(file_path):
        return
    try:
        remove(file_path)
    except OSError:
        pass


def read_json(file_path, ignore_errors=True):
    data = read(file_path, ignore_errors, False)
    if not isinstance(data, str):
        if ignore_errors:
            return None
        raise OSError(f'Reading file "{file_path}" did not return string data!')
    if len(data) == 0:
        return None
    try:
        json_data = loads(data)
    except (JSONDecodeError, OverflowError) as err:
        if ignore_errors:
            return None
        raise OSError(err)
    finally:
        del data
    return json_data


def print_error(message, error=None, quit=True):
    print(message, file=stderr)
    if error is not None:
        print(format_exc(limit=3), file=stderr)
    if quit:
        exit(1)


def read(file_path, ignore_errors=True, binary=False):
    if not isinstance(file_path, str):
        if ignore_errors:
            return None
        raise OSError('Parameter "file_path" must be a Python string!')
    if not isfile(file_path):
        if ignore_errors:
            return None
        raise OSError(f'Parameter path "{file_path}" is not a file!')
    try:
        handle = open(file_path, "rb" if binary else "r")
    except OSError as err:
        if ignore_errors:
            return None
        raise err
    try:
        data = handle.read()
    except OSError as err:
        if ignore_errors:
            return None
        raise err
    finally:
        handle.close()
        del handle
    return data


def hash_file(file_path, block=4096, ignore_errors=True):
    if not isinstance(file_path, str):
        if ignore_errors:
            return None
        raise OSError('Parameter "file_path" must be a Python string!')
    if not isfile(file_path):
        if ignore_errors:
            return None
        raise OSError(f'Parameter path "{file_path}" is not a file!')
    generator = md5()
    try:
        with open(file_path, "rb") as handle:
            while True:
                buffer = handle.read(block)
                if not buffer:
                    break
                generator.update(buffer)
    except OSError as err:
        if ignore_errors:
            return None
        raise err
    h = generator.hexdigest()
    del generator
    return h


def run(command, shell=False, wait=None, ignore_errors=True):
    cmd = command
    if shell:
        if isinstance(command, list):
            cmd = " ".join(command)
        elif not isinstance(command, str):
            cmd = str(command)
    elif not isinstance(command, list):
        if isinstance(command, str):
            cmd = command.split(" ")
        else:
            cmd = str(command).split(" ")
    time = None
    if isinstance(wait, bool):
        if not wait:
            _ProcessThread(cmd, shell).start()
            return None
    elif isinstance(wait, int) or isinstance(wait, float):
        time = float(wait)
    try:
        out = sub_run(
            cmd,
            text=True,
            shell=shell,
            check=False,
            stdout=PIPE,
            timeout=time,
            stderr=STDOUT,
            encoding="UTF-8",
            universal_newlines=True,
        )
    except (OSError, SubprocessError, UnicodeDecodeError) as err:
        if ignore_errors:
            return None
        if isinstance(err, OSError):
            raise err
        raise OSError(err)
    finally:
        del cmd
    if time is None and wait is None:
        ret = out.returncode
        del out
        del time
        if ignore_errors:
            return ret == 0
        if ret == 0:
            return True
        raise OSError(f'Process "{command}" exit code was non-zero ({ret})!')
    output = out.stdout
    del out
    del time
    if output is None or len(output) == 0:
        return None
    if output[len(output) - 1] == "\n":
        output = output[: len(output) - 1]
    return output


def write_json(file_path, obj, indent=0, sort=False, ignore_errors=True, perms=None):
    if obj is None:
        if not ignore_errors:
            raise OSError('Paramater "obj" cannot be None!')
        return False
    try:
        data = dumps(obj, indent=indent, sort_keys=sort)
    except (TypeError, JSONDecodeError, OverflowError) as err:
        if not ignore_errors:
            raise OSError(err)
        return False
    try:
        return write(file_path, data, ignore_errors, False, False, perms)
    except OSError as err:
        if not ignore_errors:
            raise err
        return False
    finally:
        del data


def write(file_path, data, ignore_errors=True, binary=False, append=False, perms=None):
    if not isinstance(file_path, str):
        if not ignore_errors:
            raise OSError('Parameter "file_path" must be a Python string!')
        return False
    file_dir = dirname(file_path)
    if not exists(file_dir):
        try:
            makedirs(file_dir, exist_ok=True)
        except OSError as err:
            if not ignore_errors:
                raise err
            return False
    del file_dir
    try:
        handle = open(
            file_path,
            ("ab" if binary else "a") if append else ("wb" if binary else "w"),
        )
    except OSError as err:
        if not ignore_errors:
            raise err
        return False
    try:
        if data is None:
            handle.write(bytes() if binary else str())
        elif isinstance(data, str):
            if binary:
                handle.write(data.encode("UTF-8"))
            else:
                handle.write(data)
        else:
            data_string = str(data)
            if binary:
                handle.write(data_string.encode("UTF-8"))
            else:
                handle.write(data_string)
            del data_string
        handle.flush()
        if isinstance(perms, int):
            chmod(file_path, perms, follow_symlinks=True)
        return True
    except (OSError, UnicodeEncodeError) as err:
        if not ignore_errors:
            raise err
        return False
    finally:
        handle.close()
        del handle


class _ProcessThread(Thread):
    def __init__(self, command, shell):
        Thread.__init__(self, name="SMDProcessCleanupThread", daemon=True)
        self._cmd = command
        self._shell = shell

    def run(self):
        try:
            sub_run(
                self._cmd,
                check=False,
                stdout=DEVNULL,
                stderr=DEVNULL,
                shell=self._shell,
            )
        except Exception:
            pass
        del self._cmd
        del self._shell
