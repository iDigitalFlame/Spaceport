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

# Shared Module Dependencies: Hydra
#   Used to keep links un-borken for non-default configurations of directories

from glob import glob
from lib.util import nes
from collections import namedtuple
from os import getuid, environ, getcwd
from lib.util.file import read, read_json, expand, info
from os.path import isfile, exists, basename, isabs, dirname
from lib.constants.config import HYDRA_VM_CONFIGS, HYDRA_DIR_USB

Device = namedtuple("Device", ["name", "path", "vendor", "product"])


def get_devices():
    d, r = glob(HYDRA_DIR_USB), dict()
    if len(d) == 0:
        return r
    for i in d:
        b = dirname(i)
        try:
            v, p = read(i, strip=True), read(f"{b}/idProduct", strip=True)
        except OSError:
            continue
        try:
            n = read(f"{b}/product", strip=True)
        except OSError:
            n = "USB Device"
        try:
            m = f'{read(f"{b}/manufacturer", strip=True)}'
        except OSError:
            m = None
        if nes(m):
            n = f"{m} {n}"
        del m
        r[f"{v}:{p}".lower()] = Device(f"{n} ({v}:{p})", b, v, p)
        del n, v, p, b
    del d
    return r


def _load_user_config(path, config):
    if not isinstance(config, dict) or "hydra" not in config:
        return None, None
    if not isinstance(config["hydra"], dict):
        return None, None
    p, d = path, expand(config["hydra"].get("directory"))
    if not isabs(path):
        a, n = config["hydra"].get("aliases"), path.lower()
        if isinstance(a, dict):
            v = expand(a.get(n))
            if nes(v) and exists(v):
                p = v
            del v
        del a, n
    if p == ".":
        p = getcwd()
    if not nes(p) or not isabs(p) and nes(d):
        v = f"{d}/{p}"
        if exists(v):
            p = v
        del v
    if nes(p) and isfile(p):
        return p, d
    if not nes(p):
        return None, d
    if "HOME" in environ:
        if not isabs(p):
            p = expand(p)
        if not isabs(p):
            v = f"{getcwd()}/{p}"
            if exists(v):
                p = v
            del v
    if not exists(p):
        return None, d
    i = info(p)
    if i.isfile:
        return p, d
    if not i.isdir:
        return None, d
    del i
    b = basename(p)
    for f in [b, f"{b}.conf", f"{b}.json", f"{b}.vmx"] + HYDRA_VM_CONFIGS:
        v = f"{p}/{f}"
        if isfile(v):
            return v, d
        del v
    del b
    return None, d


def load_vm(path, config_path=None, server=False):
    if not nes(path):
        return None
    if not server and nes(config_path):
        try:
            i = info(config_path)
        except OSError as err:
            raise OSError(f'config file "{config_path}" not found: {err}')
        try:
            i.no(dir=False, char=False, block=False).check(0o0120, getuid())
        except OSError as err:
            raise OSError(
                f'config file "{config_path}" has improper permissions: {err}'
            )
        del i
        p, _ = _load_user_config(path, read_json(config_path))
        if nes(p):
            return p
        del p
    if isfile(path):
        return path
    return None
