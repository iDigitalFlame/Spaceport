#!/usr/bin/false
# Module: Hydra (System, User)
#
# Manages, Provisions and Monitors Virtual Machines on the system.
# Requires: NGINX, Websockify, Samba, DnsMasq
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
from random import randint
from sched import scheduler
from time import time, sleep
from threading import Thread
from ipaddress import IPv4Network
from signal import SIGCONT, SIGSTOP
from lib.structs.message import Message
from lib.structs.storage import Storage
from json import dumps, loads, JSONDecodeError
from os import mkdir, listdir, environ, getcwd, chmod, stat
from subprocess import Popen, DEVNULL, PIPE, SubprocessError
from os.path import isdir, isfile, exists, basename, isabs, dirname
from socket import socket, AF_UNIX, SOCK_STREAM, error as socket_error
from lib.util import read, write, stop, run, remove_file, read_json, eval_env
from lib.constants import (
    NAME,
    EMPTY,
    HYDRA_UID,
    HOOK_HYDRA,
    HYDRA_WAKE,
    HYDRA_STOP,
    HYDRA_SLEEP,
    HYDRA_START,
    HOOK_DAEMON,
    HYDRA_BRIDGE,
    HYDRA_STATUS,
    HOOK_SUSPEND,
    HYDRA_TOKENS,
    HYDRA_RESERVE,
    HYDRA_USB_DIR,
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
        usb_devices = listdir(HYDRA_USB_DIR)
    except OSError:
        return dict()
    devices = dict()
    for device in usb_devices:
        vendor_path = f"{HYDRA_USB_DIR}/{device}/idVendor"
        product_path = f"{HYDRA_USB_DIR}/{device}/idProduct"
        if not isfile(vendor_path) or not isfile(product_path):
            continue
        try:
            vendor = read(vendor_path, ignore_errors=False).replace("\n", EMPTY)
            product = read(product_path, ignore_errors=False).replace("\n", EMPTY)
        except OSError:
            continue
        finally:
            del vendor_path
            del product_path
        name = "USB Device"
        name_vendor = f"{HYDRA_USB_DIR}/{device}/manufacturer"
        name_product = f"{HYDRA_USB_DIR}/{device}/{product}"
        try:
            if isfile(name_vendor) and isfile(name_product):
                name = "%s %s" % (
                    read(name_product, ignore_errors=False).replace("\n", EMPTY),
                    read(name_vendor, ignore_errors=False).replace("\n", EMPTY),
                )
            elif isfile(name_vendor):
                name = read(name_vendor, ignore_errors=False).replace("\n", EMPTY)
            elif isfile(name_product):
                name = read(name_product, ignore_errors=False).replace("\n", EMPTY)
        except OSError:
            continue
        finally:
            del name_vendor
            del name_product
        devices[f"{vendor}:{product}"] = {
            "name": f"{name} ({vendor}:{product}",
            "vendor": vendor,
            "product": product,
            "path": f"{HYDRA_USB_DIR}/{device}",
        }
        del name
        del vendor
        del product
    del usb_devices
    return devices


def _response(output):
    if not isinstance(output, bytes) or len(output) == 0:
        return None
    try:
        out = output.decode("UTF-8")
    except UnicodeDecodeError:
        return None
    if len(out) == 0:
        return None
    response = list()
    for line in out.split("\r\n"):
        if len(response) == 0:
            continue
        try:
            result = loads(line)
        except JSONDecodeError:
            raise OSError(f'Received an invalid server response "{line}"!')
        if not isinstance(result, dict):
            return None
        if "error" in result:
            raise OSError(result["error"])
        response.append(result)
        del result
    del out
    return response


def get_vm(path, config=None):
    if not isinstance(path, str) or len(path) == 0:
        return None
    aliases = dict()
    if isinstance(config, str) and isfile(config):
        data = read_json(config)
        if isinstance(data, dict) and "hydra" in data:
            if "aliases" in data["hydra"]:
                alias = path.lower()
                aliases = data["hydra"]["aliases"]
                if isinstance(aliases, dict) and alias in aliases:
                    user_path = eval_env(aliases[alias])
                    if exists(user_path):
                        path = user_path
                    del user_path
                del alias
                del aliases
            if isinstance(path, str) and path == ".":
                path = getcwd()
            if path is None or not isabs(path) and "directory" in data["hydra"]:
                user_dir = eval_env(data["hydra"]["directory"])
                if isinstance(user_dir, str) and len(user_dir) > 0:
                    user_path = f"{user_dir}/{path}"
                    if exists(user_path):
                        path = user_path
                    del user_path
                del user_dir
        del data
    if isinstance(path, str) and path == ".":
        path = getcwd()
    if isinstance(path, str) and isfile(path):
        return path
    if "HOME" in environ:
        if not isabs(path):
            path = eval_env(path)
        if not isabs(path):
            cwd_path = f"{getcwd()}/{path}"
            if exists(cwd_path):
                path = cwd_path
            del cwd_path
    if not exists(path):
        return None
    if isdir(path):
        base_dir = basename(path)
        names = [
            base_dir,
            f"{base_dir}.conf",
            f"{base_dir}.json",
            f"{base_dir}.vmx",
        ] + HYDRA_VM_CONFIGS
        for name in names:
            name_path = f"{path}/{name}"
            if isfile(name_path):
                return name_path
            del name_path
        del names
        del base_dir
    if isfile(path):
        return path
    return None


def user_alias(server, message):
    print(message)
    if message.type == HYDRA_USER_DIRECTORY:
        directory = message.get("directory", EMPTY)
        server.debug(f'Updating Hydra VM user directory to "{directory}".')
        server.set_config("hydra.directory", directory, True)
        del directory
        return
    name = message.get("name", None)
    aliases = server.get_config("hydra.aliases", dict(), True)
    if name is None or message.get("path", None) is None:
        return
    if message.type == HYDRA_USER_ADD_ALIAS:
        aliases[name.lower()] = message["path"]
        server.debug(f'Added user alias "{name}" to Hydra VM "{message["vmid"]}".')
    elif message.type == HYDRA_USER_DELETE_ALIAS:
        del aliases[name]
        server.debug(f'Removed user alias "{name}" from Hydra VM "{aliases[name]}".')
    server.set_config("hydra.aliases", aliases, True)
    del name
    del aliases


def _reserve(server, vmid, memory, remove=False):
    if not isinstance(memory, int):
        try:
            memory = int(memory)
        except ValueError as err:
            raise HydraError(
                f"VM ({vmid}) Unable to convert {memory} to a number! ({err})"
            )
    blocks = int(memory / HYDRA_RESERVE_SIZE)
    if blocks * HYDRA_RESERVE_SIZE < memory:
        blocks += 1
    try:
        pages = int(read(HYDRA_RESERVE, ignore_errors=False).replace("\n", EMPTY))
    except (OSError, ValueError) as err:
        raise HydraError(
            f"VM ({vmid}) Attempting to get reserve memory failed! ({err})"
        )
    if not remove:
        server.debug(
            f"HYDRA: VM({vmid}) Current page size {pages}, adding {blocks} blocks.."
        )
        pages += blocks
    else:
        server.debug(
            f"HYDRA: VM({vmid}) Current page size {pages}, removing {blocks} blocks.."
        )
        pages -= blocks
    if pages < 0:
        pages == 0
    try:
        write(HYDRA_RESERVE, f"{pages}\n", ignore_errors=False)
    except OSError as err:
        raise HydraError(f"VM({vmid}) Failed reserve memory! ({err})")
    del pages
    if not remove:
        server.debug(f"HYDRA: VM({vmid}) Reserved {blocks} blocks of memory.")
    else:
        server.debug(f"HYDRA: VM({vmid}) Removed {blocks} resevered blocks of memory.")
    del blocks
    del memory


class HydraVM(Storage):
    def __init__(self, vmid=None, file_path=None):
        Storage.__init__(self, file_path=file_path)
        self._exit = 0
        self._ready = 0
        self._usb = None
        self._event = None
        self._output = None
        self._process = None
        self._sleeping = False
        self._interfaces = None
        if vmid is not None:
            self.vmid = vmid
        elif self.get("vmid", None) is None:
            raise HydraError("HydraVM does not have a VMID!")
        self._path = f"{DIRECTORY_HYDRA}/{str(self.vmid)}"

    def _pid(self):
        return self._process.pid if self._running() else None

    def _status(self):
        if self._event is not None:
            status = "stopping"
        elif self._running():
            if self._ready == 1:
                status = "waiting"
            elif self._sleeping:
                status = "sleeping"
            else:
                status = "running"
        else:
            status = "stopped"
        return {
            "pid": self._pid(),
            "vmid": self.vmid,
            "path": self.get_file(),
            "status": status,
        }

    def _running(self):
        return self._process is not None and self._process.poll() is None

    def _stopped(self):
        return self._ready == 3 and self._process is None

    def _drives(self, server):
        if not isinstance(self.drives, dict):
            server.debug(f"HYDRA: VM({self.vmid}) No drives found, returning empty!")
            self.drives = dict()
            return list()
        ide = 0
        drives = dict()
        indexes = list()
        for name, drive in self.drives.items():
            if not isinstance(drive, dict):
                continue
            if "file" not in drive:
                server.warning(
                    f'HYDRA: VM({self.vmid}) Drive "{name}" does not contain a "file" value, skipping!'
                )
                continue
            file = drive["file"]
            if not isabs(file):
                file = f"{dirname(self.get_file())}/{file}"
                if not isfile(file):
                    raise HydraError(f'Drive "{name}" file "{file}" does not exist!')
            elif not isfile(file):
                raise HydraError(f'Drive "{name}" file "{file}" does not exist!')
            drive["file"] = file
            del file
            if "index" in drive:
                if drive["index"] in indexes or not isinstance(drive["index"], int):
                    server.warning(
                        f'HYDRA: VM({self.vmid}) Drive "{name}", removing invalid drive index "{drive["index"]}"!'
                    )
                    del drive["index"]
                else:
                    indexes.append(drive["index"])
            if "index" not in drive:
                if len(indexes) == 0:
                    drive["index"] = 1
                else:
                    drive["index"] = max(indexes) + 1
                indexes.append(drive["index"])
            if "type" not in drive:
                drive["type"] = "ide"
                ide += 1
            else:
                if (
                    drive["type"] == "ide"
                    or drive["type"] == "cd"
                    or drive["type"] == "iso"
                ):
                    ide += 1
            if ide > 4:
                raise HydraError("There can only be a maximum of 4 IDE devices!")
            if "format" not in drive:
                drive["format"] = "raw"
            drives[name] = drive
        del indexes
        ide = 0
        sata = 0
        build = list()
        for name, drive in drives.items():
            build_str = (
                f'id={name},file={drive["file"]},format={drive["format"]},index={drive["index"]},'
                f"if=none,detect-zeroes=unmap"
            )
            if not drive.get("direct", True):
                build_str += ",aio=threads"
            elif drive["format"] == "raw" and drive["type"] == "virtio":
                build_str += ",aio=native,cache.direct=on"
            else:
                build_str += ",aio=threads,cache=writeback"
            if "readonly" in drive and drive["readonly"]:
                build_str += ",readonly=on"
            if "discard" in drive and drive["discard"]:
                if drive["type"] == "scsi":
                    build_str += ",discard=on"
                else:
                    build_str += ",discard=unmap"
            build += ["-drive", build_str]
            del build_str
            if drive["type"] == "scsi":
                if ide == 0:
                    build += [
                        "-device",
                        f"virtio-scsi-pci,id=scsi0,bus={self.bus}.0,addr=0x5,iothread=iothread0",
                    ]
                build += [
                    "-device",
                    f"scsi-hd,bus=scsi0.0,channel=0,scsi-id=0,lun={ide},drive={name},id=scsi-{ide},rotation_rate=1",
                ]
                ide += 1
                self.drives[name] = drive
                continue
            if drive["type"] == "virtio":
                build += [
                    "-device",
                    f'virtio-blk-pci,id={name}-dev,drive={name},bus={self.bus}.0,bootindex={drive["index"]}',
                ]
                self.drives[name] = drive
                continue
            bus = "ide"
            bus_num = ide
            if "q35" in self.get("type"):
                bus_num += 1
            else:
                bus_num = ide / 2
            if drive["type"] == "sata":
                bus = "sata"
                if sata == 0:
                    sata = 1
                    build += ["-device", "ich9-ahci,id=sata"]
                bus_num = sata
            build += [
                "-device",
                f'ide-{"cd" if drive["type"] == "cd" or drive["type"] == "iso" else "hd"},id={name}-dev,'
                f'drive={name},bus={bus}.{bus_num},bootindex={drive["index"]}',
            ]
            del bus
            del bus_num
            if drive["type"] == "sata":
                sata += 1
            else:
                ide += 1
            self.drives[name] = drive
        del ide
        del sata
        del drives
        return build

    def _network(self, server):
        if not isinstance(self.network, dict):
            server.debug(
                f"HYDRA: VM({self.vmid}) No network interfaces, returning empty!"
            )
            self.network = dict()
            return list()
        address = 20
        build = list()
        self._interfaces = list()
        for name, net in self.network.items():
            if not isinstance(net, dict):
                server.warning(
                    f'HYDRA: VM({self.vmid}) Network Interface "{name}" was not a proper JSON dict!'
                )
                continue
            if "type" not in net:
                net["type"] = "intel"
            if "bridge" in net:
                bridge = net["bridge"]
            else:
                bridge = HYDRA_BRIDGE
            if "device" in net:
                device = net["device"]
            else:
                device = f"{HYDRA_BRIDGE}s{self.vmid}n{len(self._interfaces)}"
            self._interfaces.append(("device" not in net, device, bridge))
            if "mac" not in net:
                net[
                    "mac"
                ] = f"2c:af:01:{randint(0, 255):02x}:{randint(0, 255):02x}:{randint(0, 255):02x}"
            if net["type"] == "intel":
                net_device = "e1000"
            elif net["type"] == "virtio":
                net_device = "virtio-net-pci"
            elif net["type"] == "vmware":
                net_device = "vmxnet3"
            else:
                net_device = net["type"]
            build += [
                "-netdev",
                f"type=tap,id={name},ifname={device},script=no,downscript=no,vhost=on",
                "-device",
                f'{net_device},mac={net["mac"]},netdev={name},bus={self.bus}.0,addr={hex(address)},id={name}-dev',
            ]
            address += 1
            del device
            del bridge
            del net_device
            self.network[name] = net
        del address
        return build

    def _sleep(self, server, sleep):
        if not self._running():
            raise HydraError("VM is not currently running!")
        if sleep and self._sleeping:
            raise HydraError("VM is currently sleeping!")
        if not sleep and not self._sleeping:
            raise HydraError("VM is not currently sleeping!")
        if sleep and not self._sleeping:
            try:
                server.debug(f"HYDRA: VM({self.vmid}) Attempting to sleep VM..")
                self._process.send_signal(SIGSTOP)
            except OSError as err:
                raise HydraError(err)
            server.debug(f"HYDRA: VM({self.vmid}) Was put to sleep!")
            self._sleeping = True
        elif self._sleeping:
            try:
                server.debug(f"HYDRA: VM({self.vmid}) Attempting to wake VM..")
                self._process.send_signal(SIGCONT)
            except OSError as err:
                raise HydraError(err)
            server.debug(f"HYDRA: VM({self.vmid}) Was woken up!")
            self._sleeping = False

    def _start(self, manager, server):
        if self._running():
            return self._process.pid
        self._ready = 0
        binary = self.get("binary")
        if binary is not None:
            unsafe = server.get_config("hydra.unsafe", False, True)
            if not unsafe:
                raise HydraError(
                    f'VM({self.vmid}) Failed to start, cannot use binary "{binary}" when '
                    f'server "hydra.unsafe" is False!'
                )
            del unsafe
            allowed = server.get_config("hydra.allowed", list(), True)
            if not isinstance(allowed, list) or binary not in allowed:
                raise HydraError(
                    f'VM({self.vmid}) Failed to start, binary "{binary}" is not in server "hydra.allowed"!'
                )
            del allowed
        if binary is None or not exists(binary):
            binary = HYDRA_EXEC_VM
        try:
            s = stat(binary, follow_symlinks=False)
        except OSError as err:
            raise HydraError(
                f'VM({self.vmid}) Failed to start, binary "{binary}" could not be verified by stat! ({err})'
            )
        else:
            if s.st_uid != 0 or s.st_gid != 0:
                raise HydraError(
                    f'VM({self.vmid}) Failed to start, binary "{binary}" owner and/or group is not root! '
                    f"(Binary must have root owner and group to be ran!)"
                )
            del s
        if self.get("bios-version", 1) == 0:
            if self.get("bios-uefi", True):
                bios = "type=0,uefi=on"
            else:
                bios = "type=0"
        else:
            bios = f'type={self.get("bios-version", 1)}'
        build = [
            binary,
            "-runas",
            HYDRA_UID,
            "-smbios",
            bios,
            "-enable-kvm",
            "-k",
            "en-us",
            "-boot",
            "order=c,menu=off,splash-time=0",
            "-rtc",
            "base=localtime,clock=host",
            "-cpu",
        ]
        del bios
        del binary
        cpu_options = self.get("cpu-options", list())
        if isinstance(cpu_options, list) and len(cpu_options) > 0:
            build.append(
                f'{self.get("cpu-type", "host")},kvm=on,+kvm_pv_unhalt,+kvm_pv_eoi,hv_relaxed,'
                f'hv_spinlocks=0x1fff,hv_vapic,hv_time,{",".join(self.get("cpu-options"))}'
            )
        else:
            build.append(
                f'{self.get("cpu-type", "host")},kvm=on,+kvm_pv_unhalt,+kvm_pv_eoi,hv_relaxed,'
                f"hv_spinlocks=0x1fff,hv_vapic,hv_time"
            )
        del cpu_options
        if self.get("bios", None) and isfile(self.get("bios", None)):
            build += ["-bios", self.get("bios", None)]
        if self.get("bus", None) is None:
            if "q35" in self.get("type"):
                self.bus = "pcie"
            else:
                self.bus = "pci"
        if isinstance(self.get("extra", None), list):
            build += self.get("extra")
        cpu_num = self.get("cpu", 1)
        build += [
            "-machine",
            f'type={self.get("type", "q35")},mem-merge=on,dump-guest-core=off,accel={self.get("accel", "kvm")}',
            "-smp",
            f"{cpu_num},sockets={cpu_num},cores=1,maxcpus={cpu_num}",
            "-uuid",
            self.get("uuid", str(uuid4())),
            "-m",
            f'size={self.get("memory", 1024)}',
            "-name",
            f'"{self.get("name", f"hydra-vm-{self.vmid}")}"',
            "-pidfile",
            f"{self._path}.pid",
            "-display",
            f"vnc=unix:{self._path}.vnc",
            "-qmp",
            f"unix:{self._path}.sock,server,nowait",
            "-object",
            "iothread,id=iothread0",
            "-device",
            f"virtio-balloon-pci,id=ballon0,bus={self.bus}.0,addr=0x0c",
            "-device",
            f"virtio-keyboard-pci,id=keyboard0,bus={self.bus}.0,addr=0x11",
            "-device",
            f"usb-ehci,multifunction=on,id=usb-bus1,bus={self.bus}.0,addr=0x0d",
            "-device",
            f"piix3-usb-uhci,multifunction=on,id=usb-bus0,bus={self.bus}.0,addr=0x0e",
            "-device",
            f"pci-bridge,id=pci-bridge1,chassis_nr=1,bus={self.bus}.0,addr=0x0f",
            "-device",
            f"pci-bridge,id=pci-bridge2,chassis_nr=2,bus={self.bus}.0,addr=0x10",
        ]
        if "q35" in self.get("type"):
            build += ["-device", "intel-iommu"]
        del cpu_num
        if self.get("display", "virtio") is not None:
            build.append("-vga")
            if len(self.get("display")) == 0:
                build.append("std")
            else:
                build.append(self.get("display"))
        if self.get("sound", True):
            build += [
                "-device",
                f"intel-hda,id=sound1,bus={self.bus}.0,addr=0x0b",
                "-device",
                "hda-duplex,id=sound2",
            ]
        if self.get("input", "standard") == "tablet":
            build += ["-device", "usb-tablet,id=tablet0,bus=usb-bus0.0,port=1"]
        elif self.get("input", "standard") == "mouse":
            build += [
                "-device",
                f"virtio-mouse-pci,id=tablet0,bus={self.bus}.0,addr=0x0a",
            ]
        elif self.get("input", "standard") == "usb":
            build += [
                "-device",
                "usb-mouse,id=tablet0,bus=usb-bus0.0,port=1",
                "-device",
                "usb-kbd,id=tablet1,bus=usb-bus0.0,port=2",
            ]
        else:
            self.input = "standard"
            build += [
                "-device",
                f"virtio-tablet-pci,id=tablet0,bus={self.bus}.0,addr=0x0a",
            ]
        if self.get("tpm") is not None:
            build += ["-tpmdev", f'passthrough,id=tpm0,path={self.get("tpm")}']
        try:
            build += self._drives(server)
            build += self._network(server)
            try:
                self._start_interfaces(server)
            except HydraError:
                try:
                    # Remove any stale interfaces and try one more time
                    # :fingers-crossed:
                    self._stop_interfaces(server)
                except HydraError:
                    pass
                self._start_interfaces(server)
            if self.get_file() is not None:
                server.debug(f"HYDRA: VM({self.vmid}) Saving VM config file.")
                self.write()
        except (OSError, ValueError, SubprocessError) as err:
            raise HydraError(f"VM({self.vmid}) Failed to start! ({err})")
        server.debug(f"HYDRA: VM({self.vmid}) Built VM string, starting VM..")
        if self.get("reserve", True):
            build += ["-mem-path", "/dev/hugepages"]
            _reserve(server, self.vmid, self.get("memory", 1024), False)
        if self.get("debug", False):
            server.error(f'HYDRA: VM({self.vmid}) Dump: [{" ".join(build)}]')
        try:
            self._process = Popen(build, stdout=DEVNULL, stderr=PIPE)
        except (OSError, ValueError, SubprocessError) as err:
            server.send(
                None,
                Message(
                    header=HOOK_NOTIFICATION,
                    payload={
                        "title": "Hydra VM Status",
                        "body": f"VM({self.vmid}) failed to start!!",
                        "icon": "virt-viewer",
                    },
                ),
            )
            self.vm._ready = 2
            self._stop(manager, server, True)
            raise HydraError(f"VM({self.vmid}) Failed to start! ({err})")
        finally:
            del build
        server.send(
            None,
            Message(
                header=HOOK_NOTIFICATION,
                payload={
                    "title": "Hydra VM Status",
                    "body": f"VM({self.vmid}) was started!",
                    "icon": "virt-viewer",
                },
            ),
        )
        if not self._running():
            server.warning(
                f"HYDRA: VM({self.vmid}) is taking longer to startup, passing to thread!"
            )
            thread = HydraWaitThread(self, server)
            thread.start()
            del thread
            return 0
        self._ready = 1
        server.debug(
            f"HYDRA: VM({self.vmid}) Started, Process ID: {self._process.pid}!"
        )
        return self._process.pid

    def _thread(self, manager, server):
        if self._ready == 1:
            try:
                chmod(f"{self._path}.vnc", 0o762)
            except OSError:
                pass
            else:
                self._ready = 2
        if self._ready > 0 and not self._running():
            self._stop(manager, server, True)
        if not self._running() and self._ready == 2:
            if self._process is not None:
                self._exit = self._process.returncode
            self._process = None

    def _remove_usb(self, server, usb):
        if not isinstance(self._usb, dict) or usb not in self._usb:
            raise HydraError(
                f'Could not find USB device ID "{usb}" connected to the VM!'
            )
        try:
            self._command("device_del", {"id": f"usb-dev-{usb}"})
        except HydraError as err:
            raise HydraError(
                f'Could not remove USB device "{self._usb[usb]}", server returned "{err}"!'
            )
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
        if not isinstance(self._interfaces, list):
            return None
        server.debug(f"HYDRA: VM({self.vmid}) Attempting to remove interfaces..")
        for interface in self._interfaces:
            run(["/usr/bin/ip", "link", "set", interface[1], "nomaster"])
            run(["/usr/bin/ip", "link", "set", "dev", interface[1], "down"])
            if interface[0]:
                run(
                    [
                        "/usr/bin/ip",
                        "tuntap",
                        "delete",
                        "dev",
                        interface[1],
                        "mode",
                        "tap",
                    ]
                )
            server.debug(f'HYDRA: VM({self.vmid}) Removed interface "{interface[1]}".')
        server.debug(f"HYDRA: VM({self.vmid}) Removed interfaces.")

    def _start_interfaces(self, server):
        if not isinstance(self._interfaces, list):
            return None
        server.debug(f"HYDRA: VM({self.vmid}) Attempting to create interfaces..")
        for interface in self._interfaces:
            run(["/usr/bin/ip", "link", "set", interface[1], "nomaster"])
            run(["/usr/bin/ip", "link", "set", "dev", interface[1], "down"])
            if interface[0]:
                run(
                    [
                        "/usr/bin/ip",
                        "tuntap",
                        "delete",
                        "dev",
                        interface[1],
                        "mode",
                        "tap",
                    ]
                )
            try:
                if interface[0]:
                    run(
                        [
                            "/usr/bin/ip",
                            "tuntap",
                            "add",
                            "dev",
                            interface[1],
                            "mode",
                            "tap",
                            "user",
                            HYDRA_UID,
                        ],
                        ignore_errors=False,
                    )
                run(
                    [
                        "/usr/bin/ip",
                        "link",
                        "set",
                        interface[1],
                        "master",
                        interface[2],
                    ],
                    ignore_errors=False,
                )
                run(
                    [
                        "/usr/bin/ip",
                        "link",
                        "set",
                        "dev",
                        interface[1],
                        "up",
                        "promisc",
                        "on",
                    ],
                    ignore_errors=False,
                )
                server.debug(
                    f'HYDRA: VM({self.vmid}) Added interface "{interface[1]}".'
                )
            except OSError as err:
                self._stop_interfaces(server)
                raise HydraError(err)
        server.debug(f"HYDRA: VM({self.vmid}) Created interfaces.")

    def _command(self, command, args=None):
        if not self._running():
            raise HydraError("Cannot send a command to a stopped VM!")
        if not isinstance(command, dict) and not isinstance(command, str):
            raise HydraError('Paramater "command" must be a Python dict or str!')
        con = socket(AF_UNIX, SOCK_STREAM)
        try:
            con.connect(f"{self._path}.sock")
            con.sendall(HYDRA_COMMAND_START)
            out = _response(con.recv(4096))
            if out is None:
                raise HydraError("Invalid server response!")
            json = {"execute": command}
            if isinstance(args, dict):
                json["arguments"] = args
            encoded = bytes(dumps(json), "UTF-8")
            del json
            con.sendall(encoded)
            out = _response(con.recv(4096))
            if out is None:
                raise HydraError("Received an invalid server response!")
            con.sendall(encoded)
            con.sendall(encoded)
            out = _response(con.recv(4096))
            if out is None:
                raise HydraError("Received an invalid server response!")
            del out
            del encoded
        except (OSError, socket_error) as err:
            raise HydraError(err)
        finally:
            con.close()
            del con
        return True

    def _add_usb(self, server, vendor, product, slow):
        device = f"{vendor}:{product}"
        if not isinstance(self._usb, dict):
            self._usb = dict()
        elif device in list(self._usb.values()):
            raise HydraError(
                f'The USB device "{device}" is already mounted to the VM as "usb-dev{self._usb[device]}"!'
            )
        if len(self._usb) == 0:
            id = 1
        else:
            id = max(self._usb.keys()) + 1
        try:
            run(
                ["/usr/bin/chown", "-R", HYDRA_UID, HYDRA_USB_DEVICES],
                ignore_errors=False,
            )
        except OSError as err:
            raise HydraError(err)
        bus = "usb-bus1.0"
        if slow:
            bus = "usb-bus0.0"
        try:
            self._command(
                "device_add",
                {
                    "id": f"usb-dev-{id}",
                    "bus": bus,
                    "driver": "usb-host",
                    "vendorid": f"0x{vendor}",
                    "productid": f"0x{product}",
                },
            )
        except HydraError as err:
            raise HydraError(
                f'Could not add USB device "{device}", server returned "{err}"!'
            )
        server.debug(f'HYDRA: VM({self.vmid}) Added USB device "{device}" to the VM.')
        self._usb[id] = device
        server.send(
            None,
            Message(
                header=HOOK_NOTIFICATION,
                payload={
                    "title": "Hydra USB Device Connected",
                    "body": f'USB Device "{device}" connected to VM({self.vmid}).',
                    "icon": "usb-creator",
                },
            ),
        )
        del device
        return id

    def _stop(self, manager, server, force=False, timeout=90):
        if not force and self._running():
            if self._event is not None:
                raise HydraError("VM soft shutdown is already in progress!")
            if not isinstance(timeout, int):
                raise HydraError("Timeout must be an integer!")
            if self._sleeping:
                self._sleep(server, False)
            server.debug(
                f"HYDRA: VM({self.vmid}) Shutting down, timeout {timeout} seconds.."
            )
            try:
                self._command("system_powerdown")
            except HydraError as err:
                server.error(
                    f"HYDRA: VM({self.vmid}) Attempting to initiate VM shutdown raised an exception!",
                    err=err,
                )
                raise err
            finally:
                self._event = manager.scheduler.enter(
                    timeout, 1, self._stop, argument=(manager, server, True)
                )
            return None
        if self._process is not None and not self._running():
            self._exit = self._process.returncode
        if not self._running() and (self.get("debug") or self._exit != 0):
            try:
                self._output = (
                    self._process.stderr.read().decode("UTF-8").replace("\n", EMPTY)
                )
            except (IOError, UnicodeDecodeError, AttributeError):
                pass
            else:
                if len(self._output) > 0:
                    server.error(
                        f"HYDRA: VM({self.vmid}) Process output dump\nSTDERR[{self._output}]\n"
                    )
        server.debug(f"HYDRA: VM({self.vmid}) Stopping..")
        stop(self._process)
        self._stop_interfaces(server)
        if isinstance(self._interfaces, list):
            self._interfaces.clear()
            self._interfaces = None
        if self._event is not None:
            try:
                manager.scheduler.cancel(self._event)
            except ValueError:
                pass
            self._event = None
        try:
            del self._process
        except AttributeError:
            pass
        self._process = None
        if isinstance(self._usb, dict):
            for dev in self._usb.values():
                if dev in manager.usbs:
                    del manager.usbs[dev]
            self._usb.clear()
            self._usb = None
        if self.get("reserve", True):
            _reserve(server, self.vmid, self.get("memory", 1024), True)
        remove_file(f"{self._path}.pid")
        remove_file(f"{self._path}.vnc")
        remove_file(f"{self._path}.sock")
        self._ready = 3


class HydraServer(object):
    def __init__(self):
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
            raise HydraError("QEMU is not installed, Hydra requires QEMU!")
        server.debug("HYDRA: Attemping to start services..")
        try:
            network = IPv4Network(HYDRA_BRIDGE_NETWORK)
        except ValueError as err:
            server.error("HYDRA: Incorrect network configuration settings!", err=err)
            raise HydraError(err)
        if network.num_addresses < 3:
            server.error(
                "HYDRA: Incorrect network configuration settings, host max too small!"
            )
            del network
            raise HydraError(
                "Incorrect network configuration settings, host max too small!"
            )
        run(["/usr/bin/ip", "link", "set", HYDRA_BRIDGE, "down"], ignore_errors=True)
        run(["/usr/bin/ip", "link", "del", "name", HYDRA_BRIDGE], ignore_errors=True)
        try:
            run(
                ["/usr/bin/ip", "link", "add", "name", HYDRA_BRIDGE, "type", "bridge"],
                ignore_errors=False,
            )
            run(
                [
                    "/usr/bin/ip",
                    "addr",
                    "add",
                    "dev",
                    HYDRA_BRIDGE,
                    f"{str(network[1])}/{network.prefixlen}",
                ],
                ignore_errors=False,
            )
            run(["/usr/bin/ip", "link", "set", HYDRA_BRIDGE, "up"], ignore_errors=False)
            run(
                ["/usr/bin/sysctl", f"net.ipv4.conf.{HYDRA_BRIDGE}.forwarding=1"],
                ignore_errors=False,
            )
            run(["/usr/bin/sysctl", "net.ipv4.ip_forward=1"], ignore_errors=False)
            if not isdir(DIRECTORY_HYDRA):
                mkdir(DIRECTORY_HYDRA)
            if not isdir(HYDRA_DHCP_DIR):
                mkdir(HYDRA_DHCP_DIR)
            write(HYDRA_TOKENS, EMPTY)
            run(
                ["/usr/bin/chown", "-R", f"root:{HYDRA_UID}", DIRECTORY_HYDRA],
                ignore_errors=False,
            )
            run(["/usr/bin/chmod", "-R", "755", DIRECTORY_HYDRA], ignore_errors=False)
            run(
                ["/usr/bin/chown", "-R", f"{HYDRA_UID}:", HYDRA_DHCP_DIR],
                ignore_errors=False,
            )
            run(["/usr/bin/chmod", "-R", "750", HYDRA_DHCP_DIR], ignore_errors=False)
        except OSError as err:
            server.error(
                "HYDRA: Attempting to setup interfaces and directories raised an exception!",
                err=err,
            )
            self.stop(server, True)
            raise HydraError(err)
        dns = HYDRA_DNS_CONFIG.format(
            ip=str(network[1]),
            name=HYDRA_BRIDGE_NAME,
            network=HYDRA_BRIDGE_NETWORK,
            interface=HYDRA_BRIDGE,
            start=str(network[2]),
            netmask=str(network.netmask),
            end=str(network[network.num_addresses - 2]),
            dir=HYDRA_DHCP_DIR,
            user=HYDRA_UID,
        )
        try:
            write(HYDRA_DNS_FILE, dns, ignore_errors=False)
            run(
                ["/usr/bin/chown", "-R", f"root:{HYDRA_UID}", HYDRA_DNS_FILE],
                ignore_errors=False,
            )
            run(["/usr/bin/chmod", "-R", "640", HYDRA_DNS_FILE], ignore_errors=False)
        except OSError as err:
            server.error(
                "HYDRA: Attempting to create DNS config file raised an exception!",
                err=err,
            )
            self.stop(server, True)
            raise HydraError(err)
        finally:
            del dns
        smb = HYDRA_SMB_CONFIG.format(
            ip=str(network[1]), name=NAME, network=HYDRA_BRIDGE_NETWORK
        )
        del network
        try:
            write(HYDRA_SMB_FILE, smb, ignore_errors=False)
            run(
                ["/usr/bin/chown", "-R", f"root:{HYDRA_UID}", HYDRA_SMB_FILE],
                ignore_errors=False,
            )
            run(["/usr/bin/chmod", "-R", "640", HYDRA_SMB_FILE], ignore_errors=False)
        except OSError as err:
            server.error(
                "HYDRA: Attempting to create File server config file raised an exception!",
                err=err,
            )
            self.stop(server, True)
            raise HydraError(err)
        finally:
            del smb
        if exists(HYDRA_EXEC_DNS):
            try:
                self.dns_server = Popen(
                    [
                        "/usr/bin/dnsmasq",
                        "--keep-in-foreground",
                        f"--user={HYDRA_UID}",
                        f"--conf-file={HYDRA_DNS_FILE}",
                    ],
                    stderr=DEVNULL,
                    stdout=DEVNULL,
                )
            except (OSError, SubprocessError) as err:
                server.error(
                    "HYDRA: Attempting to start the DNS server raised an exception!",
                    err=err,
                )
                self.stop(server, True)
                raise HydraError(err)
        else:
            server.warning(
                "HYDRA: Dnsmasq is not installed, Hydra VMs will function, but will lack network connectivity!"
            )
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
                server.error(
                    "HYDRA: Attempting to start the Tokens server raised an exception!",
                    err=err,
                )
                self.stop(server, True)
                raise HydraError(err)
        else:
            server.warning(
                "HYDRA: Websockify is not installed, Hydra VMs will function, but will lack local console connectivity!"
            )
        if exists(HYDRA_EXEC_NGINX):
            try:
                self.web_server = Popen(
                    [HYDRA_EXEC_NGINX, "-c", f"{DIRECTORY_STATIC}/nginx.conf"],
                    stderr=DEVNULL,
                    stdout=DEVNULL,
                )
            except (OSError, SubprocessError) as err:
                server.error(
                    "HYDRA: Attempting to start the Web server raised an exception!",
                    err=err,
                )
                self.stop(server, True)
                raise HydraError(err)
        else:
            server.warning(
                "HYDRA: Nginx is not installed, Hydra VMs will function, but will lack screen connectivity!"
            )
        if exists(HYDRA_EXEC_SMB):
            try:
                run(
                    ["/usr/bin/systemctl", "start", "smd-hydra-smb.service"],
                    ignore_errors=False,
                )
            except OSError as err:
                server.error(
                    "HYDRA: Attempting to start the File server raised an exception!",
                    err=err,
                )
                self.stop(server, True)
                raise HydraError(err)
        else:
            server.warning(
                "HYDRA: Samba is not installed, Hydra VMs will function, but will lack file sharing!"
            )
        self.running = True
        server.debug("HYDRA: Startup complete.")

    def thread(self, server):
        if not self.running:
            if len(self.vms) == 0:
                return
            server.debug("HYDRA: Starting services due to presense of active VMS.")
            try:
                self.start(server)
            except HydraError as err:
                server.error(
                    "HYDRA: Attempting to start Hydra services raised an exception!",
                    err=err,
                )
            return
        if len(self.vms) == 0:
            server.debug("HYDRA: Stopping services due to inactivity.")
            self.stop(server)
            return
        updated = False
        for vmid in list(self.vms.keys()):
            self.vms[vmid]._thread(self, server)
            if not self.vms[vmid]._stopped():
                continue
            updated = True
            server.debug(f"HYDRA: VM({vmid}) is being removed due to inactivity.")
            msg = f"VM({vmid}) has shutdown"
            if self.vms[vmid]._exit != 0:
                msg += f" with a non-zero exit code ({self.vms[vmid]._exit})!"
            else:
                msg += "."
            if self.vms[vmid]._output is not None and len(self.vms[vmid]._output) > 0:
                msg += f"\n({self.vms[vmid]._output})"
            server.send(
                None,
                Message(
                    header=HOOK_NOTIFICATION,
                    payload={
                        "title": "Hydra VM Status",
                        "body": msg,
                        "icon": "virt-viewer",
                    },
                ),
            )
            del msg
            self._clean_usb(server, self.vms[vmid])
            self.vms[vmid]._stop(self, server, force=True)
            del self.vms[vmid]
        if updated:
            self._update_tokens(server)
        del updated
        self.scheduler.run(blocking=False)

    def hook(self, server, message):
        if message.type == HYDRA_STATUS and len(message) <= 2:
            return {"vms": [vm._status() for vm in self.vms.values()]}
        if message.get("user", False) and message.type == HYDRA_USER_DIRECTORY:
            return message.set_multicast(True)
        if message.get("all", False):
            for vm in self.vms.values():
                if not vm._running():
                    continue
                try:
                    if message.type == HYDRA_STOP:
                        vm._stop(self, server, force=message.get("force", False))
                    elif message.type == HYDRA_WAKE or message.type == HYDRA_SLEEP:
                        vm._sleep(server, message.type == HYDRA_SLEEP)
                except HydraError as err:
                    server.error(
                        f"HYDRA: Attempting to stop/sleep/wake VM({vm.vmid}) raised an exception!",
                        err=err,
                    )
            return {"vms": [vm._status() for vm in self.vms.values()]}
        try:
            vm = self._get(server, vmid=None, message=message)
        except HydraError as err:
            server.error(
                "HYDRA: Attempting to request a VM raised an exception!", err=err
            )
            return {
                "error": f"Could not load Hydra VM with the given paramaters! ({err})"
            }
        if message.get("user", False):
            message["vmid"] = vm.vmid
            message["path"] = vm.get_file()
            return message.set_multicast(True)
        if message.type == HYDRA_STATUS:
            return vm._status()
        if message.type == HYDRA_START:
            try:
                self.vms[vm.vmid] = vm
                self.start(server)
                vm._start(self, server)
                self._update_tokens(server)
            except HydraError as err:
                server.error(
                    f"HYDRA: Attempting to start VM({vm.vmid}) raised an exception!",
                    err=err,
                )
                return {"error": f"Could not start Hydra VM {vm.vmid}! ({err})"}
            return vm._status()
        if message.type == HYDRA_SLEEP or message.type == HYDRA_WAKE:
            try:
                vm._sleep(server, message.type == HYDRA_SLEEP)
            except HydraError as err:
                server.error(
                    f"HYDRA: Attempting to sleep/wake VM({vm.vmid}) raised an exception!",
                    err=err,
                )
                return {"error": f"Could not sleep/wake Hydra VM {vm.vmid}! ({err})"}
            return vm._status()
        if message.type == HYDRA_STOP:
            try:
                vm._stop(
                    self,
                    server,
                    message.get("force", False),
                    message.get("timeout", 90),
                )
            except HydraError as err:
                server.error(
                    f"HYDRA: Attempting to stop VM({vm.vmid}) raised an exception!",
                    err=err,
                )
                return {"error": f"Could not stop Hydra VM {vm.vmid}! ({err})"}
            return vm._status()
        if message.type == HYDRA_USB_QUERY:
            if not vm._running():
                return {
                    "error": f"Could not get Hydra VM {vm.vmid} USB list! (VM is not currently running!)"
                }
            status = vm._status()
            status["usb"] = vm._usb
            return status
        if message.type == HYDRA_USB_CLEAN:
            if not vm._running():
                return {
                    "error": f"Could not clear Hydra VM {vm.vmid} USB devices! (VM is not currently running!)"
                }
            self._clean_usb(server, vm)
            return vm._status()
        if message.type == HYDRA_USB_ADD:
            try:
                id = self._connect_usb(
                    server,
                    vm,
                    message.get("vendor"),
                    message.get("product"),
                    message.get("slow", False),
                )
            except HydraError as err:
                server.error(
                    f'HYDRA: Attempting to add USB device "{message.get("vendor")}:{message.get("product")}" '
                    f"to VM({vm.vmid}) raised an exception!",
                    err=err,
                )
                return {
                    "error": f"Could not add USB device to Hydra VM {vm.vmid}! ({err})"
                }
            status = vm._status()
            status["usb"] = id
            del id
            return status
        if message.type == HYDRA_USB_DELETE:
            try:
                self._disconnect_usb(server, vm, message.get("usb"))
            except HydraError as err:
                server.error(
                    f'HYDRA: Attempting to remove USB device ID "{message.get("usb")}" to '
                    f"VM({vm.vmid}) raised an exception!",
                    err=err,
                )
                return {
                    "error": f"Could not remove USB device from Hydra VM {vm.vmid}! ({err})"
                }
            return vm._status()
        return {"error": "Invalid command!"}

    def _update_tokens(self, server):
        server.debug(f'HYDRA: Updating VM tokens file "{HYDRA_TOKENS}".')
        tokens = list()
        for vmid, vm in self.vms.items():
            tokens.append(f"VM{vmid}: unix_socket:{vm._path}.vnc")
        try:
            write(HYDRA_TOKENS, "\n".join(tokens), ignore_errors=False)
            chmod(HYDRA_TOKENS, 0o640)
        except OSError as err:
            server.debug(
                f'HYDRA: Attempting to update the tokens file "{HYDRA_TOKENS}" raised an excpetion!',
                err=err,
            )
            raise HydraError(f'Filed to write to tokens file "{HYDRA_TOKENS}"! ({err})')
        finally:
            del tokens

    def _clean_usb(self, server, vm):
        if not isinstance(vm._usb, dict) or len(vm._usb) == 0:
            return
        active = list(vm._usb.keys())
        for id in active:
            self._disconnect_usb(server, vm, id)
        del active

    def stop(self, server, force=False):
        server.debug("HYDRA: Attempting to stop services and free resources..")
        try:
            stop(self.dns_server)
            del self.dns_server
        except AttributeError:
            pass
        try:
            stop(self.web_server)
            del self.web_server
        except AttributeError:
            pass
        try:
            stop(self.token_server)
            del self.token_server
        except AttributeError:
            pass
        run(["/usr/bin/systemctl", "stop", "smd-hydra-smb.service"], ignore_errors=True)
        for vm in list(self.vms.values()):
            try:
                vm._stop(self, server, force=True)
                vm.write()
            except HydraError as err:
                server.warning(
                    f"HYDRA: VM({self.vmid}) Attempting to stop VM raised an exception!",
                    err=err,
                )
        self.vms.clear()
        self.usbs.clear()
        if self.running or force:
            try:
                run(
                    ["/usr/bin/ip", "link", "set", HYDRA_BRIDGE, "down"],
                    ignore_errors=False,
                )
            except OSError as err:
                if not force:
                    server.warning(
                        "HYDRA: Attempting to remove internal bridge raised an exception!",
                        err=err,
                    )
            try:
                run(
                    ["/usr/bin/ip", "link", "del", "name", HYDRA_BRIDGE],
                    ignore_errors=False,
                )
            except OSError as err:
                if not force:
                    server.warning(
                        "HYDRA: Attempting to remove internal bridge raised an exception!",
                        err=err,
                    )
        if self.running:
            try:
                write(HYDRA_RESERVE, "0\n", ignore_errors=False)
            except OSError as err:
                server.warning(
                    "HYDRA: Attempting to clear reserved memory raised an exception!",
                    err=err,
                )
        if isdir(DIRECTORY_HYDRA):
            try:
                rmtree(DIRECTORY_HYDRA)
            except OSError as err:
                server.warning(
                    "HYDRA: Attempting to working directory raised an exception!",
                    err=err,
                )
        self.running = False
        server.debug("HYDRA: Shutdown complete.")

    def hibernate(self, server, message):
        if message.type != MESSAGE_TYPE_PRE:
            return
        if len(self.vms) == 0:
            return
        server.info("HYDRA: Sleeping all VMs due to hibernation/suspend!")
        for vm in self.vms.values():
            try:
                if not vm._sleeping:
                    vm._sleep(server, True)
            except HydraError as err:
                server.error(
                    f"HYDRA: Attempting to sleep/wake VM({vm.vmid}) raised an exception!",
                    err=err,
                )

    def _disconnect_usb(self, server, vm, usb):
        if not vm._running():
            raise HydraError("VM is not currently running!")
        if not isinstance(usb, str) and not isinstance(usb, int):
            server.error(
                f"HYDRA: VM({vm.vmid}) Attempted to remove a USB from the VM with an invalid USB ID!"
            )
            raise HydraError("Invalid USB ID!")
        device = f"{vm.vmid}:{usb}"
        if device not in list(self.usbs.values()):
            server.error(
                f'HYDRA: VM({vm.vmid}) Attempted to remove USB ID "{usb}" that is not connected to the VM!'
            )
            raise HydraError(
                f'Could not find USB ID "usb-dev{usb}" connected to VM({vm.vmid})!'
            )
        if not isinstance(usb, int):
            try:
                usb = int(usb)
            except ValueError as err:
                server.error(
                    f'HYDRA: VM({vm.vmid}) Attempted to remove invalid USB did "{usb}"!',
                    err,
                )
                raise HydraError(
                    f'Could not remove invalid USB ID "{usb}" from the VM({vm.vmid})!'
                )
        vm._remove_usb(server, usb)
        for name, did in self.usbs.copy().items():
            if did == device:
                del self.usbs[name]
                break

    def _get(self, server, vmid=None, message=None):
        if vmid is None and message is not None:
            vmid = message.get("vmid", None)
        if isinstance(vmid, str):
            try:
                vmid = int(vmid)
            except ValueError:
                vmid = None
        if isinstance(vmid, int) and vmid in self.vms:
            return self.vms[vmid]
        if message is not None and isinstance(message.get("path", None), str):
            try:
                vm = HydraVM(file_path=get_vm(message.get("path")))
            except (HydraError, OSError, TypeError) as err:
                server.error(
                    f'HYDRA: Attempting to load a VM from "{message.get("path")}" raised an exception!',
                    err=err,
                )
                raise HydraError(f"Could not load the requested HydraVM ({err})!")
            if vm.vmid in self.vms and self.vms[vm.vmid]._running():
                server.debug(
                    f'HYDRA: Loaded already running VMID({vm.vmid}) from "{vm.get_file()}", returning running instance!'
                )
                return self.vms[vm.vmid]
            server.debug(f'HYDRA: Loaded new VMID({vm.vmid}) from "{vm.get_file()}"!')
            return vm
        raise HydraError("Cannot locate VM without a proper VMID or Path value!")

    def _connect_usb(self, server, vm, vendor, product, slow=False):
        if not vm._running():
            raise HydraError("VM is not currently running!")
        if not isinstance(vendor, str) and not isinstance(product, str):
            server.error(
                f"HYDRA: VM({vm.vmid}) Attempted to add a USB to the VM with invalid product or vendor IDs!"
            )
            raise HydraError("Invalid product ot vendor IDs!")
        device = f"{vendor}:{product}"
        if device in self.usbs:
            server.error(
                f'HYDRA: VM({vm.vmid}) Attempted to add USB device "{device}" that is currently mounted on another VM!'
            )
            raise HydraError(
                f'USB device "{device}" is already connected to another VM!'
            )
        devices = get_usb()
        if device not in devices:
            del devices
            server.error(
                f'HYDRA: VM({vm.vmid}) Attempted to add USB device "{device}" that is not connected to the host!'
            )
            raise HydraError(
                f'Could not find USB device "{device}" connected to the system!'
            )
        del devices
        try:
            id = vm._add_usb(server, vendor, product, slow)
        except HydraError as err:
            server.error(
                f'HYDRA: VM({vm.vmid}) Attempted to add USB device "{device}" raised and exception!',
                err=err,
            )
            raise HydraError(
                f'Could not connect USB device "{device}" to VM({vm.vmid})!'
            )
        self.usbs[device] = f"{vm.vmid}:{id}"
        return id


class HydraError(OSError):
    def __init__(self, error):
        OSError.__init__(self, error)


class HydraWaitThread(Thread):
    def __init__(self, vm, server):
        self.vm = vm
        self.server = server

    def run(self):
        try:
            timeout = 15
            while timeout > 0:
                sleep(1)
                if self.vm._running():
                    break
                else:
                    timeout -= 1
            del timeout
            if not self.vm._running():
                self.server.error(f"HYDRA VM({self.vm.vmid}) Failed to start!")
                self.vm._ready = 2
                return
            self.server.debug(
                f"HYDRA: VM({self.vm.vmid}) Started, Process ID: {self.vm._process.pid}."
            )
            self.vm._ready = 1
        except Exception as err:
            self.server.error(
                f"HYDRA: VM({self.vm.vmid}) Exception occurred while waiting for a VM to power on!",
                err=err,
            )
            self.vm._ready = 2
