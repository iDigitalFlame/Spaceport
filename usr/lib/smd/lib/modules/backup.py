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

# Module: System/Backup
#   Creates system Backups using common Linux utilities. Backups can be scheduled
#   and run in the background without much impact to the Session.

from glob import glob
from shutil import rmtree
from threading import Event
from uuid import uuid4, UUID
from base64 import b64encode
from typing import NamedTuple
from datetime import datetime
from signal import SIGSTOP, SIGCONT, SIGUSR1
from lib.util.exec import nulexec, split, stop
from socket import socket, AF_INET, SOCK_STREAM
from lib.structs import Message, Storage, as_error
from lib.util import num, nes, cancel_nul, boolean, fnv32
from subprocess import DEVNULL, Popen, PIPE, SubprocessError
from os.path import isabs, isdir, exists, isfile, getsize, basename, getctime
from lib.util.file import read, read_json, write_json, info, write, remove_file
from os import chmod, urandom, remove, makedirs, statvfs, environ, set_blocking
from lib.constants.files import BACKUP_RESTORE_SCRIPT, BACKUP_RESTORE_SCRIPT_NO_KEY
from lib.constants.config import (
    BACKUP_STATE,
    BACKUP_HOSTS,
    CONFIG_BACKUP,
    BACKUP_EXCLUDE,
    BACKUP_TIMEOUT,
    BACKUP_KEY_SIZE,
    BACKUP_STATE_DIR,
    BACKUP_READ_TIME,
    BACKUP_WAIT_TIME,
    BACKUP_DEFAULT_DIR,
    BACKUP_BATTERY_PATH,
    BACKUP_DEFAULT_PORT,
)
from lib.constants import (
    EMPTY,
    MSG_PRE,
    NEWLINE,
    MSG_USER,
    MSG_POST,
    MSG_STATUS,
    MSG_UPDATE,
    HOOK_POWER,
    MSG_ACTION,
    MSG_CONFIG,
    HOOK_BACKUP,
    HOOK_LOCKER,
    BACKUP_SIZES,
    HOOK_SUSPEND,
    HOOK_SHUTDOWN,
    HOOK_HIBERNATE,
    BACKUP_STATE_DONE,
    LOCKER_TYPE_BACKUP,
    BACKUP_STATE_NAMES,
    BACKUP_STATE_ERROR,
    BACKUP_STATE_KEYGEN,
    BACKUP_STATE_WAITING,
    BACKUP_STATE_PACKING,
    BACKUP_STATE_PRE_CMD,
    BACKUP_STATE_COMPRESS,
    BACKUP_STATE_NO_KEYGEN,
    BACKUP_STATE_UPLOADING,
    BACKUP_STATE_HASHING_P1,
    BACKUP_STATE_HASHING_P2,
    BACKUP_STATE_ENCRYPT_COMPRESS,
)

HOOKS_SERVER = {
    HOOK_POWER: "BackupServer.hook",
    HOOK_BACKUP: "BackupServer.control",
    HOOK_SUSPEND: "BackupServer.hook",
    HOOK_SHUTDOWN: "BackupServer.hook",
    HOOK_HIBERNATE: "BackupServer.hook",
}


def _size(size):
    if size < 1024.0:
        return f"{float(abs(size)):3.1f}B"
    s = size / 1024.0
    for i in BACKUP_SIZES:
        if abs(s) < 1024.0:
            return f"{float(abs(s)):3.1f}{i}B"
        s /= 1024.0
    return f"{float(abs(s)):.1f}YB"


