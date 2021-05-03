#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame 2018
#
# Module: Hydra (System, User)
#
# Manages, Provisions and Monitors Virtual Machines on the system.
# Requires: NGINX, Websockify, Samba, DnsMasq
# Updated 10/2018

from uuid import uuid4
from shutil import rmtree
from random import randint
from sched import scheduler
from time import time, sleep
from threading import Thread
from ipaddress import IPv4Network
from lib.structs.message import Message
from lib.structs.storage import Storage
from json import dumps, loads, JSONDecodeError
from os import mkdir, listdir, environ, getcwd
from subprocess import Popen, DEVNULL, SubprocessError
from lib.util import read, write, stop, run, remove_file, read_json
from socket import socket, AF_UNIX, SOCK_STREAM, error as socket_error
from os.path import join, isdir, isfile, exists, basename, isabs, dirname
from lib.constants import (
    HOOK_SHUTDOWN,
    HOOK_DAEMON,
    HOOK_HYDRA,
    HOOK_NOTIFICATION,
    HYDRA_BRIDGE,
    HYRDA_UID,
    HYDRA_VM_CONFIGS,
    DIRECTORY_HYRDA,
    HYDRA_TOKENS,
    HYDRA_BRIDGE_NAME,
    HYDRA_BRIDGE_NETWORK,
    HYDRA_USB_DIR,
    HYDRA_DNS_CONFIG,
    HYDRA_DNS_FILE,
    HYDRA_EXEC_NGINX,
    DIRECTORY_CONFIG,
    NAME_BASE,
    HYDRA_SMB_CONFIG,
    HYDRA_SMB_FILE,
    HYDRA_EXEC_DNS,
    HYDRA_EXEC_SMB,
    HYDRA_EXEC_VM,
    HYDRA_EXEC_TOKENS,
    HYDRA_COMMAND_START,
    HYDRA_USB_DEVICES,
    EMPTY,
    HYDRA_DHCP_DIR,
)

HOOKS = {HOOK_HYDRA: "hydra_user_alias"}
HOOKS_SERVER = {
    HOOK_HYDRA: "HydraServer.hook",
    HOOK_SHUTDOWN: "HydraServer.stop",
    HOOK_DAEMON: "HydraServer.thread",
}


def get_usb():
    devices = dict()
    try:
        usbs = listdir(HYDRA_USB_DIR)
    except OSError:
        pass
    else:
        for device in usbs:
            name_path = join(HYDRA_USB_DIR, device)
            vendor_path = join(HYDRA_USB_DIR, device, "idVendor")
            product_path = join(HYDRA_USB_DIR, device, "idProduct")
            if isfile(vendor_path) and isfile(product_path):
                try:
                    vendor = read(vendor_path, ignore_errors=False).replace("\n", "")
                    product = read(product_path, ignore_errors=False).replace("\n", "")
                    name = "%s %s" % (
                        read(join(name_path, "product"), ignore_errors=False).replace(
                            "\n", ""
                        ),
                        read(
                            join(name_path, "manufacturer"), ignore_errors=False
                        ).replace("\n", ""),
                    )
                    devices["%s:%s" % (vendor, product)] = {
                        "path": join(HYDRA_USB_DIR, device),
                        "name": name,
                        "vendor": vendor,
                        "product": product,
                    }
                    del name
                    del vendor
                    del product
                except OSError:
                    pass
            del name_path
            del vendor_path
            del product_path
        del usbs
    return devices


def _read_response(response_bytes):
    if isinstance(response_bytes, bytes):
        try:
            response_str = response_bytes.decode("UTF-8")
        except UnicodeDecodeError:
            return None
        else:
            responses = list()
            for response in response_str.split("\r\n"):
                if len(response) > 0:
                    try:
                        response_dict = loads(response)
                        if not isinstance(response_dict, dict):
                            return None
                        if "error" in response_dict:
                            raise OSError(response_dict["error"])
                        responses.append(response_dict)
                    except JSONDecodeError:
                        raise OSError(
                            'Received an invalid server response "%s"!' % str(response)
                        )
            return responses
    return None


def hydra_user_alias(server, message):
    if message.get("action") == "directory":
        directory = message.get("directory", EMPTY)
        server.debug('Updating Hydra VM directory to "%s".' % directory)
        server.set("hydra_directory", directory)
        del directory
    elif "alias" in message.get("action", EMPTY) and "alias" in message:
        alias = message.get("alias")
        names = server.config("hydra_aliases", dict())
        if message.get("action") == "alias-add" and "vm" in message:
            names[alias] = message["vm"]["path"]
            server.debug(
                'Added alias "%s" to Hydra VM "%s".' % (alias, message["vm"]["vmid"])
            )
        elif message.get("action") == "alias-del" and alias in names:
            server.debug(
                'Removed alias "%s" from Hydra VM "%s".' % (alias, names[alias])
            )
            del names[alias]
        server.set("hydra_aliases", names)
        del names
        del alias
    return None


