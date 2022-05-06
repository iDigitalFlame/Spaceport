#!/usr/bin/false
# Module: Hydra (System, User)
#
# Manages, Provisions and Monitors Virtual Machines on the system.
# Requires: NGINX, Websockify, Samba, DnsMasq
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

from uuid import uuid4
from pwd import getpwnam
from shutil import rmtree
from random import randint
from sched import scheduler
from time import time, sleep
from threading import Thread
from ipaddress import IPv4Network
from signal import SIGCONT, SIGSTOP
from lib.structs.storage import Storage
from json import dumps, loads, JSONDecodeError
from socket import socket, AF_UNIX, SOCK_STREAM
from lib.structs.message import Message, as_error
from os import mkdir, listdir, environ, getcwd, chmod, stat
from subprocess import Popen, DEVNULL, PIPE, SubprocessError
from lib.util import read, write, stop, run, remove_file, read_json
from stat import S_IXUSR, S_ISVTX, S_ISUID, S_IXGRP, S_IXOTH, S_IWGRP, S_IWOTH
from os.path import (
    isdir,
    isfile,
    exists,
    basename,
    isabs,
    dirname,
    expanduser,
    expandvars,
    islink,
)
from lib.constants import (
    NAME,
    EMPTY,
    NEWLINE,
    HYDRA_TAP,
    HYDRA_UID,
    HOOK_HYDRA,
    HYDRA_WAKE,
    HYDRA_STOP,
    HYDRA_SLEEP,
    HYDRA_START,
    HOOK_DAEMON,
    HYDRA_GA_IP,
    HYDRA_BRIDGE,
    HYDRA_STATUS,
    HOOK_SUSPEND,
    HYDRA_TOKENS,
    HYDRA_RESERVE,
    HYDRA_USB_DIR,
    HYDRA_GA_PING,
    HYDRA_EXEC_VM,
    HYDRA_USB_ADD,
    HOOK_SHUTDOWN,
    HYDRA_DNS_FILE,
    HOOK_HIBERNATE,
    HYDRA_EXEC_DNS,
    HYDRA_SMB_FILE,
    HYDRA_DHCP_DIR,
    HYDRA_EXEC_SMB,
    HYDRA_USB_QUERY,
    HYDRA_USB_CLEAN,
    DIRECTORY_HYDRA,
    HYDRA_DNS_CONFIG,
    HYDRA_SMB_CONFIG,
    HYDRA_USB_DELETE,
    HYDRA_EXEC_NGINX,
    MESSAGE_TYPE_PRE,
    HYDRA_VM_CONFIGS,
    DIRECTORY_STATIC,
    HYDRA_USB_DEVICES,
    HOOK_NOTIFICATION,
    HYDRA_EXEC_TOKENS,
    HYDRA_BRIDGE_NAME,
    HYDRA_RESERVE_SIZE,
    HYDRA_COMMAND_START,
    HYDRA_USER_ADD_ALIAS,
    HYDRA_BRIDGE_NETWORK,
    HYDRA_USER_DIRECTORY,
    HYDRA_USER_DELETE_ALIAS,
)

HOOKS = {HOOK_HYDRA: "user_alias"}
HOOKS_SERVER = {
    HOOK_HYDRA: "HydraServer.hook",
    HOOK_SHUTDOWN: "HydraServer.stop",
    HOOK_DAEMON: "HydraServer.thread",
    HOOK_SUSPEND: "HydraServer.hibernate",
    HOOK_HIBERNATE: "HydraServer.hibernate",
}


def get_usb():
    try:
        u = listdir(HYDRA_USB_DIR)
    except OSError:
        return dict()
    e = dict()
    for d in u:
        v = f"{HYDRA_USB_DIR}/{d}/idVendor"
        p = f"{HYDRA_USB_DIR}/{d}/idProduct"
        if not isfile(v) or not isfile(p):
            continue
        try:
            cv = read(v).replace(NEWLINE, EMPTY)
            cp = read(p).replace(NEWLINE, EMPTY)
        except OSError:
            continue
        finally:
            del v
            del p
        n = "USB Device"
        nv = f"{HYDRA_USB_DIR}/{d}/manufacturer"
        np = f"{HYDRA_USB_DIR}/{d}/{cp}"
        try:
            if isfile(nv) and isfile(np):
                n = (
                    f"{read(np).replace(NEWLINE, EMPTY)} "
                    f"{read(nv).replace(NEWLINE, EMPTY)}"
                )
            elif isfile(nv):
                n = read(nv).replace(NEWLINE, EMPTY)
            elif isfile(np):
                n = read(np).replace(NEWLINE, EMPTY)
        except OSError:
            continue
        finally:
            del nv
            del np
        e[f"{cv}:{cp}"] = {
            "name": f"{n} ({cv}:{cp}",
            "vendor": cv,
            "product": cp,
            "path": f"{HYDRA_USB_DIR}/{d}",
        }
        del n
        del cv
        del cp
    del u
    return e


def _response(output):
    if not isinstance(output, bytes) or len(output) == 0:
        return None
    try:
        o = output.decode("UTF-8")
    except UnicodeDecodeError:
        return None
    if len(o) == 0:
        return None
    r = list()
    for e in o.split("\r\n"):
        if len(r) == 0:
            continue
        try:
            d = loads(e)
        except JSONDecodeError as err:
            raise OSError(f"Invalid server response: {err}")
        if not isinstance(d, dict):
            return None
        if "error" in d:
            raise OSError(d["error"])
        r.append(d)
        del d
    del o
    return r


def get_vm(path, config=None):
    if not isinstance(path, str) or len(path) == 0:
        return None
    if isinstance(config, str) and isfile(config):
        d = read_json(config)
        if isinstance(d, dict) and "hydra" in d:
            if "aliases" in d["hydra"]:
                n = path.lower()
                a = d["hydra"]["aliases"]
                if isinstance(a, dict) and n in a:
                    u = expandvars(expanduser(a[n]))
                    if exists(u):
                        path = u
                    del u
                del n
                del a
            if isinstance(path, str) and path == ".":
                path = getcwd()
            if path is None or not isabs(path) and "directory" in d["hydra"]:
                u = expandvars(expanduser(d["hydra"]["directory"]))
                if isinstance(u, str) and len(u) > 0:
                    p = f"{u}/{path}"
                    if exists(p):
                        path = p
                    del p
                del u
        del d
    if isinstance(path, str) and path == ".":
        path = getcwd()
    if isinstance(path, str) and isfile(path):
        return path
    if "HOME" in environ:
        if not isabs(path):
            path = expandvars(expanduser(path))
        if not isabs(path):
            c = f"{getcwd()}/{path}"
            if exists(c):
                path = c
            del c
    if not exists(path):
        return None
    if isdir(path):
        b = basename(path)
        for n in [b, f"{b}.conf", f"{b}.json", f"{b}.vmx"] + HYDRA_VM_CONFIGS:
            p = f"{path}/{n}"
            if isfile(p):
                return p
            del p
        del b
    if isfile(path):
        return path
    return None


def user_alias(server, message):
    if message.type == HYDRA_USER_DIRECTORY:
        d = message.directory
        if not isinstance(d, str):
            d = EMPTY
        server.debug(f'Updating Hydra VM User Directory to "{d}".')
        server.set_config("hydra.directory", d, True)
        del d
        return
    n = message.name
    a = server.get_config("hydra.aliases", dict(), True)
    if not isinstance(n, str) or len(n) == 0 or message.vmid is None:
        return
    if message.type == HYDRA_USER_ADD_ALIAS:
        if not isinstance(message.path, str) or len(message.path) == 0:
            return
        a[n.lower()] = message.path
        server.debug(f'Added user alias "{n}" to Hydra VM "{message.vmid}".')
    elif message.type == HYDRA_USER_DELETE_ALIAS:
        del a[n]
        server.debug(f'Removed user alias "{n}" from Hydra VM "{a[n]}".')
    else:
        return
    server.set_config("hydra.aliases", a, True)
    del n
    del a


