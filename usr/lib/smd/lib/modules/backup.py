#!/usr/bin/false
# Module: Backup (System)
#
# Creates backup tarballs and offloads them to a secondary storage location.
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

from shutil import rmtree
from uuid import uuid4, UUID
from base64 import b64encode
from datetime import datetime
from signal import SIGSTOP, SIGCONT
from threading import Thread, Event
from lib.structs.message import Message
from lib.structs.storage import Storage
from socket import socket, AF_INET, SOCK_STREAM
from os.path import isdir, exists, isfile, getsize
from os import chmod, urandom, remove, makedirs, statvfs
from lib.util import read, read_json, write_json, run, stop
from subprocess import DEVNULL, Popen, PIPE, STDOUT, SubprocessError, TimeoutExpired
from lib.constants import (
    EMPTY,
    NEWLINE,
    HOOK_POWER,
    HOOK_BACKUP,
    BACKUP_SIZES,
    BACKUP_STATE,
    BACKUP_HOSTS,
    HOOK_SUSPEND,
    HOOK_SHUTDOWN,
    CONFIG_BACKUP,
    HOOK_HIBERNATE,
    BACKUP_TIMEOUT,
    BACKUP_KEY_SIZE,
    BACKUP_STATE_DIR,
    MESSAGE_TYPE_PRE,
    BACKUP_WAIT_TIME,
    MESSAGE_TYPE_POST,
    BACKUP_DEFAULT_DIR,
    BACKUP_STATUS_IDLE,
    BACKUP_BATTERY_PATH,
    MESSAGE_TYPE_STATUS,
    MESSAGE_TYPE_ACTION,
    MESSAGE_TYPE_CONFIG,
    BACKUP_STATUS_ERROR,
    BACKUP_STATUS_NAMES,
    BACKUP_DEFAULT_PORT,
    BACKUP_EXCLUDE_PATHS,
    BACKUP_STATUS_HASHING,
    BACKUP_STATUS_PACKING,
    BACKUP_RESTORE_SCRIPT,
    BACKUP_STATUS_UPLOADING,
    BACKUP_STATUS_ENCRYPTING,
    BACKUP_STATUS_COMPRESSING,
)

HOOKS_SERVER = {
    HOOK_POWER: "BackupServer.hook",
    HOOK_SUSPEND: "BackupServer.hook",
    HOOK_SHUTDOWN: "BackupServer.hook",
    HOOK_BACKUP: "BackupServer.control",
    HOOK_HIBERNATE: "BackupServer.hook",
}


def _get_config(path):
    c = Storage(path=path)
    p = c.get("plans")
    if isinstance(p, list) and len(p) > 0:
        for e in p:
            if not isinstance(e, dict):
                p.remove(e)
                continue
            u = e.get("uuid")
            if not isinstance(u, str) or len(u) == 0:
                e["uuid"] = str(uuid4())
            del u
            x = e.get("path")
            if not isinstance(x, str) or len(x) == 0:
                raise ValueError("Invalid or missing path value")
            if not isdir(x):
                raise ValueError(f'Backup path "{x}" does not exist')
            del x
    del p
    c.write(path, perms=0o0640)
    if not c.__contains__("upload"):
        return c
    u = c.get("upload")
    if not isinstance(u, dict):
        c.__delitem__("upload")
        c.write(path, perms=0o0640)
        return c
    h = c.get("upload.host")
    if not isinstance(h, str) and len(h) == 0:
        return c
    if "@" in h:
        i = h.find("@")
        u = h[:i]
        o = c.get("upload.user")
        if (not isinstance(o, str) or len(o) == 0) and len(u) > 0:
            c.set("upload.user", u)
        h = h[i + 1 :]
        del i
        del u
        del o
    if ":" in h:
        i = h.find(":")
        p = h[i + 1 :]
        o = c.get("upload.port")
        if (not isinstance(o, int) or o <= 0) and len(p) > 0:
            try:
                c.set("upload.port", int(p, 10))
            except ValueError:
                raise ValueError(f'Invalid port value "{p}"')
        h = h[:i]
        del i
        del p
        del o
    c.set("upload.host", h)
    del h
    p = c.get("upload.port")
    if isinstance(p, str):
        try:
            c.set("upload.port", int(p, 10))
        except ValueError:
            raise ValueError(f'Invalid port value "{p}"')
    elif p is None:
        c.set("upload.port", BACKUP_DEFAULT_PORT)
    del p
    if not c.__contains__("dir"):
        c.set("dir", BACKUP_DEFAULT_DIR)
    c.write(path, perms=0o640)
    return c