def get_vm(name_path, config_path=None):
    if not isinstance(name_path, str) or len(name_path) == 0:
        return None
    path = None
    if isinstance(config_path, str) and isfile(config_path):
        try:
            config = read_json(config_path, ignore_errors=False)
        except OSError:
            pass
        else:
            if isinstance(config, dict):
                if "hydra_aliases" in config and isinstance(
                    config["hydra_aliases"], dict
                ):
                    name = name_path.lower()
                    if name in config["hydra_aliases"] and exists(
                        config["hydra_aliases"][name]
                    ):
                        path = config["hydra_aliases"][name]
                    del name
                if path is None or not isabs(path):
                    if "hydra_directory" in config and isinstance(
                        config["hydra_directory"], str
                    ):
                        path_dir = join(config["hydra_directory"], name_path)
                        if exists(path_dir):
                            path = path_dir
                        del path_dir
            del config
    if isinstance(path, str) and isfile(path):
        return path
    if isfile("%s.conf" % path):
        return "%s.conf" % path
    path = name_path
    if "HOME" in environ:
        if not isabs(name_path):
            if "~/" in path:
                path = name_path.replace("~/", environ["HOME"])
            if "$" in path:
                for env, value in environ.items():
                    if env in path:
                        path = path.replace("$%s" % env, value)
        if not isabs(path):
            path_dir = join(getcwd(), path)
            if exists(path_dir):
                path = path_dir
            del path_dir
    if not exists(path):
        del path
        return None
    if isdir(path):
        base = basename(path)
        names = [
            base,
            "%s.conf" % base,
            "%s.json" % base,
            "%s.vmx" % base,
        ] + HYDRA_VM_CONFIGS
        for name in names:
            path_file = join(path, name)
            if isfile(path_file):
                return path_file
            del path_file
        del base
        del names
    if isfile(path):
        return path
    del path
    return None


