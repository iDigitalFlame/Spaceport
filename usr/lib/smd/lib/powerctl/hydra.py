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

# PowerCTL Module: Hydra
#   Command line user module to configure and control Hydra VMs.

from time import sleep
from uuid import uuid4
from os import fork, execl
from os.path import basename
from datetime import datetime
from lib.util import nes, num
from lib.util.file import expand, read_json
from socket import AF_UNIX, SOCK_STREAM, socket
from lib import check_error, print_error, send_message
from lib.shared.hydra import load_vm, get_devices, get_device_name, valid_snap_name
from lib.constants.config import (
    HYDRA_DIR,
    CONFIG_CLIENT,
    HYDRA_EXEC_VNC,
    HYDRA_EXEC_SPICE,
    TIMEOUT_SEC_MESSAGE,
)
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
    HYDRA_GA_PING,
    HYDRA_RESTART,
    HYDRA_USB_ADD,
    HYDRA_HIBERNATE,
    HYDRA_SNAP_LIST,
    HYDRA_SNAP_TAKE,
    HYDRA_USB_CLEAN,
    HYDRA_USB_QUERY,
    HYDRA_SEND_INPUT,
    HYDRA_USB_DELETE,
    HYDRA_SNAP_DELETE,
    HYDRA_USER_RESULT,
    HYDRA_SNAP_RESTORE,
    HYDRA_USER_ADD_ALIAS,
    HYDRA_USER_DIRECTORY,
    HYDRA_USER_DELETE_ALIAS,
)

