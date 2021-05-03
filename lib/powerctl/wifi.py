#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame 2018
#
# PowerCTL Module: Wireless
#  powerctl wifi, wifictl, wifi
#
# PowerCTL command line user module to configure wireless options.
# Updated 10/2018

from os import listdir
from os.path import exists, join, isdir
from lib.structs.message import send_message
from lib.util import read, boolean, print_error
from lib.constants import HOOK_POWER, WIRELESS_WIFI_DEVICES, BOOLEANS, EMPTY

ARGS = [
    (
        "-d",
        {
            "required": False,
            "action": "store_true",
            "dest": "disable",
            "help": "Disable Wireless.",
        },
        "config",
    ),
    (
        "-e",
        {
            "required": False,
            "action": "store_true",
            "dest": "enable",
            "help": "Enable Wireless.",
        },
        "config",
    ),
    (
        "-b",
        {
            "required": False,
            "action": "store",
            "type": str,
            "dest": "boot",
            "metavar": "boot",
            "help": "Set the Wireless status on boot.",
            "choices": ("0", "1", "true", "false"),
        },
        "config",
    ),
    (
        "command",
        {
            "nargs": "?",
            "action": "store",
            "default": None,
            "help": "Wireless commands.",
            "choices": BOOLEANS + ["set", "boot"],
        },
        "command",
    ),
    (
        "args",
        {
            "nargs": "*",
            "action": "store",
            "default": None,
            "help": "Optional arguments to the command.",
        },
    ),
]
DESCRIPTION = "System Wireless Management Module"


def config(arguments):
    set_config(arguments, "wireless")


def command(arguments):
    if not set_command(arguments, "wireless"):
        default(arguments)


def default(arguments):
    try:
        devices = listdir(WIRELESS_WIFI_DEVICES)
    except OSError as err:
        print_error(
            "Attempting to retrive wireless devices raised an exception!", err, True
        )
    else:
        for device in devices:
            path = join(WIRELESS_WIFI_DEVICES, device, "flags")
            wireless = join(WIRELESS_WIFI_DEVICES, device, "wireless")
            if exists(path) and isdir(wireless):
                try:
                    flags = read(path, ignore_errors=False)
                except OSError as err:
                    print_error(
                        "Attempting to retrive wireless status raised an exception!",
                        err,
                        True,
                    )
                else:
                    if (
                        isinstance(flags, str)
                        and flags.replace("\n", EMPTY) == "0x1003"
                    ):
                        print("Wireless is enabled")
                        return
                finally:
                    del flags
            del path
            del wireless
    finally:
        del devices
    print("Wireless is disabled!")


def set_config(arguments, status_type):
    if arguments.boot:
        _set(arguments.socket, status_type, arguments.boot)
    else:
        _set(arguments.socket, status_type, None, arguments.enable, arguments.disable)


def set_command(arguments, status_type):
    command = arguments.command.lower()
    if command in BOOLEANS:
        _set(arguments.socket, status_type, None, boolean(command))
        return True
    if arguments.args is not None and len(arguments.args) > 0:
        if command == "set":
            _set(arguments.socket, status_type, None, boolean(arguments.args[0]))
            return True
        if command == "boot":
            _set(arguments.socket, status_type, arguments.args[0])
            return True
    return False


def _set(socket, device, boot=None, enable=False, disable=False):
    message = {"type": device}
    if boot is not None:
        message["action"] = "boot"
        message["boot"] = boolean(boot)
        print(
            'Setting "%s" boot status to "%s"!'
            % (device, "Enabled" if message["boot"] else "Disabled")
        )
    else:
        message["action"] = "set"
        message["set"] = enable and not disable
        print(
            'Setting "%s" status to "%s"!'
            % (device, "Enabled" if message["set"] else "Disabled")
        )
    try:
        send_message(socket, HOOK_POWER, None, None, message)
    except OSError as err:
        print_error(
            'Attempting to set "%s" status raised an Exception!' % device, err, True
        )
    finally:
        del message


# EOF