class HydraVM(Storage):
    def __init__(self, vmid=None, file_path=None):
        Storage.__init__(self, file_path=file_path)
        self._ready = 0
        self._usb = None
        self._event = None
        self._process = None
        self._interfaces = None
        if vmid is not None:
            self.vmid = vmid
        elif self.get("vmid", None) is None:
            raise HydraError("HydraVM does not have a VMID!")
        self._path = join(DIRECTORY_HYRDA, str(self.vmid))

    def _pid(self):
        return self._process.pid if self._running() else None

    def _status(self):
        if self._event is not None:
            status = "stopping"
        elif self._running():
            if self._ready == 1:
                status = "waiting"
            else:
                status = "running"
        else:
            status = "stopped"
        return {
            "vmid": self.vmid,
            "pid": self._pid(),
            "status": status,
            "path": self.get_file(),
        }

    def _running(self):
        return self._process is not None and self._process.poll() is None

    def _stopped(self):
        return self._ready > 0 and self._process is None

    def _get_drives(self, server):
        if not isinstance(self.drives, dict):
            server.debug("HYDRA: VM(%d) No drives found, returning empty!" % self.vmid)
            self.drives = dict()
            return list()
        ide = 0
        drives = dict()
        indexes = list()
        for did, drive in self.drives.items():
            if not isinstance(drive, dict):
                continue
            if "file" not in drive:
                server.warning(
                    'HYDRA: VM(%d) Drive "%s" does not contain a "file" value!'
                    % (self.vmid, did)
                )
                continue
            file = drive["file"]
            if not isabs(file):
                file = join(dirname(self.get_file()), file)
                if not isfile(file):
                    raise HydraError(
                        'Drive "%s" file "%s" does not exist!' % (did, file)
                    )
            elif not isfile(file):
                raise HydraError('Drive "%s" file "%s" does not exist!' % (did, file))
            drive["file"] = file
            del file
            if "index" in drive:
                if drive["index"] in indexes or not isinstance(drive["index"], int):
                    server.warning(
                        'HYDRA: VM(%d) Drive "%s", removing invalid drive index "%s"!'
                        % (self.vmid, did, drive["index"])
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
                raise HydraError(
                    "VM(%d): There can only be a maximum of 4 IDE devices!" % self.vmid
                )
            if "format" not in drive:
                drive["format"] = "raw"
            drives[did] = drive
        del indexes
        ide = 0
        build = list()
        for did, drive in drives.items():
            build_str = (
                "id=%s,file=%s,format=%s,index=%d,if=none,aio=threads,detect-zeroes=unmap"
                % (did, drive["file"], drive["format"], drive["index"])
            )
            if "readonly" in drive and drive["readonly"]:
                build_str += ",readonly=on"
            if "discard" in drive and drive["discard"]:
                build_str += ",discard=unmap"
            build += ["-drive", build_str]
            del build_str
            if drive["type"] == "virtio":
                build += [
                    "-device",
                    "virtio-blk-pci,id=%s-dev,drive=%s,bus=%s.0,bootindex=%d"
                    % (did, did, self.pci, drive["index"]),
                ]
            else:
                build += [
                    "-device",
                    "ide-%s,id=%s-dev,drive=%s,bus=ide.%d,bootindex=%d"
                    % (
                        (
                            "cd"
                            if drive["type"] == "cd" or drive["type"] == "iso"
                            else "hd"
                        ),
                        did,
                        did,
                        ide / 2,
                        drive["index"],
                    ),
                ]
                ide += 1
            self.drives[did] = drive
        del ide
        del drives
        return build

    def _get_network(self, server):
        if not isinstance(self.network, dict):
            server.debug(
                "HYDRA: VM(%d) No network interfaces, returning empty!" % self.vmid
            )
            self.network = dict()
            return list()
        address = 20
        build = list()
        self._interfaces = list()
        for nid, net in self.network.items():
            if not isinstance(net, dict):
                server.warning(
                    'HYDRA: VM(%d) Network Interface "%s" was not a proper JSON dict!'
                    % (self.vmid, nid)
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
                device = "%ss%dn%d" % (HYDRA_BRIDGE, self.vmid, len(self._interfaces))
            self._interfaces.append(("device" not in net, device, bridge))
            if "mac" not in net:
                net["mac"] = "2c:af:01:%02x:%02x:%02x" % (
                    randint(0, 255),
                    randint(0, 255),
                    randint(0, 255),
                )
            if net["type"] == "intel" or net["type"] == "e1000":
                netdev = "e1000"
            elif net["type"] == "virtio":
                netdev = "virtio-net-pci"
            elif net["type"] == "vmware" or net["type"] == "vmxnet3":
                netdev = "vmxnet3"
            else:
                netdev = net["type"]
            build += [
                "-netdev",
                "type=tap,id=%s,ifname=%s,script=no,downscript=no,vhost=on"
                % (nid, device),
                "-device",
                "%s,mac=%s,netdev=%s,bus=%s.0,addr=%s,id=%s-dev"
                % (netdev, net["mac"], nid, self.pci, hex(address), nid),
            ]
            address += 1
            del netdev
            del device
            del bridge
            self.network[nid] = net
        del address
        return build

    def _start(self, manager, server):
        if self._running():
            return self._process.pid
        self._ready = 0
        binary = self.get("vm-bin", None)
        if binary is None or not isfile(binary):
            binary = HYDRA_EXEC_VM
        build = [
            binary,
            "-runas",
            HYRDA_UID,
            "-smbios",
            "type=%s" % str(self.get("bios-version", 1)),
            "-enable-kvm",
            "-k",
            "en-us",
            "-boot",
            "order=c,menu=off,splash-time=0",
            "-rtc",
            "base=localtime,clock=host",
            "-cpu",
        ]
        del binary
        cpu_options = self.get("cpu-options", [])
        if isinstance(cpu_options, list) and len(cpu_options) > 0:
            build.append(
                "%s,%s"
                % (self.get("cpu-type", "host"), ",".join(self.get("cpu-options")))
            )
        else:
            build.append(self.get("cpu-type", "host"))
        if self.get("bios", None) and isfile(self.get("bios", None)):
            build += ["-bios", self.get("bios", None)]
        if self.get("type") == "q35":
            self.pci = "pcie"
        else:
            self.pci = "pci"
        build += [
            "-machine",
            "type=%s,mem-merge=on" % self.get("type", "q35"),
            "-accel",
            "accel=kvm,thread=multi",
            "-smp",
            "cpus=%s,cores=1" % str(self.get("cpu", 1)),
            "-uuid",
            self.get("uuid", str(uuid4())),
            "-m",
            "size=%s" % str(self.get("memory", 1024)),
            "-name",
            self.get("name", "hydra-vm-%d" % self.vmid),
            "-pidfile",
            "%s.pid" % self._path,
            "-display",
            "vnc=unix:%s.vnc" % self._path,
            "-qmp",
            "unix:%s.sock,server,nowait" % self._path,
            "-device",
            "virtio-balloon-pci,id=ballon0,bus=%s.0,addr=0x0c" % self.pci,
            "-device",
            "virtio-keyboard-pci,id=keyboard0,bus=%s.0,addr=0x11" % self.pci,
            "-device",
            "usb-ehci,multifunction=on,id=usb-bus1,bus=%s.0,addr=0x0d" % self.pci,
            "-device",
            "piix3-usb-uhci,multifunction=on,id=usb-bus0,bus=%s.0,addr=0x0e" % self.pci,
            "-device",
            "pci-bridge,id=pci-bridge1,chassis_nr=1,bus=%s.0,addr=0x0f" % self.pci,
            "-device",
            "pci-bridge,id=pci-bridge2,chassis_nr=2,bus=%s.0,addr=0x10" % self.pci,
        ]
        if self.get("display", "virtio") == "virtio":
            build += ["-vga", "virtio"]
        elif self.get("display", "virtio") == "vmware":
            build += ["-vga", "vmware"]
        if self.get("sound", True):
            build += [
                "-soundhw",
                "hda,pcspk",
                "-device",
                "intel-hda,id=sound1,bus=%s.0,addr=0x0b" % self.pci,
            ]
        if self.get("input", "pci") == "pci":
            build += [
                "-device",
                "virtio-tablet-pci,id=tablet0,bus=%s.0,addr=0x0a" % self.pci,
            ]
        elif self.get("input", "pci") == "usb":
            build += ["-device", "usb-tablet,id=tablet0,bus=usb-bus0.0,port=1"]
        elif self.get("input", "pci") == "mouse":
            build += [
                "-device",
                "virtio-mouse-pci,id=tablet0,bus=%s.0,addr=0x0a" % self.pci,
            ]
        elif self.get("input", "pci") == "mouse-usb":
            build += ["-device", "usb-mouse,id=tablet0,bus=usb-bus0.0,port=1"]
        if self.get("tpm") is not None:
            build += ["-tpmdev", "passthrough,id=tpm0,path=%s" % self.get("tpm")]
        try:
            build += self._get_drives(server)
            build += self._get_network(server)
            self._start_interfaces(manager, server)
            if self.get_file() is not None:
                server.debug("HYDRA: VM(%d) Saving VM config file." % self.vmid)
                self.write()
            server.debug("HYDRA: VM(%d) Built VM string, starting VM.." % self.vmid)
            if self.get("debug"):
                server.error("HYDRA: VM(%d) Dump: [%s]" % (self.vmid, " ".join(build)))
            server.send(
                None,
                Message(
                    header=HOOK_NOTIFICATION,
                    payload={
                        "title": "Hydra VM Status",
                        "body": "VM(%d) was started!" % self.vmid,
                        "icon": "virt-viewer",
                    },
                ),
            )
            self._process = Popen(build, stdout=DEVNULL, stderr=DEVNULL)
        except (OSError, ValueError, SubprocessError) as err:
            raise HydraError("VM(%d) Failed to start! (%s)" % (self.vmid, str(err)))
        else:
            if not self._running():
                server.warning(
                    "HYDRA: VM(%d) is taking longer to startup, passing to thread!"
                    % self.vmid
                )
                thread = HydraWaitThread(self, server)
                thread.start()
                del thread
                return 0
            self._ready = 1
            server.debug(
                "HYDRA: VM(%d) Started, Process ID: %d."
                % (self.vmid, self._process.pid)
            )
            return self._process.pid
        finally:
            del build
        return None

    def _thread(self, manager, server):
        if self._ready == 1:
            try:
                run(
                    ["/usr/bin/chmod", "762", "%s.vnc" % self._path],
                    ignore_errors=False,
                )
            except OSError as err:
                server.warning(
                    "HYDRA: VM(%d) Could not change permissions of VNC socket!"
                    % self.vmid,
                    err=err,
                )
            else:
                self._ready = 2
        if self._ready > 0 and not self._running():
            self._stop(manager, server, True)
        if not self._running() and self._ready == 2:
            self._process = None

    def _remove_usb(self, server, usbid):
        if not isinstance(self._usb, dict) or usbid not in self._usb:
            raise HydraError(
                'Could not find USB device ID "%s" connected to the VM!' % usbid
            )
        try:
            self._command("device_del", {"id": "usb-dev-%s" % usbid})
        except HydraError as err:
            raise HydraError(
                'Could not remove USB device "%s", server returned "%s"!'
                % (self._usb[usbid], str(err))
            )
        else:
            server.debug(
                'HYDRA: VM(%d) Removed USB device "%s" from the VM.'
                % (self.vmid, self._usb[usbid])
            )
            server.send(
                None,
                Message(
                    header=HOOK_NOTIFICATION,
                    payload={
                        "title": "Hydra USB Device Removed",
                        "body": 'USB Device "%s" disconnected from VM(%d).'
                        % (self._usb[usbid], self.vmid),
                        "icon": "usb-creator",
                    },
                ),
            )
            del self._usb[usbid]

    def _stop_interfaces(self, manager, server):
        if isinstance(self._interfaces, list):
            server.debug("HYDRA: VM(%d) Attempting to remove interfaces." % self.vmid)
            for interface in self._interfaces:
                try:
                    run(
                        ["/usr/bin/ip", "link", "set", interface[1], "nomaster"],
                        ignore_errors=False,
                    )
                except OSError as err:
                    server.warning(
                        'HYDRA: VM(%d) Attempting to remove interface "%s" raised an exception!'
                        % (self.vmid, interface[1]),
                        err=err,
                    )
                try:
                    run(
                        ["/usr/bin/ip", "link", "set", "dev", interface[1], "down"],
                        ignore_errors=False,
                    )
                except OSError as err:
                    server.warning(
                        'HYDRA: VM(%d) Attempting to remove interface "%s" raised an exception!'
                        % (self.vmid, interface[1]),
                        err=err,
                    )
                if interface[0]:
                    try:
                        run(
                            [
                                "/usr/bin/ip",
                                "tuntap",
                                "delete",
                                "dev",
                                interface[1],
                                "mode",
                                "tap",
                            ],
                            ignore_errors=False,
                        )
                    except OSError as err:
                        server.warning(
                            'HYDRA: VM(%d) Attempting to remove interface "%s" raised an exception!'
                            % (self.vmid, interface[1]),
                            err=err,
                        )
                server.debug(
                    'HYDRA: VM(%d) Removed interface "%s".' % (self.vmid, interface[1])
                )
            server.debug("HYDRA: VM(%d) Removed interfaces." % self.vmid)

    def _command(self, command, arguments=None):
        if not self._running():
            raise HydraError("Cannot send a command to a stopped VM!")
        if not isinstance(command, dict) and not isinstance(command, str):
            raise HydraError('Paramater "command" must be a Python dict or str!')
        try:
            connection = socket(AF_UNIX, SOCK_STREAM)
            connection.connect("%s.sock" % self._path)
            connection.sendall(
                HYDRA_COMMAND_START
            )  # bytes('{"execute": "qmp_capabilities"}', 'UTF-8'))
            response = _read_response(connection.recv(4096))
            if response is None:
                raise HydraError("Invalid server response!")
            command_json = {"execute": command}
            if isinstance(arguments, dict):
                command_json["arguments"] = arguments
            # command = bytes('{"execute": "%s", "arguments": %s}' % (command, dumps(arguments)), 'UTF-8')
            command_bytes = bytes(dumps(command_json), "UTF-8")
            del command_json
            connection.sendall(command_bytes)
            response = _read_response(connection.recv(4096))
            if response is None:
                raise HydraError("Received an invalid server response!")
            connection.sendall(command_bytes)
            connection.sendall(command_bytes)
            response = _read_response(connection.recv(4096))
            if response is None:
                raise HydraError("Received an invalid server response!")
            del response
            del command_bytes
        except (OSError, socket_error) as err:
            raise HydraError(err)
        finally:
            connection.close()
            del connection

    def _add_usb(self, server, vendor, product):
        device = "%s:%s" % (vendor, product)
        if not isinstance(self._usb, dict):
            self._usb = dict()
        elif device in list(self._usb.values()):
            raise HydraError(
                'The USB device "%s" is already mounted to the VM as "usb-dev%s"!'
                % (device, self._usb[device])
            )
        if len(self._usb) == 0:
            did = 1
        else:
            did = max(self._usb.keys()) + 1
        try:
            run(
                ["/usr/bin/chown", HYRDA_UID, "-R", HYDRA_USB_DEVICES],
                ignore_errors=False,
            )
        except OSError as err:
            raise HydraError(err)
        else:
            try:
                self._command(
                    "device_add",
                    {
                        "driver": "usb-host",
                        "id": "usb-dev-%s" % did,
                        "bus": "usb-bus1.0",
                        "vendorid": "0x%s" % vendor,
                        "productid": "0x%s" % product,
                    },
                )
            except HydraError as err:
                raise HydraError(
                    'Could not add USB device "%s", server returned "%s"!'
                    % (device, str(err))
                )
            else:
                server.debug(
                    'HYDRA: VM(%d) Added USB device "%s" to the VM.'
                    % (self.vmid, device)
                )
                self._usb[did] = device
                server.send(
                    None,
                    Message(
                        header=HOOK_NOTIFICATION,
                        payload={
                            "title": "Hydra USB Device Connected",
                            "body": 'USB Device "%s" connect to VM(%d).'
                            % (device, self.vmid),
                            "icon": "usb-creator",
                        },
                    ),
                )
                return did
        finally:
            del device
        return None

    def _start_interfaces(self, manager, server):
        if isinstance(self._interfaces, list):
            server.debug("HYDRA: VM(%d) Attempting to create interfaces." % self.vmid)
            for interface in self._interfaces:
                run(
                    ["/usr/bin/ip", "link", "set", interface[1], "nomaster"],
                    ignore_errors=True,
                )
                run(
                    ["/usr/bin/ip", "link", "set", "dev", interface[1], "down"],
                    ignore_errors=True,
                )
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
                        ],
                        ignore_errors=True,
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
                                HYRDA_UID,
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
                        'HYDRA: VM(%d) Added interface "%s".'
                        % (self.vmid, interface[1])
                    )
                except OSError as err:
                    self._stop_interfaces(manager, server)
                    raise HydraError(err)
            server.debug("HYDRA: VM(%d) Created interfaces." % self.vmid)

    def _stop(self, manager, server, force=False, timeout=90):
        if not force and self._running():
            if self._event is not None:
                raise HydraError("VM soft shutdown is already in progress!")
            if not isinstance(timeout, int):
                raise HydraError("Timeout must be an integer!")
            server.debug(
                "HYDRA: VM(%d) Shutting down, timeout %d seconds.."
                % (self.vmid, timeout)
            )
            try:
                self._command("system_powerdown")
            except HydraError as err:
                server.error(
                    "HYDRA: VM(%d) Attempting to initiate VM shutdown raised an exception!"
                    % self.vmid,
                    err=err,
                )
                raise err
            finally:
                self._event = manager.scheduler.enter(
                    timeout, 1, self._stop, argument=(manager, server, True)
                )
        else:
            server.debug("HYDRA: VM(%d) Stopping.." % self.vmid)
            stop(self._process)
            self._stop_interfaces(manager, server)
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
                self._usb.clear()
                self._usb = None
            remove_file("%s.pid" % self._path)
            remove_file("%s.vnc" % self._path)
            remove_file("%s.sock" % self._path)