def _time(delta):
    t = delta.total_seconds()
    if t < 60:
        return f"{round(t)}s"
    h = round(t // 3600)
    t -= h * 3600
    m = round(t // 60)
    s = round(t - (m * 60))
    if h == 0:
        return f"{m}m" if s == 0 else f"{m}m {s}s"
    if m == 0:
        return f"{h}hr" if s == 0 else f"{h}hr {s}s"
    return f"{h}hr {m}m" if m > 0 and s == 0 else f"{h}hr {m}m {s}s"


def _on_battery(force=False):
    return force or read(BACKUP_BATTERY_PATH, errors=False, strip=True) == "1"


def _output_strip(v, add=None):
    if isinstance(v, (bytes, bytearray)):
        s = v.decode("UTF-8", "ignore")
    elif not isinstance(v, str):
        if nes(add):
            return add
        return ""
    else:
        s = v.strip()
    if len(s) == 0:
        if nes(add):
            return add
        return EMPTY
    if NEWLINE not in s:
        if ": Removing leading" in s:
            if nes(add):
                return nes
            return EMPTY
        if nes(add):
            s += f";{add}"
        return s
    if s.count(NEWLINE) == 1 and s[-1] == NEWLINE:
        if ": Removing leading" in s:
            if nes(add):
                return nes
            return EMPTY
        if nes(add):
            return s[:-1] + f";{add}"
        return s[:-1]
    r = list()
    for i in s.split(NEWLINE):
        if ": Removing leading" in s:
            continue
        n = i.strip()
        if len(n) > 0:
            r.append(n)
        del n
    o = "; ".join(r)
    del r, s
    if nes(add):
        o += f";{add}"
    return o


def _match_path_or_id(v, plan):
    if not nes(v):
        return False
    if len(v) == 10 and v[0] == "P":
        return plan.id == v
    if plan.path[-1] == "/" and v[-1] != "/":
        return plan.path[0:-1] == v
    if plan.path[-1] != "/" and v[-1] == "/":
        return plan.path == v[0:-1]
    return plan.path == v


class Plan(object):
    __slots__ = (
        "id",
        "dir",
        "key",
        "keep",
        "uuid",
        "path",
        "wait",
        "debug",
        "upload",
        "exclude",
        "cmd_pre",
        "cmd_post",
        "schedule",
        "description",
    )

    def __init__(self, data):
        self.dir = data.get("dir")
        if nes(self.dir):
            if not isabs(self.dir):
                raise ValueError(f'plan "path" "{self.dir}" must be a full path')
        self.path = data.get("path")
        if not nes(self.path):
            raise ValueError('plan "path" cannot be missing or empty')
        if self.path[-1] != "/":
            self.path = f"{self.path}/"
        if not isabs(self.path):
            raise ValueError(f'plan "path" "{self.path}" must be a full path')
        self.wait = data.get("wait", BACKUP_WAIT_TIME)
        if not isinstance(self.wait, int) or self.wait < 0:
            raise ValueError(
                'plan "wait" must be a positive number greater than or equal to zero'
            )
        self.schedule, self.key = Schedule(data.get("schedule")), data.get("public_key")
        if nes(self.key):
            if not isabs(self.key):
                raise ValueError('plan "public_key" must be a full path')
        self.exclude = data.get("exclude")
        if self.exclude is not None and not isinstance(self.exclude, list):
            raise ValueError('plan "exclude" must be a list')
        u = data.get("upload")
        if isinstance(u, dict) and len(u) > 0:
            self.upload = Upload(u)
        elif isinstance(u, bool) and not u:
            self.upload = Upload(None)
        elif u is not None and not isinstance(u, dict):
            raise ValueError('plan "upload" must be an object or false')
        else:
            self.upload = None
        self.uuid = data.get("uuid")
        if not nes(self.uuid):
            self.uuid = str(uuid4())
            data["uuid"] = self.uuid
        else:
            try:
                UUID(self.uuid)
            except ValueError:
                raise ValueError(f'plan "uuid" "{self.uuid}" is invalid')
        del u
        self.id = f"P{hex(fnv32(self.uuid))[2:].zfill(9)}"
        self.keep = data.get("keep", False)
        if isinstance(self.keep, int) and self.keep <= 0:
            self.keep = False
        elif not isinstance(self.keep, (bool, int)):
            self.keep = boolean(self.keep)
        self.debug = boolean(data.get("debug"))
        self.description = data.get("description")
        self.cmd_pre, self.cmd_post = data.get("command_pre"), data.get("command_post")

    def check(self):
        if nes(self.dir) and not isdir(self.dir):
            # NOTE(dij): We allow Backups with a potential non-existsant dir with
            #            a pre-run command as it might create the dir. If the
            #            command fails, the backup won't run anyway.
            if self.cmd_pre is not None:
                return
            raise ValueError(
                f'plan "dir" "{self.dir}" does not exist or is not a directory'
            )
        if not isdir(self.path):
            raise ValueError(
                f'plan "path" "{self.path}" does not exist or is not a directory'
            )
        if nes(self.key):
            info(self.key).only(file=True).check(0o01377, 0, 0)

    def __str__(self):
        return f"{self.uuid}/[{self.id}]"

    def incremental(self, state, force_full):
        if self.uuid not in state:
            # NOTE(dij): If no entry exists, do a full backup.
            state[self.uuid] = {"last": None, "size": None, "error": False, "count": 0}
            return False
        c = state[self.uuid].get("count", 0)
        if not isinstance(c, int) or c < 0:
            c = 0
        if force_full:
            f, c = True, 0
        else:
            f = self.schedule.is_full(c)
            c = 0 if f else c + 1
        state[self.uuid]["count"] = c
        del c
        return not f


class Queue(object):
    __slots__ = ("_map", "_entries")

    def __init__(self):
        self._map = dict()
        self._entries = list()

    def _pop(self):
        if len(self._entries) == 0:
            return None
        v = self._entries.pop(0)
        if v is not None:
            del self._map[v.uuid]
        return v

    def clear(self):
        self._map.clear()
        self._entries.clear()

    def is_empty(self):
        return len(self._entries) == 0

    def remove(self, path):
        if len(self._entries) == 0:
            return False
        v = None
        for i in self._entries:
            if not _match_path_or_id(path, i):
                continue
            v = i
            break
        if v is None:
            return None
        self._entries.remove(v)
        del self._map[v.uuid]
        return v

    def __contains__(self, value):
        if nes(value):
            return value in self._map
        return isinstance(value, Plan) and value.uuid in self._map

    def _add(self, plan, first=False):
        if plan.uuid in self._map:
            return
        self._map[plan.uuid] = True
        if first:
            self._entries.insert(0, plan)
        else:
            self._entries.append(plan)

    def next(self, server, state, path, force):
        d = read_json(state, errors=False)
        if not isinstance(d, dict):
            server.warning(
                "[m/backup]: Cannot read/parse the Backup state file, using empty state!"
            )
            d = dict()
        n = datetime.now()
        while len(self._entries) > 0:
            x = self._pop()
            if x is None:
                break
            try:
                x.check()
                if x.upload:
                    x.upload.check()
            except (OSError, ValueError) as err:
                server.warning(
                    f"[m/backup]: Skipping Plan {x} ({x.path}) as check failed!", err
                )
                continue
            if _match_path_or_id(path, x):
                return (x, d)
            if force or x.uuid not in d:
                return (x, d)
            t = d[x.uuid].get("last")
            if not nes(t):
                return (x, d)
            v = n - datetime.fromisoformat(t)
            try:
                if v.total_seconds() > x.wait:
                    return (x, d)
            except ValueError:
                pass
            del t
            if d[x.uuid].get("error", False):
                return (x, d)
            server.debug(
                f"[m/backup]: Skipping Backup {x} as the last successful run was less than "
                f"{_time(v)} ago."
            )
            del x, v
        del n
        return (None, d)

    def add_plans(self, server, plans, path, current):
        if len(plans.entries) == 0:
            return list()
        r = current is not None and current.running()
        w, c = datetime.now().weekday(), 0
        for i in plans.entries:
            server.debug(f'[m/backup/add_plans]: Evaluating Plan "{i.id}"..')
            if r and i.id == current.id:
                # NOTE(dij): Don't re-add the running backup.
                server.debug(
                    f'[m/backup/add_plans]: Skipping currently running Plan "{i.id}".'
                )
                continue
            if _match_path_or_id(path, i):
                # NOTE(dij): If we specify a matched entry, add it first!
                #            This feels sorta hacky, but it's an easier way to
                #            handle requested Plans then interrupting the call to
                #            "next" as it does some checks.
                self._add(i, True)
                c += 1
                server.debug(
                    f'[m/backup/add_plans]: Adding Plan "{i.id}" that matched Path or ID "{path}".'
                )
                continue
            if nes(path):
                continue
            if not i.schedule.runnable(w):
                server.debug(
                    f'[m/backup/add_plans]: Skipping non-runnable Plan "{i.id}".'
                )
                continue
            self._add(i)
            c += 1
            server.debug(f'[m/backup/add_plans]: Adding runnable Plan "{i.id}".')
        del w
        server.debug(f"[m/backup/add_plans]: Added {c} Plans to queue.")
        return c, r


class Multi(object):
    __slots__ = ("_cmds", "_proc", "_break")

    def __init__(self, cmds, stop_error=True):
        if not isinstance(cmds, (list, tuple)) or len(cmds) == 0:
            raise OSError("cmd list must be a non-empty list or tuple")
        self._break = stop_error
        self._cmds = cmds
        self._proc = self._next()

    def pid(self):
        return self._proc.pid

    def kill(self):
        self._cmds.clear()
        self._proc.kill()

    def poll(self):
        # NOTE(dij): We'll use the polling scheduler to advance the array.
        #            If the current process completes, start the next one until
        #            there's no more left.
        r = self._proc.poll()
        if r is None:
            # Proc is still running..
            return None
        if (r is not None and len(self._cmds) == 0) or (
            self._break and isinstance(r, int) and r != 0
        ):
            # We're empty! Say we're done or if we hit a non-zero error while
            # break is True.
            return r
        try:
            # Try next proc.
            self._proc = self._next()
        except OSError:
            # If we fail, bail!
            return r
        # We don't check the output of the new proc yet, so we don't break on
        # processes that exit immediately. We do this instead of looping, which
        # while has a small time overhead, it prevents keeping the event loop busy.
        return None

    def stop(self):
        self._cmds.clear()
        stop(self._proc)

    def _next(self):
        v = nulexec(self._cmds.pop(0))
        nulexec(
            ["/usr/bin/renice", "-n", "15", "--pid", f"{v.pid}"],
            wait=True,
            errors=False,
        )
        nulexec(
            ["/usr/bin/ionice", "-c", "3", "-p", f"{v.pid}"],
            wait=True,
            errors=False,
        )
        return v

    def output(self):
        if self._proc is None:
            return (0, "", "")
        return (self._proc.wait(), "", "")

    def terminate(self):
        self._cmds.clear()
        self._proc.terminate()

    def wait(self, timeout=None):
        return self._proc.wait(timeout)

    def send_signal(self, signal):
        self._proc.send_signal(signal)


class Plans(object):
    __slots__ = ("dir", "key", "upload", "entries", "storage", "updated")

    def __init__(self, file):
        self.updated, self.entries = False, list()
        self.storage = Storage(file, load=True)
        if len(self.storage) == 0:
            self.dir = BACKUP_DEFAULT_DIR
            self.key, self.upload, self.storage = None, None, None
            return
        p = self.storage.get("plans")
        if p is not None and not isinstance(p, list):
            raise ValueError(f'"plans" value should be a list (not "{type(p)}")')
        if p is None or len(p) == 0:
            self.dir = BACKUP_DEFAULT_DIR
            self.key, self.upload, self.storage = None, None, None
            return
        for i in p:
            if not isinstance(i, dict):
                raise ValueError('"plans" entries must be object types')
            if "uuid" not in i and not self.updated:
                self.updated = True
            self.entries.append(Plan(i))
        del p
        u = self.storage.get("upload")
        self.dir = self.storage.get("dir", BACKUP_DEFAULT_DIR)
        if not nes(self.dir):
            self.dir = BACKUP_DEFAULT_DIR
        self.upload = Upload(u) if isinstance(u, dict) and len(u) > 0 else None
        del u
        self.key = self.storage.get("public_key")
        if not nes(self.key):
            return
        if not isabs(self.key):
            raise ValueError('plan "public_key" value must be a full path')
        info(self.key).only(file=True).check(0o01377, 0, 0)

    def save(self, server):
        if self.storage is None:
            return
        server.debug("[m/backup]: Saving Backup config file.")
        try:
            self.storage.save()
        except OSError as err:
            server.error("[m/backup]: Cannot write to the Backup config file!", err)

    def status(self, server, queue, current):
        try:
            s = read_json(BACKUP_STATE, errors=False)
            if not isinstance(s, dict):
                s = dict()
        except OSError as err:
            server.warning("[m/backup]: Cannot read the Backup state file!", err)
            s = dict()
        r, c = list(), current is not None and current.running()
        for i in self.entries:
            if c and current.id == i.id:
                try:
                    v = BACKUP_STATE_NAMES[current._state].title()
                except IndexError:
                    v = "Invalid"
                if current.paused():
                    x = "W"
                else:
                    x = "R"
            else:
                v = EMPTY
                if i.uuid in queue:
                    x = "Q"
                else:
                    x = EMPTY
            if i.uuid not in s:
                r.append(
                    {
                        "id": i.id,
                        "last": None,
                        "size": None,
                        "uuid": i.uuid,
                        "path": i.path,
                        "full": False,
                        "error": None,
                        "state": x,
                        "status": v,
                        "description": i.description,
                    }
                )
                continue
            f = s[i.uuid].get("count")
            r.append(
                {
                    "id": i.id,
                    "last": s[i.uuid].get("last"),
                    "size": s[i.uuid].get("size"),
                    "uuid": i.uuid,
                    "path": i.path,
                    "full": False if isinstance(f, int) and f > 0 else True,
                    "error": boolean(s[i.uuid].get("error")),
                    "state": x,
                    "status": v,
                    "description": i.description,
                }
            )
            del v, x, f
        del c, s
        return r


class Upload(object):
    __slots__ = ("key", "port", "_host", "_user")

    def __init__(self, data):
        if data is None:
            self.key, self._host, self.port, self._user = None, None, None, None
            return
        self._host = data.get("host")
        if not nes(self._host):
            raise ValueError('upload "host" must be a non-empty string')
        self._host, self._user = Upload._split_user(self._host, data.get("user"))
        if not nes(self._user):
            raise ValueError('upload "user"  must be a non-empty string')
        self._host, self.port = Upload._split_port(
            self._host, data.get("port", BACKUP_DEFAULT_PORT)
        )
        if not isinstance(self.port, int) or self.port <= 0 or self.port >= 0xFFFF:
            raise ValueError(
                'upload "port" must be a non-zero positive number inside [1-65535]'
            )
        if len(self._host) == 0:
            raise ValueError('upload "host" must be a non-empty string')
        data["host"], data["user"], data["port"] = self._host, self._user, self.port
        self.key = data.get("key")
        if nes(self.key) and not isabs(self.key):
            raise ValueError('upload "key" must be a full path')

    def host(self):
        return f"{self._user}@{self._host}" if nes(self._user) else self._host

    def check(self):
        s = socket(AF_INET, SOCK_STREAM)
        try:
            s.settimeout(5)
            s.connect((self._host, self.port))
        except OSError:
            pass
        else:
            if nes(self.key):
                info(self.key).only(file=True).check(0o01377, 0, 0)
            return True
        finally:
            s.close()
            del s
        return False

    def valid(self):
        return nes(self._host) and isinstance(self.port, int) and 0 < self.port < 0xFFFF

    def __bool__(self):
        return self.valid()

    @staticmethod
    def _split_user(s, other):
        i = s.find("@")
        if i <= 0 or i + 1 > len(s):
            return (s, other)
        return (s[0:i], s[i + 1 :])

    @staticmethod
    def _split_port(s, other):
        i, b = s.rfind(":"), s.rfind("]")
        if i <= 1 and b <= 1:
            return (s, other)
        if i + 1 > len(s):
            return (s, other)
        if i > 1 and i > b:
            try:
                return (s[0:i], num(s[i + 1 :], False))
            except ValueError:
                raise ValueError(f'host "{s}" is invalid')
        del i, b
        return (s, other)


class Backup(object):
    __slots__ = (
        "id",
        "_key",
        "_dir",
        "_plan",
        "_proc",
        "_last",
        "_path",
        "_time",
        "_size",
        "_debug",
        "_state",
        "_cancel",
        "_paused",
        "_upload",
        "_reader",
        "_timeout",
        "_increment",
    )

    def __init__(self, work, key, upload, plan, inc):
        self.id = plan.id
        self._key = plan.key if nes(plan.key) else key
        self._dir = plan.dir if nes(plan.dir) else work
        self._plan = plan
        self._proc = None
        self._last = None
        self._path = (
            f'{self._dir}/backup-{plan.id}-{datetime.now().strftime("%Y%m%d-%H%M")}'
        )
        self._time = None
        self._size = None
        self._debug = plan.debug
        self._state = BACKUP_STATE_WAITING
        self._cancel = Event()
        self._paused = Event()
        self._reader = None
        self._upload = plan.upload if plan.upload is not None else upload
        self._timeout = None
        self._increment = inc

    def paused(self):
        return self._paused.is_set()

    def running(self):
        return not self._cancel.is_set()

    def __str__(self):
        return f"{self._plan.path} ({self.id})"

    def start(self, server):
        if self._upload and not self._upload.check():
            raise ConnectionError()
        if isdir(self._path):
            try:
                rmtree(self._path)
            except OSError as err:
                raise OSError(f'cannot remove directory "{self._path}": {err}')
        try:
            makedirs(BACKUP_STATE_DIR, exist_ok=True, mode=0o0750)
        except OSError as err:
            raise OSError(f'cannot make directory "{BACKUP_STATE_DIR}": {err}')
        server.info(f"[m/backup/job/{self.id}] Starting Backup Job {self}..")
        server.notify("Backup Status", f"Staring Backup {self}!", "yed")
        self._next(server)

    def resume(self, server):
        if self._proc is not None and self._proc.poll() is None:
            try:
                self._proc.send_signal(SIGCONT)
            except (SubprocessError, OSError) as err:
                return server.error(
                    f"[m/backup/job/{self.id}] Cannot resume Backup {self}!", err
                )
        server.info(f"[m/backup/job/{self.id}] Resuming Backup {self}.")
        self._paused.clear()
        return True

    def suspend(self, server):
        if self._proc is not None and self._proc.poll() is None:
            try:
                self._proc.send_signal(SIGSTOP)
            except (SubprocessError, OSError) as err:
                return server.error(
                    f"[m/backup/job/{self.id}] Cannot suspend Backup {self}!", err
                )
        server.info(f"[m/backup/job/{self.id}] Suspending Backup {self}.")
        self._paused.set()
        return True

    def _cleanup(self, server):
        # NOTE(dij): Return value is flipped
        #             True  - delete
        #             False - don't delete
        if not self._plan.keep:
            return self._upload.valid()
        if isinstance(self._plan.keep, bool):
            return not self._plan.keep
        if not isinstance(self._plan.keep, int) or self._plan.keep <= 0:
            return self._upload.valid()
        server.debug(
            f'[m/backup/job/{self.id}]: Validating keep value of "{self._plan.keep}"..'
        )
        g = glob(f"{self._dir}/backup-{self._plan.id}-*.tar", recursive=False)
        g.sort(key=lambda f: getctime(f))
        g.reverse()
        k = self._plan.keep + 1
        server.debug(f"[m/backup/job/{self.id}]: Keep {k}, found {len(g)}.")
        if len(g) <= k:
            return False
        x = g[k:]
        for i in x:
            server.debug(f'[m/backup/job/{self.id}]: Removing old backup file "{i}".')
            try:
                remove(i)
            except OSError as err:
                server.error(
                    f'[m/backup/job/{self.id}]: Cannot delete old Backup file "{i}"!',
                    err,
                )
        del k
        server.debug(
            f"[m/backup/job/{self.id}]: Removed {len(x)} old backup files, keeping {(len(g)-len(x))-1}."
        )
        del x, g
        return False

    def _step_read(self, server):
        server.debug(f"[m/backup/job/{self.id}]: Attempting to read process output..")
        server.cancel(self._reader)
        if (
            self._proc is None
            or self._cancel.is_set()
            or self._proc.poll() is not None
            or (
                self._state != BACKUP_STATE_PACKING
                and self._state != BACKUP_STATE_COMPRESS
                and self._state != BACKUP_STATE_UPLOADING
                and self._state != BACKUP_STATE_ENCRYPT_COMPRESS
            )
        ):
            return
        if self._paused.is_set():
            self._reader = server.task(BACKUP_READ_TIME, self._step_read, (server,))
            return server.debug(
                f"[m/backup/job/{self.id}]: Skipping read for paused process."
            )
        if self._state != BACKUP_STATE_UPLOADING:
            try:
                if self._state == BACKUP_STATE_ENCRYPT_COMPRESS:
                    self._proc.p1.send_signal(SIGUSR1)
                else:
                    self._proc.send_signal(SIGUSR1)
            except OSError as err:
                server.debug(
                    f"[m/backup/job/{self.id}]: Cannot send a SIGUSR1 signal to the process!",
                    err,
                )
        try:
            o = _output_strip(
                self._proc.read(8192, self._state != BACKUP_STATE_UPLOADING)
            )
        except OSError as err:
            server.debug(f"[m/backup/job/{self.id}]: Cannot read process output!", err)
        else:
            if len(o) > 0:
                server.info(
                    f"[m/backup/job/{self.id}]: Current process output status: [{o}]"
                )
            del o
        self._reader = server.task(BACKUP_READ_TIME, self._step_read, (server,))

    def _step_pack(self, server):
        if not self._update(server, BACKUP_STATE_PACKING):
            return
        if not self._check_space(server, "data.pak"):
            return self._update(server, BACKUP_STATE_ERROR)
        server.debug(f"[m/backup/job/{self.id}]: Starting the [Packing] step..")
        try:
            self._exec_and_watch(
                server,
                [
                    "/bin/tar",
                    "-c",
                    "--sparse",
                    "--no-acls",
                    "--restrict",
                    "--no-xattrs",
                    "--recursion",
                    "--no-selinux",
                    "--force-local",
                    "--totals=USR1",
                    "--remove-files",
                    "--one-file-system",
                    "-f",
                    f"{self._path}.tar",
                    f"--directory={self._dir}",
                    basename(self._path),
                ],
                read=True,
            )
        except OSError as err:
            server.error(
                f"[m/backup/job/{self.id}]: Cannot start the packing process!", err
            )
            return self._update(server, BACKUP_STATE_ERROR)

    def save(self, server, file):
        try:
            s = read_json(file, errors=True)
        except OSError as err:
            server.warning(
                f"[m/backup/job/{self.id}]: Cannot read the Backup state file!", err
            )
            s = dict()
        if not isinstance(s, dict):
            s = dict()
        if self._plan.uuid in s:
            c = s[self._plan.uuid].get("count", 0)
            if not isinstance(c, int) or c < 0:
                c = 0
        else:
            c = 0
        n = {
            "size": self._size,
            "last": datetime.now().isoformat(),
            "count": c + 1,
            "error": self._state == BACKUP_STATE_ERROR,
        }
        s[self._plan.uuid] = n
        try:
            write_json(BACKUP_STATE, s, perms=0o640)
        except OSError as err:
            server.warning(
                f"[m/backup/job/{self.id}]: Cannot save the Backup state file!", err
            )
        else:
            server.debug(
                f'[m/backup/job/{self.id}]: Saved the data "{n}" to the Backup state file!'
            )
        del s, c, n
        return self._state == BACKUP_STATE_DONE

    def _check_proc(self, server):
        if self._proc is None:
            return True
        try:
            n, self._last, e = self._proc.output()
        except OSError as err:
            server.error(f"[m/backup/job/{self.id}]: Cannot read process output!", err)
            return self._update(server, BACKUP_STATE_ERROR)
        # NOTE(dij): Packing and compress don't seem to throw these exit codes
        #            anymore during normal operations, but let's keep them here
        #            as tar/openssl will bail with a different code if something
        #            serious fails.
        if BACKUP_STATE_NO_KEYGEN < self._state <= BACKUP_STATE_COMPRESS and n <= 1:
            return True
        if n == 0:
            return True
        if len(e) == 0:
            server.error(
                f"[m/backup/job/{self.id}]: Process exited with a non-zero exit code ({n})!"
            )
            return self._update(server, BACKUP_STATE_ERROR)
        server.error(
            f"[m/backup/job/{self.id}]: Process exited with a non-zero exit code ({n}): {e}!"
        )
        del n, e
        return self._update(server, BACKUP_STATE_ERROR)

    def _step_keygen(self, server):
        if not self._update(server, BACKUP_STATE_KEYGEN):
            return
        if not nes(self._key):
            self.server.info(
                f"[m/backup/job/{self.id}]: Skipping encryption step with no keyfile! "
                "BACKUPS WILL NOT BE ENCRYPTED!"
            )
            self._key = None
            self._update(server, BACKUP_STATE_NO_KEYGEN)
            return self._next(server)
        if not exists(self._key):
            self.server.warning(
                f'[m/backup/job/{self.id}]: Skipping encryption step as the public key "{self._key}" '
                "does not exist! BACKUPS WILL NOT BE ENCRYPTED!"
            )
            self._key = None
            self._update(server, BACKUP_STATE_NO_KEYGEN)
            return self._next(server)
        server.debug(f"[m/backup/job/{self.id}]: Starting the [Key Generation] step..")
        try:
            x = b64encode(urandom(BACKUP_KEY_SIZE)).decode("UTF-8")
            self._exec_and_watch(
                server,
                [
                    "/bin/openssl",
                    "pkeyutl",
                    "-encrypt",
                    "-pubin",
                    "-in",
                    "-",
                    "-inkey",
                    self._key,
                    "-out",
                    f"{self._path}/data.pem",
                ],
                x,
                x,
            )
        except OSError as err:
            server.error(
                f"[m/backup/job/{self.id}]: Cannot start the Key Generation process!",
                err,
            )
            self._update(server, BACKUP_STATE_ERROR)
        finally:
            x = None
            del x

    def _step_upload(self, server):
        if not self._update(server, BACKUP_STATE_UPLOADING):
            return
        f = f"{self._path}.tar"
        if not self._upload.valid():
            server.info(f"[m/backup/job/{self.id}]: Skipping Upload with no target!")
            return self._next(server, f)
        if not exists(BACKUP_HOSTS):
            server.error(
                f"[m/backup/job/{self.id}]: Unable to upload Backup, the known hosts file "
                f'"{BACKUP_HOSTS}" is missing! Please execute "ssh -o UserKnownHostsFile=file {self._upload.host()}" '
                f'to generate the file and copy it to "{BACKUP_HOSTS}".'
            )
            return self._update(server, BACKUP_STATE_ERROR)
        server.debug(f"[m/backup/job/{self.id}]: Starting the [Upload] step..")
        o = f"/bin/ssh -o VisualHostKey=no -o UserKnownHostsFile={BACKUP_HOSTS} -p {self._upload.port}"
        if nes(self._upload.key):
            try:
                chmod(self._upload.key, 0o0400, follow_symlinks=True)
            except OSError:
                pass
            o = f"{o} -i {self._upload.key}"
        try:
            self._exec_and_watch(
                server,
                [
                    "/bin/rsync",
                    "--sparse",
                    "--progress",
                    "--compress",
                    "--recursive",
                    "--safe-links",
                    "--open-noatime",
                    "--human-readable",
                    "--one-file-system",
                    "-e",
                    o,
                    f,
                    f"{self._upload.host()}:",
                ],
                add=f,
                read=True,
            )
        except OSError as err:
            server.error(
                f"[m/backup/job/{self.id}]: Cannot start the upload process!",
                err,
            )
            return self._update(server, BACKUP_STATE_ERROR)
        finally:
            del o, f

    def _stop(self, server, force):
        if self._cancel.is_set():
            return
        self._cancel.set()
        self._paused.clear()
        server.debug(f"[m/backup/job/{self.id}]: Cleaning up..")
        self._timeout = cancel_nul(server, self._timeout)
        stop(self._proc, False)
        try:
            rmtree(self._path, ignore_errors=True)
        except OSError as err:
            server.error(
                f'[m/backup/job/{self.id}]: Cannot remove directory "{self._path}"!',
                err,
            )
        if isdir(self._path):
            server.error(
                f'[m/backup/job/{self.id}]: Cannot remove directory "{self._path}"!'
            )
        if force or self._state != BACKUP_STATE_UPLOADING:
            self._state = BACKUP_STATE_ERROR
            remove_file(f"{self._path}.tar")
        else:
            self._state = BACKUP_STATE_DONE
        # NOTE(dij): We run this after so we can unmount anything used.
        try:
            self._start_post_cmd(server)
        except Exception as err:
            server.error(f"[m/backup/job/{self.id}]: Error during post-cmd!", err)
        finally:
            server.debug(f"[m/backup/job/{self.id}]: Stop completed.")

    def _step_ec(self, server, key):
        if not self._update(server, BACKUP_STATE_ENCRYPT_COMPRESS):
            return
        server.debug(
            f"[m/backup/job/{self.id}]: Starting the [Compress|Encrypt] step.."
        )
        s = f"{BACKUP_STATE_DIR}/{self._plan.uuid}.db"
        try:
            if not self._increment and isfile(s):
                remove(s)
        except OSError as err:
            server.error(f"[m/backup/job/{self.id}]: Cannot remove state file", err)
            return self._update(server, BACKUP_STATE_ERROR)
        x = [
            "/bin/tar",
            "-c",
            "--zstd",
            "--acls",
            "--sparse",
            "--xattrs",
            "--restrict",
            "--recursion",
            "--no-selinux",
            "--totals=USR1",
            "--warning=no-xdev",
            "--one-file-system",
            "--preserve-permissions",
            "--warning=no-file-ignored",
            "--warning=no-file-changed",
            "--warning=no-file-removed",
            f"--listed-incremental={s}",
            f"--exclude={self._dir}",
            f"--directory={self._plan.path}",
        ]
        for i in BACKUP_EXCLUDE:
            x.append(f"--exclude={i}")
        if isinstance(self._plan.exclude, list) and len(self._plan.exclude) > 0:
            for i in self._plan.exclude:
                x.append(f"--exclude={i}")
        del s
        if self._debug:
            x += ["-v", "-v"]
        x += ["-f", "-", self._plan.path]
        e = environ.copy()
        e["SMD_ENC_KEY"] = key
        server.debug(
            f"[m/backup/job/{self.id}]: Starting the combo compress|encrypt process.."
        )
        try:
            p1 = Popen(x, stdin=DEVNULL, stdout=PIPE, stderr=PIPE, close_fds=True)
            p2 = Popen(
                [
                    "/bin/openssl",
                    "aes-256-ctr",
                    "-bufsize",
                    "16384",
                    "-e",
                    "-salt",
                    "-pbkdf2",
                    "-pass",
                    "env:SMD_ENC_KEY",
                    "-in",
                    "-",
                    "-out",
                    f"{self._path}/data.pak",
                ],
                env=e,
                text=True,
                stdin=p1.stdout,
                stdout=PIPE,
                stderr=PIPE,
                encoding="UTF-8",
                close_fds=True,
                universal_newlines=True,
            )
            p1.stdout.close()
        except OSError as err:
            server.error(
                f"[m/backup/job/{self.id}]: Cannot start the encryption process!",
                err,
            )
            return self._update(server, BACKUP_STATE_ERROR)
        finally:
            del e["SMD_ENC_KEY"]
            del e, x
        self._proc = Dual(p1, p2)
        del p1, p2
        server.debug(
            f"[m/backup/job/{self.id}]: Command started, PID {self._proc.pid()}."
        )
        self._proc.nice()
        server.watch(self._proc, self._next, (server,))
        try:
            set_blocking(self._proc.p1.stderr.fileno(), False)
        except OSError as err:
            server.warning(
                f"[m/backup/job/{self.id}]: Cannot set non-blocking mode for PID {self._proc.pid()}!",
                err,
            )
        else:
            self._reader = server.task(BACKUP_READ_TIME, self._step_read, (server,))

    def _step_pre_cmd(self, server):
        if not self._update(server, BACKUP_STATE_PRE_CMD):
            return
        c = split(
            self._plan.cmd_pre,
            env={
                "BACKUP_ID": self.id,
                "BACKUP_DIR": self._dir,
                "BACKUP_PATH": self._path,
            },
        )
        if c is None:
            server.warning(
                f'[m/backup/job/{self.id}]: Ignoring pre-start command type "{type(self._plan.cmd_pre)}"!'
            )
            return self._next(server)
        if len(c) == 0:
            return self._next(server)
        server.info(f'[m/backup/job/{self.id}]: Executing pre-start command set "{c}".')
        try:
            self._proc = Multi(c)
        except OSError as err:
            server.error(
                f'[m/backup/job/{self.id}]: Cannot start the pre-start command "{c}"!',
                err,
            )
            return self._update(server, BACKUP_STATE_ERROR)
        finally:
            del c
        server.debug(
            f"[m/backup/job/{self.id}]: Pre-start command started, PID {self._proc.pid()}."
        )
        server.watch(self._proc, self._next, (server,))

    def _update(self, server, state):
        if self._cancel.is_set():
            server.info(f"[m/backup/job/{self.id}]: Backup was stopped!")
            self._stop(server, True)
            return False
        p, self._state = self._state, state
        # NOTE(dij): Catch paused state between steps and wait if needed.
        if self._paused.is_set():
            self._paused.wait()
        self._paused.clear()
        server.forward(
            Message(
                HOOK_BACKUP,
                {
                    "type": MSG_UPDATE,
                    "uuid": self._plan.uuid,
                    "prev": p,
                    "state": state,
                },
            )
        )
        del p
        if state == BACKUP_STATE_ERROR:
            return self._stop(server, True)
        return True

    def _step_compress(self, server):
        if not self._update(server, BACKUP_STATE_COMPRESS):
            return
        server.debug(f"[m/backup/job/{self.id}]: Starting the [Compression] step..")
        s = f"{BACKUP_STATE_DIR}/{self._plan.uuid}.db"
        try:
            if not self._increment and isfile(s):
                remove(s)
        except OSError as err:
            server.error(f"[m/backup/job/{self.id}]: Cannot remove state file", err)
            return self._update(server, BACKUP_STATE_ERROR)
        x = [
            "/bin/tar",
            "-c",
            "--zstd",
            "--acls",
            "--sparse",
            "--xattrs",
            "--restrict",
            "--recursion",
            "--no-selinux",
            "--totals=USR1",
            "--warning=no-xdev",
            "--one-file-system",
            "--preserve-permissions",
            "--warning=no-file-ignored",
            "--warning=no-file-changed",
            "--warning=no-file-removed",
            f"--listed-incremental={s}",
            f"--exclude={self._dir}",
            f"--directory={self._plan.path}",
        ]
        for i in BACKUP_EXCLUDE:
            x.append(f"--exclude={i}")
        if isinstance(self._plan.exclude, list) and len(self._plan.exclude) > 0:
            for i in self._plan.exclude:
                x.append(f"--exclude={i}")
        del s
        if self._debug:
            x += ["-v", "-v"]
        x += ["-f", f"{self._path}/data.pak", self._plan.path]
        try:
            self._exec_and_watch(server, x, read=True)
        except OSError as err:
            server.error(
                f"[m/backup/job/{self.id}]: Cannot start the compress process!", err
            )
            return self._update(server, BACKUP_STATE_ERROR)
        finally:
            del x

    def _next(self, server, arg=None):
        server.cancel(self._reader)
        server.cancel(self._timeout)
        if self._time is not None:
            n = datetime.now()
            self._time, d = n, (n - self._time)
            server.debug(f"[m/backup/job/{self.id}]: Execution took {_time(d)}.")
            del n, d
        server.debug(f"[m/backup/job/{self.id}]: State {self._state} entered.. ")
        if self._cancel.is_set():
            stop(self._proc, False)
            server.forward(
                Message(
                    HOOK_LOCKER,
                    {
                        "type": MSG_ACTION,
                        "name": LOCKER_TYPE_BACKUP,
                        "time": False,
                        "force": True,
                    },
                )
            )
            server.forward(
                Message(
                    HOOK_BACKUP,
                    {
                        "type": MSG_UPDATE,
                        "uuid": self._plan.uuid,
                        "state": self._state,
                        "final": True,
                    },
                )
            )
            return server.debug(f"[m/backup/job/{self.id}]: Stop fully completed.")
        if self._cancel.is_set():
            return
        if self._time is None:
            self._time = datetime.now()
        self._timeout = server.task(BACKUP_TIMEOUT, self._step_timeout, (server, False))
        if self._state == BACKUP_STATE_WAITING:
            server.forward(
                Message(
                    HOOK_LOCKER,
                    {
                        "type": MSG_ACTION,
                        "name": LOCKER_TYPE_BACKUP,
                        "time": None,
                        "force": True,
                    },
                )
            )
            if self._plan.cmd_pre is not None:
                return self._step_pre_cmd(server)
        if self._state <= BACKUP_STATE_PRE_CMD:
            try:
                makedirs(self._path, mode=0o0750, exist_ok=True)
            except OSError as err:
                server.error(
                    f'[m/backup/job/{self.id}]: Cannot make Backup directory "{self._path}"!',
                    err,
                )
                return self._stop(server, True)
        if self._proc is not None:
            r = self._check_proc(server)
            stop(self._proc)
            self._proc = None
        else:
            r = True
        server.debug(f"[m/backup/job/{self.id}]: Command output state was {r}.")
        if not r:
            return self._stop(server, True)
        del r
        server.debug(f"[m/backup/job/{self.id}]: Step completed, moving to next step!")
        if self._state == BACKUP_STATE_WAITING:
            return self._step_keygen(server)
        if self._state == BACKUP_STATE_PRE_CMD:
            return self._step_keygen(server)
        if self._state == BACKUP_STATE_NO_KEYGEN:
            return self._step_compress(server)
        if self._state == BACKUP_STATE_KEYGEN:
            return self._step_ec(server, arg)
        if self._state == BACKUP_STATE_COMPRESS:
            return self._step_hash_part1(server)
        if self._state == BACKUP_STATE_ENCRYPT_COMPRESS:
            return self._step_hash_part1(server)
        if self._state == BACKUP_STATE_HASHING_P1:
            return self._step_hash_part2(server)
        if self._state == BACKUP_STATE_HASHING_P2:
            return self._step_pack(server)
        if self._state == BACKUP_STATE_PACKING:
            return self._step_upload(server)
        if self._state == BACKUP_STATE_UPLOADING:
            try:
                self._size = _size(getsize(arg))
            except OSError as err:
                self._size = "U"
                server.error(
                    f'[m/backup/job/{self.id}]: Cannot retrive size of file "{arg}"!',
                    err,
                )
            else:
                if self._upload.valid():
                    server.info(
                        f'[m/backup/job/{self.id}]: Uploaded Backup file "{arg}" ({self._size}) to '
                        f'"{self._upload._host}" successfully!'
                    )
                else:
                    server.info(
                        f'[m/backup/job/{self.id}]: Backup to file "{arg}" ({self._size}) was successful!'
                    )
            if self._cleanup(server):
                try:
                    remove(arg)
                except OSError as err:
                    server.error(
                        f'[m/backup/job/{self.id}]: Cannot remove Backup file "{arg}"!',
                        err,
                    )
        self._stop(server, False)

    def _start_post_cmd(self, server):
        if self._plan.cmd_post is None:
            return self._next(server)
        c = split(
            self._plan.cmd_post,
            env={
                "BACKUP_ID": self.id,
                "BACKUP_DIR": self._dir,
                "BACKUP_PATH": self._path,
            },
        )
        if c is None:
            server.warning(
                f'[m/backup/job/{self.id}]: Ignoring post-backup command type "{type(self._plan.cmd_pre)}"!'
            )
            return self._next(server)
        if len(c) == 0:
            return self._next(server)
        # NOTE(dij): Add a final timeout just in-case.
        self._timeout = server.task(BACKUP_TIMEOUT, self._step_timeout, (server, True))
        server.info(
            f'[m/backup/job/{self.id}]: Executing post-backup command set "{c}".'
        )
        try:
            # NOTE(dij): Don't break on command errors so all commands in the "chain"
            #            complete.
            self._proc = Multi(c, stop_error=False)
        except OSError as err:
            server.error(
                f'[m/backup/job/{self.id}]: Cannot start the post-backup command "{c}"!',
                err,
            )
            return self._next(server)
        finally:
            del c
        server.debug(
            f"[m/backup/job/{self.id}]: Post-backup command started, PID {self._proc.pid()}."
        )
        # NOTE(dij): We're instead going to wait for the post-command to complete
        #            as it might hold up resources and allows our suspend block to
        #            keep alive as long it needs to do it's thing.
        server.watch(self._proc, self._next, (server,))

    def _step_hash_part1(self, server):
        if not self._update(server, BACKUP_STATE_HASHING_P1):
            return
        server.debug(f"[m/backup/job/{self.id}]: Starting the [Hashing] step..")
        try:
            return self._exec_and_watch(
                server, ["/bin/sha256sum", "--binary", f"{self._path}/data.pak"]
            )
        except OSError as err:
            server.error(
                f"[m/backup/job/{self.id}]: Cannot start the hashing process!", err
            )
        return self._update(server, BACKUP_STATE_ERROR)

    def _step_hash_part2(self, server):
        if not self._update(server, BACKUP_STATE_HASHING_P2):
            return
        if not nes(self._last):
            server.error(
                f"[m/backup/job/{self.id}]: Hash process did not return any data!"
            )
            return self._update(server, BACKUP_STATE_ERROR)
        h = self._last.replace(f"*{self._path}/", EMPTY)
        if len(h) == 0:
            server.error(
                f"[m/backup/job/{self.id}]: Hash process did not return valid data!"
            )
            return self._update(server, BACKUP_STATE_ERROR)
        try:
            write(f"{self._path}/data.sum", h)
        except OSError as err:
            server.error(
                f"[m/backup/job/{self.id}]: Cannot write Backup hash data!", err
            )
            return self._update(server, BACKUP_STATE_ERROR)
        i = h.find(" ")
        h, d = h[:i], self._plan.description
        del i
        if not nes(d):
            d = f'Backup of "{self._plan.path}" on {datetime.now().strftime("%A %d, %B %m, %Y %R")}'
        try:
            write(
                f"{self._path}/info.txt",
                f"{d}\n\nSOURCE: {self._plan.path}\nSHA256: {h}\nSIZE:   "
                f'{_size(getsize(f"{self._path}/data.pak"))}\nDATE:   '
                f'{datetime.now().strftime("%b %d %Y %H:%M:%S")}\nTYPE:   '
                f'{"Incremental" if self._increment else "Full"}\n',
            )
        except OSError as err:
            server.error(
                f"[m/backup/job/{self.id}]: Cannot write Backup info data!", err
            )
            return self._update(server, BACKUP_STATE_ERROR)
        finally:
            del d, h
        try:
            write(
                f"{self._path}/extract.sh",
                BACKUP_RESTORE_SCRIPT_NO_KEY
                if self._key is None
                else BACKUP_RESTORE_SCRIPT,
            )
        except OSError as err:
            server.error(
                f"[m/backup/job/{self.id}]: Cannot write Backup extract script!", err
            )
            return self._update(server, BACKUP_STATE_ERROR)
        self._next(server)

    def stop(self, server, force=False):
        if self._cancel.is_set():
            return
        server.info(f"[m/backup/job/{self.id}]: Stopping Backup Job {self}.")
        self._stop(server, force)

    def _step_timeout(self, server, post):
        if post:
            server.error(
                f"[m/backup/job/{self.id}]: Backup post-backup command timeout after {BACKUP_TIMEOUT} seconds!"
            )
            return self._next(server)
        server.error(
            f"[m/backup/job/{self.id}]: Backup timeout after {BACKUP_TIMEOUT} seconds!"
        )
        self._stop(server, True)

    def _check_space(self, server, file, extra=1.5):
        p = f"{self._path}/{file}"
        try:
            s, x = statvfs(p), round(float(getsize(p)) * extra)
            r = (s.f_frsize * s.f_bavail) - x
        except OSError as err:
            return server.error(
                f"[m/backup/job/{self.id}] Cannot get free space size for Backup storage!",
                err,
            )
        del s, p
        if r < 0:
            return server.error(
                f"[m/backup/job/{self.id}] Insufficient space on device, {_size(x)} needed {_size(r)} free!"
            )
        server.debug(
            f"[m/backup/job/{self.id}] Free space check {_size(x)} needed, {_size(r)} free."
        )
        del r, x
        return True

    def _exec_and_watch(self, server, cmd, stdin=None, add=None, read=False):
        server.debug(f'[m/backup/job/{self.id}]: Executing command "{" ".join(cmd)}".')
        self._proc = Single.new(cmd, stdin)
        server.debug(
            f"[m/backup/job/{self.id}]: Command started, PID {self._proc.pid()}."
        )
        self._proc.nice()
        if read:
            try:
                self._proc.set_non_blocking()
            except OSError as err:
                server.warning(
                    f"[m/backup/job/{self.id}]: Cannot set non-blocking mode for PID {self._proc.pid()}!",
                    err,
                )
            else:
                self._reader = server.task(BACKUP_READ_TIME, self._step_read, (server,))
        if add is None:
            return server.watch(self._proc, self._next, (server,))
        return server.watch(self._proc, self._next, (server, add))


class Schedule(object):
    __slots__ = ("_days", "_cycle", "_increment")

    def __init__(self, data):
        if not isinstance(data, dict):
            self._days, self._cycle, self._increment = None, None, None
            return
        self._days = data.get("days")
        if self._days is not None and not isinstance(self._days, list):
            raise ValueError(
                f'schedule "days" value should be a list (not "{type(self._days)}")'
            )
        self._cycle = num(data.get("cycle", 0), False)
        self._increment = boolean(data.get("increment"))

    def is_full(self, count):
        if not isinstance(self._days, list) or not self._increment:
            return True
        return isinstance(self._cycle, int) and (
            self._cycle == 0 or count >= self._cycle
        )

    def runnable(self, current_day):
        if not isinstance(self._days, list) or len(self._days) == 0:
            return False
        for i in self._days:
            if not nes(i):
                continue
            v = i.lower()
            if current_day == 0 and v[0] == "m":
                return True
            if current_day == 2 and v[0] == "w":
                return True
            if current_day == 4 and v[0] == "f":
                return True
            if len(v) < 2:
                continue
            if current_day == 1 and v[0] == "t" and v[1] == "u":
                return True
            if current_day == 3 and v[0] == "t" and v[1] == "h":
                return True
            if current_day == 5 and v[0] == "s" and v[1] == "a":
                return True
            if current_day == 6 and v[0] == "s" and v[1] == "u":
                return True
            del v
        return False


class Dual(NamedTuple):
    # NOTE(dij): Dual is a "holder" for multi-process "piped" items. Since it's
    #            max two, we can just use a NamedTuple. We make the assumption
    #            that both are non-None and we return the status of the last
    #            process always as it should be the last one running. Kill, wait
    #            and poll will call on both to prevent zombie processes.
    p1: Popen
    p2: Popen

    def pid(self):
        return self.p2.pid

    def nice(self):
        nulexec(
            ["/usr/bin/renice", "-n", "15", "--pid", f"{self.p1.pid}"],
            wait=True,
            errors=False,
        )
        nulexec(
            ["/usr/bin/renice", "-n", "15", "--pid", f"{self.p2.pid}"],
            wait=True,
            errors=False,
        )
        nulexec(
            ["/usr/bin/ionice", "-c", "3", "-p", f"{self.p1.pid}"],
            wait=True,
            errors=False,
        )
        nulexec(
            ["/usr/bin/ionice", "-c", "3", "-p", f"{self.p2.pid}"],
            wait=True,
            errors=False,
        )

    def kill(self):
        self.p1.kill()
        self.p2.kill()

    def poll(self):
        self.p1.poll()
        return self.p2.poll()

    def stop(self):
        stop(self.p1)
        stop(self.p2)

    def output(self):
        try:
            set_blocking(self.p1.stderr.fileno(), True)
        except OSError:
            pass
        return (
            max(self.p1.wait(), self.p2.wait()),
            _output_strip(self.p1.stderr.read(), _output_strip(self.p2.stdout.read())),
            _output_strip(self.p2.stderr.read()),
        )

    def terminate(self):
        self.p1.terminate()
        self.p2.terminate()

    def read(self, count, _):
        # NOTE(dij): We can't read stdout of the p1 process as it's being
        #            piped.
        return self.p1.stderr.read(count)

    def wait(self, timeout=None):
        self.p1.wait(timeout)
        return self.p2.wait(timeout)

    def send_signal(self, signal):
        self.p1.send_signal(signal)
        self.p2.send_signal(signal)


class Single(NamedTuple):
    p1: Popen

    def pid(self):
        return self.p1.pid

    def nice(self):
        nulexec(
            ["/usr/bin/renice", "-n", "15", "--pid", f"{self.p1.pid}"],
            wait=True,
            errors=False,
        )
        nulexec(
            ["/usr/bin/ionice", "-c", "3", "-p", f"{self.p1.pid}"],
            wait=True,
            errors=False,
        )

    def kill(self):
        self.p1.kill()

    def poll(self):
        return self.p1.poll()

    def stop(self):
        stop(self.p1)

    def output(self):
        try:
            set_blocking(self.p1.stdout.fileno(), True)
            set_blocking(self.p1.stderr.fileno(), True)
        except OSError:
            pass
        return (
            self.p1.wait(),
            _output_strip(self.p1.stdout.read()),
            _output_strip(self.p1.stderr.read()),
        )

    def terminate(self):
        self.p1.terminate()

    def set_non_blocking(self):
        set_blocking(self.p1.stdout.fileno(), False)
        set_blocking(self.p1.stderr.fileno(), False)

    def wait(self, timeout=None):
        return self.p1.wait(timeout)

    def read(self, count, stderr):
        return self.p1.stderr.read(count) if stderr else self.p1.stdout.read(count)

    @classmethod
    def new(cls, cmd, stdin=None):
        try:
            p = cls(
                Popen(
                    cmd,
                    text=True,
                    stdin=PIPE if stdin is not None else DEVNULL,
                    stdout=PIPE,
                    stderr=PIPE,
                    encoding="UTF-8",
                    close_fds=True,
                    universal_newlines=True,
                )
            )
        except (SubprocessError, OSError) as err:
            raise OSError(f'cannot start process "{" ".join(cmd)}": {err}')
        if stdin is None:
            return p
        try:
            if isinstance(stdin, str):
                p.p1.stdin.write(stdin)
            elif isinstance(stdin, (bytes, bytearray)):
                p.p1.stdin.write(stdin.decode("UTF-8", "ignore"))
            try:
                p.p1.stdin.close()
            except OSError:
                pass
        except OSError as err:
            raise OSError(f"cannot write stdin data: {err}")
        return p

    def send_signal(self, signal):
        self.p1.send_signal(signal)


class BackupServer(object):
    __slots__ = ("_queue", "_current")

    def __init__(self):
        self._queue = Queue()
        self._current = None

    def _status(self, server):
        try:
            p = Plans(CONFIG_BACKUP)
        except (OSError, ValueError) as err:
            server.error("[m/backup]: Cannot read the Backup config!", err)
            return as_error("could not load backup config")
        r = p.status(server, self._queue, self._current)
        if p.updated:
            p.save(server)
        del p
        return {"plans": r}

    def hook(self, server, message):
        if self._current is None or not self._current.running():
            return
        if message.header() == HOOK_SHUTDOWN:
            server.info(f"[m/backup]: Stopping Backup {self._current} due to shutdown.")
            self._current.stop(server)
            self._current.save(server, BACKUP_STATE)
            self._current = None
        elif message.type == MSG_POST and self._current.paused():
            if not _on_battery():
                return server.info(
                    "[m/backup]: Not resuming Backup as AC power is not connected."
                )
            if not self._current.resume(server):
                return
            server.notify("Backup Status", f"Backup {self._current} resumed!", "yed")
        elif message.type == MSG_PRE and not self._current.paused():
            self._current.suspend(server)

    def control(self, server, message):
        if message.type == MSG_STATUS:
            return self._status(server)
        if message.forward:
            if message.type != MSG_UPDATE or self._current is None:
                return
            if message.state < BACKUP_STATE_ERROR:
                return
            self._current.stop(server)
            if not message.final:
                return
            if self._current.save(server, BACKUP_STATE):
                server.notify(
                    "Backup Status", f"Backup {self._current} completed!", "yed"
                )
            else:
                server.notify(
                    "Backup Status",
                    f"Backup {self._current} was stopped with errors!",
                    "yed",
                )
            self._current = None
            if self._queue.is_empty():
                return
            server.debug("[m/backup]: Backup completed, checking queue for next Plan..")
            self._select(server)
            if self._current is None:
                return {"result": "No Backups are scheduled or could be started!"}
            return {"result": f"Started Backup {self._current}!"}
        if self._current is None or not self._current.running():
            if message.type == MSG_USER:
                server.debug("[m/backup]: Clearing the Backup state and cache files..")
                try:
                    remove(BACKUP_STATE)
                    rmtree(BACKUP_STATE_DIR)
                except OSError as err:
                    server.error("[m/backup]: Cannot clear the Backup cache!", err)
                    return as_error("Cannot clear the Backup cache!")
                return {"result": ""}
            if message.type == MSG_ACTION and message.action == MSG_PRE:
                return self._select(server, message.dir, message.force, message.full)
            return {"result": "No Backup is running."}
        if message.type == MSG_USER:
            return {"result": "There is currently a Backup running."}
        if message.type == MSG_CONFIG:
            if message.action == MSG_PRE:
                if self._current.paused():
                    return as_error("Backup is already suspended!")
                if not self._current.suspend(server):
                    return as_error("Cannot suspend Backup!")
                server.notify(
                    "Backup Status", f"Backup {self._current} suspended.", "yed"
                )
                return {"result": f"Suspended Backup {self._current}."}
            if not self._current.paused():
                return as_error("Backup is already running!")
            if not self._current.resume(server):
                return as_error("Cannot resume Backup!")
            server.notify("Backup Status", f"Backup {self._current} resumed!", "yed")
            return {"result": f"Resumed Backup {self._current}."}
        if message.type == MSG_ACTION:
            if message.action == MSG_PRE:
                return self._select(server, message.dir, message.force, message.full)
            if message.action == MSG_POST:
                return self._stop(server, message.dir)
        return as_error("unknown/invalid backup command")

    def _stop(self, server, path=None):
        if not nes(path) and (self._current is None or not self._current.running()):
            return {"result": "There is no Backup running."}
        if not nes(path):
            self._current.stop(server, True)
            return {"result": f"Backup {self._current} was stopped."}
        if (
            self._current is not None
            and self._current.running()
            and _match_path_or_id(path, self._current._plan)
        ):
            self._current.stop(server, True)
            return {"result": f'Backup "{self._current._plan.id}" was stopped.'}
        r = self._queue.remove(path)
        if r is not None:
            return {"result": f"Backup {r} was removed from the queue."}
        return {"result": "Backup was not found in queue or running."}

    def _select(self, server, path=None, force=False, force_full=False):
        if not _on_battery(force):
            server.info("[m/backup]: Not starting a Backup on battery power.")
            return as_error(
                'Cannot run on battery power, please connect to AC power or use the "-f" switch!'
            )
        if not nes(path) and self._current is not None and self._current.running():
            return {"result": f"Backup {self._current} is currently running!"}
        try:
            p = Plans(CONFIG_BACKUP)
        except (OSError, ValueError) as err:
            server.error("[m/backup]: Cannot read the Backup config!", err)
            return as_error("Cannot load the Backup config!")
        a, r = self._queue.add_plans(server, p, path, self._current)
        if p.updated:
            p.save(server)
        if r:
            server.debug(
                f"[m/backup]: Not starting a Backup as {self._current} is running."
            )
            if a > 0:
                return {"result": "Backup added to queue."}
            return {"result": "Backup is already in queue or running!"}
        del r, a
        if self._queue.is_empty():
            server.debug("[m/backup]: Not starting a Backup as the queue is empty.")
            return {"result": "No Backups are scheduled or could be started!"}
        try:
            n, s = self._queue.next(server, BACKUP_STATE, path, force)
        except OSError as err:
            server.error("[m/backup]: Cannot read the Backup state file!", err)
            return as_error("Cannot read the Backup state!")
        if n is None:
            server.debug("[m/backup]: Not starting a Backup as the queue is empty.")
            return {"result": "No Backups are scheduled or could be started!"}
        server.debug(f"[m/backup]: Selected Plan {n}..")
        i = n.incremental(s, force_full)
        try:
            write_json(BACKUP_STATE, s, perms=0o0640)
        except OSError as err:
            server.error("[m/backup]: Cannot write to the Backup state file!", err)
            return as_error("Cannot write the Backup state")
        finally:
            del s
        self._current = Backup(p.dir, p.key, p.upload, n, i)
        server.info(
            f'[m/backup]: Starting Backup {n} as a{"n incremental" if i else " full"} backup!'
        )
        del n, i, p
        try:
            self._current.start(server)
        except ConnectionError:
            server.error(
                f'[m/backup]: Cannot connect to the upload server "{self._current._upload._host}:'
                f'{self._current._upload.port}", stopping backup!'
            )
            server.notify(
                "Backup Status",
                f'Backup target "{self._current._upload._host}" is not reachable, not backing up!',
                "yed",
            )
            self._current.stop(server, True)
            self._current = None
            return as_error("Cannot connect to the Backup upload server!")
        except OSError as err:
            server.error("[m/backup]: Cannot start Backup!", err)
            self._current.stop(server, True)
            self._current = None
            return as_error("Cannot start Backup!")
        return f"Backup {self._current} started!"
