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

# file.py
#   Python file-based utility functions.

from io import StringIO
from hashlib import md5
from grp import getgrgid
from pwd import getpwuid
from shutil import copyfile
from lib.util import nes
from sys import _getframe
from typing import NamedTuple
from lib.constants import EMPTY
from string import ascii_letters, digits
from json import loads, dumps, JSONDecodeError
from os import chown, environ, makedirs, stat, chmod, remove, fspath
from os.path import (
    isfile,
    exists,
    islink,
    dirname,
    relpath,
    realpath,
    expanduser,
)

_VAR_CHARS = ascii_letters + digits + "_-"


class Stat(NamedTuple):
    stat: object
    uid: int
    gid: int
    isfile: bool
    isdir: bool
    islink: bool
    ischardev: bool
    isblockdev: bool
    path: str

    def no_dir(self, hide=False):
        if not self.isdir:
            return
        if hide:
            raise FileNotFoundError()
        raise PermissionError(f'"{self.path}" cannot be a directory')

    def no_link(self, hide=False):
        if not self.islink:
            return
        if hide:
            raise FileNotFoundError()
        raise PermissionError(f'"{self.path}" cannot be a symlink')

    def no_char_dev(self, hide=False):
        if not self.ischardev:
            return
        if hide:
            raise FileNotFoundError()
        raise PermissionError(f'"{self.path}" cannot be a character device')

    def no_block_dev(self, hide=False):
        if not self.isblockdev:
            return
        if hide:
            raise FileNotFoundError()
        raise PermissionError(f'"{self.path}" cannot be a block device')

    def check(self, mask=None, uid=None, gid=None, req=None, hide=False):
        if self.stat is None:
            raise FileNotFoundError(f'"{self.path}" does not exist')
        if isinstance(uid, int) and self.uid != uid:
            if uid == 0:
                n = "root"
            else:
                try:
                    n = getpwuid(uid).pw_name
                except KeyError:
                    n = uid
            if hide:
                raise FileNotFoundError(f'"{self.path}" does not exist')
            raise PermissionError(f'"{self.path}" owner is not "{n}"')
        if isinstance(gid, int) and self.gid != gid:
            if gid == 0:
                n = "root"
            else:
                try:
                    n = getgrgid(gid).gr_name
                except KeyError:
                    n = gid
            if hide:
                raise FileNotFoundError(f'"{self.path}" does not exist')
            raise PermissionError(f'"{self.path}" group is not "{n}"')
        if isinstance(mask, int) and (self.stat.st_mode & mask) != 0:
            if hide:
                raise FileNotFoundError(f'"{self.path}" does not exist')
            raise PermissionError(
                f'"{self.path}" permissions ({self.stat.st_mode:0o}) do not match the mask ({mask:0o})'
            )
        if isinstance(req, int) and (self.stat.st_mode & req) < req:
            if hide:
                raise FileNotFoundError(f'"{self.path}" does not exist')
            raise PermissionError(
                f'"{self.path}" permissions ({self.stat.st_mode:0o}) do not match the required permissions ({req:0o})'
            )
        return self

    def check_if(self, cond, mask=None, uid=None, gid=None, req=None, hide=False):
        if not cond:
            return self
        return self.check(mask, uid, gid, req, hide)

    def no(self, file=None, dir=None, char=None, block=None, link=None, hide=False):
        if file is not None:
            if file and not self.isfile:
                if hide:
                    raise FileNotFoundError(f'"{self.path}" does not exist')
                raise PermissionError(f'"{self.path}" must be a file')
            if not file and self.isfile:
                if hide:
                    raise FileNotFoundError(f'"{self.path}" does not exist')
                raise PermissionError(f'"{self.path}" cannot be a file')
        if dir is not None:
            if dir and not self.isdir:
                if hide:
                    raise FileNotFoundError(f'"{self.path}" does not exist')
                raise PermissionError(f'"{self.path}" must be a dir')
            if not dir and self.isdir:
                if hide:
                    raise FileNotFoundError(f'"{self.path}" does not exist')
                raise PermissionError(f'"{self.path}" cannot be a dir')
        if link is not None:
            if link and not self.islink:
                if hide:
                    raise FileNotFoundError(f'"{self.path}" does not exist')
                raise PermissionError(f'"{self.path}" must be a link')
            if not link and self.islink:
                if hide:
                    raise FileNotFoundError(f'"{self.path}" does not exist')
                raise PermissionError(f'"{self.path}" cannot be a link')
        if char is not None:
            if char and not self.ischardev:
                if hide:
                    raise FileNotFoundError(f'"{self.path}" does not exist')
                raise PermissionError(f'"{self.path}" must be a character device')
            if not char and self.ischardev:
                if hide:
                    raise FileNotFoundError(f'"{self.path}" does not exist')
                raise PermissionError(f'"{self.path}" cannot be a character device')
        if block is not None:
            if block and not self.isblockdev:
                if hide:
                    raise FileNotFoundError(f'"{self.path}" does not exist')
                raise PermissionError(f'"{self.path}" must be a block device')
            if not block and self.isblockdev:
                if hide:
                    raise FileNotFoundError(f'"{self.path}" does not exist')
                raise PermissionError(f'"{self.path}" cannot be a block device')
        return self

    def check_if_owner(
        self, owner_uid, mask=None, uid=None, gid=None, req=None, hide=False
    ):
        return self.check_if(owner_uid == self.uid, mask, uid, gid, req, hide)

    def check_if_not_owner(
        self, owner_uid, mask=None, uid=None, gid=None, req=None, hide=False
    ):
        return self.check_if(owner_uid != self.uid, mask, uid, gid, req, hide)

    def only(
        self, file=False, dir=False, char=False, block=False, link=False, hide=False
    ):
        return self.no(file, dir, char, block, link, hide)