def _format_size(size):
    if size < 1024.0:
        return f"{float(size):3.1f}B"
    size /= 1024.0
    for name in BACKUP_SIZES:
        if abs(size) < 1024.0:
            return f"{float(size):3.1f}{name}iB"
        size /= 1024.0
    return f"{float(size):.1f}YiB"


def _runnable(weekday, schedule):
    if not isinstance(schedule, list) or len(schedule) == 0:
        return False
    for v in schedule:
        if not isinstance(v, str) or len(v) == 0:
            continue
        d = v.lower()
        if weekday == 0 and d[0] == "m":
            return True
        if weekday == 2 and d[0] == "w":
            return True
        if weekday == 4 and d[0] == "f":
            return True
        if len(d) < 2:
            continue
        if weekday == 1 and d[0] == "t" and d[1] == "u":
            return True
        if weekday == 3 and d[0] == "t" and d[1] == "h":
            return True
        if weekday == 5 and d[0] == "s" and d[1] == "a":
            return True
        if weekday == 6 and d[0] == "s" and d[1] == "u":
            return True
        del d
    return False


def _get_plans(config, path=None):
    p = config.get("plans")
    r = list()
    if isinstance(p, list) and len(p) > 0:
        w = datetime.now().weekday()
        for e in p:
            if path == e["path"]:
                r.append(e)
                continue
            if "schedule" not in e:
                continue
            if "days" not in e["schedule"]:
                continue
            if not _runnable(w, e["schedule"]["days"]):
                continue
            r.append(e)
    del p
    return r


def _output_to_error(output, code):
    if not isinstance(output, str) or len(output) == 0:
        return f"exit ({code})"
    if NEWLINE not in output:
        return output
    r = list()
    for line in output.split(NEWLINE):
        if line.startswith("Removing leading"):
            continue
        v = line.strip()
        if len(v) > 0:
            r.append(v)
        del v
    return f'exit ({code}): {";".join(r)}'


def _plan_state(server, plan, state):
    c = 0
    u = plan["uuid"]
    if u not in state:
        state[u] = {"count": 0}
    else:
        c = state[u].get("count")
        if not isinstance(c, int) or c < 0:
            c = 0
    f = True
    if "schedule" in plan:
        f = not plan["schedule"].get("increment", False)
        if not f:
            r = plan["schedule"].get("cycle")
            if isinstance(r, int) and c >= r:
                f = True
                state[u] = {"count": 0}
            del r
    state[u]["count"] += 1
    state[u]["stop"] = False
    state[u]["error"] = False
    state[u]["last"] = datetime.now().isoformat()
    server.debug(
        f'Running backup "{u}" as a{" full" if f else "n incremental"} backup..'
    )
    del u
    del c
    return not f


def _check_space(server, path, extra=1.5):
    s = statvfs(path)
    x = round(float(getsize(path)) * extra)
    r = (s.f_frsize * s.f_bavail) - x
    del s
    if r < 0:
        raise OSError(f"Insufficient space on device (need {_format_size(r)} free)")
    server.debug(
        f"Free space check, requested {_format_size(x)}, free {_format_size(r)}.."
    )
    del r
    del x