def _reserve(server, vmid, memory, remove):
    if not isinstance(memory, int):
        try:
            memory = int(memory)
        except ValueError as err:
            raise HydraError(f"Unable to parse memory size: {err}")
    if memory <= 0:
        return
    b = int(memory / HYDRA_RESERVE_SIZE)
    if b * HYDRA_RESERVE_SIZE < memory:
        b += 1
    try:
        p = int(read(HYDRA_RESERVE).replace(NEWLINE, EMPTY), 10)
    except (OSError, ValueError) as err:
        raise HydraError(f"Error reserving memory: {err}")
    if not remove:
        server.debug(f"HYDRA: VM({vmid}) Current page size {p}, adding {b} blocks..")
        p += b
    else:
        server.debug(f"HYDRA: VM({vmid}) Current page size {p}, removing {b} blocks..")
        p -= b
    if p < 0:
        p == 0
    try:
        write(HYDRA_RESERVE, f"{p}\n")
    except OSError as err:
        raise HydraError(f"Error reserving memory: {err}")
    del p
    if not remove:
        server.debug(f"HYDRA: VM({vmid}) Reserved {b} blocks of memory.")
    else:
        server.debug(f"HYDRA: VM({vmid}) Removed {b} resevered blocks of memory.")
        remove_file(f"/dev/hugepages/{vmid}.ram")
    del b