def remove_file(path):
    if not isinstance(path, str) or len(path) == 0 or not isfile(path):
        return
    try:
        remove(path)
    except OSError:
        pass


def import_file(path):
    i = info(path, no_fail=True)
    if not i.isfile:
        return
    try:
        # NOTE(dij): Prevent loading insecure config files.
        i.check(0o7133, 0, 0, req=0o0400)
    except OSError:
        return
    finally:
        del i
    v = read_json(path, errors=False)
    if isinstance(v, dict) and len(v) > 0:
        g = _getframe(1).f_globals
        for n, d in v.items():
            if not nes(n):
                continue
            # NOTE(dij): Ignore names that do not start with [a-zA-Z]
            if not (0x61 <= ord(n[0]) <= 0x7A or 0x41 <= ord(n[0]) <= 0x5A):
                continue
            # NOTE(dij): If errors occur here, we want to break with an exception
            #            so we're not gonna catch them. AttributeErrors won't
            #            happen, but anything like TypeErrors might but that's a
            #            user issue.
            g[n.upper()] = d
        del g
    del v


def expand(path, env=None):
    if not nes(path):
        return None
    try:
        return _expand_custom(expanduser(path), env)
    except TypeError:
        return None
    except ValueError:
        return path


def read_json(path, errors=True):
    d = read(path, binary=False, errors=errors)
    if not isinstance(d, str):
        if errors:
            raise OSError(f'file "{path}" was empty')
        return None
    if len(d) == 0:
        return None
    try:
        j = loads(d)
    except JSONDecodeError as err:
        if errors:
            raise OSError(f'file "{path}" is not properly formatted: {err}')
        return None
    finally:
        del d
    return j


def ensure_dir(file, mode=0o0755):
    try:
        d = dirname(file)
    except TypeError:
        return
    if exists(d):
        return
    try:
        makedirs(d, exist_ok=True, mode=mode)
    finally:
        del d


def clean(path, root, links=False):
    if not nes(path):
        raise ValueError('"path" must be a non-empty string')
    if not nes(root):
        raise ValueError('"root" must be a non-empty string')
    if len(root) >= len(path):
        raise ValueError(f'path "{path}" is not in "{root}"')
    r = root
    if r[-1] == "/":
        r = r[:-1]
    v, c = relpath(path, start=r), path[len(r) + 1 :]
    del r
    if len(v) != len(c) or c != v:
        raise ValueError(f'path "{path}" is not in "{root}"')
    p = f"{root}{v}" if root[-1] == "/" or v[-1] == "/" else f"{root}/{v}"
    del v, c
    if realpath(path) != p:
        raise ValueError(f'path "{path}" is not in "{root}"')
    if not links and islink(p):
        raise ValueError(f'path "{path}" / "{p}" in "{root}" cannot be a link')
    return p


def _expand_custom(path, env=None):
    p = fspath(path)
    if "$" not in p and "%" not in p:
        return p
    if not isinstance(env, dict) or len(env) == 0:
        e = environ
    else:
        e = environ.copy()
        e.update(env)
    b, i = StringIO(), 0
    while i < len(p):
        c = p[i : i + 1]
        if c == "'":
            p = p[i + 1 :]
            try:
                i = p.index("'")
                b.write(f"'{p[: i + 1]}")
            except ValueError:
                b.write(f"'{p}")
                i = len(p) - 1
        elif c == "%":
            if p[i + 1 : i + 2] == "%":
                b.write("%")
                i += 1
            else:
                p = p[i + 1 :]
                try:
                    i = p.index("%")
                except ValueError:
                    b.write(f"%{p}")
                    i = len(p) - 1
                else:
                    try:
                        b.write(e[p[:i]])
                    except KeyError:
                        b.write(f"%{p[:i]}%")
        elif c == "$":
            if p[i + 1 : i + 2] == "$":
                b.write("$")
                i += 1
            elif p[i + 1 : i + 2] == "{":
                p = p[i + 2 :]
                try:
                    i = p.index("}")
                except ValueError:
                    b.write("${" + p)
                    i = len(p) - 1
                else:
                    var = p[:i]
                    try:
                        b.write(e[p[:i]])
                    except KeyError:
                        b.write(f"${{{var}}}")
            else:
                t, i = StringIO(), i + 1
                c = p[i : i + 1]
                while c and c in _VAR_CHARS:
                    t.write(c)
                    i += 1
                    c = p[i : i + 1]
                r = t.getvalue()
                t.close()
                del t
                try:
                    b.write(e[r])
                except KeyError:
                    b.write(f"${r}")
                del r
                if c:
                    i -= 1
        else:
            b.write(c)
        i += 1
    r = b.getvalue()
    b.close()
    del b, e
    return r


