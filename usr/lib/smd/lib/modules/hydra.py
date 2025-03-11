#!/usr/bin/false
################################
### iDigitalFlame  2016-2025 ###
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
# Copyright (C) 2016 - 2025 iDigitalFlame
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

# Module: System/HydraServer, User/user_alias
#   Provisions and monitors Virtual Machines on the system.

from time import time
from uuid import uuid4
from grp import getgrgid
from shutil import rmtree
from random import randint
from ipaddress import IPv4Network
from collections import namedtuple
from pwd import getpwnam, getpwuid
from signal import SIGCONT, SIGSTOP
from lib.structs.storage import Storage
from lib.structs.message import as_error
from lib.util import nes, num, cancel_nul
from lib.util.exec import stop, nulexec, run
from json import dumps, loads, JSONDecodeError
from socket import socket, AF_UNIX, SOCK_STREAM
from os import chown, mkdir, chmod, remove, stat
from select import epoll, EPOLLERR, EPOLLHUP, EPOLLIN
from lib.shared.hydra import load_vm, get_devices, valid_snap_name
from lib.constants.files import HYDRA_CONFIG_DNS, HYDRA_CONFIG_SMB
from os.path import isdir, isfile, exists, isabs, dirname, splitext
from lib.util.file import read, write, remove_file, expand, info, copy
from lib.constants.config import (
    NAME,
    HYDRA_DIR,
    HYDRA_USER,
    HYDRA_BRIDGE,
    HYDRA_RESERVE,
    HYDRA_VM_ARCH,
    HYDRA_EXEC_VM,
    HYDRA_TPM_SIZE,
    HYDRA_FILE_DNS,
    HYDRA_EXEC_DNS,
    HYDRA_FILE_SMB,
    HYDRA_DIR_DHCP,
    HYDRA_EXEC_SMB,
    HYDRA_WAIT_TIME,
    HYDRA_FILE_UEFI,
    HYDRA_DIR_SNAPS,
    HYDRA_EXEC_SWTPM,
    HYDRA_PATH_MOUNTS,
    HYDRA_DIR_DEVICES,
    HYDRA_BRIDGE_NAME,
    HYDRA_RESERVE_SIZE,
    HYDRA_SOCK_BUF_SIZE,
    HYDRA_BRIDGE_NETWORK,
    HYDRA_FILE_UEFI_VARS,
)
from lib.constants import (
    MSG_PRE,
    NEWLINE,
    HYDRA_TAP,
    HOOK_HYDRA,
    HYDRA_WAKE,
    HYDRA_STOP,
    HYDRA_SLEEP,
    HYDRA_START,
    HOOK_DAEMON,
    HYDRA_GA_IP,
    HYDRA_STATUS,
    HOOK_SUSPEND,
    HYDRA_RESTART,
    HYDRA_GA_PING,
    HYDRA_USB_ADD,
    HOOK_SHUTDOWN,
    HOOK_HIBERNATE,
    HYDRA_KEYS_MAP,
    HYDRA_KEYS_CTRL,
    HYDRA_USB_QUERY,
    HYDRA_USB_CLEAN,
    HYDRA_HIBERNATE,
    HYDRA_SNAP_LIST,
    HYDRA_SNAP_TAKE,
    HYDRA_SEND_INPUT,
    HYDRA_USB_DELETE,
    HYDRA_STATE_DONE,
    HYDRA_STATE_SNAP,
    HYDRA_KEYS_NAMED,
    HYDRA_KEYS_SIMPLE,
    HYDRA_SNAP_DELETE,
    HYDRA_STATE_FAILED,
    HYDRA_SNAP_RESTORE,
    HYDRA_STATE_RUNNING,
    HYDRA_STATE_STOPPED,
    HYDRA_STATE_WAITING,
    HYDRA_KEYS_CTRL_MAP,
    HYDRA_STATE_SNAP_DEL,
    HYDRA_STATE_SLEEPING,
    HYDRA_USER_ADD_ALIAS,
    HYDRA_USER_DIRECTORY,
    HYDRA_STATE_SNAP_LOAD,
    HYDRA_USER_DELETE_ALIAS,
)

HOOKS = {HOOK_HYDRA: "user_alias"}
HOOKS_SERVER = {
    HOOK_HYDRA: "HydraServer.hook",
    HOOK_DAEMON: "HydraServer.thread",
    HOOK_SUSPEND: "HydraServer.hibernate",
    HOOK_SHUTDOWN: "HydraServer.hook",
    HOOK_HIBERNATE: "HydraServer.hibernate",
}

_HYDRA_IPC = b'{"execute": "qmp_capabilities"}\r\n'
_HYDRA_USER = None

Error = OSError
Interface = namedtuple("Interface", ["auto", "bridge", "device"])
Restricted = namedtuple(
    "Restricted",
    [
        "bin",
        "extra",
        "memory",
        "reserve",
        "bios",
        "bios_vars",
        "tpm",
        "kernel",
        "initrd",
        "dtb",
        "user",
        "intel",
    ],
)


def _hydra_user():
    global _HYDRA_USER
    if _HYDRA_USER is None:
        try:
            _HYDRA_USER = getpwnam(HYDRA_USER)
        except OSError:
            raise RuntimeError(f'cannot find the user entry for "{HYDRA_USER}"')
    return _HYDRA_USER


def _parse_mounted():
    e = read(HYDRA_PATH_MOUNTS)
    if not nes(e):
        raise OSError("no mounts found")
    r = list()
    for i in e.split(NEWLINE):
        v = i.split(" ")
        if len(v) == 0 or not nes(v[0]) or "/" not in v[0]:
            continue
        x = v[0].strip()
        if x not in r:
            r.append(x)
        del x, v
    return r


def _command_response(v):
    if not isinstance(v, (bytes, bytearray)) or len(v) == 0:
        return None
    try:
        b = v.decode("UTF-8")
    except UnicodeDecodeError:
        return None
    if len(b) == 0:
        return None
    r = list()
    for e in b.split("\r\n"):
        if len(e) == 0:
            continue
        try:
            d = loads(e)
        except JSONDecodeError as err:
            raise Error(f"invalid JSON response: {err}")
        if not isinstance(d, dict):
            return None
        if "error" in d:
            raise Error(d["error"])
        r.append(d)
        del d
    del b
    if len(r) == 1:
        if isinstance(r[0], dict) and "return" in r[0]:
            return r[0]["return"]
        return r[0]
    return r


def _read_full(sock, size):
    b = bytearray(sock.recv(size))
    sock.setblocking(False)
    try:
        while True:
            v = sock.recv(size)
            if not isinstance(v, (bytes, bytearray)):
                break
            b += v
            if len(v) < size:
                break
    except BlockingIOError:
        pass
    sock.setblocking(True)
    return b


def _is_snapshotable(drive):
    if not isinstance(drive, dict) or len(drive) == 0 or "inserted" not in drive:
        return False
    if (
        "device" not in drive
        or drive["device"].startswith("efi")
        or drive.get("locked", False)
    ):
        return False
    v = drive["inserted"]
    return (
        isinstance(v, dict)
        and len(v) > 0
        and (v.get("drv", "").startswith("qcow") or v.get("drv", "") == "vdmk")
        and "file" in v
        and "node-name" in v
        and not v.get("ro", False)
    )


def user_alias(server, message):
    if message.type == HYDRA_USER_DIRECTORY:
        if nes(message.directory):
            server.debug(
                f'[m/hydra/user]: Updated Hydra user directory to "{message.directory}".'
            )
            server.set("hydra.directory", message.directory)
            server.save()
        return
    if not nes(message.name) or message.vmid is None:
        return
    if message.type != HYDRA_USER_ADD_ALIAS and message.type != HYDRA_USER_DELETE_ALIAS:
        return
    if message.type == HYDRA_USER_ADD_ALIAS and not nes(message.file):
        return
    a, n = server.get("hydra.aliases", dict(), True), message.name.lower()
    if message.type == HYDRA_USER_ADD_ALIAS:
        server.debug(f'[m/hydra/user]: Added user alias "{n}" to VM "{message.vmid}".')
        a[n] = message.file
    else:
        server.debug(f'[m/hydra/user]: Removed user alias "{n}" from VM "{a[n]}".')
        del a[n]
    server.set("hydra.aliases", a)
    server.save()
    del n, a


def _is_snapshot_done(last, jobs):
    if not isinstance(jobs, list) or len(jobs) == 0:
        return (False, None)
    v = None
    for i in jobs:
        if "id" not in i:
            continue
        if i["id"] == last:
            v = i
            break
    if not isinstance(v, dict):
        return (False, None)
    if "status" not in v:
        return (False, None)
    return (v["status"] == "concluded", v.get("error"))


