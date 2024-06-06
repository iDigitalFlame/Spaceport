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

# Module: System/HydraServer, User/user_alias
#   Provisions and monitors Virtual Machines on the system.

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
from os import chown, mkdir, chmod, remove
from lib.util.exec import stop, nulexec, run
from json import dumps, loads, JSONDecodeError
from socket import socket, AF_UNIX, SOCK_STREAM
from lib.shared.hydra import load_vm, get_devices
from os.path import isdir, isfile, exists, isabs, dirname
from lib.util.file import read, write, remove_file, expand, info
from lib.constants.files import HYDRA_CONFIG_DNS, HYDRA_CONFIG_SMB
from lib.constants.config import (
    NAME,
    HYDRA_DIR,
    HYDRA_USER,
    HYDRA_BRIDGE,
    HYDRA_RESERVE,
    HYDRA_EXEC_VM,
    HYDRA_FILE_DNS,
    HYDRA_EXEC_DNS,
    HYDRA_FILE_SMB,
    HYDRA_DIR_DHCP,
    HYDRA_EXEC_SMB,
    HYDRA_WAIT_TIME,
    HYDRA_PATH_MOUNTS,
    HYDRA_DIR_DEVICES,
    HYDRA_BRIDGE_NAME,
    HYDRA_RESERVE_SIZE,
    HYDRA_SOCK_BUF_SIZE,
    HYDRA_BRIDGE_NETWORK,
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
    HYDRA_USB_CLEAN,
    HYDRA_HIBERNATE,
    HYDRA_USB_DELETE,
    HYDRA_STATE_DONE,
    HYDRA_STATE_FAILED,
    HYDRA_STATE_RUNNING,
    HYDRA_STATE_STOPPED,
    HYDRA_STATE_WAITING,
    HYDRA_STATE_SLEEPING,
    HYDRA_USER_ADD_ALIAS,
    HYDRA_USER_DIRECTORY,
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
    if not isinstance(v, bytes) or len(v) == 0:
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


class VM(Storage):
    __slots__ = (
        "_usb",
        "_path",
        "_proc",
        "_wait",
        "_state",
        "_event",
        "_agent",
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
            i = info(path, False)
        except OSError as err:
            raise Error(f'cannot read "{path}": {err}')
        # NOTE(dij): We don't wrap these as they're the same as an Error
        #            and they already provide context.
        i.only(file=True).check(0o7137, uid, _hydra_user().pw_gid)
        del i
        Storage.__init__(self, path, load=True)
        if not nes(self.get("vm.uuid")):
            self.set("vm.uuid", str(uuid4()))
        if self.vmid is None:
            self.vmid = max(hash(self.get("vm.uuid")) % 512, 256)
        elif not isinstance(self.vmid, int) or self.vmid <= 0:
            raise Error("vmid must be a positive non-zero number")
        self._usb = dict()
        self._path = f"{HYDRA_DIR}/{self.vmid}"
        self._proc = None
        self._wait = 0
        self._state = HYDRA_STATE_STOPPED
        self._event = None
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
        else:
            s = "stopped"
        return {
            "pid": self._proc.pid if self._running() else None,
            "usb": self._usb,
            "vmid": self.vmid,
            "file": self.path(),
            "guest": self._agent,
            "status": s,
        }

    def _running(self):
        return self._proc is not None and self._proc.poll() is None

    def _ip(self, server):
        try:
            r = self._cmd(server, "guest-network-get-interfaces", ga=True)
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
        s = self._status()
        try:
            self._cmd(server, "guest-ping", ga=True)
        except Exception as err:
            server.warning(f"[m/hydra/VM({self.vmid})]: QEMU-GA ping failed!", err)
            s["ping"] = False
        else:
            s["ping"] = True
        return s

    def _hibernate(self, server):
        if self._state == HYDRA_STATE_STOPPED:
            return
        if self._state == HYDRA_STATE_WAITING:
            raise Error("cannot hibernate while waiting")
        if self._state != HYDRA_STATE_RUNNING:
            raise Error("not able to hibernate")
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

    def _sleep(self, server, sleep):
        if sleep and self._state == HYDRA_STATE_SLEEPING:
            raise Error("already sleeping")
        if not sleep and self._state != HYDRA_STATE_SLEEPING:
            raise Error("not currently sleeping")
        if self._state != HYDRA_STATE_RUNNING and self._state != HYDRA_STATE_SLEEPING:
            raise Error("not able to sleep")
        if sleep:
            server.debug(f"[m/hydra/VM({self.vmid})]: Entering sleep")
            self._proc.send_signal(SIGSTOP)
            self._state = HYDRA_STATE_SLEEPING
            return
        server.debug(f"[m/hydra/VM({self.vmid})]: Resuming from sleep")
        self._proc.send_signal(SIGCONT)
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
            server.notify(
                "Hydra VM Status",
                f"VM({self.vmid}) failed to start!",
                "virt-viewer",
            )
            return
        try:
            chmod(f"{self._path}.vnc", 0o0762, follow_symlinks=False)
            chmod(f"{self._path}.spice", 0o0762, follow_symlinks=False)
        except OSError:
            pass
        else:
            self._state = HYDRA_STATE_RUNNING
            server.debug(
                f"[m/hydra/VM({self.vmid})]: Socket became active, bootstrap complete!"
            )
            server.notify("Hydra VM Status", f"VM({self.vmid}) started!", "virt-viewer")

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

    def _build(self, server, manager, uid):
        # NOTE(dij): Do stuff that requires a bunch of checking first.
        x = self._build_restriced(server, manager, uid)
        # NOTE(dij): If the above passes, we should be good!
        b, t = self.get("dev.bus"), self.get("vm.type", "q35")
        if not nes(b):
            if nes(t) and "q35" in t:
                b = self.set("dev.bus", "pcie")
            else:
                b = self.set("dev.bus", "pci")
        if self.get("bios.version", 1) == 0:
            if self.get("bios.uefi", False):
                s = "type=0,uefi=on"
            else:
                s = "type=0"
        else:
            s = f'type={self.get("bios.version", 1)}'
        o, c = self.get("cpu.options", list()), self.get("cpu.type", "host")
        i = c == "host"
        if x.intel and self.get("cpu.auto_options", True):
            c = (
                f"{c},kvm=on,migratable=no,pdpe1gb,+kvm_pv_unhalt,+kvm_pv_eoi,+kvmclock,hv_relaxed,hv_passthrough,"
                "hv_frequencies,hv_synic,hv_reenlightenment,hv_vpindex,hv_spinlocks=0x1FFF,hv_vapic,hv_time,hv_stimer"
            )
        if i:
            c = f"{c},l3-cache=on"
        del i
        try:
            if isinstance(o, list) and len(o) > 0:
                c = f'{c},{",".join(o)}'
        except TypeError:
            raise Error('"cpu.options" list can only contain string values')
        # NOTE(dij): These two lines /could/ fail just in case, luckily we haven't
        #            done /much/ yet.
        d = self._build_drives(server, uid, x.user, b, t)
        a = self._build_adapters(server, b)
        n = self.get("cpu.sockets", 1)
        r = [
            x.bin,
            "-runas",
            HYDRA_USER,
            "-smbios",
            s,
            "-enable-kvm",
            "-nographic",
            "-no-user-config",
            "-nodefaults",
            "-boot",
            "order=cdn,menu=off,splash-time=0",
            "-rtc",
            "base=localtime,clock=host",
            "-machine",
            f'type={t},mem-merge=on,dump-guest-core=off,nvdimm=off,{"hpet=off,vmport=on," if x.intel else ""}'
            f'hmat=off,suppress-vmdesc=on,accel={self.get("vm.accel", "kvm")}',
            "-m",
            f"size={x.memory}",
            "-cpu",
            c,
            "-smp",
            f'{n},sockets={n},cores={self.get("cpu.cores", 1)},maxcpus={n}',
            "-uuid",
            self.get("vm.uuid"),
            "-name",
            f'"{self.get("vm.name", f"hydra-vm-{self.vmid}")}",debug-threads=off',
            "-pidfile",
            f"{self._path}.pid",
            "-display",
            f"vnc=unix:{self._path}.vnc,connections=512,lock-key-sync=on,"
            "password=off,power-control=on,share=ignore",
            "-qmp",
            f"unix:{self._path}.sock,server=on,wait=off",
            "-chardev",
            f"socket,id=qga0,path={self._path}.qga,server=on,wait=off",
            "-device",
            f"virtio-serial,id=qga0,bus={b}.0,addr=0x9",
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
        ]
        if x.reserve is not None:
            r += ["-mem-path", x.reserve, "-mem-prealloc"]
        if x.bios is not None:
            r += ["-bios", x.bios]
        if x.tpm is not None:
            r += ["-tpmdev", f"passthrough,id=tpm0,path={x.tpm}"]
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
        del x, s, t, o, c, n, v
        s = self.get("dev.osk")
        if nes(s):
            # NOTE(dij): Support MacOS with an OSK. This allows MacOS to not need
            #            to use the "extra" tag.
            r += ["-device", f"isa-applesmc,osk={s}"]
        g = self.get("dev.display", "virtio")
        if nes(g):
            r += ["-vga", g]
        else:
            r += ["-vga", "std"]
        del g, s
        if self.get("dev.sound", True):
            r += ["-device", f"intel-hda,id=sound1,bus={b}.0,addr=0x0b"]
        i = self.get("dev.input", "virtio")
        if i == "tablet":
            r += ["-device", "usb-tablet,id=tablet0,bus=usb-bus2.0,port=1"]
        elif i == "mouse":
            r += [
                "-device",
                f"virtio-mouse-pci,id=tablet0,bus={b}.0,addr=0x0a",
            ]
        elif i == "usb":
            r += [
                "-device",
                "usb-mouse,id=tablet0,bus=usb-bus2.0,port=1",
                "-device",
                "usb-kbd,id=tablet1,bus=usb-bus2.0,port=2",
            ]
        else:
            if i != "virtio":
                self.set("dev.input", "virtio")
            r += [
                "-device",
                f"virtio-tablet-pci,id=tablet0,bus={b}.0,addr=0x0a",
            ]
        del i
        if self.get("vm.spice", True):
            # NOTE(dij): We're adding the lines to add USB redirect support
            #            via SPICE, but Hydra won't know about the added devices
            #            it shouldn't be an issue, but documenting it incase
            #            it does.
            r += [
                "-spice",
                f"unix=on,addr={self._path}.spice,disable-ticketing=on,playback-compression=off,image-compression=off",
                "-chardev",
                "spicevmc,id=spicechannel0,name=vdagent",
                "-device",
                "virtserialport,chardev=spicechannel0,name=com.redhat.spice.0",
                "-device",
                "nec-usb-xhci,id=usb",
                "-chardev",
                "spicevmc,name=usbredir,id=usbredirchardev1",
                "-device",
                "usb-redir,chardev=usbredirchardev1,id=usbredirdev1",
                "-chardev",
                "spicevmc,name=usbredir,id=usbredirchardev2",
                "-device",
                "usb-redir,chardev=usbredirchardev2,id=usbredirdev2",
                "-chardev",
                "spicevmc,name=usbredir,id=usbredirchardev3",
                "-device",
                "usb-redir,chardev=usbredirchardev3,id=usbredirdev3",
            ]
        r += a + d
        del a, d, b
        if self.get("vm.debug", False):
            server.error(
                f'[m/hydra/VM({self.vmid})]: Runtime command dump: [{" ".join(r)}]'
            )
        return r

    def _start(self, server, manager, uid):
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
        x = self._build(server, manager, uid)
        if nes(self.path()):
            self.save(perms=0o640)
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
            self._proc = run(x, out=self.get("vm.debug", False))
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
        try:
            chmod(f"{self._path}.vnc", 0o0762, follow_symlinks=False)
            chmod(f"{self._path}.spice", 0o0762, follow_symlinks=False)
        except OSError:
            server.info(
                f"[m/hydra/VM({self.vmid})]: Started VM with PID {self._proc.pid}, but waiting for sockets!"
            )
            self._state = HYDRA_STATE_WAITING
        else:
            self._state = HYDRA_STATE_RUNNING
            server.info(
                f"[m/hydra/VM({self.vmid})]: Started VM with PID {self._proc.pid}!"
            )
            server.notify("Hydra VM Status", f"VM({self.vmid}) started!", "virt-viewer")
        try:
            # NOTE(dij): Last chance effort, as some get caught in this quasi-state.
            chmod(f"{self._path}.vnc", 0o0762, follow_symlinks=False)
            chmod(f"{self._path}.spice", 0o0762, follow_symlinks=False)
        except OSError:
            pass
        return self._proc.pid

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
            #            Can only be a file owned by the calling user that has 0o0640
            #            permissions.
            info(f, False, hide=True).check(0o7137, uid, hide=True).only(file=True)
        else:
            # NOTE(dij): Set to None to remove anything else.
            f = None
        t = self.get("dev.tpm")
        if nes(t):
            # NOTE(dij): Security Check
            #            Can only be a TPM chardev device that is not owned by
            #            root. The calling user must by in the group owned by the
            #            owner (usually "tss"). The device must have 0o0660 permissions.
            i = (
                info(t, False, hide=True)
                .check(0o7117, req=0o0660, hide=True)
                .only(char=True)
            )
            if i.uid != uid:
                raise Error(f'character device "{f}" cannot have a non-system owner')
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
            del v, g, i
        else:
            # NOTE(dij): Set to None to remove anything else.
            t = None
        k = expand(self.get("dev.kernel"))
        if nes(k):
            # NOTE(dij): Security Check
            #            Can only be a file owned by the calling user that has 0o0640
            #            permissions.
            info(k, False, hide=True).check(0o7137, uid, hide=True).only(file=True)
        else:
            # NOTE(dij): Set to None to remove anything else.
            k = None
        d = expand(self.get("dev.initrd"))
        if nes(d):
            # NOTE(dij): Security Check
            #            Can only be a file owned by the calling user that has 0o0640
            #            permissions.
            info(d, False, hide=True).check(0o7137, uid, hide=True).only(file=True)
        else:
            # NOTE(dij): Set to None to remove anything else.
            d = None
        o = expand(self.get("dev.devicetree"))
        if nes(o):
            # NOTE(dij): Security Check
            #            Can only be a file owned by the calling user that has 0o0640
            #            permissions.
            info(o, False, hide=True).check(0o7137, uid, hide=True).only(file=True)
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
        return Restricted(x, e, n, r, f, t, k, d, o, u.pw_name, x.endswith("-x86_64"))

    def _build_drives(self, server, uid, user, bus, machine):
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
            #            If the target is a file and is owned by the user
            #            it must have the Hydra group and the permissions of
            #            0o660. Unless the "readonly" value is True, in which
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
                    v.check(0o7133, req=0o0640)
                elif v.uid == uid:
                    if d.get("readonly", False):
                        v.check(0o7133, req=0o0440)
                    else:
                        v.check(0o7117, gid=_hydra_user().pw_gid, req=0o0660)
                else:
                    v.check(0o7133, req=0o0644, hide=True)
                    server.debug(
                        f'[m/hydra/VM({self.vmid})]: Mounting drive "{n}" target "{p}" as read only as the user '
                        f'does not have write permissions to "{p}".'
                    )
                    d["readonly"] = True
            if v.isblockdev:
                if v.uid != 0:
                    raise PermissionError(f'block device "{p}" must be owned by root')
                v.check(0o7117, req=0o0660, hide=True)
                try:
                    g = getgrgid(v.gid)
                except KeyError:
                    raise PermissionError(f'cannot find group "{v.gid}" for "{p}"')
                if user not in g.gr_mem:
                    server.debug(
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
            del p, v
            v = d.get("index")
            if isinstance(v, int):
                if v < 0 or v in b:
                    server.warning(
                        f'[m/hydra/VM({self.vmid})]: Removing drive "{n}" "index" value as its invalid!'
                    )
                    del d["index"]
                    v = max(b) + 1
                    d["index"] = v
                    b.append(v)
                else:
                    b.append(v)
            else:
                v = max(b) + 1
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
                d["format"] = "raw"
            w[n] = d
            del d
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
                s += ",aio=threads"
            elif d["format"] == "raw" and d["type"] == "virtio":
                s += ",aio=native,cache.direct=on"
            else:
                s += ",aio=threads,cache=writeback"
            # NOTE(dij): CDs and ISOs are always read only.
            if d.get("readonly", False) or d["type"] == "cd" or d["type"] == "iso":
                s += ",readonly=on"
            if d.get("discard", False):
                if d["type"] == "scsi":
                    s += ",discard=on"
                else:
                    s += ",discard=unmap"
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
            return self._cmd(server, "guest-shutdown", ga=True)
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
        if self._output is None and self.get("vm.debug", False):
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
            if nes(r):
                server.error(f"[m/hydra/VM({self.vmid})]: Process output ({r}).")
        else:
            r = None
        if self._output is None:
            self._output = (e, r)
        server.info(f"[m/hydra/VM({self.vmid})]: Stopping and cleaning up..")
        stop(self._proc)
        if self._proc is not None:
            try:
                self._proc.wait(0.5)
            except Exception:
                pass
        self._proc = None
        self._close_adapters(server)
        self._event = cancel_nul(server, self._event)
        self._usb_clean(server, manager)
        remove_file(f"{self._path}.pid")
        remove_file(f"{self._path}.vnc")
        remove_file(f"{self._path}.sock")
        try:
            if self.get("memory.reserve", True):
                manager.pages(server, self.vmid, None, True)
        except Error as err:
            server.warning(
                f"HYDRA: VM({self.vmid}) Error removing reserved memory!", err
            )
        self._state = HYDRA_STATE_STOPPED

    def _cmd(self, server, command, args=None, ga=False, timeout=1):
        if not self._running():
            # NOTE(dij): I don't see this path being called, but I'm
            #            leaving this logic here to prevent any weird
            #            shit happening.
            return
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
                r = _command_response(s.recv(HYDRA_SOCK_BUF_SIZE))
                if r is None:
                    raise Error("invalid hello response")
                server.debug(f'[m/hydra/VM({self.vmid})]: Hello response "{r}".')
                del r
            # NOTE(dij): Now send our command
            s.sendall(p)
            s.sendall(b"\r\n")
            r = _command_response(s.recv(HYDRA_SOCK_BUF_SIZE))
            server.debug(
                f'[m/hydra/VM({self.vmid})]: Command "{command}" response "{r}".'
            )
        finally:
            s.close()
            del s, f, p
        if ga and not self._agent:
            # NOTE(dij): If we received a response from the Guest Agent, flag it
            #            so we know to use it again.
            self._agent = True
        return r

    def _usb_add(self, server, manager, vendor, product, slow=False):
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
        n = 1 if len(self._usb) == 0 else max(self._usb.keys()) + 1
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
                    "vendorid": f"0x{vendor}",
                    "productid": f"0x{product}",
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
            "usb-creator",
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
                raise Error(f'device ID "{i}" is not connected')
            n = f"{i}"
            for k, v in self._usb.items():
                if v == i:
                    n = k
                    break
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


class HydraServer(object):
    __slots__ = ("_vms", "_dns", "_usb", "_pages", "_running")

    def __init__(self):
        self._vms = dict()
        self._dns = None
        self._usb = dict()
        self._pages = dict()
        self._running = False

    def start(self, server):
        if self._running:
            return
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
            chmod(HYDRA_DIR, 0o0755, follow_symlinks=False)
            chmod(HYDRA_DIR_DHCP, 0o0750, follow_symlinks=False)
            chown(HYDRA_DIR, 0, _hydra_user().pw_gid, follow_symlinks=False)
            chown(
                HYDRA_DIR_DHCP,
                _hydra_user().pw_uid,
                _hydra_user().pw_gid,
                follow_symlinks=False,
            )
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

    def thread(self, server):
        if not self._running:
            if len(self._vms) == 0:
                return
            server.debug("[m/hydra]: Starting Hydra for pending VMs..")
            self.start(server)
            if self._running:
                return
            self._vms.clear()
            return server.error(
                "[m/hydra]: Hydra startup failed, clearing pending VMs!"
            )
        if len(self._vms) == 0:
            server.debug("[m/hydra]: Shutting down Hydra for inactivity.")
            return self.stop(server, False)
        for v, x in list(self._vms.items()):
            x._thread(server, self)
            if x._state < HYDRA_STATE_STOPPED:
                continue
            server.debug(f"[m/hydra/VM({v})]: Removing shutdown VM.")
            server.notify(
                "Hydra VM Status", f"VM({v}) has shutdown{x._msg()}", "virt-viewer"
            )
            x._stop(server, self, True)
            del self._vms[v]

    def stop(self, server, force):
        if self._running:
            server.debug("[m/hydra]: Stopping and releasing resources..")
        server.debug("[m/hydra]: Stopping all active VMs..")
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

    def hook(self, server, message):
        if message.header() == HOOK_SHUTDOWN:
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
                    x._start(server, self, message.uid())
                return x._status()
            try:
                self.start(server)
                x._start(server, self, message.uid())
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
        if message.type == HYDRA_STOP:
            try:
                x._stop(server, self, message.force, message.get("timeout", 90))
            except Error as err:
                server.error(f"[m/hydra/VM({x.vmid})]: Cannot stop the VM!", err)
                return as_error(f"cannot stop VM {x.vmid}: {err}")
            return x._status()
        if message.type == HYDRA_GA_IP:
            return x._ip(server)
        if message.type == HYDRA_GA_PING:
            return x._ping(server)
        if message.type == HYDRA_TAP:
            try:
                x._stop(server, self, False, tap=True)
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