def read(path, binary=False, errors=True, strip=False):
    if not isinstance(path, str) or len(path) == 0:
        if errors:
            raise ValueError('"path" must be a non-empty string!')
        return None
    if not isfile(path):
        if errors:
            raise OSError(f'file "{path}" does not exist or is not a file')
        return None
    try:
        with open(path, "rb" if binary else "r") as f:
            d = f.read()
            if binary or not strip:
                return d
            v = d.strip()
            del d
            if len(v) <= 2:
                return v
            if v[-1] == "\n":
                return v[0:-2] if v[-2] == "\r" else v[0:-1]
            if v[-1] == "\r":
                return v[0:-2] if v[-2] == "\n" else v[0:-1]
            return v
    except (OSError, UnicodeDecodeError) as err:
        if errors:
            raise err
    return None


def hash_file(path, block=4096, errors=True, hasher=md5):
    if not callable(hasher):
        if errors:
            raise ValueError('"hasher" must be callable')
        return None
    if not isinstance(path, str):
        if errors:
            raise ValueError('"path" must be a string!')
        return None
    if not isfile(path):
        if errors:
            raise OSError(f'file "{path}" does not exist or is not a file')
        return None
    try:
        g = hasher(usedforsecurity=False)
    except TypeError:
        g = hasher()
    try:
        with open(path, "rb") as f:
            while True:
                b = f.read(block)
                if not b:
                    break
                g.update(b)
    except OSError as err:
        if errors:
            raise err
        return None
    else:
        return g.hexdigest()
    finally:
        del g


def info(path, sym=True, st=None, no_fail=False, hide=False):
    if st is None:
        try:
            s = stat(path, follow_symlinks=sym)
        except OSError as err:
            if hide:
                raise FileNotFoundError()
            if no_fail:
                return Stat(None, None, None, False, False, False, False, False, path)
            raise err
    else:
        s = st
    m = s.st_mode & 0o170000
    return Stat(
        s,
        s.st_uid,
        s.st_gid,
        m == 0o100000,  # isfile
        m == 0o040000,  # isdir
        m == 0o120000,  # islink
        m == 0o020000,  # ischardev
        m == 0o060000,  # isblockdev
        path,
    )


def copy(src, dst, uid=None, gid=None, perms=None, errors=True):
    if not isinstance(src, str) or len(src) == 0:
        if errors:
            raise ValueError('"src" must be a non-empty string!')
        return False
    if not isinstance(dst, str) or len(dst) == 0:
        if errors:
            raise ValueError('"dst" must be a non-empty string!')
        return False
    try:
        copyfile(src, dst, follow_symlinks=False)
        if isinstance(uid, int) and isinstance(gid, int):
            chown(dst, uid, gid, follow_symlinks=True)
        if isinstance(perms, int):
            chmod(dst, perms, follow_symlinks=True)
    except OSError as err:
        if errors:
            raise err
        return False


def perm_check(path, mask=None, uid=None, gid=None, sym=True, st=None):
    info(path, sym=sym, st=st).check(mask, uid, gid)


def write(path, data, binary=False, errors=True, append=False, perms=None):
    if not isinstance(path, str) or len(path) == 0:
        if errors:
            raise ValueError('"path" must be a non-empty string')
        return False
    try:
        ensure_dir(path)
    except OSError as err:
        if errors:
            raise err
        return False
    m = ("ab" if binary else "a") if append else ("wb" if binary else "w")
    try:
        with open(path, m) as f:
            if data is None:
                f.write(bytes() if binary else EMPTY)
            elif isinstance(data, (bytes, bytearray)):
                f.write(data if binary else data.decode("UTF-8"))
            elif isinstance(data, str):
                f.write(data.encode("UTF-8") if binary else data)
            else:
                f.write(f"{data}".encode("UTF-8") if binary else f"{data}")
            f.flush()
        if isinstance(perms, int):
            chmod(path, perms, follow_symlinks=True)
    except (OSError, UnicodeEncodeError) as err:
        if errors:
            raise err
        return False
    finally:
        del m
    return True


def write_json(path, obj, errors=True, indent=None, sort=False, perms=None):
    if obj is None:
        if errors:
            raise ValueError('"obj" must not be None')
        return False
    try:
        d = dumps(obj, indent=indent, sort_keys=sort)
    except (TypeError, JSONDecodeError) as err:
        if errors:
            raise ValueError(f'cannot convert "obj" to JSON: {err}')
        return False
    try:
        return write(path, d, binary=False, errors=errors, append=False, perms=perms)
    except OSError as err:
        if errors:
            raise err
    finally:
        del d
    return False