class VM(Storage):
    __slots__ = (
        "_usb",
        "_path",
        "_proc",
        "_wait",
        "_stpm",
        "_name",
        "_state",
        "_event",
        "_agent",
        "_debug",
        "_output",
        "_adapters",
    )

    def __init__(self, path, uid):
        if (
            not nes(path)
            or path.startswith("/etc")
            or path.startswith("/dev")
            or path.startswith("/sys")
            or path.startswith("/proc")
        ):
            raise Error(f'path "{path}" is invalid')
        try:
            i = info(path, sym=False)
        except OSError as err:
            raise Error(f'cannot read "{path}": {err}')
        # NOTE(dij): We don't wrap these as they're the same as an Error
        #            and they already provide context.
        #            Must be owner with exclusive access.
        i.only(file=True).check(0o7177, uid, req=0o600, own_gid=True)
        # NOTE(dij): Verify that the host directory is also owned by the user
        #            and has write permissions.
        info(dirname(path), sym=False).check(0o7027, uid, req=0o700, own_gid=True).only(
            dir=True
        )
        del i
        Storage.__init__(self, path, load=True)
        if not nes(self.get("vm.uuid")):
            self.set("vm.uuid", str(uuid4()))
        if self.vmid is None:
            self.vmid = hash(self.get("vm.uuid")) % 512
        elif not isinstance(self.vmid, int) or self.vmid <= 0:
            raise Error("vmid must be a positive non-zero number")
        self._usb = dict()
        self._path = f"{HYDRA_DIR}/{self.vmid}"
        self._proc = None
        self._wait = 0
        self._stpm = None
        self._name = self.get("vm.name")
        self._state = HYDRA_STATE_STOPPED
        self._event = None
        self._debug = False
        self._agent = False
        self._output = None
        self._adapters = list()

    def _msg(self):
        if self._output is None:
            return ""
        if isinstance(self._output[0], int) and self._output[0] != 0:
            v = f" with a non-zero exit code ({self._output[0]})!"
        else:
            v = "."
        if not nes(self._output[1]):
            return v
        return v + f"\n({self._output[1]})"

    def __stop(self):
        if self._state == HYDRA_STATE_STOPPED:
            return
        if self._state == HYDRA_STATE_WAITING:
            self._state = HYDRA_STATE_FAILED
        else:
            self._state = HYDRA_STATE_DONE

    def _status(self):
        if self._event is not None:
            s = "stopping"
        elif self._state == HYDRA_STATE_DONE:
            s = "stopped"
        elif self._state == HYDRA_STATE_FAILED:
            s = "error"
        elif self._state == HYDRA_STATE_STOPPED:
            s = "stopped"
        elif self._state == HYDRA_STATE_RUNNING:
            s = "running"
        elif self._state == HYDRA_STATE_WAITING:
            s = "waiting"
        elif self._state == HYDRA_STATE_SLEEPING:
            s = "sleeping"
        elif self._state == HYDRA_STATE_SNAP:
            s = "saving"
        elif self._state == HYDRA_STATE_SNAP_DEL:
            s = "updating"
        elif self._state == HYDRA_STATE_SNAP_LOAD:
            s = "reverting"
        else:
            s = "stopped"
        return {
            "pid": self._proc.pid if self._running() else None,
            "usb": self._usb,
            "vmid": self.vmid,
            "file": self.path(),
            "name": self._name,
            "guest": self._agent,
            "status": s,
        }

    def _running(self):
        return self._proc is not None and self._proc.poll() is None

    def _ip(self, server):
        if self._state != HYDRA_STATE_RUNNING:
            raise Error("invalid state to check GA")
        try:
            r, _ = self._cmd(server, "guest-network-get-interfaces", ga=True)
        except Exception as err:
            server.warning(
                f"[m/hydra/VM({self.vmid})]: QEMU-GA get-interfaces failed!", err
            )
            return self._status()
        s = self._status()
        if not isinstance(r, list) or len(r) == 0:
            return s
        x = list()
        for i in r:
            n = i.get("name")
            if not nes(n):
                continue
            a = i.get("ip-addresses")
            if isinstance(a, list) and len(a) > 0:
                for v in a:
                    if not isinstance(v, dict):
                        continue
                    if v.get("ip-address-type") != "ipv4":
                        continue
                    p = v.get("ip-address")
                    if nes(p) and not v["ip-address"].startswith("127."):
                        x.append({"name": n, "ip": p})
                    del p
            del a, n
        del r
        s["ips"] = x
        del x
        return s

    def _ping(self, server):
        if self._state != HYDRA_STATE_RUNNING:
            raise Error("invalid state to check GA")
        s = self._status()
        try:
            self._cmd(server, "guest-ping", ga=True)
        except Exception as err:
            server.warning(f"[m/hydra/VM({self.vmid})]: QEMU-GA ping failed!", err)
            s["ping"] = False
        else:
            s["ping"] = True
        return s

    def _socket_perms_set(self):
        try:
            chmod(f"{self._path}.vnc", 0o0762, follow_symlinks=False)
            chmod(f"{self._path}.spice", 0o0762, follow_symlinks=False)
        except OSError:
            return False
        try:
            a, b = stat(f"{self._path}.vnc"), stat(f"{self._path}.spice")
            if a.st_mode & 0o0762 == 0o0762 and b.st_mode & 0o0762 == 0o0762:
                return True
        except OSError:
            return False
        finally:
            del a, b
        return False

    def _hibernate(self, server):
        if self._state == HYDRA_STATE_STOPPED:
            return
        if self._state == HYDRA_STATE_WAITING:
            raise Error("cannot hibernate while waiting")
        if self._state != HYDRA_STATE_RUNNING:
            raise Error("invalid state to hibernate")
        if not self._agent:
            server.debug(
                f"[m/hydra/VM({self.vmid})]: QEMU Guest Agent was not detected, trying anyway.."
            )
        server.debug(f"[m/hydra/VM({self.vmid})]: Sending Hibernate request to VM..")
        try:
            self._cmd(server, "guest-suspend-disk", ga=True, timeout=2)
        except TimeoutError:
            server.warning(
                f"[m/hydra/VM({self.vmid})]: Hibernate request timed-out but may have still worked.."
            )

    def _snap_last(self, server):
        if not isfile(f"{HYDRA_DIR_SNAPS}/{self.vmid}"):
            return None
        try:
            with open(f"{HYDRA_DIR_SNAPS}/{self.vmid}") as f:
                return f.read().strip()
        except Error as err:
            return server.error(
                f'[m/hydra/VM({self.vmid})]: Cannot load Snapshot state file "{HYDRA_DIR_SNAPS}/{self.vmid}": {err}!',
                err,
            )

    def _snap_list(self, server):
        if self._state != HYDRA_STATE_RUNNING:
            raise Error("invalid state to query Snapshots")
        r, _ = self._cmd(server, "query-block")
        d = dict()
        if not isinstance(r, list) or len(r) == 0:
            return d
        for i in r:
            if not _is_snapshotable(i):
                continue
            v = i["inserted"]
            s = v.get("image", dict()).get("snapshots")
            if not isinstance(s, list) or len(s) == 0:
                d[i["device"]] = {
                    "file": v["file"],
                    "name": v["node-name"],
                    "snaps": list(),
                }
                continue
            e = list()
            for x in s:
                if not isinstance(x, dict) or len(x) == 0 or "date-sec" not in x:
                    continue
                if "id" not in x or "name" not in x or "vm-clock-sec" not in x:
                    continue
                e.append(
                    {
                        "id": x["id"],
                        "name": x["name"],
                        "date": x["date-sec"],
                        "order": x["vm-clock-sec"],
                    }
                )
            e.sort(key=lambda y: (y["id"], y["order"]))
            d[i["device"]] = {
                "file": v["file"],
                "name": v["node-name"],
                "snaps": e,
            }
            del e, v, s
        del r
        return d

    def _sleep(self, server, sleep):
        if sleep and self._state == HYDRA_STATE_SLEEPING:
            raise Error("already sleeping")
        if not sleep and self._state != HYDRA_STATE_SLEEPING:
            raise Error("not currently sleeping")
        if self._state != HYDRA_STATE_RUNNING and self._state != HYDRA_STATE_SLEEPING:
            raise Error("invalid state to sleep")
        if sleep:
            server.debug(f"[m/hydra/VM({self.vmid})]: Entering sleep")
            self._cmd(server, "stop")
            self._proc.send_signal(SIGSTOP)
            # NOTE(dij): Sleep the STPM process also.
            if self._stpm is not None:
                self._stpm.send_signal(SIGSTOP)
            self._state = HYDRA_STATE_SLEEPING
            return
        server.debug(f"[m/hydra/VM({self.vmid})]: Resuming from sleep")
        # NOTE(dij): Wake the STPM process also.
        if self._stpm is not None:
            self._stpm.send_signal(SIGCONT)
        self._proc.send_signal(SIGCONT)
        self._cmd(server, "cont")
        self._state = HYDRA_STATE_RUNNING

    def _init_adapters(self, server):
        if not isinstance(self._adapters, list) or len(self._adapters) == 0:
            return
        server.debug(f"[m/hydra/VM({self.vmid})]: Creating network interfaces..")
        try:
            for i in self._adapters:
                if i.auto:
                    nulexec(
                        [
                            "/usr/bin/ip",
                            "tuntap",
                            "add",
                            "dev",
                            i.device,
                            "mode",
                            "tap",
                            "user",
                            HYDRA_USER,
                        ],
                        wait=True,
                    )
                nulexec(
                    ["/usr/bin/ip", "link", "set", i.device, "master", i.bridge],
                    wait=True,
                )
                nulexec(
                    [
                        "/usr/bin/ip",
                        "link",
                        "set",
                        "dev",
                        i.device,
                        "up",
                        "promisc",
                        "on",
                    ],
                    wait=True,
                )
                server.debug(
                    f'[m/hydra/VM({self.vmid})]: Created interface "{i.device}".'
                )
        except OSError as err:
            # NOTE(dij): Cleanup on failure.
            self._close_adapters(server)
            raise err
        server.debug(
            f"[m/hydra/VM({self.vmid})]: Created {len(self._adapters)} network interfaces."
        )

    def _close_adapters(self, server):
        if not isinstance(self._adapters, list) or len(self._adapters) == 0:
            return
        server.debug(f"[m/hydra/VM({self.vmid})]: Cleaning up network interfaces..")
        for i in self._adapters:
            try:
                nulexec(["/usr/bin/ip", "link", "set", i.device, "nomaster"], wait=True)
                nulexec(
                    ["/usr/bin/ip", "link", "set", "dev", i.device, "down"], wait=True
                )
                if not i.auto:
                    continue
                nulexec(
                    [
                        "/usr/bin/ip",
                        "tuntap",
                        "delete",
                        "dev",
                        i.device,
                        "mode",
                        "tap",
                    ],
                    wait=True,
                )
            except OSError as err:
                server.error(
                    f'[m/hydra/VM({self.vmid})]: Could not remove interface "{i.device}".',
                    err,
                )
                continue
            server.debug(f'[m/hydra/VM({self.vmid})]: Removed interface "{i.device}".')
        server.debug(
            f"[m/hydra/VM({self.vmid})]: Removed {len(self._adapters)} network interfaces."
        )
        self._adapters.clear()

    def _thread(self, server, manager):
        if self._state == HYDRA_STATE_STOPPED:
            return
        if self._state == HYDRA_STATE_DONE:
            server.debug(f"[m/hydra/VM({self.vmid})]: Natural shutdown, stopping VM!")
            self._stop(server, manager, True)
            self._state = HYDRA_STATE_STOPPED
        elif self._state == HYDRA_STATE_FAILED:
            server.error(f"[m/hydra/VM({self.vmid})]: Process failed, stopping VM!")
            self._stop(server, manager, True)
            self._state == HYDRA_STATE_STOPPED
            server.notify(
                "Hydra VM Status", f"VM({self.vmid}) failed to start!", "virt-viewer"
            )
        if self._state != HYDRA_STATE_WAITING:
            return
        if not self._running():
            self._wait += 1
            if self._wait < HYDRA_WAIT_TIME:
                return
            server.error(f"[m/hydra/VM({self.vmid})]: Wait time reached, stopping VM!")
            self._stop(server, manager, True)
            self._state = HYDRA_STATE_STOPPED
            return server.notify(
                "Hydra VM Status",
                f"VM({self.vmid}) failed to start!",
                "virt-viewer",
            )
        if not self._socket_perms_set():
            return
        self._state = HYDRA_STATE_RUNNING
        server.debug(
            f"[m/hydra/VM({self.vmid})]: Socket became active, bootstrap complete!"
        )
        server.notify("Hydra VM Status", f"VM({self.vmid}) started!", "virt-viewer")

    def _input(self, server, data, caps):
        if self._state != HYDRA_STATE_RUNNING:
            raise Error("invalid state to add USB devices")
        if not nes(data):
            return
        x, b = 0, data.encode("UTF-8")
        _, s = self._cmd(server, "input-send-event", {"events": []}, close=False)
        try:
            while x < len(b):
                (z, i, c, k) = _key_next(b, x, len(b))
                if z:
                    _key_send(s, {"type": "qcode", "data": c.lower()}, False, caps)
                else:
                    _key_send(s, c, k, caps)
                x = i
                del z, i, c, k
            del b, x
        except (OSError, UnicodeError) as err:
            raise Error(err)
        finally:
            s.close()
            del s

    def _usb_clean(self, server, manager):
        if self._running:
            for k, v in list(self._usb.items()):
                try:
                    self._cmd(server, "device_del", {"id": f"usb-dev-{v}"})
                except OSError as err:
                    raise Error(f'cannot remove device "{v}": {err}')
                # NOTE(dij): We remove from the "self._usb" dict here just in case
                #            line above fails and we don't leave it in a quasi-weird
                #            half state of USB devices already removed.
                del self._usb[k], manager._usb[k]
                server.debug(
                    f'[m/hydra/VM({self.vmid})]: Removed USB device "{k}" with ID {v}.'
                )
        self._usb.clear()
        server.debug(f"[m/hydra/VM({self.vmid})]: Removed All USB devices.")

    def _build_adapters(self, server, bus):
        if not isinstance(self.network, dict):
            self.network = dict()
            return server.debug(
                f"[m/hydra/VM({self.vmid})]: Network value was not found, skipping interface setup."
            )
        if len(self.network) == 0:
            return server.debug(
                f"[m/hydra/VM({self.vmid})]: Network value was empty, skipping interface setup."
            )
        r = list()
        self._adapters.clear()
        for n, a in self.network.items():
            if not isinstance(a, dict) or len(a) == 0:
                server.warning(
                    f'[m/hydra/VM({self.vmid})]: Skipping invalid network interface "{n}"!'
                )
                continue
            if "type" not in a:
                a["type"] = "intel"
            if "bridge" in a:
                b = a["bridge"]
            else:
                b = HYDRA_BRIDGE
            if "device" in a:
                d, k = a["device"], False
            else:
                d, k = f"{HYDRA_BRIDGE}s{self.vmid}n{len(self._adapters)}", True
            self._adapters.append(Interface(k, b, d))
            del b, k
            if "mac" not in a:
                a["mac"] = (
                    "2c:af:01:"
                    + f"{randint(0, 255):02x}:{randint(0, 255):02x}:{randint(0, 255):02x}"
                )
            if a["type"] == "intel":
                x = "e1000"
            elif a["type"] == "virtio":
                x = "virtio-net-pci"
            elif a["type"] == "vmware":
                x = "vmxnet3"
            else:
                x = a["type"]
            r += [
                "-netdev",
                f"type=tap,id={n},ifname={d},script=no,downscript=no,vhost=on",
                "-device",
                f'{x},mac={a["mac"]},netdev={n},bus={bus}.0,addr={hex(0x14 + len(self._adapters))},id={n}-dev',
            ]
            del d, x
            self.network[n] = a
        return r

    def _restart(self, server, reset=False):
        if self._state == HYDRA_STATE_STOPPED:
            return
        if self._state == HYDRA_STATE_WAITING:
            raise Error("cannot restart/reset while waiting")
        if self._state != HYDRA_STATE_RUNNING:
            raise Error("not able to restart/reset")
        if reset:
            server.debug(f"[m/hydra/VM({self.vmid})]: Forcefully resetting VM!")
            try:
                self._cmd(server, "system_reset", timeout=2)
            except TimeoutError:
                server.warning(
                    f"[m/hydra/VM({self.vmid})]: Reset request timed-out but may have still worked.."
                )
            return
        if not self._agent:
            server.debug(
                f"[m/hydra/VM({self.vmid})]: QEMU Guest Agent was not detected, trying anyway.."
            )
        server.debug(f"[m/hydra/VM({self.vmid})]: Sending restart request to VM..")
        try:
            self._cmd(server, "guest-shutdown", {"mode": "reboot"}, True, timeout=2)
        except TimeoutError:
            server.warning(
                f"[m/hydra/VM({self.vmid})]: Restart timed-out but may have still worked.."
            )

    def _build_bios(self, server, info, uid):
        t = self.get("bios.type", 1)
        if not isinstance(t, int):
            t = 1
        elif t > 0x29 or t < 0:
            t = 1
        if not self.get("bios.uefi"):
            return [f"type={t}"]
        if nes(info.bios):
            f = info.bios
        else:
            c = int(info.intel)
            if self.get("bios.secure_boot"):
                c += 2
            f = HYDRA_FILE_UEFI[c]
            del c
        if nes(info.bios_vars):
            v = info.bios_vars
        else:
            v = f"{dirname(self.path())}/uefi_vars.fd"
            server.debug(
                f'[m/hydra/VM({self.vmid})]: Copying the default UEFI variables to "{v}".'
            )
            try:
                u = getpwuid(uid)
                copy(
                    HYDRA_FILE_UEFI_VARS[int(self.get("bios.secure_boot", False))],
                    v,
                    uid,
                    u.pw_gid,
                    0o0600,
                )
                del u
            except OSError as err:
                raise Error(f'Cannot create VM specific UEFI vars file "{v}": {err}')
            else:
                self.bios["vars"] = v
        return [
            f'type={t},uuid={self.get("vm.uuid")}',
            "-drive",
            f"if=pflash,id=efi0-bios,bus=0,format=raw,unit=0,readonly=on,file={f}",
            "-drive",
            f"if=pflash,id=efi0-user,bus=0,format=raw,unit=1,file={v}",
        ]

    def _snap_drives(self, server, snaps=False):
        r, _ = self._cmd(server, "query-block")
        d = dict()
        if not isinstance(r, list) or len(r) == 0:
            return d
        for i in r:
            if not _is_snapshotable(i):
                continue
            if snaps:
                s = i["inserted"].get("image", dict()).get("snapshots")
                if not isinstance(s, list) or len(s) == 0:
                    continue
                del s
            d[i["device"]] = i["inserted"]["node-name"]
        del r
        return dict(sorted(d.items()))

    def _snap_done(self, server, job, name, err):
        if self._state == HYDRA_STATE_SNAP:
            s = "Snapshot"
        elif self._state == HYDRA_STATE_SNAP_LOAD:
            s = "Revert"
        else:
            s = "Snapshot Delete"
        p = self._state != HYDRA_STATE_SNAP_DEL
        self._state = HYDRA_STATE_RUNNING
        if err is None:
            if p:
                try:
                    with open(f"{HYDRA_DIR_SNAPS}/{self.vmid}", "w") as f:
                        f.write(name)
                except Error as err:
                    server.error(
                        f"[m/hydra/VM({self.vmid})]: Cannot save Snapshot state "
                        f'file "{HYDRA_DIR_SNAPS}/{self.vmid}": {err}!',
                        err,
                    )
            server.info(f'[m/hydra/VM({self.vmid})]: Snapper Job "{job}" completed!')
            return server.notify(
                "Hydra VM Snapshot",
                f"VM({self.vmid}) {s} complete!",
                "virt-viewer",
            )
        del p
        server.error(
            f'[m/hydra/VM({self.vmid})]: Snapper Job "{job}" failed with error: {err}!'
        )
        server.notify(
            "Hydra VM Snapshot",
            f"VM({self.vmid}) {s} failed!\n{err}",
            "virt-viewer",
        )
        del s

    def _build(self, server, manager, uid, opts):
        # NOTE(dij): Do stuff that requires a bunch of checking first.
        x = self._build_restriced(server, manager, uid)
        # NOTE(dij): If the above passes, we should be good!
        b, t = self.get("dev.bus"), self.get("dev.type", "q35")
        if not nes(b):
            if nes(t) and "q35" in t:
                b = self.set("dev.bus", "pcie")
            else:
                b = self.set("dev.bus", "pci")
        o, c = self.get("cpu.options", list()), self.get("cpu.type", "host")
        i, m = c == "host", self.get("cpu.saveable", False)
        h = self.get("cpu.hide_vm", False)
        if x.intel and self.get("cpu.auto_options", True):
            c = (
                f"{c},kvm={'off' if h else 'on'},+kvm_pv_unhalt,+kvm_pv_eoi,+hv-evmcs,+hv-tlbflush,+kvmclock,+aes,"
                "+pdpe1gb,hv_ipi,hv_relaxed,hv_frequencies,hv_synic,hv_reenlightenment,hv_vpindex,hv_spinlocks=0x1FFF,"
                "hv_vapic,hv_time,hv_stimer,hv_reset,hv_runtime"
            )
            if m:
                c += ",migratable=yes,-invtsc"
            elif i or c == "max" or c.startswith("kvm") or c.startswith("qemu"):
                # TODO(dij): Should we expand this list? ^
                #            There might be more CPUs that can support this value, but
                #            we'd need a test criteria.
                c += ",migratable=no,hv_passthrough"
            else:
                c += ",hv_passthrough"
        if h:
            c = f"{c},-hypervisor"
        if i:
            c = f"{c},l3-cache=on"
        del h, i
        try:
            if isinstance(o, list) and len(o) > 0:
                c = f'{c},{",".join(o)}'
        except TypeError:
            raise Error('"cpu.options" list can only contain string values')
        # NOTE(dij): These two lines /could/ fail just in case, luckily we haven't
        #            done /much/ yet.
        try:
            d = self._build_drives(
                server,
                uid,
                x.user,
                b,
                t,
                opts,
            )
            a = self._build_adapters(server, b)
        except KeyError as err:
            raise Error(f'building requires the missing value "{err}"')
        n = self.get("cpu.sockets", 1)
        r = [
            x.bin,
            "-run-with",
            f"user={HYDRA_USER}",
            "-smbios",
        ] + self._build_bios(server, x, uid)
        w = self._name if nes(self._name) else f"hydra-vm-{self.vmid}"
        r += [
            "-enable-kvm",
            "-nographic",
            "-no-user-config",
            "-nodefaults",
            "-boot",
            "order=cdn,menu=on,splash-time=0,reboot-timeout=1000,strict=on",
            "-rtc",
            "base=localtime,clock=host",
            "-machine",
            f'type={t},mem-merge=on,dump-guest-core=off,nvdimm=off,{"hpet=off,vmport=on," if x.intel else ""}'
            f'hmat=off,suppress-vmdesc=on,accel={self.get("dev.accel", "kvm")}',
            "-m",
            f"size={x.memory}",
            "-cpu",
            c,
            "-smp",
            f'{n},sockets={n},cores={self.get("cpu.cores", 1)},maxcpus={n}',
            "-uuid",
            self.get("vm.uuid"),
            "-name",
            f'"{w}",debug-threads=off',
            "-pidfile",
            f"{self._path}.pid",
            "-display",
            f"vnc=unix:{self._path}.vnc,connections=512,lock-key-sync=on,"
            "password=off,power-control=on,share=ignore",
            "-qmp",
            f"unix:{self._path}.sock,server=on,wait=off,mux=on",
            "-chardev",
            f"socket,id=qga0,path={self._path}.qga,server=on,wait=off",
            "-device",
            f"virtio-serial-pci,id=qga0,bus={b}.0,addr=0x9",
            "-device",
            "virtserialport,chardev=qga0,name=org.qemu.guest_agent.0",
            "-object",
            "iothread,id=iothread0",
            "-device",
            f"virtio-balloon-pci,id=ballon0,bus={b}.0,addr=0x0c",
            "-device",
            f"virtio-keyboard-pci,id=keyboard0,bus={b}.0,addr=0x11",
            "-device",
            f"qemu-xhci,multifunction=on,streams=on,id=usb-bus3,bus={b}.0,addr=0x12",
            "-device",
            f"usb-ehci,multifunction=on,id=usb-bus2,bus={b}.0,addr=0x0d",
            "-device",
            f"piix3-usb-uhci,multifunction=on,id=usb-bus1,bus={b}.0,addr=0x0e",
            "-device",
            f"pci-bridge,id=pci-bridge1,chassis_nr=1,bus={b}.0,addr=0x0f",
            "-device",
            f"pci-bridge,id=pci-bridge2,chassis_nr=2,bus={b}.0,addr=0x10",
            "-object",
            "rng-random,filename=/dev/urandom,id=rng0",
            "-device",
            f"virtio-rng-pci,rng=rng0,bus={b}.0,addr=0x08",
            "-sandbox",
            "on,obsolete=deny,spawn=deny",
        ]
        del w
        if x.reserve is not None:
            r += ["-mem-path", x.reserve, "-mem-prealloc"]
        if x.bios is not None:
            r += ["-bios", x.bios]
        if x.tpm is not None:
            if not self.get("dev.tpm.software"):
                r += [
                    "-tpmdev",
                    f"passthrough,id=tpm0,path={x.tpm},version=v2.0",
                    "-device",
                    "tpm-tis,tpmdev=tpm0",
                ]
            elif isfile(HYDRA_EXEC_SWTPM):
                self._stpm = nulexec(
                    [
                        HYDRA_EXEC_SWTPM,
                        "socket",
                        "--tpm2",
                        "--terminate",
                        "--tpmstate",
                        f"backend-uri=file://{x.tpm},mode=0600,lock",
                        "--ctrl",
                        f"type=unixio,path={self._path}.swtpm,mode=0600,uid=0,gid=0,terminate",
                        "--pid",
                        f"file={self._path}.swtpm.pid",
                    ],
                )
                server.debug(
                    f"[m/hydra/VM({self.vmid})]: Starting software TPM process, PID({self._stpm.pid})."
                )
                r += [
                    "-chardev",
                    f"socket,id=tpm0c,path={self._path}.swtpm",
                    "-tpmdev",
                    "emulator,id=tpm0,chardev=tpm0c",
                    "-device",
                    "tpm-tis,tpmdev=tpm0",
                ]
            else:
                server.warning(
                    f'[m/hydra/VM({self.vmid})]: Cannot start TPM process as "swtpm" is not installed, '
                    "not adding TPM!"
                )
        if x.extra is not None:
            r += x.extra
        if "q35" in t and self.get("dev.iommu", True):
            r += ["-device", "intel-iommu"]
        if x.kernel is not None:
            r += ["-kernel", x.kernel]
        if x.initrd is not None:
            r += ["-initrd", x.initrd]
        v = self.get("dev.cmdline")
        if nes(v):
            r += ["-append", v]
        if x.dtb is not None:
            r += ["-dtb", x.dtb]
        del x, t, o, c, n, v
        s = self.get("dev.osk")
        if nes(s):
            # NOTE(dij): Support MacOS with an OSK. This allows MacOS to not need
            #            to use the "extra" tag.
            r += ["-device", f"isa-applesmc,osk={s}"]
        del s
        g = self.get("dev.display", "virtio")
        if nes(g):
            if g == "virtio":
                # NOTE(dij): VirtIO VGA drivers are REALLY buggy on Windows. They cause
                #            BSODs randomally. It's driver related as if the driver isn't
                #            installed, the BSODs stop. However, this limits your maximum
                #            screen resolution to 1200x1080.
                server.warning(
                    f"[m/hydra/VM({self.vmid})]: The drivers for the VirtIO VGA device have compatibility issues with"
                    " Windows, your VM may BSOD."
                )
                s, v = (
                    "virtio-vga,disable-modern=false,disable-legacy=auto,iommu_platform=true,hostmem=32M",
                    True,
                )
            elif g == "qxl":
                s, v = "qxl-vga,vram_size_mb=32,ram_size_mb=32", True
            else:
                v, s = False, g
        else:
            v, s = False, "std"
        n = self.set("dev.display_count", 1)
        if not isinstance(n, int) or n <= 0 or n > 4:
            self.set("dev.display_count", 1)
            n = 1
        for _ in range(0, n):
            if v:
                r += ["-device", f"{s},bus={b}.0"]
            else:
                r += ["-vga", s]
        del g, s, v
        s = self.get("dev.sound", True)
        # "dev.sound" = false will disable this.
        # When it's true, we use the default sound device.
        if s is not None and s and s != "none":
            r += [
                "-audiodev",
                f"driver=pa,id=audio0,server=/var/run/user/{uid}/pulse/native",
            ]
            if s == "virtio":
                r += [
                    "-device",
                    f"virtio-sound-pci,audiodev=audio0,id=sound1,bus={b}.0,addr=0x0b",
                ]
            elif s == "intel":
                r += [
                    "-device",
                    f"intel-hda,id=sound1,bus={b}.0,addr=0x0b",
                    "-device",
                    "hda-output,audiodev=audio0,mixer=true",
                ]
            elif s == "intel-duplex" or isinstance(s, bool) and m:
                r += [
                    "-device",
                    f"intel-hda,id=sound1,bus={b}.0,addr=0x0b",
                    "-device",
                    "hda-duplex,audiodev=audio0,mixer=true",
                ]
            else:
                r += [
                    "-device",
                    "usb-audio,id=sound1,audiodev=audio0,bus=usb-bus3.0,port=1",
                ]
        del m
        i = self.get("dev.input", "virtio")
        if i == "tablet":
            r += ["-device", "usb-tablet,id=input0,bus=usb-bus2.0,port=1"]
        elif i == "mouse":
            r += [
                "-device",
                f"virtio-mouse-pci,id=input0,bus={b}.0,addr=0x0a",
            ]
        elif i == "usb":
            r += [
                "-device",
                "usb-mouse,id=input0,bus=usb-bus2.0,port=1",
                "-device",
                "usb-kbd,id=input1,bus=usb-bus2.0,port=2",
            ]
        else:
            if i != "virtio":
                self.set("dev.input", "virtio")
            r += [
                "-device",
                f"virtio-tablet-pci,id=input0,bus={b}.0,addr=0x0a",
            ]
        del i
        if self.get("vm.spice", True):
            # NOTE(dij): We're adding the lines to add USB redirect support
            #            via SPICE, but Hydra won't know about the added devices
            #            it shouldn't be an issue, but documenting it incase
            #            it does.
            r += [
                "-spice",
                f"unix=on,addr={self._path}.spice,disable-ticketing=on,playback-compression=off,"
                "image-compression=off,gl=on,agent-mouse=on,disable-copy-paste=off,seamless-migration=on,"
                "disable-agent-file-xfer=off",
                "-chardev",
                "spicevmc,id=spice0,name=vdagent",
                "-device",
                "virtserialport,chardev=spice0,name=com.redhat.spice.0",
                "-device",
                "nec-usb-xhci,id=spice-usb-bus,addr=0x13",
                "-chardev",
                "spicevmc,name=usbredir,id=spice-usb1-c",
                "-device",
                "usb-redir,chardev=spice-usb1-c,id=spice-usb1",
                "-chardev",
                "spicevmc,name=usbredir,id=spice-usb2-c",
                "-device",
                "usb-redir,chardev=spice-usb2-c,id=spice-usb2",
                "-chardev",
                "spicevmc,name=usbredir,id=spice-usb3-c",
                "-device",
                "usb-redir,chardev=spice-usb3-c,id=spice-usb3",
            ]
        r += a + d
        del a, d, b
        self._debug = self.get("vm.debug", False) or opts.debug
        if self._debug:
            server.dump(f'[m/hydra/VM({self.vmid})]: Runtime command: [{" ".join(r)}]')
        return r

    def _start(self, server, manager, uid, opts):
        if self._running():
            if self._state == HYDRA_STATE_SLEEPING:
                server.debug(
                    f"[m/hydra/VM({self.vmid})]: Waking suspended VM due to start command."
                )
                return self._sleep(server, False)
            return self._process.pid
        if self._state != HYDRA_STATE_STOPPED:
            server.warning(
                f'[m/hydra/VM({self.vmid})]: "_start" called on invalid state 0x{self._state:X}!'
            )
        self._state, self._proc = HYDRA_STATE_STOPPED, None
        x = self._build(server, manager, uid, opts)
        if nes(self.path()):
            self.save(perms=0o600)
            server.debug(f'[m/hydra/VM({self.vmid})]: Saved config to "{self.path()}".')
        try:
            self._init_adapters(server)
        except OSError:
            # NOTE(dij): Remove any stale interfaces and try one more time
            #            :fingers-crossed:
            #
            #            NEW: _init_adapters now removes interfaces itself
            #                 if it fails during runtime, but still throws the
            #                 OSError.
            self._init_adapters(server)
        self._wait = 0
        try:
            self._proc = run(x, out=self._debug)
        except OSError as err:
            server.notify(
                "Hydra VM Status", f"VM({self.vmid}) failed to start!", "virt-viewer"
            )
            self._state = HYDRA_STATE_STOPPED
            self._stop(manager, server, True)
            raise err
        server.watch(self._proc, self.__stop)
        if not self._running():
            self._state = HYDRA_STATE_WAITING
            server.debug(f"[m/hydra/VM({self.vmid})]: Waiting for process.")
            return 0
        if self._socket_perms_set():
            self._state = HYDRA_STATE_RUNNING
            server.info(
                f"[m/hydra/VM({self.vmid})]: Started VM with PID {self._proc.pid}!"
            )
            server.notify("Hydra VM Status", f"VM({self.vmid}) started!", "virt-viewer")
        else:
            self._state = HYDRA_STATE_WAITING
            server.info(
                f"[m/hydra/VM({self.vmid})]: Started VM with PID {self._proc.pid}, but waiting for sockets!"
            )
        # NOTE(dij): Last chance effort, as some get caught in this quasi-state.
        self._socket_perms_set()
        return self._proc.pid

    def _snap_delete(self, server, manager, name):
        if self._state != HYDRA_STATE_RUNNING:
            raise Error("invalid state to delete a Snapshot")
        d = self._snap_drives(server, True)
        if len(d) == 0:
            raise Error("no disks avaliable with Snapshots")
        v = list(d.values())
        a = {
            "tag": name,
            "job-id": f"snap-job-{self.vmid}-{int(time()):X}",
            "devices": v,
        }
        _, s = self._cmd(server, "snapshot-delete", a, timeout=5, close=False)
        manager._register_snap(server, self, a["job-id"], s, name)
        self._state = HYDRA_STATE_SNAP_DEL
        del a, s, v

    def _snap_restore(self, server, manager, name):
        if self._state != HYDRA_STATE_RUNNING:
            raise Error("invalid state to revert to a Snapshot")
        d = self._snap_drives(server, True)
        if len(d) == 0:
            raise Error("no disks avaliable to restore")
        v = list(d.values())
        a = {
            "tag": name,
            "job-id": f"snap-job-{self.vmid}-{int(time()):X}",
            "devices": v,
            "vmstate": v[0],
        }
        _, s = self._cmd(server, "snapshot-load", a, timeout=5, close=False)
        manager._register_snap(server, self, a["job-id"], s, name)
        self._state = HYDRA_STATE_SNAP_LOAD
        del a, s, v

    def _snap_capture(self, server, manager, name):
        if self._state != HYDRA_STATE_RUNNING:
            raise Error("invalid state to Snapshot")
        d = self._snap_drives(server)
        if len(d) == 0:
            raise Error("no disks avaliable to Snapshot")
        v = list(d.values())
        a = {
            "tag": name,
            "job-id": f"snap-job-{self.vmid}-{int(time()):X}",
            "devices": v,
            "vmstate": v[0],
        }
        _, s = self._cmd(server, "snapshot-save", a, timeout=5, close=False)
        manager._register_snap(server, self, a["job-id"], s, name)
        self._state = HYDRA_STATE_SNAP
        del a, s, v

    def _build_restriced(self, server, manager, uid):
        try:
            u = getpwuid(uid)
        except KeyError:
            # NOTE(dij): This shouldn't really fail but *shrug* if it does, it
            #            means something is horribly wrong or we're getting bs'd.
            raise Error(f'cannot find user for "{uid}"')
        # NOTE(dij): We don't expand any vars in the "vm.binary" option as it
        #            must be a full path.
        x, v = self.get("vm.binary"), server.get("hydra.unsafe.enabled", False, True)
        if nes(x):
            if not v:
                raise Error(
                    'cannot use "vm.binary" when "hydra.unsafe.enabled" is false or unset'
                )
            if not isabs(x):
                raise Error('"vm.binary" must be an absolute path')
            a = server.get("hydra.unsafe.allowed_binaries", list(), True)
            if not isinstance(a, list) or x not in a:
                raise Error(f'binary "{x}" is not in "hydra.unsafe.allowed_binaries"')
            del a
        else:
            k = self.get("vm.arch")
            if nes(k):
                x = HYDRA_VM_ARCH.get(k.lower(), HYDRA_EXEC_VM)
            else:
                x = HYDRA_EXEC_VM
        e = self.get("vm.extra")
        if isinstance(e, list) and len(e) > 0:
            if not v:
                raise Error(
                    'cannot use "vm.extra" when "hydra.unsafe.enabled" is false or unset'
                )
            if not server.get("hydra.unsafe.extra", False, True):
                raise Error(
                    'cannot use "vm.extra" when "hydra.unsafe.extra" is false or unset'
                )
            server.info(
                f'[m/hydra/VM({self.vmid})]: Adding additional arguments via "vm.extra" = [{" ".join(e)}]!'
            )
        else:
            # NOTE(dij): Set to None to remove anything else.
            e = None
        del v
        # NOTE(dij): Security Check
        #            Can only be a root owned/group file that has 0o0755 permissions.
        info(x, False, hide=True).only(file=True, hide=True).check(
            0o7022, 0, 0, req=0o0755, hide=True
        )
        f = expand(self.get("bios.file"))
        if nes(f):
            # NOTE(dij): Security Check
            #            Can only be a file owned by the calling user that has 0o0400
            #            permissions.
            info(f, False, hide=True).check_if_owner(
                0o7177, uid=uid, req=0o0400, hide=True
            ).check_if_not_owner(uid, 0o7133, req=0o0644, hide=True).only(file=True)
        else:
            # NOTE(dij): Set to None to remove anything else.
            f = None
        q = expand(self.get("bios.vars"))
        if nes(q):
            # NOTE(dij): Security Check
            #            Can only be a file owned by the calling user that has 0o0600
            #            permissions.
            info(q, False, hide=True).check(
                0o7137, uid, hide=True, req=0o600, own_gid=True
            ).only(file=True)
        else:
            # NOTE(dij): Set to None to remove anything else.
            q = None
        t, c = self.get("dev.tpm.path"), self.get("dev.tpm.software")
        if nes(t) and not isabs(t):
            t = f"{dirname(self.path())}/{t}"
        if c and not nes(t):
            t = self.set("dev.tpm.path", f"{dirname(self.path())}/tpm.raw")
        if nes(t):
            if c and not exists(t):
                # NOTE(dij): Security Check
                #            Virtual TPM file. Don't need to check here as we check
                #            on creation of the VM object anyway.
                server.debug(
                    f'[m/hydra/VM({self.vmid})]: Creating no-existant software TPM file "{t}".'
                )
                with open(t, "wb") as v:
                    v.seek(HYDRA_TPM_SIZE - 1)
                    v.write(b"\0")
                chmod(t, 0o0600, follow_symlinks=False)
                chown(t, uid, u.pw_gid, follow_symlinks=False)
            i = info(t, False, hide=True)
            if i.isfile:
                if not c:
                    raise Error(
                        f'tmp device "{t}" is a file but "dev.tpm.software" is not set as "true"'
                    )
                # NOTE(dij): Security Check
                #            Virtual TPM file. Can only be a file owned by the
                #            calling user that has 0o0600 permissions.
                i.check(0o7177, uid, hide=True, req=0o0600, own_gid=True).only(
                    file=True
                )
            else:
                # NOTE(dij): Security Check
                #            Can only be a TPM chardev device that is not owned by
                #            root. The calling user must by in the group owned by the
                #            owner (usually "tss"). The device must have 0o0660 permissions.
                i.check(0o7117, req=0o0660, hide=True).only(char=True)
                if i.uid != uid:
                    raise Error(
                        f'character device "{f}" cannot have a non-system owner'
                    )
                if i.uid == 0:
                    raise Error(f'character device "{t}" cannot be owned by root')
                try:
                    v = getpwuid(i.uid)
                except KeyError:
                    raise Error(f'cannot find user "{i.uid}" for "{t}"')
                try:
                    g = getgrgid(v.pw_gid)
                except KeyError:
                    raise Error(f'cannot find group "{v.pw_gid}" for "{t}"')
                if u.pw_name not in g.gr_mem:
                    raise Error(
                        f'user "{u.pw_name}" must be in the group "{g.gr_name}" for "{t}"'
                    )
                del v, g
            del i
        else:
            # NOTE(dij): Set to None to remove anything else.
            t = None
        del c
        k = expand(self.get("dev.kernel"))
        if nes(k):
            # NOTE(dij): Security Check
            #            Can only be a file owned by the calling user that has 0o0600
            #            permissions. The file must also be owned by the user's primary group.
            info(k, False, hide=True).check(
                0o7177, uid, hide=True, req=0o600, own_gid=True
            ).only(file=True)
        else:
            # NOTE(dij): Set to None to remove anything else.
            k = None
        d = expand(self.get("dev.initrd"))
        if nes(d):
            # NOTE(dij): Security Check
            #            Can only be a file owned by the calling user that has 0o0600
            #            permissions. The file must also be owned by the user's primary group.
            info(d, False, hide=True).check(
                0o7177, uid, hide=True, req=0o0600, own_gid=True
            ).only(file=True)
        else:
            # NOTE(dij): Set to None to remove anything else.
            d = None
        o = expand(self.get("dev.devicetree"))
        if nes(o):
            # NOTE(dij): Security Check
            #            Can only be a file owned by the calling user that has 0o0600
            #            permissions. The file must also be owned by the user's primary group.
            info(o, False, hide=True).check(
                0o7177, uid, hide=True, req=0o0600, own_gid=True
            ).only(file=True)
        else:
            # NOTE(dij): Set to None to remove anything else.
            o = None
        n = self.get("memory.size", 1024)
        if not isinstance(n, int) or n <= 0:
            raise Error("memory size must be a non-zero positive number")
        if self.get("memory.reserve", True):
            r = f"/dev/hugepages/{self.vmid}.ram"
            if exists(r):
                try:
                    remove(r)
                except OSError:
                    raise Error(f'memory reserve file "{r}" already exists')
            server.debug(f"[m/hydra/VM({self.vmid})]: Reserving {n}MB of memory..")
            manager.pages(server, self.vmid, round(n / HYDRA_RESERVE_SIZE))
        else:
            # NOTE(dij): Set to None to remove anything else.
            r = None
        return Restricted(
            x, e, n, r, f, q, t, k, d, o, u.pw_name, x.endswith("-x86_64")
        )

    def _build_drives(self, server, uid, user, bus, machine, opts):
        if not isinstance(self.drives, dict):
            self.drives = dict()
            return server.debug(
                f"[m/hydra/VM({self.vmid})]: Drives value was not found, skipping drive setup."
            )
        if len(self.drives) == 0:
            return server.debug(
                f"[m/hydra/VM({self.vmid})]: Drives value was empty, skipping drive setup."
            )
        w, i, b = dict(), 0, list()
        for n, d in self.drives.items():
            if not isinstance(d, dict) or len(d) == 0:
                server.warning(
                    f'[m/hydra/VM({self.vmid})]: Skipping invalid drive "{n}"!'
                )
                continue
            if "type" not in d:
                raise Error(f'drive "{n}" is missing the "type" value')
            # NOTE(dij): Expanded forms do NOT get re-saved back to the file so
            #            they can be evaluated again.
            p = expand(d.get("file"))
            if not nes(p):
                server.warning(
                    f'[m/hydra/VM({self.vmid})]: Skipping drive "{n}" with a missing "file" entry!'
                )
                continue
            if not isabs(p):
                p = f"{dirname(self.path())}/{p}"
                try:
                    v = info(p, False, hide=True)
                except OSError as err:
                    raise Error(
                        f'drive "{n}" file "{p}" does not exist or is not a file: {err}'
                    )
                # NOTE(dij): Relative paths do get saved over.
                d["file"] = p
            else:
                try:
                    v = info(p, False, hide=True)
                except OSError as err:
                    raise Error(
                        f'drive "{n}" file "{p}" does not exist or is not a file: {err}'
                    )
            # NOTE(dij): Security Check
            #            Can only be a file or block device. If the target is
            #            a block device, it must be owned by root and the
            #            calling user must be in the group on the device, if
            #            not the drive is mounted as read only. The block
            #            device permissions must be 0o0660.
            #
            #            If the target is a file and is owned by the user and
            #            it must have the user's primary group and the permissions of
            #            0o600. Unless the "readonly" value is True, in which
            #            the drive will be checked to see if the user has at least
            #            read permissions and the file is not executable.
            #
            #            If the target is a file not owned by the calling user
            #            it must have the permissions of 0o0644 and will be
            #            mounted as read only.
            #
            #            There is an exception if the device is an ISO/CD as
            #            these are always marked as read only. So these files
            #            can realistically have any permissions and owner, but
            #            we'll at least expect 0o0640.
            v.no(dir=False, link=False, char=False, hide=True)
            if v.isfile:
                if d["type"] == "cd" or d["type"] == "iso":
                    v.check(0o7133, req=0o0400)
                elif v.uid == uid:
                    v.check_if(d.get("readonly", False), 0o7133, req=0o0440).check_if(
                        not d.get("readonly", False),
                        0o7177,
                        req=0o0600,
                        own_gid=True,
                    )
                else:
                    v.check(0o7133, req=0o0644, hide=True)
                    server.info(
                        f'[m/hydra/VM({self.vmid})]: Mounting drive "{n}" target "{p}" as read only as the user '
                        f'does not have write permissions to "{p}".'
                    )
                    d["readonly"] = True
            elif v.isblockdev:
                if v.uid != 0:
                    raise PermissionError(f'block device "{p}" must be owned by root')
                v.check(0o7117, req=0o0660, hide=True)
                try:
                    g = getgrgid(v.gid)
                except KeyError:
                    raise PermissionError(f'cannot find group "{v.gid}" for "{p}"')
                if user not in g.gr_mem:
                    server.info(
                        f'[m/hydra/VM({self.vmid})]: Mounting drive "{n}" target "{p}" as read only as user is not '
                        f'in group "{g.gr_name}".'
                    )
                    d["readonly"] = True
                if not d.get("readonly", False):
                    # NOTE(dij): Don't care if we're mounting a shared disk as
                    #            read only.
                    try:
                        m = _parse_mounted()
                        if p in m:
                            raise Error(
                                f'drive "{n}" block dev "{p}" is currently mounted'
                            )
                        # NOTE(dij): Check submounts, meaning we should deter
                        #            using a blockdev that has partitions of
                        #            itself mounted.
                        for i in m:
                            if i.startswith(p):
                                raise Error(
                                    f'drive "{n}" block dev "{p}" is currently sub-mounted'
                                )
                        del m
                    except OSError:
                        raise Error(
                            f'drive "{n}" block dev "{p}" cannot be checked for mount status'
                        )
                del g
            else:
                # NOTE(dij): This shouldn't reach here, but catch any non-file/blockdev
                #            disk mount attempts.
                raise Error(
                    f'drive "{n}" file "{p}" is not a valid file or block device'
                )
            del v
            v = d.get("index")
            if isinstance(v, int):
                if v < 0 or v in b:
                    server.warning(
                        f'[m/hydra/VM({self.vmid})]: Removing drive "{n}" "index" value as its invalid!'
                    )
                    del d["index"]
                    v = max(b) + 1 if len(b) > 0 else 0
                    d["index"] = v
                    b.append(v)
                else:
                    b.append(v)
            else:
                v = max(b) + 1 if len(b) > 0 else 0
                d["index"] = v
                b.append(v)
            del v
            t = d.get("type")
            # NOTE(dij): The "i" var is the number of IDE devices added. QEMU on
            #            q35 has a hard limit of 4 on a single bus. We shouldn't
            #            be using a lot of IDE so it's alright to break on.
            if not nes(t):
                d["type"] = "ide"
                i += 1
            elif t == "ide" or t == "cd" or t == "iso":
                i += 1
            del t
            if i > 4:
                raise Error("max limit of 4 IDE devices reached")
            if "format" not in d:
                if d["type"] == "cd" or d["type"] == "iso":
                    d["format"] = "raw"
                else:
                    # NOTE(dij): Try to guess based on extension.
                    _, k = splitext(p)
                    if nes(k) and len(k) >= 2:
                        d["format"] = k[1:]
                    else:
                        d["format"] = "raw"
            w[n] = d
            del d, p
        del i, b
        i, r, a, k = 0, list(), False, 0
        # NOTE(dij): This loop will re-save all formatted drive entries.
        for n, d in w.items():
            f = d["type"] if d["type"].endswith("flash") else "none"
            s = (
                f'id={n},file={d["file"]},format={d["format"]},index={d["index"]},'
                f"if={f},detect-zeroes=unmap"
            )
            del f
            # NOTE(dij): Determine how we handle the drive based on the type and
            #            driver.
            if not d.get("direct", True):
                s += ",aio=io_uring"
            elif d["format"] == "raw" and d["type"] == "virtio":
                s += ",aio=native,cache.direct=on"
            else:
                s += ",aio=threads,cache=writeback"
            u = False
            # NOTE(dij): CDs and ISOs are always read only.
            if d.get("readonly", False) or d["type"] == "cd" or d["type"] == "iso":
                s += ",readonly=on"
                u = True
            if d.get("discard", False):
                if d["type"] == "scsi":
                    s += ",discard=on"
                else:
                    s += ",discard=unmap"
            if opts.temp and not u:
                server.debug(
                    f'[m/hydra/VM({self.vmid})]: Setting drive "{n}" as a temporary drive due to startup option.'
                )
            # NOTE(dij): Gate to readonly. Can't be temporary if we can't write
            #            to it anyway.
            if (d.get("temp", False) or opts.temp) and not u:
                s += ",snapshot=on"
            del u
            r += ["-drive", s]
            del s
            if d["type"] == "usb":
                r += ["-device", f"usb-storage,bus=usb-bus3.0,drive={n}"]
            elif d["type"] == "scsi":
                # NOTE(dij): If the SCSI bus isn't added, add it.
                if not a:
                    a = True
                    r += [
                        "-device",
                        f"virtio-scsi-pci,id=scsi0,bus={bus}.0,addr=0x5,iothread=iothread0",
                    ]
                r += [
                    "-device",
                    f"scsi-hd,bus=scsi0.0,channel=0,scsi-id=0,lun={i},drive={n},id=scsi-{i},rotation_rate=1",
                ]
                i += 1
            elif d["type"] == "virtio":
                r += [
                    "-device",
                    f'virtio-blk-pci,id={n}-dev,drive={n},bus={bus}.0,bootindex={d["index"]}',
                ]
            elif not d["type"].endswith("flash"):
                # NOTE(dij): Treat q35 and older machines differently. Q35 will default
                #            to the SATA bus if nothing is specified. Older machines
                #            get IDE.
                v = i + 1 if "q35" in machine else i / 2
                if d["type"] == "sata":
                    t = "sata"
                    if k == 0:
                        # NOTE(dij): Add the SATA bus if not added already.
                        k = 1
                        r += ["-device", "ich9-ahci,id=sata"]
                    v = k
                else:
                    t = "ide"
                r += [
                    "-device",
                    f'ide-{"cd" if d["type"] == "cd" or d["type"] == "iso" else "hd"},id={n}-dev,'
                    f'drive={n},bus={t}.{v},bootindex={d["index"]}',
                ]
                if t == "sata":
                    k += 1
                else:
                    i += 1
                del t, v
            self.drives[n] = d
        del i, a, k, w
        return r

    def _stop(self, server, manager, force, timeout=90, tap=False):
        if self._state == HYDRA_STATE_STOPPED:
            return
        if not force and tap:
            if self._state == HYDRA_STATE_SLEEPING:
                raise Error("cannot ACPI shutdown while suspended")
            server.debug(
                f'[m/hydra/VM({self.vmid})]: "Tapping" the power button for ACPI shutdown.'
            )
            if self._agent:
                return self._cmd(server, "guest-shutdown", ga=True)
            try:
                self._cmd(server, "guest-shutdown", ga=True, timeout=1)
            except Error:
                self._cmd(server, "system_powerdown")
            return
        if not force and self._state == HYDRA_STATE_WAITING:
            raise Error("cannot non-force stop while waiting")
        if not force and self._running():
            if self._event is not None:
                raise Error("soft shutdown already in progress")
            if self._state == HYDRA_STATE_SLEEPING:
                raise Error("cannot ACPI shutdown while suspended")
            try:
                t = num(timeout, False)
            except ValueError:
                raise Error("timeout must be a non-zero positive number")
            if t == 0:
                raise Error("timeout must be a non-zero positive number")
            if self._state == HYDRA_STATE_SLEEPING:
                self._sleep(server, False)
            if self._agent:
                self._cmd(server, "guest-shutdown", ga=True)
            else:
                try:
                    self._cmd(server, "guest-shutdown", ga=True)
                except Error:
                    self._cmd(server, "system_powerdown")
            self._event = server.task(t, self._stop, (server, manager, True))
            server.debug(
                f'[m/hydra/VM({self.vmid})]: Started shutdown, grace for "{t}" seconds.'
            )
            del t
            return
        # NOTE(dij): If force is true, we're not throwing any errors.
        stop(self._proc)
        if self._proc is not None:
            try:
                e = self._proc.wait(0.25)
            except Exception:
                e = None
        else:
            e = None
        if isinstance(e, int) and e != 0:
            server.warning(f"[m/hydra/VM({self.vmid})]: Exit was non-zero ({e}).")
        # NOTE(dij): If debugging is enabled check the output of the process.
        if self._output is None and self._debug:
            try:
                o = self._proc.stdout.read().replace(NEWLINE, ";")
                v = self._proc.stderr.read().replace(NEWLINE, ";")
                if nes(o):
                    r = f"{o};{v}" if nes(v) else o
                elif nes(v):
                    r = v
                else:
                    r = None
                del o, v
            except (ValueError, AttributeError, OSError):
                r = None
            if isinstance(r, str) and len(r) == 0:
                r = None
            elif nes(r):
                r = r.strip()
                if r.endswith(";"):
                    r = r[0:-1]  # Remove trailer
                server.error(f"[m/hydra/VM({self.vmid})]: Process output ({r}).")
        else:
            r = None
        if self._output is None:
            self._output = (e, r)
        server.info(f"[m/hydra/VM({self.vmid})]: Stopping and cleaning up..")
        if self._stpm is not None:
            stop(self._stpm)
        stop(self._proc)
        if self._proc is not None:
            try:
                self._proc.wait(0.5)
            except Exception:
                pass
        self._proc = None
        self._stpm = None
        self._close_adapters(server)
        self._event = cancel_nul(server, self._event)
        self._usb_clean(server, manager)
        remove_file(f"{self._path}.pid")
        remove_file(f"{self._path}.vnc")
        remove_file(f"{self._path}.sock")
        remove_file(f"{self._path}.swtpm")
        remove_file(f"{self._path}.swtpm.pid")
        try:
            if self.get("memory.reserve", True):
                manager.pages(server, self.vmid, None, True)
        except Error as err:
            server.warning(
                f"HYDRA: VM({self.vmid}) Error removing reserved memory!", err
            )
        self._state = HYDRA_STATE_STOPPED

    def _usb_add(self, server, manager, vendor, product, slow=False):
        if self._state != HYDRA_STATE_RUNNING:
            raise Error("invalid state to add USB devices")
        if not nes(vendor) or not nes(product):
            raise Error("device vendor and product cannot be empty")
        d, i = get_devices(), f"{vendor}:{product}".lower()
        if i not in d:
            raise Error(f'device "{i}" not found')
        del d
        if not self._running():
            raise Error("cannot add a device while stopped")
        if i in self._usb:
            raise Error(f'device "{i}" is already mounted as "usb-dev-{self._usb[i]}"!')
        if i in manager._usb:
            raise Error(f'device "{i}" is already mounted to VM({manager._usb[i]})!')
        n = 1 if len(self._usb) == 0 else max(self._usb.values()) + 1
        nulexec(
            ["/usr/bin/chown", "-R", HYDRA_USER, HYDRA_DIR_DEVICES],
            wait=True,
            errors=False,
        )
        b = "usb-bus2.0" if slow else "usb-bus3.0"
        try:
            self._cmd(
                server,
                "device_add",
                {
                    "id": f"usb-dev-{n}",
                    "bus": b,
                    "driver": "usb-host",
                    "vendorid": int(vendor, 16),
                    "productid": int(product, 16),
                },
            )
        except OSError as err:
            raise Error(f'cannot add device "{i}": {err}')
        self._usb[i], manager._usb[i] = n, self.vmid
        server.debug(
            f'[m/hydra/VM({self.vmid})]: Connected USB device "{i}" to bus "{b}" with ID {n}.'
        )
        server.notify(
            "Hydra USB Device Connected",
            f'USB Device "{i}" was connected to VM({self.vmid}).',
            "uos-installtool",
        )
        del b, i
        return n

    def _usb_remove(self, server, manager, vendor=None, product=None, usb=None):
        if usb is not None:
            try:
                i = num(usb, False)
            except ValueError:
                raise Error("device ID must be a non-zero positive number")
            if i not in self._usb.values():
                raise Error(f'cannot find device with ID "{i}"')
            n = None
            for k, v in self._usb.items():
                # Grab the device vendor:product from the ID
                if v == i:
                    n = k
                    break
            if n is None:
                raise Error(f'cannot find device with ID "{i}"')
        elif nes(vendor) and nes(product):
            n = f"{vendor}:{product}".lower()
            i = self._usb.get(n)
            if i is None:
                raise Error(f'device "{n}" is not connected')
        else:
            raise Error("device ID or device vendor/product must be specified")
        if self._running():
            try:
                self._cmd(server, "device_del", {"id": f"usb-dev-{i}"})
            except OSError as err:
                raise Error(f'cannot remove device "{i}": {err}')
        server.debug(
            f'[m/hydra/VM({self.vmid})]: Removed USB device "{n}" with ID {i}.'
        )
        server.notify(
            "Hydra USB Device Removed",
            f'USB Device "{self._usb[n]}" was disconnected from VM({self.vmid}).',
            "usb-creator",
        )
        del self._usb[n], manager._usb[n], i
        del n

    def _cmd(self, server, command, args=None, ga=False, timeout=2.5, close=True):
        if not self._running():
            # NOTE(dij): I don't see this path being called, but I'm
            #            leaving this logic here to prevent any weird
            #            shit happening.
            return (None, None)
        if not nes(command) and not isinstance(command, dict):
            raise Error('"command" must be a dict or string')
        if ga and self._state == HYDRA_STATE_SLEEPING:
            server.warning(
                f"[m/hydra/VM({self.vmid})]: Sending a GA command to a sleeping VM might not work!"
            )
        d = {"execute": command}
        if isinstance(args, dict):
            d["arguments"] = args
        try:
            p = dumps(d).encode("UTF-8")
        except (TypeError, UnicodeDecodeError):
            raise Error("invalid payload data")
        f = f'{self._path}.{"qga" if ga else "sock"}'
        server.debug(f'[m/hydra/VM({self.vmid})]: Sending "{d}" to "{f}".')
        del d
        s = socket(AF_UNIX, SOCK_STREAM)
        s.settimeout(timeout)
        try:
            s.connect(f)
            # NOTE(dij): Trigger initial server greeting
            s.sendall(b"\r\n")
            if not ga:
                # NOTE(dij): Read initial server greeting
                _command_response(s.recv(HYDRA_SOCK_BUF_SIZE))
                # NOTE(dij): Capabilities negotiation response
                s.sendall(_HYDRA_IPC)
                r = _command_response(_read_full(s, HYDRA_SOCK_BUF_SIZE))
                if r is None:
                    raise Error("invalid hello response")
                server.debug(f'[m/hydra/VM({self.vmid})]: Hello response "{r}".')
                del r
            # NOTE(dij): Now send our command
            s.sendall(p)
            s.sendall(b"\r\n")
            r = _command_response(_read_full(s, HYDRA_SOCK_BUF_SIZE))
            server.debug(
                f'[m/hydra/VM({self.vmid})]: Command "{command}" response "{r}".'
            )
        finally:
            if close:
                s.close()
            del f, p
        if ga and not self._agent:
            # NOTE(dij): If we received a response from the Guest Agent, flag it
            #            so we know to use it again.
            self._agent = True
        return (r, s)