_CACHE = dict()
_SCHEMA = """# HydraVM Schema v3-release
{
    [BIOS Information, Section is Optional but Recommended]
    "bios": {
        "file"           <String[File Path], Optional>
                          Supported values: Any valid file path.

                          This value allows for supplying a BIOS ROM file that can
                          be used as the BIOS instead of the default QEMU BIOS.

                          This file must exist or the VM will fail during startup
                          and must have the permissions 0o0644 if not owned, or
                          0o0600 if owned.

        "native"         <Boolean, Optional[Default = false]>
                          Enables the ability for the VM to use the Host's SMBIOS
                          data when creating the VM. This will include devices
                          such as fans and temperature sensors.

                          If the SMBIOS file does not exist, this value is ignored.
                          If the SMBIOS file exists, this will ignore the "bios.type"
                          option.

        "secure_boot"    <Boolean, Optional[Default = false]>
                          Enables the secure boot enabled UEFI vars file, if
                          avaliable. Does nothing if "bios.file" is specified or
                          if "uefi" is false.

        "type"           <Integer, Optional[Default = 1]>
                          Supported values: Integer in the range 0 - 41.

                          Specify the BIOS information type. Rarely needed for
                          anything but specific VMs such as MacOS.

        "uefi"           <Boolean, Optional[Default = false]>
                          Enables/Diasables the UEFI BIOS. If false, this disables
                          the ability for secure boot and the "bios.vars" data.

        "vars"           <String[File Path], Optional>
                          Supported values: Any valid file path.

                          This value allows for supplying a UEFI BIOS variable
                          storage file. If not present and UEFI is enabled, this
                          file will be created and added automatically.

                          This file must exist or the VM will fail during startup
                          and must have the permissions 0o0600 and must be directly
                          owned by the user.
    },
    [CPU Information, Required]
    "cpu": {
        "auto_options"   <Boolean, Optional[Default = true]
                          If true, basic CPU flags for maximum performance will be
                          added. This may be modified by "cpu.saveable". The values
                          in "cpu.options" will still be respected when true. For
                          greater control of the CPU flags, this may be set to false
                          to prevent any flags from being added automatically.

        "options"        <List[String], Optional>
                          The value contains a string list of CPU flags that will be
                          added during the Virtual Machine building process.

                          Each value in the list can be prefixed with a '+' or '-'
                          to indicate enabled status. Omitting the prefix infers
                          '+' or enabled. The plus '+' sign can be used to enable
                          a flag (which is the same as omitting the prefix), while
                          the minus '-' sign will disable a flag.

                          Supplied flags that are not valid for the CPU or host will
                          cause the VM to fail during startup.
        "saveable"       <Boolean, Optional[Default = false]>
                          If true, any automatic CPU flags added that prevent snapshots
                          of restoring a VM will be removed and will allow for snapshots
                          of to be created. If false, the VM cannot be snapshotted,
                          but will allow the incompatible CPU flags to be set.

                          This option may be disabled depending on the "cpu.type"
                          value.

        "sockets"        <Integer, Required[Default = 1]>
                          Supported values: Integer greater than zero.

                          Specify the amount of CPU sockets avaliable for the VM.

        "type"           <String, Required[Default = "host"]>
                          Supported values: "host" | "kvm32" | "kvm64" | "qemu32" | "qemu64" |
                           "base" | "Broadwell" | "EPYC" | "Haswell" | [etc...]

                          Type/Model of CPU to use. This may have an impact on performance
                          and the CPU flags that can be used.
    },
    [Device Information, Required]
    "dev": {
        "accel"          <String, Optional[Default = "kvm"]>
                          Supported values: "kvm" | "xen" | "hax" | "hvf" | "nvmm" |
                           "whpx" | "tcg"

                          Specify the accelerator used for the VM. The default value
                          "kvm" will work for most configurations depending on the
                          host hardware and kernel configuration.

        "bus"            <String, Optional[Default = "pcie"]>
                          Supported values: "pci" | "pcie"

                          Specify the underlying BUS technology type. It is recommended
                          to let Hydra pick this one based on the "dev.type" value.

        "display"        <String, Optional[Default = virtio]>
                          Supported values: "std" | "cirrus" | "vmware" | "qxl" | "virtio" |
                           "virtio-vga" | "vga" | "none"

                          Changes the specific type of graphics driver used. This
                          only affects how the display is rendered. This may affect
                          resolution and performance. Setting this to "none" does NOT
                          disable the VNC or spice viewers.

                          Some display drivers may cause issues with some hosts. The
                          "virtio" driver for example, may cause BSODs in Windows VMs.

        "display_count"  <Integer, Optional[Default = 1]>
                          Supported values: Integer greater than zero.

                          Specify the number of virtual displays attached to the
                          VM.

        "input"          <String, Optional[Default = "virtio"]>
                          Supported values: "virtio" | "tablet" | "usb" | "mouse"

                          Specify the input device driver used. The default "virtio"
                          driver will work for most VMs, but the "usb" or "tablet"
                          driver may work better in some specific configurations.

        "iommu"          <Boolean, Optional[Default = true]>
                          If IOMMU is enabled on the host, setting this value to
                          true will expose the native graphics device to the VM.

        "osk"            <String, Optional>
                          The OSK is the "magic" string value used when running
                          a MacOS VM. Setting this value to a non-empty string will
                          add an apple-smc device to the VM with the specified OSK.

        "sound"          <String | Boolean, Optional[Default = true]>
                          Supported values: true | false | "virtio" | "output" |
                           "old" / "compat" | "none"

                          Specify the sound driver used. The default true (boolean)
                          value represents the Intel ICH9 HDA Audio device. Using the
                          "old" or "compat" values will switch the device to use the
                          Intel ICH6 HDA Audio device, for older Operating Systems.
                          The "output" value can be used to disable Line-In (Microphone)
                          input and will only provide an output device. The "virtio"
                          device is a VirtIO audio device that currently does not
                          have Windows driver support, but can used in Linux VMs
                          without additional drivers.

                          Every driver will connect to the launching user's audio
                          session bus on startup.

                          This setting can have a String or Boolean value. The false
                          value is the same as "none".

        [TPM Information, Optional]
        "tpm": {
            "path":      <String[File Path], Optional>
                          Supported values: Any valid file or device path.

                          Specify a path to a TPM device or an emulated TPM storage
                          file.

                          This path must exist or the VM will fail during startup.
                          If the path is a file, it must be owned with the permissions
                          0o0600, otherwise if this is a device the user must be in
                          owning group for the device and it must have the permissions
                          0o0640.

            "software"   <Boolean, Optional[Default = false]>
                          Indicate the "dev.tpm.path" value is a file that represents
                          an emulated TPM device. If this value is not set when the
                          path is a file, VM startup may fail.
        }
        "type"           <String, Required[Default = "q35"]>
                          Supported values: "pc" | "microvm" | "q35" | "pc-i440fx-*" |
                           "pc-q35-*" | "x-remote"

                          Specify the underlying VM hardware type. This value affects
                          the hardware and devices that can be used. Changing this
                          value may cause hardware changes and reconfigurations in
                          VM OS's, especially Windows.
    },
    [Drive Information, Section is Optional but Recommended]
    "drives": {
        <String[Disk ID]>: {
            "direct"     <Boolean, Optional[Default = true]>
                          Specify if access to the underlying backing file or disk
                          can be accessed directly by the VM. Setting this to true
                          will increase the access speed of the selected disk, but
                          may require more resources.

            "discard"    <Boolean, Optional[Default = true]>
                          Specify if the "discard" command may be used on the backing
                          file or disk. This is recommended if the backing store is,
                          or is on a SSD device.

            "file"       <String[File Path], Required>
                          Supported values: Any valid file or device path.

            "format"     <String, Required[Default = "raw"]>
                          Supported values: "raw" | "qcow" | "qcow2" | "vmdk"

                          Specify the disk format type. This will determine the
                          featureset and read/write speeds avaliable.

                          QCOW/QCOW2 disks have the ability to capture and restore
                          snapshots, but are slower than "raw", which has no
                          snapshot operations.

            "index"      <Integer, Optional[Default = 0]>
                          Supported values: Integer greater than zero.

                          Specify the boot order of this drive. The boot order
                          starts from zero (0) and moves upward. Multiple drives
                          may have the same boot order, but their evaluation order
                          will differ depending on VM hardware.

                          If not specified, this value will be calculated to be
                          the last valid boot index.

            "readonly"   <Boolean, Optional[Default = false]>
                          Specify if the backing file or disk is readonly. If
                          the disk type is "iso", "cd" or does not have sufficient
                          permission restrictions, it will automatically be mounted
                          readonly.

            "temp"       <Boolean, Optional[Default = false]>
                          Specify if writes to the disk should be considered temporary.
                          If true, this setting will make any writes to this disk only
                          persist for the VM's running session. Once the VM is completely
                          powered off an removed from the Hydra server state, the disk
                          will still be the same state before launch.

            "type"       <String, Required[Default = "ide"]>
                          Supported values: "ide" | "cd" | "iso" | "sata" | "scsi" |
                           "virtio" | "flash"

                          Specify the bus connection type for this disk. Some bus
                          connection types will not have support without an installed
                          driver.

                          The "iso" and "cd" values are special and will specifically
                          mount the drive as an IDE disk drive in read only mode.

                          The "flash" type will mounted as a "plash" disk instead of
                          a "drive" type.
        }
    },
    [Memory Information, Required]
    "memory": {
        "reserve"        <Boolean, Optional[Default = false]>
                          If true, this will preallocate the VM memory backing "file"
                          in "/dev/hugepages".

                          This provides an increase in memory performance, but
                          requires setup and kernel configuration of the "HugePages"
                          driver. If preallocation fails, the VM will fail during
                          startup.

        "size"           <Integer, Required[Default= 1024]>
                          Supported values: Integer greater than zero.

                          Size of memory allocated for the Virtual Machine in MB.

                          Values larger than the host memory will cause the VM
                          to fail during startup.
    },
    [Network Information, Optional]
    "network": {
        <String[Disk ID]>: {
            "mac"        <String[Mac Address (aa:bb:cc:dd:ee:ff)], Optional[Default = Random]>
                          Supported values: Valid Mac Address in hexadecimal format.

                          Specify the Mac (hardware) Address of this network interface.
                          If not specified, this will be randomally generated.

            "type"       <String, Required[Default = "intel"]>
                          Supported values: "intel" | "virtio" | "vmware" | [other]

                          Specify the network interface driver used. Some interface
                          types will not have support without an installed driver.

                          The "virtio" driver is a para-virtualized driver and provides
                          the best network speed overall, but is the least compatible.
        }
    },
    [Metadata Information, Section is Optional but Recommended]
     "vm": {
        "debug"          <Boolean, Optional[Default = true]>
                          Sets the "debug" flag for the VM. This can be used for
                          debugging VM startup problems. When enabled, the built
                          configuration will be logged before runtime and the
                          stderr/stdout logs will be capture and returned when
                          the VM shuts down.

                          The "--debug" command line flag, enables this option only
                          for the specific VM runtime.

        "name"           <String, Optional>
                          Specify a well-known name to be used by this VM that
                          can be used to identify and select it.

        "spice"          <Boolean, Optional[Default = true]>
                          Enable or diasable the Spice display protocol. If
                          enabled, the Spice viewer can be used, which provides
                          smoother display operation, Host<>VM Copy/Paste and
                          easy USB connectivity. If this is disabled, attempting
                          to use the Spice connection option will fail.

        "uuid"           <String, Optional[Default = Random]>
                          Specify a UUID for internal VM sorting and identification.

                          This does not have to be a valid UUID string, but is
                          recommended to be unique.
    },
    "vmid"               <Integer, Required>
                          Supported values: Unique Integer greater than zero.

                          Callable ID value for the VM. This value must be unique
                          across all local VMs and cannot be less than zero.

                          Similar to the "vm.name" option, this can be used to
                          identify and select the VM.
}"""
_EXAMPLE = """{{
    "bios": {{
        "secure_boot": true,
        "uefi": true,
        "vars": "uefi_vars.fd"
    }},
    "cpu": {{
        "auto_options": false,
        "options": [],
        "saveable": true,
        "sockets": 2,
        "type": "host"
    }},
    "dev": {{
        "bus": "pcie",
        "display": "qxl",
        "display_count": 1,
        "input": "virtio",
        "iommu": true,
        "sound": true,
        "tpm": {{
            "path": "tpm.raw",
            "software": true
        }}
    }},
    "drives": {{
        "disk0": {{
            "file": disk0.qcow2",
            "format": "qcow2",
            "index": 0,
            "type": "virtio"
        }}
    }},
    "memory": {{
        "reserve": false,
        "size": 2048
    }},
    "network": {{
        "en0": {{
            "type": "virtio"
        }}
    }},
    "vm": {{
        "accel": "kvm",
        "debug": false,
        "name": "My New VM",
        "spice": true,
        "type": "q35",
        "uuid": "{uuid}"
    }},
    "vmid": {vmid}
}}"""


