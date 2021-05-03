#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame
#
# PowerCTL Module: Bluetooth
#  powerctl blue, bluectl, blue
#
# PowerCTL command line user module to configure bluetooth options.

from os import listdir
from os.path import join, exists
from lib.util import print_error, read
from lib.powerctl.wifi import set_command, set_config
from lib.constants import WIRELESS_BLUE_DEVICES, BOOLEANS, EMPTY

ARGS = [
    (
        "-d",
        {
            "required": False,
            "action": "store_true",
            "dest": "disable",
            "help": "Disable Bluetooth.",
        },
        "config",
    ),
    (
        "-e",
        {
            "required": False,
            "action": "store_true",
            "dest": "enable",
            "help": "Enable Bluetooth.",
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
            "help": "Set the Bluetooth status on boot.",
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
            "help": "Bluetooth commands.",
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
            "help": "Optional arguments to command.",
        },
    ),
]
DESCRIPTION = "System Bluetooth Management Module"


def config(arguments):
    set_config(arguments, "bluetooth")


def command(arguments):
    if not set_command(arguments, "bluetooth"):
        default(arguments)


def default(arguments):
    try:
        devices = listdir(WIRELESS_BLUE_DEVICES)
    except OSError as err:
        print_error("Could not list Bluetooth devices!", err, True)
    else:
        for device in devices:
            dev = join(WIRELESS_BLUE_DEVICES, device, "rfkill4", "state")
            if exists(dev):
                try:
                    flags = read(dev, ignore_errors=False)
                except OSError as err:
                    print_error(
                        "Attempting to retrive Bluetooth status raised an exception!",
                        err,
                        True,
                    )
                else:
                    if isinstance(flags, str) and flags.replace("\n", EMPTY) == "1":
                        print("Bluetooth is enabled.")
                        return
                finally:
                    del flags
            del dev
    finally:
        del devices
    print("Bluetooth is disabled.")
