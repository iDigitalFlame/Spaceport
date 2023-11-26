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


def fnv32(v):
    d, h = v.encode("UTF-8"), 0x811C9DC5
    for i in d:
        h *= 0x1000193
        h = h & 0xFFFFFFFF
        h ^= i
        h = h & 0xFFFFFFFF
    del d
    return h


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
    if isinstance(value, bool) and value:
        return "Ability Disabled"
    t = round(value - now)
    if t <= 0:
        return "0s"
    if t < 60:
        return f"{t}s"
    h = round(t // 3600)
    t -= h * 3600
    m = round(t // 60)
    s = round(t - (m * 60))
    if h == 0:
        return f"{m}m" if s == 0 else f"{m}m {s}s"
    if m == 0:
        return f"{h}hr" if s == 0 else f"{h}hr {s}s"
    return f"{h}hr {m}m" if m > 0 and s == 0 else f"{h}hr {m}m {s}s"
