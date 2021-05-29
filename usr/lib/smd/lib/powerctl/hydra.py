#!/usr/bin/false
# PowerCTL Module: Hydra
#  powerctl hydra, hydractl, hydra
#
# PowerCTL command line user module to control and configure Hydra VMs
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

from os import fork
from sys import exit
from time import sleep
from lib.structs.message import send_message
from lib.modules.hydra import get_vm, get_usb
from lib.util import read_json, print_error, run, eval_env
from lib.constants import (
    EMPTY,
    HOOK_HYDRA,
    HYDRA_STOP,
    HYDRA_WAKE,
    HYDRA_SLEEP,
    HYDRA_START,
    HYDRA_STATUS,
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


def all(args):
    do_all(args, args.all_sleep, args.all_wake, args.all_stop)


def default(args):
    list_vms(args)


def list_vms(args):
    try:
        out = send_message(
            args.socket, HOOK_HYDRA, (HOOK_HYDRA, "vms"), 5, {"type": HYDRA_STATUS}
        )
    except OSError as err:
        return print_error("Attempting to query VM list raised an exception!", err)
    if "error" in out:
        return print_error(out["error"])
    if not args.dmenu:
        print(f'{"Name":20}{"VMID":8}{"Process ID":12}{"Status":12}\n{"="*50}')
    if out.get("vms") is None:
        exit(0)
    for vm in out["vms"]:
        if args.dmenu:
            print(
                f'{_resolve_name(vm["vmid"], vm["path"])},{vm["status"].title()},{vm["vmid"]}'
            )
            continue
        print(
            f'{_resolve_name(vm["vmid"], vm["path"]):20}{vm["vmid"]:<8}'
            f'{vm["pid"] if vm["pid"] is not None else EMPTY:<12}{vm["status"].title()}'
        )
    del out
    exit(0)


def tokenize(args):
    if args.command is None:
        list_vms(args)
    command = args.command.lower()
    if command == "list" or args.list:
        list_vms(args)
    elif command == "dir" or command == "directory" or args.directory:
        if len(args.args) >= 1:
            args.directory = args.args[0]
        directory(args)
    if len(args.args) >= 1:
        vm = _resolve_vm(args, args.args[0])
    else:
        vm = _resolve_vm(args)
    if command == "start" or args.start:
        start(args, vm)
    elif command == "stop" or args.stop:
        if vm is None or args.all_stop or args.all_force:
            do_all(args, False, False, True)
        else:
            stop(args, vm)
    elif command == "vnc" or command == "v" or args.connect_vnc:
        args.connect_vnc = True
        connect(args, vm)
    elif command == "view" or command == "connect" or args.connect:
        connect(args, vm)
    elif command == "usb" or args.usb_add or args.usb_delete:
        name = EMPTY
        option = EMPTY
        if len(args.args) >= 2:
            option = args.args[1].lower()
        if len(args.args) >= 3:
            name = args.args[2].lower()
        if len(name) > 0:
            args.usb_name = name
        if option not in HYDRA_USB_COMMANDS and not (args.usb_delete or args.usb_add):
            if len(option) > 0:
                args.usb_name = option
            else:
                usb_list(args, vm)
        if len(name) == 0 and (args.usb_list or option == "list"):
            usb_list(args, vm)
        elif option == "clean" or option == "clear":
            usb_clean(args, vm)
        else:
            usb(args, (option == "remove" or option == "del") or args.usb_delete, vm)
        del name
        del option
    elif command == "wake" or args.wake:
        if vm is None or args.all_wake:
            do_all(args, False, True, False)
        else:
            sleep_vm(args, False, vm)
    elif command == "sleep" or args.sleep:
        if vm is None or args.all_sleep:
            do_all(args, True, False, False)
        else:
            sleep_vm(args, True, vm)
    elif command == "alias" or command == "name" or args.alias_add or args.alias_delete:
        name = EMPTY
        option = EMPTY
        if len(args.args) >= 2:
            option = args.args[1].lower()
        if len(args.args) >= 3:
            name = args.args[2].lower()
        if option == "add" and len(name) > 0:
            args.alias_add = name
        elif option == "delete" or option == "del" and len(name) > 0:
            args.alias_delete = name
        elif len(option) > 0 and len(name) == 0:
            args.alias_add = option
        alias(args, vm)
        del name
        del option
    else:
        return print_error(f'Invalid command "{command}" given!')
    exit(0)


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
        return print_error(
            "Attempting to set the VM search directory raised an exception!", err
        )
    exit(0)


def _resolve_usb(args):
    if not args.usb_name:
        return
    usb_devices = get_usb()
    search = str(args.usb_name).lower()
    if len(search) == 9 and ":" in search and search in usb_devices:
        args.usb_vendor = search[:4]
        args.usb_product = search[5:]
        del search
        del usb_devices
        return
    match = list()
    for device in usb_devices.values():
        if search in device["name"].lower():
            match.append(device)
    del usb_devices
    selected = None
    if len(match) > 1:
        print(
            f'Multiple devices match "{search}", please select a device from the list:'
        )
        try:
            while True:
                print(f'{"#":3}{"USB-ID":12}{"Description":20}\n{"="*50}')
                for x in range(0, len(match)):
                    did = f'{match[x]["vendor"]}:{match[x]["product"]}'
                    print(f'{x:3}{did:<12}{match[x]["name"]:<20}')
                    del did
                index = input("Index [Default 0, Cancel 'q']: ")
                if index is None or len(index) == 0:
                    selected = match[0]
                    break
                if len(index) == 1 and index.lower() == "q":
                    return print_error("Aborted USB operation.")
                try:
                    index = int(index)
                    if 0 <= index < len(match):
                        selected = match[index]
                        break
                except ValueError:
                    pass
                print(f'Invalid index "{index}"!\n')
                del index
        except KeyboardInterrupt:
            print()
            return print_error("Aborted USB operation.")
    elif len(match) == 1:
        selected = match[0]
    else:
        return print_error(
            f'Could not find any connected USB devices matching name "{search}"!'
        )
    del match
    del search
    print(
        f'\nSelecting Device "{selected["vendor"]}:{selected["product"]} - {selected["name"]}" '
        f"based on search results."
    )
    args.usb_vendor = selected["vendor"]
    args.usb_product = selected["product"]
    del selected


def stop(args, vm=None):
    if vm is None:
        vm = _resolve_vm(args)
    vm["type"] = HYDRA_STOP
    vm["force"] = args.stop_force
    vm["timeout"] = args.timeout
    try:
        out = send_message(args.socket, HOOK_HYDRA, HOOK_HYDRA, 5, vm)
    except OSError as err:
        return print_error("Attempting to stop the VM raised an exception!", err)
    if "error" in out:
        return print_error(out["error"])
    print(f'{_resolve_name(out["vmid"], out["path"])} - {out["status"].title()}!')
    del vm
    del out
    exit(0)


def start(args, vm=None):
    if vm is None:
        vm = _resolve_vm(args)
    vm["type"] = HYDRA_START
    try:
        out = send_message(args.socket, HOOK_HYDRA, HOOK_HYDRA, 5, vm)
    except OSError as err:
        return print_error("Attempting to start the VM raised an exception!", err)
    if "error" in out:
        return print_error(out["error"])
    print(f'{_resolve_name(out["vmid"], out["path"])} - {out["status"].title()}!')
    del vm
    del out
    exit(0)


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
        return print_error("Attempting to add a VM alias raised an exception!", err)
    del vm
    exit(0)


def connect(args, vm=None):
    if vm is None:
        vm = _resolve_vm(args)
    vm["type"] = HYDRA_START
    try:
        out = send_message(args.socket, HOOK_HYDRA, HOOK_HYDRA, 5, vm)
    except OSError as err:
        return print_error("Attempting to start the VM raised an exception!", err)
    if "error" in out:
        return print_error(out["error"])
    if args.connect_vnc:
        try:
            if fork() != 0:
                exit(0)
            if out["status"] == "waiting":
                sleep(2)
            run(
                [
                    "/usr/bin/vncviewer",
                    "FullscreenSystemKeys=0",
                    f'{DIRECTORY_HYDRA}/{out["vmid"]}.vnc',
                ],
                ignore_errors=False,
            )
        except OSError as err:
            return print_error(
                "Attempting to connect to the VM raised an exception!", err
            )
    else:
        try:
            if fork() != 0:
                exit(0)
            if out["status"] == "waiting":
                sleep(2)
            run(
                [
                    "/usr/bin/surf",
                    "-BDfgIKmnSTxc",
                    "/dev/null",
                    f'http://hydra:8600/?path=websockify?token=VM{out["vmid"]}&scaling=local&autoconnect=true',
                ],
                ignore_errors=False,
            )
        except OSError as err:
            return print_error(
                "Attempting to connect to the VM raised an exception!", err
            )
    del vm
    del out


def usb_list(args, vm=None):
    if vm is None:
        vm = _resolve_vm(args)
    vm["type"] = HYDRA_USB_QUERY
    try:
        out = send_message(args.socket, HOOK_HYDRA, HOOK_HYDRA, 5, vm)
    except OSError as err:
        return print_error("Attempting to stop the VM raised an exception!", err)
    if "error" in out:
        return print_error(out["error"])
    devices = get_usb()
    print(f'{"ID":3}{"USB-ID":12}{"Description":20}\n{"=" * 50}')
    if "usb" in out and out.get("usb") is not None:
        for id, device in out["usb"].items():
            if device not in devices:
                print(f'{id:3}{device:<12}{"USB Device":<20}')
                continue
            print(f'{id:3}{device:<12}{devices[device]["name"]:<20}')
    del vm
    del out
    del devices
    exit(0)


def usb_clean(args, vm=None):
    if vm is None:
        vm = _resolve_vm(args)
    vm["type"] = HYDRA_USB_CLEAN
    try:
        out = send_message(args.socket, HOOK_HYDRA, HOOK_HYDRA, 5, vm)
    except OSError as err:
        return print_error(
            "Attempting to remove all USB devices on the VM raised an exception!", err
        )
    if "error" in out:
        return print_error(out["error"])
    print(f'Removed all USB devices from {_resolve_name(out["vmid"], out["path"])}')
    del vm
    del out
    exit(0)


def _resolve_name(vmid, path):
    if len(NAMES) == 0:
        config = read_json(eval_env(CONFIG_CLIENT), ignore_errors=True)
        if isinstance(config, dict) and "hydra" in config:
            if isinstance(config["hydra"], dict) and "aliases" in config["hydra"]:
                for name, file in config["hydra"]["aliases"].items():
                    NAMES[file.lower()] = name.title()
        NAMES["__loaded"] = True
        del config
    name = NAMES.get(path.lower(), None)
    if name is not None:
        return f"{name} ({vmid})"
    return f"VM({vmid})"


def _resolve_vm(args, name=None):
    if name == "all":
        return None
    if name is None:
        name = args.name
    if name is None:
        name = args.command
    if name is not None:
        path = get_vm(name, eval_env(CONFIG_CLIENT))
        if path is None:
            try:
                return {"vmid": int(name)}
            except ValueError:
                pass
            return print_error(f'Cannot locate VM "{name}"!')
        return {"path": path}
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
            usb_clean(args, vm)
            return
        _resolve_usb(args)
    elif args.usb_vendor and args.usb_product:
        pass
    elif not (remove or args.usb_delete) or args.usb_id is None:
        return print_error("USB Name, ID, or VendorID and ProductID must be specified!")
    if remove or args.usb_delete:
        if args.usb_id is None:
            vm["type"] = HYDRA_USB_QUERY
            try:
                out = send_message(args.socket, HOOK_HYDRA, HOOK_HYDRA, 5, vm)
            except OSError as err:
                return print_error(
                    "Attempting to query the connected USB devices raised an exception!",
                    err,
                )
            if "error" in out:
                return print_error(out["error"])
            if "usb" not in out or out.get("usb") is None:
                return print_error(
                    "No USB devices are currently connected to the specified VM!"
                )
            device_id = f"{args.usb_vendor}:{args.usb_product}".lower()
            if "usb" in out and isinstance(out.get("usb"), dict):
                for id, device in out["usb"].items():
                    if device.lower() == device_id:
                        args.usb_id = id
                        break
            del out
            del device_id
        vm["usb"] = args.usb_id
        vm["type"] = HYDRA_USB_DELETE
    else:
        vm["type"] = HYDRA_USB_ADD
        vm["slow"] = args.usb_slow
        vm["vendor"] = args.usb_vendor
        vm["product"] = args.usb_product
    try:
        out = send_message(args.socket, HOOK_HYDRA, HOOK_HYDRA, 5, vm)
    except OSError as err:
        return print_error(
            "Attempting to change USB on the VM raised an exception!", err
        )
    if "error" in out:
        return print_error(out["error"])
    if remove or args.usb_delete:
        print(
            f'USB Device with device ID {args.usb_id} removed from {_resolve_name(out["vmid"], out["path"])}!'
        )
    else:
        print(
            f'USB Device "{args.usb_vendor}{args.usb_product}" attached to '
            f'{_resolve_name(out["vmid"], out["path"])} with device ID {out["usb"]}'
        )
    del vm
    del out
    exit(0)


def sleep_vm(args, do_sleep=True, vm=None):
    if vm is None:
        vm = _resolve_vm(args)
    if do_sleep or args.sleep:
        vm["type"] = HYDRA_SLEEP
    elif not do_sleep or args.wake:
        vm["type"] = HYDRA_WAKE
    try:
        out = send_message(args.socket, HOOK_HYDRA, HOOK_HYDRA, 5, vm)
    except OSError as err:
        return print_error("Attempting to sleep/wake the VM raised an exception!", err)
    if "error" in out:
        return print_error(out["error"])
    print(f'{_resolve_name(out["vmid"], out["path"])} - {out["status"].title()}')
    del vm
    del out
    exit(0)


def do_all(args, do_sleep, do_wake, do_stop):
    query = {"all": True}
    if do_sleep and not (do_wake or do_stop):
        query["type"] = HYDRA_SLEEP
    elif do_wake and not (do_sleep or do_stop):
        query["type"] = HYDRA_WAKE
    elif do_stop or args.all_force and not (do_sleep or do_wake):
        if args.all_force:
            query["force"] = True
        query["type"] = HYDRA_STOP
    if "type" not in query:
        return print_error("An action must be specified!")
    try:
        out = send_message(args.socket, HOOK_HYDRA, (HOOK_HYDRA, "vms"), 5, query)
    except OSError as err:
        return print_error("Attempting to do a setall raised an exception!", err)
    if "error" in out:
        return print_error(out["error"])
    print(f'{"Name":20}{"VMID":8}{"Process ID":12}{"Status":12}\n{"="*50}')
    if out.get("vms") is None:
        exit(0)
    for vm in out["vms"]:
        print(
            f'{_resolve_name(vm["vmid"], vm["path"]):20}{vm["vmid"]:<8}'
            f'{vm["pid"] if vm["pid"] is not None else EMPTY:<12}{vm["status"].title():<12}'
        )
    del out
    exit(0)
