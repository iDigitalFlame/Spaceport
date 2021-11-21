#!/usr/bin/false
# Module: Brightness (System)
#
# Sets and changes the System Brightness.
#
# System Management Daemon
#
# Copyright (C) 2016 - 2021 iDigitalFlame
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

from uuid import uuid4
from shutil import rmtree
from base64 import b64encode
from datetime import datetime
from signal import SIGSTOP, SIGCONT
from threading import Thread, Event
from lib.structs.message import Message
from lib.structs.storage import Storage
from socket import socket, AF_INET, SOCK_STREAM
from os.path import isdir, exists, isfile, getsize
from lib.util import read, read_json, write_json, run
from os import chmod, urandom, remove, makedirs, statvfs
from subprocess import DEVNULL, Popen, PIPE, STDOUT, SubprocessError, TimeoutExpired
from lib.constants import (
    EMPTY,
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


def _format_size(size):
    if size < 1024.0:
        return f"{float(size):3.1f}B"
    size /= 1024.0
    for name in BACKUP_SIZES:
        if abs(size) < 1024.0:
            return f"{float(size):3.1f}{name}iB"
        size /= 1024.0
    return f"{float(size):.1f}YiB"


def _get_config(file_path):
    config = Storage(file_path=file_path)
    plans = config.get("plans")
    if isinstance(plans, list):
        for plan in plans:
            if not isinstance(plan, dict):
                plans.remove(plan)
                continue
            uuid = plan.get("uuid")
            if not isinstance(uuid, str) or len(uuid) == 0:
                plan["uuid"] = str(uuid4())
            del uuid
            path = plan.get("path")
            if not isinstance(path, str) or len(path) == 0:
                raise ValueError("Invalid or missing path value!")
            if not isdir(path):
                raise ValueError(f'Backup path "{path}" does not exist!')
            del path
    del plans
    config.write(file_path, ignore_errors=False, perms=0o640)
    if not config.__contains__("upload"):
        return config
    upload = config.get("upload")
    if not isinstance(upload, dict):
        config.__delitem__("upload")
        config.write(file_path, ignore_errors=False, perms=0o640)
        return config
    host = config.get("upload.host")
    if not isinstance(host, str) and len(host) == 0:
        return config
    if "@" in host:
        idx = host.find("@")
        user = host[:idx]
        user_orig = config.get("upload.user")
        if (not isinstance(user_orig, str) or len(user_orig) == 0) and len(user) > 0:
            config.set("upload.user", user)
        host = host[idx + 1 :]
        del idx
        del user
        del user_orig
    if ":" in host:
        idx = host.find(":")
        port = host[idx + 1 :]
        port_orig = config.get("upload.port")
        if (not isinstance(port_orig, int) or port_orig <= 0) and len(port) > 0:
            try:
                config.set("upload.port", int(port))
            except ValueError:
                raise ValueError(f'Invalid port value "{port}"!')
        host = host[:idx]
        del idx
        del port
        del port_orig
    config.set("upload.host", host)
    del host
    port = config.get("upload.port")
    if isinstance(port, str):
        try:
            config.set("upload.port", int(port))
        except ValueError:
            raise ValueError(f'Invalid port value "{port}"!')
    elif port is None:
        config.set("upload.port", BACKUP_DEFAULT_PORT)
    del port
    if not config.__contains__("dir"):
        config.set("dir", BACKUP_DEFAULT_DIR)
    config.write(file_path, ignore_errors=False, perms=0o640)
    return config


def _runnable(weekday, schedule):
    if not isinstance(schedule, list) or len(schedule) == 0:
        return False
    for day in schedule:
        if not isinstance(day, str) or len(day) == 0:
            continue
        d = day.lower()
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
    plans = config.get("plans")
    runnable = list()
    if not isinstance(plans, list) or len(plans) == 0:
        return runnable
    weekday = datetime.now().weekday()
    for plan in plans:
        if path == plan["path"]:
            runnable.append(plan)
            continue
        if "schedule" not in plan:
            continue
        if "days" not in plan["schedule"]:
            continue
        if not _runnable(weekday, plan["schedule"]["days"]):
            continue
        runnable.append(plan)
    del plans
    return runnable


def _output_to_error(output, code):
    if not isinstance(output, str) or len(output) == 0:
        return f"exit ({code})"
    if "\n" not in output:
        return output
    results = list()
    for line in output.split("\n"):
        if line.startswith("Removing leading"):
            continue
        results.append(line)
    return f'exit ({code}): {"; ".join(results)}'


def _plan_state(server, plan, state):
    count = 0
    uuid = plan["uuid"]
    if uuid not in state:
        state[uuid] = {"count": 0}
    else:
        count = state[uuid].get("count")
        if not isinstance(count, int) or count < 0:
            count = 0
    full = True
    if "schedule" in plan:
        full = not plan["schedule"].get("increment", False)
        if not full:
            runs = plan["schedule"].get("cycle")
            if isinstance(runs, int) and count >= runs:
                full = True
                state[uuid] = {"count": 0}
    state[uuid]["count"] += 1
    state[uuid]["stop"] = False
    state[uuid]["error"] = False
    state[uuid]["last"] = datetime.now().isoformat()
    server.debug(
        f'Running backup "{uuid}" as a {"full" if full else "incremental"} backup...'
    )
    del uuid
    del count
    return not full


def _check_space(server, path, extra=1.5):
    space = statvfs(path)
    size = round(float(getsize(path)) * extra)
    left = (space.f_frsize * space.f_bavail) - size
    del space
    if left < 0:
        raise OSError(
            f"Insufficient space on device (need {_format_size(left)} free MB)!"
        )
    server.debug(
        f"Free space check. Requested {_format_size(size)}, free {_format_size(left)}."
    )
    del left
    del size


class BackupServer(object):
    def __init__(self):
        self.thread = None
        self.queue = dict()

    def _status(self, server):
        try:
            config = _get_config(CONFIG_BACKUP)
        except (OSError, ValueError) as err:
            server.error(f"Could not load backup config: {err}!", err=err)
            return {"error": f"Could not read the backup config! ({err})"}
        plans = list()
        running = None
        state = read_json(BACKUP_STATE)
        if not isinstance(state, dict):
            state = dict()
        if self.thread is not None and self.thread.running():
            running = self.thread.plan["uuid"]
        if "plans" in config and len(config["plans"]) > 0:
            for plan in config["plans"]:
                current = EMPTY
                if plan["uuid"] == running:
                    try:
                        current = BACKUP_STATUS_NAMES[self.thread.status].title()
                    except IndexError:
                        current = "Error"
                    if self.thread._paused:
                        current += " (paused)"
                if plan["uuid"] not in state:
                    plans.append(
                        {
                            "last": EMPTY,
                            "stop": False,
                            "error": False,
                            "status": current,
                            "uuid": plan["uuid"],
                            "path": plan["path"],
                        }
                    )
                else:
                    info = state[plan["uuid"]]
                    plans.append(
                        {
                            "status": current,
                            "last": info["last"],
                            "uuid": plan["uuid"],
                            "path": plan["path"],
                            "stop": info.get("stop", False),
                            "error": info.get("error", False),
                        }
                    )
                    del info
                del current
        del state
        del running
        return {"plans": plans}

    def hook(self, server, message):
        if message.header() == HOOK_SHUTDOWN:
            if self.thread is None or not self.thread.running():
                return
            server.info(f'Stopping a running backup plan "{self.thread.plan["uuid"]}"!')
            try:
                self.thread.stop()
            except OSError as err:
                server.error(f"Could not stop the running backup: {err}!", err=err)
            return server.notify(
                "Backup Status",
                "Backup was stopped due to shutdown!",
                "yed",
            )
        if self.thread is None or not self.thread.running():
            return
        if message.type == MESSAGE_TYPE_POST and self.thread._paused:
            server.debug(f'Resuming a paused backup plan "{self.thread.plan["uuid"]}"!')
            try:
                self.thread.resume()
            except OSError as err:
                server.error(f"Could not resume the running backup: {err}!", err=err)
            return server.notify("Backup Status", "Backup was resumed", "yed")
        if message.type == MESSAGE_TYPE_PRE and not self.thread._paused:
            server.debug(f'Pausing a running backup plan "{self.thread.plan["uuid"]}"!')
            try:
                self.thread.pause()
            except OSError as err:
                server.error(f"Could not pause the running backup: {err}!", err=err)
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
            state = read_json(BACKUP_STATE)
            if isinstance(state, dict) and message.uuid in state:
                state[message.uuid]["stop"] = message.get("stop", False)
                state[message.uuid]["error"] = message.get("error", False)
                if state[message.uuid]["count"] > 0:
                    state[message.uuid]["count"] -= 1
            try:
                write_json(
                    BACKUP_STATE,
                    state,
                    indent=4,
                    sort=True,
                    ignore_errors=False,
                    perms=0o640,
                )
            except OSError as err:
                server.error(f"Could not save backup state: {err}!", err=err)
            return
        if self.thread is None or not self.thread.running():
            if message.type == MESSAGE_TYPE_ACTION:
                return self._pick(
                    server, message.get("path"), message.get("force", False)
                )
            if message.type == BACKUP_STATUS_UPLOADING:
                server.debug(
                    "Attempting to clear backup statistics and database cache..."
                )
                try:
                    remove(BACKUP_STATE)
                    rmtree(BACKUP_STATE_DIR)
                except OSError as err:
                    return {"error": f"Could not clear the backup cache! {err}"}
                server.debug("Cleared the backup statistics and database cache!")
                return EMPTY
            return "There is currently not a backup running!"
        if message.type == MESSAGE_TYPE_ACTION:
            return "There is currently a backup running!"
        if message.type == MESSAGE_TYPE_POST and self.thread._paused:
            server.debug(f'Resuming a paused backup plan "{self.thread.plan["uuid"]}"!')
            try:
                self.thread.resume()
            except OSError as err:
                return {"error": f"Could not resume the backup! {err}"}
            server.notify("Backup Status", "Backup was resumed.", "yed")
        if message.type == MESSAGE_TYPE_PRE and not self.thread._paused:
            server.debug(f'Pausing a running backup plan "{self.thread.plan["uuid"]}"!')
            try:
                self.thread.pause()
            except OSError as err:
                return {"error": f"Could not pause the backup! ({err})"}
            server.notify("Backup Status", "Backup was paused.", "yed")
        if message.type == MESSAGE_TYPE_CONFIG:
            server.debug(
                f'Stopping a running backup plan "{self.thread.plan["uuid"]}"!'
            )
            try:
                self.thread.stop()
            except OSError as err:
                return {"error": f"Could not stop the backup! ({err})"}
            server.notify("Backup Status", "Backup was stopped!", "yed")
        return EMPTY

    def _pick(self, server, path=None, force=False):
        on_ac = read(BACKUP_BATTERY_PATH, ignore_errors=True)
        if not force and (on_ac is None or len(on_ac) == 0 or on_ac[0] == "0"):
            server.info("Not triggering a backup as we are on battery power!")
            return 'Cannot run a backup on AC power, please connect power or use the "-f" switch!'
        try:
            config = _get_config(CONFIG_BACKUP)
        except (OSError, ValueError) as err:
            server.error(f"Could not load/save backup config: {err}!", err=err)
            return f"Could not load backup config: {err}!"
        for plan in _get_plans(config, path):
            if plan["uuid"] in self.queue:
                continue
            self.queue[plan["uuid"]] = plan
        if self.thread is not None and self.thread.running():
            server.debug(
                f'Not triggering a backup as a backup "{self.thread.plan["uuid"]}" is running.'
            )
            return "Cannot run a backup while a backup is running!"
        if len(self.queue) == 0:
            server.debug("Not triggering a backup as there are not plans to do!")
            return "No scheduled or specified backup plans to choose from!"
        server.debug(
            f"Backup config and plans loaded, {len(self.queue)} plans are ready to run!"
        )
        plan = None
        state = read_json(BACKUP_STATE)
        if not isinstance(state, dict):
            state = dict()
        plan = self._pick_plan(server, path, force, state)
        if not isinstance(plan, dict):
            server.debug("Not triggering a backup as there are no plans to do!")
            return "No backup plans scheduled or specified!"
        server.debug(f'Selected plan "{plan["uuid"]}" to be run...')
        increment = _plan_state(server, plan, state)
        try:
            write_json(
                BACKUP_STATE,
                state,
                indent=4,
                sort=True,
                ignore_errors=False,
                perms=0o640,
            )
        except OSError as err:
            server.error(f"Could not save backup state: {err}!", err=err)
            return f"Could not save backup state: {err}!"
        public_key = plan.get("public_key")
        if not isinstance(public_key, str) or len(public_key) == 0:
            public_key = config.get("public_key")
        self.thread = BackupThread(
            server,
            plan,
            config.get("dir", BACKUP_DEFAULT_DIR),
            public_key,
            config.get("upload.host"),
            config.get("upload.key"),
            config.get("upload.user"),
            config.get("upload.port"),
            increment,
        )
        self.thread.start()
        server.info(f'Started Backup thread for plan "{plan["uuid"]}"!')
        del state
        del config
        del increment
        del public_key
        return f'Backup for "{plan["path"]}" was started!'

    def _pick_plan(self, server, path, force, state):
        now = datetime.now()
        while len(self.queue) > 0:
            uuid, plan = self.queue.popitem()
            if not isinstance(plan, dict):
                continue
            if isinstance(path, str):
                if path == plan["path"]:
                    return plan
                else:
                    continue
            if force:
                return plan
            if uuid in state:
                last = state[uuid].get("last")
                if not isinstance(last, str) or len(last) == 0:
                    return plan
                try:
                    if (
                        now - datetime.fromisoformat(last)
                    ).total_seconds() > BACKUP_WAIT_TIME:
                        return plan
                    if state[uuid].get("error", False) or state[uuid].get(
                        "stop", False
                    ):
                        return plan
                except ValueError:
                    pass
                server.debug(
                    f'Skipping backup "{uuid}" as it has not be 24hrs since last runtime!'
                )
                continue
            return plan
        del now
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
                    f'Could not remove backup directory "{self.path}": {err}!',
                    err=err,
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
                    f'Not starting a backup as the upload server "{self.host}" is not reachable!',
                    "yed",
                )
                self.server.error(
                    f'Could not connect to the upload server "{self.host}:{self.port}", backup will not continue!'
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
                f'Could not make backup directory "{self.path}": {err}!',
                err=err,
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
            "Backup Status",
            f'Staring a backup of "{self.plan["path"]}"!',
            "yed",
        )
        try:
            self._process()
        except Exception as err:
            self.status = BACKUP_STATUS_ERROR
            self.server.error(
                f"Unexpected error occurred during backup runtime: {err}!",
                err=err,
            )
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
                "Backup Status",
                f'Backup of "{self.plan["path"]}" completed!',
                "yed",
            )
        try:
            self.stop()
        except Exception as err:
            self.server.warning(
                f"Unexpected error occurred when attempting to stop the backup: {err}!",
                err=err,
            )
        if isdir(self.path):
            try:
                rmtree(self.path)
            except OSError as err:
                self.server.error(
                    f'Could not remove backup directory "{self.path}": {err}!',
                    err=err,
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
            self.server.error(f"Failed to stop backup process: {err}!", err=err)
        self._paused = False
        return self._wait()

    def pause(self):
        if not self._running() or self._paused:
            return
        try:
            self._proc.send_signal(SIGSTOP)
        except (SubprocessError, OSError) as err:
            raise OSError(f"Failed to pause process: {err}")
        self._paused = True

    def resume(self):
        if not self._running() or not self._paused:
            return
        try:
            self._proc.send_signal(SIGCONT)
        except (SubprocessError, OSError) as err:
            raise OSError(f"Failed to continue process: {err}")
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
            self.server.debug("Compression backup step completed!")
        except OSError as err:
            self.status = BACKUP_STATUS_ERROR
            if self._cancel.is_set():
                return
            return self.server.error(
                f"An error occurred during the Compression backup step: {err}!",
                err=err,
            )
        if self._cancel.is_set():
            raise OSError("Backup was Stopped")
        _check_space(self.server, f"{self.path}/data.tar.zx", 2.5)
        self._paused = False
        try:
            self.status = BACKUP_STATUS_HASHING
            self._step_hash()
            self.server.debug("Hashing backup step completed!")
        except OSError as err:
            self.status = BACKUP_STATUS_ERROR
            if self._cancel.is_set():
                return
            return self.server.error(
                f"An error occurred during the Hashing backup step: {err}!",
                err=err,
            )
        if self._cancel.is_set():
            raise OSError("Backup was Stopped")
        self._paused = False
        try:
            self.status = BACKUP_STATUS_ENCRYPTING
            self._step_encrypt()
            self.server.debug("Encryption backup step completed!")
        except OSError as err:
            self.status = BACKUP_STATUS_ERROR
            if self._cancel.is_set():
                return
            return self.server.error(
                f"An error occurred during the Encryption backup step: {err}!",
                err=err,
            )
        if self._cancel.is_set():
            raise OSError("Backup was Stopped")
        _check_space(self.server, f"{self.path}/data.ebf")
        self._paused = False
        try:
            self.status = BACKUP_STATUS_PACKING
            self._step_pack()
            self.server.debug("Packing backup step completed!")
        except OSError as err:
            self.status = BACKUP_STATUS_ERROR
            if self._cancel.is_set():
                return
            return self.server.error(
                f"An error occurred during the Packing backup step: {err}!",
                err=err,
            )
        if self._cancel.is_set():
            raise OSError("Backup was Stopped")
        self._paused = False
        try:
            self.status = BACKUP_STATUS_UPLOADING
            self._step_upload()
            self.server.debug("Upload backup step completed!")
        except OSError as err:
            self.status = BACKUP_STATUS_ERROR
            if self._cancel.is_set():
                return
            return self.server.error(
                f"An error occurred during the Uploading backup step: {err}!",
                err=err,
            )
        if self._cancel.is_set():
            raise OSError("Backup was Stopped")

    def _step_hash(self):
        self._execute(["/bin/sha256sum", "--binary", f"{self.path}/data.tar.zx"])
        if self._wait() != 0:
            raise OSError(_output_to_error(self._output, self._proc.returncode))
        hash_file = open(f"{self.path}/data.sum", "w")
        hash_data = self._output.replace(f"*{self.path}/", EMPTY)
        hash_file.write(hash_data)
        hash_file.close()
        del hash_file
        idx = hash_data.find(" ")
        hash_data = hash_data[:idx]
        del idx
        desc_data = self.plan.get("description")
        if not isinstance(desc_data, str) or len(desc_data) == 0:
            desc_data = f'Backup of "{self.plan["path"]}" on {datetime.now().strftime("%A %d, %B %m, %Y %R")}'
        desc_file = open(f"{self.path}/info.txt", "w")
        desc_file.write(
            f'{desc_data}\n\nSOURCE: {self.plan["path"]}\nSHA256: {hash_data}\nSIZE:   '
            f'{_format_size(getsize(f"{self.path}/data.tar.zx"))}\nDATE:   '
            f'{datetime.now().strftime("%b %d %Y %H:%M:%S")}\nTYPE:   {"Incremental" if self.increment else "Full"}\n'
        )
        desc_file.close()
        del desc_file
        del desc_data
        del hash_data
        script_file = open(f"{self.path}/extract.sh", "w")
        script_file.write(BACKUP_RESTORE_SCRIPT)
        script_file.close()
        del script_file

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
                f'Unable to upload backup, the known hosts file "{BACKUP_HOSTS}" is missing! Please use "'
                f'ssh -o UserKnownHostsFile=file user@host" to generate the file and copy it."'
            )
        ssh_opts = f"/bin/ssh -o VisualHostKey=no -o UserKnownHostsFile={BACKUP_HOSTS} -p {self.port}"
        if isinstance(self.acl, str) and len(self.acl) > 0:
            try:
                chmod(self.acl, 0o400, follow_symlinks=True)
            except OSError:
                pass
            ssh_opts += f" -i {self.acl}"
        host = self.host
        if isinstance(self.user, str) and len(self.user) > 0:
            host = f"{self.user}@{host}"
        file = f"{self.dst}/{self._file}.tar"
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
                ssh_opts,
                file,
                f"{host}:",
            ]
        )
        del host
        del ssh_opts
        ret = self._wait()
        size = getsize(file)
        if not self.plan.get("keep", False):
            remove(file)
        del file
        if ret != 0:
            raise OSError(_output_to_error(self._output, self._proc.returncode))
        del ret
        self.server.debug(
            f'Uploaded backup of size {_format_size(size)} to "{self.host}"!'
        )
        del size

    def _step_encrypt(self):
        if not isinstance(self.key, str) or len(self.key) == 0:
            return self.server.warning(
                "Skipping encryption as there is valid public key present!"
            )
        if not exists(self.key):
            return self.server.warning(
                f'Skipping encryption as the supplied public key "{self.key}" does not exist!'
            )
        key = b64encode(urandom(BACKUP_KEY_SIZE)).decode("UTF-8")
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
                    stdin=key,
                )
                != 0
            ):
                raise OSError(_output_to_error(self._output, self._proc.returncode))
        except OSError as err:
            key = None
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
                    stdin=f"{key}\n",
                )
                != 0
            ):
                raise OSError(_output_to_error(self._output, self._proc.returncode))
        except OSError as err:
            raise err
        finally:
            del key
        remove(f"{self.path}/data.tar.zx")

    def _step_compress(self):
        command = [
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
        ]
        command.append(f"--exclude={self.dst}")
        command.append(f"--exclude={self.path}")
        for e in BACKUP_EXCLUDE_PATHS:
            command.append(f"--exclude={e}")
        exclude = self.plan.get("exclude")
        if isinstance(exclude, list) and len(exclude) > 0:
            for e in exclude:
                command.append(f"--exclude={e}")
        del exclude
        db = f"{BACKUP_STATE_DIR}/{self.plan['uuid']}.db"
        if not self.increment and isfile(db):
            remove(db)
        makedirs(BACKUP_STATE_DIR, exist_ok=True)
        chmod(BACKUP_STATE_DIR, 0o750, follow_symlinks=False)
        command.append(f"--listed-incremental={db}")
        del db
        command += ["-f", f"{self.path}/data.tar.zx", self.plan["path"]]
        self._execute(command)
        del command
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
                raise OSError("Failed waiting for process: TimeoutExpired")
            except (SubprocessError, OSError) as err:
                raise OSError(f"Failed waiting for process: {err}")
        if self._cancel.is_set():
            return self._proc.returncode
        try:
            self._output = self._proc.stdout.read()
        except (SubprocessError, OSError) as err:
            raise OSError(f"Failed reading process output: {err}")
        return self._proc.returncode

    def _execute(self, command, stdin=None, timeout=BACKUP_TIMEOUT):
        self._output = None
        inp = DEVNULL
        if stdin is not None:
            inp = PIPE
        try:
            self._proc = Popen(
                command,
                text=True,
                stdin=inp,
                stdout=PIPE,
                stderr=STDOUT,
                encoding="UTF-8",
                universal_newlines=True,
            )
        except (SubprocessError, OSError) as err:
            raise OSError(f'Error starting command "{" ".join(command)}": {err}')
        del inp
        run(
            ["/usr/bin/renice", "-n", "15", "--pid", f"{self._proc.pid}"],
            ignore_errors=True,
        )
        run(
            ["/usr/bin/ionice", "-c", "3", "-p", f"{self._proc.pid}"],
            ignore_errors=True,
        )
        if stdin is None:
            return self._wait(timeout)
        try:
            self._proc.communicate(stdin, timeout=timeout)
        except (SubprocessError, OSError) as err:
            raise OSError(
                f'Error communicating with command "{" ".join(command)}": {err}'
            )
        return self._wait(timeout)
