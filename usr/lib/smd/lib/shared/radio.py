################################
### iDigitalFlame  2016-2026 ###
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
# Copyright (C) 2016 - 2026 iDigitalFlame
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

# Shared Module Dependencies: Radio
#   Used to keep links un-borken for non-default configurations of directories

from lib.util import boolean
from lib.constants.config import TIMEOUT_SEC_MESSAGE
from lib import check_error, print_error, send_message
from lib.constants import BOOLEANS, HOOK_RADIO, MSG_ACTION, MSG_CONFIG, MSG_STATUS


def get_status(args, radio):
    try:
        r = send_message(
            args.socket,
            HOOK_RADIO,
            (HOOK_RADIO, "state"),
            TIMEOUT_SEC_MESSAGE,
            {"type": MSG_STATUS, "radio": radio},
        )
    except Exception as err:
        return print_error(f'Cannot query the "{radio}" status!', err)
    check_error(r, f'Cannot retrive the "{radio}" status')
    print(f'Status of "{radio}":\n  - State: {"Enabled" if r.state else "Disabled"}')
    print(f'  - Boot : {"Enabled" if r.boot else "Disabled"}')
    del r
    return True


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
