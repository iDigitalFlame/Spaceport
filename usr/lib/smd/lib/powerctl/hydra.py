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

# PowerCTL Module: Hydra
#   Command line user module to configure and control Hydra VMs.

from time import sleep
from os import fork, execl
from os.path import basename
from lib.util import nes, num
from lib.util.file import read_json, expand
from lib.shared.hydra import load_vm, get_devices
from lib import print_error, send_message, check_error
from lib.constants import (
    EMPTY,
    HYDRA_TAP,
    HOOK_HYDRA,
    HYDRA_STOP,
    HYDRA_WAKE,
    HYDRA_GA_IP,
    HYDRA_SLEEP,
    HYDRA_START,
    HYDRA_STATUS,
    HYDRA_RESTART,
    HYDRA_GA_PING,
    HYDRA_USB_ADD,
    HYDRA_HIBERNATE,
    HYDRA_USB_QUERY,
    HYDRA_USB_CLEAN,
    HYDRA_USB_DELETE,
    HYDRA_USER_DIRECTORY,
    HYDRA_USER_ADD_ALIAS,
    HYDRA_USER_DELETE_ALIAS,
)
from lib.constants.config import (
    HYDRA_DIR,
    CONFIG_CLIENT,
    HYDRA_EXEC_VNC,
    HYDRA_EXEC_SPICE,
    TIMEOUT_SEC_MESSAGE,
)

