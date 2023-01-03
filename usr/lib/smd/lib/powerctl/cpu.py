#!/usr/bin/false
# PowerCTL Module: CPU
#  powerctl cpu, cpuctl, cpu
#
# PowerCTL command line user module to configure CPU Speed/Power options.
#
# System Management Daemon
#
# Copyright (C) 2016 - 2023 iDigitalFlame
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

from lib.util import boolean, print_error
from lib.structs.message import send_message
from lib.modules.cpu import get_cpu, print_frequency, validate_cpu
from lib.constants import EMPTY, HOOK_CPU, HOOK_OK, MESSAGE_TYPE_CONFIG


def config(arguments):
    try:
        i = get_cpu(arguments.selector)
    except OSError as err:
        return print_error("Error retriving CPU information!", err)
    q = {"cpus": dict(), "type": MESSAGE_TYPE_CONFIG}
    for v in i["cpus"].keys():
        c = dict()
        if arguments.minimum is not None:
            try:
                c["scale_min"] = _parse_frequency(arguments.minimum)
            except ValueError as err:
                return print_error(f'Minimum "{arguments.minimum}" is not valid!', err)
        if arguments.maximum is not None:
            try:
                c["scale_max"] = _parse_frequency(arguments.maximum)
            except ValueError as err:
                return print_error(f'Maximum "{arguments.minimum}" is not valid!', err)
        if arguments.governor is not None:
            c["governor"] = str(arguments.governor)
        if arguments.power_governor is not None:
            c["performance"] = str(arguments.power_governor)
        q["cpus"][v] = c
        del c
    if arguments.turbo is not None:
        q["turbo"] = boolean(arguments.turbo)
    if arguments.turbo_minimum is not None:
        try:
            q["turbo_min"] = int(arguments.turbo_minimum.replace("%", EMPTY), 10)
        except ValueError as err:
            return print_error(
                f'CPU Turbo minimum "{arguments.turbo_minimum}" is not valid!', err
            )
    if arguments.turbo_maximum is not None:
        try:
            q["turbo_max"] = int(arguments.turbo_maximum.replace("%", EMPTY), 10)
        except ValueError as err:
            return print_error(
                f'CPU Turbo maximum "{arguments.turbo_maximum}" is not valid!', err
            )
    try:
        validate_cpu(q, i)
    except ValueError as err:
        return print_error(str(err))
    finally:
        del i
    w = None
    if arguments.wait:
        w = HOOK_OK
        q["ping"] = True
    try:
        send_message(arguments.socket, HOOK_CPU, w, 5, q)
    except OSError as err:
        print_error("Error updating CPU information!", err)
    del q
    if w is not None:
        default(arguments)
    del w


def default(arguments):
    try:
        i = get_cpu(arguments.selector)
    except OSError as err:
        return print_error("Error retriving CPU information!", err)
    if not arguments.advanced:
        print(
            f'{"CPU":6}{"Current":11}{"Minimum":11}{"Maximum":11}{"Governor":12}{"Power Gov":12}\n{"="*63}'
        )
    for name in sorted(i["cpus"]):
        _print_socket(name, i["cpus"][name], arguments.advanced)
    if not arguments.advanced:
        print()
    print(
        f'Turbo Enabled:\t{"Yes" if i["turbo"] else "No"}\nTurbo Minimum:\t'
        f'{i["turbo_min"]}%\nTurbo Maximum:\t{i["turbo_max"]}%'
    )
    del i


def _parse_frequency(frequency):
    f = frequency.lower()
    if f.endswith("hz"):
        try:
            if "ghz" in f:
                f = float(f.replace("ghz", EMPTY).strip()) * 1000.00
            elif "mhz" in f:
                f = float(f.replace("mhz", EMPTY).strip())
            else:
                f = float(f.replace("hz", EMPTY).strip())
        except ValueError:
            raise ValueError(f'"{frequency}" is not valid')
    else:
        try:
            f = float(f.strip())
        except ValueError:
            raise ValueError(f'"{frequency}" is not valid')
    return round(f * 1000.00, None)


def _print_socket(name, cpu, advanced):
    if advanced:
        return print(
            f'{name.upper()}:\t\t{print_frequency(cpu["current"])}\n{"="*36}\nFrequencies:\t'
            f'{print_frequency(cpu["min"])} - {print_frequency(cpu["max"])}\nGovernor:\t'
            f'{cpu["governor"]}\nGov Min Freq:\t{print_frequency(cpu["scale_min"])}\nGov Max Freq:\t'
            f'{print_frequency(cpu["scale_max"])}\nGovernors:\t{", ".join(cpu["governor_list"])}\n'
            f'Power Gov:\t{cpu["performance"]}\nPower Govs:\t{", ".join(cpu["performance_list"])}\n'
        )
    print(
        f'{name.upper():6}{print_frequency(cpu["current"]):<11}{print_frequency(cpu["scale_min"]):<11}'
        f'{print_frequency(cpu["scale_max"]):<11}{cpu["governor"]:<12}{cpu["performance"]:<12}'
    )
