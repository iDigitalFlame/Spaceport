#!/usr/bin/false
# PowerCTL Module: Hydra
#  powerctl hydra, hydractl, hydra
#
# PowerCTL command line user module to control and configure Hydra VMs
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

from os import fork
from time import sleep
from os.path import expandvars, expanduser
from lib.structs.message import send_message
from lib.modules.hydra import get_vm, get_usb
from lib.util import read_json, print_error, run
from lib.constants import (
    EMPTY,
    HOOK_OK,
    HYDRA_TAP,
    HOOK_HYDRA,
    HYDRA_STOP,
    HYDRA_WAKE,
    HYDRA_GA_IP,
    HYDRA_SLEEP,
    HYDRA_START,
    HYDRA_STATUS,
    HYDRA_GA_PING,
    HYDRA_USB_ADD,
    CONFIG_CLIENT,
    HYDRA_USB_QUERY,
    HYDRA_USB_CLEAN,
    DIRECTORY_HYDRA,
    HYDRA_USB_DELETE,
    HYDRA_USB_COMMANDS,
    HYDRA_USER_DIRECTORY,
    HYDRA_USER_ADD_ALIAS,
    HYDRA_USER_DELETE_ALIAS,
)

NAMES = dict()
SCHEMA = """# HydraVM Schema v1-release

bios {
    file            <String[File Path], Optional>
        Supported values: Any valid file path

        This value allows for supplying a BIOS ROM file that can be
        used as the BIOS instead of the default QEMU BIOS.

        This file must exist or the VM will fail during startup.

    version         <Integer, Optional[default= 1>
        Supported values: 0 | 1 | 2

        This value indicates the version of the BIOS used for the
        Virtual Machine. The primary usage of this is to enable or
        disable UEFI boot, which by default is disabled.

    uefi            <Boolean, Optional[default= false]>
        Supported values: false | true

        Enables or Disables UEFI mode for the Virtual Machine. This
        config option only is ONLY applicable if the setting
        "bios.version" == 0.
}
cpu {
    options         <List[string], Optional>
        The value contains a string list of CPU flags that will be
        added during the Virtual Machine building process. Each value
        in the list can be prefixed with a '+' or '-' to indicate
        enabled status. Omitting the prefix infers '+' or enabled.
        The plus '+' sign can be used to enable a flag (which is the
        same as omitting the prefix), while the minus '-' sign will
        disable a flag.

        Supplied flags that are not valid for the CPU or host will
        cause the VM to fail during startup.

    sockets         <Integer[default= 1]>
        Supported values: Integer greater than zero (> 0)

    type            <String[default= "host"]>
        Supported values: "host" | "kvm32" | "kvm64" | "qemu32" | "qemu64" |
            "base" | "Broadwell" | "EPYC" | "Haswell" | [etc...]
}
dev {
    bus             <String, Optional[default= "pci"]>
        Supported values: "pci" | "pcie"

        Determines the underlying BUS technology type. It is recommended
        to let Hydra pick this one based on the VM type.

    display         <String, Optional[default= "virtio"]>
        Supported values: "std" | "cirrus" | "vmware" | "qxl" | "virtio" | "none"

        Changes the specific type of VGA graphics driver used. This only
        affects how the display is rendered and rendered. This may affect
        resolution and performance. Setting this to "none" does NOT disable
        the VNC or spice viewers.

    input           <String, Optional[default= "standard"]>
        Supported values: "standard" | "virtio" | "tablet" | "usb" | "mouse"

    iommu           <Boolean, Optional[default= true]>
        Supported values: false | true

    sound           <Boolean, Optional[default= true]>
        Supported values: false | true

    tpm             <String[File Path], Optional>
        Supported values: Any valid file path
}
drives {
    <String[name of disk]> {
        file        <String[File Path]>
            Supported values: Any valid file (non-executable, non-suid/guid) path

        index       <Integer, Optional[default= 0]>
            Supported values: Any non-negative Integer

        type        <String, Optional[default= "ide"]>
            Supported values: "ide" | "cd" | "iso" | "sata" | "scsi" | "virtio"

        format      <String, Optional[default= "raw"]>
            Supported values: "raw" | "qcow" | "qcow2" | "vmdk"

        readonly    <Boolean, Optional[default= false]>
            Supported values: false | true

        discard     <Boolean, Optional[default= false]>
            Supported values: false | true

        direct      <Boolean, Optional[default= true]>
            Supported values: false | true
    }
}
memory {
    size            <Integer, Optional[default= 1024]>
        Supported values: Integer greater than zero (> 0)

        Size of memory allocated for the Virtual Machine in megabytes.
        This defaults to 1024MB (1GB) if omitted.

        Values less than or equal to zero or values larger than the
        host memory will cause the VM to fail during startup.

    reserve         <Boolean, Optional[default= false]>
        Supported values: false | true

        If true, this will indicate that the Virtual Machine ram "file"
        will be preallocated in the "/dev/hugepages" memory mount (if
        enabled). If preallocation fails, the VM will fail during startup.
}
network {
    <String[name of interface]> {
        mac     <String, Optional> = [mac address, 'aa:bb:cc:dd:ee:ff' format]
            Supported values: Mac address in hexadecimal format.

        type    <String, Optional[default= "intel"]>
            Supported values: "intel" | "virtio" | "vmware" | [other]

        bridge  <String, Optional>
            Supported values: Name of system bridge interface as String.

            This option can be used to bound the Virtual Machine interface
            to a specific device instead of the default "vmi0" interface.
            Hydra will be only responsible for adding the connection as the
            bridge client, it is the caller's responsibility to ensure it is
            configured and ready to use.
    }
}
vm {
    accel       <String, Optional[default= "kvm"]>
        Supported values: "kvm" | "xen" | "hax" | "hvf" | "nvmm" | "whpx" | "tcg"

        Specify the accelerator used for the Virtual Machine. Multiple
        values may be provided (seperated by a comma) which will
        attempt each one until one works properly. Default value is "kvm".

    binary      <String[File Path], Optional>
        Supported values: Any valid file path

        Specify the path of the Virtual Machine Emulator to use. This
        can be supplied to emulate different architecture or platform
        types.

        If specified, the "hydra.unsafe" server config option
        must be set to true and the provided path must exist in
        the "hydra.allowed" server config option.

        Paths supplied must have root owner and group, cannot be
        writable by group or other and must have execute permissions
        for owner and group (ie: chmod 755) in order to be executed.

    debug       <Bool, Optional>
        Supported values: false | true

    extra       <List[String], Optional> = [extra QEMU arguments]
        Supported values: List of string command arguments to be added

        Extra arguments to be added to the command string for
        QEMU. These are parsed directly and will are NOT shell
        expanded.

        Requires the "hydra.unsafe" server config option to be
        used. Extra lines are written to the system log under the
        "info" level.

    name        <String, Optional>
        Supported values: Virtual Machine name as a String

    spice       <Bool, Optional[default= true]>
        Supported values: false | true

        This setting will enable/disable the SPICE client connector, which
        allows for separate USB connectivity and full copy/paste between
        the host and client.

    type        <String[default= "q35"]>
        Supported values: "pc" | "microvm" | "q35" | "pc-i440fx-*" | "pc-q35-*" | "x-remote"

    uuid        <String[UUID], Optional>
        Supported values: UUID String in a valid UUID4 format.
}
vmid        <Integer>
        Supported values: Unique Integer greater than zero (> 0)

        ID value for the Virtual Machine. This value must be unique
        across all local VMs and cannot be less than zero.

        This value is used to indicate the VM in operations or via the
        command line.
"""
EXAMPLE = """{{
    "bios": {{
        "uefi": false,
        "version": 1
    }},
    "cpu": {{
        "options": [],
        "sockets": 2,
        "type": "host"
    }},
    "dev": {{
        "bus": "pcie",
        "display": "virtio",
        "input": "standard",
        "iommu": true,
        "sound": true
    }},
    "drives": {{
        "disk0": {{
            "file": "disk0.raw",
            "format": "raw",
            "index": 0,
            "type": "virtio"
        }}
    }},
    "memory": {{
        "reserve": false,
        "size": 1024
    }},
    "network": {{
        "eth0": {{
            "type": "virtio"
        }}
    }},
    "vm": {{
        "accel": "kvm",
        "debug": false,
        "spice": false,
        "name": "ExampleVM",
        "type": "q35"
    }},
    "vmid": {vmid}
}}
"""


