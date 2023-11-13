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

# __init__.py
#   The Utils Python package is used to help assist with simple repeatable functions
#   that may be used across SMD. Functions are broken out into multiple sub-package
#   files and some very generic ones may be placed here.

from time import time


def nes(v):
    return isinstance(v, str) and len(v) > 0


def seconds():
    return round(time())


def boolean(value):
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, int) or isinstance(value, float):
        return value > 0
    if isinstance(value, str):
        if len(value) == 0:
            return False
        v = value.lower().strip()
        try:
            return v[0] == "t" or v[0] == "y" or v[0] == "e" or v == "1" or v == "on"
        finally:
            del v
    return False


def num(val, neg=True):
    if val is None:
        return 0
    if isinstance(val, bool):
        return 1 if val else 0
    if isinstance(val, int):
        if not neg and val < 0:
            return abs(val)
        return val
    if isinstance(val, float):
        if not neg and val < 0:
            return abs(round(val))
        return round(val)
    if not isinstance(val, str):
        raise ValueError("value is not an int or string")
    if len(val) == 0:
        return 0
    if not neg:
        return abs(int(val, 10))
    return int(val, 10)


def cancel_nul(server, event):
    if event is None:
        return None
    server.cancel(event)
    return None


def time_to_str(value, now=None):
    if now is None:
        now = seconds()
    if value is None:
        return "Until Reboot"
    n = round(value - now)
    if n <= 0:
        return "0s"
    if n <= 60:
        return f"{n}s"
    if n > 60:
        m = n // 60
        s = n - (m * 60)
        del n
        return f"{m}m" if s == 0 else f"{m}m {s}s"
    return None
