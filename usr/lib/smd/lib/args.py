#!/usr/bin/false
# This is the static arguments and descriptions storage file. This stores some of
# the static content that does not belong in constants.py.
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

from lib.constants import BOOLEANS

ARGS = {
    "cpu": [
        (
            "-a",
            {
                "dest": "advanced",
                "help": "Display detailed CPU information.",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            "-g",
            {
                "type": str,
                "dest": "governor",
                "help": "Set the CPU governor.",
                "action": "store",
                "metavar": "governor",
                "required": False,
            },
            "config",
        ),
        (
            "-m",
            {
                "type": str,
                "dest": "minimum",
                "help": "Set the minimum CPU frequency.",
                "action": "store",
                "metavar": "frequency",
                "required": False,
            },
            "config",
        ),
        (
            "-x",
            {
                "type": str,
                "dest": "maximum",
                "help": "Set the maximum CPU frequency.",
                "action": "store",
                "metavar": "frequency",
                "required": False,
            },
            "config",
        ),
        (
            "-p",
            {
                "type": str,
                "dest": "power_governor",
                "help": "Set the CPU power governor.",
                "action": "store",
                "metavar": "power_governor",
                "required": False,
            },
            "config",
        ),
        (
            "-t",
            {
                "type": str,
                "dest": "turbo",
                "help": "Enable or disable CPU turbo mode.",
                "action": "store",
                "metavar": "turbo",
                "choices": BOOLEANS,
                "required": False,
            },
            "config",
        ),
        (
            "-tm",
            {
                "type": str,
                "dest": "turbo_minimum",
                "help": "Set the CPU turbo driver minimum percentage.",
                "action": "store",
                "metavar": "percentage",
                "required": False,
            },
            "config",
        ),
        (
            "-tx",
            {
                "type": str,
                "action": "store",
                "dest": "turbo_maximum",
                "help": "Set the CPU turbo driver maximum percentage.",
                "metavar": "percentage",
                "required": False,
            },
            "config",
        ),
        (
            "-n",
            {
                "type": str,
                "dest": "selector",
                "help": "Filter to specific CPU(s) (Name, Number or Comma Separated).",
                "action": "store",
                "metavar": "selector",
                "required": False,
            },
        ),
        (
            "-w",
            {
                "dest": "wait",
                "help": "Display CPU details after setting.",
                "action": "store_true",
                "required": False,
            },
        ),
    ],
    "blue": [
        (
            "-d",
            {
                "dest": "disable",
                "help": "Disable Bluetooth.",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            "-e",
            {
                "dest": "enable",
                "help": "Enable Bluetooth.",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            "-t",
            {
                "dest": "toggle",
                "help": "Toggle Bluetooth.",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            "-b",
            {
                "type": str,
                "dest": "boot",
                "help": "Set the Bluetooth status on boot.",
                "required": False,
                "action": "store",
                "metavar": "boot",
                "choices": BOOLEANS,
            },
            "config",
        ),
        (
            "command",
            {
                "help": "Bluetooth commands.",
                "nargs": "?",
                "action": "store",
                "default": None,
                "choices": BOOLEANS + ["set", "boot"],
            },
            "command",
        ),
        (
            "args",
            {
                "nargs": "*",
                "help": "Optional arguments to command.",
                "action": "store",
                "default": None,
            },
        ),
    ],
    "wifi": [
        (
            "-d",
            {
                "dest": "disable",
                "help": "Disable wireless.",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            "-e",
            {
                "dest": "enable",
                "help": "Enable wireless.",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            "-t",
            {
                "dest": "toggle",
                "help": "Toggle wireless.",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            "-b",
            {
                "type": str,
                "dest": "boot",
                "help": "Set the wireless status on boot.",
                "action": "store",
                "metavar": "boot",
                "choices": BOOLEANS,
                "required": False,
            },
            "config",
        ),
        (
            "command",
            {
                "help": "Wireless commands.",
                "nargs": "?",
                "action": "store",
                "default": None,
                "choices": BOOLEANS + ["set", "boot"],
            },
            "command",
        ),
        (
            "args",
            {
                "help": "Optional arguments to the command.",
                "nargs": "*",
                "action": "store",
                "default": None,
            },
        ),
    ],
    "lock": [
        (
            "-f",
            {
                "dest": "force",
                "help": "Force lock screen regardless of locker settings",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            "-t",
            {
                "type": int,
                "dest": "suspend",
                "help": "Set the suspend locker timeout (in seconds) on lock, zero to disable.",
                "action": "store",
                "metavar": "seconds",
                "required": False,
            },
        ),
        (
            "-kt",
            {
                "type": int,
                "dest": "suspend_force",
                "help": "Force set the suspend locker timeout (in seconds) on lock, zero to disable.",
                "action": "store",
                "metavar": "seconds",
                "required": False,
            },
        ),
        (
            "-z",
            {
                "type": int,
                "dest": "hibernate",
                "action": "store",
                "metavar": "seconds",
                "help": "Set the hibernate locker timeout (in seconds) on lock, zero to disable.",
                "required": False,
            },
        ),
        (
            "-kz",
            {
                "type": int,
                "dest": "hibernate_force",
                "help": "Force set the hibernate locker timeout (in seconds) on lock, zero to disable.",
                "action": "store",
                "metavar": "seconds",
                "required": False,
            },
        ),
        (
            "timeout",
            {
                "help": "Set the suspend locker timeout (in seconds) on lock, zero to disable.",
                "nargs": "?",
                "action": "store",
                "default": None,
            },
        ),
    ],
    "hydra": [
        (
            "-l",
            {
                "dest": "list",
                "help": "List running VMs.",
                "action": "store_true",
                "required": False,
            },
            "list_vms",
        ),
        (
            "-i",
            {
                "type": int,
                "dest": "vmid",
                "help": "VMID of VM to select.",
                "action": "store",
                "metavar": "vmid",
                "required": False,
            },
        ),
        (
            "-n",
            {
                "type": str,
                "dest": "name",
                "help": "Name or Path of VM to select.",
                "action": "store",
                "metavar": "name",
                "required": False,
            },
        ),
        (
            "command",
            {
                "help": "Hydra command to execute.",
                "nargs": "?",
                "action": "store",
                "default": None,
            },
            "tokenize",
        ),
        (
            "args",
            {
                "nargs": "*",
                "default": None,
                "action": "store",
                "help": "Optional arguments to command.",
            },
        ),
        (
            "-d",
            {
                "dest": "directory",
                "type": str,
                "help": "Set the user VM search directory.",
                "action": "store",
                "metavar": "dir",
                "required": False,
            },
            "directory",
        ),
        (
            "-a",
            {
                "dest": "alias_add",
                "type": str,
                "help": "Add an alias to the selected VM.",
                "action": "store",
                "metavar": "alias",
                "required": False,
            },
            "alias",
        ),
        (
            "-ar",
            {
                "dest": "alias_delete",
                "type": str,
                "help": "Remove an alias from the selected VM.",
                "action": "store",
                "metavar": "alias",
                "required": False,
            },
            "alias",
        ),
        (
            "-x",
            {
                "dest": "stop",
                "help": "Softly stop the selected VM.",
                "action": "store_true",
                "required": False,
            },
            "stop",
        ),
        (
            "-s",
            {
                "dest": "start",
                "help": "Start the selected VM.",
                "action": "store_true",
                "required": False,
            },
            "start",
        ),
        (
            "-f",
            {
                "dest": "stop_force",
                "help": "Force poweroff (halt) the selected VM.",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            "-t",
            {
                "type": int,
                "dest": "timeout",
                "help": "Optional shutdown timeout. (Ignored with -f)",
                "action": "store",
                "metavar": "timeout",
                "default": 90,
                "required": False,
            },
        ),
        (
            "-u",
            {
                "dest": "usb_add",
                "help": "Connect a USB device to the selected VM.",
                "action": "store_true",
                "required": False,
            },
            "usb",
        ),
        (
            "-ur",
            {
                "dest": "usb_delete",
                "help": "Disconnect a USB device from the selected VM.",
                "action": "store_true",
                "required": False,
            },
            "usb",
        ),
        (
            "-ul",
            {
                "dest": "usb_list",
                "help": "List a USB devices connected to the selected VM.",
                "action": "store_true",
                "required": False,
            },
            "usb_list",
        ),
        (
            "-uc",
            {
                "dest": "usb_clean",
                "help": "Remove all USB devices connected to the selected VM.",
                "action": "store_true",
                "required": False,
            },
            "usb_clean",
        ),
        (
            "-un",
            {
                "type": str,
                "dest": "usb_name",
                "help": "Name of USB device to select.",
                "action": "store",
                "metavar": "name",
                "required": False,
            },
        ),
        (
            "-ui",
            {
                "type": int,
                "dest": "usb_id",
                "help": "USB device ID to select.",
                "action": "store",
                "metavar": "id",
                "required": False,
            },
        ),
        (
            "-uv",
            {
                "type": str,
                "dest": "usb_vendor",
                "help": "USB device vendor ID to select.",
                "action": "store",
                "metavar": "vendor",
                "required": False,
            },
        ),
        (
            "-up",
            {
                "type": str,
                "dest": "usb_product",
                "help": "USB device product ID to select.",
                "action": "store",
                "metavar": "product",
                "required": False,
            },
        ),
        (
            "-u2",
            {
                "dest": "usb_slow",
                "help": "Use the USB2.0 bus instead of USB3.0 (Default is 3.0)",
                "action": "store_true",
                "required": False,
            },
            "all",
        ),
        (
            "-c",
            {
                "dest": "connect",
                "help": "Connect to the selected VM (using NoVNC)",
                "required": False,
                "action": "store_true",
            },
            "connect",
        ),
        (
            "-cv",
            {
                "dest": "connect_vnc",
                "help": "Connect to the selected VM (using VNC)",
                "action": "store_true",
                "required": False,
            },
            "connect",
        ),
        (
            "-w",
            {
                "dest": "wake",
                "help": "Wake VM.",
                "action": "store_true",
                "required": False,
            },
            "sleep_vm",
        ),
        (
            "-z",
            {
                "dest": "sleep",
                "help": "Sleep VM.",
                "action": "store_true",
                "required": False,
            },
            "sleep_vm",
        ),
        (
            "-za",
            {
                "dest": "all_sleep",
                "help": "Sleep all running VMs.",
                "action": "store_true",
                "required": False,
            },
            "all",
        ),
        (
            "-wa",
            {
                "dest": "all_wake",
                "help": "Wake all sleeping VMs.",
                "required": False,
                "action": "store_true",
            },
            "all",
        ),
        (
            "-xa",
            {
                "dest": "all_stop",
                "help": "Stop all running VMs",
                "action": "store_true",
                "required": False,
            },
            "all",
        ),
        (
            "-fa",
            {
                "dest": "all_force",
                "help": "Force poweroff (halt) all running VMs",
                "action": "store_true",
                "required": False,
            },
            "all",
        ),
        (
            "--dmenu",
            {
                "dest": "dmenu",
                "help": "List output in a dmenu compatible format",
                "action": "store_true",
                "required": False,
            },
            "all",
        ),
    ],
    "locker": [
        (
            "-b",
            {
                "type": str,
                "dest": "blank",
                "help": "Set the screen blank locker time (Seconds, True - Until Reboot, False - Disable).",
                "action": "store",
                "metavar": "seconds",
                "required": False,
            },
            "config",
        ),
        (
            "-l",
            {
                "type": str,
                "dest": "lockscreen",
                "help": "Set the lock screen locker time (Seconds, True - Until Reboot, False - Disable).",
                "action": "store",
                "metavar": "seconds",
                "required": False,
            },
            "config",
        ),
        (
            "-s",
            {
                "type": str,
                "dest": "suspend",
                "help": "Set the suspend locker time (Seconds, True - Until Reboot, False - Disable).",
                "action": "store",
                "metavar": "seconds",
                "required": False,
            },
            "config",
        ),
        (
            "-z",
            {
                "type": str,
                "dest": "hibernate",
                "help": "Set the hibernate locker time (Seconds, True - Until Reboot, False - Disable).",
                "action": "store",
                "metavar": "seconds",
                "required": False,
            },
            "config",
        ),
        (
            "-d",
            {
                "type": str,
                "dest": "lid",
                "help": "Set the lid locker time (Seconds, True - Until Reboot, False - Disable).",
                "action": "store",
                "metavar": "seconds",
                "required": False,
            },
            "config",
        ),
        (
            "-y",
            {
                "type": str,
                "dest": "key",
                "help": "Set the key locker time (Seconds, True - Until Reboot, False - Disable).",
                "action": "store",
                "metavar": "seconds",
                "required": False,
            },
            "config",
        ),
        (
            "-kb",
            {
                "type": str,
                "dest": "blank_force",
                "help": "Force the screen blank locker time (Seconds, True - Until Reboot, False - Disable).",
                "action": "store",
                "metavar": "seconds",
                "required": False,
            },
            "config",
        ),
        (
            "-kl",
            {
                "type": str,
                "dest": "lockscreen_force",
                "help": "Force the lock screen locker time (Seconds, True - Until Reboot, False - Disable).",
                "action": "store",
                "metavar": "seconds",
                "required": False,
            },
            "config",
        ),
        (
            "-ks",
            {
                "type": str,
                "dest": "suspend_force",
                "help": "Force the suspend locker time (Seconds, True - Until Reboot, False - Disable).",
                "action": "store",
                "metavar": "seconds",
                "required": False,
            },
            "config",
        ),
        (
            "-kz",
            {
                "type": str,
                "dest": "hibernate_force",
                "help": "Force the hibernate locker time (Seconds, True - Until Reboot, False - Disable).",
                "action": "store",
                "metavar": "seconds",
                "required": False,
            },
            "config",
        ),
        (
            "-kd",
            {
                "type": str,
                "dest": "lid_force",
                "help": "Force the lid locker time (Seconds, True - Until Reboot, False - Disable).",
                "action": "store",
                "metavar": "seconds",
                "required": False,
            },
            "config",
        ),
        (
            "-ky",
            {
                "type": str,
                "dest": "key_force",
                "help": "Force the key locker time (Seconds, True - Until Reboot, False - Disable).",
                "action": "store",
                "metavar": "seconds",
                "required": False,
            },
            "config",
        ),
    ],
    "backup": [
        (
            "-l",
            {
                "dest": "list",
                "help": "List backup plans.",
                "action": "store_true",
                "required": False,
            },
            "default",
        ),
        (
            "-s",
            {
                "dest": "start",
                "help": "Start a backup.",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            "-x",
            {
                "dest": "stop",
                "help": "Stop a backup.",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            "-p",
            {
                "dest": "pause",
                "help": "Pause a running backup.",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            "-r",
            {
                "dest": "resume",
                "help": "Resume a paused backup.",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            "-f",
            {
                "dest": "force",
                "help": "Force a backup to start, even on battery.",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            "-c",
            {
                "dest": "clear",
                "help": "Clear backup database cache.",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            "-d",
            {
                "type": str,
                "dest": "dir",
                "help": "Directory to trigger a backup for.",
                "action": "store",
                "metavar": "dir",
                "required": False,
            },
            "config",
        ),
        (
            "path",
            {
                "help": "Directory to trigger a backup for.",
                "nargs": "?",
                "action": "store",
                "default": None,
            },
            "config",
        ),
    ],
    "rotate": [
        (
            "-d",
            {
                "dest": "disable",
                "help": "Disable rotation lock.",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            "-e",
            {
                "dest": "enable",
                "help": "Enable rotation lock.",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            "-t",
            {
                "dest": "toggle",
                "help": "Toggle rotation lock.",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            "-s",
            {
                "type": str,
                "dest": "set",
                "help": "Set the rotation lock.",
                "action": "store",
                "metavar": "rotate",
                "choices": BOOLEANS,
                "required": False,
            },
            "config",
        ),
        (
            "state",
            {
                "help": "Enable/Disable the rotation lock.",
                "nargs": "?",
                "action": "store",
                "default": None,
                "choices": BOOLEANS,
            },
            "config",
        ),
    ],
    "reload": [
        (
            "-l",
            {
                "type": int,
                "default": -1,
                "dest": "level",
                "help": "Set the log level to reload with (temporary, 0 [debug] - 4 [critical]).",
                "action": "store",
                "metavar": "level",
                "required": False,
            },
        ),
        (
            "-a",
            {
                "dest": "all",
                "help": "Reload all services (Not just userland)",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            "-z",
            {
                "dest": "no_reload",
                "help": "Do not reload the system (Only change log level).",
                "action": "store_true",
                "required": False,
            },
        ),
    ],
    "brightness": [
        (
            "-i",
            {
                "dest": "increase",
                "help": "Increase the current brightness level by 25.",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            "-d",
            {
                "dest": "decrease",
                "help": "Decrease the current brightness level by 25.",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            "-s",
            {
                "type": str,
                "dest": "brightness",
                "help": "Set the current brightness level.",
                "action": "store",
                "metavar": "level",
                "required": False,
            },
        ),
        (
            "level",
            {
                "nargs": "?",
                "help": "Set the current brightness level.",
                "action": "store",
                "default": None,
            },
        ),
    ],
}
DESCRIPTIONS = {
    "cpu": "Processor Management Module",
    "blue": "Bluetooth Management Module",
    "wifi": "Wireless Management Module",
    "lock": "Lock Screen Management Module",
    "hydra": "Hydra Hypervisor Management Module",
    "locker": "Locker Management Module",
    "backup": "Backup Management Module",
    "rotate": "Screen Rotation Management Module",
    "reload": "Configuration Reload Management Module",
    "brightness": "Display Brightness Management Module",
}
