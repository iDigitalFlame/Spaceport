#!/usr/bin/false
# PowerCTL Module: CPU
#  powerctl cpu, cpuctl, cpu
#
# PowerCTL command line user module to configure CPU Speed/Power options.
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

from lib.util import boolean, print_error
from lib.structs.message import send_message
from lib.modules.cpu import get_cpu, validate_cpu, print_frequency
from lib.constants import HOOK_CPU, EMPTY, MESSAGE_TYPE_CONFIG, HOOK_OK


def config(arguments):
    try:
        info = get_cpu(arguments.selector)
    except OSError as err:
        return print_error(
            "Attempting to read CPU information raised an exception!", err
        )
    send = {"cpus": dict(), "type": MESSAGE_TYPE_CONFIG}
    for cpu in info["cpus"].keys():
        c = dict()
        if arguments.minimum is not None:
            try:
                c["scale_min"] = _parse_frequency(arguments.minimum)
            except ValueError as err:
                return print_error(
                    f'Minimum frequency "{arguments.minimum}" is not a valid frequency!',
                    err,
                )
        if arguments.maximum is not None:
            try:
                c["scale_max"] = _parse_frequency(arguments.maximum)
            except ValueError as err:
                return print_error(
                    f'Maximum frequency "{arguments.minimum}" is not a valid frequency!',
                    err,
                )
        if arguments.governor is not None:
            c["governor"] = str(arguments.governor)
        if arguments.power_governor is not None:
            c["performance"] = str(arguments.power_governor)
        send["cpus"][cpu] = c
        del c
    if arguments.turbo is not None:
        send["turbo"] = boolean(arguments.turbo)
    if arguments.turbo_minimum is not None:
        try:
            send["turbo_min"] = int(arguments.turbo_minimum.replace("%", EMPTY))
        except ValueError as err:
            return print_error(
                f'CPU Turbo minimum "{arguments.turbo_minimum}" is not a valid number!',
                err,
            )
    if arguments.turbo_maximum is not None:
        try:
            send["turbo_max"] = int(arguments.turbo_maximum.replace("%", EMPTY))
        except ValueError as err:
            return print_error(
                f'CPU Turbo maximum "{arguments.turbo_maximum}" is not a valid number!',
                err,
            )
    try:
        validate_cpu(send, info)
    except ValueError as err:
        return print_error(str(err))
    finally:
        del info
    look = None
    if arguments.wait:
        look = HOOK_OK
        send["ping"] = True
    try:
        send_message(arguments.socket, HOOK_CPU, look, 5, send)
    except OSError as err:
        print_error("Attempting to update the CPU status raised an exception!", err)
    del send
    if look is not None:
        default(arguments)
        del look


def default(arguments):
    try:
        info = get_cpu(arguments.selector)
    except OSError as err:
        return print_error(
            "Attempting to read CPU information raised an exception!", err
        )
    if not arguments.advanced:
        print(
            f'{"CPU":6}{"Current":11}{"Minimum":11}{"Maximum":11}{"Governor":12}{"Power Gov":12}\n{"="*63}'
        )
    for name in sorted(info["cpus"]):
        _print_socket(name, info["cpus"][name], arguments.advanced)
    if not arguments.advanced:
        print()
    print(
        f'Turbo Enabled:\t{"Yes" if info["turbo"] else "No"}\nTurbo Minimum:\t'
        f'{info["turbo_min"]}%\nTurbo Maximum:\t{info["turbo_max"]}%'
    )
    del info


def _parse_frequency(frequency):
    cpu_frequency = frequency.lower()
    if cpu_frequency.endswith("hz"):
        try:
            if "ghz" in cpu_frequency:
                cpu_frequency = (
                    float(cpu_frequency.replace("ghz", EMPTY).strip()) * 1000.00
                )
            elif "mhz" in cpu_frequency:
                cpu_frequency = float(cpu_frequency.replace("mhz", EMPTY).strip())
            else:
                cpu_frequency = float(cpu_frequency.replace("hz", EMPTY).strip())
        except ValueError:
            raise ValueError(f'"{frequency}" is not a proper frequency!')
    else:
        try:
            cpu_frequency = float(cpu_frequency.strip())
        except ValueError:
            raise ValueError(f'"{frequency}" is not a proper frequency!')
    return round(cpu_frequency * 1000.00, None)


def _print_socket(name, cpu, advanced):
    if advanced:
        print(
            f'{name.upper()}:\t\t{print_frequency(cpu["current"])}\n{"="*36}\nFrequencies:\t'
            f'{print_frequency(cpu["min"])} - {print_frequency(cpu["max"])}\nGovernor:\t'
            f'{cpu["governor"]}\nGov Min Freq:\t{print_frequency(cpu["scale_min"])}\nGov Max Freq:\t'
            f'{print_frequency(cpu["scale_max"])}\nGovernors:\t{", ".join(cpu["governor_list"])}\n'
            f'Power Gov:\t{cpu["performance"]}\nPower Govs:\t{", ".join(cpu["performance_list"])}\n'
        )
        return
    print(
        f'{name.upper():6}{print_frequency(cpu["current"]):<11}{print_frequency(cpu["scale_min"]):<11}'
        f'{print_frequency(cpu["scale_max"]):<11}{cpu["governor"]:<12}{cpu["performance"]:<12}'
    )
