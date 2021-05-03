#!/usr/bin/false
# PowerCTL Module: Rotate
#  powerctl rotate, rotatectl, rotate
#
# PowerCTL command line user module to configure screen rotaion options.
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

from lib.util import boolean, print_error
from lib.structs.message import send_message
from lib.constants import HOOK_ROTATE, MESSAGE_TYPE_STATUS, MESSAGE_TYPE_CONFIG


def config(arguments):
    message = {"type": MESSAGE_TYPE_CONFIG}
    if arguments.toggle:
        message["toggle"] = True
    elif arguments.state:
        message["lock"] = not boolean(arguments.state)
    elif arguments.set:
        message["lock"] = boolean(arguments.set)
    else:
        message["lock"] = arguments.enable and not arguments.disable
    try:
        send_message(arguments.socket, HOOK_ROTATE, None, None, message)
    except OSError as err:
        print_error(
            "An exception was raised when attempting to set the Rotation Lock!",
            err,
            True,
        )
    del message


def default(arguments):
    try:
        query = send_message(
            arguments.socket,
            HOOK_ROTATE,
            (HOOK_ROTATE, "lock"),
            payload={"type": MESSAGE_TYPE_STATUS},
        )
    except OSError as err:
        return print_error(
            "Attempting to retrive Rotation Lock state raised an exception!", err, True
        )
    print(f'Screen Rotation Lock is {"enabled" if query["lock"] else "disabled"}')
    del query
