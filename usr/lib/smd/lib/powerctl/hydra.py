#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame
#
# PowerCTL Module: Hydra
#  powerctl hydra, hydractl, hydra
#
# PowerCTL command line user module to control and configure Hydra VMs

from sys import exit
from time import sleep
from os.path import join
from os import environ, fork
from lib.structs.message import send_message
from lib.modules.hydra import get_vm, get_usb
from lib.util import read_json, print_error, run
from lib.constants import (
    HOOK_HYDRA,
    CONFIG_CLIENT,
    HYDRA_POWERCTL_COMMANDS,
    DIRECTORY_HYRDA,
    HYDRA_BROWSER_COMMAND,
    HYDRA_VNC_COMMAND,
)

ARGS = [
    (
        "-l",
        {
            "required": False,
            "action": "store_true",
            "dest": "list",
            "help": "List running VMs.",
        },
        "hydra_list",
    ),
    (
        "-i",
        {
            "required": False,
            "action": "store",
            "dest": "vmid",
            "type": int,
            "metavar": "vmid",
            "help": "VMID of VM to select.",
        },
    ),
    (
        "-n",
        {
            "required": False,
            "action": "store",
            "dest": "name",
            "type": str,
            "metavar": "name",
            "help": "Name or Path of VM to select.",
        },
    ),
    (
        "command",
        {
            "nargs": "?",
            "action": "store",
            "default": None,
            "help": "Hydra command to execute.",
        },
        "hydra_command_check",
    ),
    (
        "args",
        {
            "nargs": "*",
            "action": "store",
            "default": None,
            "help": "Optional arguments to command.",
        },
    ),
    (
        "-a",
        {
            "required": False,
            "action": "store",
            "dest": "aliasadd",
            "type": str,
            "metavar": "alias",
            "help": "Add an Alias to the VM.",
        },
        "hydra_name_add",
    ),
    (
        "-ar",
        {
            "required": False,
            "action": "store",
            "dest": "aliasdel",
            "type": str,
            "metavar": "alias",
            "help": "Remove an Alias from the VM.",
        },
        "hydra_name_remove",
    ),
    (
        "-x",
        {
            "required": False,
            "action": "store_true",
            "dest": "stop",
            "help": "Stop the VM.",
        },
        "hydra_stop",
    ),
    (
        "-s",
        {
            "required": False,
            "action": "store_true",
            "dest": "start",
            "help": "Start the VM.",
        },
        "hydra_start",
    ),
    (
        "-p",
        {
            "required": False,
            "action": "store_true",
            "dest": "force",
            "help": "Poweroff (Halt) the VM.",
        },
        "hydra_stop",
    ),
    (
        "-t",
        {
            "required": False,
            "action": "store",
            "dest": "timeout",
            "type": str,
            "default": None,
            "help": "Optional Shutdown timeout.",
        },
        "hydra_stop",
    ),
    (
        "-u",
        {
            "required": False,
            "action": "store_true",
            "dest": "usbadd",
            "help": "Connect a USB Device",
        },
        "hydra_usb_add",
    ),
    (
        "-ur",
        {
            "required": False,
            "action": "store_true",
            "dest": "usbdel",
            "help": "Disconnect a USB Device.",
        },
        "hydra_usb_remove",
    ),
    (
        "-ul",
        {
            "required": False,
            "action": "store_true",
            "dest": "usblist",
            "help": "List a USB Devices connected to a VM.",
        },
        "hydra_usb_list",
    ),
    (
        "-un",
        {
            "required": False,
            "action": "store",
            "dest": "usbname",
            "type": str,
            "metavar": "usb_name",
            "help": "Name of USB Device to select.",
        },
    ),
    (
        "-ui",
        {
            "required": False,
            "action": "store",
            "dest": "usbid",
            "type": int,
            "metavar": "usb_id",
            "help": "USB Device ID to select.",
        },
    ),
    (
        "-uv",
        {
            "required": False,
            "action": "store",
            "dest": "vendor",
            "type": str,
            "metavar": "usb_vendor",
            "help": "USB Device Vendor ID to select.",
        },
    ),
    (
        "-up",
        {
            "required": False,
            "action": "store",
            "dest": "product",
            "type": str,
            "metavar": "usb_product",
            "help": "USB Device Product ID to select.",
        },
    ),
    (
        "-c",
        {
            "required": False,
            "action": "store_true",
            "dest": "connect",
            "help": "Connect to VM (Web Window)",
        },
        "hydra_start",
    ),
    (
        "-cv",
        {
            "required": False,
            "action": "store_true",
            "dest": "vncconnect",
            "help": "Connect to VM (VNC Window)",
        },
        "hydra_start",
    ),
    (
        "-w",
        {
            "required": False,
            "action": "store_true",
            "dest": "wakevm",
            "help": "Wake VM if Sleeping",
        },
        "hydra_sleep",
    ),
    (
        "-z",
        {
            "required": False,
            "action": "store_true",
            "dest": "sleepvm",
            "help": "Sleep VM if awake",
        },
        "hydra_sleep",
    ),
    (
        "-za",
        {
            "required": False,
            "action": "store_true",
            "dest": "sleepall",
            "help": "Sleep all woken VMs",
        },
        "hydra_setall",
    ),
    (
        "-wa",
        {
            "required": False,
            "action": "store_true",
            "dest": "wakeall",
            "help": "Wake all sleeping VMs",
        },
        "hydra_setall",
    ),
    (
        "-xa",
        {
            "required": False,
            "action": "store_true",
            "dest": "stopall",
            "help": "Stop all running VMs",
        },
        "hydra_setall",
    ),
]
NAMES = dict()
DESCRIPTION = "Hyrda Management Module"
CONFIG = CONFIG_CLIENT.replace("{home}", environ["HOME"])


