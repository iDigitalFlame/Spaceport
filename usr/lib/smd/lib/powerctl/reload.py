#!/usr/bin/false
# PowerCTL Module: Reload
#  powerctl reload, reloadctl, reload
#
# PowerCTL command line user module to reload the system configuration.
#
# System Management Daemon
#
# Copyright (C) 2016 - 2022 iDigitalFlame
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

from lib.util import print_error
from lib.structs.message import send_message
from lib.constants import HOOK_LOG, HOOK_RELOAD


def default(arguments):
    try:
        if arguments.level > -1 and arguments.level < 5:
            send_message(arguments.socket, HOOK_LOG, payload={"level": arguments.level})
        if arguments.no_reload:
            return
        send_message(arguments.socket, HOOK_RELOAD, payload={"all": arguments.all})
    except OSError as err:
        return print_error("Error sending a Reload message!", err)
    print("Sent a Reload message to the system.")
