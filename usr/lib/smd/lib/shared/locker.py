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

# Shared Module Dependencies: Locker
#   Used to keep links un-borken for non-default configurations of directories

from re import compile
from lib import print_error
from lib.util import boolean
from datetime import timedelta
from lib.constants import EMPTY
from lib.constants.config import LOCKER_TYPE_NAMES

_PARSER = compile(r"((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?")


def _parse(v):
    try:
        return int(v)
    except ValueError:
        pass
    r = _PARSER.match(v.replace(" ", EMPTY).lower())
    if r is None:
        return None
    a = dict()
    for k, v in r.groupdict().items():
        if v is None:
            continue
        try:
            a[k] = int(v)
        except ValueError:
            pass
    del r
    return timedelta(**a).seconds


def pase_locker(entries, locker, arg, force):
    if arg is None and force is None:
        return
    v = force if force is not None else arg
    if boolean(v):
        return entries.append(
            {"name": locker, "time": None, "force": force is not None}
        )
    try:
        n = _parse(v)
    except ValueError as err:
        return print_error(
            f'Cannot parse "{LOCKER_TYPE_NAMES.get(locker, locker)}" value: {err}'
        )
    finally:
        del v
    entries.append({"name": locker, "time": n, "force": force is not None})
    del n