def _usb(e):
    print(f'{"ID":>4} {"Device ID":12}{"Description":20}\n{"=" * 60}')
    if not isinstance(e, dict) or len(e) == 0:
        return
    d = get_devices()
    for k, v in e.items():
        if k not in d:
            print(f'{v:4} {k:<12}{get_device_name(k, "USB Device"):<20}')
        else:
            print(f"{v:4} {k:<12}{d[k].name:<20}")
    del d


def _time(n, s):
    if not isinstance(s, (float, int)) or s == 0:
        return ""
    v = datetime.fromtimestamp(s)
    if v.year < 1971:
        return ""
    if n == v:
        return "0s"
    if (n - v).days > 0:
        return v.strftime("%H:%M %m/%d/%y")
    m, y = divmod((n - v).seconds, 60)
    h, m = divmod(m, 60)
    if h > 12:
        if h >= n.hour:
            return v.strftime("%H:%M %m/%d/%y")
        return v.strftime("%H:%M")
    del v
    if h > 0:
        return f"{h}h {m}m"
    if m > 0:
        return f"{m}m {y}s"
    return f"{y}s"


def _vm(x, n, p):
    if nes(n):
        if len(n) > 25:
            return n[0:25]
        return n
    # Ignore the F824 rule for this, as it's being modified but Flake8 can't
    # understand that.
    global _CACHE  # noqa: F824
    if len(_CACHE) == 0:
        d = read_json(expand(CONFIG_CLIENT), False, True)
        if isinstance(d, dict) and "hydra" in d and isinstance(d["hydra"], dict):
            i = d["hydra"].get("aliases")
            if isinstance(i, dict) and len(i) > 0:
                for k, v in i.items():
                    _CACHE[v.lower()] = k.title()
            del i
        _CACHE["__loaded"] = True
        del d
    if nes(p):
        v = _CACHE.get(p.lower())
        if nes(v):
            if len(v) > 23:
                return f"{v[0:23]} ({x})"
            return f"{v} ({x})"
    return f"VM({x})"