def all(args):
    return do_all(args, args.all_sleep, args.all_wake, args.all_stop)


def default(args):
    return list_vms(args)


def list_vms(args):
    try:
        r = send_message(
            args.socket, HOOK_HYDRA, (HOOK_HYDRA, "vms"), 5, {"type": HYDRA_STATUS}
        )
    except OSError as err:
        return print_error("Error retriving VM list!", err)
    if r.is_error():
        return print_error(f"Error retriving VM list: {r.error}!")
    if not args.dmenu:
        print(f'{"Name":20}{"VMID":8}{"Process ID":12}{"Status":12}\n{"="*50}')
    if not isinstance(r.vms, list) or len(r.vms) == 0:
        return
    for vm in r.vms:
        if args.dmenu:
            print(
                f'{_resolve(vm["vmid"], vm["path"])},{vm["status"].title()},{vm["vmid"]}'
            )
            continue
        print(
            f'{_resolve(vm["vmid"], vm["path"]):20}{vm["vmid"]:<8}'
            f'{vm["pid"] if vm["pid"] is not None else EMPTY:<12}{vm["status"].title()}'
        )
    del r
    return True


def tokenize(args):
    if args.command is None:
        return list_vms(args)
    c = args.command.lower()
    if c == "list" or args.list:
        return list_vms(args)
    if c == "dir" or c == "directory" or args.directory:
        if len(args.args) >= 1:
            args.directory = args.args[0]
        return directory(args)
    if c == "example" or args.example:
        return example(args, False)
    if c == "schema" or args.schema:
        return example(args, True)
    if len(args.args) >= 1:
        vm = _resolve_vm(args, args.args[0])
    else:
        vm = _resolve_vm(args)
    if c == "start" or args.start:
        return start(args, vm)
    if c == "stop" or args.stop:
        if vm is None or args.all_stop or args.all_force:
            return do_all(args, False, False, True)
        return stop(args, vm)
    if c == "tap" or args.tap:
        return tap(args, vm)
    if c == "web" or args.connect_web:
        return connect(args, vm)
    if c == "vnc" or c == "v" or args.connect_vnc:
        return connect(args, vm, True)
    if c == "spice" or c == "s" or args.connect_spice:
        return connect(args, vm, spice=True)
    if c == "view" or c == "connect" or args.connect_spice:
        return connect(args, vm, spice=True)
    if c == "ip" or args.ga_ip:
        return ip(args, vm)
    if c == "ping" or args.ga_ping:
        return ping(args, vm)
    if c == "wake" or args.wake:
        if vm is None or args.all_wake:
            return do_all(args, False, True, False)
        return sleep_vm(args, False, vm)
    if c == "sleep" or args.sleep:
        if vm is None or args.all_sleep:
            return do_all(args, True, False, False)
        return sleep_vm(args, True, vm)
    if c == "usb" or args.usb_add or args.usb_delete:
        n = EMPTY
        o = EMPTY
        if len(args.args) >= 2:
            o = args.args[1].lower()
        if len(args.args) >= 3:
            n = args.args[2].lower()
        if len(n) > 0:
            args.usb_name = n
        if o not in HYDRA_USB_COMMANDS and not (args.usb_delete or args.usb_add):
            if len(o) > 0:
                args.usb_name = o
            else:
                usb_list(args, vm)
        if len(n) == 0 and (args.usb_list or o == "list"):
            usb_list(args, vm)
        elif o == "clean" or o == "clear":
            usb_clean(args, vm)
        else:
            usb(args, (o == "remove" or o == "del") or args.usb_delete, vm)
        del n
        del o
    elif c == "alias" or c == "name" or args.alias_add or args.alias_delete:
        n = EMPTY
        o = EMPTY
        if len(args.args) >= 2:
            o = args.args[1].lower()
        if len(args.args) >= 3:
            n = args.args[2].lower()
        if o == "add" and len(n) > 0:
            args.alias_add = n
        elif (o == "delete" or o == "del") and len(n) > 0:
            args.alias_delete = n
        elif len(o) > 0 and len(n) == 0:
            args.alias_add = o
        alias(args, vm)
        del n
        del o
    else:
        return print_error(f'Invalid command "{c}"!')
    del c
    return True


