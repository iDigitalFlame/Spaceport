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

# args.py
#   This is the static arguments and descriptions storage file. This stores some
#   of the static content that can be dynamically loaded by the powerctl loader.

from lib.constants import BOOLEANS

ARGS = {
    "cpu": [
        (
            "-a",
            {
                "dest": "advanced",
                "help": "display detailed CPU information",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            "-g",
            {
                "type": str,
                "dest": "governor",
                "help": "set the CPU governor",
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
                "help": "set the minimum CPU frequency",
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
                "help": "set the maximum CPU frequency",
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
                "help": "set the CPU power governor",
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
                "help": "enable or disable CPU turbo mode",
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
                "help": "set the CPU turbo driver minimum percentage",
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
                "help": "set the CPU turbo driver maximum percentage",
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
                "help": "filter to specific CPU(s) (name, number or comma separated)",
                "action": "store",
                "metavar": "selector",
                "required": False,
            },
        ),
        (
            "-w",
            {
                "dest": "wait",
                "help": "display CPU details after setting",
                "action": "store_true",
                "required": False,
            },
        ),
    ],
    "log": [
        (
            "-l",
            {
                "type": str,
                "dest": "level",
                "help": "set the log level to use (temporary, 0 [debug] - 4 [critical])",
                "action": "store",
                "metavar": "level",
                "required": True,
            },
        ),
    ],
    "blue": [
        (
            "-d",
            {
                "dest": "disable",
                "help": "disable Bluetooth",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            "-e",
            {
                "dest": "enable",
                "help": "enable Bluetooth",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            "-t",
            {
                "dest": "toggle",
                "help": "toggle Bluetooth",
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
                "help": "set the Bluetooth boot state",
                "required": False,
                "action": "store",
                "metavar": "boot",
                "choices": BOOLEANS,
            },
            "config",
        ),
        (
            "-f",
            {
                "dest": "force",
                "help": "force enable/disable Bluetooth regardless of current state",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            "command",
            {
                "help": "bluetooth commands",
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
                "help": "optional arguments",
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
                "help": "disable Wireless",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            "-e",
            {
                "dest": "enable",
                "help": "enable Wireless",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            "-t",
            {
                "dest": "toggle",
                "help": "toggle Wireless",
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
                "help": "set the Wireless boot state",
                "action": "store",
                "metavar": "boot",
                "choices": BOOLEANS,
                "required": False,
            },
            "config",
        ),
        (
            "-f",
            {
                "dest": "force",
                "help": "force enable/disable Wireless regardless of current state",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            "command",
            {
                "help": "wireless commands",
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
                "help": "Optional arguments",
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
                "help": "force Lockscreen and override lockers",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            "-t",
            {
                "type": str,
                "dest": "suspend",
                "help": "set the Suspend timeout (seconds / true - until reboot / false - disable)",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
        ),
        (
            "-kt",
            {
                "type": str,
                "dest": "suspend_force",
                "help": "force set the Suspend timeout (seconds / true - until reboot / false - disable)",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
        ),
        (
            "-z",
            {
                "type": str,
                "dest": "hibernate",
                "action": "store",
                "metavar": "seconds",
                "help": "set the Hibernate timeout (seconds / true - until reboot / false - disable)",
                "required": False,
            },
        ),
        (
            "-kz",
            {
                "type": str,
                "dest": "hibernate_force",
                "help": "force set the Hibernate timeout (seconds / true - until reboot / false - disable)",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
        ),
        (
            "timeout",
            {
                "help": "set the Suspend timeout (seconds / true - until reboot / false - disable)",
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
                "help": "list running VMs",
                "action": "store_true",
                "required": False,
            },
            "vm_list",
        ),
        (
            "-i",
            {
                "type": int,
                "dest": "vmid",
                "help": "VMID of VM to select",
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
                "help": "name or path of VM to select",
                "action": "store",
                "metavar": "name",
                "required": False,
            },
        ),
        (
            "-d",
            {
                "dest": "directory",
                "type": str,
                "help": "set the user VM search directory",
                "action": "store",
                "metavar": "dir",
                "required": False,
            },
            "user_directory",
        ),
        (
            "-a",
            {
                "dest": "alias_add",
                "type": str,
                "help": "add an alias to the selected VM",
                "action": "store",
                "metavar": "alias",
                "required": False,
            },
            "user_alias",
        ),
        (
            "-ar",
            {
                "dest": "alias_delete",
                "type": str,
                "help": "remove an alias from the selected VM",
                "action": "store",
                "metavar": "alias",
                "required": False,
            },
            "user_alias",
        ),
        (
            "-T",
            {
                "dest": "tap",
                "help": "tap the VM power button",
                "action": "store_true",
                "required": False,
            },
            "vm_tap",
        ),
        (
            "-x",
            {
                "dest": "stop",
                "help": "softly stop the VM",
                "action": "store_true",
                "required": False,
            },
            "vm_stop",
        ),
        (
            "-xa",
            {
                "dest": "all_stop",
                "help": "stop all running VMs",
                "action": "store_true",
                "required": False,
            },
            "vm_all",
        ),
        (
            "-f",
            {
                "dest": "stop_force",
                "help": "force poweroff (halt) the VM",
                "action": "store_true",
                "required": False,
            },
            "vm_stop",
        ),
        (
            "-fa",
            {
                "dest": "all_force",
                "help": "force poweroff (halt) all running VMs",
                "action": "store_true",
                "required": False,
            },
            "vm_all",
        ),
        (
            "-t",
            {
                "type": int,
                "dest": "timeout",
                "help": 'optional shutdown timeout, ignored using "-f"',
                "action": "store",
                "metavar": "timeout",
                "default": 90,
                "required": False,
            },
        ),
        (
            "-s",
            {
                "dest": "start",
                "help": "start the VM",
                "action": "store_true",
                "required": False,
            },
            "vm_start",
        ),
        (
            "-r",
            {
                "dest": "restart",
                "help": "restart the VM",
                "action": "store_true",
                "required": False,
            },
            "vm_restart",
        ),
        (
            "-ra",
            {
                "dest": "all_restart",
                "help": "restart all running VMs",
                "action": "store_true",
                "required": False,
            },
            "vm_all",
        ),
        (
            "-R",
            {
                "dest": "reset",
                "help": "force reset the VM",
                "action": "store_true",
                "required": False,
            },
            "vm_restart",
        ),
        (
            "-Ra",
            {
                "dest": "all_reset",
                "help": "force reset all running VMs",
                "action": "store_true",
                "required": False,
            },
            "vm_all",
        ),
        (
            "-q",
            {
                "dest": "hibernate",
                "help": "hibernate (suspend to disk) the VM",
                "action": "store_true",
                "required": False,
            },
            "vm_hibernate",
        ),
        (
            "-qa",
            {
                "dest": "all_hibernate",
                "help": "hibernate (suspend to disk) all running VMs",
                "action": "store_true",
                "required": False,
            },
            "vm_all",
        ),
        (
            "-ul",
            {
                "dest": "usb_list",
                "help": "list USB devices connected to the VM",
                "action": "store_true",
                "required": False,
            },
            "vm_usb_list",
        ),
        (
            "-u",
            {
                "dest": "usb_add",
                "help": "connect a USB device to the VM",
                "action": "store_true",
                "required": False,
            },
            "vm_usb",
        ),
        (
            "-ur",
            {
                "dest": "usb_delete",
                "help": "disconnect a USB device from the VM",
                "action": "store_true",
                "required": False,
            },
            "vm_usb",
        ),
        (
            "-un",
            {
                "type": str,
                "dest": "usb_name",
                "help": "name of USB device to select",
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
                "help": "USB device ID to select",
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
                "help": "USB device vendor ID to select",
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
                "help": "USB device product ID to select",
                "action": "store",
                "metavar": "product",
                "required": False,
            },
        ),
        (
            "-uc",
            {
                "dest": "usb_clean",
                "help": "remove all USB devices connected to the VM",
                "action": "store_true",
                "required": False,
            },
            "vm_usb_clean",
        ),
        (
            "--usb2",
            {
                "dest": "usb_slow",
                "help": "use the USB2.0 bus instead of USB3.0 (default is 3.0)",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            "-c",
            {
                "dest": "connect",
                "help": "connect to the selected VM",
                "action": "store_true",
                "required": False,
            },
            "vm_connect",
        ),
        (
            "-cv",
            {
                "dest": "connect_vnc",
                "help": "connect to the selected VM (using VNC)",
                "action": "store_true",
                "required": False,
            },
            "vm_connect",
        ),
        (
            "--no-fork",
            {
                "dest": "no_fork",
                "help": "do not fork when connecting to a VM",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            "-w",
            {
                "dest": "wake",
                "help": "resume the VM",
                "action": "store_true",
                "required": False,
            },
            "vm_sleep",
        ),
        (
            "-wa",
            {
                "dest": "all_wake",
                "help": "resume all suspended VMs",
                "required": False,
                "action": "store_true",
            },
            "vm_all",
        ),
        (
            "-z",
            {
                "dest": "sleep",
                "help": "suspend the VM",
                "action": "store_true",
                "required": False,
            },
            "vm_sleep",
        ),
        (
            "-za",
            {
                "dest": "all_sleep",
                "help": "suspend all running VMs",
                "action": "store_true",
                "required": False,
            },
            "vm_all",
        ),
        (
            "-es",
            {
                "dest": "schema",
                "help": "output the VM config file schema",
                "action": "store_true",
                "required": False,
            },
            "example",
        ),
        (
            "-e",
            {
                "dest": "example",
                "help": "output a VM config file example",
                "action": "store_true",
                "required": False,
            },
            "example",
        ),
        (
            "-p",
            {
                "dest": "ga_ping",
                "help": "check the status of the QEMU Guest Agent",
                "action": "store_true",
                "required": False,
            },
            "vm_ping",
        ),
        (
            "-I",
            {
                "dest": "ga_ip",
                "help": "retrive the VM IP addresses using the QEMU Guest Agent",
                "action": "store_true",
                "required": False,
            },
            "vm_ip",
        ),
        (
            "--dmenu",
            {
                "dest": "dmenu",
                "help": "list output in a dmenu compatible format",
                "action": "store_true",
                "required": False,
            },
            "vm_list",
        ),
        (
            "command",
            {
                "help": "command to execute",
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
                "help": "optional arguments",
            },
        ),
    ],
    "locker": [
        (
            "-b",
            {
                "type": str,
                "dest": "blank",
                "help": "set the Blank inhibitor time (seconds / true - until reboot / false - disable)",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
            "config",
        ),
        (
            "-kb",
            {
                "type": str,
                "dest": "blank_force",
                "help": "force set the Blank inhibitor time (seconds / true - until reboot / false - disable)",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
            "config",
        ),
        (
            "-l",
            {
                "type": str,
                "dest": "lockscreen",
                "help": "set the Lockscreen inhibitor time (seconds / true - until reboot / false - disable)",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
            "config",
        ),
        (
            "-kl",
            {
                "type": str,
                "dest": "lockscreen_force",
                "help": "force set the Lockscreen inhibitor time (seconds / true - until reboot / false - disable)",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
            "config",
        ),
        (
            "-s",
            {
                "type": str,
                "dest": "suspend",
                "help": "set the Suspend inhibitor time (seconds / true - until reboot / false - disable)",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
            "config",
        ),
        (
            "-ks",
            {
                "type": str,
                "dest": "suspend_force",
                "help": "force set the Suspend inhibitor time (seconds / true - until reboot / false - disable)",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
            "config",
        ),
        (
            "-z",
            {
                "type": str,
                "dest": "hibernate",
                "help": "set the Hibernate inhibitor time (seconds / true - until reboot / false - disable)",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
            "config",
        ),
        (
            "-kz",
            {
                "type": str,
                "dest": "hibernate_force",
                "help": "force set the Hibernate inhibitor time (seconds / true - until reboot / false - disable)",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
            "config",
        ),
        (
            "-d",
            {
                "type": str,
                "dest": "lid",
                "help": "set the Lid inhibitor time (seconds / true - until reboot / false - disable)",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
            "config",
        ),
        (
            "-kd",
            {
                "type": str,
                "dest": "lid_force",
                "help": "force set the Lid inhibitor time (seconds / true - until reboot / false - disable)",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
            "config",
        ),
        (
            "-y",
            {
                "type": str,
                "dest": "key",
                "help": "set the Key inhibitor time (seconds / true - until reboot / false - disable)",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
            "config",
        ),
        (
            "-ky",
            {
                "type": str,
                "dest": "key_force",
                "help": "force set the Key inhibitor time (seconds / true - until reboot / false - disable)",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
            "config",
        ),
        (
            "-f",
            {
                "type": str,
                "dest": "freeze",
                "help": "set the App Freeze inhibitor time (seconds / true - until reboot / false - disable)",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
            "config",
        ),
        (
            "-kf",
            {
                "type": str,
                "dest": "freeze_force",
                "help": "force set the App Freeze inhibitor time (seconds / true - until reboot / false - disable)",
                "action": "store",
                "metavar": "timeval",
                "required": False,
            },
            "config",
        ),
        (
            "-C",
            {
                "dest": "clear",
                "help": "clear all current inhibitors",
                "action": "store_true",
                "required": False,
            },
            "clear",
        ),
    ],
    "backup": [
        (
            "-l",
            {
                "dest": "list",
                "help": "list backup plans",
                "action": "store_true",
                "required": False,
            },
            "default",
        ),
        (
            "-a",
            {
                "dest": "advanced",
                "help": "display detailed backup plan information",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            "-s",
            {
                "dest": "start",
                "help": "start a backup",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            "-F",
            {
                "dest": "full",
                "help": "force a full backup instead of the current state",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            "-x",
            {
                "dest": "stop",
                "help": "stop a backup",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            "-p",
            {
                "dest": "pause",
                "help": "pause a running backup",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            "-r",
            {
                "dest": "resume",
                "help": "resume a paused backup",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            "-f",
            {
                "dest": "force",
                "help": "force a backup to start, even on battery",
                "action": "store_true",
                "required": False,
            },
            "config",
        ),
        (
            "-C",
            {
                "dest": "clear",
                "help": "clear backup database cache",
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
                "help": "select the backup target path",
                "action": "store",
                "metavar": "dir",
                "required": False,
            },
            "config",
        ),
        (
            "path",
            {
                "help": "backup target path",
                "nargs": "?",
                "action": "store",
                "default": None,
            },
            "config",
        ),
    ],
    "reload": [
        (
            "-a",
            {
                "dest": "all",
                "help": "reload all system and user services",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            "-f",
            {
                "dest": "force",
                "help": "do not prompt for conrifmation",
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
                "help": "increase the current Brightness level by 5%",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            "-d",
            {
                "dest": "decrease",
                "help": "decrease the current Brightness level by 5%",
                "action": "store_true",
                "required": False,
            },
        ),
        (
            "-s",
            {
                "type": str,
                "dest": "brightness",
                "help": "set the current Brightness level",
                "action": "store",
                "metavar": "level",
                "required": False,
            },
        ),
        (
            "level",
            {
                "nargs": "?",
                "help": "set the current Brightness level",
                "action": "store",
                "default": None,
            },
        ),
    ],
}
DESCRIPTIONS = {
    "cpu": "Processor Management Module",
    "log": "Logging Management Module",
    "blue": "Bluetooth Management Module",
    "wifi": "Wireless Management Module",
    "lock": "Lockscreen Management Module",
    "hydra": "Hydra Hypervisor Management Module",
    "locker": "Locker Management Module",
    "backup": "Backup Management Module",
    "reload": "Configuration Reload Management Module",
    "brightness": "Display Brightness Management Module",
}