def _is_result(r):
    return "error" in r or r.type == HYDRA_USER_RESULT


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
    print(f'\nSelected Device "{c.name}" based on search results.\n')
    args.usb_vendor, args.usb_product = c.vendor, c.product
    del c


def _get_check(args, vm):
    if vm is not None:
        return vm
    return _get_vm(args)


def _print_snaps(snaps, sel):
    if not isinstance(snaps, list) or len(snaps) == 0:
        return
    n = datetime.now()
    if sel == snaps[0]["name"]:
        print(
            f' - *{snaps[0]["name"]} - {_time(n, snaps[0]["date"])} [Base Snapshot] [You are Here]'
        )
    else:
        print(f' - {snaps[0]["name"]} - {_time(n, snaps[0]["date"])} [Base Snapshot]')
    if len(snaps) == 1:
        return
    c, z = 0, None
    for x in range(1, len(snaps)):
        s = sel == snaps[x]["name"]
        if z is None:
            print(
                f'{" " * (c + 1)} - {"*" if s else ""}{snaps[x]["name"]} - '
                f'{_time(n, snaps[x]["date"])}{" [You are Here]" if s else ""}'
            )
            z = snaps[x]
            continue
        if (
            z["id"] > snaps[x]["id"]
            and z["date"] > snaps[x]["date"]
            and z["order"] < snaps[x]["order"]
        ):
            c -= 1
        else:
            c += 1
        if c < 0:
            c = 0
        print(
            f'{" " * (c + 1)} - {"*" if s else ""}{snaps[x]["name"]} - '
            f'{_time(n, snaps[x]["date"])}{" [You are Here]" if s else ""}'
        )
        z = snaps[x]
    del c, n, z


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
            print(f'{"#":>4} {"Device ID":12}{"Description":20}\n{"=" * 60}')
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
    print(f'{"Name":26}{"VMID":8}{"Process ID":12}{"Status":12}\n{"=" * 60}')
    if not isinstance(r.vms, list) or len(r.vms) == 0:
        return True
    for x in r.vms:
        print(
            f'{_vm(x["vmid"], x["name"], x.get("path")):26}{x["vmid"]:<8}'
            f'{x["pid"] if x["pid"] is not None else EMPTY:<12}{x["status"].title():<12}'
        )
    del r
    return True