def default(arguments):
    if arguments.command:
        hydra_command(str(arguments.command).lower(), arguments, arguments.args)
    else:
        hydra_list(arguments)


def hydra_vm(arguments):
    if arguments.name:
        path = get_vm(arguments.name, CONFIG)
        if path is None:
            try:
                return {"vmid": int(arguments.name)}
            except ValueError:
                pass
            print_error('Cannot locate VM "%s"!' % arguments.name, None, True)
        return {"path": path}
    if arguments.vmid:
        try:
            return {"vmid": int(arguments.vmid)}
        except ValueError as err:
            print_error("VMID must be an integer!", err, True)
    print_error("No VMID or Path given!", None, True)
    return None


def hydra_list(arguments):
    try:
        query = send_message(
            arguments.socket, HOOK_HYDRA, (HOOK_HYDRA, "vms"), 10, {"type": "list"}
        )
    except OSError as err:
        print_error("Attempting to query VM list raised an exception!", err, True)
    else:
        print(
            "%-20s%-6s%-12s%-12s\n%s"
            % ("Name", "VMID", "Process ID", "Status", "=" * 50)
        )
        if "vms" in query:
            for vm in query["vms"]:
                print(
                    "%-20s%-6s%-12s%-12s"
                    % (
                        hydra_name(vm["vmid"], vm["path"]),
                        vm["vmid"],
                        vm["pid"],
                        vm["status"].title(),
                    )
                )
        elif "error" in query:
            print_error(query["error"], None, True)
        del query


def hydra_stop(arguments):
    message = hydra_vm(arguments)
    message["type"] = "stop"
    if arguments.force:
        message["force"] = True
    if arguments.timeout:
        message["timeout"] = arguments.timeout
    try:
        response = send_message(arguments.socket, HOOK_HYDRA, HOOK_HYDRA, 15, message)
    except OSError as err:
        print_error("Attempting to stop the VM raised an exception!", err, True)
    else:
        if "error" in response:
            print_error(response["error"], None, True)
        else:
            print(
                "%s %s!"
                % (
                    hydra_name(response["vmid"], response["path"]),
                    response["status"].title(),
                )
            )
        del response
    finally:
        del message


