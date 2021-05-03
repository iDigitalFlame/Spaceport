#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame 2018
#
# PowerCTL Module: Rotate
#  powerctl rotate, rotatectl, rotate
#
# PowerCTL command line user module to configure screen rotaion options.
# Updated 10/2018

from lib.util import boolean, print_error
from lib.structs.message import send_message
from lib.constants import HOOK_ROTATE, BOOLEANS

ARGS = [
    (
        "-d",
        {
            "required": False,
            "action": "store_true",
            "dest": "disable",
            "help": "Disable Rotation lock",
        },
        "config",
    ),
    (
        "-e",
        {
            "required": False,
            "action": "store_true",
            "dest": "enable",
            "help": "Enable Rotation lock",
        },
        "config",
    ),
    (
        "-t",
        {
            "required": False,
            "action": "store_true",
            "dest": "toggle",
            "help": "Toggle Rotation lock",
        },
        "config",
    ),
    (
        "-s",
        {
            "required": False,
            "action": "store",
            "type": str,
            "dest": "set",
            "metavar": "rotate",
            "help": "Set the Rotation lock.",
            "choices": BOOLEANS,
        },
        "config",
    ),
    (
        "state",
        {
            "nargs": "?",
            "action": "store",
            "default": None,
            "help": "Enable/Disable the Rotation lock",
            "choices": BOOLEANS,
        },
        "config",
    ),
]
DESCRIPTION = "System Screen Rotation Management Module"


def config(arguments):
    if arguments.toggle:
        try:
            send_message(arguments.socket, HOOK_ROTATE, None, None, {"toggle": True})
        except OSError as err:
            print_error(
                "An excepton was raised when attempting to set the Rotation Lock!",
                err,
                True,
            )
    else:
        if arguments.state:
            lock = not boolean(arguments.state)
        elif arguments.set:
            lock = boolean(arguments.set)
        else:
            lock = arguments.enable and not arguments.disable
        try:
            send_message(arguments.socket, HOOK_ROTATE, None, None, {"lock": lock})
        except OSError as err:
            print_error(
                "An excepton was raised when attempting to set the Rotation Lock!",
                err,
                True,
            )
        finally:
            del lock


def default(arguments):
    try:
        query = send_message(
            arguments.socket, HOOK_ROTATE, (HOOK_ROTATE, "lock"), None, {"query": True}
        )
    except OSError as err:
        print_error(
            "Attempting to retrive Rotation Lock state raised an exception!", err, True
        )
    else:
        print(
            "Screen Rotation Lock is %s!"
            % ("enabled" if query.get("lock") else "disabled")
        )
        del query


# EOF