class HydraVM(Storage):
    def __init__(self, vmid=None, path=None):
        if not isinstance(path, str) or not isfile(path) or path.startswith("/dev"):
            raise HydraError(f'Invalid path "{path}"')
        Storage.__init__(self, path=path)
        self._exit = 0
        self._ready = 0
        self._ga = False
        self._usb = None
        self._event = None
        self._output = None
        self._process = None
        self._sleeping = False
        self._interfaces = None
        if vmid is not None:
            self.vmid = vmid
        elif self.get("vmid") is None:
            raise HydraError("VMID is missing")
        if not isinstance(self.vmid, int) or self.vmid <= 0:
            raise HydraError("VMID is invalid")
        self._path = f"{DIRECTORY_HYDRA}/{str(self.vmid)}"

    def _running(self):
        return self._process is not None and self._process.poll() is None

    def _stopped(self):
        return self._ready == 3 and self._process is None

    def _ip(self, server):
        d = self._ga_command(server, "guest-network-get-interfaces")
        if not isinstance(d, list) or len(d) == 0:
            return self._status()
        i = list()
        for e in d:
            if "name" not in e or len(e["name"]) == 0:
                continue
            if "ip-addresses" not in e or len(e["ip-addresses"]) == 0:
                continue
            for v in e["ip-addresses"]:
                if not isinstance(v, dict):
                    continue
                if "ip-address-type" not in v or v["ip-address-type"] != "ipv4":
                    continue
                if "ip-address" not in v or len(v["ip-address"]) == 0:
                    continue
                if v["ip-address"].startswith("127."):
                    continue
                i.append(v["ip-address"])
        del d
        s = self._status()
        s["ips"] = i
        del i
        return s

    def _ping(self, server):
        s = self._status()
        try:
            self._ga_command(server, "guest-ping")
        except Exception as err:
            server.warning(f"HYDRA: VM({self.vmid}) QEMU-GA ping failed!", err=err)
            s["ping"] = False
        else:
            s["ping"] = True
        return s

    def _status(self, usb=False):
        if self._event is not None:
            s = "stopping"
        elif self._running():
            if self._ready == 1:
                s = "waiting"
            elif self._sleeping:
                s = "sleeping"
            else:
                s = "running"
        else:
            s = "stopped"
        if usb:
            return {
                "pid": self._process.pid if self._running() else None,
                "usb": self._usb,
                "vmid": self.vmid,
                "path": self.get_file(),
                "guest": self._ga,
                "status": s,
            }
        return {
            "pid": self._process.pid if self._running() else None,
            "vmid": self.vmid,
            "path": self.get_file(),
            "guest": self._ga,
            "status": s,
        }

    def _network(self, server, bus):
        if not isinstance(self.get("network"), dict):
            server.debug(
                f"HYDRA: VM({self.vmid}) No valid Network Interfaces found, skipping!"
            )
            self.set("network", dict())
            return list()
        a = 20
        b = list()
        self._interfaces = list()
        for n, x in self.network.items():
            if not isinstance(x, dict):
                server.warning(
                    f'HYDRA: VM({self.vmid}) Network Interface "{n}" was invalid and skipped!'
                )
                continue
            if "type" not in x:
                x["type"] = "intel"
            if "bridge" in x:
                s = x["bridge"]
            else:
                s = HYDRA_BRIDGE
            if "device" in x:
                d = x["device"]
            else:
                d = f"{HYDRA_BRIDGE}s{self.vmid}n{len(self._interfaces)}"
            self._interfaces.append(("device" not in x, d, s))
            if "mac" not in x:
                x[
                    "mac"
                ] = f"2c:af:01:{randint(0, 255):02x}:{randint(0, 255):02x}:{randint(0, 255):02x}"
            if x["type"] == "intel":
                v = "e1000"
            elif x["type"] == "virtio":
                v = "virtio-net-pci"
            elif x["type"] == "vmware":
                v = "vmxnet3"
            else:
                v = x["type"]
            b += [
                "-netdev",
                f"type=tap,id={n},ifname={d},script=no,downscript=no,vhost=on",
                "-device",
                f'{v},mac={x["mac"]},netdev={n},bus={bus}.0,addr={hex(a)},id={n}-dev',
            ]
            a += 1
            del d
            del s
            del v
            self.network[n] = x
        del a
        return b

    def _sleep(self, server, sleep):
        if sleep and self._sleeping:
            raise HydraError("VM is currently sleeping")
        if not sleep and not self._sleeping:
            raise HydraError("VM is not currently sleeping")
        if sleep:
            try:
                server.debug(f"HYDRA: VM({self.vmid}) Attempting to sleep VM..")
                self._process.send_signal(SIGSTOP)
            except OSError as err:
                raise HydraError(f"Could not send sleep signal: {err}")
            self._sleeping = True
            return server.debug(f"HYDRA: VM({self.vmid}) Was put to sleep!")
        try:
            server.debug(f"HYDRA: VM({self.vmid}) Attempting to wake VM..")
            self._process.send_signal(SIGCONT)
        except OSError as err:
            raise HydraError(f"Could not send wake signal: {err}")
        self._sleeping = False
        server.debug(f"HYDRA: VM({self.vmid}) Was woken up!")

    def _start(self, manager, server):
        if self._running():
            return self._process.pid
        self._ready = 0
        m = self.get("memory.size", 1024)
        if not isinstance(m, int) and m <= 0:
            raise HydraError("Invalid memory size")
        del m
        x = self.get("vm.binary")
        if x is not None:
            u = server.get_config("hydra.unsafe", False, True)
            if not u:
                raise HydraError(
                    f'Cannot use binary "{x}" when "hydra.unsafe" is False'
                )
            del u
            a = server.get_config("hydra.allowed", None)
            if not isinstance(a, list) or x not in a:
                raise HydraError(f'Binary "{x}" is not in "hydra.allowed"')
            del a
        if not isinstance(x, str) or len(x) == 0 or not exists(x):
            x = HYDRA_EXEC_VM
        if islink(x):
            raise HydraError(f'Binary "{x}" cannot be a symlink')
        try:
            s = stat(x, follow_symlinks=False)
        except OSError as err:
            raise HydraError(f'Binary "{x}" could not be verified by stat: {err}')
        if s.st_uid != 0 or s.st_gid != 0:
            raise HydraError(
                f'Binary "{x}" owner and/or group is not root (Binary must have root UID/GID!)'
            )
        if s.st_mode & (S_IWGRP | S_IWOTH) > 0:
            raise HydraError(
                f'Binary "{x}" cannot be writable by Group or Other (chmod 755 it!)'
            )
        if s.st_mode & (S_IXUSR | S_IXGRP) == 0:
            raise HydraError(
                f'Binary "{x}" is not executable by User or Group (chmod 755 it!)'
            )
        del s
        if self.get("bios.version", 1) == 0:
            if self.get("bios.uefi", False):
                v = "type=0,uefi=on"
            else:
                v = "type=0"
        else:
            v = f'type={self.get("bios.version", 1)}'
        c = [
            x,
            "-runas",
            HYDRA_UID,
            "-smbios",
            v,
            "-enable-kvm",
            "-no-hpet",
            # "-k",
            # "en-us",
            "-nographic",
            "-no-user-config",
            "-nodefaults",
            "-boot",
            "order=cdn,menu=off,splash-time=0",
            "-rtc",
            "base=localtime,clock=host",
        ]
        del v
        del x
        f = self.get("bios.file")
        if isinstance(f, str) and isfile(f):
            c += ["-bios", f]
        del f
        c.append("-cpu")
        o = self.get("cpu.options", list())
        if isinstance(o, list) and len(o) > 0:
            c.append(
                f'{self.get("cpu.type", "host")},kvm=on,+kvm_pv_unhalt,+kvm_pv_eoi,hv_relaxed,'
                f'hv_spinlocks=0x1fff,hv_vapic,hv_time,{",".join(o)}'
            )
        else:
            c.append(
                f'{self.get("cpu.type", "host")},kvm=on,+kvm_pv_unhalt,+kvm_pv_eoi,hv_relaxed,'
                "hv_spinlocks=0x1fff,hv_vapic,hv_time"
            )

            # enforce,hv_ipi,hv_relaxed,hv_reset,hv_runtime,hv_spinlocks=0x1fff,hv_stimer,hv_synic,
            # hv_time,hv_vapic,hv_vpindex,+kvm_pv_eoi,+kvm_pv_unhalt
        del o
        y = self.get("dev.bus")
        v = self.get("vm.type", "q35")
        if not isinstance(y, str) or len(y) == 0:
            if isinstance(v, str) and "q35" in v:
                y = self.set("dev.bus", "pcie")
            else:
                y = self.set("dev.bus", "pci")
        e = self.get("vm.extra")
        if isinstance(e, list) and len(e) > 0:
            u = server.get_config("hydra.unsafe", False)
            if not u:
                raise HydraError('Cannot use "vm.extra" when "hydra.unsafe" is False')
            del u
            server.info(
                f'HYDRA: VM({self.vmid}) Adding "vm.extra" to build = [{" ".join(e)}].'
            )
            c += e
        del e
        n = self.get("cpu.sockets", 1)
        c += [
            "-machine",
            f"type={v},mem-merge=on,dump-guest-core=off,vmport=on,nvdimm=off,"
            f'hmat=off,suppress-vmdesc=on,accel={self.get("vm.accel", "kvm")}',
            "-smp",
            f"{n},sockets={n},cores=1,maxcpus={n}",
            "-uuid",
            self.get("vm.uuid", str(uuid4())),
            "-m",
            f'size={self.get("memory.size", 1024)}',
            "-name",
            f'"{self.get("vm.name", f"hydra-vm-{self.vmid}")}",debug-threads=off',
            "-pidfile",
            f"{self._path}.pid",
            "-display",
            f"vnc=unix:{self._path}.vnc,connections=512,lock-key-sync=on,"
            "password=off,power-control=on,share=ignore",
            "-qmp",
            # f"unix:{self._path}.sock,server,nowait",
            f"unix:{self._path}.sock,server=on,wait=off",
            "-chardev",
            f"socket,id=qga0,path={self._path}.qga,server=on,wait=off",
            "-device",
            f"virtio-serial,id=qga0,bus={y}.0,addr=0x9",
            "-device",
            "virtserialport,chardev=qga0,name=org.qemu.guest_agent.0",
            "-object",
            "iothread,id=iothread0",
            "-device",
            f"virtio-balloon-pci,id=ballon0,bus={y}.0,addr=0x0c",
            "-device",
            f"virtio-keyboard-pci,id=keyboard0,bus={y}.0,addr=0x11",
            "-device",
            f"qemu-xhci,multifunction=on,id=usb-bus1,bus={y}.0,addr=0x0d",
            "-device",
            f"piix3-usb-uhci,multifunction=on,id=usb-bus0,bus={y}.0,addr=0x0e",
            "-device",
            f"pci-bridge,id=pci-bridge1,chassis_nr=1,bus={y}.0,addr=0x0f",
            "-device",
            f"pci-bridge,id=pci-bridge2,chassis_nr=2,bus={y}.0,addr=0x10",
        ]
        del n
        if self.get("vm.spice", True):
            c += [
                "-spice",
                f"unix=on,addr={self._path}.spice,disable-ticketing=on",
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
            # NOTE(dij): We're adding the above lines to add USB redirect support
            #            via SPICE, but Hydra won't know about the added devices
            #            it shouldn't be an issue, but documenting it incase
            #            it does.
        if isinstance(v, str) and "q35" in v and self.get("dev.iommu", True):
            c += ["-device", "intel-iommu"]
        g = self.get("dev.display", "virtio")
        if isinstance(g, str) and len(g) > 0:
            c += ["-vga", g]
        else:
            c += ["-vga", "std"]
        del g
        if self.get("dev.sound", True):
            c += [
                "-device",
                f"intel-hda,id=sound1,bus={y}.0,addr=0x0b",
                "-device",
                "hda-duplex,id=sound2",
            ]
        i = self.get("dev.input")
        if i == "tablet":
            c += ["-device", "usb-tablet,id=tablet0,bus=usb-bus1.0,port=1"]
        elif i == "mouse":
            c += [
                "-device",
                f"virtio-mouse-pci,id=tablet0,bus={y}.0,addr=0x0a",
            ]
        elif i == "usb":
            c += [
                "-device",
                "usb-mouse,id=tablet0,bus=usb-bus0.0,port=1",
                "-device",
                "usb-kbd,id=tablet1,bus=usb-bus0.0,port=2",
            ]
        else:
            if i != "virtio":
                self.set("dev.input", "standard")
            c += [
                "-device",
                f"virtio-tablet-pci,id=tablet0,bus={y}.0,addr=0x0a",
            ]
        del i
        t = self.get("dev.tpm")
        if isinstance(t, str) and len(t) > 0:
            c += ["-tpmdev", f"passthrough,id=tpm0,path={t}"]
        del t
        c += self._drives(server, y, v)
        c += self._network(server, y)
        del v
        del y
        server.debug(f"HYDRA: VM({self.vmid}) Built VM string, starting process..")
        if self.get("memory.reserve", True):
            c += ["-mem-path", f"/dev/hugepages/{self.vmid}.ram", "-mem-prealloc"]
            _reserve(server, self.vmid, self.get("memory.size", 1024), False)
        if self.get("vm.debug", False):
            server.error(f'HYDRA: VM({self.vmid}) Dump: [{" ".join(c)}]')
        if self.get_file() is not None:
            self.write()
            server.debug(f'HYDRA: VM({self.vmid}) Saved VM config "{self.get_file()}.')
        try:
            self._start_interfaces(server)
        except OSError:
            # NOTE(dij): Remove any stale interfaces and try one more
            #            time :fingers-crossed:
            #
            #            NEW: _start_interfaces now removes interfaces itself
            #                 if it fails during runtime, but still throws the
            #                 OSError.
            try:
                self._start_interfaces(server)
            except OSError as err:
                raise HydraError(f"Error creating interfaces: {err}")
        try:
            self._process = Popen(c, stdout=PIPE, stderr=PIPE)
        except (OSError, SubprocessError) as err:
            server.send(
                None,
                Message(
                    header=HOOK_NOTIFICATION,
                    payload={
                        "title": "Hydra VM Status",
                        "body": f"VM({self.vmid}) failed to start!",
                        "icon": "virt-viewer",
                    },
                ),
            )
            self._ready = 2
            self._stop(manager, server, True)
            raise HydraError(f"Failed to start: {err}")
        finally:
            del c
        server.send(
            None,
            Message(
                header=HOOK_NOTIFICATION,
                payload={
                    "title": "Hydra VM Status",
                    "body": f"VM({self.vmid}) started!",
                    "icon": "virt-viewer",
                },
            ),
        )
        if not self._running():
            server.warning(
                f"HYDRA: VM({self.vmid}) is taking longer to startup, passing to thread!"
            )
            HydraWaitThread(self, server).start()
            return 0
        self._ready = 1
        server.debug(f"HYDRA: VM({self.vmid}) Started, PID: {self._process.pid}!")
        return self._process.pid

    def _thread(self, manager, server):
        if self._ready == 1 and not self._running():
            server.warning(
                f"HYDRA: VM({self.vmid}) Process died before bootstrapping complete!"
            )
            return self._stop(manager, server, True, errors=False)
        if self._ready == 1:
            try:
                chmod(f"{self._path}.vnc", 0o762, follow_symlinks=False)
                chmod(f"{self._path}.spice", 0o762, follow_symlinks=False)
            except OSError:
                return
            server.debug(
                f"HYDRA: VM({self.vmid}) VNC socket became active, bootstrap complete!"
            )
            self._ready = 2
        elif self._ready == 2 and not self._running():
            server.debug(f"HYDRA: VM({self.vmid}) Natural shutdown, stopping instance.")
            self._stop(manager, server, True, errors=False)

    def _remove_usb(self, server, usb):
        if not isinstance(self._usb, dict) or usb not in self._usb:
            raise HydraError(f'Could not find USB ID "{usb}" connected to the VM')
        try:
            self._command(server, "device_del", {"id": f"usb-dev-{usb}"})
        except (HydraError, OSError) as err:
            raise HydraError(f'Remove USB failed "{self._usb[usb]}": {err}')
        server.debug(
            f'HYDRA: VM({self.vmid}) Removed USB device "{self._usb[usb]}" from the VM.'
        )
        server.send(
            None,
            Message(
                header=HOOK_NOTIFICATION,
                payload={
                    "title": "Hydra USB Device Removed",
                    "body": f'USB Device "{self._usb[usb]}" disconnected from VM({self.vmid}).',
                    "icon": "usb-creator",
                },
            ),
        )
        del self._usb[usb]

    def _stop_interfaces(self, server):
        if self._interfaces is None:
            return
        if not isinstance(self._interfaces, list) or len(self._interfaces) == 0:
            return
        server.debug(f"HYDRA: VM({self.vmid}) Removing interfaces..")
        for i in self._interfaces:
            run(["/usr/bin/ip", "link", "set", i[1], "nomaster"])
            run(["/usr/bin/ip", "link", "set", "dev", i[1], "down"])
            if i[0]:
                run(["/usr/bin/ip", "tuntap", "delete", "dev", i[1], "mode", "tap"])
            server.debug(f'HYDRA: VM({self.vmid}) Removed interface "{i[1]}".')
        server.debug(
            f"HYDRA: VM({self.vmid}) Removed {len(self._interfaces)} interfaces."
        )

    def _start_interfaces(self, server):
        if not isinstance(self._interfaces, list) or len(self._interfaces) == 0:
            return None
        server.debug(f"HYDRA: VM({self.vmid}) Creating interfaces..")
        try:
            for i in self._interfaces:
                if i[0]:
                    run(
                        [
                            "/usr/bin/ip",
                            "tuntap",
                            "add",
                            "dev",
                            i[1],
                            "mode",
                            "tap",
                            "user",
                            HYDRA_UID,
                        ]
                    )
                run(["/usr/bin/ip", "link", "set", i[1], "master", i[2]])
                run(["/usr/bin/ip", "link", "set", "dev", i[1], "up", "promisc", "on"])
                server.debug(f'HYDRA: VM({self.vmid}) Added interface "{i[1]}".')
        except OSError as err:
            try:
                self._stop_interfaces(server)
            except OSError:
                pass
            raise err
        server.debug(
            f"HYDRA: VM({self.vmid}) Created {len(self._interfaces)} interfaces."
        )

    def _drives(self, server, bus, type):
        if not isinstance(self.get("drives"), dict):
            server.debug(f"HYDRA: VM({self.vmid}) No valid drives found, skipping!")
            self.set("drives", dict())
            return list()
        o = 0
        d = dict()
        v = list()
        for n, x in self.drives.items():
            if not isinstance(x, dict):
                server.warning(
                    f'HYDRA: VM({self.vmid}) Drive "{n}" was invalid and skipped!'
                )
                continue
            if "file" not in x:
                server.warning(
                    f'HYDRA: VM({self.vmid}) Drive "{n}" does not contain a "file" value, skipping!'
                )
                continue
            f = x["file"]
            if not isabs(f):
                f = f"{dirname(self.get_file())}/{f}"
                if not isfile(f):
                    raise HydraError(f'Drive "{n}" file "{f}" does not exist')
                x["file"] = f
            elif not isfile(f):
                raise HydraError(f'Drive "{n}" file "{f}" does not exist')
            if islink(f):
                raise HydraError(f'Drive "{n}" file "{f}" cannot be a symlink')
            try:
                s = stat(f, follow_symlinks=False)
            except OSError as err:
                raise HydraError(f'Error reading drive "{n}" file "{f}": {err}')
            u = 0
            g = 0
            try:
                p = getpwnam(HYDRA_UID)
                u = p.pw_uid - 1
                g = p.pw_gid - 1
                del p
            except (OSError, ValueError) as err:
                server.warning(
                    f'HYDRA: Error getting password entry for "{HYDRA_UID}", falling back to "root"!',
                    err=err,
                )
            if (
                s.st_uid <= u
                or s.st_gid <= g
                or s.st_mode & (S_IXUSR | S_ISVTX | S_ISUID | S_IXGRP | S_IXOTH) > 0
            ):
                raise HydraError(f'Drive "{n}" file "{f}" has improper permissions')
            del u
            del g
            del f
            del s
            if "index" in x:
                i = x["index"]
                if i in v or not isinstance(i, int) or i < 0:
                    server.warning(
                        f'HYDRA: VM({self.vmid}) Removing invalid drive "{n}" index "{i}"'
                    )
                    del x["index"]
                else:
                    v.append(i)
                del i
            if "index" not in x:
                x["index"] = max(v) + 1
                v.append(x["index"])
            if "type" not in x:
                x["type"] = "ide"
                o += 1
            else:
                if x["type"] == "ide" or x["type"] == "cd" or x["type"] == "iso":
                    o += 1
            if o > 4:
                raise HydraError("There can only be a maximum of 4 IDE devices")
            if "format" not in x:
                x["format"] = "raw"
            d[n] = x
        del v
        o = 0
        u = 0
        b = list()
        j = False
        w = False
        for n, x in d.items():
            s = (
                f'id={n},file={x["file"]},format={x["format"]},index={x["index"]},'
                "if=none,detect-zeroes=unmap"
            )
            if not x.get("direct", True):
                s += ",aio=threads"
            elif x["format"] == "raw" and x["type"] == "virtio":
                s += ",aio=native,cache.direct=on"
            else:
                s += ",aio=threads,cache=writeback"
            if x.get("readonly", False):
                s += ",readonly=on"
            if x.get("discard", False):
                if x["type"] == "scsi":
                    s += ",discard=on"
                else:
                    s += ",discard=unmap"
            b += ["-drive", s]
            del s
            if x["type"] == "scsi":
                if not j:
                    j = True
                    b += [
                        "-device",
                        f"virtio-scsi-pci,id=scsi0,bus={bus}.0,addr=0x5,iothread=iothread0",
                    ]
                b += [
                    "-device",
                    f"scsi-hd,bus=scsi0.0,channel=0,scsi-id=0,lun={o},drive={n},id=scsi-{o},rotation_rate=1",
                ]
                o += 1
                self.drives[n] = x
                continue
            if x["type"] == "virtio":
                b += [
                    "-device",
                    f'virtio-blk-pci,id={n}-dev,drive={n},bus={bus}.0,bootindex={x["index"]}',
                ]
                self.drives[n] = x
                continue
            e = o
            t = "ide"
            if "q35" in type:
                e += 1
            else:
                e = o / 2
            if x["type"] == "sata":
                t = "sata"
                if not w:
                    u = 1
                    w = True
                    b += ["-device", "ich9-ahci,id=sata"]
                e = u
            b += [
                "-device",
                f'ide-{"cd" if x["type"] == "cd" or x["type"] == "iso" else "hd"},id={n}-dev,'
                f'drive={n},bus={t}.{e},bootindex={x["index"]}',
            ]
            del t
            del e
            if x["type"] == "sata":
                u += 1
            else:
                o += 1
            self.drives[n] = x
        del o
        del u
        del d
        del j
        del w
        return b

    def _command(self, server, command, args=None):
        if not self._running():
            # NOTE(dij): I don't see this path being called, but I'm
            #            leaving this logic here to prevent any weird
            #            shit happening.
            return
        if not isinstance(command, dict) and not isinstance(command, str):
            raise HydraError('"command" must be a Dict or String')
        server.debug(f'HYDRA: VM({self.vmid}) Sending command "{command}"..')
        s = socket(AF_UNIX, SOCK_STREAM)
        # NOTE(dij): There seems to be a bug in QMP that causes the socket
        #            to timeout sometimes when sleep/wake occurs. Note sure
        #            what directly causes it.
        #
        #            Just something to note with the timeout option that /should/
        #            have been here in the first place.
        s.settimeout(1)
        try:
            s.connect(f"{self._path}.sock")
            s.sendall(HYDRA_COMMAND_START)
            o = _response(s.recv(4096))
            if o is None:
                raise HydraError("Invalid server response")
            d = {"execute": command}
            if isinstance(args, dict):
                d["arguments"] = args
            e = bytes(dumps(d), "UTF-8")
            del d
            s.sendall(e)
            o = _response(s.recv(4096))
            if o is None:
                raise HydraError("Invalid server response")
            del o
            # NOTE(dij): QMP seems to have a high lag and needs to have the
            #            message sent multiple times for it to be received.
            s.sendall(e)
            s.sendall(e)
            o = _response(s.recv(4096))
            if o is None:
                raise HydraError("Invalid server response")
            del o
            del e
        finally:
            s.close()
            del s
        server.debug(f'HYDRA: VM({self.vmid}) Command "{command}" completed.')
        return True

    def _ga_command(self, server, command, args=None):
        if not isinstance(command, str) or len(command) == 0:
            command = "guest-ping"
        # NOTE(dij): Disabling the below code since we want
        #            to try all commands regardless of status.
        #
        # if command != "guest-ping" and not self._ga:
        #    server.debug(
        #        f'HYDRA: VM({self.vmid}) Refusing to run QEMU-GA command "{command}" when GA is not running!'
        #    )
        #    return None
        if not exists(f"{self._path}.qga"):
            raise HydraError(f'QEMU-GA socket "{self._path}.qga" is missing')
        server.debug(f'HYDRA: VM({self.vmid}) Sending QEMU-GA command "{command}"..')
        s = socket(AF_UNIX, SOCK_STREAM)
        s.settimeout(1)
        try:
            s.connect(f"{self._path}.qga")
            d = {"execute": command}
            if isinstance(args, dict):
                d["arguments"] = args
            e = bytes(dumps(d), "UTF-8")
            del d
            s.sendall(e)
            # NOTE(dij): Is there a payload for this larger than 4096?
            r = s.recv(4096)
            if not isinstance(r, bytes):
                raise HydraError("Invalid server response")
            try:
                v = loads(r.decode("UTF-8"))
            except (JSONDecodeError, UnicodeDecodeError):
                raise HydraError("Invalid server response")
        finally:
            s.close()
            del s
        if "error" in v:
            return HydraError(f'QEMU-GA Error: {v["error"]}')
        if not self._ga:
            self._ga = True
        server.debug(f'HYDRA: VM({self.vmid}) QEMU-GA Command "{command}" completed.')
        return v.get("return")

    def _add_usb(self, server, vendor, product, slow):
        d = f"{vendor}:{product}"
        if not isinstance(self._usb, dict):
            self._usb = dict()
        elif len(self._usb) > 0 and d in list(self._usb.values()):
            raise HydraError(
                f'USB device "{d}" is already mounted as "usb-dev-{self._usb[d]}"!'
            )
        if len(self._usb) == 0:
            i = 1
        else:
            i = max(self._usb.keys()) + 1
        run(["/usr/bin/chown", "-R", HYDRA_UID, HYDRA_USB_DEVICES])
        b = "usb-bus1.0"
        if isinstance(slow, bool) and slow:
            b = "usb-bus0.0"
        try:
            self._command(
                server,
                "device_add",
                {
                    "id": f"usb-dev-{id}",
                    "bus": b,
                    "driver": "usb-host",
                    "vendorid": f"0x{vendor}",
                    "productid": f"0x{product}",
                },
            )
        except HydraError as err:
            # NOTE(dij): Ignoring 'OSError' here as upper function
            #            catches it.
            raise HydraError(f'Could not add USB device "{d}": {err}')
        finally:
            del b
        server.debug(f'HYDRA: VM({self.vmid}) Added USB device "{d}" to the VM.')
        self._usb[i] = d
        server.send(
            None,
            Message(
                header=HOOK_NOTIFICATION,
                payload={
                    "title": "Hydra USB Device Connected",
                    "body": f'USB Device "{d}" connected to VM({self.vmid}).',
                    "icon": "usb-creator",
                },
            ),
        )
        del d
        return i

    def _stop(self, manager, server, force, timeout=90, errors=True, tap=False):
        if self._ready == 3:
            return
        if force is not None and not isinstance(force, bool):
            force = False
        if tap:
            try:
                if self._ga:
                    return self._command(server, "guest-shutdown")
                return self._command(server, "system_powerdown")
            except (HydraError, OSError) as err:
                raise HydraError(f"Error triggering shutdown: {err}")
        if (force is None or not force) and self._running():
            if self._event is not None:
                raise HydraError("Soft shutdown is already in progress")
            if not isinstance(timeout, int) or timeout < 0:
                raise HydraError('"timeout" must be a valid integer')
            if self._sleeping:
                self._sleep(server, False)
            server.debug(
                f"HYDRA: VM({self.vmid}) Shutting down, timeout {timeout} seconds.."
            )
            try:
                if self._ga:
                    self._command(server, "guest-shutdown")
                else:
                    self._command(server, "system_powerdown")
            except (HydraError, OSError) as err:
                raise HydraError(f"Error triggering shutdown: {err}")
            finally:
                self._event = manager.scheduler.enter(
                    timeout, 1, self._stop, argument=(manager, server, True)
                )
            return
        if self._running():
            stop(self._process, True)
            try:
                self._exit = self._process.wait(0.25)
            except SubprocessError as err:
                server.warning(f"HYDRA: VM({self.vmid}) Process wait failed!", err=err)
        if isinstance(self._exit, int) and self._exit > 0:
            server.warning(
                f"HYDRA: VM({self.vmid}) Exit status was non-zero ({self._exit})"
            )
        if (
            self._output is None
            and self._process is not None
            and (self.get("vm.debug") or self._exit != 0)
        ):
            try:
                o = self._process.stdout.read().decode("UTF-8").replace(NEWLINE, ";")
                self._output = (
                    self._process.stderr.read().decode("UTF-8").replace(NEWLINE, ";")
                )
                if isinstance(o, str) and len(o) > 0:
                    if self._output is None or len(self._output) == 0:
                        self._output = o
                    else:
                        self._output = o + ";" + self._output
                del o
            except (ValueError, IOError, UnicodeDecodeError, AttributeError):
                pass
            if len(self._output) > 0:
                server.error(
                    f"HYDRA: VM({self.vmid}) Process output dump:\n{self._output}\n"
                )
        server.debug(f"HYDRA: VM({self.vmid}) Stopping and cleaning up.")
        stop(self._process)
        if self._process is not None:
            try:
                self._process.wait(0.5)
            except SubprocessError:
                pass
        self._process = None
        try:
            self._stop_interfaces(server)
        except OSError as err:
            if errors:
                raise HydraError(f"Could not stop interfaces: {err}")
            server.warning(
                f"HYDRA: VM({self.vmid}) Error removing interfaces!", err=err
            )
        if isinstance(self._interfaces, list):
            self._interfaces.clear()
            self._interfaces = None
        if self._event is not None:
            try:
                manager.scheduler.cancel(self._event)
            except ValueError:
                pass
            self._event = None
        if isinstance(self._usb, dict):
            for d in self._usb.values():
                if d in manager.usbs:
                    del manager.usbs[d]
            self._usb.clear()
            self._usb = None
        try:
            if self.get("memory.reserve", True):
                _reserve(server, self.vmid, self.get("memory.size", 1024), True)
        except HydraError as err:
            if errors:
                raise err
            server.warning(
                f"HYDRA: VM({self.vmid}) Error removing reserved memory!", err=err
            )
        finally:
            remove_file(f"{self._path}.pid")
            remove_file(f"{self._path}.vnc")
            remove_file(f"{self._path}.sock")
            self._ready = 3


class HydraServer(object):
    def __init__(self):
        self.web = True
        self.vms = dict()
        self.usbs = dict()
        self.running = False
        self.dns_server = None
        self.web_server = None
        self.token_server = None
        self.scheduler = scheduler(timefunc=time, delayfunc=sleep)

    def start(self, server):
        if self.running:
            return
        if not exists(HYDRA_EXEC_VM):
            raise HydraError("QEMU is not installed, Hydra requires QEMU")
        server.debug("HYDRA: Attemping to start services..")
        try:
            n = IPv4Network(HYDRA_BRIDGE_NETWORK)
        except ValueError as err:
            raise HydraError(f"Invalid Network settings: {err}")
        if n.num_addresses < 3:
            del n
            raise HydraError(
                "Invalid Network configuration settings, host max too small"
            )
        run(["/usr/bin/ip", "link", "set", HYDRA_BRIDGE, "down"], errors=False)
        run(["/usr/bin/ip", "link", "del", "name", HYDRA_BRIDGE], errors=False)
        try:
            run(["/usr/bin/ip", "link", "add", "name", HYDRA_BRIDGE, "type", "bridge"])
            run(
                [
                    "/usr/bin/ip",
                    "addr",
                    "add",
                    "dev",
                    HYDRA_BRIDGE,
                    f"{str(n[1])}/{n.prefixlen}",
                ]
            )
            run(["/usr/bin/ip", "link", "set", HYDRA_BRIDGE, "up"])
            run(["/usr/bin/sysctl", f"net.ipv4.conf.{HYDRA_BRIDGE}.forwarding=1"])
            run(["/usr/bin/sysctl", "net.ipv4.ip_forward=1"])
            if not isdir(DIRECTORY_HYDRA):
                mkdir(DIRECTORY_HYDRA)
            if not isdir(HYDRA_DHCP_DIR):
                mkdir(HYDRA_DHCP_DIR)
            write(HYDRA_TOKENS, EMPTY)
            run(["/usr/bin/chown", "-R", f"root:{HYDRA_UID}", DIRECTORY_HYDRA])
            run(["/usr/bin/chmod", "-R", "755", DIRECTORY_HYDRA])
            run(["/usr/bin/chown", "-R", f"{HYDRA_UID}:", HYDRA_DHCP_DIR])
            run(["/usr/bin/chmod", "-R", "750", HYDRA_DHCP_DIR])
        except OSError as err:
            self.stop(server, True)
            HydraError(f"Error setting up interfaces and directories: {err}")
        d = HYDRA_DNS_CONFIG.format(
            ip=str(n[1]),
            name=HYDRA_BRIDGE_NAME,
            network=HYDRA_BRIDGE_NETWORK,
            interface=HYDRA_BRIDGE,
            start=str(n[2]),
            netmask=str(n.netmask),
            end=str(n[n.num_addresses - 2]),
            dir=HYDRA_DHCP_DIR,
            user=HYDRA_UID,
        )
        try:
            write(HYDRA_DNS_FILE, d)
            run(["/usr/bin/chown", "-R", f"root:{HYDRA_UID}", HYDRA_DNS_FILE])
            run(["/usr/bin/chmod", "-R", "640", HYDRA_DNS_FILE])
        except OSError as err:
            self.stop(server, True)
            raise HydraError(f"Error writing DNS config: {err}")
        finally:
            del d
        s = HYDRA_SMB_CONFIG.format(
            ip=str(n[1]), name=NAME, network=HYDRA_BRIDGE_NETWORK
        )
        del n
        try:
            write(HYDRA_SMB_FILE, s)
            run(["/usr/bin/chown", "-R", f"root:{HYDRA_UID}", HYDRA_SMB_FILE])
            run(["/usr/bin/chmod", "-R", "640", HYDRA_SMB_FILE])
        except OSError as err:
            self.stop(server, True)
            raise HydraError(f"Error writing Samba config: {err}")
        finally:
            del s
        if exists(HYDRA_EXEC_DNS):
            try:
                self.dns_server = Popen(
                    [
                        "/usr/bin/dnsmasq",
                        "--keep-in-foreground",
                        "--log-facility=-",
                        f"--user={HYDRA_UID}",
                        f"--conf-file={HYDRA_DNS_FILE}",
                    ],
                    stderr=DEVNULL,
                    stdout=DEVNULL,
                )
            except (OSError, SubprocessError) as err:
                self.stop(server, True)
                raise HydraError(f"Error starting DNS server: {err}")
        else:
            server.warning(
                "HYDRA: Dnsmasq is not installed, VMs will function, but will lack network connectivity!"
            )
        self.web = server.get_config("hydra.web", True, True)
        if self.web:
            if exists(HYDRA_EXEC_TOKENS):
                try:
                    self.token_server = Popen(
                        [
                            "/usr/bin/python3",
                            HYDRA_EXEC_TOKENS,
                            "--token-plugin",
                            "TokenFile",
                            "--token-source",
                            HYDRA_TOKENS,
                            "127.0.0.1:8500",
                        ],
                        stderr=DEVNULL,
                        stdout=DEVNULL,
                    )
                except (OSError, SubprocessError) as err:
                    self.stop(server, True)
                    raise HydraError(f"Error starting Tokens server: {err}")
            else:
                server.warning(
                    "HYDRA: Websockify is not installed, VMs will function, but will lack local console connectivity!"
                )
            if exists(HYDRA_EXEC_NGINX):
                try:
                    self.web_server = Popen(
                        [HYDRA_EXEC_NGINX, "-c", f"{DIRECTORY_STATIC}/nginx.conf"],
                        stderr=DEVNULL,
                        stdout=DEVNULL,
                    )
                except (OSError, SubprocessError) as err:
                    self.stop(server, True)
                    raise HydraError(f"Error starting NGINX: {err}")
            else:
                server.warning(
                    "HYDRA: NGINX is not installed, VMs will function, but will lack screen connectivity!"
                )
        else:
            self.web_server = None
            self.token_server = None
            server.debug(
                "HYDRA: Not enabling Websockify as it's enable in the server config."
            )
        if exists(HYDRA_EXEC_SMB):
            try:
                # NOTE(dij): We're running this as a separate systemd service
                #            to ensure user home directory protection for the
                #            'smd-daemon' service but allow for users to use SMB
                #            to write files to their home dir.
                run(["/usr/bin/systemctl", "start", "smd-hydra-smb.service"])
            except OSError as err:
                self.stop(server, True)
                raise HydraError(f"Error starting Samba Systemd unit: {err}")
        else:
            server.warning(
                "HYDRA: Samba is not installed, VMs will function, but will lack file sharing!"
            )
        self.running = True
        server.info("HYDRA: Startup complete.")

    def thread(self, server):
        if not self.running:
            if len(self.vms) == 0:
                return
            server.debug("HYDRA: Starting due to presense of active VMs.")
            try:
                self.start(server)
            except HydraError as err:
                server.error("HYDRA: Error starting, clearing active VMs!", err=err)
                self.vms.clear()
            return
        if len(self.vms) == 0:
            server.debug("HYDRA: Shutting down due to inactivity.")
            return self.stop(server, False)
        u = False
        for vmid in list(self.vms.keys()):
            self.vms[vmid]._thread(self, server)
            if not self.vms[vmid]._stopped():
                continue
            u = True
            server.debug(f"HYDRA: VM({vmid}) Removing due to inactivity.")
            m = f"VM({vmid}) has shutdown"
            if self.vms[vmid]._exit != 0:
                m += f" with a non-zero exit code ({self.vms[vmid]._exit})!"
            else:
                m += "."
            if (
                isinstance(self.vms[vmid]._output, str)
                and len(self.vms[vmid]._output) > 0
            ):
                m += f"\n({self.vms[vmid]._output})"
            server.send(
                None,
                Message(
                    header=HOOK_NOTIFICATION,
                    payload={
                        "title": "Hydra VM Status",
                        "body": m,
                        "icon": "virt-viewer",
                    },
                ),
            )
            del m
            self._clean_usb(server, self.vms[vmid])
            self.vms[vmid]._stop(self, server, True, errors=False)
            del self.vms[vmid]
        if u and len(self.vms) > 0 and self.web:
            try:
                self._update_tokens(server)
            except HydraError as err:
                server.error("HYDRA: Error writing Tokens file!", err=err)
        del u
        self.scheduler.run(blocking=False)

    def stop(self, server, force):
        server.debug("HYDRA: Stopping services and freeing resources..")
        try:
            stop(self.dns_server)
        except AttributeError:
            pass
        if self.web:
            try:
                stop(self.web_server)
            except AttributeError:
                pass
            try:
                stop(self.token_server)
            except AttributeError:
                pass
        run(["/usr/bin/systemctl", "stop", "smd-hydra-smb.service"], errors=False)
        for vm in list(self.vms.values()):
            try:
                vm._stop(self, server, True)
                vm.write()
            except (HydraError, OSError) as err:
                server.warning(f"HYDRA: VM({vm.vmid}) Error stopping VM!", err=err)
        self.vms.clear()
        self.usbs.clear()
        if self.running or force:
            try:
                run(["/usr/bin/ip", "link", "set", HYDRA_BRIDGE, "down"])
            except OSError as err:
                if not force:
                    server.warning("HYDRA: Error disabling internal bridge!", err=err)
            try:
                run(["/usr/bin/ip", "link", "del", "name", HYDRA_BRIDGE])
            except OSError as err:
                if not force:
                    server.warning("HYDRA: Error removing internal bridge!", err=err)
        if self.running:
            try:
                write(HYDRA_RESERVE, "0\n", errors=False)
            except OSError as err:
                server.warning("HYDRA: Error clearing reserved memory!", err=err)
        if isdir(DIRECTORY_HYDRA):
            try:
                rmtree(DIRECTORY_HYDRA)
            except OSError as err:
                server.warning("HYDRA: Error removing the working directory!", err=err)
        self.running = False
        server.debug("HYDRA: Shutdown complete.")

    def hook(self, server, message):
        if "type" not in message or not isinstance(message.type, int):
            return
        if message.type == HYDRA_STATUS and len(message) <= 2:
            return {"vms": [vm._status() for vm in self.vms.values()]}
        if message.user and message.type == HYDRA_USER_DIRECTORY:
            return message.set_multicast(True)
        if message.all:
            for vm in self.vms.values():
                if not vm._running():
                    continue
                try:
                    if message.type == HYDRA_STOP:
                        vm._stop(self, server, message.force)
                    elif message.type == HYDRA_WAKE or message.type == HYDRA_SLEEP:
                        vm._sleep(server, message.type == HYDRA_SLEEP)
                except HydraError as err:
                    if message.type == HYDRA_STOP:
                        server.error(
                            f"HYDRA: VM({vm.vmid}) Error stopping VM!", err=err
                        )
                    elif message.type == HYDRA_WAKE:
                        server.error(f"HYDRA: VM({vm.vmid}) Error waking VM!", err=err)
                        continue
                    server.error(f"HYDRA: VM({vm.vmid}) Error sleeping VM!", err=err)
            return {"vms": [vm._status() for vm in self.vms.values()]}
        try:
            vm, n = self._get(server, message=message)
        except HydraError as err:
            server.error("HYDRA: Error loading VM!", err=err)
            return as_error(f"Could not load the specified VM: {err}")
        if message.user:
            message["vmid"] = vm.vmid
            message["path"] = vm.get_file()
            del vm
            return message.set_multicast(True)
        if message.type == HYDRA_STATUS:
            return vm._status()
        if message.type == HYDRA_START:
            if not n:
                return vm._status()
            try:
                self.vms[vm.vmid] = vm
                if vm._ready > 0:
                    return vm._status()
                self.start(server)
                vm._start(self, server)
                self._update_tokens(server)
            except (TypeError, HydraError) as err:
                if vm.vmid in self.vms and vm._process is None:
                    del self.vms[vm.vmid]
                server.error(f"HYDRA: VM({vm.vmid}) Error starting VM!", err=err)
                return as_error(f"Could not start VM {vm.vmid}: {err}")
            return vm._status()
        if not vm._running():
            return as_error(f"VM {vm.vmid} is not running!")
        if message.type == HYDRA_SLEEP or message.type == HYDRA_WAKE:
            try:
                vm._sleep(server, message.type == HYDRA_SLEEP)
            except HydraError as err:
                if message.type == HYDRA_SLEEP:
                    server.error(f"HYDRA: VM({vm.vmid}) Error sleeping VM!", err=err)
                    return as_error(f"Could not sleep VM {vm.vmid}: {err}")
                server.error(f"HYDRA: VM({vm.vmid}) Error waking VM!", err=err)
                return as_error(f"Could not wake VM {vm.vmid}: {err}")
            return vm._status()
        if message.type == HYDRA_STOP:
            try:
                vm._stop(self, server, message.force, message.get("timeout", 90))
            except HydraError as err:
                server.error(f"HYDRA: VM({vm.vmid}) Error stopping VM!", err=err)
                return as_error(f"Could not stop VM {vm.vmid}: {err}")
            return vm._status()
        if message.type == HYDRA_USB_QUERY:
            return vm._status(usb=True)
        if message.type == HYDRA_USB_CLEAN:
            self._clean_usb(server, vm)
            return vm._status()
        if message.type == HYDRA_USB_ADD:
            try:
                self._connect_usb(
                    server, vm, message.vendor, message.product, message.slow
                )
            except (ValueError, HydraError) as err:
                server.error(
                    f'HYDRA: VM({vm.vmid}) Error adding USB device "{message.vendor}:{message.product}"!',
                    err=err,
                )
                return as_error(f"Could not add USB to VM {vm.vmid}: {err}")
            return vm._status(usb=True)
        if message.type == HYDRA_USB_DELETE:
            try:
                self._disconnect_usb(server, vm, message.usb)
            except (ValueError, HydraError) as err:
                server.error(
                    f'HYDRA: VM({vm.vmid}) Error removing USB ID "{message.usb}"!',
                    err=err,
                )
                return as_error(f"Could not remove USB from VM {vm.vmid}: {err}")
            return vm._status(usb=True)
        if message.type == HYDRA_GA_IP:
            try:
                return vm._ip(server)
            except HydraError as err:
                server.error(
                    f"HYDRA: VM({vm.vmid}) Error retriving the IP address for the VM!",
                    err=err,
                )
                return as_error(f"Could not retrive the VM IP address: {err}")
        if message.type == HYDRA_GA_PING:
            return vm._ping(server)
        if message.type == HYDRA_TAP:
            try:
                vm._stop(self, server, False, tap=True)
            except HydraError as err:
                server.error(f"HYDRA: VM({vm.vmid}) Error tapping VM!", err=err)
                return as_error(f"Could not tap VM {vm.vmid}: {err}")
            return True
        return as_error("Unknown or invalid command!")

    def _update_tokens(self, server):
        if not self.web:
            return
        server.debug(f'HYDRA: Updating VM tokens file "{HYDRA_TOKENS}".')
        t = list()
        for vmid, vm in self.vms.items():
            t.append(f"VM{vmid}: unix_socket:{vm._path}.vnc")
        try:
            write(HYDRA_TOKENS, NEWLINE.join(t), perms=0o640)
        except OSError as err:
            raise HydraError(f'Error writing tokens "{HYDRA_TOKENS}": {err}')
        finally:
            del t

    def _clean_usb(self, server, vm):
        if not isinstance(vm._usb, dict) or len(vm._usb) == 0:
            return
        e = list(vm._usb.keys())
        for i in e:
            try:
                self._disconnect_usb(server, vm, i)
            except (ValueError, HydraError) as err:
                server.error(f'HYDRA: VM({vm.vmid}) Error removing USB "{i}"!', err=err)
        del e

    def hibernate(self, server, message):
        if message.type != MESSAGE_TYPE_PRE or len(self.vms) == 0:
            return
        server.info("HYDRA: Sleeping all VMs due to Hibernation/Suspend.")
        for vm in self.vms.values():
            try:
                if vm._sleeping:
                    continue
                vm._sleep(server, True)
            except HydraError as err:
                server.error(f"HYDRA: VM({vm.vmid}) Error sleeping VM!", err=err)

    def _disconnect_usb(self, server, vm, usb):
        if not isinstance(usb, str) and not isinstance(usb, int):
            raise ValueError("USB ID value is invalid")
        if isinstance(usb, str):
            # NOTE(dij): Verify that usb is a valid integer string.
            #            The upper function will catch it.
            int(usb, 10)
        d = f"{vm.vmid}:{usb}"
        if d not in list(self.usbs.values()):
            raise HydraError(
                f'Could not find USB "usb-dev-{usb}" connected to VM({vm.vmid})!'
            )
        vm._remove_usb(server, usb)
        for n, i in self.usbs.copy().items():
            if i != d:
                continue
            del self.usbs[n]
            server.debug(
                f'HYDRA: VM({vm.vmid}) Removed USB device "{n}" ({usb}) from the VM.'
            )
            break
        del d

    def _get(self, server, vmid=None, message=None):
        if vmid is None and message is not None:
            vmid = message.get("vmid")
        if isinstance(vmid, str):
            try:
                vmid = int(vmid, 10)
            except ValueError:
                vmid = None
        if isinstance(vmid, int) and vmid in self.vms:
            return self.vms[vmid], False
        if message is not None and isinstance(message.get("path"), str):
            try:
                vm = HydraVM(path=get_vm(message.path))
            except (HydraError, OSError) as err:
                raise HydraError(f'Cannot load VM from "{message.path}": {err}!')
            if vm.vmid in self.vms and self.vms[vm.vmid]._running():
                server.debug(
                    f'HYDRA: VM({vm.vmid}) Currently running VM was loaded from "{vm.get_file()}", '
                    "returning running instance instead!"
                )
                return self.vms[vm.vmid], True
            server.debug(f'HYDRA: VM({vm.vmid}) Loaded from "{vm.get_file()}"!')
            return vm, True
        raise HydraError("Cannot locate VM without a proper VMID or Path value")

    def _connect_usb(self, server, vm, vendor, product, slow):
        if not isinstance(vendor, str) and not isinstance(product, str):
            raise ValueError("Vendor/Product values are invalid")
        if len(vendor) == 0 or len(product) == 0:
            raise ValueError("Vendor/Product values are invalid")
        d = f"{vendor}:{product}"
        if d in self.usbs:
            raise HydraError(f'USB device "{d}" is already connected to another VM')
        e = get_usb()
        if d not in e:
            del e
            raise HydraError(f'USB device "{d}" is not connected to the system')
        del e
        try:
            i = vm._add_usb(server, vendor, product, slow)
        except (HydraError, OSError) as err:
            raise HydraError(f'Could not connect USB device "{d}": {err}')
        self.usbs[d] = f"{vm.vmid}:{i}"
        server.debug(f'HYDRA: VM({vm.vmid}) Added USB device "{d}" to VM as "{i}"!')
        del d
        return i


class HydraError(OSError):
    def __init__(self, error):
        OSError.__init__(self, error)


class HydraWaitThread(Thread):
    def __init__(self, vm, server):
        self.vm = vm
        self.server = server

    def run(self):
        try:
            for _ in range(0, 15):
                sleep(1)
                if self.vm._running():
                    break
            if not self.vm._running():
                self.vm._ready = 2
                return self.server.error(f"HYDRA: VM({self.vm.vmid}) Failed to start!")
            self.server.debug(
                f"HYDRA: VM({self.vm.vmid}) Started, PID: {self.vm._process.pid}!"
            )
            self.vm._ready = 1
        except Exception as err:
            self.server.error(
                f"HYDRA: VM({self.vm.vmid}) Error waiting for VM power on!", err=err
            )
            self.vm._ready = 2