def directory(args):
    try:
        send_message(
            args.socket,
            HOOK_HYDRA,
            payload={
                "user": True,
                "type": HYDRA_USER_DIRECTORY,
                "directory": args.directory,
            },
        )
    except OSError as err:
        return print_error("Error setting VM search directory!", err)
    return True


def _print_usb(usbs):
    d = get_usb()
    print(f'{"ID":3}{"USB-ID":12}{"Description":20}\n{"=" * 50}')
    for i, e in usbs.items():
        if e not in d:
            print(f'{i:3}{e:<12}{"USB Device":<20}')
            continue
        print(f'{i:3}{e:<12}{d[e]["name"]:<20}')
    del d


def ip(args, vm=None):
    if vm is None:
        vm = _resolve_vm(args)
    vm["type"] = HYDRA_GA_IP
    try:
        r = send_message(args.socket, HOOK_HYDRA, HOOK_HYDRA, 5, vm)
    except OSError as err:
        return print_error("Error retriving IP from VM!", err)
    if r.is_error():
        return print_error(f"Error retriving IP from VM: {r.error}!")
    print(f'{_resolve(r.vmid, r.path)} - {r.status.title()}\n{"="*26}')
    if "ips" in r and isinstance(r["ips"], list):
        for e in r["ips"]:
            print(e)
    del r
    del vm
    return True


