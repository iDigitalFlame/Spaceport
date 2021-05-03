#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame 2018
#
# Module: CPU (System)
#
# Sets and changes the System CPU Power settings.
# Updated 10/2018

from glob import glob
from os.path import join, sep, exists
from lib.util import read, write, read_json, write_json, boolean
from lib.constants import (
    HOOK_POWER,
    HOOK_HIBERNATE,
    HOOK_SHUTDOWN,
    CPU_MIN_FREQ,
    CPU_MAX_FREQ,
    CPU_DIRECTORY,
    CPU_CURRENT_FREQ,
    CPU_SCALING_MIN_FREQ,
    CPU_SCALING_MAX_FREQ,
    CPU_SCALING_GOVERNOR,
    CPU_GOVERNORS_AVAILABLE,
    CPU_PERFORMANCE_STATE,
    CPU_PERFORMANCE_STATE_AVAILABLE,
    EMPTY,
    CPU_PSTATE_TURBO,
    CPU_PSTATE_TURBO_MAX,
    CPU_STATE,
    CPU_PSTATE_TURBO_MIN,
    HOOK_STARTUP,
)

HOOKS = None
HOOKS_SERVER = {
    HOOK_POWER: "cpu_set",
    HOOK_HIBERNATE: "cpu_state",
    HOOK_SHUTDOWN: "cpu_state",
    HOOK_STARTUP: "cpu_state",
}


def _cpu_save(server):
    server.debug("Attempting to save CPU state information..")
    try:
        info = get_cpu_info()
    except OSError as err:
        server.error("Exception occured getting CPU power state!", err=err)
    else:
        state = {
            "cpu-turbo": info[1],
            "cpu-turbo-min": info[2],
            "cpu-turbo-max": info[3],
            "cpu-data": list(),
        }
        for name, cpu in info[0].items():
            state["cpu-data"].append(
                {
                    "cpu": name.lower(),
                    "cpu-min": cpu[3],
                    "cpu-max": cpu[4],
                    "cpu-gov": cpu[5],
                    "cpu-pgov": cpu[7],
                }
            )
        try:
            write_json(CPU_STATE, state, indent=4, sort=True, ignore_errors=False)
        except OSError as err:
            server.error("Exception occured saving CPU power state!", err=err)
        del state
    finally:
        del info


def cpu_set(server, message):
    if message.get("type") == "cpu":
        _set_cpu(server, message)
        _cpu_save(server)


def cpu_state(server, message):
    if message.header() == HOOK_STARTUP or message.get("state") == "post":
        if exists(CPU_STATE):
            server.debug("Attempting to load CPU state information..")
            try:
                info = read_json(CPU_STATE, ignore_errors=False)
            except OSError as err:
                server.error(
                    "Attempting to read saved CPU power state raised an exception!",
                    err=err,
                )
            else:
                _set_cpu(server, info)
                del info
    elif message.get("state") != "post-driver":
        _cpu_save(server)


def _set_cpu(server, cpu_info):
    if "cpu-data" in cpu_info:
        for cpu in cpu_info["cpu-data"]:
            path = join(
                CPU_DIRECTORY, cpu["cpu"].replace("/", EMPTY).replace("\\", EMPTY)
            )
            try:
                if "cpu-min" in cpu:
                    server.debug(
                        'Setting CPU "%s" minimum to "%s"'
                        % (cpu["cpu"], cpu["cpu-min"])
                    )
                    write(
                        join(path, CPU_SCALING_MIN_FREQ),
                        str(cpu["cpu-min"]),
                        ignore_errors=False,
                    )
                if "cpu-max" in cpu:
                    server.debug(
                        'Setting CPU "%s" maximum to "%s"'
                        % (cpu["cpu"], cpu["cpu-max"])
                    )
                    write(
                        join(path, CPU_SCALING_MAX_FREQ),
                        str(cpu["cpu-max"]),
                        ignore_errors=False,
                    )
                if "cpu-gov" in cpu:
                    server.debug(
                        'Setting CPU "%s" governor to "%s"'
                        % (cpu["cpu"], cpu["cpu-gov"])
                    )
                    write(
                        join(path, CPU_SCALING_GOVERNOR),
                        cpu["cpu-gov"],
                        ignore_errors=False,
                    )
                if "cpu-pgov" in cpu:
                    server.debug(
                        'Setting CPU "%s" power governor to "%s"'
                        % (cpu["cpu"], cpu["cpu-pgov"])
                    )
                    write(
                        join(path, CPU_PERFORMANCE_STATE),
                        cpu["cpu-pgov"],
                        ignore_errors=False,
                    )
            except OSError as err:
                server.error(
                    'Attempting to set CPU settings on "%s" raised an exception!' % cpu,
                    err=err,
                )
            finally:
                del path
    if "cpu-turbo" in cpu_info:
        server.debug('Setting CPU turbo mode to "%s"' % cpu_info["cpu-turbo"])
        try:
            write(
                CPU_PSTATE_TURBO,
                "0" if cpu_info["cpu-turbo"] else "0",
                ignore_errors=False,
            )
        except OSError as err:
            server.error(
                "Attempting to set CPU Turbo state raised an exception!", err=err
            )
    if "cpu-turbo-min" in cpu_info:
        server.debug('Setting CPU turbo minimum to "%s%%"' % cpu_info["cpu-turbo-min"])
        try:
            write(
                CPU_PSTATE_TURBO_MIN,
                str(cpu_info["cpu-turbo-min"]),
                ignore_errors=False,
            )
        except OSError as err:
            server.error(
                "Attempting to set CPU Turbo state raised an exception!", err=err
            )
    if "cpu-turbo-max" in cpu_info:
        server.debug('Setting CPU turbo maximum to "%s%%"' % cpu_info["cpu-turbo-max"])
        try:
            write(
                CPU_PSTATE_TURBO_MAX,
                str(cpu_info["cpu-turbo-max"]),
                ignore_errors=False,
            )
        except OSError as err:
            server.error(
                "Attempting to set CPU Turbo state raised an exception!", err=err
            )


