#!/usr/bin/false
# Module: CPU (System)
#
# Sets and changes the System CPU Power settings.
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

from glob import glob
from os.path import exists
from lib.util import read, write, read_json, write_json, boolean, clean_path
from lib.constants import (
    EMPTY,
    NEWLINE,
    CPU_PATH,
    HOOK_CPU,
    CONFIG_CPU,
    HOOK_STARTUP,
    CPU_PATH_MIN,
    CPU_PATH_MAX,
    HOOK_SHUTDOWN,
    HOOK_HIBERNATE,
    CPU_PATH_TURBO,
    CPU_PATH_CURRENT,
    MESSAGE_TYPE_PRE,
    CPU_PATH_GOVERNOR,
    CPU_PATH_TURBO_MIN,
    CPU_PATH_TURBO_MAX,
    CPU_PATH_GOVERNORS,
    MESSAGE_TYPE_CONFIG,
    CPU_PATH_MIN_SCALING,
    CPU_PATH_MAX_SCALING,
    CPU_PATH_PERFORMANCE,
    CPU_PATH_PERFORMANCES,
)

HOOKS_SERVER = {
    HOOK_CPU: "config",
    HOOK_STARTUP: "startup",
    HOOK_SHUTDOWN: "shutdown",
    HOOK_HIBERNATE: "startup",
}


def shutdown(server):
    _save_cpu(server)
    try:
        i = get_cpu()
    except (ValueError, OSError) as err:
        return server.error("Error reading CPU settings!", err=err)
    i["turbo"] = 1
    i["turbo_min"] = 10
    i["turbo_max"] = 100
    for c in i["cpus"].values():
        c["scale_min"] = c["min"]
        c["scale_max"] = c["max"]
        c["governor"] = c["governor_list"][0]
        c["performance"] = c["performance_list"][0]
    _set_cpu(server, i)
    del i


def _get_socket(cpu):
    try:
        return {
            "min": int(read(f"{cpu}/{CPU_PATH_MIN}"), 10),
            "max": int(read(f"{cpu}/{CPU_PATH_MAX}"), 10),
            "scale_min": int(read(f"{cpu}/{CPU_PATH_MIN_SCALING}"), 10),
            "scale_max": int(read(f"{cpu}/{CPU_PATH_MAX_SCALING}"), 10),
            "current": int(read(f"{cpu}/{CPU_PATH_CURRENT}"), 10),
            "governor": (
                read(f"{cpu}/{CPU_PATH_GOVERNOR}").strip().replace(NEWLINE, EMPTY)
            ),
            "governor_list": (
                read(f"{cpu}/{CPU_PATH_GOVERNORS}")
                .strip()
                .replace(NEWLINE, EMPTY)
                .split(" ")
            ),
            "performance": (
                read(f"{cpu}/{CPU_PATH_PERFORMANCE}").strip().replace(NEWLINE, EMPTY)
            ),
            "performance_list": (
                read(f"{cpu}/{CPU_PATH_PERFORMANCES}")
                .strip()
                .replace(NEWLINE, EMPTY)
                .split(" ")
            ),
        }
    except (ValueError, OSError) as err:
        raise OSError(f'Error reading CPU "{cpu}" values: {err}')


def _save_cpu(server):
    server.debug("Saving CPU state information..")
    try:
        i = get_cpu()
    except (ValueError, OSError) as err:
        return server.error("Error reading CPU settings!", err=err)
    try:
        write_json(CONFIG_CPU, i, perms=0o640)
    except OSError as err:
        server.error("Error saving CPU power state!", err=err)
    del i


def _set_cpu(server, info):
    for n, c in info["cpus"].items():
        try:
            p = clean_path(f"{CPU_PATH}/{n}", CPU_PATH)
        except ValueError as err:
            return server.error(f'Error cleaning CPU path "{n}"!', err=err)
        if not exists(p):
            return server.error(f'Requested CPU path "{p}" does not exist!')
        try:
            if "scale_min" in c:
                server.debug(f'Setting CPU "{n}" minimum to "{c["scale_min"]}"')
                write(f"{p}/{CPU_PATH_MIN_SCALING}", str(c["scale_min"]))
            if "scale_max" in c:
                server.debug(f'Setting CPU "{n}" maximum to "{c["scale_max"]}"')
                write(f"{p}/{CPU_PATH_MAX_SCALING}", str(c["scale_max"]))
            if "governor" in c:
                server.debug(f'Setting CPU "{n}" governor to "{c["governor"]}"')
                write(f"{p}/{CPU_PATH_GOVERNOR}", c["governor"])
            if "performance" not in c:
                continue
            server.debug(f'Setting CPU "{n}" power governor to "{c["performance"]}"')
            try:
                write(f"{p}/{CPU_PATH_PERFORMANCE}", c["performance"])
            except OSError as err:
                # NOTE(dij): Catch a bug in the "intel_pstate" driver causing
                #            a "Device or Resource Busy" error (16).
                if err.errno == 16:
                    server.info(
                        f'Bug setting CPU "{n}" power governor to "{c["performance"]}"!'
                    )
                    continue
                raise err
        except OSError as err:
            return server.error(f'Error setting CPU values for "{c}"!', err=err)
        del p
    if "turbo" in info:
        server.debug(f'Setting CPU turbo mode to "{info["turbo"]}"')
        try:
            write(CPU_PATH_TURBO, "0" if boolean(info["turbo"]) else "1")
        except OSError as err:
            server.error("Error setting CPU Turbo state!", err=err)
    if "turbo_min" in info:
        server.debug(f'Setting CPU turbo minimum to "{info["turbo_min"]}%"')
        try:
            write(CPU_PATH_TURBO_MIN, str(info["turbo_min"]))
        except OSError as err:
            server.error("Error setting CPU Turbo minimum!", err=err)
    if "turbo_max" in info:
        server.debug(f'Setting CPU turbo minimum to "{info["turbo_max"]}%"')
        try:
            write(CPU_PATH_TURBO_MAX, str(info["turbo_max"]))
        except OSError as err:
            server.error("Error setting CPU Turbo maximum!", err=err)