def _resolve_usb(args):
    if not args.usb_name:
        return
    d = get_usb()
    s = str(args.usb_name).lower()
    if len(s) == 9 and ":" in s and s in d:
        args.usb_vendor = s[:4]
        args.usb_product = s[5:]
        del s
        del d
        return
    m = list()
    for e in d.values():
        if s not in e["name"].lower():
            continue
        m.append(e)
    del d
    c = None
    if len(m) > 1:
        print(f'Multiple devices match "{s}", please select from the list:')
        try:
            while True:
                print(f'{"#":3}{"USB-ID":12}{"Description":20}\n{"="*50}')
                for x in range(0, len(m)):
                    i = f'{m[x]["vendor"]}:{m[x]["product"]}'
                    print(f'{x:3}{i:<12}{m[x]["name"]:<20}')
                    del i
                i = input("Index [Default 0, Cancel 'q']: ")
                if i is None or len(i) == 0:
                    c = m[0]
                    break
                if len(i) == 1 and i.lower() == "q":
                    return print_error("USB operation aborted.")
                try:
                    n = int(i, 10)
                    if 0 <= n < len(n):
                        c = m[n]
                        break
                    del n
                except ValueError:
                    pass
                print(f'Invalid index "{i}"!\n')
                del i
        except KeyboardInterrupt:
            print()
            return print_error("USB operation aborted.")
    elif len(m) == 1:
        c = m[0]
    else:
        return print_error(f'Could not find any USB devices matching "{s}"!')
    del m
    del s
    print(
        f'\nSelected Device "{c["vendor"]}:{c["product"]} - {c["name"]}" '
        f"based on search results."
    )
    args.usb_vendor = c["vendor"]
    args.usb_product = c["product"]
    del c