_CACHE = dict()
_SCHEMA = """# HydraVM Schema v2-release

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
        for owner and group (ie: chmod 0755) in order to be executed.

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
_EXAMPLE = """{{
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


def _usb(e):
    print(f'{"ID":>4} {"Device ID":12}{"Description":20}\n{"=" * 50}')
    if not isinstance(e, dict) or len(e) == 0:
        return
    d = get_devices()
    for k, v in e.items():
        if k not in d:
            print(f'{v:4} {k:<12}{"USB Device":<20}')
        else:
            print(f"{v:4} {k:<12}{d[k].name:<20}")
    del d


def _vm(x, p):
    global _CACHE
    if len(_CACHE) == 0:
        d = read_json(expand(CONFIG_CLIENT), errors=False)
        if isinstance(d, dict) and "hydra" in d and isinstance(d["hydra"], dict):
            i = d["hydra"].get("aliases")
            if isinstance(i, dict) and len(i) > 0:
                for k, v in i.items():
                    _CACHE[v.lower()] = k.title()
            del i
        _CACHE["__loaded"] = True
        del d
    if nes(p):
        n = _CACHE.get(p.lower())
        if isinstance(n, str) and len(n) > 0:
            return f"{n} ({x})"
    return f"VM({x})"


def _usb_vet(args):
    d, n = get_devices(), args.usb_name.lower()
    if len(n) == 9 and ":" in n and n in d:
        args.usb_vendor, args.usb_product = n[:4], n[5:]
        del n, d
        return
    m = list()
    for i in d.values():
        if n not in i.name.lower():
            continue
        m.append(i)
    del d
    c = None
    if len(m) > 1:
        c = _usb_prompt(n, m)
    elif len(m) == 1:
        c = m[0]
    else:
        return print_error(f'Cannot find any USB devices matching "{n}"!')
    del m, n
    print(
        f'\nSelected Device "{c.vendor}:{c.product} - {c.name}" based on search results.\n'
    )
    args.usb_vendor, args.usb_product = c.vendor, c.product
    del c


def _get_check(args, vm):
    if vm is not None:
        return vm
    return _get_vm(args)


def _get_vm(args, name=None):
    if name == "all":
        return None
    n = name
    if not nes(n):
        n = args.name
    if not nes(n):
        n = args.command
    if nes(n):
        f = load_vm(n, expand(CONFIG_CLIENT))
        if not nes(f):
            try:
                return {"vmid": num(n, False, False)}
            except ValueError:
                pass
            return print_error(f'Cannot find the VM "{n}"!')
        return {"file": f}
    del n
    try:
        return {"vmid": num(name, False, False)}
    except ValueError:
        pass
    if args.command is not None:
        try:
            return {"vmid": num(args.command, False, False)}
        except ValueError:
            pass
    if args.vmid is not None:
        try:
            return {"vmid": num(args.vmid, False, False)}
        except ValueError as err:
            return print_error(
                "Cannot use an invalid VMID (it must be a positive number)!", err
            )
    return print_error("Cannot find VM: no valid VMID, path or alias given!")


def _usb_prompt(name, matches):
    print(f'Multiple devices match "{name}", please select from the list:')
    try:
        while True:
            print(f'{"#":>4} {"Device ID":12}{"Description":20}\n{"="*50}')
            for x in range(0, len(matches)):
                v = f"{matches[x].vendor}:{matches[x].product}"
                print(f"{x:4} {v:<12}{matches[x].name:<20}")
                del v
            r = input("Selected Index [Default 0, Cancel 'q']: ")
            if not nes(r):
                return matches[0]
            if len(r) == 1 and (r[0] == "q" or r[0] == "Q"):
                return print_error("USB selection aborted.")
            try:
                i = num(r)
            except ValueError:
                print(f'Invalid number value "{r}"!\n')
                continue
            if 0 <= i < len(matches):
                return matches[i]
            print(f'Invalid index value "{i}"!\n')
            del i, r
    except KeyboardInterrupt:
        print()
        return print_error("USB selection aborted.")


def _all(args, cmd, force=False):
    p = {
        "all": True,
        "type": cmd,
        "force": True if args.all_force or args.all_reset or force else False,
    }
    try:
        r = send_message(
            args.socket, HOOK_HYDRA, (HOOK_HYDRA, "vms"), TIMEOUT_SEC_MESSAGE, p
        )
    except OSError as err:
        return print_error('Cannot perform a "set all" operation!', err)
    del p
    check_error(r, 'Cannot perform a "set all" operation')
    print(f'{"Name":20}{"VMID":8}{"Process ID":12}{"Status":12}\n{"="*50}')
    if not isinstance(r.vms, list) or len(r.vms) == 0:
        return True
    for x in r.vms:
        print(
            f'{_vm(x["vmid"], x.get("path")):20}{x["vmid"]:<8}'
            f'{x["pid"] if x["pid"] is not None else EMPTY:<12}{x["status"].title():<12}'
        )
    del r
    return True


def user_directory(args):
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
        return print_error("Cannot set the VM search directory!", err)
    return True


def user_alias(args, vm=None):
    vm = _get_check(args, vm)
    vm["user"] = True
    if nes(args.alias_add) and not nes(args.alias_delete):
        vm["name"], vm["type"] = args.alias_add, HYDRA_USER_ADD_ALIAS
    elif nes(args.alias_delete) and not nes(args.alias_add):
        vm["name"], vm["type"] = args.alias_delete, HYDRA_USER_DELETE_ALIAS
    if "type" not in vm:
        return print_error('Cannot perform operation: a "type" must be specified!')
    try:
        send_message(args.socket, HOOK_HYDRA, payload=vm)
    except OSError as err:
        if vm["type"] == HYDRA_USER_ADD_ALIAS:
            return print_error("Cannot add an alias!", err)
        return print_error("Cannot remove an alias!", err)
    del vm
    return True


def example(args, schema=False):
    if args.schema or schema:
        print(_SCHEMA)
    else:
        n = args.vmid
        if not nes(n):
            n = args.name
        if not nes(n) and args.command != "example":
            n = args.command
        if not nes(n):
            n = "[vmid]"
        print(_EXAMPLE.format(vmid=n))
        del n
    return True


def vm_all(args):
    if args.all_wake or args.wake:
        return _all(args, HYDRA_WAKE)
    if args.all_sleep or args.sleep:
        return _all(args, HYDRA_SLEEP)
    if args.all_reset or args.reset:
        return _all(args, HYDRA_RESTART, True)
    if args.all_restart or args.restart:
        return _all(args, HYDRA_RESTART)
    if args.all_hibernate or args.hibernate:
        return _all(args, HYDRA_HIBERNATE)
    if args.all_stop or args.stop or args.all_force:
        return _all(args, HYDRA_STOP)
    return print_error("invalid or unknown arguments combonation!")


def default(args):
    return vm_list(args)


def vm_list(args):
    try:
        r = send_message(
            args.socket,
            HOOK_HYDRA,
            (HOOK_HYDRA, "vms"),
            TIMEOUT_SEC_MESSAGE,
            {"type": HYDRA_STATUS},
        )
    except Exception as err:
        return print_error("Cannot retrive the VM list!", err)
    check_error(r, "Cannot retrive the VM list!")
    if not args.dmenu:
        print(f'{"Name":20}{"VMID":8}{"Process ID":12}{"Status":12}\n{"="*50}')
    if not isinstance(r.vms, list) or len(r.vms) == 0:
        return
    r.vms.sort(key=lambda x: x["vmid"])
    for x in r.vms:
        if args.dmenu:
            print(f'{x["vmid"]}|{x["status"].title()}|{_vm(x["vmid"], x["file"])}')
            continue
        print(
            f'{_vm(x["vmid"], x["file"]):20}{x["vmid"]:<8}'
            f'{x["pid"] if x["pid"] is not None else EMPTY:<12}{x["status"].title()}'
        )
    del r
    return True


def tokenize(args):
    if not nes(args.command):
        return vm_list(args)
    c = args.command.lower()
    if c == "list" or args.list:
        return vm_list(args)
    if c == "dir" or c == "directory" or nes(args.directory):
        if not nes(args.directory) and len(args.args) >= 1:
            args.directory = args.args[0]
        return user_directory(args)
    if c == "example" or args.example:
        return example(args, False)
    if c == "schema" or args.schema:
        return example(args, True)
    if len(args.args) >= 1:
        vm = _get_vm(args, args.args[0])
    else:
        vm = _get_vm(args)
    if c == "start" or args.start:
        return vm_start(args, vm)
    if c == "reboot" or c == "restart" or args.restart:
        if vm is None or args.all_restart or args.args[0] == "all":
            return _all(args, HYDRA_RESTART)
        return vm_restart(args, vm)
    if c == "reset" or args.reset:
        if vm is None or args.all_reset or args.args[0] == "all":
            return _all(args, HYDRA_RESTART, True)
        return vm_restart(args, vm, True)
    if c == "hibernate" or args.hibernate:
        if vm is None or args.all_hibernate or args.args[0] == "all":
            return _all(args, HYDRA_HIBERNATE)
        return vm_hibernate(args, vm)
    if c == "stop" or c == "shutdown" or args.stop:
        if vm is None or args.all_stop or args.all_force or args.args[0] == "all":
            return _all(args, HYDRA_STOP)
        return vm_stop(args, vm)
    if c == "tap" or args.tap:
        return vm_tap(args, vm)
    if c == "vnc" or c == "v" or args.connect_vnc:
        return vm_connect(args, vm, True)
    if c == "spice" or c == "s" or c == "view" or c == "connect" or args.connect:
        return vm_connect(args, vm)
    if c == "ip" or args.ga_ip:
        return vm_ip(args, vm)
    if c == "ping" or args.ga_ping:
        return vm_ping(args, vm)
    if c == "wake" or c == "resume" or args.wake:
        if vm is None or args.all_wake or args.args[0] == "all":
            return _all(args, HYDRA_WAKE)
        return vm_sleep(args, True, vm)
    if c == "sleep" or c == "suspend" or args.sleep:
        if vm is None or args.all_sleep or args.args[0] == "all":
            return _all(args, HYDRA_SLEEP)
        return vm_sleep(args, False, vm)
    if c == "alias" or c == "name" or args.alias_add or args.alias_delete:
        o = args.args[1].lower() if len(args.args) >= 2 else None
        n = args.args[2].lower() if len(args.args) >= 3 else None
        if nes(o) and nes(n) and o == "add":
            args.alias_add = n
        elif nes(o) and nes(n) and (o == "delete" or o == "del"):
            args.alias_delete = n
        elif nes(o) and not nes(n):
            args.alias_add = o
        del n, o
        return user_alias(args, vm)
    if c == "usb" or args.usb_add or args.usb_delete:
        o = args.args[1].lower() if len(args.args) >= 2 else None
        n = args.args[2].lower() if len(args.args) >= 3 else None
        if nes(n):
            args.usb_name = n
        if nes(o) and not (args.usb_delete or args.usb_add):  # and o in :
            if o != "add" and o != "del" and o != "list" and o != "remove":
                args.usb_name = o
        if not nes(o):
            return vm_usb_list(args, vm)
        if not nes(n) and (args.usb_list or o == "list"):
            return vm_usb_list(args, vm)
        if o == "clean" or o == "clear":
            return vm_usb_clean(args, vm)
        vm_usb(args, (o == "remove" or o == "del") or args.usb_delete, vm)
        del n, o
        return
    return print_error(f'invalid or unknown command "{c}"!')


def vm_ip(args, vm=None):
    vm = _get_check(args, vm)
    vm["type"] = HYDRA_GA_IP
    try:
        r = send_message(args.socket, HOOK_HYDRA, HOOK_HYDRA, TIMEOUT_SEC_MESSAGE, vm)
    except OSError as err:
        return print_error("Cannot retrive the IP from the VM!", err)
    check_error(r, "Cannot retrive the IP from the VM")
    print(
        f'{_vm(r.vmid, r.file)} - {r.status.title()}\n\n{"Interface":16}IP Address\n{"="*32}'
    )
    a = r.get("ips")
    del r
    if not isinstance(a, list) or len(a) == 0:
        return True
    for i in a:
        print(f'{i["name"]:16}{i["ip"]}')
    del a, vm
    return True


def vm_tap(args, vm=None):
    vm = _get_check(args, vm)
    vm["type"], vm["force"], vm["timeout"] = HYDRA_TAP, args.stop_force, args.timeout
    try:
        r = send_message(
            args.socket, HOOK_HYDRA, (HOOK_HYDRA, True), TIMEOUT_SEC_MESSAGE, vm
        )
    except OSError as err:
        return print_error("Cannot signal ACPI shutdown to the VM!", err)
    check_error(r, "Cannot signal ACPI shutdown to the VM")
    del r, vm
    return True


def vm_stop(args, vm=None):
    vm = _get_check(args, vm)
    vm["type"], vm["force"], vm["timeout"] = HYDRA_STOP, args.stop_force, args.timeout
    try:
        r = send_message(args.socket, HOOK_HYDRA, HOOK_HYDRA, TIMEOUT_SEC_MESSAGE, vm)
    except OSError as err:
        return print_error("Cannot stop the VM!", err)
    check_error(r, "Cannot stop the VM")
    print(f"{_vm(r.vmid, r.file)} - {r.status.title()}!")
    del r, vm
    return True


def vm_ping(args, vm=None):
    vm = _get_check(args, vm)
    vm["type"] = HYDRA_GA_PING
    try:
        r = send_message(args.socket, HOOK_HYDRA, HOOK_HYDRA, TIMEOUT_SEC_MESSAGE, vm)
    except OSError as err:
        return print_error("Cannot ping the VM!", err)
    check_error(r, "Cannot ping the VM")
    print(
        f'{_vm(r.vmid, r.file)} - Guest Agent {"" if r.get("ping", False) else "not "}Running!'
    )
    del r, vm
    return True


def vm_start(args, vm=None):
    vm = _get_check(args, vm)
    vm["type"] = HYDRA_START
    try:
        r = send_message(args.socket, HOOK_HYDRA, HOOK_HYDRA, TIMEOUT_SEC_MESSAGE, vm)
    except OSError as err:
        return print_error("Cannot start the VM!", err)
    check_error(r, "Cannot start the VM")
    print(f"{_vm(r.vmid, r.file)} - {r.status.title()}!")
    del r, vm
    return True


def vm_usb_list(args, vm=None):
    vm = _get_check(args, vm)
    vm["type"] = HYDRA_USB_QUERY
    try:
        r = send_message(args.socket, HOOK_HYDRA, HOOK_HYDRA, TIMEOUT_SEC_MESSAGE, vm)
    except OSError as err:
        return print_error("Cannot list USB devices!", err)
    check_error(r, "Cannot list USB devices")
    _usb(r.usb)
    del r, vm
    return True


def vm_usb_clean(args, vm=None):
    vm = _get_check(args, vm)
    vm["type"] = HYDRA_USB_CLEAN
    try:
        r = send_message(args.socket, HOOK_HYDRA, HOOK_HYDRA, TIMEOUT_SEC_MESSAGE, vm)
    except OSError as err:
        return print_error("Cannot remove all USB devices!", err)
    check_error(r, "Cannot remove all USB devices")
    print(f"Removed all USB devices from {_vm(r.vmid, r.file)}.")
    del r, vm
    return True


def vm_hibernate(args, vm=None):
    vm = _get_check(args, vm)
    vm["type"] = HYDRA_HIBERNATE
    try:
        r = send_message(
            args.socket, HOOK_HYDRA, (HOOK_HYDRA, True), TIMEOUT_SEC_MESSAGE, vm
        )
    except OSError as err:
        return print_error("Cannot hibernate the VM!", err)
    check_error(r, "Cannot hibernate the VM")
    del r, vm
    return True


def vm_usb(args, remove=False, vm=None):
    vm = _get_check(args, vm)
    if nes(args.usb_name):
        if args.usb_name == "all" and (remove or args.usb_delete):
            return vm_usb_clean(args, vm)
        # NOTE(dij): We already checked the name so we're good.
        _usb_vet(args)
    elif nes(args.usb_vendor) and nes(args.usb_product):
        pass
    elif not (remove or args.usb_delete) or isinstance(args.usb_id, int):
        return print_error("USB name, ID or vendor and product must be specified!")
    if remove or args.usb_delete:
        if not isinstance(args.usb_id, int):
            vm["type"] = HYDRA_USB_QUERY
            try:
                r = send_message(
                    args.socket, HOOK_HYDRA, HOOK_HYDRA, TIMEOUT_SEC_MESSAGE, vm
                )
            except OSError as err:
                return print_error("Cannot retrive the connected USB devices!", err)
            check_error(r, "Cannot retrive the connected USB devices")
            if not isinstance(r.usb, dict) or len(r.usb) == 0:
                return print_error("No USB devices are connected to the VM!")
            args.usb_id = r.usb.get(f"{args.usb_vendor}:{args.usb_product}".lower())
            del r
        if not isinstance(args.usb_id, int) or args.usb_id <= 0:
            return print_error("Missing or invalid USB ID!")
        vm["usb"], vm["type"] = args.usb_id, HYDRA_USB_DELETE
    else:
        vm["type"], vm["slow"] = HYDRA_USB_ADD, args.usb_slow
        vm["vendor"], vm["product"] = args.usb_vendor, args.usb_product
    try:
        r = send_message(args.socket, HOOK_HYDRA, HOOK_HYDRA, 5, vm)
    except OSError as err:
        return print_error("Cannot perform USB operation!", err)
    check_error(r, "Cannot perform USB operation")
    if remove or args.usb_delete:
        print(f'USB Device "ID-{args.usb_id}" was removed from {_vm(r.vmid, r.file)}!')
    else:
        _usb(r.usb)
    del r, vm
    return True


def vm_sleep(args, wake=False, vm=None):
    vm = _get_check(args, vm)
    if args.wake and args.sleep:
        return print_error('"resume" and "suspend" cannot be used at the same time!')
    w = wake
    if args.wake:
        w = True
    elif args.sleep:
        w = False
    vm["type"] = HYDRA_WAKE if w else HYDRA_SLEEP
    try:
        r = send_message(args.socket, HOOK_HYDRA, HOOK_HYDRA, TIMEOUT_SEC_MESSAGE, vm)
    except OSError as err:
        return print_error(f'Cannot {"resume" if w else "suspend"} the VM!', err)
    check_error(r, f'Cannot {"resume" if w else "suspend"} the VM')
    print(f"{_vm(r.vmid, r.file)} - {r.status.title()}")
    del r, w, vm
    return True


def vm_connect(args, vm=None, vnc=False):
    vm = _get_check(args, vm)
    vm["type"] = HYDRA_START
    try:
        r = send_message(args.socket, HOOK_HYDRA, HOOK_HYDRA, TIMEOUT_SEC_MESSAGE, vm)
    except OSError as err:
        return print_error("Cannot start the VM!", err)
    check_error(r, "Cannot start the VM")
    del vm
    if not args.no_fork and fork() != 0:
        return True
    if r.status == "waiting":
        sleep(2)
    if args.connect_vnc or vnc:
        try:
            execl(
                HYDRA_EXEC_VNC,
                basename(HYDRA_EXEC_VNC),
                "FullscreenSystemKeys=0",
                "Shared=1",
                f"{HYDRA_DIR}/{r.vmid}.vnc",
            )
        except OSError as err:
            return print_error("Cannot connect to the VM via VNC!", err)
        del r
        return True
    try:
        execl(
            HYDRA_EXEC_SPICE,
            basename(HYDRA_EXEC_SPICE),
            f"--title=VM{r.vmid}",
            f"--uri=spice+unix:///var/run/smd/hydra/{r.vmid}.spice",
        )
    except OSError as err:
        return print_error("Cannot connect to the VM via Spice!", err)
    del r
    return True


def vm_restart(args, vm=None, reset=False):
    vm = _get_check(args, vm)
    vm["type"] = HYDRA_RESTART
    vm["force"] = reset or args.reset
    try:
        r = send_message(
            args.socket, HOOK_HYDRA, (HOOK_HYDRA, True), TIMEOUT_SEC_MESSAGE, vm
        )
    except OSError as err:
        return print_error("Cannot hibernate the VM!", err)
    check_error(r, "Cannot hibernate the VM")
    del r, vm
    return True