def get_cpu(selector=None):
    if isinstance(selector, str) and len(selector) > 0:
        if "/" in selector or "\\" in selector:
            raise OSError(f'Invalid CPU Selector "{selector}"')
        c = list()
        if "," in selector:
            for n in selector.split(","):
                p = clean_path(
                    f"{CPU_PATH}/cpu{n.strip().lower().replace('cpu', EMPTY)}", CPU_PATH
                )
                if exists(p):
                    c.append(p)
                    continue
                del p
                raise OSError(f'Cannot find CPU "{n}"')
        else:
            n = selector.strip().lower().replace("cpu", EMPTY)
            p = clean_path(f"{CPU_PATH}/cpu{n}", CPU_PATH)
            if exists(p):
                c.append(p)
            else:
                raise OSError(f'Cannot find CPU "{n}"')
            del n
            del p
    else:
        c = glob(f"{CPU_PATH}/cpu[0-9+]")
    i = {"cpus": dict(), "turbo": not boolean(read(CPU_PATH_TURBO, errors=False))}
    for v in c:
        i["cpus"][v.replace(CPU_PATH, EMPTY).replace("/", EMPTY)] = _get_socket(v)
    try:
        i["turbo_min"] = int(read(CPU_PATH_TURBO_MIN), 10)
        i["turbo_max"] = int(read(CPU_PATH_TURBO_MAX), 10)
    except (ValueError, OSError) as err:
        raise OSError(f"Error reading CPU Turbo values: {err}")
    return i


def config(server, message):
    if message.cpus is None and message.type != MESSAGE_TYPE_CONFIG:
        return
    try:
        i = get_cpu()
    except (ValueError, OSError) as err:
        server.error("Error reading CPU settings!", err=err)
        return {"error": str(err)}
    try:
        validate_cpu(message, i)
    except (ValueError, OSError) as err:
        server.error("Error validating CPU settings!", err=err)
        return {"error": str(err)}
    del i
    _set_cpu(server, message)
    _save_cpu(server)
    if message.get("ping", False):
        return True
    return None


def validate_cpu(base, info):
    if "turbo_min" in base and not (0 <= base["turbo_min"] <= 100):
        raise ValueError(
            f'CPU turbo_min "{base["turbo_min"]}" must be between 0 and 100'
        )
    if "turbo_max" in base and not (0 <= base["turbo_max"] <= 100):
        raise ValueError(
            f'CPU turbo_max "{base["turbo_max"]}" must be between 0 and 100'
        )
    if (
        "turbo_max" in base
        and "turbo_min" in base
        and base["turbo_max"] < base["turbo_min"]
    ):
        raise ValueError("CPU turbo_min cannot be greater than turbo_max")
    for n, c in base["cpus"].items():
        if n not in info["cpus"]:
            raise ValueError(f'Base contains CPU "{n}" that is not present')
        _validate_socket(n, c, info["cpus"][n])


def startup(server, message):
    if message.header() == HOOK_HIBERNATE and message.type == MESSAGE_TYPE_PRE:
        return shutdown(server)
    try:
        d = read_json(CONFIG_CPU)
    except OSError as err:
        return server.error("Error reading saved CPU power state!", err=err)
    _set_cpu(server, d)
    del d


def print_frequency(frequency):
    f = frequency / 1000
    if f < 1000:
        return f"{f:.2f} MHz"
    return f"{round(float(f) / float(1000), 2):.2f} GHz"


def _validate_socket(name, base, info):
    if "scale_min" in base and not (info["min"] <= base["scale_min"] <= info["max"]):
        raise ValueError(
            f'CPU "{name}" min "{print_frequency(base["scale_min"])}" must be between '
            f'"{print_frequency(info["min"])}" and "{print_frequency(info["max"])}"'
        )
    if "scale_max" in base and not (info["min"] <= base["scale_max"] <= info["max"]):
        raise ValueError(
            f'CPU "{name}" max "{print_frequency(base["scale_max"])}" must be between '
            f'"{print_frequency(info["min"])}" and "{print_frequency(info["max"])}"'
        )
    if (
        "scale_max" in base
        and "scale_min" in base
        and base["scale_max"] < base["scale_min"]
    ):
        raise ValueError(
            f'CPU "{name}" max "{print_frequency(base["scale_max"])}" cannot be less '
            f'than min "{print_frequency(base["scale_min"])}"'
        )
    if "governor" in base and base["governor"] not in info["governor_list"]:
        raise ValueError(
            f'CPU "{name}" governor must be one of the following "{", ".join(info["governor_list"])}"'
        )
    if "performance" in base and base["performance"] not in info["performance_list"]:
        raise ValueError(
            f'CPU "{name}" power governor must be one of the following "{", ".join(info["performance_list"])}"'
        )