def hydra_name(vmid, path):
    if len(NAMES) == 0:
        config = read_json(CONFIG, ignore_errors=True)
        if isinstance(config, dict) and "hydra_aliases" in config:
            for name, file in config["hydra_aliases"].items():
                NAMES[file] = name.title()
        NAMES["__loaded"] = True
        del config
    if path in NAMES:
        return "VM(%s) - %s" % (vmid, NAMES[path])
    return "VM(%s)" % vmid


def hydra_start(arguments):
    message = hydra_vm(arguments)
    message["type"] = "start"
    try:
        response = send_message(arguments.socket, HOOK_HYDRA, HOOK_HYDRA, 15, message)
    except OSError as err:
        print_error("Attempting to start the VM raised an exception!", err, True)
    else:
        if "error" in response:
            print_error(response["error"], None, True)
        else:
            if arguments.connect or arguments.vncconnect:
                try:
                    if fork() == 0:
                        if response["status"] == "waiting":
                            print("Waiting for VM VNC server to come online..")
                            sleep(2)
                        if arguments.vncconnect:
                            run(
                                HYDRA_VNC_COMMAND
                                + [join(DIRECTORY_HYRDA, "%s.vnc" % response["vmid"])],
                                ignore_errors=False,
                            )
                        else:
                            run(
                                HYDRA_BROWSER_COMMAND
                                + [
                                    "http://hydra:8600/?path=websockify?token=VM%s&scaling=local&autoconnect=true"
                                    % response["vmid"]
                                ],
                                ignore_errors=False,
                            )
                    exit(0)
                except OSError as err:
                    print_error(
                        "Attempting to connect to the VM raised an exception!",
                        err,
                        True,
                    )
            else:
                print(
                    "VM(%s) - %s!\n"
                    % (
                        hydra_name(response["vmid"], response["path"]),
                        response["status"].title(),
                    )
                )
                hydra_list(arguments)
        del response
    finally:
        del message


def hydra_sleep(arguments):
    message = hydra_vm(arguments)
    if arguments.wakevm:
        message["type"] = "wake"
    elif arguments.sleepvm:
        message["type"] = "sleep"
    try:
        response = send_message(arguments.socket, HOOK_HYDRA, HOOK_HYDRA, 15, message)
    except OSError as err:
        print_error("Attempting to sleep/wake the VM raised an exception!", err, True)
    else:
        if "error" in response:
            print_error(response["error"], None, True)
        else:
            print(
                "%s %s!"
                % (
                    hydra_name(response["vmid"], response["path"]),
                    response["status"].title(),
                )
            )
        del response
    finally:
        del message


def hydra_setall(arguments):
    action = "sleep"
    if arguments.wakeall:
        action = "wake"
    elif arguments.stopall:
        action = "stop"
    try:
        query = send_message(
            arguments.socket,
            HOOK_HYDRA,
            (HOOK_HYDRA, "vms"),
            10,
            {"type": "setall", "action": action},
        )
    except OSError as err:
        print_error("Attempting to %s all VMS raised an exception!" % action, err, True)
    else:
        print(
            "%-20s%-6s%-12s%-12s\n%s"
            % ("Name", "VMID", "Process ID", "Status", "=" * 50)
        )
        if "vms" in query:
            for vm in query["vms"]:
                print(
                    "%-20s%-6s%-12s%-12s"
                    % (
                        hydra_name(vm["vmid"], vm["path"]),
                        vm["vmid"],
                        vm["pid"],
                        vm["status"].title(),
                    )
                )
        elif "error" in query:
            print_error(query["error"], None, True)
        del query
    del action


def hydra_vm_usbs(arguments):
    message = hydra_vm(arguments)
    message["type"] = "usb"
    message["action"] = "query"
    try:
        response = send_message(arguments.socket, HOOK_HYDRA, HOOK_HYDRA, 15, message)
    except OSError as err:
        print_error("Attempting to start the VM raised an exception!", err, True)
    else:
        if "error" in response:
            print_error(response["error"], None, True)
        elif "usb" in response:
            return response["usb"]
    return None