def tap(args, vm=None):
    if vm is None:
        vm = _resolve_vm(args)
    vm["type"] = HYDRA_TAP
    vm["force"] = args.stop_force
    vm["timeout"] = args.timeout
    try:
        r = send_message(args.socket, HOOK_HYDRA, HOOK_OK, 5, vm)
    except OSError as err:
        return print_error("Error tapping VM!", err)
    if r.is_error():
        return print_error(f"Error tapping VM: {r.error}!")
    del r
    del vm
    return True


def stop(args, vm=None):
    if vm is None:
        vm = _resolve_vm(args)
    vm["type"] = HYDRA_STOP
    vm["force"] = args.stop_force
    vm["timeout"] = args.timeout
    try:
        r = send_message(args.socket, HOOK_HYDRA, HOOK_HYDRA, 5, vm)
    except OSError as err:
        return print_error("Error stopping VM!", err)
    if r.is_error():
        return print_error(f"Error stopping VM: {r.error}!")
    print(f"{_resolve(r.vmid, r.path)} - {r.status.title()}!")
    del r
    del vm
    return True


def ping(args, vm=None):
    if vm is None:
        vm = _resolve_vm(args)
    vm["type"] = HYDRA_GA_PING
    try:
        r = send_message(args.socket, HOOK_HYDRA, HOOK_HYDRA, 5, vm)
    except OSError as err:
        return print_error("Error pinging VM!", err)
    if r.is_error():
        return print_error(f"Error pinging VM: {r.error}!")
    m = "Guest Agent Not Running"
    if r.get("ping", False):
        m = "Guest Agent Running"
    print(f"{_resolve(r.vmid, r.path)} - {m}!")
    del r
    del m
    del vm
    return True


def start(args, vm=None):
    if vm is None:
        vm = _resolve_vm(args)
    vm["type"] = HYDRA_START
    try:
        r = send_message(args.socket, HOOK_HYDRA, HOOK_HYDRA, 5, vm)
    except OSError as err:
        return print_error("Error starting VM!", err)
    if r.is_error():
        return print_error(f"Error starting VM: {r.error}!")
    print(f"{_resolve(r.vmid, r.path)} - {r.status.title()}!")
    del r
    del vm
    return True


def alias(args, vm=None):
    if vm is None:
        vm = _resolve_vm(args)
    vm["user"] = True
    if args.alias_add and not args.alias_delete:
        vm["name"] = args.alias_add
        vm["type"] = HYDRA_USER_ADD_ALIAS
    elif args.alias_delete and not args.alias_add:
        vm["name"] = args.alias_delete
        vm["type"] = HYDRA_USER_DELETE_ALIAS
    if "type" not in vm:
        return print_error("An action must be specified!")
    try:
        send_message(args.socket, HOOK_HYDRA, None, 0, vm)
    except OSError as err:
        return print_error("Error adding an alias!", err)
    del vm
    return True


def _resolve(vmid, path):
    if len(NAMES) == 0:
        c = read_json(expandvars(expanduser(CONFIG_CLIENT)), errors=False)
        if isinstance(c, dict) and "hydra" in c:
            if isinstance(c["hydra"], dict) and "aliases" in c["hydra"]:
                for n, f in c["hydra"]["aliases"].items():
                    NAMES[f.lower()] = n.title()
        NAMES["__loaded"] = True
        del c
    n = NAMES.get(path.lower(), None)
    if isinstance(n, str) and len(n) > 0:
        return f"{n} ({vmid})"
    return f"VM({vmid})"