def user_directory(args):
    try:
        r = send_message(
            args.socket,
            HOOK_HYDRA,
            (HOOK_HYDRA, _is_result),
            TIMEOUT_SEC_MESSAGE,
            {
                "user": True,
                "type": HYDRA_USER_DIRECTORY,
                "directory": args.directory,
            },
        )
    except OSError as err:
        return print_error("Cannot set the VM search directory!", err)
    check_error(r, "Cannot set the VM search directory")
    print(f'VM search directory set to: "{args.directory}"!')
    return True


def user_alias(args, vm=None):
    if nes(args.alias_delete):
        vm = dict()
        vm["name"], vm["type"], o = args.alias_delete, HYDRA_USER_DELETE_ALIAS, "remove"
    elif nes(args.alias_add):
        vm = _get_check(args, vm)
        vm["name"], vm["type"], o = args.alias_add, HYDRA_USER_ADD_ALIAS, "add"
    else:
        return print_error(
            "Cannot perform operation: an opteration type must be specified!"
        )
    vm["user"] = True
    try:
        r = send_message(
            args.socket, HOOK_HYDRA, (HOOK_HYDRA, _is_result), TIMEOUT_SEC_MESSAGE, vm
        )
    except OSError as err:
        return print_error(f"Cannot {o} an alias!", err)
    check_error(r, f"Cannot {o} an alias")
    del o
    if vm["type"] == HYDRA_USER_DELETE_ALIAS:
        print(f'Alias "{vm["name"]}" was removed')
    else:
        print(f'Alias "{vm["name"]}" was added for VM({r.vmid})')
    del r, vm
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
        print(_EXAMPLE.format(vmid=n, uuid=str(uuid4())))
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
        print(f'{"Name":30}{"VMID":8}{"Process ID":12}{"Status":12}\n{"=" * 60}')
    if not isinstance(r.vms, list) or len(r.vms) == 0:
        return
    r.vms.sort(key=lambda x: x["vmid"])
    for x in r.vms:
        if args.dmenu:
            print(
                f'{x["vmid"]}|{x["status"].title()}|{_vm(x["vmid"], x["name"], x["file"])}'
            )
            continue
        print(
            f'{_vm(x["vmid"], x["name"], x["file"]):30}{x["vmid"]:<8}'
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
        if len(args.args) >= 2 and args.args[1].lower() == "temp":
            args.temp = True
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
        if len(args.args) >= 2 and args.args[1].lower() == "temp":
            args.temp = True
        return vm_connect(args, vm, True)
    if c == "spice" or c == "s" or c == "view" or c == "connect" or args.connect:
        if len(args.args) >= 2 and args.args[1].lower() == "temp":
            args.temp = True
        return vm_connect(args, vm)
    if c == "ip" or args.ga_ip:
        return vm_ip(args, vm)
    if c == "ping" or args.ga_ping:
        return vm_ping(args, vm)
    if c == "input" or c == "type" or args.input:
        if len(args.args) > 1:
            args.input = args.args[1].lower()
        return vm_input(args, vm)
    if c == "snap" or args.snap:
        if len(args.args) == 1:
            return vm_snap_list(args, vm)
        o = args.args[1].lower() if len(args.args) >= 3 else None
        if nes(o) and (o == "new" or o == "take"):
            args.snap = args.args[2]
            return vm_snap(args, vm)
        if nes(o) and (o == "use" or o == "restore" or o == "revert"):
            args.snap_restore = args.args[2]
            return vm_snap_restore(args, vm)
        if nes(o) and (o == "del" or o == "delete"):
            args.snap_delete = args.args[2]
            return vm_snap_delete(args, vm)
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
        f'{_vm(r.vmid, r.name, r.file)} - {r.status.title()}\n\n{"Interface":16}IP Address\n{"=" * 32}'
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
    print(f"{_vm(r.vmid, r.name, r.file)} - {r.status.title()}!")
    del r, vm
    return True


def vm_input(args, vm=None):
    vm = _get_check(args, vm)
    vm["type"], vm["input"], vm["caps"] = HYDRA_SEND_INPUT, args.input, args.use_caps
    try:
        r = send_message(
            args.socket, HOOK_HYDRA, (HOOK_HYDRA, True), TIMEOUT_SEC_MESSAGE, vm
        )
    except OSError as err:
        return print_error("Cannot send input to the VM!", err)
    check_error(r, "Cannot send input to the VM")
    del r, vm
    return True


def vm_snap(args, vm=None):
    vm = _get_check(args, vm)
    if not valid_snap_name(args.snap):
        return print_error("Snapshot name is invalid!")
    vm["type"], vm["name"] = HYDRA_SNAP_TAKE, args.snap
    try:
        r = send_message(
            args.socket, HOOK_HYDRA, (HOOK_HYDRA, True), TIMEOUT_SEC_MESSAGE, vm
        )
    except OSError as err:
        return print_error("Cannot take Snapshot!", err)
    check_error(r, "Cannot take Snapshot")
    print(f"{_vm(r.vmid, r.name, r.file)} - {r.status.title()}!")
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
        f'{_vm(r.vmid, r.name, r.file)} - Guest Agent {"" if r.get("ping", False) else "not "}Running!'
    )
    del r, vm
    return True