class Snapper(object):
    __slots__ = ("vm", "job", "sock", "name")

    def __init__(self, vm, job, sock, name):
        self.vm = vm
        self.job = job
        self.sock = sock
        self.name = name
        self.sock.setblocking(False)

    def close(self):
        self.sock.close()

    def fileno(self):
        return self.sock.fileno()

    def result(self, server):
        try:
            self.sock.sendall(b'{"execute":"query-jobs"}\r\n')
            j = _command_response(_read_full(self.sock, HYDRA_SOCK_BUF_SIZE))
            r, e = _is_snapshot_done(self.job, j)
            del j
            self.sock.sendall(
                f'{{"execute":"job-dismiss","arguments":{{"id":"{self.job}"}}}}'.encode(
                    "UTF-8"
                )
            )
            if nes(e):
                self.sock.sendall(b'{"execute":"cont"}')
                return e
            if r:
                return None
            return "unknown result"
        except Error as err:
            server.error(
                f"[m/hydra/VM({self.vm.vmid})]: Cannot read Snapper result: {err}!", err
            )
            return str(err)

    def is_done(self, server):
        try:
            r = _command_response(_read_full(self.sock, HYDRA_SOCK_BUF_SIZE))
            if not isinstance(r, list) or len(r) == 0:
                return False
            for i in r:
                if (
                    "event" not in i
                    or "data" not in i
                    or i["event"] != "JOB_STATUS_CHANGE"
                ):
                    continue
                v = i["data"]
                if not isinstance(v, dict) or len(v) == 0:
                    continue
                if v.get("status") == "concluded" and v.get("id") == self.job:
                    return True
                del v
            del r
            return False
        except Error as err:
            server.error(
                f"[m/hydra/VM({self.vm.vmid})]: Cannot read Snapper result: {err}!", err
            )
            return True


