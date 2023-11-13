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

# Module: System/CPU
#   Sets and changes the System CPU Power settings. Allows CPU settings to be
#   controlled from userspace.

from os.path import exists
from lib.util import boolean
from lib.util.file import write, clean
from lib.shared.cpu import cpu, validate
from lib.structs import Message, as_error
from lib.constants import (
    MSG_PRE,
    HOOK_CPU,
    MSG_CONFIG,
    HOOK_STARTUP,
    HOOK_SHUTDOWN,
    HOOK_HIBERNATE,
)
from lib.constants.config import (
    CPU_PATH,
    CPU_PATH_TURBO,
    CPU_PATH_GOVERNOR,
    CPU_PATH_TURBO_MIN,
    CPU_PATH_TURBO_MAX,
    CPU_PATH_SCALING_MIN,
    CPU_PATH_SCALING_MAX,
    CPU_PATH_PERFORMANCE,
)

HOOKS_SERVER = {
    HOOK_CPU: "config",
    HOOK_STARTUP: "startup",
    HOOK_SHUTDOWN: "shutdown",
    HOOK_HIBERNATE: "startup",
}


def _save(server):
    server.debug("[m/cpu]: Saving CPU state information..")
    try:
        x = cpu(all=False)
    except (ValueError, OSError) as err:
        return server.error("[m/cpu]: Cannot read CPU information!", err)
    server.set("cpu", x)
    server.save()
    del x


def shutdown(server):
    _save(server)
    try:
        x = cpu(all=False)
    except (ValueError, OSError) as err:
        return server.error("[m/cpu]: Cannot read CPU information!", err)
    x["turbo"], x["turbo_min"], x["turbo_max"] = 1, 10, 100
    for c in x["cpus"].values():
        c["scale_min"], c["scale_max"] = c["min"], c["max"]
        if "performance" in c["governor_list"]:
            # NOTE(dij): Setting the max value "performance" (if supported) to
            #            prevent the CPU setting bug that occurs with the "default"
            #            setting value. Falls back to the default if not supported.
            c["governor"] = "performance"
        else:
            c["governor"] = c["governor_list"][0]
        if "performance" in c["performance_list"]:
            # NOTE(dij): Setting the max value "performance" (if supported) to
            #            prevent the CPU setting bug that occurs with the "default"
            #            setting value. Falls back to the default if not supported.
            c["performance"] = "performance"
        else:
            c["performance"] = c["performance_list"][0]
    _set(server, x)
    del x


def _set(server, info):
    if not isinstance(info, (dict, Message)) or "cpus" not in info:
        return server.warning(
            "[m/cpu]: Attempted to set CPU info with an empty data set!"
        )
    for n, c in info["cpus"].items():
        try:
            p = clean(f"{CPU_PATH}/{n}", CPU_PATH)
        except ValueError as err:
            return server.error(
                f'[m/cpu]: Cannot use the malformed CPU path "{n}"!', err
            )
        if not exists(p):
            return server.error(f'[m/cpu]: Supplied CPU "{p}" does not exist!')
        try:
            if "scale_min" in c:
                server.debug(
                    f'[m/cpu]: Setting the CPU "{n}" minimum to "{c["scale_min"]}"'
                )
                write(f"{p}/{CPU_PATH_SCALING_MIN}", f'{c["scale_min"]}')
            if "scale_max" in c:
                server.debug(
                    f'[m/cpu]: Setting the CPU "{n}" maximum to "{c["scale_max"]}"'
                )
                write(f"{p}/{CPU_PATH_SCALING_MAX}", f'{c["scale_max"]}')
            if "governor" in c:
                server.debug(
                    f'[m/cpu]: Setting the CPU "{n}" governor to "{c["governor"]}"'
                )
                write(f"{p}/{CPU_PATH_GOVERNOR}", c["governor"])
            if "performance" not in c:
                continue
            server.debug(
                f'[m/cpu]: Setting the CPU "{n}" power governor to "{c["performance"]}"'
            )
            try:
                write(f"{p}/{CPU_PATH_PERFORMANCE}", c["performance"])
            except OSError as err:
                # NOTE(dij): Catch a bug in the "intel_pstate" driver causing
                #            a "Device or Resource Busy" error (16).
                if err.errno == 0x10:
                    server.info(
                        f'[m/cpu]: Caught bug setting the CPU "{n}" power governor to "{c["performance"]}"!'
                    )
                    continue
                raise err
        except OSError as err:
            return server.error(f'[m/cpu]: Cannot set the CPU values for "{c}"!', err)
        del p
    if "turbo" in info:
        server.debug(f'[m/cpu]: Setting the CPU turbo mode to "{info["turbo"]}"')
        try:
            write(CPU_PATH_TURBO, "0" if boolean(info["turbo"]) else "1")
        except OSError as err:
            server.error("[m/cpu]: Cannot set the CPU Turbo mode!", err)
    if "turbo_min" in info:
        server.debug(
            f'[m/cpu]: Setting the CPU turbo minimum to "{info["turbo_min"]}%"'
        )
        try:
            write(CPU_PATH_TURBO_MIN, f'{info["turbo_min"]}')
        except OSError as err:
            server.error("[m/cpu]: Cannot set the CPU Turbo minimum!", err)
    if "turbo_max" in info:
        server.debug(
            f'[m/cpu]: Setting the CPU turbo minimum to "{info["turbo_max"]}%"'
        )
        try:
            write(CPU_PATH_TURBO_MAX, f'{info["turbo_max"]}')
        except OSError as err:
            server.error("[m/cpu]: Cannot set the CPU Turbo maximum!", err)


def config(server, message):
    if message.type != MSG_CONFIG:
        return
    try:
        x = cpu()
    except (ValueError, OSError) as err:
        server.error("[m/cpu]: Cannot read CPU information!", err)
        return as_error(f"error reading CPU information: {err}")
    try:
        validate(message, x)
    except TypeError:
        server.error("[m/cpu]: Malformed CPU information received!")
        return as_error("invalid CPU information: malformed data")
    except ValueError as err:
        server.error("[m/cpu]: Invalid CPU information received!", err)
        return as_error(f"invalid CPU information: {err}")
    del x
    _set(server, message)
    _save(server)
    if message.ping:
        return True
    return None


def startup(server, message):
    if message.header() == HOOK_HIBERNATE and message.type == MSG_PRE:
        return shutdown(server)
    d = server.get("cpu")
    # NOTE(dij): We don't have to re-validate this info as we clean it in "_set"
    #            anyway.
    _set(server, d)
    del d