def hydra_usb_add(arguments):
    message = hydra_vm(arguments)
    message["type"] = "usb"
    if arguments.usbname:
        hydra_resolve_usb(arguments)
    if arguments.vendor and arguments.product:
        message["action"] = "connect"
        message["vendor"] = arguments.vendor
        message["product"] = arguments.product
        try:
            response = send_message(
                arguments.socket, HOOK_HYDRA, HOOK_HYDRA, 15, message
            )
        except OSError as err:
            print_error(
                "Attempting to add USB to the VM raised an exception!", err, True
            )
        else:
            if "usbid" in response:
                print(
                    'USB Device "%s:%s" attached to %s with Device ID: %s'
                    % (
                        arguments.vendor,
                        arguments.product,
                        hydra_name(response["vmid"], response["path"]),
                        response["usbid"],
                    )
                )
            elif "error" in response:
                print_error(response["error"], None, True)
            del response
        finally:
            del message
    else:
        print_error("USB Name or VendorID and ProductID must be specified!", None, True)


def hydra_name_add(arguments):
    if isinstance(arguments.aliasadd, str) and len(arguments.aliasadd) > 0:
        message = hydra_vm(arguments)
        message["type"] = "user"
        message["action"] = "alias-add"
        message["alias"] = str(arguments.aliasadd).strip()
        try:
            response = send_message(
                arguments.socket, HOOK_HYDRA, HOOK_HYDRA, 15, message
            )
        except OSError as err:
            print_error("Attempting to add a VM alias raised an exception!", err, True)
        else:
            if "error" in response:
                print_error(response["error"], None, True)
            else:
                print(
                    'Added alias "%s" to VM(%s)!'
                    % (response["alias"], response["vm"]["vmid"])
                )
            del response
        finally:
            del message
    else:
        print_error("Incorrect or invalid VM alias!", None, False)


def hydra_usb_list(arguments):
    usb = hydra_vm_usbs(arguments)
    if usb is not None:
        usbs = get_usb()
        print("%-4s%-11s%-20s\n%s" % ("USB ID", "USB IDs", "Description", "=" * 50))
        for did, device in usb.items():
            print("%-4s%-11s%-20s\n%s" % (did, device, usbs[device]["name"]))
        del usb
        del usbs
    else:
        print_error("Could not get a list of connected USB devices!", None, True)


def hydra_usb_remove(arguments):
    message = hydra_vm(arguments)
    message["type"] = "usb"
    if arguments.usbname:
        hydra_resolve_usb(arguments)
        if arguments.vendor and arguments.product:
            usbs = hydra_vm_usbs(arguments)
            usb = ("%s:%s" % (arguments.vendor, arguments.product)).lower()
            if usbs is None:
                print_error(
                    "Could not get a list of connected USB devices!", None, True
                )
            else:
                for did, device in usbs.items():
                    if device.lower() == usb:
                        arguments.usbid = did
                        break
            del usbs
            if not arguments.usbid:
                print_error(
                    'Could not find USB device "%s" connected to the VM!' % usb,
                    None,
                    True,
                )
            del usb
    if arguments.usbid:
        message["action"] = "disconnect"
        try:
            message["usbid"] = int(arguments.usbid)
        except ValueError as err:
            print('Invalid USB Device ID "%s"!' % arguments.usbid, err, True)
        try:
            response = send_message(
                arguments.socket, HOOK_HYDRA, HOOK_HYDRA, 15, message
            )
        except OSError as err:
            print_error(
                "Attempting to remove USB from the VM raised an exception!", err, True
            )
        else:
            if "error" in response:
                print_error(response["error"], None, True)
            else:
                print(
                    'USB Device with Device ID "%s" removed from %s!'
                    % (arguments.usbid, hydra_name(response["vmid"], response["path"]))
                )
            del response
        finally:
            del message
    else:
        print_error("USB Name or DeviceID must be specified!", None, True)