class HydraServer(object):
    __slots__ = ("_vms", "_dns", "_usb", "_poll", "_pages", "_snaps", "_running")

    def __init__(self):
        self._vms = dict()
        self._dns = None
        self._usb = dict()
        self._poll = epoll()
        self._pages = dict()
        self._snaps = dict()
        self._running = False

    def start(self, server):
        if self._running:
            return True
        if not isfile(HYDRA_EXEC_VM):
            return server.error(
                "[m/hydra]: The required QEMU package is not installed, Hydra VMs cannot run!"
            )
        server.debug("[m/hydra]: Staring up and allocating resources..")
        try:
            n = IPv4Network(HYDRA_BRIDGE_NETWORK)
        except ValueError as err:
            return server.error(
                f'[m/hydra]: Network bridge address "{HYDRA_BRIDGE_NETWORK}" is invalid!',
                err,
            )
        if n.num_addresses < 3:
            return server.error(
                f'[m/hydra]: Network bridge address "{HYDRA_BRIDGE_NETWORK}" host allocation size is too small!'
            )
        server.debug(f'[m/hydra]: Creating VM Bridge interface "{HYDRA_BRIDGE}"..')
        # NOTE(dij): Delete any existing bridge entries.
        nulexec(
            ["/usr/bin/ip", "link", "set", HYDRA_BRIDGE, "down"],
            wait=True,
            errors=False,
        )
        nulexec(
            ["/usr/bin/ip", "link", "del", "name", HYDRA_BRIDGE],
            wait=True,
            errors=False,
        )
        try:
            nulexec(
                ["/usr/bin/ip", "link", "add", "name", HYDRA_BRIDGE, "type", "bridge"],
                wait=True,
            )
            nulexec(
                [
                    "/usr/bin/ip",
                    "addr",
                    "add",
                    "dev",
                    HYDRA_BRIDGE,
                    f"{n[1]}/{n.prefixlen}",
                ],
                wait=True,
            )
            nulexec(["/usr/bin/ip", "link", "set", HYDRA_BRIDGE, "up"], wait=True)
        except OSError as err:
            server.error(
                f'[m/hydra]: Cannot create VM Bridge interface "{HYDRA_BRIDGE}"!', err
            )
            return self.stop(server, True)
        try:
            write("/proc/sys/net/ipv4/ip_forward", "1")
            write(f"/proc/sys/net/ipv4/conf/{HYDRA_BRIDGE}/forwarding", "1")
        except OSError as err:
            server.error("[m/hydra]: Cannot setup VM Bridge forwarding!", err)
            return self.stop(server, True)
        server.debug("[m/hydra]: Creating VM directories..")
        try:
            if not isdir(HYDRA_DIR):
                mkdir(HYDRA_DIR)
            if not isdir(HYDRA_DIR_DHCP):
                mkdir(HYDRA_DIR_DHCP)
            if not isdir(HYDRA_DIR_SNAPS):
                mkdir(HYDRA_DIR_SNAPS)
            chmod(HYDRA_DIR, 0o0755, follow_symlinks=False)
            chmod(HYDRA_DIR_DHCP, 0o0750, follow_symlinks=False)
            chmod(HYDRA_DIR_SNAPS, 0o0750, follow_symlinks=False)
            chown(HYDRA_DIR, 0, _hydra_user().pw_gid, follow_symlinks=False)
            chown(
                HYDRA_DIR_DHCP,
                _hydra_user().pw_uid,
                _hydra_user().pw_gid,
                follow_symlinks=False,
            )
            chown(HYDRA_DIR_SNAPS, 0, 0, follow_symlinks=False)
        except OSError as err:
            server.error("[m/hydra]: Cannot create VM directories!", err)
            return self.stop(server, True)
        i = info(HYDRA_EXEC_DNS, sym=False, no_fail=True)
        if i.isfile:
            try:
                i.check(0o7022, 0, 0, req=0o0755)
            except OSError as err:
                return server.error(
                    f'[m/hydra]: Dnsmasq binary "{HYDRA_EXEC_DNS}" has invalid permissions!',
                    err,
                )
            server.debug("[m/hydra]: Creating DNS/DHCP configuration..")
            c = HYDRA_CONFIG_DNS.format(
                ip=f"{n[1]}",
                end=f"{n[n.num_addresses - 2]}",
                dir=HYDRA_DIR_DHCP,
                name=HYDRA_BRIDGE_NAME,
                user=HYDRA_USER,
                start=f"{n[2]}",
                network=HYDRA_BRIDGE_NETWORK,
                netmask=f"{n.netmask}",
                interface=HYDRA_BRIDGE,
            )
            try:
                write(HYDRA_FILE_DNS, c, perms=0o0640)
                chown(HYDRA_FILE_DNS, 0, _hydra_user().pw_gid, follow_symlinks=False)
            except OSError as err:
                server.error("[m/hydra]: Cannot create DNS/DHCP configuration!", err)
                return self.stop(server, True)
            finally:
                del c
            try:
                self._dns = nulexec(
                    [
                        HYDRA_EXEC_DNS,
                        "--keep-in-foreground",
                        "--log-facility=-",
                        f"--user={HYDRA_USER}",
                        f"--conf-file={HYDRA_FILE_DNS}",
                    ]
                )
            except OSError as err:
                server.error("[m/hydra]: Cannot start the Dnsmasq service!", err)
                return self.stop(server, True)
            server.debug("[m/debug]: Dnsmasq service was started.")
        else:
            server.warning(
                "[m/hydra]: Dnsmasq is not installed, VMs will lack network connectivity!"
            )
        del i
        i = info(HYDRA_EXEC_SMB, sym=False, no_fail=True)
        if i.isfile:
            try:
                i.check(0o7022, 0, 0, req=0o0755)
            except OSError as err:
                return server.error(
                    f'[m/hydra]: Samba binary "{HYDRA_EXEC_SMB}" has invalid permissions!',
                    err,
                )
            server.debug("[m/hydra]: Creating Samba configuration..")
            s = HYDRA_CONFIG_SMB.format(
                ip=f"{n[1]}", name=NAME, network=HYDRA_BRIDGE_NETWORK
            )
            try:
                write(HYDRA_FILE_SMB, s, 0o0640)
                chown(HYDRA_FILE_SMB, 0, _hydra_user().pw_gid, follow_symlinks=False)
            except OSError as err:
                server.error("[m/hydra]: Cannot create Samba configuration!", err)
                return self.stop(server, True)
            finally:
                del s
            try:
                # NOTE(dij): We're running this as a separate systemd service
                #            to ensure user home directory protection for the
                #            'smd-daemon' service but allow for users to use SMB
                #            to write files to their home dir.
                nulexec(
                    ["/usr/bin/systemctl", "start", "smd-hydra-smb.service"], wait=True
                )
            except OSError as err:
                server.error("[m/hydra]: Cannot start the Samba service!", err)
                return self.stop(server, True)
            server.debug("[m/debug]: Samba service was started.")
        else:
            server.warning(
                "[m/hydra]: Samba is not installed, VMs will lack file sharing!"
            )
        del n, i
        self._running = True
        server.info("[m/hydra]: Startup complete.")
        return True

    def thread(self, server):
        if not self._running:
            if len(self._vms) == 0:
                return
            server.debug("[m/hydra]: Starting Hydra for pending VMs..")
            if self.start(server):
                return
            self._vms.clear()
            return server.error(
                "[m/hydra]: Hydra startup failed, clearing pending VMs!"
            )
        if len(self._vms) == 0:
            server.debug("[m/hydra]: Shutting down Hydra for inactivity.")
            return self.stop(server, False)
        self._check_snaps(server)
        for v, x in list(self._vms.items()):
            x._thread(server, self)
            if x._state < HYDRA_STATE_STOPPED:
                continue
            server.debug(f"[m/hydra/VM({v})]: Removing shutdown VM.")
            server.notify(
                "Hydra VM Status", f"VM({v}) has shutdown{x._msg()}", "virt-viewer"
            )
            x._stop(server, self, True)
            if len(self._snaps) > 0:
                for k, i in list(self._snaps.items()):
                    if i.vm.vmid != v:
                        continue
                    i.close()
                    del self._snaps[k]
            del self._vms[v]

    def stop(self, server, force):
        if self._running:
            server.debug("[m/hydra]: Stopping and releasing resources..")
        server.debug("[m/hydra]: Stopping all active VMs..")
        for x in list(self._snaps.values()):
            try:
                x.close()
            except OSError as err:
                server.warning(f"[m/hydra]: Cannot close Snapper: {err}!", err)
        for v, x in list(self._vms.items()):
            try:
                x._stop(server, self, True)
            except OSError as err:
                server.warning(f"[m/hydra]: Cannot stop VM({v})!", err)
        server.debug("[m/hydra]: Stopping services..")
        nulexec(
            ["/usr/bin/systemctl", "stop", "smd-hydra-smb.service"],
            wait=True,
            errors=False,
        )
        stop(self._dns)
        self._vms.clear()
        self._usb.clear()
        self._snaps.clear()
        if self._running or force:
            server.debug("[m/hydra]: Removing VM Bridge..")
            try:
                nulexec(["/usr/bin/ip", "link", "set", HYDRA_BRIDGE, "down"], wait=True)
            except OSError as err:
                if not force:
                    server.error("[m/hydra]: Cannot disable the VM Bridge!", err)
            try:
                nulexec(["/usr/bin/ip", "link", "del", "name", HYDRA_BRIDGE], wait=True)
            except OSError as err:
                if not force:
                    server.error("[m/hydra]: Cannot remove the VM Bridge!", err)
        if self._running:
            try:
                write(HYDRA_RESERVE, "0")
            except OSError as err:
                server.warning("[m/hydra]: Cannot clear reserved memory!", err)
        if isdir(HYDRA_DIR):
            try:
                rmtree(HYDRA_DIR)
            except OSError as err:
                server.error("[m/hydra]: Cannot remove the Hydra directory!", err)
        if self._running:
            server.debug("[m/hydra]: Shutdown complete.")
        self._running = False

    def _check_snaps(self, server):
        if len(self._snaps) == 0:
            return
        try:
            for f, _ in self._poll.poll(timeout=0):
                if f not in self._snaps:
                    continue
                v = self._snaps[f]
                server.debug(f"[m/hydra/VM({v.vm.vmid})]: Snapper has poll data.")
                if not v.is_done(server):
                    continue
                server.debug(f"[m/hydra/VM({v.vm.vmid})]: Snapper is complete!")
                self._poll.unregister(f)
                del self._snaps[f]
                v.vm._snap_done(server, v.job, v.name, v.result(server))
                v.close()
                del v
        except Error as err:
            server.error(f"[m/hydra]: Cannot poll running Snappers: {err}!", err)

    def hook(self, server, message):
        if message.header() == HOOK_SHUTDOWN:
            if self._poll is not None:
                self._poll.close()
                self._poll = None
            return self.stop(server, False)
        if not isinstance(message.type, int):
            return
        if message.type == HYDRA_STATUS and len(message) <= 2:
            return {"vms": [vm._status() for vm in self._vms.values()]}
        if message.user and message.type == HYDRA_USER_DIRECTORY:
            return message.multicast()
        if message.all:
            for i in self._vms.values():
                if not i._running():
                    continue
                try:
                    if message.type == HYDRA_STOP:
                        i._stop(server, self, message.force)
                    elif message.type == HYDRA_WAKE or message.type == HYDRA_SLEEP:
                        i._sleep(server, message.type == HYDRA_SLEEP)
                    elif message.type == HYDRA_HIBERNATE:
                        i._hibernate(server)
                    elif message.type == HYDRA_RESTART:
                        i._restart(server, message.force)
                except Error as err:
                    if message.type == HYDRA_STOP:
                        server.error(
                            f"[m/hydra/VM({i.vmid})]: Cannot stop the VM!", err
                        )
                    elif message.type == HYDRA_WAKE:
                        server.error(
                            f"[m/hydra/VM({i.vmid})]: Cannot resume the VM!", err
                        )
                    elif message.type == HYDRA_SLEEP:
                        server.error(
                            f"[m/hydra/VM({i.vmid})]: Cannot suspend the VM!", err
                        )
                    elif message.type == HYDRA_HIBERNATE:
                        server.error(
                            f"[m/hydra/VM({i.vmid})]: Cannot hibernate the VM!", err
                        )
                    elif message.type == HYDRA_RESTART:
                        server.error(
                            f"[m/hydra/VM({i.vmid})]: Cannot restart/reset the VM!", err
                        )
            return {"vms": [vm._status() for vm in self._vms.values()]}
        try:
            x, i = self._get_vm(server, message)
        except Error as err:
            server.error("[m/hydra]: Cannot load the VM!", err)
            return as_error(f"cannot load VM: {err}")
        if message.user:
            message.set("vmid", x.vmid)
            message.set("file", x.path())
            del x, i
            return message.multicast()
        if message.type == HYDRA_STATUS:
            return x._status()
        if message.type == HYDRA_START:
            if not i:
                if x._state == HYDRA_STATE_SLEEPING:
                    # Wake VM if we're attempting to start a sleeping VM.
                    # This calls wake if the VM is already running.
                    x._start(server, self, message.uid(), message)
                # NOTE(dij): Ensure that the sockets never fail to get set as
                #            readable. This will trigger when clients try to view
                #            the VM's screen
                x._socket_perms_set()
                return x._status()
            try:
                if not self.start(server):
                    server.error(f"[m/hydra/VM({x.vmid})]: Server setup failed!")
                    return as_error(f"cannot start VM {x.vmid}: Server setup failed")
                x._start(server, self, message.uid(), message)
                self._vms[x.vmid] = x
            except Error as err:
                # NOTE(dij): Remove VM as it failed on launch.
                if x.vmid in self._vms and (
                    not x._running() or x._state != HYDRA_STATE_RUNNING
                ):
                    del self._vms[x.vmid]
                server.error(f"[m/hydra/VM({x.vmid})]: Cannot start the VM!", err)
                return as_error(f"cannot start VM {x.vmid}: {err}")
            return x._status()
        del i
        # Can run without the VM in the running state.
        if message.type == HYDRA_USB_QUERY:
            s = x._status()
            s["usb"] = x._usb
            return s
        if not x._running() or x._state == HYDRA_STATE_STOPPED:
            return as_error(f"VM {x.vmid} is not running!")
        if message.type == HYDRA_SLEEP or message.type == HYDRA_WAKE:
            try:
                x._sleep(server, message.type == HYDRA_SLEEP)
            except Error as err:
                if message.type == HYDRA_SLEEP:
                    server.error(f"[m/hydra/VM({x.vmid})]: Cannot suspend the VM!", err)
                    return as_error(f"cannot suspend VM {x.vmid}: {err}")
                server.error(f"[m/hydra/VM({x.vmid})]: Cannot resume the VM!", err)
                return as_error(f"cannot resume VM {x.vmid}: {err}")
            return x._status()
        if message.type == HYDRA_SNAP_LIST:
            v = x._status()
            try:
                v["snaps"] = x._snap_list(server)
                v["snap_current"] = x._snap_last(server)
            except Error as err:
                server.error(
                    f"[m/hydra/VM({x.vmid})]: Cannot read the Snapshot data!", err
                )
                return as_error(f"cannot read Snapshots for VM {x.vmid}: {err}")
            return v
        if message.type == HYDRA_SNAP_TAKE:
            if not valid_snap_name(message.name):
                server.error(
                    f'[m/hydra/VM({x.vmid})]: Invalid Snapshot name "{message.name}" supplied!'
                )
                return as_error("invalid Snapshot name")
            try:
                x._snap_capture(server, self, message.name)
            except Error as err:
                server.error(f"[m/hydra/VM({x.vmid})]: Cannot Snapshot the VM!", err)
                return as_error(f"cannot take Snapshot for VM {x.vmid}: {err}")
            return x._status()
        if message.type == HYDRA_SNAP_DELETE:
            if not valid_snap_name(message.name):
                server.error(
                    f'[m/hydra/VM({x.vmid})]: Invalid Snapshot name "{message.name}" supplied!'
                )
                return as_error("invalid Snapshot name")
            try:
                x._snap_delete(server, self, message.name)
            except Error as err:
                server.error(
                    f"[m/hydra/VM({x.vmid})]: Cannot delete the VM Snapshot!", err
                )
                return as_error(f"cannot delete Snapshot for VM {x.vmid}: {err}")
            return x._status()
        if message.type == HYDRA_SNAP_RESTORE:
            if not valid_snap_name(message.name):
                server.error(
                    f'[m/hydra/VM({x.vmid})]: Invalid Snapshot name "{message.name}" supplied!'
                )
                return as_error("invalid Snapshot name")
            try:
                x._snap_restore(server, self, message.name)
            except Error as err:
                server.error(
                    f"[m/hydra/VM({x.vmid})]: Cannot restore the VM Snapshot!", err
                )
                return as_error(f"cannot restore Snapshot for VM {x.vmid}: {err}")
            return x._status()
        if message.type == HYDRA_STOP:
            try:
                x._stop(server, self, message.force, message.get("timeout", 90))
            except Error as err:
                server.error(f"[m/hydra/VM({x.vmid})]: Cannot stop the VM!", err)
                return as_error(f"cannot stop VM {x.vmid}: {err}")
            return x._status()
        if message.type == HYDRA_GA_IP:
            try:
                return x._ip(server)
            except Error as err:
                server.error(
                    f"[m/hydra/VM({x.vmid})]: Cannot check the VM Guest Agent interfaces!",
                    err,
                )
                return as_error(f"cannot check the GA for VM {x.vmid}: {err}")
        if message.type == HYDRA_GA_PING:
            try:
                return x._ping(server)
            except Error as err:
                server.error(
                    f'[m/hydra/VM({x.vmid})]: Cannot "ping" check the VM Guest Agent!',
                    err,
                )
                return as_error(f"cannot check the GA for VM {x.vmid}: {err}")
        if message.type == HYDRA_TAP:
            try:
                x._stop(server, self, False, message.get("timeout", 90), tap=True)
            except Error as err:
                server.error(f'[m/hydra/VM({x.vmid})]: Cannot ACPI "tap" the VM!', err)
                return as_error(f"cannot ACPI tap VM {x.vmid}: {err}")
            return True
        if message.type == HYDRA_RESTART:
            try:
                x._restart(server, message.force)
            except Error as err:
                server.error(
                    f"[m/hydra/VM({x.vmid})]: Cannot restart/reset the VM!", err
                )
                return as_error(f"cannot restart/reset VM {x.vmid}: {err}")
            return True
        if message.type == HYDRA_HIBERNATE:
            try:
                x._hibernate(server)
            except Error as err:
                server.error(f"[m/hydra/VM({x.vmid})]: Cannot Hibernate the VM!", err)
                return as_error(f"cannot Hibernate VM {x.vmid}: {err}")
            return True
        if message.type == HYDRA_USB_CLEAN:
            try:
                x._usb_clean(server, self)
            except Error as err:
                server.error(f"[m/hydra/VM({x.vmid})]: Cannot remove USB devices!", err)
                return as_error(f"cannot remove USB devices from VM {x.vmid}: {err}")
            return x._status()
        if message.type == HYDRA_USB_ADD:
            try:
                x._usb_add(server, self, message.vendor, message.product, message.slow)
            except Error as err:
                server.error(
                    f"[m/hydra/VM({x.vmid})]: Cannot add USB device to the VM!", err
                )
                return as_error(f"cannot add device to VM {x.vmid}: {err}")
            return x._status()
        if message.type == HYDRA_USB_DELETE:
            try:
                x._usb_remove(
                    server, self, message.vendor, message.product, message.usb
                )
            except Error as err:
                server.error(
                    f"[m/hydra/VM({x.vmid})]: Cannot remove USB device from the VM!",
                    err,
                )
                return as_error(f"cannot remove device from VM {x.vmid}: {err}")
            return x._status()
        if message.type == HYDRA_SEND_INPUT:
            try:
                x._input(server, message.input, message.caps)
            except Error as err:
                server.error(
                    f"[m/hydra/VM({x.vmid})]: Cannot send input to the VM!", err
                )
                return as_error(f"cannot send input to VM {x.vmid}: {err}")
            return True
        return as_error("unknown or invalid command")

    def _get_vm(self, server, message):
        if message.vmid is not None:
            try:
                i = num(message.vmid)
            except ValueError:
                raise Error(f'invalid VMID "{message.vmid}"')
            v = self._vms.get(i)
            if v is not None:
                return v, False
            del i
        if nes(message.file):
            p = load_vm(message.file, server=True)
            if not nes(p):
                raise Error(f'no valid config at "{message.file}"')
            v = VM(p, message.uid())
        else:
            raise Error("no VMID or path supplied")
        if v.vmid in self._vms and self._vms[v.vmid]._running():
            server.debug(
                f'[m/hydra/VM({v.vmid})]: Loaded from file "{v.path()}", but returning running instace!'
            )
            return self._vms[v.vmid], False
        server.debug(f'[m/hydra/VM({v.vmid})]: Loaded from file "{v.path()}".')
        return v, True

    def hibernate(self, server, message):
        if message.type != MSG_PRE or len(self._vms) == 0:
            return
        server.info("[m/hydra]: Suspending VMS for due to Hibernation/Suspend!")
        for x in self._vms.values():
            try:
                if x._state == HYDRA_STATE_SLEEPING:
                    continue
                x._sleep(server, True)
            except Error as err:
                server.error(f"[m/hydra/VM({x.vmid})]: Cannot suspend the VM!", err)

    def pages(self, server, vmid, size, remove=False):
        if remove and vmid not in self._pages:
            return
        if not remove and (not isinstance(size, int) or size <= 0):
            return
        if remove:
            n = self._pages[vmid]
            if not isinstance(size, int):
                size = n
            x = sum(self._pages.values()) - max(n, size)
            try:
                write(HYDRA_RESERVE, f"{x}")
            except OSError as err:
                raise Error(f"cannot reserve {x} pages: {err}")
            if size >= n:
                remove_file(f"/dev/hugepages/{vmid}.ram")
                del self._pages[vmid]
            else:
                self._pages[vmid] = n - size
            del x
            return server.debug(
                f"[m/hydra/VM({vmid})]: Removed {size} pages of reserved memory."
            )
        x = sum(self._pages.values()) + size
        try:
            write(HYDRA_RESERVE, f"{x}")
        except OSError as err:
            raise Error(f"cannot reserve {x} pages: {err}")
        if vmid not in self._pages:
            self._pages[vmid] = size
        else:
            self._pages[vmid] += size
        del x
        server.debug(f"[m/hydra/VM({vmid})]: Added {size} pages of reserved memory.")

    def _register_snap(self, server, vm, job, sock, name):
        v = Snapper(vm, job, sock, name)
        f = v.fileno()
        self._snaps[f] = v
        self._poll.register(f, EPOLLIN | EPOLLHUP | EPOLLERR)
        server.debug(
            f"[m/hydra/VM({vm.vmid})]: Registered a Snapper with FD({f}) and Job({job})."
        )
        del f, v