class BackupServer(object):
    def __init__(self):
        self.thread = None
        self.queue = dict()

    def _status(self, server):
        try:
            c = _get_config(CONFIG_BACKUP)
        except (OSError, ValueError) as err:
            server.error("Could not load Backup Config!", err=err)
            return {"error": f"Could not read the Config: {err}"}
        p = list()
        r = None
        s = read_json(BACKUP_STATE, errors=False)
        if not isinstance(s, dict):
            s = dict()
        if self.thread is not None and self.thread.running():
            r = self.thread.plan["uuid"]
        if "plans" in c and len(c["plans"]) > 0:
            for e in c["plans"]:
                v = EMPTY
                if e["uuid"] == r:
                    try:
                        v = BACKUP_STATUS_NAMES[self.thread.status].title()
                    except IndexError:
                        v = "Error"
                    if self.thread._paused:
                        v += " (paused)"
                if e["uuid"] not in s:
                    p.append(
                        {
                            "last": EMPTY,
                            "stop": False,
                            "error": False,
                            "status": v,
                            "uuid": e["uuid"],
                            "path": e["path"],
                        }
                    )
                else:
                    i = s[e["uuid"]]
                    p.append(
                        {
                            "status": v,
                            "last": i["last"],
                            "uuid": e["uuid"],
                            "path": e["path"],
                            "stop": i.get("stop", False),
                            "error": i.get("error", False),
                        }
                    )
                    del i
                del v
        del c
        del s
        del r
        return {"plans": p}

    def hook(self, server, message):
        if self.thread is None or not self.thread.running():
            return
        if message.header() == HOOK_SHUTDOWN:
            server.info(f'Stopping running Backup plan "{self.thread.plan["uuid"]}"!')
            try:
                self.thread.stop()
            except OSError as err:
                return server.error(
                    f'Could not stop the Backup plan "{self.thread.plan["uuid"]}"!',
                    err=err,
                )
            return server.notify(
                "Backup Status", "Backup was stopped due to shutdown!", "yed"
            )
        if message.type == MESSAGE_TYPE_POST and self.thread._paused:
            server.debug(f'Resuming a paused Backup plan "{self.thread.plan["uuid"]}"!')
            try:
                self.thread.resume()
            except OSError as err:
                return server.error(
                    f'Could not resume the Backup plan "{self.thread.plan["uuid"]}"!',
                    err=err,
                )
            return server.notify("Backup Status", "Backup was resumed", "yed")
        if message.type == MESSAGE_TYPE_PRE and not self.thread._paused:
            server.debug(f'Pausing a running backup plan "{self.thread.plan["uuid"]}"!')
            try:
                self.thread.pause()
            except OSError as err:
                return server.error(
                    f'Could not pause the Backup plan "{self.thread.plan["uuid"]}"!',
                    err=err,
                )
            return server.notify("Backup Status", "Backup was paused.", "yed")

    def control(self, server, message):
        if message.type == MESSAGE_TYPE_STATUS:
            return self._status(server)
        if message.type == BACKUP_STATUS_ERROR and message.forward:
            if len(self.queue) > 0:
                server.forward(
                    Message(header=HOOK_BACKUP, payload={"type": MESSAGE_TYPE_ACTION})
                )
            if self.thread is None:
                return
            self.thread = None
            if not message.get("error", False) and not message.get("stop", False):
                return
            s = read_json(BACKUP_STATE, errors=True)
            if isinstance(s, dict) and message.uuid in s:
                s[message.uuid]["stop"] = message.get("stop", False)
                s[message.uuid]["error"] = message.get("error", False)
                if s[message.uuid]["count"] > 0:
                    s[message.uuid]["count"] -= 1
            try:
                write_json(BACKUP_STATE, s, perms=0o640)
            except OSError as err:
                server.error(f"Could not save Backup state: {err}!", err=err)
            del s
            return
        if self.thread is None or not self.thread.running():
            if message.type == MESSAGE_TYPE_ACTION:
                return self._pick(
                    server, message.get("path"), message.get("force", False)
                )
            if message.type == BACKUP_STATUS_UPLOADING:
                server.debug("Clearing the Backup statistics and database cache..")
                try:
                    remove(BACKUP_STATE)
                    rmtree(BACKUP_STATE_DIR)
                except OSError as err:
                    server.error("Could not clear the Backup cache!", err=err)
                    return {"error": f"Could not clear the backup cache: {err}!"}
                return EMPTY
            return "There is currently not a Backup running!"
        if message.type == MESSAGE_TYPE_ACTION:
            return "There is currently a Backup running!"
        if message.type == MESSAGE_TYPE_POST and self.thread._paused:
            server.debug(f'Resuming a paused Backup plan "{self.thread.plan["uuid"]}"!')
            try:
                self.thread.resume()
            except OSError as err:
                server.error(
                    f'Could not resume the Backup plan "{self.thread.plan["uuid"]}"!',
                    err=err,
                )
                return {"error": f"Could not resume the Backup: {err}!"}
            server.notify("Backup Status", "Backup was resumed.", "yed")
        if message.type == MESSAGE_TYPE_PRE and not self.thread._paused:
            server.debug(f'Pausing running Backup plan "{self.thread.plan["uuid"]}"!')
            try:
                self.thread.pause()
            except OSError as err:
                server.error(
                    f'Could not pause the Backup plan "{self.thread.plan["uuid"]}"!',
                    err=err,
                )
                return {"error": f"Could not pause the Backup! ({err})"}
            server.notify("Backup Status", "Backup was paused.", "yed")
        if message.type == MESSAGE_TYPE_CONFIG:
            server.debug(f'Stopping running Backup plan "{self.thread.plan["uuid"]}"!')
            try:
                self.thread.stop()
            except OSError as err:
                server.error(
                    f'Could not stop the Backup plan "{self.thread.plan["uuid"]}"!',
                    err=err,
                )
                return {"error": f"Could not stop the Backup: {err}!"}
            server.notify("Backup Status", "Backup was stopped!", "yed")
        return EMPTY

    def _pick(self, server, path=None, force=False):
        a = read(BACKUP_BATTERY_PATH, errors=False)
        if not force and (a is None or len(a) == 0 or a[0] == "0"):
            server.info("Not triggering a Backup as we are on battery power!")
            return 'Cannot run a Backup on AC power, please connect power or use the "-f" switch!'
        del a
        try:
            c = _get_config(CONFIG_BACKUP)
        except (OSError, ValueError) as err:
            server.error("Could not load Backup config!", err=err)
            return f"Could not load Backup config: {err}!"
        for e in _get_plans(c, path):
            if e["uuid"] in self.queue:
                continue
            if (
                self.thread is not None
                and self.thread.running()
                and self.thread.plan["uuid"] == e["uuid"]
            ):
                continue
            self.queue[e["uuid"]] = e
        if self.thread is not None and self.thread.running():
            server.debug(
                f'Not triggering a Backup as "{self.thread.plan["uuid"]}" is currently running.'
            )
            return "Cannot run a Backup while one is running!"
        if len(self.queue) == 0:
            server.debug(
                "Not triggering a Backup as there are no plans able to execute."
            )
            return "No scheduled or specified Backup plans to choose from!"
        server.debug(
            f"Backup config and plans loaded, {len(self.queue)} plans are ready to run!"
        )
        s = read_json(BACKUP_STATE, errors=False)
        if not isinstance(s, dict):
            s = dict()
        e = self._pick_plan(server, path, force, s)
        if not isinstance(e, dict):
            server.debug(
                "Not triggering a Backup as there are no plans able to execute."
            )
            return "No Backup plans scheduled or specified!"
        server.debug(f'Selected plan "{e["uuid"]}" to be run..')
        x = _plan_state(server, e, s)
        try:
            write_json(BACKUP_STATE, s, perms=0o640)
        except OSError as err:
            server.error("Could not save backup state!", err=err)
            return f"Could not save backup state: {err}!"
        k = e.get("public_key")
        if not isinstance(k, str) or len(k) == 0:
            k = c.get("public_key")
        self.thread = BackupThread(
            server,
            e,
            c.get("dir", BACKUP_DEFAULT_DIR),
            k,
            c.get("upload.host"),
            c.get("upload.key"),
            c.get("upload.user"),
            c.get("upload.port"),
            x,
        )
        self.thread.start()
        server.info(f'Started Backup thread for plan "{e["uuid"]}"!')
        del s
        del c
        del x
        del k
        return f'Backup for "{e["path"]}" was started!'

    def _pick_plan(self, server, path, force, state):
        n = datetime.now()
        while len(self.queue) > 0:
            u, e = self.queue.popitem()
            if not isinstance(e, dict):
                continue
            if "uuid" not in e:
                server.warning("Skipping Backup plan with an non-existant UUID!")
                continue
            try:
                UUID(e["uuid"])
            except ValueError:
                server.warning("Skipping Backup plan with an invalid UUID!")
                continue
            if isinstance(path, str):
                if path == e["path"]:
                    return e
                else:
                    continue
            if force:
                return e
            if u in state:
                t = state[u].get("last")
                if not isinstance(t, str) or len(t) == 0:
                    return e
                try:
                    if (
                        n - datetime.fromisoformat(t)
                    ).total_seconds() > BACKUP_WAIT_TIME:
                        return e
                    if state[u].get("error", False) or state[u].get("stop", False):
                        return e
                except ValueError:
                    pass
                server.debug(
                    f'Skipping Backup "{u}" as it has not be 24hrs since last runtime!'
                )
                del t
                continue
            del u
            return e
        del n
        return None


