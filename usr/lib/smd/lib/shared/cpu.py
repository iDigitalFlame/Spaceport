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

# Shared Module Dependencies: CPU
#   Used to keep links un-borken for non-default configurations of directories

from glob import glob
from os.path import exists
from lib.constants import EMPTY
from lib.util import boolean, num, nes
from lib.util.file import read, clean
from lib.constants.config import (
    CPU_PATH,
    CPU_PATH_MIN,
    CPU_PATH_MAX,
    CPU_PATH_TURBO,
    CPU_PATH_CURRENT,
    CPU_PATH_GOVERNOR,
    CPU_PATH_GOVERNORS,
    CPU_PATH_TURBO_MIN,
    CPU_PATH_TURBO_MAX,
    CPU_PATH_SCALING_MIN,
    CPU_PATH_SCALING_MAX,
    CPU_PATH_PERFORMANCE,
    CPU_PATH_PERFORMANCES,
    CPU_PATH_TURBO_CURRENT,
)


def _socket(cpu, all):
    v = num(read(f"{cpu}/{CPU_PATH_CURRENT}"), False)
    d = {
        "min": num(read(f"{cpu}/{CPU_PATH_MIN}"), False),
        "max": num(read(f"{cpu}/{CPU_PATH_MAX}"), False),
        "scale_min": num(read(f"{cpu}/{CPU_PATH_SCALING_MIN}"), False),
        "scale_max": num(read(f"{cpu}/{CPU_PATH_SCALING_MAX}"), False),
        "governor": (read(f"{cpu}/{CPU_PATH_GOVERNOR}", strip=True)),
        "governor_list": (read(f"{cpu}/{CPU_PATH_GOVERNORS}", strip=True).split(" ")),
        "performance": (read(f"{cpu}/{CPU_PATH_PERFORMANCE}", strip=True)),
        "performance_list": (
            read(f"{cpu}/{CPU_PATH_PERFORMANCES}", strip=True).split(" ")
        ),
    }
    if all:
        d["current"] = v
    del v
    return d


def validate(check, info):
    if "turbo_min" in check and not (0 <= check["turbo_min"] <= 100):
        raise ValueError(
            f'turbo_min value "{check["turbo_min"]}" must be between 0 and 100'
        )
    if "turbo_max" in check and not (0 <= check["turbo_max"] <= 100):
        raise ValueError(
            f'turbo_max value "{check["turbo_max"]}" must be between 0 and 100'
        )
    if (
        "turbo_max" in check
        and "turbo_min" in check
        and check["turbo_max"] < check["turbo_min"]
    ):
        raise ValueError("turbo_min cannot be greater than turbo_max")
    if "cpus" not in check:
        return
    if "cpus" not in info:
        if "cpus" in check:
            del check["cpus"]
        return
    for n, c in check["cpus"].items():
        if "/" in n or "\\" in n:
            raise ValueError(f'invalid CPU name "{n}"')
        if n not in info["cpus"]:
            raise ValueError(f'contents has CPU "{n}" that is not present')
        _validate_socket(n, c, info["cpus"][n])


def freq_to_str(frequency):
    f = frequency / 1000
    if f < 1000:
        return f"{f:.2f} MHz"
    return f"{round(float(f) / float(1000), 2):.2f} GHz"


def cpu(selector=None, all=True):
    if nes(selector):
        if "/" in selector or "\\" in selector:
            raise ValueError(f'invalid CPU selector "{selector}"')
        c = list()
        if "," in selector:
            for n in selector.split(","):
                p = clean(
                    f"{CPU_PATH}/cpu{n.strip().lower().replace('cpu', EMPTY)}", CPU_PATH
                )
                if not exists(p):
                    raise OSError(f'cannot find CPU "{n}"')
                c.append(p)
                del p
        else:
            p = clean(
                f"{CPU_PATH}/cpu{selector.strip().lower().replace('cpu', EMPTY)}",
                CPU_PATH,
            )
            if not exists(p):
                raise OSError(f'cannot find CPU "{selector}"')
            c.append(p)
            del p
    else:
        c = glob(f"{CPU_PATH}/cpu[0-9+]")
    i = {
        "cpus": dict(),
        "turbo": not boolean(read(CPU_PATH_TURBO, errors=False, strip=True)),
    }
    for v in c:
        try:
            i["cpus"][v.replace(CPU_PATH, EMPTY).replace("/", EMPTY)] = _socket(v, all)
        except (ValueError, OSError) as err:
            raise OSError(f'cannot read CPU "{cpu}" info: {err}')
    try:
        i["turbo_min"] = num(read(CPU_PATH_TURBO_MIN, strip=True), False)
        i["turbo_max"] = num(read(CPU_PATH_TURBO_MAX, strip=True), False)
        if all:
            i["turbo_current"] = num(read(CPU_PATH_TURBO_CURRENT, strip=True), False)
    except (ValueError, OSError) as err:
        raise OSError(f"cannot read CPU turbo info: {err}")
    return i


def _validate_socket(name, check, info):
    if "scale_min" in check and not (info["min"] <= check["scale_min"] <= info["max"]):
        raise ValueError(
            f'CPU "{name}" min "{freq_to_str(check["scale_min"])}" must be between '
            f'"{freq_to_str(info["min"])}" and "{freq_to_str(info["max"])}"'
        )
    if "scale_max" in check and not (info["min"] <= check["scale_max"] <= info["max"]):
        raise ValueError(
            f'CPU "{name}" max "{freq_to_str(check["scale_max"])}" must be between '
            f'"{freq_to_str(info["min"])}" and "{freq_to_str(info["max"])}"'
        )
    if (
        "scale_max" in check
        and "scale_min" in check
        and check["scale_max"] < check["scale_min"]
    ):
        raise ValueError(
            f'CPU "{name}" max "{freq_to_str(check["scale_max"])}" cannot be less '
            f'than min "{freq_to_str(check["scale_min"])}"'
        )
    if "governor" in check and check["governor"] not in info["governor_list"]:
        raise ValueError(
            f'CPU "{name}" governor must be one of the following "{", ".join(info["governor_list"])}"'
        )
    if "performance" in check and check["performance"] not in info["performance_list"]:
        raise ValueError(
            f'CPU "{name}" power governor must be one of the following "{", ".join(info["performance_list"])}"'
        )
