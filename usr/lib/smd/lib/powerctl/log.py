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

# PowerCTL Module: Log
#   Command line user module to change the logging level for the current SMD
#   session. This module is NOT linked using the "*ctl" file schema and must be
#   used through powerctl as "powerctl log".

from lib import print_error, send_message
from lib.constants import HOOK_LOG, LOG_INDEX, LOG_LEVELS


def default(args):
    if not args.level:
        return
    if isinstance(args.level, int):
        if args.level not in LOG_INDEX:
            return print_error(f'Log level "{args.level}" is invalid!')
        n = args.level
    elif isinstance(args.level, str):
        if len(args.level) == 0:
            return print_error("Log level cannot be empty!")
        n = LOG_LEVELS.get(args.level.lower())
        if n is None:
            return print_error(f'Log level "{args.level}" is invalid!')
    else:
        return print_error("Log level is invalid!")
    try:
        send_message(args.socket, HOOK_LOG, payload={"level": n})
    except Exception as err:
        return print_error("Cannot set the Log level!", err)
    finally:
        del n
