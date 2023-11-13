#!/usr/bin/false
################################
### iDigitalFlame  2016-2024 ###
#                              #
#            -/`               #
#            -yy-   :/`        #
#         ./-shho`:so`         #
#    .:- /syhhhh//hhs` `-`     #
#   :ys-:shhhhhhshhhh.:o- `    #
#   /yhsoshhhhhhhhhhhyho`:/.   #
#   `:yhyshhhhhhhhhhhhhh+hd:   #
#     :yssyhhhhhyhhhhhhhhdd:   #
#    .:.oyshhhyyyhhhhhhddd:    #
#    :o+hhhhhyssyhhdddmmd-     #
#     .+yhhhhyssshdmmddo.      #
#       `///yyysshd++`         #
#                              #
########## SPACEPORT ###########
### Spaceport + SMD
#
# Copyright (C) 2016 - 2024 iDigitalFlame
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

# Shared Module Dependencies: Wireless
#   Used to keep links un-borken for non-default configurations of directories

from lib.util import boolean
from lib import send_message, print_error
from lib.constants import BOOLEANS, HOOK_RADIO, MSG_ACTION, MSG_CONFIG


def set_command(args, radio, force=False):
    c = args.command.lower()
    if c in BOOLEANS:
        _set(args.socket, radio, None, boolean(c), False, force or args.force)
        return True
    if args.args is not None and len(args.args) > 0:
        if c == "set":
            _set(
                args.socket,
                radio,
                None,
                boolean(args.args[0]),
                False,
                force or args.force,
            )
        elif c == "boot":
            _set(args.socket, radio, args.args[0])
        else:
            return False
        return True
    del c
    return False


def set_config(args, radio, toggle=None, force=False):
    if callable(toggle) and args.toggle:
        return _set(args.socket, radio, None, not toggle())
    if args.boot:
        return _set(args.socket, radio, args.boot)
    return _set(
        args.socket, radio, None, args.enable, args.disable, force or args.force
    )


def _set(sock, radio, boot, enable=False, disable=False, force=False):
    m = {"radio": radio, "force": force}
    if boot is not None:
        m["type"], m["boot"] = MSG_CONFIG, boolean(boot)
        print(
            f'Setting "{radio}" boot status to "{"Enabled" if m["boot"] else "Disabled"}".'
        )
    else:
        m["type"], m["enabled"] = MSG_ACTION, enable and not disable
        print(
            f'Setting "{radio}" status to "{"Enabled" if m["enabled"] else "Disabled"}".'
        )
    try:
        send_message(sock, HOOK_RADIO, payload=m)
    except Exception as err:
        return print_error(f'Cannot set the "{radio}" status!', err)
    del m
    return True
