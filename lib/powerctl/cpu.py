#!/usr/bin/false
# System Management Daemon - Spaceport
# iDigitalFlame 2018
#
# PowerCTL Module: CPU
#  powerctl cpu, cpuctl, cpu
#
# PowerCTL command line user module to configure CPU Speed/Power options.
# Updated 10/2018

from lib.modules.cpu import get_cpu_info
from lib.util import boolean, print_error
from lib.constants import HOOK_POWER, EMPTY
from lib.structs.message import send_message

ARGS = [
    (
        "-a",
        {
            "required": False,
            "action": "store_true",
            "dest": "advanced",
            "help": "Display detailed CPU information.",
        },
    ),
    (
        "-g",
        {
            "required": False,
            "action": "store",
            "type": str,
            "dest": "governor",
            "help": "Set the CPU Governor.",
            "metavar": "governor",
        },
        "config",
    ),
    (
        "-m",
        {
            "required": False,
            "action": "store",
            "type": str,
            "dest": "minimum",
            "help": "Set the minimum CPU frequency.",
            "metavar": "frequency",
        },
        "config",
    ),
    (
        "-x",
        {
            "required": False,
            "action": "store",
            "type": str,
            "dest": "maximum",
            "help": "Set the maximum CPU frequency.",
            "metavar": "frequency",
        },
        "config",
    ),
    (
        "-p",
        {
            "required": False,
            "action": "store",
            "type": str,
            "dest": "power_governor",
            "help": "Set the CPU Power Governor.",
            "metavar": "power_governor",
        },
        "config",
    ),
    (
        "-t",
        {
            "required": False,
            "action": "store",
            "type": str,
            "dest": "turbo",
            "metavar": "turbo",
            "help": "Enable or Disable CPU turbo mode.",
            "choices": ("0", "1", "true", "false"),
        },
        "config",
    ),
    (
        "-tm",
        {
            "required": False,
            "action": "store",
            "type": str,
            "dest": "turbo_minimum",
            "help": "Set the CPU turbo driver minimum percentage.",
            "metavar": "percentage",
        },
        "config",
    ),
    (
        "-tx",
        {
            "required": False,
            "action": "store",
            "type": str,
            "dest": "turbo_maximum",
            "help": "Set the CPU turbo driver maximum percentage.",
            "metavar": "percentage",
        },
        "config",
    ),
    (
        "-n",
        {
            "required": False,
            "action": "store",
            "type": str,
            "dest": "selector",
            "help": "Filter to specific CPU(s) (Name, Number or Comma Separated).",
            "metavar": "selector",
        },
    ),
]
DESCRIPTION = "System Processor/CPU Management Module"


def _print(frequency):
    cpu_frequency = frequency / 1000
    if cpu_frequency < 1000:
        return "%d MHz" % cpu_frequency
    cpu_frequency = round(float(cpu_frequency) / float(1000), 2)
    return "%.2f GHz" % cpu_frequency


def _parse(frequency):
    cpu_frequency = frequency.lower()
    if "." in cpu_frequency and "ghz" in cpu_frequency:
        try:
            cpu_frequency = float(cpu_frequency.replace("ghz", EMPTY).strip()) * 1000
        except ValueError:
            raise ValueError('"%s" is not a proper frequency!' % frequency)
    elif "hz" in cpu_frequency:
        try:
            if "ghz" in cpu_frequency:
                cpu_frequency = int(cpu_frequency.replace("ghz", EMPTY).strip()) * 1000
            elif "mhz" in cpu_frequency:
                cpu_frequency = int(cpu_frequency.replace("mhz", EMPTY).strip())
        except ValueError:
            raise ValueError('"%s" is not a proper frequency!' % frequency)
    else:
        try:
            cpu_frequency = int(cpu_frequency.replace("hz", EMPTY).strip())
        except ValueError:
            raise ValueError('"%s" is not a proper frequency!' % frequency)
    return int(cpu_frequency * 1000)