class BackupThread(Thread):
    def __init__(self, server, plan, dst, key, host, acl, user, port, inc):
        Thread.__init__(self, name="SMDBackupThread", daemon=False)
        self.dst = dst
        self.acl = acl
        self.key = key
        self.plan = plan
        self.host = host
        self.user = user
        self.port = port
        self._proc = None
        self._output = None
        self._paused = False
        self.server = server
        self.increment = inc
        self._cancel = Event()
        self.status = BACKUP_STATUS_IDLE
        self._file = (
            f'smd-backup-{datetime.now().strftime("%Y%m%d-%H%M")}-{plan["uuid"][:8]}'
        )
        self.path = f"{dst}/{self._file}"

    def run(self):
        if isdir(self.path):
            try:
                rmtree(self.path)
            except OSError as err:
                self.server.error(
                    f'Could not remove Backup directory "{self.path}"!', err=err
                )
                return self.server.forward(
                    Message(
                        header=HOOK_BACKUP,
                        payload={
                            "error": True,
                            "uuid": self.plan["uuid"],
                            "type": BACKUP_STATUS_ERROR,
                        },
                    )
                )
        if isinstance(self.host, str) and len(self.host) > 0 and self.port > 0:
            s = socket(AF_INET, SOCK_STREAM)
            try:
                s.settimeout(5)
                s.connect((self.host, self.port))
            except OSError:
                self.server.notify(
                    "Backup Status",
                    f'Not starting a Backup as "{self.host}" is not reachable!',
                    "yed",
                )
                self.server.error(
                    f'Could not connect to the upload server "{self.host}:{self.port}", Backup will not continue!'
                )
                return self.server.forward(
                    Message(
                        header=HOOK_BACKUP,
                        payload={
                            "error": True,
                            "uuid": self.plan["uuid"],
                            "type": BACKUP_STATUS_ERROR,
                        },
                    )
                )
            finally:
                s.close()
                del s
        try:
            makedirs(self.path, mode=0o750, exist_ok=True)
        except OSError as err:
            self.server.error(
                f'Could not make Backup directory "{self.path}"!', err=err
            )
            return self.server.forward(
                Message(
                    header=HOOK_BACKUP,
                    payload={
                        "error": True,
                        "uuid": self.plan["uuid"],
                        "type": BACKUP_STATUS_ERROR,
                    },
                )
            )
        self.server.notify(
            "Backup Status", f'Staring a Backup of "{self.plan["path"]}"!', "yed"
        )
        try:
            self._process()
        except Exception as err:
            self.status = BACKUP_STATUS_ERROR
            self.server.error("Unexpected error during backup runtime!", err=err)
        if self.status == BACKUP_STATUS_ERROR:
            if self._cancel.is_set():
                self.server.notify(
                    "Backup Status",
                    f'Backup of "{self.plan["path"]}" was stopped!',
                    "yed",
                )
            else:
                self.server.notify(
                    "Backup Status",
                    f'Backup of "{self.plan["path"]}" encountered an error!',
                    "yed",
                )
        else:
            self.server.notify(
                "Backup Status", f'Backup of "{self.plan["path"]}" completed!', "yed"
            )
        try:
            self.stop()
        except Exception as err:
            self.server.warning("Error stopping Backup!", err=err)
        if isdir(self.path):
            try:
                rmtree(self.path)
            except OSError as err:
                self.server.error(
                    f'Error removing Backup directory "{self.path}"!', err=err
                )
        return self.server.forward(
            Message(
                header=HOOK_BACKUP,
                payload={
                    "uuid": self.plan["uuid"],
                    "type": BACKUP_STATUS_ERROR,
                    "stop": self._cancel.is_set(),
                    "error": self.status == BACKUP_STATUS_ERROR,
                },
            )
        )

    def stop(self):
        if not self._running():
            return
        self._cancel.set()
        try:
            self._proc.kill()
        except (SubprocessError, OSError) as err:
            self.server.error("Error stopping Backup process!", err=err)
        stop(self._proc)
        self._paused = False
        return self._wait()

    def pause(self):
        if not self._running() or self._paused:
            return
        try:
            self._proc.send_signal(SIGSTOP)
        except (SubprocessError, OSError) as err:
            raise OSError(f"Failed to pause process: {err}") from err
        self._paused = True

    def resume(self):
        if not self._running() or not self._paused:
            return
        try:
            self._proc.send_signal(SIGCONT)
        except (SubprocessError, OSError) as err:
            raise OSError(f"Failed to continue process: {err}") from err
        self._paused = False

    def running(self):
        return not self._cancel.is_set()

    def _running(self):
        if self._cancel.is_set():
            return False
        return self._proc is not None and self._proc.poll() is None

    def _process(self):
        self._paused = False
        try:
            self.status = BACKUP_STATUS_COMPRESSING
            self._step_compress()
            self.server.debug("Compression step completed!")
        except OSError as err:
            self.status = BACKUP_STATUS_ERROR
            if self._cancel.is_set():
                return
            return self.server.error("Error during the Compression step!", err=err)
        if self._cancel.is_set():
            raise OSError("Backup was stopped")
        _check_space(self.server, f"{self.path}/data.tar.zx", 2.5)
        self._paused = False
        try:
            self.status = BACKUP_STATUS_HASHING
            self._step_hash()
            self.server.debug("Hashing step completed!")
        except OSError as err:
            self.status = BACKUP_STATUS_ERROR
            if self._cancel.is_set():
                return
            return self.server.error("Error during the Hashing step!", err=err)
        if self._cancel.is_set():
            raise OSError("Backup was stopped")
        self._paused = False
        try:
            self.status = BACKUP_STATUS_ENCRYPTING
            self._step_encrypt()
            self.server.debug("Encryption step completed!")
        except OSError as err:
            self.status = BACKUP_STATUS_ERROR
            if self._cancel.is_set():
                return
            return self.server.error("Error during the Encryption step!", err=err)
        if self._cancel.is_set():
            raise OSError("Backup was stopped")
        _check_space(self.server, f"{self.path}/data.ebf")
        self._paused = False
        try:
            self.status = BACKUP_STATUS_PACKING
            self._step_pack()
            self.server.debug("Packing step completed!")
        except OSError as err:
            self.status = BACKUP_STATUS_ERROR
            if self._cancel.is_set():
                return
            return self.server.error("Error during the Packing step!", err=err)
        if self._cancel.is_set():
            raise OSError("Backup was stopped")
        self._paused = False
        try:
            self.status = BACKUP_STATUS_UPLOADING
            self._step_upload()
            self.server.debug("Upload step completed!")
        except OSError as err:
            self.status = BACKUP_STATUS_ERROR
            if self._cancel.is_set():
                return
            return self.server.error("Error during the Uploading step!", err=err)
        if not self._cancel.is_set():
            return
        raise OSError("Backup was stopped")

    def _step_hash(self):
        self._execute(["/bin/sha256sum", "--binary", f"{self.path}/data.tar.zx"])
        if self._wait() != 0:
            raise OSError(_output_to_error(self._output, self._proc.returncode))
        h = self._output.replace(f"*{self.path}/", EMPTY)
        with open(f"{self.path}/data.sum", "w") as f:
            f.write(h)
        i = h.find(" ")
        h = h[:i]
        del i
        d = self.plan.get("description")
        if not isinstance(d, str) or len(d) == 0:
            d = f'Backup of "{self.plan["path"]}" on {datetime.now().strftime("%A %d, %B %m, %Y %R")}'
        with open(f"{self.path}/info.txt", "w") as f:
            f.write(
                f'{d}\n\nSOURCE: {self.plan["path"]}\nSHA256: {h}\nSIZE:   '
                f'{_format_size(getsize(f"{self.path}/data.tar.zx"))}\nDATE:   '
                f'{datetime.now().strftime("%b %d %Y %H:%M:%S")}\nTYPE:   '
                f'{"Incremental" if self.increment else "Full"}\n'
            )
        del d
        del h
        with open(f"{self.path}/extract.sh", "w") as f:
            f.write(BACKUP_RESTORE_SCRIPT)

    def _step_pack(self):
        self._execute(
            [
                "/bin/tar",
                "-c",
                "-C",
                self.dst,
                "--sparse",
                "--no-acls",
                "--no-xattrs",
                "--recursion",
                "--totals=USR1",
                "--remove-files",
                "--one-file-system",
                "-f",
                f"{self.dst}/{self._file}.tar",
                self._file,
            ]
        )
        if self._wait() > 1:
            raise OSError(_output_to_error(self._output, self._proc.returncode))
        if not isdir(self.path):
            return
        rmtree(self.path)

    def _step_upload(self):
        if not isinstance(self.port, int) or self.port == 0:
            return self.server.warning(
                "Skipping upload as the target host port is invalid!"
            )
        if not isinstance(self.host, str) or len(self.host) == 0:
            return self.server.warning(
                "Skipping upload as the target host is not present!"
            )
        if not exists(BACKUP_HOSTS):
            raise OSError(
                f'Unable to upload Backup, the known hosts file "{BACKUP_HOSTS}" is missing! Please use "'
                'ssh -o UserKnownHostsFile=file user@host" to generate the file and copy it.'
            )
        o = f"/bin/ssh -o VisualHostKey=no -o UserKnownHostsFile={BACKUP_HOSTS} -p {self.port}"
        if isinstance(self.acl, str) and len(self.acl) > 0:
            try:
                chmod(self.acl, 0o0400, follow_symlinks=True)
            except OSError:
                pass
            o += f" -i {self.acl}"
        h = self.host
        if isinstance(self.user, str) and len(self.user) > 0:
            h = f"{self.user}@{h}"
        f = f"{self.dst}/{self._file}.tar"
        self._execute(
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
                f"{h}:",
            ]
        )
        del h
        del o
        r = self._wait()
        s = getsize(f)
        if not self.plan.get("keep", False):
            remove(f)
        del f
        if r != 0:
            raise OSError(_output_to_error(self._output, self._proc.returncode))
        del r
        self.server.debug(
            f'Uploaded backup of size {_format_size(s)} to "{self.host}"!'
        )
        del s

    def _step_encrypt(self):
        if not isinstance(self.key, str) or len(self.key) == 0:
            return self.server.warning(
                "Skipping encryption as there is not a valid public key present!"
            )
        if not exists(self.key):
            return self.server.warning(
                f'Skipping encryption as the public key "{self.key}" does not exist!'
            )
        k = b64encode(urandom(BACKUP_KEY_SIZE)).decode("UTF-8")
        try:
            if (
                self._execute(
                    [
                        "/bin/openssl",
                        "pkeyutl",
                        "-encrypt",
                        "-pubin",
                        "-in",
                        "-",
                        "-inkey",
                        self.key,
                        "-out",
                        f"{self.path}/data.pem",
                    ],
                    stdin=k,
                )
                != 0
            ):
                raise OSError(_output_to_error(self._output, self._proc.returncode))
        except OSError as err:
            k = None
            raise err
        try:
            if (
                self._execute(
                    [
                        "/bin/openssl",
                        "aes-256-cbc",
                        "-e",
                        "-a",
                        "-pbkdf2",
                        "-pass",
                        "stdin",
                        "-in",
                        f"{self.path}/data.tar.zx",
                        "-out",
                        f"{self.path}/data.ebf",
                    ],
                    stdin=f"{k}\n",
                )
                != 0
            ):
                raise OSError(_output_to_error(self._output, self._proc.returncode))
        finally:
            del k
        remove(f"{self.path}/data.tar.zx")

    def _step_compress(self):
        c = [
            "/bin/tar",
            "-c",
            "--zstd",
            "--sparse",
            "--warning=no-xdev",
            "--warning=no-file-ignored",
            "--warning=no-file-changed",
            "--warning=no-file-removed",
            "--preserve-permissions",
            "--xattrs",
            "--acls",
            "--one-file-system",
            "--recursion",
            "--totals=USR1",
            f"--exclude={self.dst}",
            f"--exclude={self.path}",
        ]
        for e in BACKUP_EXCLUDE_PATHS:
            c.append(f"--exclude={e}")
        x = self.plan.get("exclude")
        if isinstance(x, list) and len(x) > 0:
            for e in x:
                c.append(f"--exclude={e}")
        del x
        d = f"{BACKUP_STATE_DIR}/{self.plan['uuid']}.db"
        if not self.increment and isfile(d):
            remove(d)
        makedirs(BACKUP_STATE_DIR, exist_ok=True)
        chmod(BACKUP_STATE_DIR, 0o0750, follow_symlinks=False)
        c.append(f"--listed-incremental={d}")
        del d
        c += ["-f", f"{self.path}/data.tar.zx", self.plan["path"]]
        self._execute(c)
        del c
        if self._wait() <= 1:
            return
        raise OSError(_output_to_error(self._output, self._proc.returncode))

    def _wait(self, timeout=BACKUP_TIMEOUT):
        if self._proc is None:
            return None
        if self._proc.poll() is not None:
            return self._proc.returncode
        while not self._cancel.is_set():
            try:
                self._proc.wait(timeout)
                break
            except TimeoutExpired:
                if self._paused:
                    continue
                self._proc.kill()
                raise OSError("Error waiting for process: TimeoutExpired")
            except (SubprocessError, OSError) as err:
                raise OSError(f"Error waiting for process: {err}") from err
        if self._cancel.is_set():
            return self._proc.returncode
        try:
            self._output = self._proc.stdout.read()
        except (SubprocessError, OSError) as err:
            raise OSError(f"Error reading process output: {err}") from err
        return self._proc.returncode

    def _execute(self, command, stdin=None, timeout=BACKUP_TIMEOUT):
        i = DEVNULL
        if stdin is not None:
            i = PIPE
        self._output = None
        try:
            self._proc = Popen(
                command,
                stdin=i,
                text=True,
                stdout=PIPE,
                stderr=STDOUT,
                encoding="UTF-8",
                universal_newlines=True,
            )
        except (SubprocessError, OSError) as err:
            raise OSError(
                f'Error starting command "{" ".join(command)}": {err}'
            ) from err
        del i
        run(
            ["/usr/bin/renice", "-n", "15", "--pid", f"{self._proc.pid}"],
        )
        run(
            ["/usr/bin/ionice", "-c", "3", "-p", f"{self._proc.pid}"],
        )
        if stdin is None:
            return self._wait(timeout)
        try:
            self._proc.communicate(stdin, timeout=timeout)
        except (SubprocessError, OSError) as err:
            raise OSError(f"Error sending STDIN data to command: {err}") from err
        return self._wait(timeout)
