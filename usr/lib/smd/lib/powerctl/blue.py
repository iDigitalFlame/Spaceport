#!/usr/bin/false
# PowerCTL Module: Bluetooth
#  powerctl blue, bluectl, blue
#
# PowerCTL command line user module to configure bluetooth options.
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
from lib.util import print_error, read
from lib.constants import RADIO_PATH_BLUE, EMPTY
from lib.powerctl.wifi import set_command, set_config


def _is_enabled():
    for device in glob(RADIO_PATH_BLUE):
        flags = read(device, ignore_errors=False)
        if isinstance(flags, str) and flags.replace("\n", EMPTY) == "1":
            return True
    return False


def config(arguments):
    set_config(arguments, "bluetooth", _is_enabled)


def command(arguments):
    if not set_command(arguments, "bluetooth"):
        default(arguments)


def default(arguments):
    try:
        if _is_enabled():
            print("Bluetooth is enabled.")
            return
        print("Bluetooth is disabled.")
    except OSError as err:
        return print_error(
            "Attempting to retrive Bluetooth device status raised an exception!",
            err,
            True,
        )
