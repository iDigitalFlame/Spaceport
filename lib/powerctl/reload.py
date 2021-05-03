#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame 2018
#
# PowerCTL Module: Reload
#  powerctl reolad, reloadctl, reload
#
# PowerCTL command line user module to reload the system configuration.
# Updated 10/2018

from lib.util import print_error
from lib.constants import HOOK_RELOAD
from lib.structs.message import send_message

DESCRIPTION = "System Configuration Reload Module"


def default(arguments):
    try:
        send_message(arguments.socket, HOOK_RELOAD)
    except OSError as err:
        print_error(
            "Attempting to send a reload message raised an exception!", err, True
        )
    else:
        print("Sent a reload message to the system..")


# EOF
