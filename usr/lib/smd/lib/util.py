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

from hashlib import md5
from sys import stderr, exit
from threading import Thread
from traceback import format_exc
from signal import SIGKILL, SIGINT
from json import loads, dumps, JSONDecodeError
from os import remove, makedirs, stat, chmod, kill
from os.path import isfile, dirname, exists, relpath, realpath, islink
from subprocess import (
    PIPE,
    Popen,
    STDOUT,
    DEVNULL,
    run as sub_run,
    SubprocessError,
)


def boolean(value):
    if isinstance(value, str):
        if len(value) == 0:
            return False
        v = value.lower().strip()
        return v == "1" or v == "on" or v == "yes" or v == "true" or v[0] == "t"
    if isinstance(value, bool):
        return value
    if isinstance(value, int) or isinstance(value, float):
        return value > 0
    return False


def get_pid_uid(pid):
    try:
        return stat(f"/proc/{pid}").st_uid
    except OSError:
        pass
    return None


def remove_file(path):
    if not isinstance(path, str) or not isfile(path):
        return
    try:
        remove(path)
    except OSError:
        pass


def stop(proc, no_close=False):
    if not isinstance(proc, Popen):
        return
    if proc.poll() is not None:
        return proc.wait()
    try:
        proc.send_signal(SIGINT)
    except (OSError, SubprocessError):
        pass
    try:
        proc.terminate()
    except (OSError, SubprocessError):
        pass
    try:
        proc.wait(timeout=1)
    except (OSError, SubprocessError):
        pass
    if proc.poll() is not None:
        return proc.returncode
    try:
        proc.kill()
    except (OSError, SubprocessError):
        pass
    try:
        kill(proc.pid, SIGKILL)
    except OSError:
        pass
    if no_close:
        return
    try:
        proc.communicate(timeout=2)
    except (OSError, SubprocessError):
        pass
    try:
        proc.wait(timeout=5)
    except (OSError, SubprocessError):
        pass
    del proc


def read_json(path, errors=True):
    d = read(path, False, errors)
    if not isinstance(d, str):
        if errors:
            raise OSError(f'Reading file "{path}" did not return string data')
        return None
    if len(d) == 0:
        return None
    try:
        j = loads(d)
    except (JSONDecodeError, OverflowError) as err:
        if errors:
            raise OSError(err) from err
        return None
    finally:
        del d
    return j


def clean_path(path, root, links=False):
    if not isinstance(path, str) or len(path) == 0:
        raise ValueError('"path" must be a non-empty String')
    if not isinstance(root, str) or len(root) == 0:
        raise ValueError('"root" must be a non-empty String')
    if len(root) >= len(path):
        raise ValueError(f"Invalid root path in base {root}")
    r = root
    if r[-1] == "/":
        r = r[:-1]
    v = relpath(path, start=r)
    c = path[len(r) + 1 :]
    del r
    if len(v) != len(c) or c != v:
        raise ValueError(f'Invalid path "{path}" in base "{root}"')
    if root[-1] == "/" or v[-1] == "/":
        p = f"{root}{v}"
    else:
        p = f"{root}/{v}"
    del v
    del c
    if realpath(path) != p:
        raise ValueError(f'Invalid path "{path}" in base "{root}"')
    if not links and islink(p):
        raise ValueError(f'Path "{path}" {p} in base "{root}" cannot be a link')
    return p


def read(path, binary=False, errors=True):
    if not isinstance(path, str):
        if errors:
            raise OSError('"path" must be a String!')
        return None
    if not isfile(path):
        if errors:
            raise OSError(f'Path "{path}" is not a file')
        return None
    try:
        with open(path, "rb" if binary else "r") as f:
            return f.read()
    except OSError as err:
        if errors:
            raise err
    return None


def hash_file(path, block=4096, errors=True):
    if not isinstance(path, str):
        if errors:
            raise OSError('"path" must be a String!')
        return None
    if not isfile(path):
        if errors:
            raise OSError(f'path "{path}" is not a file')
        return None
    g = md5()
    try:
        with open(path, "rb") as f:
            while True:
                b = f.read(block)
                if not b:
                    break
                g.update(b)
    except OSError as err:
        if errors:
            raise err
        return None
    h = g.hexdigest()
    del g
    return h


def print_error(message, error=None, quit=True):
    print(message, file=stderr)
    if error is not None:
        print(format_exc(limit=3), file=stderr)
    if quit:
        exit(1)
    return False


def run(command, shell=False, wait=None, errors=True):
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
            return _ProcessThread(cmd, shell).start()
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
        if not errors:
            return None
        if isinstance(err, OSError):
            raise err
        raise OSError(err) from err
    finally:
        del cmd
    if time is None and wait is None:
        ret = out.returncode
        del out
        del time
        if not errors:
            return ret == 0
        if ret == 0:
            return True
        raise OSError(f'Process "{command}" exit code was non-zero ({ret})')
    output = out.stdout
    del out
    del time
    if output is None or len(output) == 0:
        return None
    if output[len(output) - 1] == "\n":
        output = output[: len(output) - 1]
    return output


def write(path, data, binary=False, append=False, perms=None, errors=True):
    if not isinstance(path, str):
        if errors:
            raise OSError('"path" must be a String')
        return False
    d = dirname(path)
    if not exists(d):
        try:
            makedirs(d, exist_ok=True)
        except OSError as err:
            if errors:
                raise err
        return False
    del d
    m = ("ab" if binary else "a") if append else ("wb" if binary else "w")
    try:
        with open(path, m) as f:
            if data is None:
                f.write(bytes() if binary else str())
            elif isinstance(data, str):
                if binary:
                    f.write(data.encode("UTF-8"))
                else:
                    f.write(data)
            else:
                s = str(data)
                if binary:
                    f.write(s.encode("UTF-8"))
                else:
                    f.write(s)
                del s
            f.flush()
        if isinstance(perms, int):
            chmod(path, perms, follow_symlinks=True)
    except (OSError, UnicodeEncodeError) as err:
        if errors:
            raise err
        return False
    finally:
        del m
    return True


def write_json(path, obj, indent=None, sort=False, perms=None, errors=True):
    if obj is None:
        if errors:
            raise OSError('"obj" cannot be None')
        return False
    try:
        d = dumps(obj, indent=indent, sort_keys=sort)
    except (TypeError, JSONDecodeError, OverflowError) as err:
        if errors:
            raise OSError(err)
        return False
    try:
        return write(path, d, False, False, perms, errors)
    except OSError as err:
        if errors:
            raise err
    finally:
        del d
    return False


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