def usb_list(args, vm=None):
    if vm is None:
        vm = _resolve_vm(args)
    vm["type"] = HYDRA_USB_QUERY
    try:
        r = send_message(args.socket, HOOK_HYDRA, HOOK_HYDRA, 5, vm)
    except OSError as err:
        return print_error("Error listing USB devices!", err)
    if r.is_error():
        return print_error(f"Error listing USB devices: {r.error}!")
    d = get_usb()
    if isinstance(r.usb, dict) and len(r.usb) > 0:
        _print_usb(r.usb)
    del r
    del d
    del vm
    return True


def usb_clean(args, vm=None):
    if vm is None:
        vm = _resolve_vm(args)
    vm["type"] = HYDRA_USB_CLEAN
    try:
        r = send_message(args.socket, HOOK_HYDRA, HOOK_HYDRA, 5, vm)
    except OSError as err:
        return print_error("Error removing all USB devices!", err)
    if r.is_error():
        return print_error(f"Error removing all USB devices: {r.error}!")
    print(f"Removed all USB devices from {_resolve(r.vmid, r.path)}.")
    del r
    del vm
    return True


def example(args, schema=False):
    if args.schema or schema:
        print(SCHEMA)
    else:
        n = args.vmid
        if n is None:
            n = args.name
        if n is None and args.command != "example":
            n = args.command
        if n is None:
            n = "[vmid]"
        print(EXAMPLE.format(vmid=n))
        del n
    return True


def _resolve_vm(args, name=None):
    if name == "all":
        return None
    if name is None:
        name = args.name
    if name is None:
        name = args.command
    if name is not None:
        p = get_vm(name, expandvars(expanduser(CONFIG_CLIENT)))
        if p is None:
            try:
                return {"vmid": int(name)}
            except ValueError:
                pass
            return print_error(f'Cannot locate VM "{name}"!')
        return {"path": p}
    if args.command is not None:
        try:
            return {"vmid": int(args.command)}
        except ValueError:
            pass
    if args.vmid is not None:
        try:
            return {"vmid": int(args.vmid)}
        except ValueError as err:
            return print_error("VMID must be an integer!", err)
    print_error("No valid VMID, Path or Name given!")


def usb(args, remove=False, vm=None):
    if vm is None:
        vm = _resolve_vm(args)
    if args.usb_name is not None:
        if (remove or args.usb_delete) and args.usb_name == "all":
            return usb_clean(args, vm)
        _resolve_usb(args)
    elif args.usb_vendor and args.usb_product:
        pass
    elif not (remove or args.usb_delete) or args.usb_id is None:
        return print_error("USB Name, ID or VendorID and ProductID must be specified!")
    if remove or args.usb_delete:
        if args.usb_id is None:
            vm["type"] = HYDRA_USB_QUERY
            try:
                r = send_message(args.socket, HOOK_HYDRA, HOOK_HYDRA, 5, vm)
            except OSError as err:
                return print_error("Error retriving the connected USB devices!", err)
            if r.is_error():
                return print_error(
                    f"Error retriving the connected USB devices: {r.error}!"
                )
            if not isinstance(r.usb, dict) and len(r.usb) == 0:
                return print_error("No USB devices are connected to the VM!")
            v = f"{args.usb_vendor}:{args.usb_product}".lower()
            for i, d in r.usb.items():
                if d.lower() == v:
                    args.usb_id = i
                    break
            del r
            del v
        vm["usb"] = args.usb_id
        vm["type"] = HYDRA_USB_DELETE
    else:
        vm["type"] = HYDRA_USB_ADD
        vm["slow"] = args.usb_slow
        vm["vendor"] = args.usb_vendor
        vm["product"] = args.usb_product
    try:
        r = send_message(args.socket, HOOK_HYDRA, HOOK_HYDRA, 5, vm)
    except OSError as err:
        return print_error("Error performing USB operation!", err)
    if r.is_error():
        return print_error(f"Error performing USB operation: {r.error}!")
    if remove or args.usb_delete:
        print(f'USB Device "ID-{args.usb_id}" removed from {_resolve(r.vmid, r.path)}!')
    elif isinstance(r.usb, dict) and len(r.usb) > 0:
        _print_usb(r.usb)
    del r
    del vm
    return True


