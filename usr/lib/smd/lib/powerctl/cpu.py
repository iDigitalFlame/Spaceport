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

# PowerCTL Module: CPU
#   Command line user module to configure CPU Speed/Power options.

from lib.util import boolean, num, nes
from lib import print_error, send_message
from lib.constants.config import TIMEOUT_SEC_MESSAGE
from lib.shared.cpu import cpu, freq_to_str, validate
from lib.constants import EMPTY, HOOK_CPU, HOOK_OK, MSG_CONFIG


def _parse(freq):
    f = freq.lower()
    if f.endswith("hz"):
        try:
            if "ghz" in f:
                v = float(f.replace("ghz", EMPTY).strip()) * 1000.00
            elif "mhz" in f:
                v = float(f.replace("mhz", EMPTY).strip())
            else:
                v = float(f.replace("hz", EMPTY).strip())
        except ValueError:
            raise ValueError(f'"{freq}" is not valid')
    else:
        try:
            v = float(f.strip())
        except ValueError:
            raise ValueError(f'"{freq}" is not valid')
    del f
    if v <= 0:
        raise ValueError(f'"{freq}" is not valid')
    return round(v * 1000.00)


def config(args):
    try:
        x = cpu(args.selector)
    except (ValueError, OSError) as err:
        return print_error("Cannot retrive CPU information!", err)
    p = {"cpus": dict(), "type": MSG_CONFIG}
    for v in x["cpus"].keys():
        c = dict()
        if nes(args.minimum):
            try:
                c["scale_min"] = _parse(args.minimum)
            except ValueError as err:
                return print_error(f'Minimum "{args.minimum}" is not valid!', err)
        if nes(args.maximum):
            try:
                c["scale_max"] = _parse(args.maximum)
            except ValueError as err:
                return print_error(f'Maximum "{args.minimum}" is not valid!', err)
        if nes(args.governor):
            c["governor"] = args.governor
        if nes(args.power_governor):
            c["performance"] = args.power_governor
        p["cpus"][v] = c
        del c
    if nes(args.turbo):
        p["turbo"] = boolean(args.turbo)
    if nes(args.turbo_minimum):
        try:
            p["turbo_min"] = num(args.turbo_minimum.replace("%", EMPTY), False)
        except ValueError as err:
            return print_error(
                f'CPU Turbo minimum "{args.turbo_minimum}" is not valid!', err
            )
    if nes(args.turbo_maximum):
        try:
            p["turbo_max"] = num(args.turbo_maximum.replace("%", EMPTY), False)
        except ValueError as err:
            return print_error(
                f'CPU Turbo maximum "{args.turbo_maximum}" is not valid!', err
            )
    try:
        validate(p, x)
    except (TypeError, ValueError) as err:
        return print_error("CPU settings are invalid!", err)
    finally:
        del x
    if args.wait:
        w, p["ping"] = HOOK_OK, True
    else:
        w = None
    try:
        send_message(args.socket, HOOK_CPU, w, TIMEOUT_SEC_MESSAGE, p)
    except Exception as err:
        return print_error("Cannot update CPU information!", err)
    finally:
        del p
    if w is not None:
        default(args)
    del w


def default(args):
    try:
        x = cpu(args.selector)
    except (ValueError, OSError) as err:
        return print_error("Cannot retrive CPU information!", err)
    if not args.advanced:
        print(
            f'{"CPU":6}{"Current":11}{"Minimum":11}{"Maximum":11}{"Governor":12}{"Power Gov":12}\n{"="*63}'
        )
    for n, v in sorted(x["cpus"].items()):
        _print(n, v, args.advanced)
    if not args.advanced:
        print()
    print(f'Turbo Enabled:\t{"Yes" if x["turbo"] else "No"}', end="")
    if x["turbo"]:
        print(
            f' ({x["turbo_current"]}%)\nTurbo Minimum:\t{x["turbo_min"]}%\nTurbo Maximum:\t{x["turbo_max"]}%'
        )
    else:
        print()
    del x


def _print(name, cpu, advanced):
    if not advanced:
        return print(
            f'{name.upper():6}{freq_to_str(cpu["current"]):<11}{freq_to_str(cpu["scale_min"]):<11}'
            f'{freq_to_str(cpu["scale_max"]):<11}{cpu["governor"]:<12}{cpu["performance"]:<12}'
        )
    print(
        f'{name.upper()}:\t\t{freq_to_str(cpu["current"])}\n{"="*36}\nFreq Range:\t'
        f'{freq_to_str(cpu["min"])} - {freq_to_str(cpu["max"])}\nGovernor:\t'
        f'{cpu["governor"]}\nGov Min Freq:\t{freq_to_str(cpu["scale_min"])}\nGov Max Freq:\t'
        f'{freq_to_str(cpu["scale_max"])}\nGovernors:\t{", ".join(cpu["governor_list"])}\n'
        f'Power Gov:\t{cpu["performance"]}\nPower Govs:\t{", ".join(cpu["performance_list"])}\n'
    )
