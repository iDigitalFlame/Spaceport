#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame
#
# PowerCTL Module: Lock
#  powerctl lock, lockctl, lock
#
# PowerCTL command line user module to lock the screen session.

from lib.util import print_error
from lib.structs.message import send_message
from lib.constants import HOOK_POWER, HOOK_LOCK

ARGS = [
    (
        "-f",
        {
            "required": False,
            "action": "store_true",
            "dest": "force",
            "help": "Force lock screen regardless of locker settings",
        },
    ),
    (
        "-t",
        {
            "required": False,
            "action": "store",
            "type": int,
            "dest": "hibernate",
            "metavar": "hibernate",
            "help": "Set the hibernate locker timeout (in seconds) on lock, zero to disable.",
        },
    ),
    (
        "-kt",
        {
            "required": False,
            "action": "store",
            "type": int,
            "dest": "hibernate_force",
            "metavar": "hibernate",
            "help": "Force set the hibernate locker timeout (in seconds) on lock, zero to disable.",
        },
    ),
    (
        "timeout",
        {
            "nargs": "?",
            "action": "store",
            "default": None,
            "help": "Set the hibernate locker timeout (in seconds) on lock, zero to disable.",
        },
    ),
]
DESCRIPTION = "System Lock Screen Management Module"


def default(arguments):
    if arguments.hibernate or arguments.hibernate_force or arguments.timeout:
        timeout = arguments.timeout
        if timeout is None and arguments.hibernate:
            timeout = arguments.hibernate
        elif timeout is None and arguments.hibernate_force:
            timeout = arguments.hibernate_force
        try:
            timeout = int(timeout)
        except ValueError as err:
            print_error("Hibernate timeout must be a number!", err, True)
            exit(1)
        else:
            if timeout < 0:
                timeout = None
            try:
                send_message(
                    arguments.socket,
                    HOOK_POWER,
                    None,
                    None,
                    {
                        "type": "locker",
                        "action": "set",
                        "name": "hibernate",
                        "expire": timeout,
                        "force": bool(arguments.hibernate_force),
                    },
                )
            except OSError as err:
                print_error(
                    "Attempting to update Lock Hibernate timeout raised an exception!",
                    err,
                    True,
                )
        finally:
            if timeout is not None:
                del timeout
    try:
        send_message(
            arguments.socket, HOOK_LOCK, None, None, {"force": arguments.force}
        )
    except OSError as err:
        print_error(
            "Attempting to trigger the Lock Screen raised an exception!", err, True
        )
