#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame 2018
#
# PowerCTL Module: Bluetooth
#  powerctl blue, bluectl, blue
#
# PowerCTL command line user module to configure bluetooth options.
# Updated 10/2018

from os import listdir
from lib.util import print_error
from lib.powerctl.wifi import set_command, set_config
from lib.constants import WIRELESS_BLUE_DEVICES, BOOLEANS

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
        if len(devices) > 0:
            print("Bluetooth is enabled!")
        else:
            print("Bluetooth is disabled!")
        del devices


# EOF