def hydra_resolve_usb(arguments):
    if not arguments.usbname:
        return
    usbs = get_usb()
    devices = list()
    search = str(arguments.usbname).lower()
    for device in usbs.values():
        if search in device["name"].lower():
            devices.append(device)
    del usbs
    selected = None
    if len(devices) > 1:
        print(
            'Multiple devices match "%s", please select a device from the list:'
            % search
        )
        try:
            while True:
                print(
                    "%-6s%-11s%-20s\n%s" % ("Index", "USB IDs", "Description", "=" * 50)
                )
                for x in range(0, len(devices)):
                    print(
                        "%-6s%-11s%-20s"
                        % (
                            x,
                            "%s:%s" % (devices[x]["vendor"], devices[x]["product"]),
                            devices[x]["name"],
                        )
                    )
                index = input("Index [Default 0]: ")
                if index is None or len(index) == 0:
                    selected = devices[0]
                    break
                else:
                    try:
                        index = int(index)
                    except ValueError:
                        pass
                    else:
                        if 0 <= index < len(devices):
                            selected = devices[x]
                            break
                print('Invalid index "%s"!\n' % index)
                del index
        except KeyboardInterrupt:
            selected = None
    elif len(devices) == 1:
        selected = devices[0]
    else:
        print_error(
            'Could not find any USB devices matching name "%s"!' % search, None, True
        )
    del search
    del devices
    print(
        '\nSelecting Device "%s:%s" - "%s" based on search results.'
        % (selected["vendor"], selected["product"], selected["name"])
    )
    arguments.vendor = selected["vendor"]
    arguments.product = selected["product"]
    del selected


def hydra_name_remove(arguments):
    if isinstance(arguments.aliasdel, str) and len(arguments.aliasdel) > 0:
        message = hydra_vm(arguments)
        message["type"] = "user"
        message["action"] = "alias-del"
        message["alias"] = str(arguments.aliasdel).strip()
        try:
            response = send_message(
                arguments.socket, HOOK_HYDRA, HOOK_HYDRA, 15, message
            )
        except OSError as err:
            print_error(
                "Attempting to remove a VM alias raised an exception!", err, True
            )
        else:
            if "error" in response:
                print_error(response["error"], None, True)
            else:
                print('Removed alias "%s"' % response["alias"])
            del response
        finally:
            del message
    else:
        print_error("Incorrect or invalid VM alias!", None, False)


def hydra_command_check(arguments):
    if arguments.command:
        if arguments.command not in HYDRA_POWERCTL_COMMANDS:
            arguments.name = arguments.command
        else:
            default(arguments)


def hydra_command(command, arguments, params):
    if command == "list":
        hydra_list(arguments)
    elif command == "start":
        if len(params) == 1:
            arguments.name = params[0]
            hydra_start(arguments)
        else:
            print_error('Usage "start <name or path>"', None, True)
    elif command == "stop":
        if len(params) >= 1:
            if params[0] == "all":
                arguments.stopall = True
                hydra_setall(arguments)
                return
            if len(params) == 1:
                arguments.name = params[0]
            else:
                arguments.name = params[1]
                try:
                    arguments.timeout = int(params[0])
                except ValueError as err:
                    print_error("Timeout must be a number!", err, True)
            hydra_stop(arguments)
        else:
            print_error('Usage "stop [timeout] <all|name or path>"', None, True)
    elif command == "connect" or command == "vnc":
        if len(params) == 1:
            arguments.name = params[0]
            arguments.vncconnect = True
            hydra_start(arguments)
        else:
            print_error('Usage "connect <name or path>"', None, True)
    elif command == "web" or command == "novnc":
        if len(params) == 1:
            arguments.name = params[0]
            arguments.connect = True
            hydra_start(arguments)
        else:
            print_error('Usage "web <name or path>"', None, True)
    elif command == "sleep":
        if len(params) == 1:
            if params[0] == "all":
                arguments.sleepall = True
                hydra_setall(arguments)
            else:
                arguments.name = params[0]
                arguments.sleepvm = True
                hydra_sleep(arguments)
        else:
            print_error('Usage "sleep <all|name or path>"', None, True)
    elif command == "wake":
        if len(params) == 1:
            if params[0] == "all":
                arguments.wakeall = True
                hydra_setall(arguments)
            else:
                arguments.name = params[0]
                arguments.wakevm = True
                hydra_sleep(arguments)
        else:
            print_error('Usage "wake <all|name or path>"', None, True)
