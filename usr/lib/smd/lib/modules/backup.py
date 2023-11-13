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

from shutil import rmtree
from threading import Event
from uuid import uuid4, UUID
from base64 import b64encode
from typing import NamedTuple
from datetime import datetime
from lib.util.exec import nulexec, stop, split
from socket import socket, AF_INET, SOCK_STREAM
from lib.structs import Message, Storage, as_error
from lib.util import num, nes, cancel_nul, boolean
from signal import SIGSTOP, SIGCONT, SIGINT, SIGKILL
from subprocess import DEVNULL, Popen, PIPE, SubprocessError
from os.path import isabs, isdir, exists, isfile, getsize, basename
from os import chmod, urandom, remove, makedirs, statvfs, environ, kill
from lib.util.file import read, read_json, write_json, info, write, remove_file
from lib.constants.files import BACKUP_RESTORE_SCRIPT, BACKUP_RESTORE_SCRIPT_NO_KEY
from lib.constants.config import (
    BACKUP_STATE,
    BACKUP_HOSTS,
    CONFIG_BACKUP,
    BACKUP_EXCLUDE,
    BACKUP_TIMEOUT,
    BACKUP_KEY_SIZE,
    BACKUP_STATE_DIR,
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
    BACKUP_SIZES,
    HOOK_SUSPEND,
    HOOK_SHUTDOWN,
    HOOK_HIBERNATE,
    BACKUP_STATE_DONE,
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
        return f"{float(size):3.1f}B"
    s = size / 1024.0
    for i in BACKUP_SIZES:
        if abs(s) < 1024.0:
            return f"{float(s):3.1f}{i}iB"
        s /= 1024.0
    return f"{float(s):.1f}YiB"


def _time(delta):
    t = delta.total_seconds()
    if t < 60:
        return f"{round(t)}s"
    h = round(t // 3600)
    t -= h * 3600
    m = round(t // 60)
    s = round(t - (m * 60))
    if h == 0:
        if s == 0:
            return f"{m}m"
        return f"{m}m {s}s"
    if m == 0:
        return f"{h}hr" if s == 0 else f"{h}hr {s}s"
    if m > 0 and s == 0:
        return f"{h}hr {m}m"
    return f"{h}hr {m}m {s}s"


def _apes(s, last=False):
    if not nes(s):
        return ""
    if last:
        return s
    return f"{s}\n"


def _on_battery(force=False):
    return force or read(BACKUP_BATTERY_PATH, errors=False, strip=True) == "1"


def _kill_runaway(server, proc):
    server.error(f"[m/backup]: Stopping runaway process PID {proc.pid}!")
    stop(proc)


class Plan(object):
    __slots__ = (
        "dir",
        "key",
        "keep",
        "uuid",
        "path",
        "upload",
        "exclude",
        "cmd_pre",
        "schedule",
        "cmd_post",
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
        self.schedule = Schedule(data.get("schedule"))
        self.uuid = data.get("uuid")
        if not nes(self.uuid):
            self.uuid = str(uuid4())
            data["uuid"] = self.uuid
        else:
            try:
                UUID(self.uuid)
            except ValueError:
                raise ValueError(f'plan "uuid" "{self.uuid}" is invalid')
        self.key = data.get("public_key")
        if nes(self.key):
            if not isabs(self.key):
                raise ValueError('plan "public_key" must be a full path')
        self.exclude = data.get("exclude")
        if self.exclude is not None and not isinstance(self.exclude, list):
            raise ValueError('plan "exclude" must be a list')
        u = data.get("upload")
        if isinstance(u, dict) and len(u) > 0:
            self.upload = Upload(u)
        elif u is not None and not isinstance(u, dict):
            raise ValueError('plan "upload" must be an object')
        else:
            self.upload = None
        del u
        self.keep, self.description = boolean(data.get("keep")), data.get("description")
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

    def _add(self, plan):
        if plan.uuid in self._map:
            return
        self._map[plan.uuid] = True
        self._entries.append(plan)

    def remove(self, path):
        if len(self._entries) == 0:
            return False
        v = None
        for i in self._entries:
            if i.path != path:
                continue
            v = i
            break
        if v is None:
            return False
        self._entries.remove(v)
        del self._map[v.uuid], v
        return True

    def __contains__(self, value):
        if nes(value):
            return value in self._map
        return isinstance(value, Plan) and value.uuid in self._map

    def add_plans(self, plans, path, running):
        if len(plans.entries) == 0:
            return list()
        w, c = datetime.now().weekday(), 0
        for i in plans.entries:
            if i.uuid == running:
                # NOTE(dij): Don't re-add the running backup.
                continue
            if i.path == path:
                self._add(i)
                c += 1
                continue
            if not i.schedule.runnable(w):
                continue
            self._add(i)
            c += 1
        del w
        return c

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
                if x.upload is not None:
                    x.upload.check()
            except (OSError, ValueError) as err:
                server.warning(
                    f'[m/backup]: Skipping Plan "{x.uuid}" ({x.path}) as check failed!',
                    err,
                )
                continue
            if nes(path):
                if x.path != path:
                    continue
                return (x, d)
            if force or x.uuid not in d:
                return (x, d)
            t = d[x.uuid].get("last")
            if not nes(t):
                return (x, d)
            try:
                if (n - datetime.fromisoformat(t)).total_seconds() > BACKUP_WAIT_TIME:
                    return (x, d)
            except ValueError:
                pass
            del t
            if d[x.uuid].get("error", False):
                return (x, d)
            server.debug(
                f'[m/backup]: Skipping Backup "{x.uuid}" as the last successful run was less than '
                f"{round(BACKUP_WAIT_TIME/3600)}hrs ago."
            )
            del x
        del n
        return (None, d)


class Multi(object):
    __slots__ = ("_cwd", "_cmds", "_proc", "_break")

    def __init__(self, cmds, cwd=None, stop_error=True):
        if not isinstance(cmds, (list, tuple)) or len(cmds) == 0:
            raise OSError("cmd list must be a non-empty list")
        self._cwd = cwd
        self._cmds = cmds
        self._break = stop_error
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
        if r is not None and len(self._cmds) == 0:
            # We're empty! Say we're done.
            return r
        if self._break and isinstance(r, int) and r != 0:
            self._cmds.clear()
            return r
        try:
            # Try next proc.
            self._proc = self._next()
        except OSError:
            # If we fail, bail!
            self._cmds.clear()
            return r
        # We don't check the output of the new proc yet, so we don't break on
        # processes that exit immediately. We do this instead of looping, which
        # while has a small time overhead, it prevents keeping the event loop busy.
        return None

    def stop(self):
        self._cmds.clear()
        if self._proc.poll() is not None:
            return self._proc.wait()
        try:
            self._proc.send_signal(SIGINT)
        except (OSError, SubprocessError):
            pass
        try:
            self._proc.terminate()
        except (OSError, SubprocessError):
            pass
        try:
            self._proc.send_signal(SIGKILL)
        except (OSError, SubprocessError):
            pass
        if self._proc.poll() is not None:
            return self._proc.poll()
        try:
            self._proc.kill()
        except (OSError, SubprocessError):
            pass
        try:
            kill(self._proc.pid, SIGKILL)
        except OSError:
            pass
        try:
            self._proc.wait(timeout=1)
        except (OSError, SubprocessError):
            pass
        return None

    def _next(self):
        v = nulexec(self._cmds.pop(0), cwd=self._cwd)
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

    def terminate(self):
        self._cmds.clear()
        self._proc.terminate()

    def wait(self, timeout=None):
        return self._proc.wait(timeout)

    def send_signal(self, signal):
        self._proc.send_signal(signal)


class Plans(object):
    __slots__ = ("dir", "key", "upload", "entries", "storage")

    def __init__(self, file):
        self.storage = Storage(file, load=True)
        if len(self.storage) == 0:
            return Plans(BACKUP_DEFAULT_DIR, None, None, list(), None)
        p = self.storage.get("plans")
        if p is not None and not isinstance(p, list):
            raise ValueError(f'"plans" value should be a list (not "{type(p)}")')
        if p is None or len(p) == 0:
            return Plans(BACKUP_DEFAULT_DIR, None, None, list(), None)
        self.entries = list()
        for i in p:
            if not isinstance(i, dict):
                raise ValueError('"plans" entries must be object types')
            self.entries.append(Plan(i))
        del p
        u, self.dir = self.storage.get("upload"), self.storage.get(
            "dir", BACKUP_DEFAULT_DIR
        )
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


class Upload(object):
    __slots__ = ("key", "port", "_host", "_user")

    def __init__(self, data):
        self._host = data.get("host")
        if not nes(self._host):
            raise ValueError('upload "host" must be a non-empty string')
        self._host, self._user = Upload._split_host_port(self._host, data.get("user"))
        if not nes(self._user):
            raise ValueError('upload "user"  must be a non-empty string')
        self._host, self.port = Upload._split_host_port(
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
        if nes(self.key):
            if not isabs(self.key):
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

    @staticmethod
    def _split_host_user(s, other):
        i = s.find("@")
        if i <= 0 or i + 1 > len(s):
            return (s[1:0], other)
        return (s[0:i], s[i + 1 :])

    @staticmethod
    def _split_host_port(s, other):
        i, b = s.rfind(":"), s.rfind("]")
        if i <= 1 and b <= 1:
            return (s, other)
        if i + 1 > len(s):
            return (s, other)
        if i > 1 and i > b:
            try:
                return (s[0:i], num(s[i + 1 :]))
            except ValueError:
                raise ValueError(f'host "{s}" is invalid')
        del i, b
        return (s, other)


class Backup(object):
    __slots__ = (
        "_key",
        "_dir",
        "_job",
        "_plan",
        "_proc",
        "_last",
        "_path",
        "_done",
        "_time",
        "_size",
        "_state",
        "_cancel",
        "_paused",
        "_upload",
        "_timeout",
        "_increment",
    )

    def __init__(self, work, key, upload, plan, inc):
        self._key = plan.key if nes(plan.key) else key
        self._dir = plan.dir if nes(plan.dir) else work
        self._job = plan.uuid[:8].lower()
        self._plan = plan
        self._proc = None
        self._last = None
        self._done = False
        self._path = f'{self._dir}/smd-backup-{datetime.now().strftime("%Y%m%d-%H%M")}-{plan.uuid[:8]}'
        self._time = None
        self._size = None
        self._state = BACKUP_STATE_WAITING
        self._cancel = Event()
        self._paused = Event()
        self._upload = plan.upload if plan.upload is not None else upload
        self._timeout = None
        self._increment = inc

    def paused(self):
        return self._paused.is_set()

    def running(self):
        return not self._cancel.is_set()

    def resume(self, server):
        if self._proc is not None and self._proc.poll() is None:
            try:
                self._proc.send_signal(SIGCONT)
            except (SubprocessError, OSError) as err:
                return server.error(
                    f'[m/backup/job/{self._job}] Cannot resume Backup "{self._plan.uuid}"!',
                    err,
                )
        server.info(f'[m/backup/job/{self._job}] Resuming Backup "{self._plan.uuid}".')
        self._paused.clear()
        return True

    def start(self, server):
        if self._upload is not None and not self._upload.check():
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
        server.info(
            f'[m/backup/job/{self._job}] Starting Backup Job "{self._plan.uuid}"..'
        )
        self._next(server)

    def suspend(self, server):
        if self._proc is not None and self._proc.poll() is None:
            try:
                self._proc.send_signal(SIGSTOP)
            except (SubprocessError, OSError) as err:
                return server.error(
                    f'[m/backup/job/{self._job}] Cannot suspend Backup "{self._plan.uuid}"!',
                    err,
                )
        server.info(
            f'[m/backup/job/{self._job}] Suspending Backup "{self._plan.uuid}".'
        )
        self._paused.set()
        return True

    def _step_pack(self, server):
        if not self._update(server, BACKUP_STATE_PACKING):
            return
        if not self._check_space(server, "data.pak"):
            return self._update(server, BACKUP_STATE_ERROR)
        server.debug(f"[m/backup/job/{self._job}]: Starting the [Packing] step..")
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
            )
        except OSError as err:
            server.error(
                f"[m/backup/job/{self._job}]: Cannot start the packing process!",
                err,
            )
            return self._update(server, BACKUP_STATE_ERROR)

    def save(self, server, file):
        try:
            s = read_json(file, errors=True)
        except OSError as err:
            server.warning(
                f"[m/backup/job/{self._job}]: Cannot read the Backup state file!", err
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
        s[self._plan.uuid] = {
            "size": self._size,
            "last": datetime.now().isoformat(),
            "count": c + 1,
            "error": self._state == BACKUP_STATE_ERROR,
        }
        try:
            write_json(BACKUP_STATE, s, perms=0o640)
        except OSError as err:
            server.warning(
                f"[m/backup/job/{self._job}]: Cannot save the Backup state file!", err
            )
        del s, c
        return self._state == BACKUP_STATE_DONE

    def _check_proc(self, server):
        if self._proc is None:
            return True
        try:
            n, self._last, e = self._proc.output()
        except OSError as err:
            server.error(
                f"[m/backup/job/{self._job}]: Cannot read process output!", err
            )
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
                f"[m/backup/job/{self._job}]: Process exited with a non-zero exit code ({n})!"
            )
            return self._update(server, BACKUP_STATE_ERROR)
        server.error(
            f"[m/backup/job/{self._job}]: Process exited with a non-zero exit code ({n}): {e}!"
        )
        del n, e
        return self._update(server, BACKUP_STATE_ERROR)

    def _step_keygen(self, server):
        if not self._update(server, BACKUP_STATE_KEYGEN):
            return
        if not nes(self._key):
            self.server.info(
                f"[m/backup/job/{self._job}]: Skipping encryption step with no keyfile! "
                "BACKUPS WILL NOT BE ENCRYPTED!"
            )
            self._key = None
            self._update(server, BACKUP_STATE_NO_KEYGEN)
            return self._next(server)
        if not exists(self._key):
            self.server.warning(
                f'[m/backup/job/{self._job}]: Skipping encryption step as the public key "{self._key}" '
                "does not exist! BACKUPS WILL NOT BE ENCRYPTED!"
            )
            self._key = None
            self._update(server, BACKUP_STATE_NO_KEYGEN)
            return self._next(server)
        server.debug(
            f"[m/backup/job/{self._job}]: Starting the [Key Generation] step.."
        )
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
                f"[m/backup/job/{self._job}]: Cannot start the Key Generation process!",
                err,
            )
            self._update(server, BACKUP_STATE_ERROR)
        finally:
            x = None
            del x

    def _step_upload(self, server):
        if not self._update(server, BACKUP_STATE_UPLOADING):
            return
        if not self._upload.valid():
            server.info(f"[m/backup/job/{self._job}]: Skipping Upload with no target!")
            return self._next(server)
        if not exists(BACKUP_HOSTS):
            server.error(
                f"[m/backup/job/{self._job}]: Unable to upload Backup, the known hosts file "
                f'"{BACKUP_HOSTS}" is missing! Please execute "ssh -o UserKnownHostsFile=file {self._upload.host()}" '
                f'to generate the file and copy it to "{BACKUP_HOSTS}".'
            )
            return self._update(server, BACKUP_STATE_ERROR)
        server.debug(f"[m/backup/job/{self._job}]: Starting the [Upload] step..")
        o = f"/bin/ssh -o VisualHostKey=no -o UserKnownHostsFile={BACKUP_HOSTS} -p {self._upload.port}"
        if nes(self._upload.key):
            try:
                chmod(self._upload.key, 0o0400, follow_symlinks=True)
            except OSError:
                pass
            o = f"{o} -i {self._upload.key}"
        f = f"{self._path}.tar"
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
            )
        except OSError as err:
            server.error(
                f"[m/backup/job/{self._job}]: Cannot start the upload process!",
                err,
            )
            return self._update(server, BACKUP_STATE_ERROR)
        finally:
            del o, f

    def _stop(self, server, force):
        if self._done:
            return
        self._done = True
        self._paused.clear()
        self._cancel.set()
        server.debug(f"[m/backup/job/{self._job}]: Cleaning up..")
        self._timeout = cancel_nul(server, self._timeout)
        if self._proc is not None:
            self._proc.stop()
        try:
            rmtree(self._path, ignore_errors=True)
        except OSError as err:
            server.error(
                f'[m/backup/job/{self._job}]: Cannot remove directory "{self._path}"!',
                err,
            )
        if isdir(self._path):
            server.error(
                f'[m/backup/job/{self._job}]: Cannot remove directory "{self._path}"!'
            )
        if force or self._state != BACKUP_STATE_UPLOADING:
            self._state = BACKUP_STATE_ERROR
            remove_file(f"{self._path}.tar")
        else:
            self._state = BACKUP_STATE_DONE
        # NOTE(dij): We run this after so we can unmount anything used.
        self._start_post_cmd(server)
        server.forward(
            Message(
                HOOK_BACKUP,
                {"type": MSG_UPDATE, "uuid": self._plan.uuid, "state": self._state},
            )
        )

    def _step_ec(self, server, key):
        if not self._update(server, BACKUP_STATE_ENCRYPT_COMPRESS):
            return
        server.debug(
            f"[m/backup/job/{self._job}]: Starting the [Compress|Encrypt] step.."
        )
        s = f"{BACKUP_STATE_DIR}/{self._plan.uuid}.db"
        try:
            if not self._increment and isfile(s):
                remove(s)
        except OSError as err:
            server.error(f"[m/backup/job/{self._job}]: Cannot remove state file", err)
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
        x += ["-f", "-", self._plan.path]
        e = environ.copy()
        e["SMD_ENC_KEY"] = key
        server.debug(
            f"[m/backup/job/{self._job}]: Starting the combo compress|encrypt process.."
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
                f"[m/backup/job/{self._job}]: Cannot start the encryption process!",
                err,
            )
            return self._update(server, BACKUP_STATE_ERROR)
        finally:
            del e["SMD_ENC_KEY"]
            del e, x
        self._proc = Dual(p1, p2)
        del p1, p2
        server.debug(
            f"[m/backup/job/{self._job}]: Command started, PID {self._proc.pid()}."
        )
        self._proc.nice()
        server.watch(self._proc, self._next, (server,))

    def _step_pre_cmd(self, server):
        if not self._update(server, BACKUP_STATE_PRE_CMD):
            return
        c = split(self._plan.cmd_pre)
        if c is None:
            server.warning(
                f'[m/backup/job/{self._job}]: Ignoring pre-start command type "{type(self._plan.cmd_pre)}"!'
            )
            return self._next(server)
        if len(c) == 0:
            return self._next(server)
        server.info(
            f'[m/backup/job/{self._job}]: Executing pre-start command set "{c}".'
        )
        try:
            self._proc = Multi(c)
        except OSError as err:
            server.error(
                f'[m/backup/job/{self._job}]: Cannot start the pre-start command "{c}"!',
                err,
            )
            return self._update(server, BACKUP_STATE_ERROR)
        finally:
            del c
        server.debug(
            f"[m/backup/job/{self._job}]: Pre-start command started, PID {self._proc.pid()}."
        )
        server.watch(self._proc, self._next, (server,))

    def _update(self, server, state):
        if self._cancel.is_set():
            server.info(f"[m/backup/job/{self._job}]: Backup was stopped!")
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
        server.debug(f"[m/backup/job/{self._job}]: Starting the [Compression] step..")
        s = f"{BACKUP_STATE_DIR}/{self._plan.uuid}.db"
        try:
            if not self._increment and isfile(s):
                remove(s)
        except OSError as err:
            server.error(f"[m/backup/job/{self._job}]: Cannot remove state file", err)
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
        x += ["-f", f"{self._path}/data.pak", self._plan.path]
        try:
            self._exec_and_watch(server, x)
        except OSError as err:
            server.error(
                f"[m/backup/job/{self._job}]: Cannot start the compress process!", err
            )
            return self._update(server, BACKUP_STATE_ERROR)
        finally:
            del x

    def _next(self, server, arg=None):
        server.cancel(self._timeout)
        if self._time is not None:
            n = datetime.now()
            self._time, d = n, (n - self._time)
            server.debug(f"[m/backup/job/{self._job}]: Execution took {_time(d)}.")
            del n, d
        else:
            self._time = datetime.now()
        self._timeout = server.task(BACKUP_TIMEOUT, self._stop, (server, True))
        if self._state == BACKUP_STATE_WAITING and self._plan.cmd_pre is not None:
            return self._step_pre_cmd(server)
        if self._state <= BACKUP_STATE_PRE_CMD:
            try:
                makedirs(self._path, mode=0o0750, exist_ok=True)
            except OSError as err:
                server.error(
                    f'[m/backup/job/{self._job}]: Cannot make Backup directory "{self._path}"!',
                    err,
                )
                return self._stop(server, True)
            return self._step_keygen(server)
        if self._proc is not None:
            r = self._check_proc(server)
            self._proc.stop()
            self._proc = None
        else:
            r = True
        server.debug(f"[m/backup/job/{self._job}]: Command output state was {r}.")
        if not r:
            return self._stop(server, True)
        del r
        server.debug(
            f"[m/backup/job/{self._job}]: Step completed, moving to next step!"
        )
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
                    f'[m/backup/job/{self._job}]: Cannot retrive size of file "{arg}"!',
                    err,
                )
            else:
                if self._upload.valid():
                    server.info(
                        f'[m/backup/job/{self._job}]: Uploaded Backup file "{arg}" ({self._size}) to '
                        f'"{self._upload._host}" successfully!'
                    )
                else:
                    server.info(
                        f'[m/backup/job/{self._job}]: Backup to file "{arg}" ({self._size}) was successful!'
                    )
            if self._upload.valid() and not self._plan.keep:
                try:
                    remove(arg)
                except OSError as err:
                    server.error(
                        f'[m/backup/job/{self._job}]: Cannot remove Backup file "{arg}"!',
                        err,
                    )
        self._stop(server, False)

    def _start_post_cmd(self, server):
        if self._plan.cmd_post is None:
            return
        c = split(self._plan.cmd_post)
        if c is None:
            return server.warning(
                f'[m/backup/job/{self._job}]: Ignoring post-backup command type "{type(self._plan.cmd_pre)}"!'
            )
        if len(c) == 0:
            return
        server.info(
            f'[m/backup/job/{self._job}]: Executing post-backup command set "{c}".'
        )
        try:
            p = Multi(c, self._dir, False)
        except OSError as err:
            return server.error(
                f'[m/backup/job/{self._job}]: Cannot start the post-backup command "{c}"!',
                err,
            )
        finally:
            del c
        server.debug(
            f"[m/backup/job/{self._job}]: Post-backup command started, PID {p.pid()}."
        )
        # NOTE(dij): This weird dance here uses the async libs of the server to
        #            first: Add a task that will trigger in "BACKUP_TIMEOUT" seconds
        #            that will kill the process if it's still running.
        #            Second: will cancel the event and prevent the process from
        #            being killed if it exits before the timeout. (It cancels the
        #            task event handle "e").
        e = server.task(BACKUP_TIMEOUT, _kill_runaway, (server, p))
        server.watch(p, server.cancel, (e,))
        del e

    def _step_hash_part1(self, server):
        if not self._update(server, BACKUP_STATE_HASHING_P1):
            return
        server.debug(f"[m/backup/job/{self._job}]: Starting the [Hashing] step..")
        try:
            self._exec_and_watch(
                server, ["/bin/sha256sum", "--binary", f"{self._path}/data.pak"]
            )
        except OSError as err:
            server.error(
                f"[m/backup/job/{self._job}]: Cannot start the hashing process!", err
            )
            return self._update(server, BACKUP_STATE_ERROR)

    def _step_hash_part2(self, server):
        if not self._update(server, BACKUP_STATE_HASHING_P2):
            return
        if not nes(self._last):
            server.error(
                f"[m/backup/job/{self._job}]: Hash process did not return any data!"
            )
            return self._update(server, BACKUP_STATE_ERROR)
        h = self._last.replace(f"*{self._path}/", EMPTY)
        if len(h) == 0:
            server.error(
                f"[m/backup/job/{self._job}]: Hash process did not return valid data!"
            )
            return self._update(server, BACKUP_STATE_ERROR)
        try:
            write(f"{self._path}/data.sum", h)
        except OSError as err:
            server.error(
                f"[m/backup/job/{self._job}]: Cannot write Backup hash data!", err
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
                f"[m/backup/job/{self._job}]: Cannot write Backup info data!", err
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
                f"[m/backup/job/{self._job}]: Cannot write Backup extract script!", err
            )
            return self._update(server, BACKUP_STATE_ERROR)
        self._next(server)

    def stop(self, server, force=False):
        if self._cancel.is_set():
            return
        server.info(
            f'[m/backup/job/{self._job}] Stopping Backup Job "{self._plan.uuid}".'
        )
        self._stop(server, force)

    def _check_space(self, server, file, extra=1.5):
        p = f"{self._path}/{file}"
        try:
            s, x = statvfs(p), round(float(getsize(p)) * extra)
            r = (s.f_frsize * s.f_bavail) - x
        except OSError as err:
            return server.error(
                f"[m/backup/job/{self._job}] Cannot get free space size for Backup storage!",
                err,
            )
        del s, p
        if r < 0:
            return server.error(
                f"[m/backup/job/{self._job}] Insufficient space on device, {_size(x)} needed {_size(r)} free!"
            )
        server.error(
            f"[m/backup/job/{self._job}] Free space check {_size(x)} needed {_size(r)} free."
        )
        del r, x
        return True

    def _exec_and_watch(self, server, cmd, stdin=None, add=None):
        server.debug(
            f'[m/backup/job/{self._job}]: Executing command "{" ".join(cmd)}".'
        )
        self._proc = Single.new(cmd, stdin)
        server.debug(
            f"[m/backup/job/{self._job}]: Command started, PID {self._proc.pid()}."
        )
        self._proc.nice()
        if add is None:
            return server.watch(self._proc, self._next, (server,))
        return server.watch(self._proc, self._next, (server, add))


class Schedule(object):
    __slots__ = ("_days", "_cycle", "_increment")

    def __init__(self, data):
        if not isinstance(data, dict):
            self._days, self._cycle, self._increment = None, None, None
        else:
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
        return isinstance(self._cycle, int) and count >= self._cycle

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
        if self.poll() is not None:
            return self.wait()
        try:
            self.send_signal(SIGINT)
        except (OSError, SubprocessError):
            pass
        try:
            self.terminate()
        except (OSError, SubprocessError):
            pass
        try:
            self.send_signal(SIGKILL)
        except (OSError, SubprocessError):
            pass
        if self.poll() is not None:
            return self.poll()
        try:
            self.kill()
        except (OSError, SubprocessError):
            pass
        try:
            kill(self.p1.pid, SIGKILL)
        except OSError:
            pass
        try:
            kill(self.p2.pid, SIGKILL)
        except OSError:
            pass
        try:
            self.wait(timeout=1)
        except (OSError, SubprocessError):
            pass
        return None

    def output(self):
        r = max(self.p1.wait(), self.p2.wait())
        x, o, e = self.p1.stderr.read(), self.p2.stdout.read(), self.p2.stderr.read()
        v = _apes(x) + _apes(o) + _apes(e, True)
        del x, e
        if len(v) == 0 or NEWLINE not in v:
            return (r, o, v)
        d = list()
        for i in v.split(NEWLINE):
            if i.startswith("Removing leading"):
                continue
            n = i.strip()
            if len(v) > 0:
                d.append(n)
            del n
        del v
        v = ";".join(d)
        if v[-1] == ";":
            v = v[:-1]
        return (r, o, v)

    def terminate(self):
        self.p1.terminate()
        self.p2.terminate()

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
        if self.poll() is not None:
            return self.wait()
        try:
            self.send_signal(SIGINT)
        except (OSError, SubprocessError):
            pass
        try:
            self.terminate()
        except (OSError, SubprocessError):
            pass
        try:
            self.send_signal(SIGKILL)
        except (OSError, SubprocessError):
            pass
        if self.poll() is not None:
            return self.poll()
        try:
            self.kill()
        except (OSError, SubprocessError):
            pass
        try:
            kill(self.p1.pid, SIGKILL)
        except OSError:
            pass
        try:
            self.wait(timeout=1)
        except (OSError, SubprocessError):
            pass
        return None

    def output(self):
        r, o = self.p1.wait(), self.p1.stdout.read()
        v = _apes(o) + _apes(self.p1.stderr.read(), True)
        if len(v) == 0 or NEWLINE not in v:
            return (r, o, v)
        d = list()
        for i in v.split(NEWLINE):
            if i.startswith("Removing leading"):
                continue
            n = i.strip()
            if len(v) > 0:
                d.append(n)
            del n
        del v
        v = ";".join(d)
        if v[-1] == ";":
            v = v[:-1]
        return (r, o, v)

    def terminate(self):
        self.p1.terminate()

    def wait(self, timeout=None):
        return self.p1.wait(timeout)

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
        try:
            s = read_json(BACKUP_STATE, errors=False)
        except OSError as err:
            server.warning("[m/backup]: Cannot read the Backup state file!", err)
            s = dict()
        else:
            if not isinstance(s, dict):
                s = dict()
        if self._current is not None and self._current.running():
            c = self._current._plan.uuid
        else:
            c = None
        r = list()
        for i in p.entries:
            if i.uuid == c:
                try:
                    v = BACKUP_STATE_NAMES[self._current._state].title()
                except IndexError:
                    v = "Error"
                if self._current.paused():
                    v = f"{v} (paused)"
            elif i.uuid in self._queue:
                v = "Queued"
            else:
                v = EMPTY
            if i.uuid in s:
                n, x = s[i.uuid].get("last"), boolean(s[i.uuid].get("error"))
                f, j = s[i.uuid].get("count"), s[i.uuid].get("size")
            else:
                n, x, f, j = None, False, None, None
            r.append(
                {
                    "last": n,
                    "size": j,
                    "uuid": i.uuid,
                    "path": i.path,
                    "full": False if isinstance(f, int) and f > 0 else True,
                    "error": x,
                    "status": v,
                    "description": i.description,
                }
            )
            del n, x, v, f, j
        del c, s, p
        return {"plans": r}

    def hook(self, server, message):
        if self._current is None or not self._current.running():
            return
        if message.header() == HOOK_SHUTDOWN:
            server.info(
                f'[m/backup]: Stopping Backup "{self._current._plan.path}" due to shutdown.'
            )
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
            server.notify(
                "Backup Status",
                f'Backup of "{self._current._plan.path}" resumed!',
                "yed",
            )
        elif message.type == MSG_PRE and not self._current.paused():
            self._current.suspend(server)

    def control(self, server, message):
        if message.type == MSG_STATUS:
            return self._status(server)
        if message.forward:
            if message.type != MSG_UPDATE or self._current is None:
                return
            if message.state == BACKUP_STATE_KEYGEN:
                return server.notify(
                    "Backup Status",
                    f'Staring a Backup of "{self._current._plan.path}"!',
                    "yed",
                )
            if message.state < BACKUP_STATE_ERROR:
                return
            self._current.stop(server)
            if self._current.save(server, BACKUP_STATE):
                server.notify(
                    "Backup Status",
                    f'Backup of "{self._current._plan.path}" completed!',
                    "yed",
                )
            else:
                server.notify(
                    "Backup Status",
                    f'Backup of "{self._current._plan.path}" was stopped with errors!',
                    "yed",
                )
            self._current = None
            if self._queue.is_empty():
                return
            server.debug("[m/backup]: Backup completed, checking queue for next Plan..")
            self._select(server)
            if self._current is None:
                return {"result": "No Backups are scheduled or could be started!"}
            return {"result": f'Started Backup "{self._current._job}"!'}
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
                    "Backup Status",
                    f'Backup of "{self._current._plan.path}" suspended.',
                    "yed",
                )
                return {"result": f'Suspended Backup "{self._current._job}".'}
            if not self._current.paused():
                return as_error("Backup is already running!")
            if not self._current.resume(server):
                return as_error("Cannot resume Backup!")
            server.notify(
                "Backup Status",
                f'Backup of "{self._current._plan.path}" resumed!',
                "yed",
            )
            return {"result": f'Resumed backup "{self._current._job}".'}
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
            return {"result": f'Backup "{self._current._job}" was stopped.'}
        p = path
        if p[-1] != "/":
            p = f"{p}/"
        if (
            self._current is not None
            and self._current.running()
            and p == self._current._plan.path
        ):
            self._current.stop(server, True)
            return {"result": f'Backup "{self._current._job}" was stopped.'}
        if self._queue.remove(p):
            return {"result": f'Backup for "{p}" was removed from the queue.'}
        return {"result": "Backup was not found in queue or running."}

    def _select(self, server, path=None, force=False, force_full=False):
        if not _on_battery(force):
            server.info("[m/backup]: Not starting a Backup on battery power.")
            return as_error(
                'Cannot run on battery power, please connect to AC power or use the "-f" switch!'
            )
        if not nes(path) and self._current is not None and self._current.running():
            return {"result": f'Backup "{self._current._job}" is currently running!'}
        try:
            p = Plans(CONFIG_BACKUP)
        except (OSError, ValueError) as err:
            server.error("[m/backup]: Cannot read the Backup config!", err)
            return as_error("Cannot load the Backup config!")
        if self._current is not None and self._current.running():
            r = self._current._plan.uuid
        else:
            r = None
        a = self._queue.add_plans(p, path, r)
        if r is not None:
            server.debug(f'[m/backup]: Not starting a Backup as "{r}" is running.')
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
        server.debug(f'[m/backup]: Selected Plan "{n.uuid}"..')
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
            f'[m/backup]: Starting Plan "{n.uuid}" as a{"n incremental" if i else " full"} backup!'
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
        return f'Backup "{self._current._job}" ({self._current._plan.path}) started!'