def get_cpu_info(cpu_selector=None):
    if cpu_selector is not None:
        cpus = list()
        if "/" in cpu_selector or "\\" in cpu_selector:
            raise OSError('Invalid CPU Selector "%s"!' % cpu_selector)
        if "," in cpu_selector:
            for name in cpu_selector.split(","):
                name_lower = name.strip().lower().replace("cpu", EMPTY)
                path = join(CPU_DIRECTORY, "cpu%s" % name_lower)
                del name_lower
                if exists(path):
                    cpus.append(path)
                else:
                    raise OSError('Cannot find CPU "%s"!' % name)
                del path
        else:
            name = cpu_selector.strip().lower().replace("cpu", EMPTY)
            path = join(CPU_DIRECTORY, "cpu%s" % name)
            if exists(path):
                cpus.append(path)
            else:
                raise OSError('Cannot find CPU "%s"!' % name)
            del name
            del path
    else:
        cpus = glob(join(CPU_DIRECTORY, "cpu[0-9+]"))
    if not isinstance(cpus, list) or len(cpus) == 0:
        raise OSError("Could not find any CPUs!")
    info = dict()
    for cpu in cpus:
        try:
            info[cpu.replace(CPU_DIRECTORY, EMPTY).replace(sep, EMPTY)] = (
                int(read(join(cpu, CPU_CURRENT_FREQ), ignore_errors=False)),
                int(read(join(cpu, CPU_MIN_FREQ), ignore_errors=False)),
                int(read(join(cpu, CPU_MAX_FREQ), ignore_errors=False)),
                int(read(join(cpu, CPU_SCALING_MIN_FREQ), ignore_errors=False)),
                int(read(join(cpu, CPU_SCALING_MAX_FREQ), ignore_errors=False)),
                read(join(cpu, CPU_SCALING_GOVERNOR), ignore_errors=False)
                .strip()
                .replace("\n", EMPTY),
                read(join(cpu, CPU_GOVERNORS_AVAILABLE), ignore_errors=False)
                .strip()
                .replace("\n", EMPTY)
                .split(" "),
                read(join(cpu, CPU_PERFORMANCE_STATE), ignore_errors=False)
                .strip()
                .replace("\n", EMPTY),
                read(join(cpu, CPU_PERFORMANCE_STATE_AVAILABLE))
                .strip()
                .replace("\n", EMPTY)
                .split(" "),
            )
        except (ValueError, OSError) as err:
            raise OSError("Error reading CPU values! (%s)", str(err))
    del cpus
    try:
        turbo_min = int(read(CPU_PSTATE_TURBO_MIN))
        turbo_max = int(read(CPU_PSTATE_TURBO_MAX))
    except (ValueError, OSError) as err:
        raise OSError("Error reading CPU Turbo values! (%s)", str(err))
    return (
        info,
        boolean(read(CPU_PSTATE_TURBO, ignore_errors=True)),
        turbo_min,
        turbo_max,
    )


# EOF