class HydraServer(object):
    def __init__(self):
        self.vms = dict()
        self.usbs = dict()
        self.running = False
        self.dns_server = None
        self.web_server = None
        self.file_server = None
        self.token_server = None
        self.scheduler = scheduler(timefunc=time, delayfunc=sleep)

    def stop(self, server):
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
            stop(self.file_server)
            del self.file_server
        except AttributeError:
            pass
        try:
            stop(self.token_server)
            del self.token_server
        except AttributeError:
            pass
        for vm in list(self.vms.values()):
            try:
                vm._stop(self, server, force=True)
                vm.write()
            except HydraError as err:
                server.warning(
                    "HYDRA: VM(%d) Attempting to stop VM raised an exception!", err=err
                )
        self.vms.clear()
        if self.running:
            try:
                run(
                    ["/usr/bin/ip", "link", "set", HYDRA_BRIDGE, "down"],
                    ignore_errors=False,
                )
            except OSError as err:
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
                server.warning(
                    "HYDRA: Attempting to remove internal bridge raised an exception!",
                    err=err,
                )
            try:
                rmtree(DIRECTORY_HYRDA)
            except OSError as err:
                server.warning(
                    "HYDRA: Attempting to working directory raised an exception!",
                    err=err,
                )
        self.running = False
        server.debug("HYDRA: Shutdown complete.")

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
                    "%s/%d" % (str(network[1]), network.prefixlen),
                ],
                ignore_errors=False,
            )
            run(["/usr/bin/ip", "link", "set", HYDRA_BRIDGE, "up"], ignore_errors=False)
            run(
                ["/usr/bin/sysctl", "net.ipv4.conf.%s.forwarding=1" % HYDRA_BRIDGE],
                ignore_errors=False,
            )
            run(["/usr/bin/sysctl", "net.ipv4.ip_forward=1"], ignore_errors=False)
            if not isdir(DIRECTORY_HYRDA):
                mkdir(DIRECTORY_HYRDA)
            if not isdir(HYDRA_DHCP_DIR):
                mkdir(HYDRA_DHCP_DIR)
            write(HYDRA_TOKENS, EMPTY)
            run(
                ["/usr/bin/chown", "-R", "root:%s" % HYRDA_UID, DIRECTORY_HYRDA],
                ignore_errors=False,
            )
            run(["/usr/bin/chmod", "-R", "755", DIRECTORY_HYRDA], ignore_errors=False)
            run(
                ["/usr/bin/chown", "-R", "%s:" % HYRDA_UID, HYDRA_DHCP_DIR],
                ignore_errors=False,
            )
            run(["/usr/bin/chmod", "-R", "750", HYDRA_DHCP_DIR], ignore_errors=False)
        except OSError as err:
            server.error(
                "HYDRA: Attempting to setup interfaces and folders raised an exception!",
                err=err,
            )
            self.stop(server)
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
            user=HYRDA_UID,
        )
        try:
            write(HYDRA_DNS_FILE, dns, ignore_errors=False)
        except OSError as err:
            server.error(
                "HYDRA: Attempting to create DNS config file raised an exception!",
                err=err,
            )
            self.stop(server)
            raise HydraError(err)
        finally:
            del dns
        smb = HYDRA_SMB_CONFIG.format(
            ip=str(network[1]), name=NAME_BASE, network=HYDRA_BRIDGE_NETWORK
        )
        del network
        try:
            write(HYDRA_SMB_FILE, smb, ignore_errors=False)
        except OSError as err:
            server.error(
                "HYDRA: Attempting to create File server config file raised an exception!",
                err=err,
            )
            self.stop(server)
            raise HydraError(err)
        finally:
            del smb
        if exists(HYDRA_EXEC_DNS):
            try:
                self.dns_server = Popen(
                    [
                        "/usr/bin/dnsmasq",
                        "--keep-in-foreground",
                        "--user=%s" % HYRDA_UID,
                        "--conf-file=%s" % HYDRA_DNS_FILE,
                    ],
                    stderr=DEVNULL,
                    stdout=DEVNULL,
                )
            except (OSError, SubprocessError) as err:
                server.error(
                    "HYDRA: Attempting to start the DNS server raised an exception!",
                    err=err,
                )
                self.stop(server)
                raise HydraError(err)
        else:
            server.error(
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
                # TODO: Look into doing this raw Python
            except (OSError, SubprocessError) as err:
                server.error(
                    "HYDRA: Attempting to start the Tokens server raised an exception!",
                    err=err,
                )
                self.stop(server)
                raise HydraError(err)
        else:
            server.error(
                "HYDRA: Websockify is not installed, Hydra VMs will function, but will lack screen connectivity!"
            )
        if exists(HYDRA_EXEC_NGINX):
            try:
                self.web_server = Popen(
                    [
                        HYDRA_EXEC_NGINX,
                        "-c",
                        join(DIRECTORY_CONFIG, "hydra/nginx.conf"),
                    ],
                    stderr=DEVNULL,
                    stdout=DEVNULL,
                )
            except (OSError, SubprocessError) as err:
                server.error(
                    "HYDRA: Attempting to start the Web server raised an exception!",
                    err=err,
                )
                self.stop(server)
                raise HydraError(err)
        else:
            server.error(
                "HYDRA: Nginx is not installed, Hydra VMs will function, but will lack screen connectivity!"
            )
        if exists(HYDRA_EXEC_SMB):
            try:
                self.file_server = Popen(
                    [
                        HYDRA_EXEC_SMB,
                        "--foreground",
                        "--no-process-group",
                        "--configfile=%s" % HYDRA_SMB_FILE,
                    ],
                    stderr=DEVNULL,
                    stdout=DEVNULL,
                )
            except (OSError, SubprocessError) as err:
                server.error(
                    "HYDRA: Attempting to start the File server raised an exception!",
                    err=err,
                )
                self.stop(server)
                raise HydraError(err)
        else:
            server.error(
                "HYDRA: Samba is not installed, Hydra VMs will function, but will lack file sharing!"
            )
        self.running = True
        server.debug("HYDRA: Startup complete.")

    def thread(self, server):
        if self.running:
            updated = False
            for vmid in list(self.vms.keys()):
                self.vms[vmid]._thread(self, server)
                if self.vms[vmid]._stopped():
                    updated = True
                    server.debug(
                        "HYDRA: VM(%d) is being removed due to inactivity." % vmid
                    )
                    server.send(
                        None,
                        Message(
                            header=HOOK_NOTIFICATION,
                            payload={
                                "title": "Hydra VM Status",
                                "body": "VM(%d) has shutdown." % vmid,
                                "icon": "virt-viewer",
                            },
                        ),
                    )
                    del self.vms[vmid]
            if updated:
                self._update_tokens(server)
            del updated
            self.scheduler.run(blocking=False)
            if len(self.vms) == 0:
                server.debug("HYDRA: Stopping services due to inactivity.")
                self.stop(server)
        elif len(self.vms) > 0:
            server.debug("HYDRA: Starting services due to presense of active VMS.")
            try:
                self.start(server)
            except HydraError as err:
                server.error(
                    "HYDRA: Attempting to start Hydra services raised an exception!",
                    err=err,
                )

    def hook(self, server, message):
        if message.get("type") == "list":
            return {"vms": [vm._status() for vm in self.vms.values()]}
        elif message.get("type") == "user":
            if (
                message.get("action") == "directory"
                or message.get("action") == "alias-del"
            ):
                return message.set_multicast(True)
        try:
            vm = self._get(server, vmid=None, message=message)
        except HydraError as err:
            server.error(
                "HYDRA: Attempting to request a VM raised an exception!", err=err
            )
            return {
                "error": "Could not load HydraVM with given paramaters! (%s)" % str(err)
            }
        if message.get("type") == "user":
            if "alias" in message.get("action", EMPTY):
                message["vm"] = vm._status()
                return message.set_multicast(True)
            return None
        if message.get("type") == "get":
            return vm._status()
        elif message.get("type") == "start":
            try:
                self.start(server)
                vm._start(self, server)
                self._update_tokens(server)
            except HydraError as err:
                server.error(
                    "HYDRA: Attempting to start VM(%d) raised an exception!" % vm.vmid,
                    err=err,
                )
                return {
                    "error": 'Could not start HydraVM "%d"! (%s)' % (vm.vmid, str(err))
                }
            else:
                return vm._status()
        elif message.get("type") == "stop":
            try:
                vm._stop(
                    self,
                    server,
                    message.get("force", False),
                    message.get("timeout", 90),
                )
            except HydraError as err:
                server.error(
                    "HYDRA: Attempting to stop VM(%d) raised an exception!" % vm.vmid,
                    err=err,
                )
                return {
                    "error": 'Could not stop HydraVM "%d"! (%s)' % (vm.vmid, str(err))
                }
            else:
                return vm._status()
        elif message.get("type") == "status":
            return vm._status()
        elif message.get("type") == "usb":
            if message.get("action") == "query":
                status = vm._status()
                status["usb"] = vm._usb
                return status
            if message.get("action") == "connect":
                try:
                    did = self._connect_usb(
                        server, vm, message.get("vendor"), message.get("product")
                    )
                except HydraError as err:
                    server.error(
                        'HYDRA: Attempting to add USB device "%s:%s" to VM(%d) raised an exception!'
                        % (message.get("vendor"), message.get("product"), vm.vmid),
                        err=err,
                    )
                    return {
                        "error": 'Could not add USB device to HydraVM "%d"! (%s)'
                        % (vm.vmid, str(err))
                    }
                else:
                    status = vm._status()
                    status["usbid"] = did
                    del did
                    return status
            if message.get("action") == "disconnect":
                try:
                    self._disconnect_usb(server, vm, message.get("usbid"))
                except HydraError as err:
                    server.error(
                        'HYDRA: Attempting to remove USB device ID "%s" to VM(%d) raised an exception!'
                        % (message.get("usbid"), vm.vmid),
                        err=err,
                    )
                    return {
                        "error": 'Could not remove USB device from HydraVM "%d"! (%s)'
                        % (vm.vmid, str(err))
                    }
                else:
                    status = vm._status()
                    return status
        return {"error": "Invalid command!"}

    def _update_tokens(self, server):
        server.debug('HYDRA: Updating VM tokens file "%s".' % HYDRA_TOKENS)
        tokens = list()
        for vmid, vm in self.vms.items():
            tokens.append("VM%d: unix_socket:%s.vnc" % (vmid, vm._path))
        try:
            write(HYDRA_TOKENS, "\n".join(tokens), ignore_errors=False)
        except OSError as err:
            server.debug(
                'HYDRA: Attempting to update the tokens file "%s" raised an excpetion!'
                % HYDRA_TOKENS,
                err=err,
            )
            raise HydraError(
                'Filed to write to tokens file "%s"! (%s)' % (HYDRA_TOKENS, err)
            )
        finally:
            del tokens

    def _disconnect_usb(self, server, vm, usbid):
        if not isinstance(usbid, str) and not isinstance(usbid, int):
            server.error(
                "HYDRA: VM(%d) Attempted to remove a USB from the VM with an invalid USBID!"
                % vm.vmid
            )
            raise HydraError("Invalid USBID!")
        device = "%s:%s" % (vm.vmid, usbid)
        if device not in list(self.usbs.values()):
            server.error(
                'HYDRA: VM(%d) Attempted to remove USB device id "%s" that is not connected to the VM!'
                % (vm.vmid, usbid)
            )
            raise HydraError(
                'Could not find USB ID "usb-dev%s" connected to VM(%s)!'
                % (usbid, vm.vmid)
            )
        vm._remove_usb(server, usbid)
        for name, did in self.usbs.copy().items():
            if did == device:
                del self.usbs[name]
                break

    def _get(self, server, vmid=None, message=None):
        if vmid is None and message is not None and message.get("vmid"):
            vmid = message.get("vmid")
        if isinstance(vmid, str):
            try:
                vmid = int(vmid)
            except ValueError:
                vmid = None
        if vmid is not None and vmid in self.vms:
            return self.vms[vmid]
        if message is not None and message.get("path"):
            try:
                vm = HydraVM(file_path=get_vm(message.get("path")))
            except (HydraError, OSError, TypeError) as err:
                server.error(
                    'HYDRA: Attempting to load a VM from "%s" raised an exception!'
                    % message.get("path"),
                    err=err,
                )
            else:
                if vm.vmid in self.vms and self.vms[vm.vmid]._running():
                    server.debug(
                        'HYDRA: Loaded current VMID(%s) from "%s", updated saved instance with new values!'
                        % (vm.vmid, vm.get_file())
                    )
                    vm._usb = self.vms[vm.vmid]._usb
                    vm._event = self.vms[vm.vmid]._event
                    vm._ready = self.vms[vm.vmid]._ready
                    vm._process = self.vms[vm.vmid]._process
                    vm._interfaces = self.vms[vm.vmid]._interfaces
                    self.vms[vm.vmid] = vm
                else:
                    server.debug(
                        'HYDRA: Loaded VMID(%s) from "%s"!' % (vm.vmid, vm.get_file())
                    )
                    self.vms[vm.vmid] = vm
                return vm
        raise HydraError("Cannot locate VM without a proper VMID or Path value!")

    def _connect_usb(self, server, vm, vendor, product):
        if not isinstance(vendor, str) and not isinstance(product, str):
            server.error(
                "HYDRA: VM(%d) Attempted to add a USB to the VM with invalid product or vendor IDs!"
                % vm.vmid
            )
            raise HydraError("Invalid product ot vendor IDs!")
        device = "%s:%s" % (vendor, product)
        if device in self.usbs:
            server.error(
                'HYDRA: VM(%d) Attempted to add USB device "%s" that is currently mounted on another VM!'
                % (vm.vmid, device)
            )
            raise HydraError(
                'USB device "%s" is already connected to another VM!' % device
            )
        devices = get_usb()
        if device not in devices:
            del devices
            server.error(
                'HYDRA: VM(%d) Attempted to add USB device "%s" that is not connected to the host!'
                % (vm.vmid, device)
            )
            raise HydraError(
                'Could not find USB device "%s" connected to the system!' % device
            )
        del devices
        try:
            did = vm._add_usb(server, vendor, product)
        except HydraError as err:
            server.error(
                'HYDRA: VM(%d) Attempted to add USB device "%s" raised and exception!'
                % (vm.vmid, device),
                err=err,
            )
            raise HydraError(
                'Could not connect USB device "%s" to VM(%d)!' % (device, vm.vmid)
            )
        else:
            self.usbs[device] = "%s:%s" % (vm.vmid, did)
            return did
        finally:
            del device
        return None


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
                self.server.error("VM(%d) Failed to start!" % self.vm.vmid)
            else:
                self.server.debug(
                    "HYDRA: VM(%d) Started, Process ID: %d."
                    % (self.vm.vmid, self.vm._process.pid)
                )
            self.vm._ready = 1
        except Exception as err:
            self.server.send(
                None,
                Message(
                    header=HOOK_NOTIFICATION,
                    payload={
                        "title": "Hydra VM Error",
                        "body": "VM(%d) failed to start!" % self.vm.vmid,
                        "icon": "virt-viewer",
                    },
                ),
            )
            self.server.error(
                "HYDRA: VM(%d) Exception occured while waiting for a VM to power on!"
                % self.vm.vmid,
                err=err,
            )


# EOF