def sleep_vm(args, do_sleep=True, vm=None):
    if vm is None:
        vm = _resolve_vm(args)
    if do_sleep or args.sleep:
        vm["type"] = HYDRA_SLEEP
    elif not do_sleep or args.wake:
        vm["type"] = HYDRA_WAKE
    try:
        r = send_message(args.socket, HOOK_HYDRA, HOOK_HYDRA, 5, vm)
    except OSError as err:
        return print_error(
            f"Error {'sleeping' if do_sleep or args.sleep else 'waking'} the VM!", err
        )
    if r.is_error():
        return print_error(
            f"Error {'sleeping' if do_sleep or args.sleep else 'waking'} the VM: {r.error}!"
        )
    print(f"{_resolve(r.vmid, r.path)} - {r.status.title()}")
    del r
    del vm
    return True


def do_all(args, do_sleep, do_wake, do_stop):
    q = {"all": True}
    if do_sleep and not (do_wake or do_stop):
        q["type"] = HYDRA_SLEEP
    elif do_wake and not (do_sleep or do_stop):
        q["type"] = HYDRA_WAKE
    elif do_stop or args.all_force and not (do_sleep or do_wake):
        if args.all_force:
            q["force"] = True
        q["type"] = HYDRA_STOP
    if "type" not in q:
        return print_error("An action must be specified!")
    try:
        r = send_message(args.socket, HOOK_HYDRA, (HOOK_HYDRA, "vms"), 5, q)
    except OSError as err:
        return print_error('Error attempting a "set all" operation!', err)
    if r.is_error():
        return print_error(f'Error attempting a "set all" operation: {r.error}')
    del q
    print(f'{"Name":20}{"VMID":8}{"Process ID":12}{"Status":12}\n{"="*50}')
    if not isinstance(r.vms, list) or len(r.vms) == 0:
        return True
    for vm in r.vms:
        print(
            f'{_resolve(vm["vmid"], vm["path"]):20}{vm["vmid"]:<8}'
            f'{vm["pid"] if vm["pid"] is not None else EMPTY:<12}{vm["status"].title():<12}'
        )
    del r
    return True


def connect(args, vm=None, vnc=False, spice=False):
    if vm is None:
        vm = _resolve_vm(args)
    vm["type"] = HYDRA_START
    try:
        r = send_message(args.socket, HOOK_HYDRA, HOOK_HYDRA, 5, vm)
    except OSError as err:
        return print_error("Error starting the VM!", err)
    if r.is_error():
        return print_error(f"Error starting the VM: {r.error}!")
    if fork() != 0:
        return True
    if r.status == "waiting":
        sleep(2)
    if args.connect_vnc or vnc:
        try:
            run(
                [
                    "/usr/bin/vncviewer",
                    "FullscreenSystemKeys=0",
                    "Shared=1",
                    f"{DIRECTORY_HYDRA}/{r.vmid}.vnc",
                ]
            )
        except OSError as err:
            return print_error("Error connecting to the VM!", err)
        del r
        del vm
        return True
    if args.connect_spice or spice:
        try:
            run(
                [
                    "/usr/bin/spicy",
                    f"--title=VM{r.vmid}",
                    f"--uri=spice+unix:///var/run/smd/hydra/{r.vmid}.spice",
                ]
            )
        except OSError as err:
            return print_error("Error connecting to the VM!", err)
        del r
        del vm
        return True
    try:
        run(
            [
                "/usr/bin/surf",
                "-BDfgIKmnSTxc",
                "/dev/null",
                f"http://hydra:8600/?path=websockify?token=VM{r.vmid}&scaling=local&autoconnect=true",
            ]
        )
    except OSError as err:
        return print_error("Error connecting to the VM!", err)
    del r
    del vm
    return True