def vm_start(args, vm=None):
    vm = _get_check(args, vm)
    vm["type"], vm["temp"], vm["debug"] = HYDRA_START, args.temp, args.debug
    try:
        r = send_message(args.socket, HOOK_HYDRA, HOOK_HYDRA, TIMEOUT_SEC_MESSAGE, vm)
    except OSError as err:
        return print_error("Cannot start the VM!", err)
    check_error(r)
    print(f"{_vm(r.vmid, r.name, r.file)} - {r.status.title()}!")
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
    print(f"Removed all USB devices from {_vm(r.vmid, r.name, r.file)}.")
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


def vm_snap_list(args, vm=None):
    vm = _get_check(args, vm)
    vm["type"] = HYDRA_SNAP_LIST
    try:
        r = send_message(
            args.socket, HOOK_HYDRA, (HOOK_HYDRA, True), TIMEOUT_SEC_MESSAGE, vm
        )
    except OSError as err:
        return print_error("Cannot list Snapshots!", err)
    check_error(r, "Cannot list Snapshots")
    if len(r["snaps"]) == 0:
        return print("No Snapshots found.")
    n = 0
    for k, v in r["snaps"].items():
        if n > 0:
            print()
        n += 1
        print(f'Snapshots of "{k}" ({v["file"]})')
        _print_snaps(v["snaps"], r.get("snap_current"))
    del n, r, vm
    return True


