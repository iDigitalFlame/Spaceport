#!/usr/bin/false
# Module: CPU (System)
#
# Sets and changes the System CPU Power settings.
#
# System Management Daemon
#
# Copyright (C) 2016 - 2021 iDigitalFlame
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
from os.path import sep, exists
from lib.util import read, write, read_json, write_json, boolean
from lib.constants import (
    EMPTY,
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
        info = get_cpu()
    except (ValueError, OSError) as err:
        return server.error(
            "Attempting to read CPU settings raised an exception!", err=err
        )
    info["turbo"] = 1
    info["turbo_min"] = 10
    info["turbo_max"] = 100
    for cpu in info["cpus"].values():
        cpu["scale_min"] = cpu["min"]
        cpu["scale_max"] = cpu["max"]
        cpu["governor"] = cpu["governor_list"][0]
        cpu["performance"] = cpu["performance_list"][0]
    _set_cpu(server, info)
    del info


def _get_socket(cpu):
    try:
        return {
            "min": int(read(f"{cpu}/{CPU_PATH_MIN}", ignore_errors=False)),
            "max": int(read(f"{cpu}/{CPU_PATH_MAX}", ignore_errors=False)),
            "scale_min": int(
                read(f"{cpu}/{CPU_PATH_MIN_SCALING}", ignore_errors=False)
            ),
            "scale_max": int(
                read(f"{cpu}/{CPU_PATH_MAX_SCALING}", ignore_errors=False)
            ),
            "current": int(read(f"{cpu}/{CPU_PATH_CURRENT}", ignore_errors=False)),
            "governor": (
                read(f"{cpu}/{CPU_PATH_GOVERNOR}", ignore_errors=False)
                .strip()
                .replace("\n", EMPTY)
            ),
            "governor_list": (
                read(f"{cpu}/{CPU_PATH_GOVERNORS}", ignore_errors=False)
                .strip()
                .replace("\n", EMPTY)
                .split(" ")
            ),
            "performance": (
                read(f"{cpu}/{CPU_PATH_PERFORMANCE}", ignore_errors=False)
                .strip()
                .replace("\n", EMPTY)
            ),
            "performance_list": (
                read(f"{cpu}/{CPU_PATH_PERFORMANCES}", ignore_errors=False)
                .strip()
                .replace("\n", EMPTY)
                .split(" ")
            ),
        }
    except (ValueError, OSError) as err:
        raise OSError(f'Error reading CPU "{cpu}" values! ({err})')


def _save_cpu(server):
    server.debug("Attempting to save CPU state information..")
    try:
        info = get_cpu()
    except OSError as err:
        return server.error(
            "Attempting to read CPU settings raised an exception!", err=err
        )
    try:
        write_json(
            CONFIG_CPU, info, indent=4, sort=True, ignore_errors=False, perms=0o640
        )
    except OSError as err:
        server.error("Exception occurred saving CPU power state!", err=err)
    del info


def _set_cpu(server, info):
    for name, cpu in info["cpus"].items():
        path = f"{CPU_PATH}/%s" % name.replace("/", EMPTY).replace("\\", EMPTY)
        try:
            if "scale_min" in cpu:
                server.debug(f'Setting CPU "{name}" minimum to "{cpu["scale_min"]}"')
                write(
                    f"{path}/{CPU_PATH_MIN_SCALING}",
                    str(cpu["scale_min"]),
                    ignore_errors=False,
                )
            if "scale_max" in cpu:
                server.debug(f'Setting CPU "{name}" maximum to "{cpu["scale_max"]}"')
                write(
                    f"{path}/{CPU_PATH_MAX_SCALING}",
                    str(cpu["scale_max"]),
                    ignore_errors=False,
                )
            if "governor" in cpu:
                server.debug(f'Setting CPU "{name}" governor to "{cpu["governor"]}"')
                write(
                    f"{path}/{CPU_PATH_GOVERNOR}", cpu["governor"], ignore_errors=False
                )
            if "performance" in cpu:
                server.debug(
                    f'Setting CPU "{name}" power governor to "{cpu["performance"]}"'
                )
                try:
                    write(
                        f"{path}/{CPU_PATH_PERFORMANCE}",
                        cpu["performance"],
                        ignore_errors=False,
                    )
                except OSError as err:
                    # Catch a bug in the "intel_pstate" driver causing a "Device or Resource Busy" error (16)
                    if err.errno == 16:
                        server.info(
                            f'Caught a bug setting the CPU "{name}" power governor to "{cpu["performance"]}"! ({err})'
                        )
                    else:
                        raise err
        except OSError as err:
            server.error(
                f'Attempting to set CPU settings on "{cpu}" raised an exception!',
                err=err,
            )
        del path
    if "turbo" in info:
        server.debug(f'Setting CPU turbo mode to "{info["turbo"]}"')
        try:
            write(
                CPU_PATH_TURBO,
                "0" if boolean(info["turbo"]) else "1",
                ignore_errors=False,
            )
        except OSError as err:
            server.error(
                "Attempting to set CPU Turbo state raised an exception!", err=err
            )
    if "turbo_min" in info:
        server.debug(f'Setting CPU turbo minimum to "{info["turbo_min"]}%"')
        try:
            write(CPU_PATH_TURBO_MIN, str(info["turbo_min"]), ignore_errors=False)
        except OSError as err:
            server.error(
                "Attempting to set CPU Turbo minimum raised an exception!", err=err
            )
    if "turbo_max" in info:
        server.debug(f'Setting CPU turbo minimum to "{info["turbo_max"]}%"')
        try:
            write(CPU_PATH_TURBO_MAX, str(info["turbo_max"]), ignore_errors=False)
        except OSError as err:
            server.error(
                "Attempting to set CPU Turbo maximum raised an exception!", err=err
            )


def get_cpu(selector=None):
    if selector is not None:
        cpus = list()
        if "/" in selector or "\\" in selector:
            raise OSError(f'Invalid CPU Selector "{selector}"!')
        if "," in selector:
            for name in selector.split(","):
                path = f"{CPU_PATH}/cpu{name.strip().lower().replace('cpu', EMPTY)}"
                if exists(path):
                    cpus.append(path)
                else:
                    raise OSError(f'Cannot find CPU "{name}"!')
                del path
        else:
            name = selector.strip().lower().replace("cpu", EMPTY)
            path = f"{CPU_PATH}/cpu{name}"
            if exists(path):
                cpus.append(path)
            else:
                raise OSError(f'Cannot find CPU "{name}"!')
            del name
            del path
    else:
        cpus = glob(f"{CPU_PATH}/cpu[0-9+]")
    info = {
        "cpus": dict(),
        "turbo": not boolean(read(CPU_PATH_TURBO, ignore_errors=True)),
    }
    for c in cpus:
        info["cpus"][c.replace(CPU_PATH, EMPTY).replace(sep, EMPTY)] = _get_socket(c)
    try:
        info["turbo_min"] = int(read(CPU_PATH_TURBO_MIN, ignore_errors=False))
        info["turbo_max"] = int(read(CPU_PATH_TURBO_MAX, ignore_errors=False))
    except (ValueError, OSError) as err:
        raise OSError(f"Error reading CPU Turbo values! ({err})")
    return info


def config(server, message):
    if message.cpus is None and message.type != MESSAGE_TYPE_CONFIG:
        return
    try:
        info = get_cpu()
    except (ValueError, OSError) as err:
        return server.error(
            "Attempting to read CPU settings raised an exception!", err=err
        )
    try:
        validate_cpu(message, info)
    except (ValueError, OSError) as err:
        server.error(
            "Attempting to validate CPU settings raised an exception!", err=err
        )
        return {"error": str(err)}
    del info
    _set_cpu(server, message)
    _save_cpu(server)
    if message.get("ping", False):
        return True
    return None


def validate_cpu(base, info):
    if "turbo_min" in base and not (0 <= base["turbo_min"] <= 100):
        raise ValueError(
            f'CPU turbo_min "{base["turbo_min"]}" must be between 0 and 100!'
        )
    if "turbo_max" in base and not (0 <= base["turbo_max"] <= 100):
        raise ValueError(
            f'CPU turbo_max "{base["turbo_max"]}" must be between 0 and 100!'
        )
    if (
        "turbo_max" in base
        and "turbo_min" in base
        and base["turbo_max"] < base["turbo_min"]
    ):
        raise ValueError("CPU turbo_min cannot be greater than turbo_max!")
    for name, cpu in base["cpus"].items():
        if name in info["cpus"]:
            _validate_socket(name, cpu, info["cpus"][name])


def startup(server, message):
    if message.header() == HOOK_HIBERNATE and message.type == MESSAGE_TYPE_PRE:
        return shutdown(server)
    try:
        data = read_json(CONFIG_CPU, ignore_errors=False)
    except OSError as err:
        return server.error(
            "Attempting to read saved CPU power state raised an exception!", err=err
        )
    _set_cpu(server, data)
    del data


def print_frequency(frequency):
    cpu_frequency = frequency / 1000
    if cpu_frequency < 1000:
        return f"{cpu_frequency:.2f} MHz"
    cpu_frequency = round(float(cpu_frequency) / float(1000), 2)
    return f"{cpu_frequency:.2f} GHz"


def _validate_socket(name, base, info):
    if "scale_min" in base and not (info["min"] <= base["scale_min"] <= info["max"]):
        raise ValueError(
            f'CPU "{name}" min "{print_frequency(base["scale_min"])}" must be between '
            f'"{print_frequency(info["min"])}" and "{print_frequency(info["max"])}"!'
        )
    if "scale_max" in base and not (info["min"] <= base["scale_max"] <= info["max"]):
        raise ValueError(
            f'CPU "{name}" max "{print_frequency(base["scale_max"])}" must be between '
            f'"{print_frequency(info["min"])}" and "{print_frequency(info["max"])}"!'
        )
    if (
        "scale_max" in base
        and "scale_min" in base
        and base["scale_max"] < base["scale_min"]
    ):
        raise ValueError(
            f'CPU "{name}" max "{print_frequency(base["scale_max"])}" cannot be less '
            f'than min "{print_frequency(base["scale_min"])}"!'
        )
    if "governor" in base and base["governor"] not in info["governor_list"]:
        raise ValueError(
            f'CPU "{name}" governor must be one of the following "{", ".join(info["governor_list"])}"!'
        )
    if "performance" in base and base["performance"] not in info["performance_list"]:
        raise ValueError(
            f'CPU "{name}" power governor must be one of the following "{", ".join(info["performance_list"])}"!'
        )
