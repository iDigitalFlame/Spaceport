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

# exec.py
#   Python execution-based utility functions.

from os import environ, kill
from lib.util.file import expand
from signal import SIGINT, SIGKILL
from shlex import split as shell_split, join
from subprocess import Popen, SubprocessError, DEVNULL, PIPE


def stop(proc):
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
        proc.send_signal(SIGKILL)
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
    try:
        proc.wait(timeout=1)
    except (OSError, SubprocessError):
        pass
    return None


def split(val, single=False):
    if not isinstance(val, (str, list, tuple)):
        return None
    if len(val) == 0:
        return None if single else list()
    if isinstance(val, str):
        r = shell_split(expand(val))
        if single:
            return r
        return [r]
    o = list()
    for i in val:
        if isinstance(i, (list, tuple)):
            if len(i) == 0:
                continue
            r = list()
            for v in i:
                if not isinstance(v, str) or len(v) == 0:
                    continue
                r.append(expand(v))
            if single:
                o.append(join(r))
            else:
                o.append(r)
            del r
            continue
        if not isinstance(i, str) or len(i) == 0:
            continue
        if single:
            o.append(expand(i))
        else:
            o.append(shell_split(expand(i)))
    if single and len(o) == 0:
        return None
    return o


def nulexec(cmd, wait=False, timeout=5, cwd=None, ret=False, errors=True):
    return run(cmd, wait, timeout, cwd, ret, errors, False)


def run(cmd, wait=False, timeout=5, cwd=None, ret=False, errors=True, out=True):
    if isinstance(cmd, str):
        if len(cmd) == 0:
            if not errors:
                return None
            raise OSError("command cannot be empty")
        c = shell_split(cmd)
    elif isinstance(cmd, tuple):
        c = list(cmd)
    elif not isinstance(cmd, list):
        if not errors:
            return None
        raise OSError("command must be a string or list")
    else:
        c = cmd
    if out and not wait:
        p, t = PIPE, True
    else:
        p, t = DEVNULL, False
    try:
        r = Popen(
            c,
            cwd=cwd,
            env=environ,
            text=t,
            shell=False,
            stdin=DEVNULL,
            stdout=p,
            stderr=p,
            close_fds=True,
            universal_newlines=t,
        )
    except OSError as err:
        if not errors:
            return None
        raise err
    except (TypeError, ValueError, SubprocessError) as err:
        if not errors:
            return None
        raise OSError(err)
    finally:
        del c, p, t
    if not wait:
        return r
    try:
        e = r.wait(timeout)
        if ret:
            return e
        del e
    except OSError as err:
        if not errors:
            return None
        raise err
    except SubprocessError as err:
        if not errors:
            return None
        raise OSError(err)
    finally:
        if r.poll() is None:
            stop(r)
        del r
    return None