def _key_translate(v):
    if v == 0xA:
        return ({"type": "qcode", "data": "RET"}, False)
    if v == 0xD:
        return ({"type": "qcode", "data": "LF"}, False)
    if v == 0x20:
        return ({"type": "qcode", "data": "spc"}, False)
    if v in HYDRA_KEYS_SIMPLE:
        return ({"type": "qcode", "data": f"{v:c}"}, False)
    if 0x41 <= v <= 0x5A:
        return ({"type": "qcode", "data": f"{v + 0x20:c}"}, True)
    if v in HYDRA_KEYS_NAMED:
        return ({"type": "qcode", "data": HYDRA_KEYS_NAMED[v]}, False)
    try:
        return ({"type": "qcode", "data": HYDRA_KEYS_MAP[v]}, True)
    except KeyError:
        pass
    return (None, None)


def _key_next(buf, x, n):
    if buf[x] == 0x3C:
        i = buf.find(0x3E, x)
        if i > x and i + 1 <= n:
            v = buf[x + 1 : i].decode("UTF-8")
            if v in HYDRA_KEYS_CTRL_MAP:
                v = HYDRA_KEYS_CTRL_MAP[v]
            if v in HYDRA_KEYS_CTRL:
                return (True, i + 1, v.lower(), False)
            del v
        del i
    (c, k) = _key_translate(buf[x])
    return (False, x + 1, c, k)


def _key_send(s, c, k, m):
    b, e = "shift", [{"type": "key", "data": {"down": True, "key": c}}]
    if k and m:
        b = "caps_lock"
    if k:
        e.insert(
            0,
            {
                "type": "key",
                "data": {"down": True, "key": {"type": "qcode", "data": b}},
            },
        )
    s.sendall(
        dumps({"execute": "input-send-event", "arguments": {"events": e}}).encode(
            "UTF-8"
        )
    )
    del e
    s.sendall(b"\r\n")
    _command_response(_read_full(s, HYDRA_SOCK_BUF_SIZE))
    e = [{"type": "key", "data": {"down": False, "key": c}}]
    if k:
        e.append(
            {
                "type": "key",
                "data": {"down": False, "key": {"type": "qcode", "data": b}},
            }
        )
    s.sendall(
        dumps({"execute": "input-send-event", "arguments": {"events": e}}).encode(
            "UTF-8"
        )
    )
    del e, b
    s.sendall(b"\r\n")
    _command_response(_read_full(s, HYDRA_SOCK_BUF_SIZE))