def vm_snap_delete(args, vm=None):
    vm = _get_check(args, vm)
    if not valid_snap_name(args.snap_delete):
        return print_error("Snapshot name is invalid!")
    vm["type"], vm["name"] = HYDRA_SNAP_DELETE, args.snap_delete
    try:
        r = send_message(
            args.socket, HOOK_HYDRA, (HOOK_HYDRA, True), TIMEOUT_SEC_MESSAGE, vm
        )
    except OSError as err:
        return print_error("Cannot delete Snapshot!", err)
    check_error(r, "Cannot delete Snapshot")
    print(f"{_vm(r.vmid, r.name, r.file)} - {r.status.title()}!")
    del r, vm
    return True


def vm_snap_restore(args, vm=None):
    vm = _get_check(args, vm)
    if not valid_snap_name(args.snap_restore):
        return print_error("Snapshot name is invalid!")
    vm["type"], vm["name"] = HYDRA_SNAP_RESTORE, args.snap_restore
    try:
        r = send_message(
            args.socket, HOOK_HYDRA, (HOOK_HYDRA, True), TIMEOUT_SEC_MESSAGE, vm
        )
    except OSError as err:
        return print_error("Cannot restore Snapshot!", err)
    check_error(r, "Cannot restore Snapshot")
    print(f"{_vm(r.vmid, r.name, r.file)} - {r.status.title()}!")
    del r, vm
    return True


def vm_usb(args, remove=False, vm=None):
    vm = _get_check(args, vm)
    if nes(args.usb_name):
        if args.usb_name == "all" and (remove or args.usb_delete):
            return vm_usb_clean(args, vm)
        # We already checked the name so we're good.
        try:
            args.usb_id = int(args.usb_name)
        except ValueError:
            _usb_vet(args)
    elif nes(args.usb_vendor) and nes(args.usb_product):
        pass
    elif not (remove or args.usb_delete) and not isinstance(args.usb_id, int):
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
        print(
            f'USB Device "ID-{args.usb_id}" was removed from {_vm(r.vmid, r.name, r.file)}!'
        )
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
    print(f"{_vm(r.vmid, r.name, r.file)} - {r.status.title()}")
    del r, w, vm
    return True


def vm_connect(args, vm=None, vnc=False):
    vm = _get_check(args, vm)
    vm["type"], vm["temp"], vm["debug"] = HYDRA_START, args.temp, args.debug
    try:
        r = send_message(args.socket, HOOK_HYDRA, HOOK_HYDRA, TIMEOUT_SEC_MESSAGE, vm)
    except OSError as err:
        return print_error("Cannot start the VM!", err)
    check_error(r)
    del vm
    if not args.no_fork and fork() != 0:
        return True
    if r.status == "waiting":
        sleep(2)
    v = f"{HYDRA_DIR}/{r.vmid}.{'vnc' if args.connect_vnc or vnc else 'spice'}"
    for _ in range(0, 20):
        # Try to open the socket up to 20 times to wait for the permissions to
        # be fixed.
        try:
            s = socket(AF_UNIX, SOCK_STREAM)
            s.connect(v)
            s.close()
            break
        except OSError:
            pass
        finally:
            del s
        sleep(1)
    if args.connect_vnc or vnc:
        try:
            execl(
                HYDRA_EXEC_VNC,
                basename(HYDRA_EXEC_VNC),
                "FullscreenSystemKeys=0",
                "Shared=1",
                v,
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
            f"--uri=spice+unix://{v}",
        )
    except OSError as err:
        return print_error("Cannot connect to the VM via Spice!", err)
    del r, v
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
