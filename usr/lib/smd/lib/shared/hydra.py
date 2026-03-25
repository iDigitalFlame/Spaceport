################################
### iDigitalFlame  2016-2026 ###
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
# Copyright (C) 2016 - 2026 iDigitalFlame
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
from time import time
from lib.util import nes
from datetime import datetime
from collections import namedtuple
from os import getcwd, getuid, environ
from os.path import isabs, exists, isfile, dirname, basename
from lib.util.file import info, read, expand, read_json, write_json
from lib.constants.config import HYDRA_DIR_USB, HYDRA_VM_CONFIGS, HYDRA_FILE_USB_DEVICES

_DEVICES = None

Device = namedtuple("Device", ["name", "path", "vendor", "product"])
Snapshot = namedtuple("Snapshot", ["id", "sec", "parent", "depth", "cur", "tag"])


def _time(n, s):
    if not isinstance(s, (float, int)) or s == 0:
        return ""
    v = datetime.fromtimestamp(s)
    if v.year < 1971:
        return ""
    if n == v:
        return "0s"
    if (n - v).days > 0:
        return v.strftime("%H:%M %m/%d/%y")
    m, y = divmod((n - v).seconds, 60)
    h, m = divmod(m, 60)
    if h > 12:
        if h >= n.hour:
            return v.strftime("%H:%M %m/%d/%y")
        return v.strftime("%H:%M")
    del v
    if h > 0:
        return f"{h}h {m}m"
    if m > 0:
        return f"{m}m {y}s"
    return f"{y}s"


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
        k = f"{v}:{p}".lower()
        # Try to get the device name from the USB devices dictionary first
        n = get_device_name(k, n)
        del m
        r[k] = Device(f"{n} ({v}:{p})", b, v, p)
        del k, n, v, p, b
    del d
    return r


def valid_snap_name(v):
    if not nes(v) or len(v) < 4:
        return False
    for i in v:
        c = ord(i)
        if 0x61 <= c <= 0x7A:  # a-z
            continue
        if 0x41 <= c <= 0x5A:  # A-Z
            continue
        if 0x30 <= c <= 0x39:  # 0-9
            continue
        if c == 0x2E or c == 0x5F or c == 0x2D or c == 0x2B:  # . _ - +
            continue
        return False
    return True


def _print_snap(e, c, n):
    if c == 0:
        if e.cur:
            print(f"- *{e.tag} - {_time(n, e.sec)} [Base Snapshot] (You are Here)")
        else:
            print(f"- {e.tag} - {_time(n, e.sec)} [Base Snapshot]")
    else:
        if e.cur:
            print(f'{" " * c}- *{e.tag} - {_time(n, e.sec)} (You are Here)')
        else:
            print(f'{" " * c}- {e.tag} - {_time(n, e.sec)}')


def _load_usb_device_names():
    global _DEVICES
    if isinstance(_DEVICES, dict):
        return
    _DEVICES = dict()
    if not isfile(HYDRA_FILE_USB_DEVICES):
        return
    try:
        with open(HYDRA_FILE_USB_DEVICES) as f:
            b = f.read().split("\n")
    except OSError:
        return
    n, m = None, None
    for i in b:
        if len(i) <= 5 or i[0] == "#" or i[0] == " ":
            continue
        if i[1] == " " or i[2] == " " or i[3] == " " or i[0] == "C" or i[0] == "R":
            continue
        if i[0] == "\t" and m is not None and i[4] != " ":
            _DEVICES[f"{m}:{i[1:5]}"] = f"{n} {i[7:].strip()}"
            continue
        if i[5] == " ":
            n, m = i[6:].strip(), i[0:4]
    del b, n, m


def get_device_name(d, opt=None):
    _load_usb_device_names()
    return _DEVICES.get(d, opt)


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
        p, _ = _load_user_config(path, read_json(config_path, sym=True))
        if nes(p):
            return p
        del p
    if isfile(path):
        return path
    return None


class Snapshots(list):
    __slots__ = ()

    def __init__(self):
        list.__init__(self)

    def cur(self):
        for x in range(0, len(self)):
            if self[x].cur:
                return (self[x], x)
        return (None, None)

    def _new(self):
        v = 0
        if len(self) == 0:
            return v
        for i in self:
            if v > i.id:
                continue
            v = i.id
        return v + 1

    def depth(self):
        v, _ = self.cur()
        if v is None:
            return 0
        return v.depth

    def print(self):
        if len(self) == 0:
            return
        b, n = self[0], datetime.now()
        _print_snap(b, 0, n)
        for x in range(1, len(self)):
            _print_snap(self[x], self[x].depth - b.depth, n)
        del b, n

    def add(self, tag):
        c, p = self.cur()
        i = self._new()
        if c is None:
            self.append(Snapshot(i, int(time()), 0, 0, True, tag))
            return
        self[p] = self[p]._replace(cur=False)
        while p + 1 < len(self) and self[p + 1].parent >= c.id:
            p += 1
        self.insert(p + 1, Snapshot(i, int(time()), c.id, c.depth + 1, True, tag))
        del c, i
        return

    def find(self, id):
        for x in range(0, len(self)):
            if self[x].id == id:
                return (self[x], x)
        return (None, None)

    def save(self, file):
        write_json(file, self, perms=0o600)

    def delete(self, tag):
        v, p = self.find_by_tag(tag)
        if v is None:
            return
        del self[p], p
        if len(self) == 0:
            return
        e = len(self) - 1
        for x in range(0, len(self)):
            if self[x].parent == v.id:
                self[x], e = self[x]._replace(parent=v.parent), x
        if not v.cur:
            return
        _, p = self.find(v.parent)
        if p is None:
            self[e] = self[e]._replace(cur=True)
        else:
            self[p] = self[p]._replace(cur=True)
        del e, p, v

    def revert(self, tag):
        _, v = self.find_by_tag(tag)
        if v is None:
            return
        _, c = self.cur()
        if v == c:
            return
        if c is not None:
            self[c] = self[c]._replace(cur=False)
        self[v] = self[v]._replace(cur=True)

    def find_by_tag(self, tag):
        for x in range(0, len(self)):
            if self[x].tag == tag:
                return (self[x], x)
        return (None, None)

    def load(self, data, file=None):
        if nes(file) and data is None:
            return self.load(read_json(file))
        if not isinstance(data, list) or len(data) == 0:
            return
        self.clear()
        for i in data:
            if not isinstance(i, (list, tuple)) or len(i) != 6:
                continue
            self.append(Snapshot(*i))

    def sync(self, server, vmid, e):
        d, r = list(), dict()
        for i in e:
            r[i["name"]] = [i, 0]
        for i in self:
            if i.tag not in r:
                d.append(i.tag)
                continue
            r[i.tag][1] += 1
        for i in d:
            server.debug(f'[m/hydra/VM({vmid})]: Deleting un-synced Snapshot "{i}"..')
            self.delete(i)
        del d
        for k, v in r.items():
            if v[1] == 0:
                server.warning(
                    f'[m/hydra/VM({vmid})]: Snapshot "{k}" was not found in cache, but present on storage!'
                )
        del r

    def verify_tag(self, tag, exists=True):
        if len(self) == 0:
            return not exists
        x, _ = self.find_by_tag(tag)
        if (exists and x is None) or (not exists and x is not None):
            return False
        del x
        return True