def config(arguments):
    try:
        info = get_cpu_info(arguments.selector)
    except OSError as err:
        print_error(
            "Attempting to read CPU information raised an exception!", err, True
        )
    else:
        message = {"type": "cpu", "cpu-data": list()}
        try:
            for cpu in info[0].keys():
                data = {"cpu": cpu.lower()}
                if arguments.minimum is not None:
                    try:
                        data["cpu-min"] = _parse(arguments.minimum)
                    except ValueError:
                        raise ValueError(
                            'Minimum frequency "%s" is not a valid frequency!'
                            % arguments.minimum
                        )
                    if data["cpu-min"] < info[0][cpu][1]:
                        raise ValueError(
                            'Minimum frequency "%s" is less than the supported frequency "%s" for "%s"!'
                            % (
                                _print(data["cpu-min"]),
                                _print(info[0][cpu][1]),
                                cpu.upper(),
                            )
                        )
                    if data["cpu-min"] > info[0][cpu][2]:
                        raise ValueError(
                            'Minimum frequency "%s" is greater than the supported frequency "%s" for "%s"!'
                            % (
                                _print(data["cpu-min"]),
                                _print(info[0][cpu][2]),
                                cpu.upper(),
                            )
                        )
                if arguments.maximum is not None:
                    try:
                        data["cpu-max"] = _parse(arguments.maximum)
                    except ValueError:
                        raise ValueError(
                            'Minimum frequency "%s" is not a valid frequency!'
                            % arguments.maximum
                        )
                    if data["cpu-max"] < info[0][cpu][1]:
                        raise ValueError(
                            'Maximum frequency "%s" is less than the supported frequency "%s" for "%s"!'
                            % (
                                _print(data["cpu-max"]),
                                _print(info[0][cpu][1]),
                                cpu.upper(),
                            )
                        )
                    if data["cpu-max"] > info[0][cpu][2]:
                        raise ValueError(
                            'Maximum frequency "%s" is greater than the supported frequency "%s" for "%s"!'
                            % (
                                _print(data["cpu-max"]),
                                _print(info[0][cpu][2]),
                                cpu.upper(),
                            )
                        )
                if arguments.governor is not None:
                    data["cpu-gov"] = arguments.governor.lower()
                    if data["cpu-gov"] not in info[0][cpu][6]:
                        raise ValueError(
                            'Governor "%s" is not a supported governor for "%s"! (Supported: %s)'
                            % (data["cpu-gov"], cpu.upper(), ", ".join(info[0][cpu][6]))
                        )
                if arguments.power_governor is not None:
                    data["cpu-pgov"] = arguments.power_governor.lower()
                    if data["cpu-pgov"] not in info[0][cpu][8]:
                        print(
                            'Power Governor "%s" is not a supported power governor for "%s"! (Supported: %s)'
                            % (
                                data["cpu-pgov"],
                                cpu.upper(),
                                ", ".join(info[0][cpu][8]),
                            )
                        )
                message["cpu-data"].append(data)
                del data
            if arguments.turbo is not None:
                message["cpu-turbo"] = boolean(arguments.turbo)
            if arguments.turbo_minimum is not None:
                try:
                    message["cpu-turbo-min"] = int(
                        arguments.turbo_minimum.replace("%", EMPTY)
                    )
                except ValueError:
                    raise ValueError(
                        'CPU Turbo minimum "%s" is not a valid number!'
                        % arguments.turbo_minimum
                    )
                if (
                    0 > int(message["cpu-turbo-min"])
                    or int(message["cpu-turbo-min"]) > 100
                ):
                    raise ValueError(
                        "CPU Turbo minimum must be between zero and one hundred (0 - 100)!"
                    )
            if arguments.turbo_maximum is not None:
                try:
                    message["cpu-turbo-max"] = int(
                        arguments.turbo_maximum.replace("%", EMPTY)
                    )
                except ValueError:
                    raise ValueError(
                        'CPU Turbo maximum "%s" is not a valid number!'
                        % arguments.turbo_maximum
                    )
                if (
                    0 > int(message["cpu-turbo-max"])
                    or int(message["cpu-turbo-max"]) > 100
                ):
                    raise ValueError(
                        "CPU Turbo maximum must be between zero and one hundred (0 - 100)!"
                    )
        except ValueError as err:
            print_error(str(err), None, True)
        else:
            try:
                send_message(arguments.socket, HOOK_POWER, None, None, message)
            except OSError as err:
                print_error(
                    "Attempting to update the CPU status raised an exception!",
                    err,
                    True,
                )
        finally:
            del message
    finally:
        del info


def default(arguments):
    try:
        info = get_cpu_info(arguments.selector)
    except OSError as err:
        print_error(
            "Attempting to read CPU information raised an exception!", err, True
        )
    else:
        if not arguments.advanced:
            print(
                "%-6s%-10s%-10s%-10s%-12s%-12s\n%s"
                % (
                    "CPU",
                    "Current",
                    "Minimum",
                    "Maximum",
                    "Governor",
                    "Power Gov",
                    "=" * 60,
                )
            )
        for cpu in sorted(info[0].keys()):
            if arguments.advanced:
                print(
                    "%s:\t\t%s\n%s\nFrequencies:\t%s - %s\nGovernor:\t%s\nGov Min Freq:\t%s\nGov Max Freq:\t%s\n"
                    "Governors:\t%s\nPower Gov:\t%s\nPower Govs:\t%s\n"
                    % (
                        cpu.upper(),
                        _print(info[0][cpu][0]),
                        "=" * 36,
                        _print(info[0][cpu][1]),
                        _print(info[0][cpu][2]),
                        info[0][cpu][5],
                        _print(info[0][cpu][3]),
                        _print(info[0][cpu][4]),
                        ", ".join(info[0][cpu][6]),
                        info[0][cpu][7],
                        ", ".join(info[0][cpu][8]),
                    )
                )
            else:
                print(
                    "%-6s%-10s%-10s%-10s%-12s%-12s"
                    % (
                        cpu.upper(),
                        _print(info[0][cpu][0]),
                        _print(info[0][cpu][3]),
                        _print(info[0][cpu][4]),
                        info[0][cpu][5],
                        info[0][cpu][7],
                    )
                )
        if not arguments.advanced:
            print()
        print(
            "Turbo Enabled:\t%s\nTurbo Minimum:\t%s%%\nTurbo Maximum:\t%s%%"
            % ("Yes" if info[1] else "No", info[2], info[3])
        )
    finally:
        del info


# EOF
